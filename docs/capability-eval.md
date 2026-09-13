# Capability eval: deterministic-oracle two-arm runs

> Status: active pilot priority, reviewed 2026-09-11. Task builders and scoring
> exist; real paired execution is pending. See [MVP plan](mvp-plan.md) for the
> current order and admission gates.
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

Start with one fixed agent configuration on 5–10 qualified tasks. Expand to
at least 30 paired tasks after the pipeline is reliable; add 2–3 configurations
only after that, as budget permits. The contract-vs-no-contract
comparison answers the roadmap question wtcraft has kept asking and never
measured: does the contract change verified outcomes, or only feel tidier?
A null result is publishable and is not suppressed. This measures the combined
effect of the explicit Scope/Off-limits/Verification intervention; it does not
isolate document formatting from additional instructions. It also does not
measure willingness to maintain a protected authorization gate.

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
- quota per verified task = consumption / successes within the same
  quota-observed cohort, accompanied by coverage and comparable provider units

The scorer excludes `skip`/`unavailable` from each check/verify rate. Before
interpreting real runs, report total attempts and scoring coverage beside those
conditional rates. Keep agent failures/timeouts in attempted completion
accounting; show infrastructure failures separately. Missing quota remains
unknown: quota-per-success uses only the quota-observed cohort and reports its
coverage.

Report paired task differences as well as arm rates and intervals; arm-level
Wilson intervals alone do not estimate the uncertainty of the paired effect.
Separate history/mutation results and account for related tasks. At N=30–50,
intervals may still be wide; do not imply a model ranking they cannot support.

## Adding real runs

1. Use a synthetic fixture as a shape reference, then create the real record
   under gitignored `datasets/private/runs/`; do not place real data in fixtures.
2. Fill `repository` (name only, no local path), `base_revision`, and
   `oracle_revision` from real commits.
3. Redact or fingerprint the prompt; never commit raw transcripts.
4. Write under gitignored `datasets/private/runs/`.
5. Re-run the same revision to confirm the oracle is reproducible before
   trusting the pass/fail.

## Candidate screening

History scanners and the mutation seeder produce candidates. Admit each only
when a frozen buggy start fails and a reference repair passes the same checks
reproducibly. Revalidate old catalogs missing current baseline/determinism data.
Exclude failures caused only by broken harness setup, missing dependencies, or
generated-copy drift. Keep the executable command separate from descriptive
annotations and verification-unit paths.

Before execution, freeze the scoring contract and tests outside agent-editable
state; apply the same oracle to both arms, including the arm not shown a task
contract. Do not expose reference repairs through Git history or shared files.
Use equal permissions/budgets and randomize or counterbalance execution order.

The unit-granularity history scanner is useful for the 30-task target, but units
from one commit and mutations of one function remain correlated samples.

### Verification units (primary)

`scripts/scan_verifications.py` decomposes history by the verification unit a
commit introduces — a runnable test script or a contract-case directory — so a
single commit can yield many tasks:

```bash
python3 scripts/scan_verifications.py \
  --repo ../wtcraft \
  --since 2024-01-01 \
  --out datasets/private/verifications.json
```

Each unit maps to a capability-run:

- `verification` → `task.verification`
- `oracle_sha` → `task.oracle_revision`
- `base_sha` → `task.base_revision`
- `repo` → `task.repository` (name only)

### Commit candidates (secondary)

`scripts/scan_candidates.py` flags commits that touch both a test file and a
source file; useful when a repo has no case-directory convention:

```bash
python3 scripts/scan_candidates.py \
  --repo ../wtcraft --repo ../wtflow \
  --since 2024-01-01 \
  --out datasets/private/candidates.json
```

Both are heuristics: a human must confirm each unit is a real "verification now
passes" ground truth, and drop test-harness infra such as `run_all.sh` and
`framework.sh`. Keep the lists under gitignored `datasets/private/`. Repos
without real tests produce no oracle and should be excluded — a GUI shell with
no unit tests cannot supply ground truth.

## Go/no-go

A 5–10-task pilot report validates the execution pipeline and may be shared as
such. Complete the full report when:

- at least 30 qualified tasks ran to a recorded outcome in both arms;
- historical and mutation results, paired differences, related-task clusters,
  attempts, scoring coverage, and usage missingness are visible;
- the oracle pass/fail reproduced on a re-run of the same revision;
- limitations state sample size, single-codebase provenance, and the
  weak-test-weak-oracle caveat;
- the write-up separates what was measured from what was inferred.

Abandon and record why if the oracle is not reproducible — a flaky
verification command set invalidates the central claim, and that finding is
itself worth writing down.
