"""Metrics for classification, forecast calibration, and recommendation outcomes.

Do not report savings versus an unexecuted route. One observed task cannot
prove that another candidate would have failed or cost more.
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any, Iterable, Sequence

from .constants import RISKS, SIZES, WORK_KINDS

SIZE_INDEX = {label: index for index, label in enumerate(SIZES)}
RISK_INDEX = {label: index for index, label in enumerate(RISKS)}


def score_system(
    examples: Sequence[dict[str, Any]],
    predictions: Sequence[dict[str, Any]],
    metric_groups: Sequence[str],
) -> dict[str, Any]:
    if len(examples) != len(predictions):
        raise ValueError("examples and predictions must be aligned")
    report: dict[str, Any] = {"n": len(examples)}
    if "classification" in metric_groups:
        report["classification"] = classification_metrics(examples, predictions)
    if "forecast" in metric_groups:
        report["forecast"] = forecast_metrics(examples, predictions)
    if "recommendation" in metric_groups:
        report["recommendation"] = recommendation_metrics(examples, predictions)
    return report


def classification_metrics(
    examples: Sequence[dict[str, Any]],
    predictions: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    work_true = [item["labels"]["work_kind"] for item in examples]
    work_pred = [item["classification"]["work_kind"] for item in predictions]
    size_true = [item["labels"]["size"] for item in examples]
    size_pred = [item["classification"]["size"] for item in predictions]
    risk_true = [item["labels"]["risk"] for item in examples]
    risk_pred = [item["classification"]["risk"] for item in predictions]
    abstain_true = [bool(item["labels"].get("should_abstain")) for item in examples]
    abstain_pred = [
        bool(item.get("abstain") or item["classification"].get("abstain"))
        for item in predictions
    ]
    confidences = [float(item["classification"]["confidence"]) for item in predictions]
    correct = [truth == pred for truth, pred in zip(work_true, work_pred)]
    return {
        "work_kind": {
            "macro_f1": macro_f1(work_true, work_pred, WORK_KINDS),
            "accuracy": mean(correct),
            "per_class": per_class_scores(work_true, work_pred, WORK_KINDS),
            "confusion": confusion_matrix(work_true, work_pred, WORK_KINDS),
        },
        "size": {
            "macro_f1": macro_f1(size_true, size_pred, SIZES),
            "adjacent_tolerant_accuracy": adjacent_tolerant_accuracy(
                size_true, size_pred, SIZE_INDEX
            ),
        },
        "risk": {
            "macro_f1": macro_f1(risk_true, risk_pred, RISKS),
            "adjacent_tolerant_accuracy": adjacent_tolerant_accuracy(
                risk_true, risk_pred, RISK_INDEX
            ),
        },
        "confidence": {
            "brier": mean((conf - (1.0 if hit else 0.0)) ** 2 for conf, hit in zip(confidences, correct)),
            "ece": expected_calibration_error(confidences, correct),
        },
        "abstain": {
            "accuracy": mean(t == p for t, p in zip(abstain_true, abstain_pred)),
            "predicted_rate": mean(abstain_pred),
            "label_rate": mean(abstain_true),
        },
    }


def forecast_metrics(
    examples: Sequence[dict[str, Any]],
    predictions: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "reported_tokens": _scalar_forecast(
            actuals=[_usage_field(item, "reported_tokens") for item in examples],
            p50s=[_forecast_field(item, "reported_tokens_p50") for item in predictions],
            p90s=[_forecast_field(item, "reported_tokens_p90") for item in predictions],
        ),
        "subscription_quota_delta": _scalar_forecast(
            actuals=[_usage_field(item, "subscription_quota_delta") for item in examples],
            p50s=[_forecast_field(item, "subscription_quota_delta_p50") for item in predictions],
            p90s=[_forecast_field(item, "subscription_quota_delta_p90") for item in predictions],
        ),
        "unavailable_rate": mean(
            item["forecast"].get("source_confidence") == "unavailable" for item in predictions
        ),
    }


def recommendation_metrics(
    examples: Sequence[dict[str, Any]],
    predictions: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    del predictions
    scored = [item for item in examples if item.get("outcome")]
    if not scored:
        return {"n_with_outcome": 0}
    verify_pass = [item["outcome"]["result"]["verify"] == "pass" for item in scored]
    first_pass = [
        item["outcome"]["result"]["verify"] == "pass"
        and item["outcome"]["result"]["repair_rounds"] == 0
        and item["outcome"]["result"]["replan"] is False
        for item in scored
    ]
    completed = [bool(item["outcome"]["result"]["human_completed"]) for item in scored]
    repair_rounds = [item["outcome"]["result"]["repair_rounds"] for item in scored]
    overrides = [
        (item.get("human_decision") or {}).get("status") == "override" for item in scored
    ]
    quota_values = [
        item["outcome"]["usage"].get("subscription_quota_delta")
        for item in scored
        if item["outcome"]["usage"].get("subscription_quota_delta") not in (None, 0)
    ]
    completed_count = sum(1 for item in scored if item["outcome"]["result"]["human_completed"])
    quota_sum = sum(float(value) for value in quota_values)
    return {
        "n_with_outcome": len(scored),
        "verify_pass_rate": mean(verify_pass),
        "first_pass_verified_success": mean(first_pass),
        "human_completed_rate": mean(completed),
        "mean_repair_rounds": mean(repair_rounds),
        "override_rate": mean(overrides),
        "completed_per_quota_unit": (
            completed_count / quota_sum if quota_sum > 0 else None
        ),
        "note": (
            "These scores describe the observed route only. They are not a "
            "counterfactual comparison against unexecuted alternatives."
        ),
    }


def macro_f1(y_true: Sequence[str], y_pred: Sequence[str], labels: Sequence[str]) -> float:
    scores = per_class_scores(y_true, y_pred, labels)
    values = [item["f1"] for item in scores.values() if item["support"] > 0]
    return mean(values) if values else 0.0


def per_class_scores(
    y_true: Sequence[str],
    y_pred: Sequence[str],
    labels: Sequence[str],
) -> dict[str, dict[str, float]]:
    result = {}
    for label in labels:
        tp = sum(1 for truth, pred in zip(y_true, y_pred) if truth == label and pred == label)
        fp = sum(1 for truth, pred in zip(y_true, y_pred) if truth != label and pred == label)
        fn = sum(1 for truth, pred in zip(y_true, y_pred) if truth == label and pred != label)
        support = sum(1 for truth in y_true if truth == label)
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (
            0.0
            if precision + recall == 0
            else 2 * precision * recall / (precision + recall)
        )
        result[label] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": float(support),
        }
    return result


def confusion_matrix(
    y_true: Sequence[str],
    y_pred: Sequence[str],
    labels: Sequence[str],
) -> dict[str, dict[str, int]]:
    matrix = {label: {other: 0 for other in labels} for label in labels}
    for truth, pred in zip(y_true, y_pred):
        if truth in matrix and pred in matrix[truth]:
            matrix[truth][pred] += 1
    return matrix


def adjacent_tolerant_accuracy(
    y_true: Sequence[str],
    y_pred: Sequence[str],
    index: dict[str, int],
) -> float:
    hits = []
    for truth, pred in zip(y_true, y_pred):
        if truth not in index or pred not in index:
            hits.append(False)
            continue
        hits.append(abs(index[truth] - index[pred]) <= 1)
    return mean(hits)


def expected_calibration_error(
    confidences: Sequence[float],
    correct: Sequence[bool],
    bins: int = 5,
) -> float:
    if not confidences:
        return 0.0
    bucket_total: dict[int, int] = defaultdict(int)
    bucket_hit: dict[int, int] = defaultdict(int)
    bucket_conf: dict[int, float] = defaultdict(float)
    for confidence, hit in zip(confidences, correct):
        capped = min(max(confidence, 0.0), 0.999999)
        bucket = min(bins - 1, int(capped * bins))
        bucket_total[bucket] += 1
        bucket_hit[bucket] += 1 if hit else 0
        bucket_conf[bucket] += confidence
    total = len(confidences)
    error = 0.0
    for bucket, count in bucket_total.items():
        acc = bucket_hit[bucket] / count
        conf = bucket_conf[bucket] / count
        error += (count / total) * abs(acc - conf)
    return error


def _scalar_forecast(
    actuals: Sequence[float | None],
    p50s: Sequence[float | None],
    p90s: Sequence[float | None],
) -> dict[str, Any]:
    pairs_p50 = [
        (actual, pred)
        for actual, pred in zip(actuals, p50s)
        if actual is not None and pred is not None
    ]
    pairs_p90 = [
        (actual, pred)
        for actual, pred in zip(actuals, p90s)
        if actual is not None and pred is not None
    ]
    abs_errors = [abs(actual - pred) for actual, pred in pairs_p50]
    rel_errors = [
        abs(actual - pred) / actual for actual, pred in pairs_p50 if actual > 0
    ]
    log_errors = [
        abs(math.log1p(actual) - math.log1p(pred))
        for actual, pred in pairs_p50
        if actual >= 0 and pred >= 0
    ]
    widths = [max(0.0, p90 - p50) for p50, p90 in zip(p50s, p90s) if p50 is not None and p90 is not None]
    return {
        "n": len(pairs_p50),
        "median_abs_error": median(abs_errors),
        "median_relative_error": median(rel_errors),
        "median_log_error": median(log_errors),
        "p50_coverage": mean(actual <= pred for actual, pred in pairs_p50) if pairs_p50 else None,
        "p90_coverage": mean(actual <= pred for actual, pred in pairs_p90) if pairs_p90 else None,
        "median_p50_to_p90_width": median(widths),
        "missing_actual_rate": mean(value is None for value in actuals),
        "missing_forecast_rate": mean(value is None for value in p50s),
    }


def _usage_field(example: dict[str, Any], field: str) -> float | None:
    outcome = example.get("outcome") or {}
    value = (outcome.get("usage") or {}).get(field)
    return None if value is None else float(value)


def _forecast_field(prediction: dict[str, Any], field: str) -> float | None:
    value = (prediction.get("forecast") or {}).get(field)
    return None if value is None else float(value)


def mean(values: Iterable[Any]) -> float:
    items = list(values)
    if not items:
        return 0.0
    return float(sum(items)) / len(items)


def median(values: Sequence[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[mid])
    return (ordered[mid - 1] + ordered[mid]) / 2.0
