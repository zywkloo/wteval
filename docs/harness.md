# Evaluation harness

> Status: skeleton. Synthetic fixtures only. No product-value claims.

This repository is the offline lab for a possible `wtcraft advise` command.
It is not a runtime, dashboard, router, or agent launcher.

## Run the harness

Python 3.9+ and the standard library are enough.

```bash
python3 scripts/validate.py tests/fixtures/examples
python3 scripts/run_eval.py \
  --experiment experiments/000-harness-smoke/experiment.json \
  --dataset tests/fixtures/examples \
  --out reports/local/000-harness-smoke
tests/run_all.sh
```

## Layout

| Path | Role |
| --- | --- |
| `schemas/` | Frozen v1 JSON Schema for examples, decisions, outcomes, and experiments. |
| `wteval/` | Validators, chronological split, baselines, metrics, batch runner. |
| `tests/fixtures/examples/` | Synthetic labeled tasks used by CI. |
| `datasets/private/` | Gitignored real dogfood JSON. |
| `experiments/` | Versioned experiment configs. |
| `reports/local/` | Gitignored generated reports. |

## Metrics

Defined in `wteval/metrics.py` and [evaluation methodology](evaluation-methodology.md):

- classification: macro F1, per-class precision/recall, adjacent-tolerant size/risk accuracy, Brier, ECE, abstain accuracy;
- forecast: median absolute/relative/log error, p50/p90 coverage, interval width, missing/unavailable rates;
- recommendation: observed verify pass, first-pass verified success, repair rounds, override rate, completed-per-quota-unit.

Recommendation scores describe the **observed** route only. Do not report
savings against an unexecuted alternative.

## Adding a real example

1. Copy a synthetic fixture.
2. Redact or fingerprint the prompt. Do not commit raw transcripts.
3. Fill labels before looking at model output you intend to score.
4. Write the file under `datasets/private/`.
5. Keep `split` as `unassigned` unless you are freezing a chronological cut.

## Baselines

Every advisor version is compared to:

- `always_default` — current default executor/model;
- `majority` — most common train labels plus train quantile forecasts;
- `keyword` — cheap prompt-snapshot rules;
- `recorded:<name>` — a prediction already stored on the example.
