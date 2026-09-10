#!/usr/bin/env python3
"""Enumerate deterministic verification units for capability-eval tasks.

Unlike scan_candidates.py (commit granularity), this decomposes commits by the
verification unit they introduce: a runnable test script, or a contract-case
directory. Each unit is one candidate task: "make <verification> pass" from
base_sha, with oracle_sha as the ground truth where it passes.

This is a heuristic only: a human must curate the list (and drop test-harness
infra such as run_all.sh / framework.sh) before running any experiment.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

TEST_DIR_SEGMENTS = {"tests", "test", "spec", "specs", "__tests__", "e2e"}

TEST_NAME_RES = [
    re.compile(r"^test_.*\.py$"),
    re.compile(r".*_test\.py$"),
    re.compile(r".*\.test\.(ts|tsx|js|jsx|mjs|cjs)$"),
    re.compile(r".*\.spec\.(ts|tsx|js|jsx|mjs|cjs)$"),
    re.compile(r".*(Test|Tests|Spec|Specs)\.(java|kt|cs|swift|m|mm)$"),
    re.compile(r".*_test\.(go|rs|rb)$"),
    re.compile(r".*_spec\.rb$"),
]

RUNNABLE_TEST_EXTS = {
    "py", "sh", "ts", "tsx", "js", "jsx", "mjs", "cjs", "go", "rs", "rb",
    "java", "kt", "cs", "swift", "m", "mm",
}

EXCLUDE_SEGMENTS = {
    "node_modules", "vendor", "third_party", "third-party", ".git",
    "dist", "build", "__pycache__", ".venv", "venv", "target", ".idea",
    ".claude", ".agent-harness", "worktrees",
}

CASE_MARKERS = {"case.json", "expected.json"}


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout


def list_commits(
    repo: Path,
    since: str | None,
    max_commits: int,
    first_parent: bool = False,
) -> list[str]:
    cmd = ["rev-list"]
    if first_parent:
        cmd.append("--first-parent")
    if since:
        cmd.append(f"--since={since}")
    if max_commits:
        cmd.extend(["-n", str(max_commits)])
    cmd.append("HEAD")
    return [line for line in git(repo, *cmd).splitlines() if line]


def commit_meta(repo: Path, sha: str) -> dict[str, str | None]:
    out = git(repo, "show", "-s", "--format=%aI%x00%s%x00%P", sha).rstrip("\n")
    parts = out.split("\x00")
    parents = parts[2].split() if len(parts) > 2 and parts[2] else []
    return {
        "author_date": parts[0] if len(parts) > 0 else "",
        "subject": parts[1] if len(parts) > 1 else "",
        "parent": parents[0] if parents else None,
    }


def changed_files(repo: Path, sha: str) -> list[tuple[str, str]]:
    out = git(repo, "diff-tree", "--no-commit-id", "--name-status", "-r", "--root", sha)
    files = []
    for line in out.splitlines():
        status, _, path = line.partition("\t")
        if path:
            files.append((status.strip(), path))
    return files


def classify(path: str) -> str:
    parts = path.split("/")
    name = parts[-1].lower() if parts else ""
    if any(seg in EXCLUDE_SEGMENTS for seg in parts[:-1]):
        return "other"
    if any(seg in TEST_DIR_SEGMENTS for seg in parts[:-1]):
        return "test"
    if any(pat.search(name) for pat in TEST_NAME_RES):
        return "test"
    ext = name.rsplit(".", 1)[-1] if "." in name else ""
    if ext in {
        "py", "ts", "tsx", "js", "jsx", "mjs", "cjs", "go", "rs", "java",
        "kt", "kts", "rb", "c", "cc", "cpp", "h", "hpp", "cs", "swift", "m",
        "mm", "scala", "php", "sh", "ps1", "lua", "zig", "ex", "exs", "erl",
        "hs", "clj", "cljs", "dart", "r", "jl", "fs", "fsx", "vb",
    }:
        return "source"
    return "other"


def is_test_script(path: str) -> bool:
    if classify(path) != "test":
        return False
    name = path.split("/")[-1].lower()
    ext = name.rsplit(".", 1)[-1] if "." in name else ""
    return ext in RUNNABLE_TEST_EXTS


def scan_repo(
    repo: Path,
    since: str | None,
    max_commits: int,
    first_parent: bool,
) -> list[dict]:
    units = []
    for sha in list_commits(repo, since, max_commits, first_parent):
        meta = commit_meta(repo, sha)
        added = [path for status, path in changed_files(repo, sha) if status == "A"]
        case_dirs: dict[str, None] = {}
        scripts: list[str] = []
        for path in added:
            name = path.split("/")[-1]
            if name.lower() in CASE_MARKERS:
                case_dirs[str(Path(path).parent)] = None
            elif is_test_script(path):
                scripts.append(path)
        for directory in sorted(case_dirs):
            units.append(_unit(repo.name, "contract_case", directory, sha, meta))
        for script in scripts:
            units.append(_unit(repo.name, "test_script", script, sha, meta))
    return units


def _unit(repo: str, kind: str, verification: str, sha: str, meta: dict) -> dict:
    return {
        "repo": repo,
        "kind": kind,
        "verification": verification,
        "oracle_sha": sha,
        "base_sha": meta["parent"],
        "subject": meta["subject"],
        "author_date": meta["author_date"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, action="append", help="Repo path (repeatable)")
    parser.add_argument("--since", default=None, help="git rev-list --since value, e.g. 2026-01-01")
    parser.add_argument("--max-commits", type=int, default=0, help="Cap commits scanned per repo (0 = all)")
    parser.add_argument(
        "--first-parent",
        action="store_true",
        help="Follow only the first-parent (mainline) history; default is all reachable commits",
    )
    parser.add_argument("--out", default=None, help="Write JSON here; default stdout")
    args = parser.parse_args()

    units: list[dict] = []
    for raw in args.repo:
        repo = Path(raw).expanduser().resolve()
        if not (repo / ".git").exists():
            print(f"warning: {repo} is not a git repo, skipping", file=sys.stderr)
            continue
        units.extend(scan_repo(repo, args.since, args.max_commits, args.first_parent))

    units.sort(key=lambda u: (u["repo"], u["verification"]))
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "n_units": len(units),
        "units": units,
        "note": (
            "Heuristic only: human-curate before use. Each unit maps to a "
            "capability-run task with task.verification=<verification>, "
            "task.base_revision=base_sha, and task.oracle_revision=oracle_sha."
        ),
    }
    text = json.dumps(payload, indent=2)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
        print(f"wrote {len(units)} verification units to {args.out}", file=sys.stderr)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(1)
