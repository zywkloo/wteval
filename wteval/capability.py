"""Deterministic-oracle capability eval.

Scores agent runs against wtcraft check/verify outcomes, grouped by
experimental arm (contract vs no-contract) and agent configuration. This is a
measurement report, not a product-value claim; see docs/capability-eval.md.
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .constants import ARMS
from .validate import format_errors, validate_capability_run


def load_runs(root: Path) -> list[dict[str, Any]]:
    files = sorted(path for path in root.rglob("*.json") if path.is_file())
    if not files:
        raise ValueError(f"no capability run JSON under {root}")
    runs = []
    errors = []
    seen = set()
    for path in files:
        try:
            obj = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{path}: invalid JSON: {exc}")
            continue
        item_errors = validate_capability_run(obj)
        if item_errors:
            errors.append(f"{path}:\n{format_errors(item_errors)}")
            continue
        run_id = obj["run_id"]
        if run_id in seen:
            errors.append(f"{path}: duplicate run_id {run_id}")
            continue
        seen.add(run_id)
        runs.append(obj)
    if errors:
        raise ValueError("\n\n".join(errors))
    return runs


def wilson_interval(success: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion."""
    if n <= 0:
        return (float("nan"), float("nan"))
    p = success / n
    denom = 1.0 + z * z / n
    center = (p + z * z / (2.0 * n)) / denom
    margin = z * math.sqrt((p * (1.0 - p) + z * z / (4.0 * n)) / n) / denom
    return (max(0.0, center - margin), min(1.0, center + margin))


def _agent_key(agent: dict[str, Any]) -> str:
    return f"{agent['endpoint']}/{agent['model']}/{agent['config_version']}"


def _rate(success: int, n: int) -> dict[str, Any]:
    if n <= 0:
        return {"n": 0, "count": 0, "rate": None, "ci95": [None, None]}
    lo, hi = wilson_interval(success, n)
    return {"n": n, "count": success, "rate": success / n, "ci95": [lo, hi]}


def _score_group(runs: list[dict[str, Any]]) -> dict[str, Any]:
    verify_scored = [r for r in runs if r["result"]["verify"] in ("pass", "fail")]
    check_scored = [r for r in runs if r["result"]["check"] in ("pass", "fail")]
    verify_pass = sum(1 for r in runs if r["result"]["verify"] == "pass")
    check_fail = sum(1 for r in runs if r["result"]["check"] == "fail")
    first_pass = sum(
        1
        for r in runs
        if r["result"]["verify"] == "pass"
        and r["result"]["repair_rounds"] == 0
        and r["result"]["replan"] is False
    )
    repair = [r["result"]["repair_rounds"] for r in runs]
    quota = [
        float(r["usage"]["subscription_quota_delta"])
        for r in runs
        if (r.get("usage") or {}).get("subscription_quota_delta") is not None
    ]
    return {
        "n": len(runs),
        "verify_pass": _rate(verify_pass, len(verify_scored)),
        "scope_violation": _rate(check_fail, len(check_scored)),
        "first_pass": _rate(first_pass, len(verify_scored)),
        "mean_repair_rounds": (sum(repair) / len(repair)) if repair else None,
        "quota_consumed": sum(quota),
        "quota_per_verified_task": (sum(quota) / verify_pass) if verify_pass > 0 else None,
        "n_quota_reported": len(quota),
    }


def capability_metrics(runs: list[dict[str, Any]]) -> dict[str, Any]:
    arms: dict[str, Any] = {}
    for arm in ARMS:
        arm_runs = [r for r in runs if r["arm"] == arm]
        if not arm_runs:
            continue
        by_agent: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for run in arm_runs:
            by_agent[_agent_key(run["agent"])].append(run)
        arms[arm] = {
            "n": len(arm_runs),
            "overall": _score_group(arm_runs),
            "agents": {key: _score_group(group) for key, group in by_agent.items()},
        }
    return {"n_runs": len(runs), "arms": arms}


def write_capability_report(
    out_dir: Path,
    metrics: dict[str, Any],
    experiment_id: str = "capability-eval",
) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "experiment_id": experiment_id,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "n_runs": metrics["n_runs"],
        "arms": metrics["arms"],
        "caveats": [
            "Synthetic fixtures do not support product-value claims.",
            "The deterministic oracle proves the declared verification passed, not that the change is semantically correct.",
            "Two-arm comparison is only valid when both arms actually executed the same frozen task (controlled replay).",
            "Small samples produce wide intervals; report intervals, not point estimates.",
            "Quota per verified task uses only runs with reported quota.",
            "Personal run data must stay in datasets/private/.",
        ],
    }
    json_path = out_dir / "report.json"
    md_path = out_dir / "report.md"
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(_render_markdown(payload), encoding="utf-8")
    return json_path, md_path


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# {payload['experiment_id']}",
        "",
        f"- n_runs: {payload['n_runs']}",
        f"- generated_at: {payload['generated_at']}",
        "",
        "## Caveats",
        "",
    ]
    for caveat in payload["caveats"]:
        lines.append(f"- {caveat}")
    lines.append("")
    for arm, arm_report in payload["arms"].items():
        lines.append(f"## {arm} arm")
        lines.append("")
        lines.append(_render_group("overall", arm_report["overall"]))
        lines.append("")
        for key, group in arm_report["agents"].items():
            lines.append(_render_group(key, group))
            lines.append("")
    return "\n".join(lines) + "\n"


def _render_group(name: str, group: dict[str, Any]) -> str:
    def fmt_rate(label: str, rate: dict[str, Any]) -> str:
        if rate["n"] == 0:
            return f"- {label}: no scored runs"
        lo, hi = rate["ci95"]
        return (
            f"- {label}: `{rate['rate']:.3f}` ({rate['count']}/{rate['n']}) "
            f"95% CI `[{lo:.3f}, {hi:.3f}]`"
        )

    lines = [f"### {name}", "", f"- n: {group['n']}"]
    lines.append(fmt_rate("verify pass rate", group["verify_pass"]))
    lines.append(fmt_rate("scope violation rate", group["scope_violation"]))
    lines.append(fmt_rate("first-pass verified rate", group["first_pass"]))
    if group["mean_repair_rounds"] is not None:
        lines.append(f"- mean repair rounds: `{group['mean_repair_rounds']:.3f}`")
    else:
        lines.append("- mean repair rounds: null")
    if group["quota_per_verified_task"] is not None:
        lines.append(
            f"- quota per verified task: `{group['quota_per_verified_task']:.4f}` "
            f"(from {group['n_quota_reported']} quota-reported runs)"
        )
    else:
        lines.append("- quota per verified task: null (no verified runs)")
    return "\n".join(lines)
