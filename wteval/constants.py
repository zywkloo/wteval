"""Frozen v1 enums and field sets for the evaluation lab.

These constants are the executable source of truth. JSON Schema files must
agree with them; tests/test_schema_agreement.py fails if they drift.
"""

SCHEMA_VERSION = 1

WORK_KINDS = (
    "discovery",
    "planning",
    "execution",
    "verification",
    "repair",
    "finishing",
)

SIZES = ("xs", "s", "m", "l", "xl")

RISKS = ("low", "medium", "high")

ROLES = ("planner", "executor", "verifier", "finisher")

SPLITS = ("train", "holdout", "unassigned")

HUMAN_DECISIONS = ("accept", "override", "dismiss", "pending")

SOURCE_CONFIDENCE = ("authoritative", "reported", "inferred", "unavailable")

GATE_RESULTS = ("pass", "fail", "skip", "unavailable")

ADVISOR_POLICIES = ("always", "low-confidence", "shadow", "off")

EXAMPLE_REQUIRED = (
    "schema_version",
    "example_id",
    "task_id",
    "created_at",
    "features",
    "labels",
)

EXAMPLE_OPTIONAL = (
    "split",
    "decision",
    "predictions",
    "human_decision",
    "outcome",
    "notes",
)

FEATURES_REQUIRED = ("prompt_fingerprint", "features_version")

FEATURES_OPTIONAL = (
    "feature_snapshot",
    "task_contract",
    "repository_bucket",
    "quota",
    "git_summary",
)

LABELS_REQUIRED = ("work_kind", "size", "risk", "intended_sequence")

LABELS_OPTIONAL = ("should_abstain", "labeler", "labeled_at", "notes")

DECISION_REQUIRED = (
    "schema_version",
    "decision_id",
    "task_id",
    "created_at",
    "prompt_fingerprint",
    "features_version",
    "classification",
    "advisor_route",
    "recommended_route",
    "forecast",
    "reason_codes",
)

DECISION_OPTIONAL = ("human_decision",)

CLASSIFICATION_REQUIRED = (
    "work_kind",
    "size",
    "risk",
    "confidence",
    "recommended_sequence",
)

CLASSIFICATION_OPTIONAL = ("abstain", "classifier_version")

ROUTE_REQUIRED = ("role", "endpoint", "model_tier")

ROUTE_OPTIONAL = ("reasoning_tier",)

ADVISOR_ROUTE_REQUIRED = ("endpoint", "model", "policy")

FORECAST_REQUIRED = ("source_confidence",)

FORECAST_OPTIONAL = (
    "reported_tokens_p50",
    "reported_tokens_p90",
    "subscription_quota_delta_p50",
    "subscription_quota_delta_p90",
    "forecast_version",
)

OUTCOME_REQUIRED = ("schema_version", "decision_id", "actual_route", "usage", "result")

USAGE_REQUIRED = ("source", "source_confidence")

USAGE_OPTIONAL = (
    "reported_tokens",
    "api_equivalent_cost",
    "subscription_quota_delta",
)

RESULT_REQUIRED = ("check", "verify", "repair_rounds", "replan", "human_completed")

HUMAN_DECISION_REQUIRED = ("status",)

HUMAN_DECISION_OPTIONAL = ("override_reason",)

PREDICTION_REQUIRED = ("classification", "recommended_route", "forecast")

PREDICTION_OPTIONAL = ("reason_codes", "abstain", "system_id")

EXPERIMENT_REQUIRED = (
    "schema_version",
    "experiment_id",
    "dataset",
    "systems",
    "metrics",
    "split",
)

EXPERIMENT_OPTIONAL = ("description", "holdout_fraction")

METRIC_GROUPS = ("classification", "forecast", "recommendation")

ID_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._:-]{1,127}$"

TIMESTAMP_PATTERN = (
    r"^\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(\.\d+)?([Zz]|[+-]\d{2}:\d{2})$"
)
