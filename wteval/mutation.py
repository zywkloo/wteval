"""Text-level mutation catalog for mutation testing.

Injects single-token bugs into source files so a test suite can be scored by
how many mutants it kills. Text-level mutations are a cheap approximation of
AST-based tools (mutmut, mut.py): some mutants are stillborn (syntax errors)
and are excluded from the score rather than counted.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Sequence


@dataclass
class Rule:
    name: str
    pattern: re.Pattern[str]
    replacement: str


@dataclass
class Mutant:
    rule: str
    start: int
    end: int
    mutated_text: str


MUTATION_RULES: tuple[Rule, ...] = (
    Rule("ge->gt", re.compile(r">="), ">"),
    Rule("gt->ge", re.compile(r"(?<![<>=!-])>(?!=)"), ">="),
    Rule("le->lt", re.compile(r"<="), "<"),
    Rule("lt->le", re.compile(r"(?<![<>=!-])<(?!=)"), "<="),
    Rule("eq->ne", re.compile(r"=="), "!="),
    Rule("ne->eq", re.compile(r"!="), "=="),
    Rule("and->or", re.compile(r"\band\b"), "or"),
    Rule("or->and", re.compile(r"\bor\b"), "and"),
    Rule("true->false", re.compile(r"\bTrue\b"), "False"),
    Rule("false->true", re.compile(r"\bFalse\b"), "True"),
    Rule("plus->minus", re.compile(r"(?<![+\-*/%])\+(?!=)"), "-"),
)


def all_mutants(text: str, rules: Sequence[Rule] = MUTATION_RULES) -> list[Mutant]:
    mutants: list[Mutant] = []
    for rule in rules:
        for match in rule.pattern.finditer(text):
            mutated = text[: match.start()] + rule.replacement + text[match.end() :]
            mutants.append(
                Mutant(rule=rule.name, start=match.start(), end=match.end(), mutated_text=mutated)
            )
    return mutants


def score_mutation(killed: int, survived: int) -> float | None:
    """Mutation score = killed / (killed + survived); stillborn mutants excluded."""
    total = killed + survived
    if total == 0:
        return None
    return killed / total


def classify_by_exit_code(exit_code: int) -> str:
    if exit_code == 0:
        return "survived"
    return "killed"
