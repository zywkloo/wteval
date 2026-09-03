# wteval

> **Archived 2026-08-20:** superseded reviewer/eval concept. See the current
> [wteval README](../../../README.md) and
> [pivot decision](../../pivot-decision-2026-08.md). Links below are preserved
> for historical navigation; this is not an implementation plan.

> An evidence-first review and evaluation harness for AI-assisted code changes.

`wteval` is a proposed experimental companion to [wtcraft](https://github.com/zywkloo/wtcraft). It reads a
wtcraft task contract, Git changes, and deterministic `check` / `verify` JSON;
it then creates a durable run record and, optionally, asks a model to explain
the evidence and recommend a human decision.

It is deliberately **not** a subscription LLM router, autonomous coding agent,
or replacement for CI. Its job is narrower:

```text
Was this agent-assisted change authorized, what evidence was collected,
what failed, and what should a human reviewer decide next?
```

## Relationship to wtcraft

| wtcraft | wteval |
| --- | --- |
| Defines task contracts and runs deterministic Git-bound checks. | Consumes those facts to create reviewable run records and evaluations. |
| Local Git-native verification core. | Optional experimental reviewer/evaluation layer. |
| Authoritative for `check --json` and `verify --json` results. | Never rewrites, suppresses, or upgrades a failed deterministic result. |

`wteval` does not modify the wtcraft core, its task contract, Git history, or
merge state. A human remains responsible for any merge decision.

## Discovery gate

Do not implement a runtime command yet. First run a manual pilot on five frozen
wtcraft/wtflow changes with two existing reviewer configurations and human
finding labels. The pilot must show that wtcraft-specific authority evidence
changes reviewer selection or adjudication; otherwise this folder should remain
a research note or become a small wtcraft example.

If that gate passes, the first candidate surface is dataset-oriented:

```text
wteval dataset add <run-bundle>
wteval import <reviewer-output>
wteval label <run-id>
wteval compare --group-by reviewer,model,prompt
wteval export --backend phoenix|langsmith
```

Existing tools should own agent launch, local review loops, session capture,
transcript storage, and trace dashboards. Wteval, if built, imports their
outputs and evaluates a frozen evidence snapshot.

See [Product brief](product-brief.md), [architecture](architecture.md),
the [MVP plan](mvp-plan.md), and the concrete
[dogfooding loop](dogfooding.md). Remote evaluation uses a separate
[GitHub PR mode](github-pr-mode.md); it never assumes that a clone-local
task file exists in CI. Local feedback can be driven by managed
[Git-hook triggers](git-hook-triggers.md), while protected remote checks
remain authoritative.

Capture, deterministic verification, advisory review, and human adjudication
use independent, configurable triggers; see the
[verification trigger policy](verification-trigger-policy.md).

Wteval is not intended to compete as a generic AI PR reviewer. The
[product boundary](product-boundary-vs-pr-reviewers.md) treats Copilot,
CodeRabbit, and other reviewers as potential finding sources whose quality can
be evaluated against the same frozen evidence.

The August 2026 [competitive landscape](competitive-landscape-2026-08.md)
found direct substitutes for the proposed reviewer loop, local watcher,
worktree review, debounce triggers, Git-linked session evidence, and generic
evaluation dashboard. Accordingly, no standalone runtime should be built until
a small human-labeled pilot proves that wtcraft-specific policy evidence adds a
measurable signal. The current preferred scope is a dataset/import/export lab,
not a third always-on product beside wtcraft and wtflow.

A separate [quota-aware task-planning proposal](https://github.com/zywkloo/wtcraft/blob/main/docs/backlogs/quota-aware-task-planning.md)
uses wteval only for offline classifier, forecast, and recommendation-policy
evaluation. Runtime task advice and deterministic outcome evidence remain
wtcraft responsibilities.

The original bounded
[cross-agent verification loop](cross-agent-verification-loop.md) remains
a useful source of evaluation data, but should be executed by an existing tool
rather than reimplemented by wteval.

The architecture, trigger, PR-mode, and loop documents in this folder predate
the competitive scan. They are retained as design research and are not an
approved implementation plan.

## Explicit non-goals

- LLM subscription resale, model routing, billing, or a universal chat proxy
- launching coding agents or granting them repository permissions
- replacing deterministic scope checks with an LLM judgment
- automatic merge approval or deployment
- claiming production agent orchestration before it exists

## Status

Discovery and planning only. No LangChain, LangGraph, OpenTelemetry, or
LangSmith integration has been implemented in this folder yet. The next step is
a five-change manual pilot, not implementation of the earlier daemon or
reviewer-loop design.
