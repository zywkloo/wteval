# Evaluation methodology

> Goal: determine whether the advisor improves verified engineering outcomes,
> not whether its explanation sounds convincing.
>
> Frozen v1 schemas and the batch runner live in this repository. See
> [harness](harness.md) and `schemas/*-v1.schema.json`.

## Evaluation units

Use one **task decision** as the primary unit. A task may contain multiple
sessions and role stages.

Required task fields:

- redacted prompt or feature snapshot;
- task-contract version and available Scope/Off-limits/Verification fields;
- repository/toolchain bucket;
- human work-kind, size, risk, and intended role-sequence labels;
- advisor and selected route;
- current quota observations with provenance;
- Accept/Override/Dismiss;
- later tokens/quota delta, check/verify result, repair rounds, replan, and
  completion state.

Do not count every assistant message as an independent sample.

## Dataset construction

1. Begin with 30–50 real personal tasks.
2. Freeze label definitions before comparing models.
3. Preserve chronological order and use a later held-out segment.
4. Group related follow-ups under the same task to prevent leakage.
5. Version prompts, feature extraction, role config, capability catalog, quota
   adapter, and model resolution.
6. Keep synthetic cases for schema and hard-rule tests, not product-value
   claims.

The initial dataset is too small for broad generalization. It measures personal
dogfood behavior, not the global coding population.

## Baselines

Compare at least:

| Baseline | Purpose |
| --- | --- |
| Always use current default executor/model | Establish whether routing adds anything. |
| Hand-authored role matrix | Measure existing wtcraft policy without classification. |
| Majority/keyword rules | Cheap classification floor. |
| Prompt-only fixed LLM advisor | Isolate the effect of task-contract and Git features. |
| Contract-grounded fixed LLM advisor | Proposed method. |
| TokenSize preview, opt-in | Direct substitute comparison on identical safe prompts/candidates. |
| CodeRouter `route --json` | Fully local open-source routing baseline and potential adapter target. |

Selection agreement with a competitor is diagnostic only. Neither system is
ground truth.

## Classification metrics

- macro F1 for `work_kind`;
- per-class precision/recall;
- adjacent-tolerant accuracy for size/risk;
- calibration error or Brier score for confidence;
- confusion matrices and error examples;
- missing-information accuracy: whether the advisor correctly abstained.

A plausible explanation does not repair a wrong class.

## Forecast metrics

For tokens, quota delta, wall time, and repair probability:

- median absolute error and relative/log error where meaningful;
- p50 and p90 empirical interval coverage;
- interval width, so trivial infinitely wide forecasts do not pass;
- calibration plots by provider, work kind, and size bucket;
- cold-start and missing-adapter rates;
- source-confidence stratification.

Subscription quota delta must be evaluated directly from provider observations.
Do not derive it from API pricing or a universal token conversion.

## Recommendation metrics

Primary outcomes:

- deterministic verification pass;
- first-pass verified success;
- completed task per observed quota unit;
- repair and replan rounds;
- user override rate and override outcome;
- capacity left for independent verification;
- advisor latency and quota overhead.

Secondary outcomes:

- user-reported usefulness;
- passive companion retention, instruction-enable rate, instruction drift rate,
  manual task-feeding fallback rate, details-open rate, and ignore rate;
- route stability within a task;
- missing or stale capability/quota data;
- adapter failure rate.

Avoid optimizing lines changed, commits, or token minimum in isolation. Cheap
failed work is not efficient.

## Counterfactual limitation

Only the selected route normally executes. Therefore one observed task cannot
show that another route would have failed or cost more.

Use three evidence levels:

1. **Observed:** actual selected route and result.
2. **Matched historical:** similar tasks under another route; useful but
   selection-biased.
3. **Controlled replay:** frozen safe task executed across candidates with the
   same contract and verification; strongest evidence, but expensive and
   vulnerable to repository/model drift.

Never report “X% savings with equal quality” from historical selected runs
alone.

## Routing comparison protocol

For controlled tasks:

1. freeze prompt, task contract, repository revision, role candidates, model
   identifiers, permissions, and verification commands;
2. request routing decisions independently;
3. record routing overhead and route reasons;
4. execute only when budget/privacy policy permits;
5. run identical deterministic verification;
6. retain provider failures and timeouts in the denominator;
7. blind human review to router identity where practical;
8. publish prompt-level results with sensitive content redacted.

This follows the useful principle in TokenSize's published methodology: grade
the selected output, not merely the selection, and keep economics attached to
quality. Wteval adds task-contract and deterministic Git outcome fields.

## LangGraph, LangSmith, Phoenix, and OpenTelemetry

- LangGraph may implement a versioned conditional advisor graph; graph identity
  is an experiment dimension.
- LangSmith or Phoenix may hold examples, runs, evaluator scores, and side-by-
  side experiments.
- OpenTelemetry/OpenInference spans make latency, model, token, and policy steps
  portable.
- Local JSON remains the canonical reproducible artifact so one hosted backend
  is never required.

## Go/no-go thresholds

Do not predeclare an impressive percentage from a tiny sample. The minimum
decision gate is qualitative plus statistical hygiene:

- classifier beats fixed and keyword baselines on held-out tasks;
- confidence and p50/p90 intervals are directionally calibrated;
- no fabricated quota/capability facts;
- at least one recurring decision changes beneficially;
- advisor overhead is visible and acceptable;
- result remains useful after comparison with TokenSize;
- failure analysis identifies a feasible next improvement.

Otherwise stop, integrate an existing router, or keep wteval as a documented
negative experiment.
