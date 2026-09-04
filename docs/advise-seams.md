# `wtcraft advise` capability seams

> Status: design draft aligned with `decision-v1.schema.json`.
>
> Inspired by composable agent-harness patterns (e.g. DeepSeek Harness / Cordis),
> but **not** a full agent runtime. Wtcraft stays Git-native governance; advise
> is an advisory preflight sidecar.

## Non-goals

- Do not embed an agent loop, tool registry, session log, or Web UI.
- Do not replace Codex, Cursor, Claude, DeepSeek Harness, or other executors.
- Do not weaken `check`, `verify`, protected policy, or human approval gates.
- Do not route the current classification through its own output (no recursive
  self-routing).

## Design rule

**Visible recommendation means logged.** Every stage that influences the final
`decision.json` must be versioned, attributable, and replayable from the
record alone. Prompt text stays optional; fingerprints and derived features
are the default.

## Pipeline seams

Each seam is independently swappable. A better classifier does not imply a
better routing policy.

```text
inputs
  prompt/stdin + task contract + Git summary + quota snapshot
        |
        v
[1] features.extract          features_version
        |
        v
[2] classification.*          classification.{work_kind,size,risk,...}
        |                       classifier_version, abstain
        v
[3] quota.adapter             (input only; not in decision body)
        |
        v
[4] forecast.predict            forecast.{p50,p90,source_confidence,...}
        |                       forecast_version
        v
[5] policy.select               recommended_route + reason_codes
        |                       (uses capability matrix + reservation)
        v
[6] recommendation.render       human CLI/JSON; optional wtflow state
        |
        v
[7] human.decision              human_decision.{status,override_reason}
```

Parallel shadow path: `[2]` rules classifier always runs; LLM path may run in
`shadow` without changing user-visible output.

## Seam map

| Goal | Seam | Version field | `decision-v1` fields |
| --- | --- | --- | --- |
| Derive pre-execution facts | `features.extract` | `features_version` | `prompt_fingerprint`, `features_version` |
| Classify task shape | `classification.rules` | `classification.classifier_version` | `classification.*`, `reason_codes` |
| Optional LLM classify | `classification.llm` | `classification.classifier_version` | same; must not choose `advisor_route` |
| Read quota headroom | `quota.adapter` | adapter metadata (future) | feeds forecast; failures → `unavailable` |
| Predict usage ranges | `forecast.predict` | `forecast.forecast_version` | `forecast.*` |
| Choose next route | `policy.select` | policy id (future) | `recommended_route`, `reason_codes` |
| Run the advisor itself | fixed `advisor_route` | config, not dynamic | `advisor_route.{endpoint,model,policy}` |
| Record human choice | `human.decision` | n/a | `human_decision.*` |
| Attach later facts | outcome join | n/a | separate `outcome-v1` record |

## Two routes, never collapsed

| Record | Meaning | Example |
| --- | --- | --- |
| `advisor_route` | Fixed configured model that **runs** classification | lightweight Flash-class endpoint |
| `recommended_route` | Agent/model/role proposed for the **task** | executor on configured default |

The advisor's own tokens and quota are overhead spans, not task forecast.

## Configuration layers

Borrow the *layering* idea, not Cordis itself:

```text
Layer 0  wtcraft core            check / verify / task contract (trusted)
Layer 1  role-models.yml        human preference (planner, executor, …)
Layer 2  capability matrix      availability, headless, structured output
Layer 3  advisor policy preset  always | low-confidence | shadow | off
Layer 4  workspace overlay       instruction patch / Quota Cat / CLI only
Layer 5  wteval experiment       offline comparison of policy versions
```

Upper layers override presentation and invocation policy, not Git authorization.

## Adapter seam (`quota.adapter`)

Provider order (first match wins; else `unavailable`):

1. official structured provider/CLI usage or quota output
2. stable JSON export from an established usage tool
3. isolated best-effort vendor session parser
4. explicit user snapshot
5. unavailable

Every observation carries `source`, `source_version`, `observed_at`, and
`source_confidence` (`authoritative` | `reported` | `inferred` | `unavailable`).

No fixed token-to-subscription conversion. `reported_tokens`,
`api_equivalent_cost`, and `subscription_quota_delta` stay separate through
outcome join.

## Interception, not ownership

Advise behaves like a **pre-step hook**, not an agent harness:

| Behavior | Required |
| --- | --- |
| Async, non-blocking | yes |
| Failure degrades to unavailable / rules-only | yes |
| User may Accept / Override / Dismiss | yes |
| May reject with `abstain: true` when facts missing | yes |
| May launch or switch accounts | no |
| May block prompt or weaken gates | no |

Invocation policy (`advisor_route.policy`):

```text
always          run advisor for every debounced fresh request
low-confidence  run only when rules baseline is uncertain
shadow          compute and record; do not change default UX
off             rules/local path only
```

## Capability matrix seam (future)

Role preference alone cannot prove an endpoint is installed, headless-capable,
structured-output-safe, or quota-visible. A generated matrix joins preference
with runtime facts before `policy.select`.

`model-select` remains the sole fallback resolver for execution. `advise` emits
constraints and recommendations; it does not implement a second router.

## Where new behavior goes

| Add… | Touch… | Do not touch… |
| --- | --- | --- |
| New classifier | `classification.*` version + wteval baseline | `check` / `verify` |
| New quota source | `quota.adapter` + contract tests | TokenTracker internals |
| New reservation rule | `policy.select` + reason codes | task contract schema |
| New renderer | wtflow / CLI / MCP read `decision.json` | decision schema v1 |
| New experiment | `experiments/*.json` + wteval runner | runtime hot path |

## wteval evaluation per seam

| Seam | Primary metrics | Baseline to beat |
| --- | --- | --- |
| `classification.*` | macro F1, abstain accuracy, Brier/ECE | `always_default`, `keyword`, `majority` |
| `forecast.predict` | MAE, p50/p90 coverage, unavailable rate | train quantiles, `unavailable` |
| `policy.select` | observed verify pass, override rate, repair rounds | fixed default route |
| end-to-end | completed per quota unit (observed only) | no counterfactual savings claims |

Store predictions under `example.predictions.<system_id>` for replay without
re-invoking providers.

## Minimum v1 implementation order

1. `features.extract` + deterministic `classification.rules`
2. `quota.adapter` with explicit `unavailable`
3. `forecast.predict` cold-start buckets
4. `policy.select` with reason codes and reservation stub
5. append-only `decision.json` + optional `outcome.json` join
6. wteval import + held-out comparison before any LLM or UI expansion

## Related

- [Architecture](architecture.md) — evidence flow and storage
- [Evaluation methodology](evaluation-methodology.md) — metrics and limits
- [`schemas/decision-v1.schema.json`](../schemas/decision-v1.schema.json) —
  frozen record shape
- [Harness](harness.md) — offline batch runner
