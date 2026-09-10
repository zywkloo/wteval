#!/usr/bin/env python3
"""Score deterministic-oracle capability runs grouped by arm and agent."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wteval.capability import capability_metrics, load_runs, write_capability_report  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", required=True, help="Directory of capability-run JSON files")
    parser.add_argument("--out", required=True, help="Directory for report.json and report.md")
    args = parser.parse_args()
    runs = load_runs(Path(args.runs))
    metrics = capability_metrics(runs)
    json_path, md_path = write_capability_report(Path(args.out), metrics)
    print(
        json.dumps(
            {"n_runs": metrics["n_runs"], "report_json": str(json_path), "report_md": str(md_path)},
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, KeyError) as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(1)
