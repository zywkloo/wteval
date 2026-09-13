#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wteval.executor import (  # noqa: E402
    Agent,
    ManualRunner,
    RunnerResult,
    build_run_record,
    build_schedule,
    gate_result,
    safe_run_id,
)
from wteval.validate import validate_capability_run  # noqa: E402


def _task(task_id: str, origin: str) -> dict:
    return {
        "task_id": task_id,
        "origin": origin,
        "task": {
            "repository": "wtcraft",
            "base_revision": "base-sha-1",
            "oracle_revision": "oracle-sha-1",
            "prompt_fingerprint": f"test:{origin}:{task_id}",
            "verification_declared": True,
            "verification_command": "bash tests/run_all.sh",
            "verification_description": "Synthetic mutation test oracle.",
            "origin": origin,
        },
    }


class ExecutorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.agents = [Agent("codex", "gpt-5.5", "cfg-a"), Agent("claude", "opus-5", "cfg-a")]

    def test_schedule_expands_task_arm_agent(self) -> None:
        tasks = [_task("mut-001-eq->ne", "mutation"), _task("hist-001-contract_case", "history")]
        schedule = build_schedule(tasks, self.agents)
        self.assertEqual(len(schedule), 8)  # 2 tasks x 2 arms x 2 agents
        self.assertEqual({e["arm"] for e in schedule}, {"contract", "no_contract"})
        self.assertEqual(len({e["task_id"] for e in schedule}), 2)

    def test_safe_run_id_strips_invalid_chars(self) -> None:
        run_id = safe_run_id("mut-001-eq->ne", "contract", self.agents[0], 1)
        self.assertNotIn(">", run_id)
        self.assertTrue(run_id.startswith("cap-mut-001-eq--ne-contract-r1-"))

    def test_schedule_identity_includes_model_config_and_repetition(self) -> None:
        task = _task("mut-001-eq->ne", "mutation")
        schedule = build_schedule([task], self.agents[:1], repetitions=2)
        self.assertEqual(len(schedule), 4)
        self.assertEqual(len({entry["run_id"] for entry in schedule}), 4)
        self.assertEqual({entry["repetition"] for entry in schedule}, {1, 2})

    def test_schedule_rejects_duplicate_task_identity(self) -> None:
        task = _task("mut-001-eq->ne", "mutation")
        with self.assertRaisesRegex(ValueError, "duplicate run identities"):
            build_schedule([task, task], self.agents[:1])

    def test_gate_result_maps_exit_codes(self) -> None:
        self.assertEqual(gate_result(0), "pass")
        self.assertEqual(gate_result(2), "fail")

    def test_build_run_record_passes_schema(self) -> None:
        task = _task("mut-001-eq->ne", "mutation")
        entry = build_schedule([task], [self.agents[0]], arms=("contract",))[0]
        record = build_run_record(
            entry,
            RunnerResult(usage={"source": "fixture", "source_confidence": "reported"}),
            check_exit=0,
            verify_exit=2,
            created_at="2026-09-10T12:00:00Z",
        )
        self.assertEqual(record["result"]["check"], "pass")
        self.assertEqual(record["result"]["verify"], "fail")
        self.assertEqual(record["repetition"], 1)
        self.assertEqual(validate_capability_run(record), [])

    def test_manual_runner_returns_no_usage(self) -> None:
        runner = ManualRunner()
        result = runner.run("/tmp/ws", "prompt", {})
        self.assertTrue(result.ok)
        self.assertIsNone(result.usage)


if __name__ == "__main__":
    unittest.main()
