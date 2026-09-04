# Architecture: offline advisor evaluation

> Status: target evidence flow, not an implementation plan.

## System boundary

```text
                          runtime path

 prompt + task + Git + TokenTracker quota snapshot
                 |
                 v
         wtcraft advise
       /                 \
      v                   v
decision.json       wtflow companion state
                          |
                 inspect/accept/override/ignore
                          |
                          v
                  existing coding agent
                          |
              usage + Git + verify outcome
                          |
                          v
                     outcome.json

                         offline path

 decision.json + outcome.json + human labels
                          |
                          v
                wteval normalize/import
                          |
                          v
             versioned dataset + experiments
                          |
          +---------------+----------------+
          v               v                v
 classification       forecast         policy/outcome
 evaluation           calibration      comparison
          \               |                /
           +--------------+---------------+
                          v
                local report / optional
                LangSmith or Phoenix export
```

Wteval is not on the critical runtime path. A missing evaluator cannot block a
task, weaken a wtcraft gate, select an agent, or change Git state.

## Runtime records consumed by wteval

### Decision record

Minimum fields:

```json
{
  "schema_version": 1,
  "decision_id": "uuid",
  "task_id": "feat/fix-refresh",
  "created_at": "timestamp",
  "prompt_fingerprint": "sha256:redacted",
  "features_version": "task-features-v1",
  "classification": {
    "work_kind": "execution",
    "size": "s",
    "risk": "medium",
    "confidence": 0.82,
    "recommended_sequence": ["executor", "verifier"]
  },
  "advisor_route": {
    "endpoint": "agy",
    "model": "configured-flash",
    "policy": "always"
  },
  "recommended_route": {
    "role": "executor",
    "endpoint": "codex",
    "model_tier": "balanced-coding",
    "reasoning_tier": "medium"
  },
  "forecast": {
    "reported_tokens_p50": null,
    "reported_tokens_p90": null,
    "subscription_quota_delta_p50": null,
    "subscription_quota_delta_p90": null,
    "source_confidence": "unavailable"
  },
  "reason_codes": ["bounded_change", "verification_declared"],
  "human_decision": "override"
}
```

Prompt content is not required in the long-term record. A local opt-in research
dataset may retain redacted prompt text separately; the default record uses a
fingerprint and derived features.

### Outcome record

```json
{
  "schema_version": 1,
  "decision_id": "uuid",
  "actual_route": {
    "role": "executor",
    "endpoint": "claude",
    "model": "configured-model"
  },
  "usage": {
    "reported_tokens": null,
    "api_equivalent_cost": null,
    "subscription_quota_delta": null,
    "source": "adapter-name",
    "source_confidence": "reported"
  },
  "result": {
    "check": "pass",
    "verify": "pass",
    "repair_rounds": 1,
    "replan": false,
    "human_completed": true
  }
}
```

## Quantities that must remain separate

| Field | Meaning |
| --- | --- |
| `reported_tokens` | Provider/session-reported token categories when available. |
| `api_equivalent_cost` | Calculation from public API list prices; not subscription billing. |
| `subscription_quota_delta` | Observed provider rolling-window change. |
| `quota_remaining` | Provider-reported or adapter-observed window state. |
| `source_confidence` | Authoritative, reported, inferred, or unavailable. |

No fixed token-to-subscription conversion is allowed.

## Classification and routing separation

The advisor pipeline has four separable components:

1. feature extraction from prompt, task contract, stage, and Git;
2. work-kind/size/risk classification;
3. usage and quota forecasting for eligible routes;
4. policy selection under capability, risk, privacy, and reservation
   constraints.

Each component gets an independent version and evaluator. A better classifier
does not imply a better routing policy.

See [advise seams](advise-seams.md) for the composable stage map, configuration
layers, and wteval metrics per seam.

## Role preferences versus endpoint capabilities

Wtcraft's human-editable role configuration expresses preference. It cannot by
itself prove that Agy, Cursor, Claude, Codex, or another endpoint:

- is installed and authenticated;
- supports headless or asynchronous invocation;
- honors a requested model/reasoning tier;
- returns schema-constrained structured output;
- exposes usage or quota observations;
- has acceptable latency for the advisor path.

A generated capability/availability matrix supplies those facts. `model-select`
remains the sole fallback resolver. `advise` supplies role, constraints, and
quota state; it does not implement a second routing engine.

## Adapter boundary

Preferred observation order:

1. official structured provider/CLI usage or quota output;
2. stable JSON export from an established usage tool;
3. isolated best-effort vendor session parser;
4. explicit user-entered snapshot;
5. unavailable.

Every adapter records source version, observation time, and confidence. Schema
failure degrades to unavailable and never blocks normal wtcraft use.

### Preferred TokenTracker boundary

TokenTracker is the preferred first adapter because it already owns broad
provider parsing, deduplication, subscription-window observation, and quota
visibility. Quota Cat should consume a versioned read-only CLI JSON snapshot.
Internal SQLite/JSONL files and undocumented dashboard endpoints are not an
integration contract.

Prompt content crosses only into `wtcraft advise`; it never crosses into
TokenTracker. This preserves TokenTracker's no-prompt privacy guarantee while
allowing task-aware classification in the independent sidecar.

## AI and observability stack

- A deterministic rules classifier is the required baseline.
- A fixed lightweight LLM may return versioned structured classification and
  reason codes.
- LangGraph is justified only for conditional escalation, human decision, or
  multi-stage recommendation flow—not as the data store.
- OpenTelemetry records spans for feature extraction, advisor inference,
  forecast, policy, companion-state latency, human decision, and outcome join.
- LangSmith or Phoenix may store datasets/experiments and render comparisons.
  They are optional backends, never the source of task or quota truth.

Suggested root trace:

```text
wtcraft.advise
  features.extract
  classification.rules
  classification.llm
  quota.snapshot
  forecast.predict
  policy.select
  recommendation.render
  human.decision
```

Do not emit raw prompt, source code, credentials, or diff content by default.

## Storage

Keep runtime evidence local and repository-independent so worktree cleanup does
not delete it. Records may use the repository's Git common-dir identity while
storing only pseudonymous repository/task identifiers in exported datasets.

Wteval imports immutable decision/outcome snapshots. It never edits a prior
record in place; corrections become annotations with author and timestamp.
