"""Assemble a local experiment report. Optional hosted backends are later."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def write_report(
    out_dir: Path,
    experiment: dict[str, Any],
    scores: dict[str, Any],
    n_train: int,
    n_eval: int,
) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "experiment_id": experiment["experiment_id"],
        "dataset": experiment["dataset"],
        "split": experiment["split"],
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "n_train": n_train,
        "n_eval": n_eval,
        "systems": scores,
        "caveats": [
            "Synthetic fixtures do not support product-value claims.",
            "Observed recommendation metrics are not counterfactual savings.",
            "Personal labeled data must stay in datasets/private/.",
        ],
    }
    json_path = out_dir / "report.json"
    md_path = out_dir / "report.md"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(payload), encoding="utf-8")
    return json_path, md_path


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# {payload['experiment_id']}",
        "",
        f"- dataset: `{payload['dataset']}`",
        f"- split: `{payload['split']}`",
        f"- train examples: {payload['n_train']}",
        f"- eval examples: {payload['n_eval']}",
        f"- generated_at: {payload['generated_at']}",
        "",
        "## Caveats",
        "",
    ]
    for caveat in payload["caveats"]:
        lines.append(f"- {caveat}")
    lines.append("")
    for system_id, score in payload["systems"].items():
        lines.append(f"## {system_id}")
        lines.append("")
        classification = score.get("classification")
        if classification:
            work = classification["work_kind"]
            lines.append(
                f"- work_kind macro F1: `{work['macro_f1']:.3f}` accuracy: `{work['accuracy']:.3f}`"
            )
            lines.append(
                f"- size adjacent-tolerant accuracy: `{classification['size']['adjacent_tolerant_accuracy']:.3f}`"
            )
            lines.append(
                f"- risk adjacent-tolerant accuracy: `{classification['risk']['adjacent_tolerant_accuracy']:.3f}`"
            )
            lines.append(f"- confidence Brier: `{classification['confidence']['brier']:.3f}`")
            lines.append(f"- abstain accuracy: `{classification['abstain']['accuracy']:.3f}`")
        forecast = score.get("forecast")
        if forecast:
            tokens = forecast["reported_tokens"]
            lines.append(
                f"- token forecast n: `{tokens['n']}` median AE: `{_fmt(tokens['median_abs_error'])}` "
                f"p50 coverage: `{_fmt(tokens['p50_coverage'])}` p90 coverage: `{_fmt(tokens['p90_coverage'])}`"
            )
            lines.append(f"- forecast unavailable rate: `{forecast['unavailable_rate']:.3f}`")
        recommendation = score.get("recommendation")
        if recommendation:
            if recommendation.get("n_with_outcome", 0) == 0:
                lines.append("- recommendation: no outcomes attached")
            else:
                lines.append(
                    f"- verify pass: `{recommendation['verify_pass_rate']:.3f}` "
                    f"first-pass verified: `{recommendation['first_pass_verified_success']:.3f}` "
                    f"override rate: `{recommendation['override_rate']:.3f}`"
                )
        lines.append("")
    return "\n".join(lines) + "\n"


def _fmt(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)
