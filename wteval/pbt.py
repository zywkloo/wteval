"""Minimal property-based testing harness (standard library only).

Property shapes mirror the deterministic-oracle taxonomy: ``invariant``,
``round_trip``, and ``idempotent``. Inputs are generated from a seeded RNG and
a failing example is greedily shrunk toward a minimal counterexample.

This is deliberately small and honest: it demonstrates the shape of PBT
(like Kiro/Hypothesis) without claiming Hypothesis-scale random generation or
sophisticated shrinking.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Sequence


@dataclass
class Failure:
    property_name: str
    original: Any
    counterexample: Any
    shrinks: int


def gen_ints(lo: int, hi: int, n: int, seed: int) -> list[int]:
    rng = random.Random(seed)
    return [rng.randint(lo, hi) for _ in range(n)]


def gen_int_lists(
    lo: int,
    hi: int,
    length_lo: int,
    length_hi: int,
    n: int,
    seed: int,
) -> list[list[int]]:
    rng = random.Random(seed)
    out: list[list[int]] = []
    for _ in range(n):
        length = rng.randint(length_lo, length_hi)
        out.append([rng.randint(lo, hi) for _ in range(length)])
    return out


def gen_strings(alphabet: str, length_lo: int, length_hi: int, n: int, seed: int) -> list[str]:
    rng = random.Random(seed)
    out: list[str] = []
    for _ in range(n):
        length = rng.randint(length_lo, length_hi)
        out.append("".join(rng.choice(alphabet) for _ in range(length)))
    return out


def gen_json_values(depth: int, n: int, seed: int) -> list[Any]:
    """Generate nested JSON-safe values (dict/list/str/int/bool/None)."""
    rng = random.Random(seed)

    def one(remaining: int) -> Any:
        if remaining <= 0:
            return _scalar(rng)
        kind = rng.choice(["scalar", "scalar", "list", "dict"])
        if kind == "scalar":
            return _scalar(rng)
        if kind == "list":
            return [one(remaining - 1) for _ in range(rng.randint(0, 3))]
        return {str(rng.randint(0, 20)): one(remaining - 1) for _ in range(rng.randint(0, 3))}

    return [one(depth) for _ in range(n)]


def _scalar(rng: random.Random) -> Any:
    return rng.choice([rng.randint(-1000, 1000), rng.random() * 1000, rng.choice(["a", "b", "", "☃"])])


def _fails(predicate: Callable[[Any], bool], example: Any) -> bool:
    try:
        return not bool(predicate(example))
    except Exception:
        return True


def _shrink_int(value: int) -> Iterable[int]:
    # Strictly decreasing magnitude guarantees termination (no self-yield).
    for candidate in (0, value // 2, value - 1 if value > 0 else value + 1):
        if abs(candidate) < abs(value):
            yield candidate


def _shrink_str(value: str) -> Iterable[str]:
    if not value:
        return
    yield ""
    if len(value) >= 2:
        yield value[: len(value) // 2]
        yield value[1:]


def _shrink_list(value: Sequence[Any]) -> Iterable[Sequence[Any]]:
    if not value:
        return
    yield []
    if len(value) >= 2:
        yield value[: len(value) // 2]
        yield value[len(value) // 2 :]
        yield value[1:]


def _shrinkers(value: Any) -> Iterable[Any]:
    if isinstance(value, bool):
        return
    if isinstance(value, int):
        yield from _shrink_int(value)
    elif isinstance(value, str):
        yield from _shrink_str(value)
    elif isinstance(value, (list, tuple)):
        yield from _shrink_list(value)


def minimize(predicate: Callable[[Any], bool], start: Any) -> tuple[Any, int]:
    """Greedy shrink to a local minimum counterexample."""
    current = start
    steps = 0
    improved = True
    while improved:
        improved = False
        for smaller in _shrinkers(current):
            if _fails(predicate, smaller):
                current = smaller
                steps += 1
                improved = True
                break
    return current, steps


def find_failure(
    predicate: Callable[[Any], bool],
    examples: Sequence[Any],
    name: str,
) -> Failure | None:
    for example in examples:
        if _fails(predicate, example):
            counterexample, shrinks = minimize(predicate, example)
            return Failure(
                property_name=name,
                original=example,
                counterexample=counterexample,
                shrinks=shrinks,
            )
    return None


def invariant(predicate: Callable[[Any], bool], examples: Sequence[Any], name: str) -> Failure | None:
    return find_failure(predicate, examples, name)


def round_trip(
    encode: Callable[[Any], Any],
    decode: Callable[[Any], Any],
    examples: Sequence[Any],
    name: str,
    eq: Callable[[Any, Any], bool] = lambda a, b: a == b,
) -> Failure | None:
    def predicate(x: Any) -> bool:
        return eq(decode(encode(x)), x)

    return find_failure(predicate, examples, name)


def idempotent(
    f: Callable[[Any], Any],
    examples: Sequence[Any],
    name: str,
    eq: Callable[[Any, Any], bool] = lambda a, b: a == b,
) -> Failure | None:
    def predicate(x: Any) -> bool:
        return eq(f(f(x)), f(x))

    return find_failure(predicate, examples, name)
