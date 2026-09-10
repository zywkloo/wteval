#!/usr/bin/env python3
"""Convert git-history verification units into the unified task format.

Runs scan_verifications.py, filters test-harness infra, and emits tasks in the
same shape seed_mutations.py uses (origin=history). Test-harness infra such as
run_all.sh / framework.sh / smoke.sh and the contract runner are dropped because
they duplicate finer-grained units.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wteval.history import build_task  # noqa: E402

DEFAULT_EXCLUDE = ("run_all.sh", "framework.sh", "smoke.sh", "contract_policy_envelope")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, action="append", help="Repo path (repeatable)")
    parser.add_argument("--since", default=None, help="git rev-list --since value")
    parser.add_argument("--exclude", action="append", default=[], help="Extra substring to drop (repeatable)")
    parser.add_argument("--out", required=True, help="Output dir for seed-tasks.json")
    args = parser.parse_args()

    cmd = [sys.executable, str(ROOT / "scripts" / "scan_verifications.py")]
    for repo in args.repo:
        cmd.append(f"--repo={repo}")
    if args.since:
        cmd.append(f"--since={args.since}")
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "scan_verifications failed")

    units = json.loads(proc.stdout)["units"]
    excludes = tuple(DEFAULT_EXCLUDE) + tuple(args.exclude)

    tasks = []
    index = 0
    for unit in units:
        verification = unit["verification"]
        if any(exclude in verification for exclude in excludes):
            continue
        index += 1
        tasks.append(build_task(unit, index))

    payload = {
        "schema_version": 1,
        "tool": "emit_history_tasks",
        "n_units": len(units),
        "n_tasks": len(tasks),
        "excluded": list(excludes),
        "tasks": tasks,
        "note": "History tasks reuse the capability-run task shape; origin=history separates them from mutation-seeded tasks.",
    }
    out = Path(args.out).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out / "seed-tasks.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"emitted {len(tasks)} history tasks (from {len(units)} units) -> {out}/seed-tasks.json")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, ValueError, KeyError) as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(1)
