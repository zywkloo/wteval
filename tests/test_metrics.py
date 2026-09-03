#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest

ROOT = __import__("pathlib").Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wteval.metrics import (  # noqa: E402
    adjacent_tolerant_accuracy,
    classification_metrics,
    expected_calibration_error,
    forecast_metrics,
    macro_f1,
    recommendation_metrics,
)


class MetricsTests(unittest.TestCase):
    def test_macro_f1_perfect(self) -> None:
        labels = ("a", "b")
        self.assertEqual(macro_f1(["a", "b"], ["a", "b"], labels), 1.0)

    def test_macro_f1_all_wrong(self) -> None:
        labels = ("a", "b")
        self.assertEqual(macro_f1(["a", "a"], ["b", "b"], labels), 0.0)

    def test_adjacent_size_tolerance(self) -> None:
        index = {"xs": 0, "s": 1, "m": 2}
        self.assertEqual(
            adjacent_tolerant_accuracy(["s", "s"], ["xs", "m"], index),
            1.0,
        )
        self.assertEqual(
            adjacent_tolerant_accuracy(["xs"], ["m"], index),
            0.0,
        )

    def test_brier_and_ece_known_values(self) -> None:
        examples = [
            {"labels": {"work_kind": "execution", "size": "s", "risk": "low", "should_abstain": False}},
            {"labels": {"work_kind": "planning", "size": "m", "risk": "high", "should_abstain": False}},
        ]
        predictions = [
            {
                "classification": {
                    "work_kind": "execution",
                    "size": "s",
                    "risk": "low",
                    "confidence": 1.0,
                    "abstain": False,
                },
                "abstain": False,
            },
            {
                "classification": {
                    "work_kind": "planning",
                    "size": "m",
                    "risk": "high",
                    "confidence": 1.0,
                    "abstain": False,
                },
                "abstain": False,
            },
        ]
        scores = classification_metrics(examples, predictions)
        self.assertEqual(scores["confidence"]["brier"], 0.0)
        self.assertEqual(expected_calibration_error([1.0, 1.0], [True, True]), 0.0)

    def test_forecast_coverage(self) -> None:
        examples = [
            {"outcome": {"usage": {"reported_tokens": 10, "subscription_quota_delta": 0.2}}},
            {"outcome": {"usage": {"reported_tokens": 30, "subscription_quota_delta": 0.8}}},
        ]
        predictions = [
            {
                "forecast": {
                    "reported_tokens_p50": 20,
                    "reported_tokens_p90": 40,
                    "subscription_quota_delta_p50": 0.5,
                    "subscription_quota_delta_p90": 0.9,
                    "source_confidence": "inferred",
                }
            },
            {
                "forecast": {
                    "reported_tokens_p50": 20,
                    "reported_tokens_p90": 40,
                    "subscription_quota_delta_p50": 0.5,
                    "subscription_quota_delta_p90": 0.9,
                    "source_confidence": "inferred",
                }
            },
        ]
        scores = forecast_metrics(examples, predictions)
        self.assertEqual(scores["reported_tokens"]["p50_coverage"], 0.5)
        self.assertEqual(scores["reported_tokens"]["p90_coverage"], 1.0)
        self.assertEqual(scores["reported_tokens"]["median_abs_error"], 10.0)

    def test_recommendation_is_observed_only(self) -> None:
        examples = [
            {
                "human_decision": {"status": "accept"},
                "outcome": {
                    "usage": {"subscription_quota_delta": 0.2},
                    "result": {
                        "check": "pass",
                        "verify": "pass",
                        "repair_rounds": 0,
                        "replan": False,
                        "human_completed": True,
                    },
                },
            },
            {
                "human_decision": {"status": "override"},
                "outcome": {
                    "usage": {"subscription_quota_delta": 0.3},
                    "result": {
                        "check": "pass",
                        "verify": "pass",
                        "repair_rounds": 1,
                        "replan": False,
                        "human_completed": True,
                    },
                },
            },
        ]
        scores = recommendation_metrics(examples, [{}, {}])
        self.assertEqual(scores["verify_pass_rate"], 1.0)
        self.assertEqual(scores["first_pass_verified_success"], 0.5)
        self.assertEqual(scores["override_rate"], 0.5)
        self.assertIn("observed route", scores["note"])


if __name__ == "__main__":
    unittest.main()
