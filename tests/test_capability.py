#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wteval.capability import capability_metrics, load_runs, wilson_interval  # noqa: E402
from wteval.validate import validate_capability_run  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures" / "runs"


class CapabilityTests(unittest.TestCase):
    def test_fixtures_load(self) -> None:
        runs = load_runs(FIXTURES)
        self.assertEqual(len(runs), 8)
        self.assertEqual({r["arm"] for r in runs}, {"contract", "no_contract"})

    def test_unknown_field_rejected(self) -> None:
        run = copy.deepcopy(load_runs(FIXTURES)[0])
        run["secret_prompt"] = "do not store this"
        errors = validate_capability_run(run)
        self.assertTrue(any("unknown fields" in item for item in errors))

    def test_invalid_arm_rejected(self) -> None:
        run = copy.deepcopy(load_runs(FIXTURES)[0])
        run["arm"] = "with_contract"
        errors = validate_capability_run(run)
        self.assertTrue(any("arm" in item for item in errors))

    def test_duplicate_run_identity_rejected_even_with_distinct_ids(self) -> None:
        first = load_runs(FIXTURES)[0]
        second = copy.deepcopy(first)
        second["run_id"] = "distinct-run-id"
        duplicate_dir = self._write_runs([first, second])
        with self.assertRaisesRegex(ValueError, "duplicate run identity"):
            load_runs(duplicate_dir)

    def test_metrics_group_by_arm(self) -> None:
        metrics = capability_metrics(load_runs(FIXTURES))
        self.assertIn("contract", metrics["arms"])
        self.assertIn("no_contract", metrics["arms"])
        contract = metrics["arms"]["contract"]["overall"]
        no_contract = metrics["arms"]["no_contract"]["overall"]
        self.assertEqual(contract["n"], 4)
        self.assertEqual(no_contract["n"], 4)
        self.assertEqual(contract["verify_pass"]["count"], 3)
        self.assertEqual(no_contract["verify_pass"]["count"], 1)
        self.assertEqual(contract["scope_violation"]["count"], 0)
        self.assertEqual(no_contract["scope_violation"]["count"], 2)

    def test_wilson_interval_bounds(self) -> None:
        lo, hi = wilson_interval(3, 4)
        self.assertGreaterEqual(lo, 0.0)
        self.assertLessEqual(hi, 1.0)
        self.assertLessEqual(lo, hi)

    def test_verification_command_fields_validate(self) -> None:
        run = copy.deepcopy(load_runs(FIXTURES)[0])
        run["task"]["verification_command"] = "bash tests/run_all.sh"
        run["task"]["verification_description"] = "synthetic oracle"
        self.assertEqual(validate_capability_run(run), [])

    def test_verification_command_must_be_string(self) -> None:
        run = copy.deepcopy(load_runs(FIXTURES)[0])
        run["task"]["verification_command"] = 123
        errors = validate_capability_run(run)
        self.assertTrue(any("verification_command" in item for item in errors))

    def test_quota_per_verified_task_uses_observed_success_cohort(self) -> None:
        runs = load_runs(FIXTURES)
        runs[0]["usage"] = {"source": "unavailable", "source_confidence": "unavailable"}
        report = capability_metrics(runs)["arms"]["contract"]["overall"]
        self.assertEqual(report["n_quota_reported"], 3)
        self.assertEqual(report["n_quota_verified"], 2)
        self.assertAlmostEqual(report["quota_consumed"], 0.20)
        self.assertAlmostEqual(report["quota_per_verified_task"], 0.1)
        self.assertEqual(report["quota_coverage"], 0.75)

    def _write_runs(self, runs: list[dict]) -> Path:
        import tempfile

        root = Path(tempfile.mkdtemp())
        for index, run in enumerate(runs):
            (root / f"run-{index}.json").write_text(json.dumps(run), encoding="utf-8")
        self.addCleanup(lambda: __import__("shutil").rmtree(root))
        return root


if __name__ == "__main__":
    unittest.main()
