#!/usr/bin/env python3
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wteval.dataset import load_examples  # noqa: E402
from wteval.validate import validate_example, validate_experiment  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures" / "examples"


class ValidateTests(unittest.TestCase):
    def test_fixtures_load(self) -> None:
        examples = load_examples(FIXTURES)
        self.assertEqual(len(examples), 10)
        self.assertEqual({item["split"] for item in examples}, {"train", "holdout"})

    def test_unknown_field_rejected(self) -> None:
        example = copy.deepcopy(load_examples(FIXTURES)[0])
        example["secret_prompt"] = "do not store this"
        errors = validate_example(example)
        self.assertTrue(any("unknown fields" in item for item in errors))

    def test_invalid_work_kind_rejected(self) -> None:
        example = copy.deepcopy(load_examples(FIXTURES)[0])
        example["labels"]["work_kind"] = "coding"
        errors = validate_example(example)
        self.assertTrue(any("work_kind" in item for item in errors))

    def test_p90_below_p50_rejected(self) -> None:
        example = copy.deepcopy(load_examples(FIXTURES)[0])
        example["predictions"] = {
            "bad": {
                "classification": example["labels"] | {
                    "confidence": 0.2,
                    "recommended_sequence": example["labels"]["intended_sequence"],
                },
                "recommended_route": {
                    "role": "executor",
                    "endpoint": "codex",
                    "model_tier": "balanced-coding",
                },
                "forecast": {
                    "reported_tokens_p50": 100,
                    "reported_tokens_p90": 50,
                    "source_confidence": "inferred",
                },
            }
        }
        # labels | extra produces invalid classification because labels has labeler fields
        example["predictions"]["bad"]["classification"] = {
            "work_kind": "execution",
            "size": "s",
            "risk": "medium",
            "confidence": 0.2,
            "recommended_sequence": ["executor"],
        }
        errors = validate_example(example)
        self.assertTrue(any("reported_tokens_p90" in item for item in errors))

    def test_experiment_requires_known_metric_group(self) -> None:
        errors = validate_experiment(
            {
                "schema_version": 1,
                "experiment_id": "bad",
                "dataset": "x",
                "systems": ["majority"],
                "metrics": ["bleu"],
                "split": "holdout",
            }
        )
        self.assertTrue(any("metrics[0]" in item for item in errors))


if __name__ == "__main__":
    unittest.main()
