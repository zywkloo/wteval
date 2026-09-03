#!/usr/bin/env python3
"""Validate example JSON files against the v1 example schema."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wteval.dataset import load_examples  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="Directory of example JSON files")
    args = parser.parse_args()
    examples = load_examples(Path(args.path))
    print(f"validated {len(examples)} examples")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(1)
