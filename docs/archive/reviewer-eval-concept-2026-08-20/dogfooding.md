# Dogfooding wteval

> **Status:** Pre-market workflow note. Use an existing review-loop tool for
> execution; wteval should only import and evaluate results if the pilot passes.
> See [competitive-landscape-2026-08.md](competitive-landscape-2026-08.md).

## The daily reason to use it

Persisting `wtcraft check --json` and `verify --json` is necessary plumbing, but
it is not enough reason for a solo developer to run another tool.

The dogfood-worthy loop is:

```text
one agent implements a task
        |
        v
wtcraft produces deterministic evidence
        |
        v
a different reviewer examines the frozen diff and evidence
        |
        v
the human labels each finding and records the merge decision
        |
        v
those labeled runs become the evaluator regression dataset
```

The practical daily question is:

> Codex/Claude changed this worktree. Did an independent reviewer find a real
> risk that the deterministic checks and I missed?

## First workflow in the wtcraft and wtflow repositories

Use wteval at the existing finish/handoff boundary, not throughout every agent
turn:

```bash
# Agent finishes work in a contracted worktree.
wteval review --repo /path/to/wtcraft --worktree feat/task \
  --reviewer claude-cli

# Or, when Claude implemented the task:
wteval review --repo /path/to/wtflow --worktree feat/task \
  --reviewer codex-cli
```

The command should:

1. freeze the current base/head/diff identity;
2. collect `wtcraft check --json` and `verify --json`;
3. give the reviewer only the task contract, bounded diff, and captured facts;
4. require structured findings with evidence references;
5. display the gate and findings in the terminal;
6. ask the human to label findings and record a decision.

Using a different reviewer from the executor is a useful default, but it is not
a security guarantee. The selected reviewer is explicit; wteval does not
perform automatic subscription or quota routing.

## Minimum useful terminal interaction

```text
WTEval Run 01J...
Executor: codex
Reviewer: claude-cli
Revision: abc123

Gate
  Scope: PASS
  Verification: PASS (18/18)

Reviewer findings
  F1 [high] Cancellation can leave .worktree-session.json in running state.
     Evidence: diff:src/runner/session.py; verify:test_session_lifecycle
  F2 [low] Rename this helper for readability.

Label F1: valid
Label F2: invalid/style-only
Decision: request_changes
```

The labels should be small and queryable:

- `valid`
- `invalid`
- `duplicate`
- `style_only`
- `cannot_verify`
- `fixed_before_merge`

## What gets measured

After 10–20 real tasks, wteval should be able to answer:

- How often did the reviewer produce at least one valid finding?
- What was its false-positive rate?
- Which failures were already caught by deterministic gates?
- Which valid findings were fixed before merge?
- How often did the human override the recommendation?
- What were reviewer latency and provider-reported cost/token usage?

This is the dataset used to compare graph, prompt, model, and rule versions. A
benchmark is meaningful only after it replays actual or carefully curated
examples with human labels.

Once GitHub ingestion exists, a reviewer may be GitHub Copilot, CodeRabbit, or
another installed service rather than a wteval-owned model call. Wteval's value
is the normalized evidence, labels, and comparison—not the production of one
more generic review comment.

## Phased dogfood target

### Slice 1 — terminal second review

- one repository and one completed worktree;
- facts capture plus one reviewer adapter;
- terminal findings and manual labels;
- local run bundle and report.

Success criterion: at least one finding can be traced from reviewer output to a
specific captured artifact, labeled by the human, and replayed later.

### Slice 2 — finish-hook convenience

- allow `/finishwt` or an explicit handoff command to invoke wteval;
- optionally enqueue a review from `post-commit`, bound to the new commit SHA;
- keep `pre-push` limited to fast deterministic results or warnings, never a
  required network model call;
- infer executor identity from the task/session facts when available;
- mark a run stale whenever its Git revision changes;
- keep an interactive fallback when a headless reviewer adapter is unavailable.

### Slice 3 — evaluator regression

- collect 10–20 labeled tasks from wtcraft and wtflow work;
- replay frozen bundles through two reviewer configurations;
- compare verdict accuracy, valid-finding rate, unsupported claims, latency,
  and human override rate;
- optionally export traces and experiments to LangSmith.

### Slice 4 — wtflow display

Only after the terminal loop proves useful, add a wtflow panel with:

- deterministic gate badge;
- reviewer findings and their labels;
- evidence links;
- human decision controls;
- local trace or optional LangSmith link.

## What not to dogfood yet

- automatic agent dispatch or an always-running ACP-dependent orchestrator;
- universal model routing;
- automated merge approval;
- live evaluation against a moving diff;
- copying entire agent conversations into the wteval store.

The first dogfood loop stays useful even if every headless agent adapter breaks:
capture the run, open the generated review input in an interactive agent, then
import or manually record structured findings.
