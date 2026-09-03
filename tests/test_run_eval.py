#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wteval.run import run_experiment  # noqa: E402


class RunEvalTests(unittest.TestCase):
    def test_smoke_experiment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = run_experiment(
                ROOT / "experiments" / "000-harness-smoke" / "experiment.json",
                ROOT / "tests" / "fixtures" / "examples",
                Path(tmp),
            )
            self.assertEqual(result["n_train"], 6)
            self.assertEqual(result["n_eval"], 4)
            keyword_f1 = result["scores"]["keyword"]["classification"]["work_kind"]["accuracy"]
            default_f1 = result["scores"]["always_default"]["classification"]["work_kind"]["accuracy"]
            majority_f1 = result["scores"]["majority"]["classification"]["work_kind"]["accuracy"]
            self.assertGreater(keyword_f1, default_f1)
            self.assertGreater(keyword_f1, majority_f1)
            self.assertEqual(keyword_f1, 0.75)
            self.assertEqual(
                result["scores"]["keyword"]["classification"]["abstain"]["accuracy"],
                1.0,
            )
            self.assertIn("observed route", result["scores"]["keyword"]["recommendation"]["note"])
            report = json.loads(Path(result["report_json"]).read_text(encoding="utf-8"))
            self.assertEqual(report["experiment_id"], "000-harness-smoke")
            self.assertTrue(Path(result["report_md"]).is_file())


if __name__ == "__main__":
    unittest.main()
