#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wteval.pbt import (  # noqa: E402
    gen_int_lists,
    gen_ints,
    gen_strings,
    idempotent,
    invariant,
    minimize,
    round_trip,
)


class PbtTests(unittest.TestCase):
    def test_generators_are_seeded_and_shaped(self) -> None:
        self.assertEqual(gen_ints(0, 0, 5, 1), [0, 0, 0, 0, 0])
        lists = gen_int_lists(0, 0, 3, 3, 4, 1)
        self.assertEqual(len(lists), 4)
        self.assertTrue(all(len(x) == 3 for x in lists))
        strings = gen_strings("a", 5, 5, 3, 1)
        self.assertEqual(strings, ["aaaaa", "aaaaa", "aaaaa"])

    def test_round_trip_passes_for_identity(self) -> None:
        failure = round_trip(
            encode=lambda x: x,
            decode=lambda x: x,
            examples=[1, 2, 3],
            name="identity",
        )
        self.assertIsNone(failure)

    def test_invariant_finds_failure(self) -> None:
        failure = invariant(
            predicate=lambda x: x > 0,
            examples=[1, 2, -3, 4],
            name="positive",
        )
        self.assertIsNotNone(failure)
        self.assertEqual(failure.original, -3)
        self.assertEqual(failure.counterexample, 0)  # minimal refutation of x > 0

    def test_minimize_shrinks_counterexample(self) -> None:
        # Predicate fails for any list containing a negative number.
        predicate = lambda xs: all(x >= 0 for x in xs)
        shrunk, steps = minimize(predicate, [5, 5, -1, 5])
        self.assertEqual(shrunk, [-1])
        self.assertGreaterEqual(steps, 1)

    def test_idempotent_sorted(self) -> None:
        failure = idempotent(sorted, examples=[[3, 1, 2], [1], []], name="sorted")
        self.assertIsNone(failure)


if __name__ == "__main__":
    unittest.main()
