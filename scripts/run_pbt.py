#!/usr/bin/env python3
"""Run property-based tests: the built-in demo or an external catalog.

External catalogs (e.g. ``pbt_properties/wtcraft.py``) must export
``properties()`` returning a list of dicts ``{"name", "shape", "failure"}``
where ``failure`` is a ``wteval.pbt.Failure`` or ``None``. In gate mode
(external catalog, or ``--strict``) a failing property makes the process exit
non-zero.
"""

from __future__ import annotations

import argparse
import importlib.util
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


def _load_external(path: Path) -> list[dict]:
    spec = importlib.util.spec_from_file_location("pbt_catalog", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load catalog {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not callable(getattr(module, "properties", None)):
        raise RuntimeError(f"{path} must export properties()")
    return module.properties()


def _compact(value, limit: int = 160) -> str:
    if isinstance(value, (dict, list, tuple)):
        text = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    else:
        text = repr(value)
    return text if len(text) <= limit else text[:limit] + "..."


def _render(failure: Failure | None) -> str:
    if failure is None:
        return "PASS"
    return (
        f"FAIL counterexample={_compact(failure.counterexample)} "
        f"(shrinks={failure.shrinks}, original={_compact(failure.original)})"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--properties", default=None, help="Catalog module exporting properties()")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero on failure even for the demo")
    args = parser.parse_args()

    props = _load_external(Path(args.properties)) if args.properties else _properties()

    passed = 0
    failed = 0
    for prop in props:
        failure = prop.get("failure")
        if failure is None:
            passed += 1
        else:
            failed += 1
        print(f"{prop.get('name', '?'):28s} [{prop.get('shape', '?'):30s}] {_render(failure)}")
    print(f"\n{passed} passed, {failed} failed")
    strict = args.strict or args.properties is not None
    return 1 if (failed and strict) else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, FileNotFoundError, OSError) as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(1)
