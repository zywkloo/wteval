# MVP plan

> **Status:** Superseded by the manual go/no-go pilot in
> [competitive-landscape-2026-08.md](competitive-landscape-2026-08.md). Do not
> implement this MVP as written.

## Build order

### Milestone 0 — facts-only run recorder

Goal: a useful artifact without LangChain, LangGraph, or any model API.

- [ ] Define `manifest.json`, `check.json`, `verify.json`, and `report.md`
      schemas/examples.
- [ ] Implement `wteval review --repo ... --worktree ...` as a local command.
- [ ] Invoke wtcraft's machine protocol and capture command versions/exit codes.
- [ ] Generate a report with hard-rule verdict and `human decision: pending`.
- [ ] Bind every result to the captured Git revision and mark it stale after the
      worktree changes.
- [ ] Implement configurable trigger profiles (`fast`, `balanced`, `strict`)
      with separate policies for capture, deterministic verify, advisory
      review, and adjudication.
- [ ] Add trailing-edge local debounce and exact-SHA stale/cancellation rules.
- [ ] Persist a small append-only `events.jsonl`; reference runner logs rather
      than copying complete agent transcripts.
- [ ] Implement `capture`, `evaluate`, and `show`, with `review` as their
      one-shot convenience command.
- [ ] Add fixture-based tests for passing scope, scope violation, and failed
      verification.

Definition of done: a reviewer can run one command and receive a reproducible,
facts-only report. No provider account is required.

### Milestone 1 — bounded LLM reviewer

Goal: add an advisory reviewer without weakening deterministic gates.

- [ ] Wrap the captured bundle with typed LangChain tools.
- [ ] Implement the fixed LangGraph flow described in `architecture.md`.
- [ ] Require a JSON schema: `recommendation`, `risk_level`, `findings[]`, and
      `evidence_refs[]`.
- [ ] Enforce hard rules after model output as well as before it.
- [ ] Persist the model response separately from facts and label it `advisory`.
- [ ] Add human labels for each finding (`valid`, `invalid`, `duplicate`,
      `style_only`, `cannot_verify`, or `fixed_before_merge`).
- [ ] Record the final human decision separately from the reviewer
      recommendation.
- [ ] Add a bounded executor-reviewer loop with fixed contract/policy digest,
      exact revision per round, finding lifecycle, and `max_rounds`.
- [ ] Require later rounds to verify accepted prior findings before reporting
      new findings.

Definition of done: a model cannot return `approve` when scope or verification
failed, and every rendered finding links to a captured artifact.

### Milestone 2 — tracing and evaluation

Goal: make the reviewer debuggable and measurable.

- [ ] Add OpenTelemetry spans and local console/JSON exporter.
- [ ] Add opt-in LangSmith export, configured only through environment/config.
- [ ] Build evaluation fixtures from wtcraft's policy-envelope test cases.
- [ ] Record verdict accuracy, unsupported claims, latency, and human override.
- [ ] Add a comparison command for already-configured providers/models; this is
      an experiment flag, not a routing product.

Definition of done: two reviewer configurations can be compared against the
same frozen run bundles with results stored locally.

The first 10–20 labeled bundles should come from real wtcraft and wtflow tasks;
see [dogfooding.md](dogfooding.md). Synthetic fixtures protect hard rules, but
they do not establish that the reviewer is useful in daily engineering work.

## Initial technical choices to validate

- Keep `wteval` a separate Python package/repository until its interface is
  stable; do not add heavy runtime dependencies to the wtcraft core.
- Consume only public wtcraft JSON command outputs. File parsing is a fallback,
  not the primary integration.
- Use a strict structured-output schema and generate human-readable Markdown
  from it.
- Keep default operation local. Remote tracing and any model provider require
  explicit opt-in.

## Open questions before implementation

1. Where should run bundles be retained: local cache, a repository artifact
   folder, or CI artifacts?
2. Which redaction policy is required before trace export, particularly for
   diffs and test output?
3. Should the initial human decision be a CLI prompt, a checked-in JSON file,
   or a wtflow UI action?
4. Does the first vertical slice target local worktrees only, or GitHub PRs as
   well?

The safe default is local worktrees, locally retained bundles, a CLI decision
record, and no patch/source-code export to tracing.

GitHub PR support follows as a distinct adapter after the local bundle schema is
stable. It accepts immutable PR facts and optional wtcraft policy evidence; it
must not expect `.worktree-task.md` to exist. See
[github-pr-mode.md](github-pr-mode.md).
