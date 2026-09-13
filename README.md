# wteval

> Offline lab for reproducible coding-agent capability evaluation.
>
> Status, reviewed 2026-09-11: executable stdlib evaluation tools and task
> builders; the real contract/no-contract executor is not yet connected.
> Advisor evaluation remains a downstream, deferred experiment.

The immediate question is whether an explicit wtcraft task contract changes
verified coding outcomes. The experiment scores frozen tasks with deterministic
scope and test checks, without a judge model. A passing oracle establishes only
that the declared checks passed; test adequacy must be assessed separately.

## Design principle: test the tests

The Planner side of [wtcraft](https://github.com/zywkloo/wtcraft) can use an LLM
to inspect a repository and propose task-specific acceptance commands. The
implementing agent does not grade itself: `wtcraft verify` runs those exact
commands and records their exit codes through a language-agnostic shell runner.

Mechanical execution is necessary, but it is not proof that the proposed checks
are complete, stable, or semantically correct. That is wteval's boundary:

> `wtcraft verify` asks whether the declared checks passed; `wteval` asks whether
> those checks can detect defects.

Mutation testing injects small faults and checks whether the suite catches them.
Property-based testing exercises stated invariants over generated inputs. Wteval
keeps those methods and their experimental evidence outside wtcraft's runtime
and does not replace the repository's ordinary tests or act as an LLM judge.

## Current priority

Follow [the MVP plan](docs/mvp-plan.md): correct measurement and run identity,
qualify 5–10 tasks, run both arms with one fixed agent configuration, then expand
to at least 30 qualified paired tasks and publish a report. Existing synthetic
reports and task candidates do not establish a contract benefit, model ranking,
or quota savings.

The lab already has schemas, validators, deterministic advisor baselines,
capability report generation, history/mutation task builders, and mutation/PBT
instruments. The remaining execution work is workspace preparation, live scoring,
and a bounded runner connection. [Executor status](docs/executor.md) distinguishes
implemented interfaces from planned execution.

## Project boundary

| Component | Owns |
| --- | --- |
| wtcraft | Local task checks and protected change-authorization tooling; ordinary CI still owns tests at the merge boundary. |
| wteval | Task datasets, controlled experiments, scoring, calibration, and reports; no production agent runtime. |
| Existing agents | Actual task implementation; the lab records and independently scores their outputs. |
| Deferred advisor | A possible future consumer of measured outcomes, subject to the MVP resume gate. |

A contract effectiveness result does not establish demand for policy approval
workflows. Wtcraft validates protected authorization separately. The lab consumes
existing facts and reports results back; it does not add semantic judgments to
wtcraft's trusted evidence or create a public `wtcraft/eval/` tree.

Real tasks, labels, and run records stay gitignored under `datasets/private/`.
Committed fixtures are synthetic. See [lab boundary](docs/lab-boundary.md).

## Deferred research

Advisor classification, route recommendations, quota forecasting, and reserve
policies remain possible consumers of real run data. Resume only when observed
quality/usage differences and a recurring decision justify the experiment.
Do not build a PR reviewer, universal gateway, launcher service, dashboard, GUI,
or generic trace platform as part of the current capability evaluation.

## Tools

Frozen v1 schemas, deterministic baselines, and the batch runners are
executable now:

```bash
python3 scripts/validate.py tests/fixtures/examples
python3 scripts/run_eval.py \
  --experiment experiments/000-harness-smoke/experiment.json \
  --dataset tests/fixtures/examples \
  --out reports/local/000-harness-smoke
python3 scripts/run_capability.py \
  --runs tests/fixtures/runs \
  --out reports/local/capability-smoke
python3 scripts/run_pbt.py
python3 scripts/run_pbt.py --properties pbt_properties/wtcraft.py   # needs ../wtcraft
python3 scripts/seed_mutations.py \
  --repo ../wtcraft --files "scripts/policy_evaluator.py" \
  --test-cmd "python3 tests/contract_policy_envelope.py" \
  --max-mutants 20 --out datasets/private/mutations
tests/run_all.sh
```

See [harness](docs/harness.md) for metrics, baselines, and how to add a private
labeled example. Real dogfood JSON stays in gitignored `datasets/private/`.

Task-set builders (`scripts/scan_verifications.py`, `scripts/scan_candidates.py`),
the mutation gate and seeder (`scripts/run_mutation.py`,
`scripts/seed_mutations.py`), and PBT catalogs (`pbt_properties/`) are
documented in [capability eval](docs/capability-eval.md) and
[mutation & PBT](docs/mutation-pbt.md).

## Documents and planning authority

The MVP plan owns the current execution order; capability eval and executor
specify its methodology and implementation gaps. Advisor-oriented product,
architecture, pivot, seams, and ambient UX documents are deferred references,
not parallel implementation queues.

- [Pivot decision](docs/pivot-decision-2026-08.md) — reasoning, rejected
  hypotheses, remaining wedge, and stop conditions.
- [Product brief](docs/product-brief.md) — user problem and cross-project
  boundary.
- [Architecture](docs/architecture.md) — decision/outcome evidence flow and
  offline evaluation design.
- [Advise seams](docs/advise-seams.md) — composable preflight stages mapped to
  `decision-v1`.
- [MVP plan](docs/mvp-plan.md) — active pilot/report sequence and deferred advisor reference.
- [Lab boundary](docs/lab-boundary.md) — why experiments stay here instead of
  public `wtcraft/eval/`.
- [Harness](docs/harness.md) — schema, metrics, baselines, and batch runner.
- [Capability eval](docs/capability-eval.md) — deterministic-oracle two-arm
  runs scored by `wtcraft check/verify`.
- [Mutation & PBT](docs/mutation-pbt.md) — mutation-score gate and
  property-based testing instruments.
- [Executor](docs/executor.md) — two-arm run scheduling and result mapping.
- [Evaluation methodology](docs/evaluation-methodology.md) — datasets,
  baselines, metrics, and counterfactual limits.
- [Ambient companion UX](docs/ambient-companion.md) — lightweight Quota Cat
  overlay; TokenTracker owns the heavy dashboard/pet surface.
- [Archive](docs/archive/README.md) — superseded reviewer/eval concept.

## Honest positioning

Safe current description:

> Built a stdlib evaluation toolkit with schema validation, deterministic
> baselines, capability reports, history/mutation task builders, and PBT checks.
> The real paired agent experiment is pending; no measured contract improvement
> or routing benefit is claimed.

Do not claim a built routing system, production LLM orchestration, external
adoption, forecast accuracy, or cost savings until measured evidence exists.
