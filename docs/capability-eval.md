# Capability eval: deterministic-oracle two-arm runs

> Status: planned experiment. Synthetic fixtures only until real runs land.
>
> Rationale lives in
> [wtcraft's agent-capability-eval memo](https://github.com/zywkloo/wtcraft/blob/main/docs/backlogs/agent-capability-eval.md).
> The harness lives here.

## What this measures

Does a wtcraft task contract (Scope, Off-limits, Verification) change verified
coding-agent outcomes, and how do agent configurations compare when scored by a
deterministic oracle instead of a judge model?

The oracle is `wtcraft check` + `wtcraft verify`, which are already shipped:

| Signal | Source | Determinism |
| --- | --- | --- |
| Task passed | `verify` runs the declared commands | Deterministic given a fixed revision and toolchain |
| Change stayed in scope | `check` compares paths against Scope/Off-limits | Deterministic |
| Repair rounds | Cycles before first pass | Observed |
| Token/quota | Provider-reported | Reported with source confidence |

Honest limit: a passing oracle proves the declared verification passed, not
that the change is semantically correct. A weak test is a weak oracle.

## Two arms

- `contract`: agent runs with a wtcraft task contract.
- `no_contract`: same prompt, no contract.

Each arm runs 2-3 agent/model configurations. The contract-vs-no-contract
comparison answers the roadmap question wtcraft has kept asking and never
measured: does the contract change verified outcomes, or only feel tidier?
A null result is publishable and is not suppressed.

## Schema

`schemas/capability-run-v1.schema.json` — one agent execution of one benchmark
task under one arm:

- `arm`: `contract` | `no_contract`
- `agent`: `endpoint`, `model`, `config_version`
- `task`: `repository`, `base_revision`, `oracle_revision`, `prompt_fingerprint`,
  optional `verification_declared`
- `result`: `check`, `verify`, `repair_rounds`, `replan`
- `usage`: `reported_tokens`, `subscription_quota_delta`, `source`, `source_confidence`

`oracle_revision` is the historical commit whose test is the ground truth;
`base_revision` is where the agent starts.

## Runner

```bash
python3 scripts/run_capability.py \
  --runs tests/fixtures/runs \
  --out reports/local/capability-smoke
```

Validates every run, groups by arm then agent, writes `report.json` and
`report.md`.

## Metrics

- verify pass rate (Wilson 95% CI)
- scope violation rate (Wilson 95% CI)
- first-pass verified rate (verify pass, zero repair rounds, no replan)
- mean repair rounds
- quota per verified task = reported consumption / verified successes

Runs whose check/verify is `skip` or `unavailable` are excluded from that
rate's denominator. Report intervals, not point estimates; at N=40 intervals
are wide.

## Adding real runs

1. Copy a synthetic fixture under `tests/fixtures/runs/`.
2. Fill `repository` (name only, no local path), `base_revision`, and
   `oracle_revision` from real commits.
3. Redact or fingerprint the prompt; never commit raw transcripts.
4. Write under gitignored `datasets/private/runs/`.
5. Re-run the same revision to confirm the oracle is reproducible before
   trusting the pass/fail.

## Candidate screening

`scripts/scan_candidates.py` flags commits that touch both a test file and a
source file, as a first pass for building the real task set:

```bash
python3 scripts/scan_candidates.py \
  --repo ../wtcraft --repo ../wtflow \
  --since 2026-01-01 \
  --out datasets/private/candidates.json
```

Output is a JSON candidate list; each entry maps to a capability-run:

- `oracle_sha` → `task.oracle_revision`
- `base_sha` → `task.base_revision`
- `repo` → `task.repository` (name only)
- `subject` + `test_files` → a redacted `prompt_fingerprint`

The heuristic is only a filter: a human must confirm each commit is a real
"test now passes" ground truth (the test existed at base or is injected from
oracle, and passes at oracle). Keep the list under gitignored
`datasets/private/`. Repos without real tests produce no oracle and should be
excluded — a GUI shell with no unit tests cannot supply ground truth.

## Go/no-go

Ship the report when:

- at least 30 tasks ran to a recorded outcome in both arms;
- the oracle pass/fail reproduced on a re-run of the same revision;
- limitations state sample size, single-codebase provenance, and the
  weak-test-weak-oracle caveat;
- the write-up separates what was measured from what was inferred.

Abandon and record why if the oracle is not reproducible — a flaky
verification command set invalidates the central claim, and that finding is
itself worth writing down.
