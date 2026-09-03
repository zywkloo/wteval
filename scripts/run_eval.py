#!/usr/bin/env python3
"""Run a versioned experiment config against a labeled dataset directory."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wteval.run import run_experiment  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment", required=True, help="Path to experiment.json")
    parser.add_argument("--dataset", required=True, help="Directory of example JSON files")
    parser.add_argument("--out", required=True, help="Directory for report.json and report.md")
    args = parser.parse_args()
    result = run_experiment(Path(args.experiment), Path(args.dataset), Path(args.out))
    print(json.dumps({"n_train": result["n_train"], "n_eval": result["n_eval"], "report_json": result["report_json"]}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, KeyError) as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(1)
