#!/usr/bin/env python3
"""Seed deterministic-oracle capability tasks by injecting known bugs.

The mutation gate (``run_mutation.py``) scores a test suite. This script is the
complementary half: every mutant the suite *kills* becomes a capability-eval
task whose ground truth is known exactly — ``base_revision`` is the mutated
commit, ``oracle_revision`` is the pre-mutation ``HEAD``, and the failing test
is the declared verification.

Each killed mutant is committed on a detached worktree, kept alive as a
``wteval/mut-*`` branch in the target repo, and emitted as a patch plus a task
catalog. The catalog's ``task`` object is drop-in for the capability-run
schema's ``task``, so running the two-arm experiment is a matter of copying a
task into a run record per arm and executing the agent.

Example against wtcraft:

    python3 scripts/seed_mutations.py \
      --repo ../wtcraft \
      --files "src/**/*.py" "scripts/*.py" \
      --test-cmd "bash tests/run_all.sh" \
      --max-mutants 30 \
      --out datasets/private/mutations
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wteval.mutation import MUTATION_RULES, all_mutants, score_mutation  # noqa: E402

# Best-effort failing-test extraction from unittest/pytest-style output.
_FAILING_TEST_RE = re.compile(
    r"(?:^|\n)(?:FAILED\s+(\S+)|(?:FAIL|ERROR):\s+(\S+))"
)


def _run(args: list[str], cwd: Path, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args, cwd=cwd, capture_output=True, text=True, timeout=timeout
    )


def _run_shell(cmd: str, cwd: Path, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout)


def _git(repo: Path, *args: str, cwd: Path | None = None, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
    return _run(["git", "-C", str(repo), *args], cwd or repo, timeout)


def _head_sha(repo: Path) -> str:
    proc = _git(repo, "rev-parse", "HEAD")
    if proc.returncode != 0:
        raise RuntimeError("target is not a git repository with a HEAD commit")
    return proc.stdout.strip()


def _ensure_clean(repo: Path) -> None:
    proc = _git(repo, "status", "--porcelain")
    if proc.stdout.strip():
        raise RuntimeError(
            "target working tree is dirty; commit or stash before seeding "
            f"(git status:\n{proc.stdout})"
        )


def _repo_name(repo: Path) -> str:
    proc = _git(repo, "config", "--get", "remote.origin.url")
    url = proc.stdout.strip()
    if url:
        return url
    return repo.resolve().name


def _collect_sites(workdir: Path, file_globs: list[str]) -> list[tuple[str, object]]:
    """Return (relative_path, Mutant) pairs in deterministic order."""
    sites: list[tuple[str, object]] = []
    for glob in file_globs:
        for path in sorted(workdir.glob(glob)):
            if not path.is_file():
                continue
            rel = str(path.relative_to(workdir))
            text = path.read_text(encoding="utf-8")
            for mutant in all_mutants(text, MUTATION_RULES):
                sites.append((rel, mutant))
    return sites


def _extract_failing_test(output: str) -> str | None:
    match = _FAILING_TEST_RE.search(output)
    if match:
        return match.group(1) or match.group(2)
    return None


def _verification_string(test_cmd: str, rule: str, rel: str, failing_test: str | None) -> str:
    suffix = f" (failing: {failing_test})" if failing_test else ""
    return f"{test_cmd} [mutant {rule} in {rel}]{suffix}"


def _emit_patch(repo: Path, oracle: str, base: str, out: Path, task_id: str) -> Path:
    proc = _git(repo, "diff", oracle, base)
    patch_path = out / "mutations" / f"{task_id}.patch"
    patch_path.parent.mkdir(parents=True, exist_ok=True)
    patch_path.write_text(proc.stdout, encoding="utf-8")
    return patch_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, help="Git repo to mutate (read-only working tree)")
    parser.add_argument("--files", nargs="+", required=True, help="Glob(s) of source files to mutate, e.g. 'src/**/*.py'")
    parser.add_argument("--test-cmd", required=True, help="Verification command; non-zero exit = mutant killed")
    parser.add_argument("--max-mutants", type=int, default=30, help="Cap on injected mutants (0 = unlimited)")
    parser.add_argument("--seed", type=int, default=None, help="Shuffle sites with this seed; default = deterministic order")
    parser.add_argument("--timeout", type=int, default=300, help="Per-mutant test timeout in seconds")
    parser.add_argument("--out", required=True, help="Output dir for seed-tasks.json + mutations/*.patch")
    args = parser.parse_args()

    repo = Path(args.repo).expanduser().resolve()
    out = Path(args.out).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)

    _ensure_clean(repo)
    oracle = _head_sha(repo)
    name = _repo_name(repo)

    # Discover sites on a throwaway copy so we know counts before touching git.
    tmp_probe = Path(tempfile.mkdtemp(prefix="wteval-probe-"))
    try:
        probe_wt = tmp_probe / "repo"
        _git(repo, "worktree", "add", "--detach", str(probe_wt), oracle)
        sites = _collect_sites(probe_wt, args.files)
    finally:
        _git(repo, "worktree", "remove", "--force", str(probe_wt))
        shutil.rmtree(tmp_probe, ignore_errors=True)

    if args.seed is not None:
        import random

        random.Random(args.seed).shuffle(sites)
    if args.max_mutants:
        sites = sites[: args.max_mutants]

    tasks: list[dict] = []
    records: list[dict] = []
    counts = {"killed": 0, "survived": 0, "timeout": 0}

    for index, (rel, mutant) in enumerate(sites, start=1):
        task_id = f"mut-{index:03d}-{mutant.rule}"
        tmp = Path(tempfile.mkdtemp(prefix="wteval-seed-"))
        wt = tmp / "worktree"
        try:
            _git(repo, "worktree", "add", "--detach", str(wt), oracle)
            target = wt / rel
            original = target.read_text(encoding="utf-8")
            target.write_text(mutant.mutated_text, encoding="utf-8")

            try:
                proc = _run_shell(args.test_cmd, cwd=wt, timeout=args.timeout)
                timed_out = False
            except subprocess.TimeoutExpired:
                proc = None
                timed_out = True

            if not timed_out and proc.returncode == 0:
                counts["survived"] += 1
                records.append({"task_id": task_id, "rule": mutant.rule, "file": rel, "status": "survived"})
                continue

            if timed_out:
                counts["timeout"] += 1
                output = ""
            else:
                counts["killed"] += 1
                output = (proc.stdout or "") + "\n" + (proc.stderr or "")

            # Commit the mutant so base_revision is a real SHA.
            _git(wt, "add", "-A")
            commit = _git(
                wt,
                "-c", "user.name=wteval",
                "-c", "user.email=wteval@localhost",
                "commit", "-m", f"wteval mutant {task_id}: {mutant.rule} in {rel}",
            )
            if commit.returncode != 0:
                raise RuntimeError(f"failed to commit mutant {task_id}: {commit.stderr}")
            base = _head_sha(wt)

            # Keep the commit alive beyond the detached worktree.
            _git(repo, "branch", f"wteval/{task_id}", base)
            patch = _emit_patch(repo, oracle, base, out, task_id)

            failing = _extract_failing_test(output)
            status = "timeout" if timed_out else "killed"
            records.append(
                {
                    "task_id": task_id,
                    "rule": mutant.rule,
                    "file": rel,
                    "status": status,
                    "failing_test": failing,
                }
            )
            tasks.append(
                {
                    "task_id": task_id,
                    "origin": "mutation",
                    "task": {
                        "repository": name,
                        "base_revision": base,
                        "oracle_revision": oracle,
                        "prompt_fingerprint": f"mutation:{mutant.rule}:{rel}",
                        "verification_declared": True,
                        "verification": _verification_string(args.test_cmd, mutant.rule, rel, failing),
                        "origin": "mutation",
                    },
                    "mutation": {"rule": mutant.rule, "file": rel, "original": original, "mutated": mutant.mutated_text},
                    "patch": f"mutations/{task_id}.patch",
                    "failing_test": failing,
                }
            )
        finally:
            _git(repo, "worktree", "remove", "--force", str(wt))
            shutil.rmtree(tmp, ignore_errors=True)

    score = score_mutation(counts["killed"] + counts["timeout"], counts["survived"])
    payload = {
        "schema_version": 1,
        "tool": "seed_mutations",
        "repo": name,
        "oracle_revision": oracle,
        "test_cmd": args.test_cmd,
        "n_sites": len(sites),
        "n_tasks": len(tasks),
        "counts": counts,
        "mutation_score": score,
        "tasks": tasks,
        "note": "timeout mutants count as killed (verification did not pass); survived mutants are test gaps, not tasks.",
    }
    (out / "seed-tasks.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        f"seeded {len(tasks)} tasks ({counts['killed']} killed, {counts['timeout']} timeout, "
        f"{counts['survived']} survived) from {len(sites)} sites -> {out}/seed-tasks.json"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, RuntimeError) as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(1)
