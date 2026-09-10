# Two-arm capability executor (design + stub)

> Status: interface and stub. The agent seam is defined; a real runner is not
> yet wired.

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

`--dry-run` (via `scripts/run_executor.py`) is fully working now and prints the
full expansion.
