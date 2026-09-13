"""Deterministic two-arm capability executor (interface + stub).

Consumes the unified task pool (mutation + history), expands each task into a
run schedule across arms x agent configs, and assembles capability-run records.
Only the ``Runner`` seam (the agent driver) is non-deterministic; everything
else — worktree setup, check/verify capture, record assembly — is deterministic.

A real runner (Codex/Claude/...) implements ``Runner.run``. ``ManualRunner`` is
a no-op stub for smoke-testing the record pipeline without an agent.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Protocol, Sequence

ARMS = ("contract", "no_contract")

# capability-run run_id allows [A-Za-z0-9._:-] only; drop anything else.
_RUN_ID_INVALID = re.compile(r"[^A-Za-z0-9._:-]")


@dataclass
class Agent:
    endpoint: str
    model: str
    config_version: str


@dataclass
class RunnerResult:
    ok: bool = True
    usage: dict[str, Any] | None = None
    repair_rounds: int = 0
    replan: bool = False
    notes: str = ""


class Runner(Protocol):
    """The agent seam. Runs one task in a prepared workspace and reports usage."""

    def run(self, workspace: str, prompt: str, task: dict[str, Any]) -> RunnerResult:
        ...


class ManualRunner:
    """No-op runner: leaves the workspace unchanged, reports no usage."""

    def run(self, workspace: str, prompt: str, task: dict[str, Any]) -> RunnerResult:
        return RunnerResult(ok=True, notes="manual runner: no agent executed")


def build_schedule(
    tasks: Sequence[dict[str, Any]],
    agents: Sequence[Agent],
    arms: Sequence[str] = ARMS,
    repetitions: int = 1,
) -> list[dict[str, Any]]:
    """Expand tasks into a collision-free task x arm x agent x repeat schedule."""
    if repetitions < 1:
        raise ValueError("repetitions must be >= 1")
    schedule = []
    for task in tasks:
        for arm in arms:
            for agent in agents:
                for repetition in range(1, repetitions + 1):
                    entry = {
                        "task_id": task["task_id"],
                        "origin": task["origin"],
                        "arm": arm,
                        "repetition": repetition,
                        "agent": asdict(agent),
                        "task": task["task"],
                    }
                    entry["run_id"] = safe_run_id(
                        entry["task_id"], arm, agent, repetition
                    )
                    schedule.append(entry)
    run_ids = [entry["run_id"] for entry in schedule]
    if len(run_ids) != len(set(run_ids)):
        raise ValueError("schedule contains duplicate run identities")
    return schedule


def safe_run_id(task_id: str, arm: str, agent: Agent | dict[str, str], repetition: int) -> str:
    """Build a stable ID unique to task, arm, endpoint, model, config, and repeat."""
    if repetition < 1:
        raise ValueError("repetition must be >= 1")
    agent_data = asdict(agent) if isinstance(agent, Agent) else agent
    identity = "\x1f".join(
        (task_id, arm, agent_data["endpoint"], agent_data["model"], agent_data["config_version"], str(repetition))
    )
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]
    safe_task = _RUN_ID_INVALID.sub("-", task_id).strip("-.")[:56] or "task"
    safe_arm = _RUN_ID_INVALID.sub("-", arm).strip("-.")[:20] or "arm"
    safe_repetition = str(repetition)[:8]
    return f"cap-{safe_task}-{safe_arm}-r{safe_repetition}-{digest}"


def gate_result(exit_code: int) -> str:
    """Map a check/verify exit code to the capability-run gate enum."""
    return "pass" if exit_code == 0 else "fail"


def build_run_record(
    entry: dict[str, Any],
    runner_result: RunnerResult,
    check_exit: int,
    verify_exit: int,
    created_at: str,
) -> dict[str, Any]:
    """Assemble a capability-run record from a schedule entry + outcomes."""
    return {
        "schema_version": 1,
        "run_id": entry.get("run_id")
        or safe_run_id(entry["task_id"], entry["arm"], entry["agent"], entry["repetition"]),
        "task_id": entry["task_id"],
        "created_at": created_at,
        "arm": entry["arm"],
        "repetition": entry["repetition"],
        "agent": entry["agent"],
        "task": entry["task"],
        "result": {
            "check": gate_result(check_exit),
            "verify": gate_result(verify_exit),
            "repair_rounds": runner_result.repair_rounds,
            "replan": runner_result.replan,
        },
        "usage": runner_result.usage
        or {"source": "unavailable", "source_confidence": "unavailable"},
        "notes": runner_result.notes or None,
    }


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
