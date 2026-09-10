#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wteval.mutation import MUTATION_RULES, all_mutants, score_mutation  # noqa: E402


class MutationTests(unittest.TestCase):
    def test_all_mutants_finds_sites(self) -> None:
        mutants = all_mutants("x = a > b", MUTATION_RULES)
        self.assertTrue(any(m.rule == "gt->ge" for m in mutants))

    def test_boolean_flip_mutates_word_boundaries(self) -> None:
        mutants = all_mutants("if a and b:", MUTATION_RULES)
        self.assertTrue(any(m.rule == "and->or" and " or " in m.mutated_text for m in mutants))

    def test_plus_to_minus_avoids_assignment(self) -> None:
        mutants = all_mutants("x += 1", MUTATION_RULES)
        self.assertFalse(any(m.rule == "plus->minus" for m in mutants))

    def test_score_excludes_stillborn(self) -> None:
        self.assertEqual(score_mutation(killed=3, survived=1), 0.75)
        self.assertIsNone(score_mutation(killed=0, survived=0))


if __name__ == "__main__":
    unittest.main()
