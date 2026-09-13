# Two-arm capability executor (design + stub)

> Status: interface and stub. The agent seam is defined; a real runner is not
> yet wired. Reviewed 2026-09-11; the active implementation order is in
> [MVP plan](mvp-plan.md).

## Pipeline

```text
unified task pool (origin=mutation|history)
        │  build_schedule()
        ▼
run schedule  =  task × arm(contract|no_contract) × agent
        │  execute_one()  ← Runner (the only non-deterministic seam)
        ▼
capability-run record  →  run_capability.py scores the two arms
```

## The seam: `Runner`

`wteval.executor.Runner` is a `Protocol` with one method:

```python
def run(self, workspace: str, prompt: str, task: dict) -> RunnerResult
```

- `workspace` — a git worktree already at `base_revision` with any mutation or
  verification injection applied.
- `prompt` — the task instruction; the `contract` arm includes Scope/Off-limits/
  Verification, the `no_contract` arm omits them.
- Returns `RunnerResult(ok, usage, repair_rounds, replan, notes)` — the agent
  reports only its own usage and loop counts; the executor measures the outcome.

A real runner (Codex CLI, Claude Code, a human in a loop) implements this.
`ManualRunner` is a no-op stub for smoke-testing the record pipeline.

## Result mapping (deterministic part)

| capability-run field | Source |
| --- | --- |
| `result.check` | `wtcraft check` exit code → 0=`pass`, else `fail` |
| `result.verify` | verification command exit code → 0=`pass`, else `fail` |
| `result.repair_rounds` | `RunnerResult.repair_rounds` |
| `result.replan` | `RunnerResult.replan` |
| `usage.*` | `RunnerResult.usage` (or `source=unavailable`) |

The executor never asks the model "did it pass"; it runs `check`/`verify` and
reads the exit code.

## Base-state setup (per origin)

- `origin=mutation`: checkout `base_revision` (the mutated commit — the bug is
  already present). Verification = the test command.
- `origin=history`: checkout `base_revision` (parent, before the test existed),
  then inject the verification file/case from `oracle_revision` so the agent
  knows the target.
- `origin=pbt|fixture`: reserved; not used by the current pool.

## Gotcha recorded

Mutation `task_id`s contain `->` (from rule names like `eq->ne`). That is valid
for `task_id` (no charset restriction) but violates `run_id`'s
`^[A-Za-z0-9._:-]{1,127}$` pattern. `safe_run_id()` strips invalid chars before
assembling `run_id`.

## Not built yet (the actual run)

- worktree checkout + mutation/verification injection;
- `execute_one()`'s check/verify invocation against a live repo;
- a real agent runner (Codex/Claude/human).

`scripts/run_executor.py` currently only expands and writes the schedule; there
is no `--dry-run` flag and no execution mode. Treat schedule output as a plan,
not a completed run.

## P0 implementation acceptance

The first three safeguards below are implemented in the schedule/record layer;
the remaining items are requirements for the bounded real-run adapter:

- The schedule gives each task/arm/endpoint/model/configuration/repetition a
  stable unique ID and rejects collisions; report loading independently rejects
  duplicate identities even if their `run_id`s differ.
- Mutation tasks now store `verification_command` separately from descriptive
  context. History units retain only an explicit description/path until a known
  runner materializes an executable command; they must not be passed to a shell.
- Freeze task, prompt, toolchain, permissions, and budget. Prepare clean isolated
  workspaces; reference repair commits and shared prior-run state must not be
  available to the agent. A worktree sharing the full oracle history alone does
  not meet this requirement.
- Keep the scoring contract and oracle outside agent-editable state. Score both
  arms against identical inputs after implementation, regardless of whether the
  agent was shown the contract. Do not trust a modified test or the agent's own
  success claim.
- Distinguish failed checks from failed invocation, timeout, or unavailable
  tooling. The current zero/nonzero helper cannot express that distinction.
  Preserve all attempts and diagnostics without making infra errors look like
  scope violations or dropping them from completion accounting.
- Record usage with provenance or mark it unavailable. Repair counts reported
  by the runner must remain attributed; where possible count observable loops.
- Quota aggregation keeps missing data unknown, uses successes from the same
  observed cohort, and publishes coverage rather than implying total cost is known.
- Keep the first pilot to one fixed configuration and 5–10 paired tasks. A
  bounded experiment adapter or recorded human-assisted run is sufficient;
  this does not authorize a generic agent launcher/runtime in this repository.

If these requirements need new schema fields, update constants, validators,
schemas, and agreement tests together. Do not silently repurpose frozen fields.
