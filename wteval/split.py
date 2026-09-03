"""Chronological train/holdout split.

Related follow-ups that share a task_id stay in the earlier split of the
group so labels cannot leak from a later turn into training.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any


def parse_timestamp(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def assign_splits(
    examples: list[dict[str, Any]],
    holdout_fraction: float = 0.2,
) -> list[dict[str, Any]]:
    if not 0 < holdout_fraction < 1:
        raise ValueError("holdout_fraction must be in (0, 1)")
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for example in examples:
        grouped[example["task_id"]].append(example)
    tasks = []
    for task_id, items in grouped.items():
        items.sort(key=lambda item: (parse_timestamp(item["created_at"]), item["example_id"]))
        tasks.append((parse_timestamp(items[0]["created_at"]), task_id, items))
    tasks.sort(key=lambda item: (item[0], item[1]))
    holdout_count = max(1, int(round(len(tasks) * holdout_fraction)))
    if holdout_count >= len(tasks):
        holdout_count = len(tasks) - 1
    if holdout_count < 1:
        raise ValueError("need at least two task_id groups to split")
    cutoff = len(tasks) - holdout_count
    assigned = []
    for index, (_started, _task_id, items) in enumerate(tasks):
        split = "train" if index < cutoff else "holdout"
        for item in items:
            copy = dict(item)
            copy["split"] = split
            assigned.append(copy)
    assigned.sort(key=lambda item: (parse_timestamp(item["created_at"]), item["example_id"]))
    return assigned


def split_examples(
    examples: list[dict[str, Any]],
    holdout_fraction: float = 0.2,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if all(example.get("split") in ("train", "holdout") for example in examples):
        assigned = examples
    else:
        assigned = assign_splits(examples, holdout_fraction=holdout_fraction)
    train = [item for item in assigned if item.get("split") == "train"]
    holdout = [item for item in assigned if item.get("split") == "holdout"]
    if not train or not holdout:
        raise ValueError("both train and holdout splits must be non-empty")
    return train, holdout


def select_split(
    examples: list[dict[str, Any]],
    split: str,
    holdout_fraction: float = 0.2,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    train, holdout = split_examples(examples, holdout_fraction=holdout_fraction)
    if split == "train":
        return train, train
    if split == "holdout":
        return train, holdout
    if split == "all":
        return train, train + holdout
    raise ValueError(f"unknown eval split: {split}")
