#!/usr/bin/env python3
"""Run the seeded property-based testing demo properties.

Each property maps to the deterministic-oracle taxonomy: round-trip,
idempotent, and invariant. One property is intentionally naive to demonstrate
counterexample discovery and shrinking.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wteval.pbt import (  # noqa: E402
    Failure,
    gen_int_lists,
    gen_json_values,
    gen_strings,
    idempotent,
    invariant,
    round_trip,
)

SEED = 20260910


def _properties():
    return [
        {
            "name": "round_trip_utf8",
            "shape": "round-trip (byte identity)",
            "failure": round_trip(
                encode=lambda s: s.encode("utf-8"),
                decode=lambda b: b.decode("utf-8"),
                examples=gen_strings("abc☃", 0, 20, 200, SEED),
                name="round_trip_utf8",
            ),
        },
        {
            "name": "round_trip_json",
            "shape": "round-trip",
            "failure": round_trip(
                encode=json.dumps,
                decode=json.loads,
                examples=gen_json_values(3, 200, SEED),
                name="round_trip_json",
                eq=lambda a, b: _json_eq(a, b),
            ),
        },
        {
            "name": "idempotent_sorted",
            "shape": "idempotent",
            "failure": idempotent(
                sorted,
                examples=gen_int_lists(-50, 50, 0, 12, 200, SEED),
                name="idempotent_sorted",
            ),
        },
        {
            "name": "invariant_mean_bounds",
            "shape": "invariant",
            "failure": invariant(
                predicate=lambda xs: (not xs) or min(xs) <= _mean(xs) <= max(xs),
                examples=gen_int_lists(-50, 50, 1, 12, 200, SEED),
                name="invariant_mean_bounds",
            ),
        },
        {
            "name": "naive_median_index",
            "shape": "invariant (intentionally naive)",
            "failure": invariant(
                predicate=lambda xs: not xs or _median(xs) == sorted(xs)[len(xs) // 2],
                examples=gen_int_lists(0, 10, 1, 8, 200, SEED),
                name="naive_median_index",
            ),
        },
    ]


def _mean(xs):
    return sum(xs) / len(xs)


def _median(xs):
    ordered = sorted(xs)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2


def _json_eq(a, b) -> bool:
    # JSON round-trips tuples to lists and int keys to str keys; normalize.
    return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def _render(failure: Failure | None) -> str:
    if failure is None:
        return "PASS"
    return (
        f"FAIL counterexample={failure.counterexample!r} "
        f"(shrinks={failure.shrinks}, original={failure.original!r})"
    )


def main() -> int:
    passed = 0
    failed = 0
    for prop in _properties():
        result = _render(prop["failure"])
        if prop["failure"] is None:
            passed += 1
        else:
            failed += 1
        print(f"{prop['name']:24s} [{prop['shape']:28s}] {result}")
    print(f"\n{passed} passed, {failed} failed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
