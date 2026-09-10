"""AST-guided mutation testing for Python source (standard library only).

Finds real mutation sites by walking the parsed AST, then applies each mutation
as a source-level splice at the operator's byte offsets. This keeps mutmut's
precision with no third-party dependency, and avoids text-level mutation's two
failure modes:

- no stillborn mutants — every mutant is a syntactically valid operator swap;
- no string/comment mutation — only code nodes are visited.

Operator leaves (``cmpop``/``boolop``/``operator``) carry no position in the
AST, so offsets are recovered from the gap between the surrounding operands.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Sequence


@dataclass
class Mutant:
    rule: str
    start: int
    end: int
    before: str
    after: str
    mutated_text: str


MUTATION_RULES = (
    "eq->ne", "ne->eq",
    "lt->le", "le->lt",
    "gt->ge", "ge->gt",
    "and->or", "or->and",
    "add->sub", "sub->add",
    "true->false", "false->true",
)

# op type -> (rule, replacement source, operator source token)
_CMP = {
    ast.Eq: ("eq->ne", "!=", "=="),
    ast.NotEq: ("ne->eq", "==", "!="),
    ast.Lt: ("lt->le", "<=", "<"),
    ast.LtE: ("le->lt", "<", "<="),
    ast.Gt: ("gt->ge", ">=", ">"),
    ast.GtE: ("ge->gt", ">", ">="),
}
_BOOL = {
    ast.And: ("and->or", "or", "and"),
    ast.Or: ("or->and", "and", "or"),
}
_BIN = {
    ast.Add: ("add->sub", "-", "+"),
    ast.Sub: ("sub->add", "+", "-"),
}
_AUG = {
    ast.Add: ("add->sub", "-=", "+="),
    ast.Sub: ("sub->add", "+=", "-="),
}


def _offsets(data: bytes, lines: list[bytes], node: ast.AST) -> tuple[int, int] | None:
    lineno = getattr(node, "lineno", None)
    col_offset = getattr(node, "col_offset", None)
    end_lineno = getattr(node, "end_lineno", None)
    end_col_offset = getattr(node, "end_col_offset", None)
    if None in (lineno, col_offset, end_lineno, end_col_offset):
        return None

    def off(ln: int, col: int) -> int:
        total = 0
        for i in range(ln - 1):
            total += len(lines[i]) + 1  # +1 for the newline
        return total + col

    return off(lineno, col_offset), off(end_lineno, end_col_offset)


def _gap(data: bytes, lines: list[bytes], left: ast.AST, right: ast.AST, token: str) -> tuple[int, int] | None:
    left_span = _offsets(data, lines, left)
    right_span = _offsets(data, lines, right)
    if left_span is None or right_span is None:
        return None
    gap = data[left_span[1] : right_span[0]]
    needle = token.encode("utf-8")
    idx = gap.find(needle)
    if idx < 0:
        return None
    start = left_span[1] + idx
    return start, start + len(needle)


def all_mutants(text: str, rules: Sequence[str] = MUTATION_RULES) -> list[Mutant]:
    enabled = set(rules)
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    data = text.encode("utf-8")
    lines = data.split(b"\n")
    mutants: list[Mutant] = []

    def emit(rule: str, replacement: str, start: int, end: int) -> None:
        mutated = data[:start] + replacement.encode("utf-8") + data[end:]
        mutants.append(
            Mutant(
                rule=rule,
                start=start,
                end=end,
                before=data[start:end].decode("utf-8"),
                after=replacement,
                mutated_text=mutated.decode("utf-8"),
            )
        )

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and (node.value is True or node.value is False):
            rule = "true->false" if node.value is True else "false->true"
            if rule not in enabled:
                continue
            span = _offsets(data, lines, node)
            if span:
                replacement = "False" if node.value is True else "True"
                emit(rule, replacement, span[0], span[1])
        elif isinstance(node, ast.Compare):
            operands = [node.left, *node.comparators]
            for i, op in enumerate(node.ops):
                entry = _CMP.get(type(op))
                if entry is None or entry[0] not in enabled:
                    continue
                pos = _gap(data, lines, operands[i], operands[i + 1], entry[2])
                if pos:
                    emit(entry[0], entry[1], pos[0], pos[1])
        elif isinstance(node, ast.BoolOp):
            entry = _BOOL.get(type(node.op))
            if entry is None or entry[0] not in enabled:
                continue
            for i in range(len(node.values) - 1):
                pos = _gap(data, lines, node.values[i], node.values[i + 1], entry[2])
                if pos:
                    emit(entry[0], entry[1], pos[0], pos[1])
        elif isinstance(node, ast.BinOp):
            entry = _BIN.get(type(node.op))
            if entry is None or entry[0] not in enabled:
                continue
            pos = _gap(data, lines, node.left, node.right, entry[2])
            if pos:
                emit(entry[0], entry[1], pos[0], pos[1])
        elif isinstance(node, ast.AugAssign):
            entry = _AUG.get(type(node.op))
            if entry is None or entry[0] not in enabled:
                continue
            pos = _gap(data, lines, node.target, node.value, entry[2])
            if pos:
                emit(entry[0], entry[1], pos[0], pos[1])

    return mutants


def score_mutation(killed: int, survived: int) -> float | None:
    """Mutation score = killed / (killed + survived); stillborn mutants excluded."""
    total = killed + survived
    if total == 0:
        return None
    return killed / total
