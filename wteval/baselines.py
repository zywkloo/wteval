"""Deterministic baselines every advisor version must beat."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any, Callable

from .constants import SIZES, WORK_KINDS, RISKS

DEFAULT_ROUTE = {
    "role": "executor",
    "endpoint": "configured-default",
    "model_tier": "balanced-coding",
    "reasoning_tier": "medium",
}

KEYWORD_WORK_KIND = (
    ("finishing", r"\b(handoff|commit message|pr text|cleanup|archive)\b"),
    ("repair", r"\b(repair|failed check|failing test|address findings)\b"),
    ("verification", r"\b(review|verify|verification|test the diff)\b"),
    ("planning", r"\b(design|architecture|plan|spec|sequence)\b"),
    ("discovery", r"\b(understand|explore|unfamiliar|how does)\b"),
    ("execution", r"\b(implement|fix|add|bug|feature)\b"),
)

KEYWORD_SIZE = (
    ("xs", r"\b(typo|one-liner|nit)\b"),
    ("xl", r"\b(rewrite|migrate platform)\b"),
    ("l", r"\b(migrate|multi-module)\b"),
    ("m", r"\b(refactor|module|adapter)\b"),
    ("s", r"\b(bug|small|bounded)\b"),
)

KEYWORD_RISK = (
    ("high", r"\b(auth|security|policy|credentials)\b"),
    ("low", r"\b(docs|comment|typo)\b"),
)


def always_default(_train: list[dict[str, Any]], example: dict[str, Any]) -> dict[str, Any]:
    del example
    return _prediction(
        work_kind="execution",
        size="s",
        risk="medium",
        sequence=["executor"],
        confidence=1.0,
        classifier_version="always-default-v1",
        forecast=_unavailable_forecast(),
    )


def majority(train: list[dict[str, Any]], example: dict[str, Any]) -> dict[str, Any]:
    del example
    work_kind = _mode(item["labels"]["work_kind"] for item in train) or "execution"
    size = _mode(item["labels"]["size"] for item in train) or "s"
    risk = _mode(item["labels"]["risk"] for item in train) or "medium"
    sequence = _mode(tuple(item["labels"]["intended_sequence"]) for item in train) or ("executor",)
    tokens = [item["outcome"]["usage"].get("reported_tokens") for item in train if _has_tokens(item)]
    quota = [
        item["outcome"]["usage"].get("subscription_quota_delta")
        for item in train
        if _has_quota(item)
    ]
    return _prediction(
        work_kind=work_kind,
        size=size,
        risk=risk,
        sequence=list(sequence),
        confidence=0.5,
        classifier_version="majority-v1",
        forecast=_quantile_forecast(tokens, quota),
    )


def keyword(_train: list[dict[str, Any]], example: dict[str, Any]) -> dict[str, Any]:
    text = (example.get("features") or {}).get("feature_snapshot") or ""
    work_kind = _first_match(text, KEYWORD_WORK_KIND, "execution")
    size = _first_match(text, KEYWORD_SIZE, "s")
    risk = _first_match(text, KEYWORD_RISK, "medium")
    sequence = {
        "discovery": ["planner"],
        "planning": ["planner"],
        "execution": ["executor", "verifier"],
        "verification": ["verifier"],
        "repair": ["executor", "verifier"],
        "finishing": ["finisher"],
    }[work_kind]
    abstain = not bool(text.strip())
    confidence = 0.35 if abstain else 0.6
    return _prediction(
        work_kind=work_kind,
        size=size,
        risk=risk,
        sequence=sequence,
        confidence=confidence,
        classifier_version="keyword-v1",
        forecast=_unavailable_forecast(),
        abstain=abstain,
    )


SYSTEMS: dict[str, Callable[[list[dict[str, Any]], dict[str, Any]], dict[str, Any]]] = {
    "always_default": always_default,
    "majority": majority,
    "keyword": keyword,
}


def predict_system(
    system_id: str,
    train: list[dict[str, Any]],
    example: dict[str, Any],
) -> dict[str, Any]:
    if system_id.startswith("recorded:"):
        key = system_id.split(":", 1)[1]
        recorded = (example.get("predictions") or {}).get(key)
        if recorded is None and key == "decision":
            recorded = _prediction_from_decision(example.get("decision"))
        if recorded is None:
            raise KeyError(f"{system_id} missing on example {example.get('example_id')}")
        copy = dict(recorded)
        copy["system_id"] = system_id
        return copy
    if system_id not in SYSTEMS:
        raise KeyError(f"unknown system: {system_id}")
    prediction = SYSTEMS[system_id](train, example)
    prediction["system_id"] = system_id
    return prediction


def _prediction_from_decision(decision: dict[str, Any] | None) -> dict[str, Any] | None:
    if not decision:
        return None
    return {
        "classification": decision["classification"],
        "recommended_route": decision["recommended_route"],
        "forecast": decision["forecast"],
        "reason_codes": decision.get("reason_codes") or [],
        "abstain": bool(decision.get("classification", {}).get("abstain")),
    }


def _prediction(
    work_kind: str,
    size: str,
    risk: str,
    sequence: list[str],
    confidence: float,
    classifier_version: str,
    forecast: dict[str, Any],
    abstain: bool = False,
) -> dict[str, Any]:
    if work_kind not in WORK_KINDS or size not in SIZES or risk not in RISKS:
        raise ValueError("baseline produced an invalid label")
    return {
        "classification": {
            "work_kind": work_kind,
            "size": size,
            "risk": risk,
            "confidence": confidence,
            "recommended_sequence": sequence,
            "abstain": abstain,
            "classifier_version": classifier_version,
        },
        "recommended_route": dict(DEFAULT_ROUTE),
        "forecast": forecast,
        "reason_codes": [classifier_version],
        "abstain": abstain,
    }


def _unavailable_forecast() -> dict[str, Any]:
    return {
        "reported_tokens_p50": None,
        "reported_tokens_p90": None,
        "subscription_quota_delta_p50": None,
        "subscription_quota_delta_p90": None,
        "source_confidence": "unavailable",
        "forecast_version": "cold-start-v1",
    }


def _quantile_forecast(tokens: list[Any], quota: list[Any]) -> dict[str, Any]:
    token_values = [float(value) for value in tokens if value is not None]
    quota_values = [float(value) for value in quota if value is not None]
    if not token_values and not quota_values:
        return _unavailable_forecast()
    return {
        "reported_tokens_p50": _quantile(token_values, 0.5),
        "reported_tokens_p90": _quantile(token_values, 0.9),
        "subscription_quota_delta_p50": _quantile(quota_values, 0.5),
        "subscription_quota_delta_p90": _quantile(quota_values, 0.9),
        "source_confidence": "inferred",
        "forecast_version": "train-quantile-v1",
    }


def _quantile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * q))))
    return ordered[index]


def _mode(values: Any) -> Any:
    counts = Counter(values)
    if not counts:
        return None
    return counts.most_common(1)[0][0]


def _first_match(text: str, rules: tuple[tuple[str, str], ...], default: str) -> str:
    lowered = text.lower()
    for label, pattern in rules:
        if re.search(pattern, lowered):
            return label
    return default


def _has_tokens(example: dict[str, Any]) -> bool:
    outcome = example.get("outcome") or {}
    usage = outcome.get("usage") or {}
    return usage.get("reported_tokens") is not None


def _has_quota(example: dict[str, Any]) -> bool:
    outcome = example.get("outcome") or {}
    usage = outcome.get("usage") or {}
    return usage.get("subscription_quota_delta") is not None
