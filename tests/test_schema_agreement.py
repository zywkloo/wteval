#!/usr/bin/env python3
"""Compare published JSON Schema field sets with the executable validator."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wteval import constants  # noqa: E402


def load(name: str) -> dict:
    with (ROOT / "schemas" / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


class SchemaAgreementTests(unittest.TestCase):
    def test_example_fields(self) -> None:
        schema = load("example-v1.schema.json")
        self.assertEqual(tuple(schema["required"]), constants.EXAMPLE_REQUIRED)
        self.assertEqual(
            set(schema["properties"]),
            set(constants.EXAMPLE_REQUIRED) | set(constants.EXAMPLE_OPTIONAL),
        )
        features = schema["$defs"]["features"]
        self.assertEqual(tuple(features["required"]), constants.FEATURES_REQUIRED)
        self.assertEqual(
            set(features["properties"]),
            set(constants.FEATURES_REQUIRED) | set(constants.FEATURES_OPTIONAL),
        )
        labels = schema["$defs"]["labels"]
        self.assertEqual(tuple(labels["required"]), constants.LABELS_REQUIRED)
        self.assertEqual(
            set(labels["properties"]),
            set(constants.LABELS_REQUIRED) | set(constants.LABELS_OPTIONAL),
        )

    def test_decision_fields(self) -> None:
        schema = load("decision-v1.schema.json")
        self.assertEqual(tuple(schema["required"]), constants.DECISION_REQUIRED)
        self.assertEqual(
            set(schema["properties"]),
            set(constants.DECISION_REQUIRED) | set(constants.DECISION_OPTIONAL),
        )
        classification = schema["$defs"]["classification"]
        self.assertEqual(tuple(classification["required"]), constants.CLASSIFICATION_REQUIRED)
        self.assertEqual(
            set(classification["properties"]),
            set(constants.CLASSIFICATION_REQUIRED) | set(constants.CLASSIFICATION_OPTIONAL),
        )
        route = schema["$defs"]["route"]
        self.assertEqual(tuple(route["required"]), constants.ROUTE_REQUIRED)
        self.assertEqual(
            set(route["properties"]),
            set(constants.ROUTE_REQUIRED) | set(constants.ROUTE_OPTIONAL),
        )
        forecast = schema["$defs"]["forecast"]
        self.assertEqual(tuple(forecast["required"]), constants.FORECAST_REQUIRED)
        self.assertEqual(
            set(forecast["properties"]),
            set(constants.FORECAST_REQUIRED) | set(constants.FORECAST_OPTIONAL),
        )

    def test_outcome_fields(self) -> None:
        schema = load("outcome-v1.schema.json")
        self.assertEqual(tuple(schema["required"]), constants.OUTCOME_REQUIRED)
        usage = schema["properties"]["usage"]
        self.assertEqual(tuple(usage["required"]), constants.USAGE_REQUIRED)
        self.assertEqual(
            set(usage["properties"]),
            set(constants.USAGE_REQUIRED) | set(constants.USAGE_OPTIONAL),
        )
        result = schema["properties"]["result"]
        self.assertEqual(tuple(result["required"]), constants.RESULT_REQUIRED)

    def test_experiment_fields(self) -> None:
        schema = load("experiment-v1.schema.json")
        self.assertEqual(tuple(schema["required"]), constants.EXPERIMENT_REQUIRED)
        self.assertEqual(
            set(schema["properties"]),
            set(constants.EXPERIMENT_REQUIRED) | set(constants.EXPERIMENT_OPTIONAL),
        )

    def test_enums(self) -> None:
        labels = load("example-v1.schema.json")["$defs"]["labels"]["properties"]
        self.assertEqual(tuple(labels["work_kind"]["enum"]), constants.WORK_KINDS)
        self.assertEqual(tuple(labels["size"]["enum"]), constants.SIZES)
        self.assertEqual(tuple(labels["risk"]["enum"]), constants.RISKS)
        self.assertEqual(
            tuple(labels["intended_sequence"]["items"]["enum"]),
            constants.ROLES,
        )


if __name__ == "__main__":
    unittest.main()
