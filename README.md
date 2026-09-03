# wteval

> Offline evaluation lab for wtcraft's quota-aware coding-agent advisor.
>
> Status: planning docs plus a stdlib harness skeleton. No runtime, router,
> daemon, GUI, or LangChain/LangGraph integration exists in this folder.

Wteval exists to answer whether a proposed advisor is actually useful:

```text
Given a coding task, repository state, configured agent/model routes, and
subscription headroom, can we recommend the next role and execution route
better than simple rules or a fixed default—and prove it against later
verification outcomes?
```

The runtime feature, if the evidence supports building it, belongs in
[wtcraft](https://github.com/zywkloo/wtcraft/blob/main/docs/backlogs/quota-aware-task-planning.md). TokenTracker
is the preferred telemetry and existing quota-visibility surface; wtflow may
render a small, distinct Quota Cat overlay with a cat and a few quota jars, but
should not recreate its dashboard, widgets, or general usage pet. Wteval owns
only datasets, experiments, calibration, and reports. Those artifacts live in
this private repository, not in a public `wtcraft/eval/` tree. See
[lab boundary](docs/lab-boundary.md).

## Current decision

Do not build wteval as any of the following:

- a PR reviewer or cross-agent review loop;
- a token dashboard or local-session parser;
- a universal LLM gateway or subscription router;
- an agent launcher, ACP adapter, or worktree manager;
- a generic trace/evaluation dashboard.

The old review, session-capture, usage-dashboard, and generic-eval surfaces are
already crowded. The new preflight-advisor micro-category is different: it has
clear concept overlap but little demonstrated adoption. TokenSize describes
most of the proposed user experience, while CodeRoute and experimental routers
classify coding work and adapt from repository/execution feedback; their public
signals do not establish a mature market or meaningful user base.

This changes the bar. TokenTracker already ships the polished dashboard,
menu-bar, widgets, quota views, achievements, and desktop-pet surface. The
remaining experiment is a separate prompt-aware decision layer plus a small
distinct visual language: consume structured facts, recommend a route, reserve
verification/repair capacity, and show that state through a cat and a few jars.

## Project boundary

| Component | Owns |
| --- | --- |
| `wtcraft advise` | Preflight classification, quota forecast, route recommendation, reason codes, decision record, and later outcome attachment. |
| `wtflow` | Optional instruction enable/disable and minimal Quota Cat overlay/advice rendering after the decision engine proves useful; no duplicate quota dashboard. |
| `wteval` | Labeled task datasets, deterministic baselines, advisor experiments, forecast calibration, routing-policy comparison, and methodology reports. |
| TokenTracker | Preferred provider/session usage, quota-window, provenance, and existing dashboard/pet surfaces. |
| Existing agents | Actual planning, execution, verification, and repair. |

The advisor may recommend a lifecycle sequence such as `planner -> executor ->
verifier`; wteval evaluates that recommendation. It never launches the sequence.

## Why keep wteval

The remaining research questions are still useful and portfolio-relevant:

- Does explicit wtcraft task scope, stage, risk, and verification evidence
  improve classification over prompt-only routing?
- Can personal history produce calibrated p50/p90 token and subscription-quota
  ranges without presenting API-equivalent cost as subscription billing?
- Does reserving capacity for independent verification and one repair cycle
  improve verified completion under limited subscription windows?
- Which choices maximize verified task success per unit of scarce quota?
- When does a fixed lightweight advisor add enough value to justify its own
  latency and quota overhead?

The answers may be negative. A negative result is acceptable; inventing a
product moat or a precise quota forecast is not.

## Harness skeleton

Synthetic fixtures, frozen v1 schemas, deterministic baselines, and the batch
runner are executable now:

```bash
python3 scripts/validate.py tests/fixtures/examples
python3 scripts/run_eval.py \
  --experiment experiments/000-harness-smoke/experiment.json \
  --dataset tests/fixtures/examples \
  --out reports/local/000-harness-smoke
tests/run_all.sh
```

See [harness](docs/harness.md) for metrics, baselines, and how to add a private
labeled example. Real dogfood JSON stays in gitignored `datasets/private/`.

## Active documents

- [Pivot decision](docs/pivot-decision-2026-08.md) — reasoning, rejected
  hypotheses, remaining wedge, and stop conditions.
- [Product brief](docs/product-brief.md) — user problem and cross-project
  boundary.
- [Architecture](docs/architecture.md) — decision/outcome evidence flow and
  offline evaluation design.
- [MVP plan](docs/mvp-plan.md) — smallest dogfood vertical slice.
- [Lab boundary](docs/lab-boundary.md) — why experiments stay here instead of
  public `wtcraft/eval/`.
- [Harness](docs/harness.md) — schema, metrics, baselines, and batch runner.
- [Evaluation methodology](docs/evaluation-methodology.md) — datasets,
  baselines, metrics, and counterfactual limits.
- [Ambient companion UX](docs/ambient-companion.md) — lightweight Quota Cat
  overlay; TokenTracker owns the heavy dashboard/pet surface.
- [Archive](docs/archive/README.md) — superseded reviewer/eval concept.

## Honest positioning

Safe current description:

> Designed a local-first evaluation plan for a quota-aware coding-agent
> advisor, including task/role classification, subscription-usage forecasting,
> human overrides, OpenTelemetry evidence, and calibration against deterministic
> Git verification outcomes.

Do not claim a built routing system, production LLM orchestration, external
adoption, forecast accuracy, or cost savings until measured evidence exists.
