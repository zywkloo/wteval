#!/usr/bin/env python3
"""Schedule (and later execute) the two-arm capability experiment.

Dry-run expands the unified task pool into task x arm x agent entries. The
execute path (worktree setup, agent runner, check/verify capture) is defined by
wteval.executor's Runner seam and is filled in when a real runner exists.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wteval.executor import Agent, build_schedule  # noqa: E402


def _load_tasks(paths: list[str]) -> list[dict]:
    tasks = []
    for raw in paths:
        path = Path(raw).expanduser()
        if path.is_dir():
            path = path / "seed-tasks.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        tasks.extend(data["tasks"])
    return tasks


def _load_agents(raw: str) -> list[Agent]:
    candidate = Path(raw).expanduser()
    if candidate.is_file():
        raw = candidate.read_text(encoding="utf-8")
    return [Agent(**item) for item in json.loads(raw)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", required=True, nargs="+", help="seed-tasks.json files or dirs")
    parser.add_argument("--agents", required=True, help="JSON list of {endpoint, model, config_version}, or a file")
    parser.add_argument("--repetitions", type=int, default=1, help="Runs per task/arm/agent; default 1")
    parser.add_argument("--out", default=None, help="Write schedule JSON here; default stdout")
    args = parser.parse_args()

    tasks = _load_tasks(args.tasks)
    agents = _load_agents(args.agents)
    schedule = build_schedule(tasks, agents, repetitions=args.repetitions)
    payload = {"schema_version": 1, "n_runs": len(schedule), "schedule": schedule}

    text = json.dumps(payload, indent=2)
    if args.out:
        Path(args.out).expanduser().write_text(text + "\n", encoding="utf-8")
        print(f"scheduled {len(schedule)} runs -> {args.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(1)
