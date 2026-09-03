"""Hand-written v1 validators.

JSON Schema files document the contract. This module is what the batch runner
executes, so a missing jsonschema dependency cannot silently skip checks.
"""

from __future__ import annotations

import re
from typing import Any, Iterable, Mapping, Sequence

from .constants import (
    ADVISOR_POLICIES,
    ADVISOR_ROUTE_REQUIRED,
    CLASSIFICATION_OPTIONAL,
    CLASSIFICATION_REQUIRED,
    DECISION_OPTIONAL,
    DECISION_REQUIRED,
    EXAMPLE_OPTIONAL,
    EXAMPLE_REQUIRED,
    EXPERIMENT_OPTIONAL,
    EXPERIMENT_REQUIRED,
    FEATURES_OPTIONAL,
    FEATURES_REQUIRED,
    FORECAST_OPTIONAL,
    FORECAST_REQUIRED,
    GATE_RESULTS,
    HUMAN_DECISION_OPTIONAL,
    HUMAN_DECISION_REQUIRED,
    HUMAN_DECISIONS,
    ID_PATTERN,
    LABELS_OPTIONAL,
    LABELS_REQUIRED,
    METRIC_GROUPS,
    OUTCOME_REQUIRED,
    PREDICTION_OPTIONAL,
    PREDICTION_REQUIRED,
    RESULT_REQUIRED,
    ROLES,
    ROUTE_OPTIONAL,
    ROUTE_REQUIRED,
    SCHEMA_VERSION,
    SIZES,
    SOURCE_CONFIDENCE,
    SPLITS,
    TIMESTAMP_PATTERN,
    USAGE_OPTIONAL,
    USAGE_REQUIRED,
    WORK_KINDS,
    RISKS,
)

_ID_RE = re.compile(ID_PATTERN)
_TS_RE = re.compile(TIMESTAMP_PATTERN)


def validate_example(obj: Any, path: str = "$") -> list[str]:
    errors = _expect_object(obj, path)
    if errors:
        return errors
    errors.extend(_closed_object(obj, path, EXAMPLE_REQUIRED, EXAMPLE_OPTIONAL))
    errors.extend(_const_version(obj, path))
    errors.extend(_id(obj.get("example_id"), f"{path}.example_id"))
    errors.extend(_nonempty_string(obj.get("task_id"), f"{path}.task_id"))
    errors.extend(_timestamp(obj.get("created_at"), f"{path}.created_at"))
    if "split" in obj:
        errors.extend(_enum(obj.get("split"), f"{path}.split", SPLITS))
    errors.extend(validate_features(obj.get("features"), f"{path}.features"))
    errors.extend(validate_labels(obj.get("labels"), f"{path}.labels"))
    if obj.get("decision") is not None:
        errors.extend(validate_decision(obj["decision"], f"{path}.decision"))
    if "predictions" in obj and obj["predictions"] is not None:
        errors.extend(_predictions(obj["predictions"], f"{path}.predictions"))
    if "human_decision" in obj and obj["human_decision"] is not None:
        errors.extend(validate_human_decision(obj["human_decision"], f"{path}.human_decision"))
    if obj.get("outcome") is not None:
        errors.extend(validate_outcome(obj["outcome"], f"{path}.outcome"))
    if "notes" in obj and obj["notes"] is not None:
        errors.extend(_nonempty_string(obj["notes"], f"{path}.notes", allow_empty=True))
    return errors


def validate_features(obj: Any, path: str) -> list[str]:
    errors = _expect_object(obj, path)
    if errors:
        return errors
    errors.extend(_closed_object(obj, path, FEATURES_REQUIRED, FEATURES_OPTIONAL))
    errors.extend(_nonempty_string(obj.get("prompt_fingerprint"), f"{path}.prompt_fingerprint"))
    errors.extend(_nonempty_string(obj.get("features_version"), f"{path}.features_version"))
    if "feature_snapshot" in obj and obj["feature_snapshot"] is not None:
        errors.extend(_nonempty_string(obj["feature_snapshot"], f"{path}.feature_snapshot", allow_empty=True))
    if "repository_bucket" in obj and obj["repository_bucket"] is not None:
        errors.extend(_nonempty_string(obj["repository_bucket"], f"{path}.repository_bucket"))
    if "git_summary" in obj and obj["git_summary"] is not None:
        errors.extend(_nonempty_string(obj["git_summary"], f"{path}.git_summary", allow_empty=True))
    if "task_contract" in obj and obj["task_contract"] is not None:
        errors.extend(_task_contract(obj["task_contract"], f"{path}.task_contract"))
    if "quota" in obj and obj["quota"] is not None:
        errors.extend(_quota(obj["quota"], f"{path}.quota"))
    return errors


def validate_labels(obj: Any, path: str) -> list[str]:
    errors = _expect_object(obj, path)
    if errors:
        return errors
    errors.extend(_closed_object(obj, path, LABELS_REQUIRED, LABELS_OPTIONAL))
    errors.extend(_enum(obj.get("work_kind"), f"{path}.work_kind", WORK_KINDS))
    errors.extend(_enum(obj.get("size"), f"{path}.size", SIZES))
    errors.extend(_enum(obj.get("risk"), f"{path}.risk", RISKS))
    errors.extend(_role_sequence(obj.get("intended_sequence"), f"{path}.intended_sequence"))
    if "should_abstain" in obj and obj["should_abstain"] is not None:
        errors.extend(_bool(obj["should_abstain"], f"{path}.should_abstain"))
    if "labeler" in obj and obj["labeler"] is not None:
        errors.extend(_nonempty_string(obj["labeler"], f"{path}.labeler"))
    if "labeled_at" in obj and obj["labeled_at"] is not None:
        errors.extend(_timestamp(obj["labeled_at"], f"{path}.labeled_at"))
    if "notes" in obj and obj["notes"] is not None:
        errors.extend(_nonempty_string(obj["notes"], f"{path}.notes", allow_empty=True))
    return errors


def validate_decision(obj: Any, path: str) -> list[str]:
    errors = _expect_object(obj, path)
    if errors:
        return errors
    errors.extend(_closed_object(obj, path, DECISION_REQUIRED, DECISION_OPTIONAL))
    errors.extend(_const_version(obj, path))
    errors.extend(_id(obj.get("decision_id"), f"{path}.decision_id"))
    errors.extend(_nonempty_string(obj.get("task_id"), f"{path}.task_id"))
    errors.extend(_timestamp(obj.get("created_at"), f"{path}.created_at"))
    errors.extend(_nonempty_string(obj.get("prompt_fingerprint"), f"{path}.prompt_fingerprint"))
    errors.extend(_nonempty_string(obj.get("features_version"), f"{path}.features_version"))
    errors.extend(_classification(obj.get("classification"), f"{path}.classification"))
    errors.extend(_advisor_route(obj.get("advisor_route"), f"{path}.advisor_route"))
    errors.extend(_route(obj.get("recommended_route"), f"{path}.recommended_route"))
    errors.extend(_forecast(obj.get("forecast"), f"{path}.forecast"))
    errors.extend(_string_list(obj.get("reason_codes"), f"{path}.reason_codes"))
    if "human_decision" in obj and obj["human_decision"] is not None:
        errors.extend(validate_human_decision(obj["human_decision"], f"{path}.human_decision"))
    return errors


def validate_outcome(obj: Any, path: str) -> list[str]:
    errors = _expect_object(obj, path)
    if errors:
        return errors
    errors.extend(_closed_object(obj, path, OUTCOME_REQUIRED, ()))
    errors.extend(_const_version(obj, path))
    errors.extend(_id(obj.get("decision_id"), f"{path}.decision_id"))
    errors.extend(_route(obj.get("actual_route"), f"{path}.actual_route"))
    errors.extend(_usage(obj.get("usage"), f"{path}.usage"))
    errors.extend(_result(obj.get("result"), f"{path}.result"))
    return errors


def validate_human_decision(obj: Any, path: str) -> list[str]:
    errors = _expect_object(obj, path)
    if errors:
        return errors
    errors.extend(_closed_object(obj, path, HUMAN_DECISION_REQUIRED, HUMAN_DECISION_OPTIONAL))
    errors.extend(_enum(obj.get("status"), f"{path}.status", HUMAN_DECISIONS))
    if "override_reason" in obj and obj["override_reason"] is not None:
        errors.extend(_nonempty_string(obj["override_reason"], f"{path}.override_reason"))
    return errors


def validate_prediction(obj: Any, path: str) -> list[str]:
    errors = _expect_object(obj, path)
    if errors:
        return errors
    errors.extend(_closed_object(obj, path, PREDICTION_REQUIRED, PREDICTION_OPTIONAL))
    errors.extend(_classification(obj.get("classification"), f"{path}.classification"))
    errors.extend(_route(obj.get("recommended_route"), f"{path}.recommended_route"))
    errors.extend(_forecast(obj.get("forecast"), f"{path}.forecast"))
    if "reason_codes" in obj and obj["reason_codes"] is not None:
        errors.extend(_string_list(obj["reason_codes"], f"{path}.reason_codes"))
    if "abstain" in obj and obj["abstain"] is not None:
        errors.extend(_bool(obj["abstain"], f"{path}.abstain"))
    if "system_id" in obj and obj["system_id"] is not None:
        errors.extend(_nonempty_string(obj["system_id"], f"{path}.system_id"))
    return errors


def validate_experiment(obj: Any, path: str = "$") -> list[str]:
    errors = _expect_object(obj, path)
    if errors:
        return errors
    errors.extend(_closed_object(obj, path, EXPERIMENT_REQUIRED, EXPERIMENT_OPTIONAL))
    errors.extend(_const_version(obj, path))
    errors.extend(_id(obj.get("experiment_id"), f"{path}.experiment_id"))
    errors.extend(_nonempty_string(obj.get("dataset"), f"{path}.dataset"))
    systems = obj.get("systems")
    if not isinstance(systems, list) or not systems:
        errors.append(f"{path}.systems must be a non-empty array")
    else:
        for i, item in enumerate(systems):
            errors.extend(_nonempty_string(item, f"{path}.systems[{i}]"))
    metrics = obj.get("metrics")
    if not isinstance(metrics, list) or not metrics:
        errors.append(f"{path}.metrics must be a non-empty array")
    else:
        for i, item in enumerate(metrics):
            errors.extend(_enum(item, f"{path}.metrics[{i}]", METRIC_GROUPS))
    errors.extend(_enum(obj.get("split"), f"{path}.split", ("holdout", "train", "all")))
    if "holdout_fraction" in obj and obj["holdout_fraction"] is not None:
        value = obj["holdout_fraction"]
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 < float(value) < 1:
            errors.append(f"{path}.holdout_fraction must be a number in (0, 1)")
    if "description" in obj and obj["description"] is not None:
        errors.extend(_nonempty_string(obj["description"], f"{path}.description", allow_empty=True))
    return errors


def format_errors(errors: Sequence[str]) -> str:
    return "\n".join(errors)


def _predictions(obj: Any, path: str) -> list[str]:
    errors = _expect_object(obj, path)
    if errors:
        return errors
    if not obj:
        return [f"{path} must not be empty when present"]
    for key, value in obj.items():
        errors.extend(_nonempty_string(key, f"{path} key"))
        errors.extend(validate_prediction(value, f"{path}.{key}"))
    return errors


def _classification(obj: Any, path: str) -> list[str]:
    errors = _expect_object(obj, path)
    if errors:
        return errors
    errors.extend(_closed_object(obj, path, CLASSIFICATION_REQUIRED, CLASSIFICATION_OPTIONAL))
    errors.extend(_enum(obj.get("work_kind"), f"{path}.work_kind", WORK_KINDS))
    errors.extend(_enum(obj.get("size"), f"{path}.size", SIZES))
    errors.extend(_enum(obj.get("risk"), f"{path}.risk", RISKS))
    errors.extend(_confidence(obj.get("confidence"), f"{path}.confidence"))
    errors.extend(_role_sequence(obj.get("recommended_sequence"), f"{path}.recommended_sequence"))
    if "abstain" in obj and obj["abstain"] is not None:
        errors.extend(_bool(obj["abstain"], f"{path}.abstain"))
    if "classifier_version" in obj and obj["classifier_version"] is not None:
        errors.extend(_nonempty_string(obj["classifier_version"], f"{path}.classifier_version"))
    return errors


def _route(obj: Any, path: str) -> list[str]:
    errors = _expect_object(obj, path)
    if errors:
        return errors
    errors.extend(_closed_object(obj, path, ROUTE_REQUIRED, ROUTE_OPTIONAL))
    errors.extend(_enum(obj.get("role"), f"{path}.role", ROLES))
    errors.extend(_nonempty_string(obj.get("endpoint"), f"{path}.endpoint"))
    errors.extend(_nonempty_string(obj.get("model_tier"), f"{path}.model_tier"))
    if "reasoning_tier" in obj and obj["reasoning_tier"] is not None:
        errors.extend(_nonempty_string(obj["reasoning_tier"], f"{path}.reasoning_tier"))
    return errors


def _advisor_route(obj: Any, path: str) -> list[str]:
    errors = _expect_object(obj, path)
    if errors:
        return errors
    errors.extend(_closed_object(obj, path, ADVISOR_ROUTE_REQUIRED, ()))
    errors.extend(_nonempty_string(obj.get("endpoint"), f"{path}.endpoint"))
    errors.extend(_nonempty_string(obj.get("model"), f"{path}.model"))
    errors.extend(_enum(obj.get("policy"), f"{path}.policy", ADVISOR_POLICIES))
    return errors


def _forecast(obj: Any, path: str) -> list[str]:
    errors = _expect_object(obj, path)
    if errors:
        return errors
    errors.extend(_closed_object(obj, path, FORECAST_REQUIRED, FORECAST_OPTIONAL))
    errors.extend(_enum(obj.get("source_confidence"), f"{path}.source_confidence", SOURCE_CONFIDENCE))
    for field in FORECAST_OPTIONAL:
        if field == "forecast_version":
            if field in obj and obj[field] is not None:
                errors.extend(_nonempty_string(obj[field], f"{path}.{field}"))
            continue
        if field in obj and obj[field] is not None:
            errors.extend(_non_negative_number(obj[field], f"{path}.{field}"))
    p50 = obj.get("reported_tokens_p50")
    p90 = obj.get("reported_tokens_p90")
    if isinstance(p50, (int, float)) and isinstance(p90, (int, float)) and not isinstance(p50, bool) and not isinstance(p90, bool):
        if p90 < p50:
            errors.append(f"{path}.reported_tokens_p90 must be >= reported_tokens_p50")
    q50 = obj.get("subscription_quota_delta_p50")
    q90 = obj.get("subscription_quota_delta_p90")
    if isinstance(q50, (int, float)) and isinstance(q90, (int, float)) and not isinstance(q50, bool) and not isinstance(q90, bool):
        if q90 < q50:
            errors.append(f"{path}.subscription_quota_delta_p90 must be >= subscription_quota_delta_p50")
    return errors


def _usage(obj: Any, path: str) -> list[str]:
    errors = _expect_object(obj, path)
    if errors:
        return errors
    errors.extend(_closed_object(obj, path, USAGE_REQUIRED, USAGE_OPTIONAL))
    errors.extend(_nonempty_string(obj.get("source"), f"{path}.source"))
    errors.extend(_enum(obj.get("source_confidence"), f"{path}.source_confidence", SOURCE_CONFIDENCE))
    for field in USAGE_OPTIONAL:
        if field in obj and obj[field] is not None:
            errors.extend(_non_negative_number(obj[field], f"{path}.{field}"))
    return errors


def _result(obj: Any, path: str) -> list[str]:
    errors = _expect_object(obj, path)
    if errors:
        return errors
    errors.extend(_closed_object(obj, path, RESULT_REQUIRED, ()))
    errors.extend(_enum(obj.get("check"), f"{path}.check", GATE_RESULTS))
    errors.extend(_enum(obj.get("verify"), f"{path}.verify", GATE_RESULTS))
    rounds = obj.get("repair_rounds")
    if not _is_int(rounds) or rounds < 0:
        errors.append(f"{path}.repair_rounds must be an integer >= 0")
    errors.extend(_bool(obj.get("replan"), f"{path}.replan"))
    errors.extend(_bool(obj.get("human_completed"), f"{path}.human_completed"))
    return errors


def _task_contract(obj: Any, path: str) -> list[str]:
    errors = _expect_object(obj, path)
    if errors:
        return errors
    allowed = ("available_fields", "verification_declared")
    extra = set(obj) - set(allowed)
    if extra:
        errors.append(f"{path} has unknown fields: {sorted(extra)}")
    if "available_fields" in obj:
        fields = obj["available_fields"]
        if not isinstance(fields, list) or not all(isinstance(item, str) and item for item in fields):
            errors.append(f"{path}.available_fields must be an array of non-empty strings")
    if "verification_declared" in obj:
        errors.extend(_bool(obj["verification_declared"], f"{path}.verification_declared"))
    return errors


def _quota(obj: Any, path: str) -> list[str]:
    errors = _expect_object(obj, path)
    if errors:
        return errors
    allowed = ("source", "source_confidence", "providers")
    extra = set(obj) - set(allowed)
    if extra:
        errors.append(f"{path} has unknown fields: {sorted(extra)}")
    if "source" in obj and obj["source"] is not None:
        errors.extend(_nonempty_string(obj["source"], f"{path}.source"))
    if "source_confidence" in obj:
        errors.extend(_enum(obj.get("source_confidence"), f"{path}.source_confidence", SOURCE_CONFIDENCE))
    if "providers" in obj and obj["providers"] is not None:
        providers = obj["providers"]
        if not isinstance(providers, list):
            errors.append(f"{path}.providers must be an array")
        else:
            for i, item in enumerate(providers):
                errors.extend(_quota_provider(item, f"{path}.providers[{i}]"))
    return errors


def _quota_provider(obj: Any, path: str) -> list[str]:
    errors = _expect_object(obj, path)
    if errors:
        return errors
    allowed = ("name", "remaining", "window")
    extra = set(obj) - set(allowed)
    if extra:
        errors.append(f"{path} has unknown fields: {sorted(extra)}")
    if "name" not in obj:
        errors.append(f"{path}.name is required")
    else:
        errors.extend(_nonempty_string(obj.get("name"), f"{path}.name"))
    if "remaining" in obj and obj["remaining"] is not None:
        value = obj["remaining"]
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= float(value) <= 1:
            errors.append(f"{path}.remaining must be a number in [0, 1]")
    if "window" in obj and obj["window"] is not None:
        errors.extend(_nonempty_string(obj["window"], f"{path}.window"))
    return errors


def _role_sequence(obj: Any, path: str) -> list[str]:
    if not isinstance(obj, list) or not obj:
        return [f"{path} must be a non-empty array of roles"]
    errors = []
    for i, item in enumerate(obj):
        errors.extend(_enum(item, f"{path}[{i}]", ROLES))
    return errors


def _closed_object(
    obj: Mapping[str, Any],
    path: str,
    required: Iterable[str],
    optional: Iterable[str],
) -> list[str]:
    required = tuple(required)
    allowed = set(required) | set(optional)
    errors = []
    for key in required:
        if key not in obj:
            errors.append(f"{path}.{key} is required")
    extra = set(obj) - allowed
    if extra:
        errors.append(f"{path} has unknown fields: {sorted(extra)}")
    return errors


def _expect_object(obj: Any, path: str) -> list[str]:
    if not isinstance(obj, dict):
        return [f"{path} must be an object"]
    return []


def _const_version(obj: Mapping[str, Any], path: str) -> list[str]:
    if obj.get("schema_version") != SCHEMA_VERSION:
        return [f"{path}.schema_version must be {SCHEMA_VERSION}"]
    return []


def _id(value: Any, path: str) -> list[str]:
    if not isinstance(value, str) or not _ID_RE.match(value):
        return [f"{path} must match {ID_PATTERN}"]
    return []


def _timestamp(value: Any, path: str) -> list[str]:
    if not isinstance(value, str) or not _TS_RE.match(value):
        return [f"{path} must be an RFC 3339 timestamp"]
    return []


def _enum(value: Any, path: str, allowed: Sequence[str]) -> list[str]:
    if value not in allowed:
        return [f"{path} must be one of {list(allowed)}"]
    return []


def _nonempty_string(value: Any, path: str, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, str):
        return [f"{path} must be a string"]
    if not allow_empty and not value.strip():
        return [f"{path} must be a non-empty string"]
    return []


def _bool(value: Any, path: str) -> list[str]:
    if not isinstance(value, bool):
        return [f"{path} must be a boolean"]
    return []


def _confidence(value: Any, path: str) -> list[str]:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= float(value) <= 1:
        return [f"{path} must be a number in [0, 1]"]
    return []


def _non_negative_number(value: Any, path: str) -> list[str]:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or float(value) < 0:
        return [f"{path} must be a number >= 0"]
    return []


def _string_list(value: Any, path: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        return [f"{path} must be an array of non-empty strings"]
    return []


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)
