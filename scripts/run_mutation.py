#!/usr/bin/env python3
"""Mutation-test a target repo: inject mutants, run its tests, report the score.

Operates on a temporary copy of the target repo, so the working tree is never
touched. A mutant is:

- stillborn  if the mutated source no longer compiles (excluded from score);
- killed     if the test command exits non-zero;
- survived   if the test command still exits zero (a gap in the tests).

Example against wteval itself:

    python3 scripts/run_mutation.py \
      --repo . \
      --files "wteval/*.py" \
      --test-cmd "python3 -m unittest discover -s tests -p test_metrics.py -q" \
      --max-mutants 40
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wteval.mutation import MUTATION_RULES, all_mutants, score_mutation  # noqa: E402

IGNORE = shutil.ignore_patterns(".git", "__pycache__", "*.pyc", "reports", "datasets", ".venv", ".DS_Store")


def _copy_repo(repo: Path) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="wteval-mutation-"))
    shutil.copytree(repo, tmp / "repo", ignore=IGNORE)
    return tmp / "repo"


def _run(cmd: str, cwd: Path) -> int:
    proc = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    return proc.returncode


def _py_compiles(path: Path) -> bool:
    proc = subprocess.run(
        [sys.executable, "-m", "py_compile", str(path)],
        capture_output=True,
        text=True,
    )
    return proc.returncode == 0


def _classify(mutant_text: str, file_path: Path, test_cmd: str, cwd: Path) -> str:
    original = file_path.read_text(encoding="utf-8")
    try:
        file_path.write_text(mutant_text, encoding="utf-8")
        if file_path.suffix == ".py" and not _py_compiles(file_path):
            return "stillborn"
        exit_code = _run(test_cmd, cwd)
        return "survived" if exit_code == 0 else "killed"
    finally:
        file_path.write_text(original, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, help="Target repo to copy and mutate")
    parser.add_argument("--files", required=True, help="Glob of source files to mutate, e.g. 'wteval/*.py'")
    parser.add_argument("--test-cmd", required=True, help="Command that exits non-zero when tests fail")
    parser.add_argument("--max-mutants", type=int, default=40, help="Cap total mutants (0 = all)")
    parser.add_argument("--out", default=None, help="Write JSON report here; default stdout")
    args = parser.parse_args()

    repo = Path(args.repo).expanduser().resolve()
    workdir = _copy_repo(repo)

    mutants = []
    for path in sorted(workdir.glob(args.files)):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for mutant in all_mutants(text, MUTATION_RULES):
            mutants.append((path, mutant))
            if args.max_mutants and len(mutants) >= args.max_mutants:
                break
        if args.max_mutants and len(mutants) >= args.max_mutants:
            break

    records = []
    counts = {"killed": 0, "survived": 0, "stillborn": 0}
    for path, mutant in mutants:
        rel = path.relative_to(workdir)
        status = _classify(mutant.mutated_text, path, args.test_cmd, workdir)
        counts[status] += 1
        records.append(
            {
                "file": str(rel),
                "rule": mutant.rule,
                "status": status,
                "site": f"{mutant.start}:{mutant.end}",
            }
        )

    shutil.rmtree(workdir.parent, ignore_errors=True)
    score = score_mutation(counts["killed"], counts["survived"])
    payload = {
        "schema_version": 1,
        "repo": str(repo),
        "test_cmd": args.test_cmd,
        "n_mutants": len(records),
        "counts": counts,
        "mutation_score": score,
        "records": records,
        "note": "stillborn mutants (syntax errors) are excluded from the score.",
    }
    text = json.dumps(payload, indent=2)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
        print(f"mutation score: {score} ({counts['killed']} killed / {counts['survived']} survived / {counts['stillborn']} stillborn) -> {args.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, RuntimeError) as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(1)
