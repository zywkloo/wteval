# wteval product brief

## Decision recorded

Do **not** yet build an Agent Run Recorder or standalone Review/Eval Harness.
First run a small evaluation pilot that imports existing evidence and reviewer
outputs. The market already contains direct implementations of local
cross-agent loops, worktree review, debounce/re-review, Git-linked session
capture, and generic eval backends; see
[competitive-landscape-2026-08.md](competitive-landscape-2026-08.md).

If the pilot demonstrates measurable value, keep wteval as a wtcraft-specific
**reviewer-quality evaluation lab**, not an LLM router.

It is also not another generic AI PR-review bot. Existing reviewers may produce
findings that wteval records and evaluates; see
[product-boundary-vs-pr-reviewers.md](product-boundary-vs-pr-reviewers.md).

The differentiator is Git-bound evidence and human review: providers already
solve calling models, while teams still need a trustworthy answer to whether an
agent-assisted change stayed within its authorized task and passed the checks
that matter.

The concrete input workflow may be a bounded executor-reviewer loop run by an
existing tool. Wteval would only import its rounds and compare finding lifecycle
across providers; see
[cross-agent-verification-loop.md](cross-agent-verification-loop.md).

## User problem

After Claude Code, Codex, Cursor, or a similar tool changes a worktree, a
reviewer needs to reconstruct facts scattered across a task file, Git diff,
terminal output, and CI:

- What scope was authorized, and what files changed?
- Did deterministic scope and verification checks pass?
- What is the concrete remaining risk?
- Was the model recommendation supported by evidence?
- When provider, prompt, or policy changes, did review quality improve or
  regress?

## Target user and moment

An individual developer or a small engineering team that already uses coding
agents and Git worktrees. The moment is immediately before handoff, code
review, or merge—not while an agent is choosing a model or generating code.

## Observer versus evaluator

These are separate responsibilities:

| Question | Owner |
| --- | --- |
| Is the agent process running, waiting, idle, or exited? | Launcher session sidecar and `wtcraft observe`. |
| What files changed and did scope/verification pass? | wtcraft deterministic commands. |
| What does the frozen evidence imply, what risk remains, and how does this run compare with prior runs? | wteval. |
| Should this change be merged? | Human reviewer or protected repository policy. |

`wteval` may record lifecycle events, but it must not become the canonical
process-liveness observer. Its primary operation is a one-shot evaluation of a
specific Git revision and evidence snapshot.

## Evaluation moments

1. **Baseline capture (optional):** record task authorization and base revision
   before execution so later policy drift is visible.
2. **Handoff / agent exit (primary):** freeze the diff, run `check` and
   `verify`, then generate the deterministic verdict and optional advisory
   review.
3. **PR / CI boundary:** re-evaluate the exact PR head against protected policy;
   never reuse a local pass for a different revision.
4. **Offline regression:** replay stored fixtures or redacted run bundles to
   compare graph, prompt, model, or rule versions.

During an active agent session, wteval may append events and traces, but any
displayed assessment is `in_progress`. It must not emit a final verdict against
a moving changeset.

## Product promise

For each agent-assisted task, produce one portable `run bundle` that contains:

- authorization facts: task ID, base revision, allowed paths, off-limits paths,
  verification commands;
- actual-change facts: worktree, commit/diff identity, changed-file list;
- deterministic evidence: raw `wtcraft check --json` and `verify --json`;
- optional model review: structured findings that cite the captured facts;
- human decision: approve, request changes, or block, including rationale;
- telemetry: timing, model/provider metadata when available, tool outcomes, and
  cost/token fields only when the provider exposes them.

The product must make a failing deterministic check impossible to hide behind a
plausible LLM summary.

## A concrete output

```text
Agent Run Review
Task: feat/fix-login
Evidence: scope check passed; verification: 3 passed, 1 failed
Risk: medium

Findings
- All modified files match the authorized scope.
- auth.e2e.test.ts failed after retry logic changed.
- No verification covers an expired refresh-token path.

Recommendation: request_changes
Reason: deterministic verification failure remains unresolved.
Human decision: pending
```

The three result dimensions must remain visible rather than being collapsed
into one vague score:

```text
Deterministic gate: BLOCKED      # authoritative check/verify facts
Advisory review: request_changes # optional model analysis
Human decision: pending          # explicit approval record
```

## Product boundaries

| Belongs in wteval | Does not belong in wteval |
| --- | --- |
| Evidence collection, structured review, evaluator datasets, trace export, and human decision records. | Provider subscriptions, token resale, global model routing, agent process launching, merge automation. |
| Tool wrappers around `wtcraft status/check/verify` and Git read-only facts. | A claim that an LLM can override scope or verification failures. |
| Offline/local report generation. | A hosted control plane requirement. |

## Success metrics

- A reviewer can understand an agent run without reopening every terminal pane.
- Every recommendation cites run-bundle evidence, with no invented test result.
- On policy fixtures, the evaluator catches out-of-scope and failed-verification
  cases at least as reliably as a simple rule baseline.
- Human override rate and rationale are recorded so model usefulness is
  measurable rather than anecdotal.

## Positioning language

Safe future description once built:

> Built an observable agent-workflow evaluation harness that reviews
> AI-assisted code changes against task scope, deterministic verification
> results, and human approval gates.

Do not use this as an existing resume claim until an end-to-end vertical slice,
including persisted evidence and evaluations, actually exists.
