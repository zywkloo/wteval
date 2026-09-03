"""Load and validate example JSON files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .validate import format_errors, validate_example, validate_experiment


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_examples(root: Path) -> list[dict[str, Any]]:
    files = sorted(path for path in root.rglob("*.json") if path.is_file())
    if not files:
        raise ValueError(f"no JSON examples under {root}")
    examples = []
    errors = []
    seen = set()
    for path in files:
        try:
            obj = load_json(path)
        except json.JSONDecodeError as exc:
            errors.append(f"{path}: invalid JSON: {exc}")
            continue
        item_errors = validate_example(obj)
        if item_errors:
            errors.append(f"{path}:\n{format_errors(item_errors)}")
            continue
        example_id = obj["example_id"]
        if example_id in seen:
            errors.append(f"{path}: duplicate example_id {example_id}")
            continue
        seen.add(example_id)
        examples.append(obj)
    if errors:
        raise ValueError("\n\n".join(errors))
    return examples


def load_experiment(path: Path) -> dict[str, Any]:
    obj = load_json(path)
    errors = validate_experiment(obj)
    if errors:
        raise ValueError(f"{path}:\n{format_errors(errors)}")
    return obj
