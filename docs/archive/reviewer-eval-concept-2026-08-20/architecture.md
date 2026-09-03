# Architecture: evidence first, model optional

> **Status:** Pre-market design note, not an approved implementation plan. The
> competitive scan found direct substitutes for the proposed recorder, runner,
> and eval backend. See
> [competitive-landscape-2026-08.md](competitive-landscape-2026-08.md).

## Core flow

```text
task contract + Git diff + wtcraft JSON
                 |
                 v
           Run Bundle Builder
          /        |         \
         v         v          v
  deterministic   report    trace events
     verdict      files          |
         |                       v
         |                 OpenTelemetry export
         v                       |
  optional Reviewer Graph ------+----> LangSmith (optional)
         |
         v
structured recommendation -> human decision -> final run record
```

`Run Bundle Builder` is the primary product. The reviewer graph is a consumer
of the bundle, not a source of truth.

## Inputs

All inputs should be captured before a model call, with redaction applied to
patches and command output where required:

| Input | Source | Trust level |
| --- | --- | --- |
| Task authorization | `.worktree-task.md`; later a reviewed policy envelope | Declared local policy; not a security boundary until wtcraft Phase 6. |
| Changed files / diff metadata | Git | Repository fact. |
| Scope verdict | `wtcraft check --json` | Deterministic authoritative result. |
| Verification verdict | `wtcraft verify --json` | Deterministic authoritative result. |
| Reviewer analysis | Model graph | Advisory only. |
| Final decision | Named human | Decision record. |

Local worktrees and remote pull requests normalize into the same frozen
`ChangeSubject` (`repository`, base/merge-base/head revisions, head ref, and
changed paths). Local mode may capture `.worktree-task.md`; protected GitHub
mode obtains authority from wtcraft's protected policy envelope. See
[github-pr-mode.md](github-pr-mode.md).

## Run bundle contract (draft)

```text
runs/<run-id>/
  manifest.json            # schema version, timestamps, tool versions, hashes
  events.jsonl             # append-only wteval lifecycle journal
  task-contract.md         # captured input, never modified in place
  git-summary.json         # base/head/repo/worktree/changed files
  check.json               # raw wtcraft result
  verify.json              # raw wtcraft result
  review.json              # optional structured model output
  decision.json            # human decision and reason; optional until submitted
  report.md                # generated, readable summary
```

`manifest.json` should hash each input artifact. The first implementation can
keep bundles local and out of Git by default; a team can choose a retention
location later.

## Trigger model

The MVP is event-triggered but not a long-running observer:

```text
manual `wteval review` -----------+
agent/session exit observed -------+--> capture frozen revision
handoff requested in wtflow -------+          |
post-commit hook (non-blocking) ----+          |
PR/CI check -----------------------+          v
                                          evaluate
```

The caller may be a human, wtflow, a runner exit hook, or CI. The result is
always bound to the captured Git revision. If the revision changes, the result
becomes stale and a new run is required.

Hook details are defined in [git-hook-triggers.md](git-hook-triggers.md).
Local hooks provide fast feedback and dogfooding convenience; they never
replace protected remote re-evaluation.

## Result presentation

One canonical result bundle should support multiple renderers:

- **CLI:** concise gate, review, human-decision, and artifact-path summary;
- **wtflow:** status badge plus Checks, Findings, Evidence, and Trace views;
- **CI:** check summary with evidence references and a failing exit code when a
  hard gate fails;
- **Markdown:** portable `report.md` for handoff or PR attachment.

The UI must show deterministic gate, advisory review, and human decision as
three separate fields. A model recommendation never paints a failed gate green.

## Log ownership

Avoid turning wteval into a duplicate conversation store:

| Artifact | Owner | wteval behavior |
| --- | --- | --- |
| Raw Codex/Claude/Agy stdout or transcript | Runner/vendor CLI | Keep only an optional local `log_path` reference; do not copy by default. |
| Session state and PID/liveness | Launcher sidecar | Read a snapshot when available; never become its canonical writer. |
| Scope and verification evidence | wtcraft | Capture raw JSON and hashes in the run bundle. |
| Evaluation lifecycle | wteval | Append small structured events to `events.jsonl`. |
| Traces and timings | OpenTelemetry | Store/export according to explicit local and remote configuration. |
| Model review and human decision | wteval | Store separately from deterministic evidence. |

Suggested lifecycle events are `capture.started`, `evidence.captured`,
`check.completed`, `verify.completed`, `review.completed`, and
`decision.recorded`. Events contain identifiers and summaries, not raw source
code or prompts by default.

## Reviewer graph

LangGraph is appropriate only for the bounded review workflow, not as the
system's source of authority:

```text
collect_facts
  -> apply_hard_rules
  -> summarize_diff
  -> identify_uncovered_risk
  -> formulate_recommendation
  -> require_human_decision
```

Hard rules execute before the model:

- `check.result == fail` means the recommendation cannot be `approve`.
- `verify.result == fail` means the recommendation cannot be `approve`.
- missing/invalid evidence means `block` or `request_changes`, never an
  optimistic pass.
- the model may not write task contracts, alter Git state, run arbitrary shell
  commands, or commit/merge.

### LangChain's role

Use small, typed tools rather than a general shell tool:

- `load_run_bundle(run_id)`
- `read_diff_summary(run_id)`
- `read_check_result(run_id)`
- `read_verify_result(run_id)`
- `write_review_draft(run_id, structured_output)`

The agent receives pre-collected evidence and cannot expand its own authority.

## Observability

Instrument the workflow with OpenTelemetry. Useful span structure:

```text
wteval.review
  wteval.collect_inputs
  wtcraft.check
  wtcraft.verify
  wteval.apply_hard_rules
  wteval.reviewer_graph
    wteval.summarize_diff
    wteval.risk_review
  wteval.write_report
```

Recommended attributes: `run.id`, `task.id`, `repo.id` (hashed), worktree
name, base revision, changed-file count, scope result, verification result,
recommendation, model/provider name, latency, and provider-reported token/cost
values when supplied. Do not emit source code, secrets, or raw patches by
default.

OpenTelemetry remains vendor-neutral. LangSmith is an optional trace/evaluation
destination, useful for comparing structured reviewer behavior across prompts,
models, or graph versions; it must not be required for local bundle generation.

## Evaluation design

The evaluation target is not “did the model write nice prose?” It is whether a
recommendation has the correct verdict and cites real evidence.

Initial fixture classes:

1. authorized change + passing verification -> eligible for `approve`;
2. out-of-scope file -> must not approve;
3. off-limits file -> must not approve;
4. failed verification -> must not approve;
5. missing verification evidence -> must not approve;
6. stale base revision / policy mismatch -> must flag or block once wtcraft
   policy envelopes exist;
7. clean checks but a test-coverage gap -> may recommend changes, but must not
   invent a failure.

Measure verdict accuracy, unsupported-claim rate, hard-rule violations,
latency, provider-reported cost, and human override rate.
