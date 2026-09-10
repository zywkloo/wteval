#!/usr/bin/env python3
"""Scan git history for "make this test pass" candidate tasks.

Flags commits that touch at least one test file and at least one source file,
then emits a candidate list that maps to capability-run records
(schemas/capability-run-v1.schema.json).

This is a heuristic only: a human must curate the list and confirm each commit
is a real "test now passes" ground truth before running any experiment.
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

SOURCE_EXTENSIONS = {
    "py", "ts", "tsx", "js", "jsx", "mjs", "cjs", "go", "rs", "java", "kt",
    "kts", "rb", "c", "cc", "cpp", "h", "hpp", "cs", "swift", "m", "mm",
    "scala", "php", "sh", "ps1", "lua", "zig", "ex", "exs", "erl", "hs",
    "clj", "cljs", "dart", "r", "jl", "fs", "fsx", "vb",
}

EXCLUDE_SEGMENTS = {
    "node_modules", "vendor", "third_party", "third-party", ".git",
    "dist", "build", "__pycache__", ".venv", "venv", "target", ".idea",
    ".claude", ".agent-harness", "worktrees",
}


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
    if ext in SOURCE_EXTENSIONS:
        return "source"
    return "other"


def scan_repo(
    repo: Path,
    since: str | None,
    max_commits: int,
    first_parent: bool,
) -> list[dict]:
    candidates = []
    for sha in list_commits(repo, since, max_commits, first_parent):
        meta = commit_meta(repo, sha)
        test_files: list[dict] = []
        source_files: list[dict] = []
        for status, path in changed_files(repo, sha):
            kind = classify(path)
            if kind == "test":
                test_files.append({"path": path, "status": status})
            elif kind == "source":
                source_files.append({"path": path, "status": status})
        if not test_files or not source_files:
            continue
        candidates.append({
            "repo": repo.name,
            "oracle_sha": sha,
            "base_sha": meta["parent"],
            "subject": meta["subject"],
            "author_date": meta["author_date"],
            "test_files": test_files,
            "source_files": source_files,
            "test_added": any(f["status"] == "A" for f in test_files),
        })
    return candidates


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

    candidates: list[dict] = []
    for raw in args.repo:
        repo = Path(raw).expanduser().resolve()
        if not (repo / ".git").exists():
            print(f"warning: {repo} is not a git repo, skipping", file=sys.stderr)
            continue
        candidates.extend(scan_repo(repo, args.since, args.max_commits, args.first_parent))

    candidates.sort(key=lambda c: c["author_date"], reverse=True)
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "n_candidates": len(candidates),
        "candidates": candidates,
        "note": (
            "Heuristic only: human-curate before use. Map each candidate to a "
            "capability-run with task.base_revision=base_sha and "
            "task.oracle_revision=oracle_sha."
        ),
    }
    text = json.dumps(payload, indent=2)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
        print(f"wrote {len(candidates)} candidates to {args.out}", file=sys.stderr)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(1)
