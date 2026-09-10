#!/usr/bin/env python3
from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wteval.mutation import MUTATION_RULES, all_mutants, score_mutation  # noqa: E402


class MutationTests(unittest.TestCase):
    def test_comparison_flip(self) -> None:
        mutants = all_mutants("x = a > b", MUTATION_RULES)
        self.assertTrue(any(m.rule == "gt->ge" and m.mutated_text == "x = a >= b" for m in mutants))

    def test_equality_flip(self) -> None:
        mutants = all_mutants("a == b", MUTATION_RULES)
        self.assertTrue(any(m.rule == "eq->ne" and m.mutated_text == "a != b" for m in mutants))

    def test_boolean_flip(self) -> None:
        mutants = all_mutants("x = a and b", MUTATION_RULES)
        self.assertTrue(any(m.rule == "and->or" and m.mutated_text == "x = a or b" for m in mutants))

    def test_arithmetic_flip_on_augassign(self) -> None:
        # AST-level mutation reaches AugAssign's operator, unlike text-level.
        mutants = all_mutants("x += 1", MUTATION_RULES)
        self.assertTrue(any(m.rule == "add->sub" and m.mutated_text == "x -= 1" for m in mutants))

    def test_no_string_mutation(self) -> None:
        # The '>' lives inside a string literal, not code — no mutant should be made.
        self.assertEqual(all_mutants('x = "a > b"', MUTATION_RULES), [])

    def test_no_stillborn_mutants(self) -> None:
        src = "def f(a, b):\n    return a > b and a != b"
        for mutant in all_mutants(src, MUTATION_RULES):
            ast.parse(mutant.mutated_text)  # must not raise

    def test_score_excludes_stillborn(self) -> None:
        self.assertEqual(score_mutation(killed=3, survived=1), 0.75)
        self.assertIsNone(score_mutation(killed=0, survived=0))


if __name__ == "__main__":
    unittest.main()
