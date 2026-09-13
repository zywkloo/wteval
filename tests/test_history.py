#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wteval.history import build_task  # noqa: E402


class HistoryTests(unittest.TestCase):
    def test_build_task_maps_unit_fields(self) -> None:
        unit = {
            "repo": "wtcraft",
            "kind": "contract_case",
            "verification": "tests/contracts/policy-envelope/authorized-change",
            "base_sha": "base1",
            "oracle_sha": "oracle1",
            "subject": "add contract case",
            "author_date": "2026-07-01T00:00:00Z",
        }
        task = build_task(unit, 1)
        self.assertEqual(task["task_id"], "hist-001-contract_case")
        self.assertEqual(task["origin"], "history")
        self.assertEqual(task["task"]["repository"], "wtcraft")
        self.assertEqual(task["task"]["base_revision"], "base1")
        self.assertEqual(task["task"]["oracle_revision"], "oracle1")
        self.assertEqual(
            task["task"]["verification_description"],
            "History verification unit: tests/contracts/policy-envelope/authorized-change",
        )
        self.assertEqual(task["task"]["origin"], "history")
        self.assertEqual(task["verification_unit"]["kind"], "contract_case")


if __name__ == "__main__":
    unittest.main()
