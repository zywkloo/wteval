#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wteval.baselines import keyword, majority, predict_system  # noqa: E402
from wteval.dataset import load_examples  # noqa: E402
from wteval.split import assign_splits, select_split  # noqa: E402


class SplitTests(unittest.TestCase):
    def test_same_task_stays_together(self) -> None:
        examples = [
            {
                "example_id": "a1",
                "task_id": "same",
                "created_at": "2026-07-01T00:00:00Z",
            },
            {
                "example_id": "b1",
                "task_id": "later",
                "created_at": "2026-08-01T00:00:00Z",
            },
            {
                "example_id": "a2",
                "task_id": "same",
                "created_at": "2026-09-01T00:00:00Z",
            },
        ]
        assigned = assign_splits(examples, holdout_fraction=0.5)
        by_id = {item["example_id"]: item["split"] for item in assigned}
        self.assertEqual(by_id["a1"], by_id["a2"])
        self.assertNotEqual(by_id["a1"], by_id["b1"])


class BaselineTests(unittest.TestCase):
    def test_keyword_rules(self) -> None:
        train: list[dict] = []
        planning = keyword(
            train,
            {"features": {"feature_snapshot": "Design the architecture for adapters."}},
        )
        self.assertEqual(planning["classification"]["work_kind"], "planning")
        empty = keyword(train, {"features": {"feature_snapshot": ""}})
        self.assertTrue(empty["abstain"])

    def test_majority_uses_train_only(self) -> None:
        train = [
            {
                "labels": {
                    "work_kind": "execution",
                    "size": "s",
                    "risk": "medium",
                    "intended_sequence": ["executor"],
                },
                "outcome": {"usage": {"reported_tokens": 10, "subscription_quota_delta": 0.1}},
            }
        ]
        pred = majority(train, {"labels": {"work_kind": "planning"}})
        self.assertEqual(pred["classification"]["work_kind"], "execution")
        self.assertEqual(pred["forecast"]["reported_tokens_p50"], 10)

    def test_recorded_system(self) -> None:
        examples = load_examples(ROOT / "tests" / "fixtures" / "examples")
        holdout = [item for item in examples if item["example_id"] == "syn-007"][0]
        pred = predict_system("recorded:shadow-rules", [], holdout)
        self.assertEqual(pred["classification"]["work_kind"], "execution")
        self.assertEqual(pred["system_id"], "recorded:shadow-rules")

    def test_frozen_fixture_split(self) -> None:
        examples = load_examples(ROOT / "tests" / "fixtures" / "examples")
        train, holdout = select_split(examples, "holdout")
        self.assertEqual(len(train), 6)
        self.assertEqual(len(holdout), 4)


if __name__ == "__main__":
    unittest.main()
