# MVP plan: real paired capability runs and a reproducible report

> Status: active execution plan, reviewed 2026-09-11. This plan supersedes the
> advisor-first delivery order. The prior advisor sequence is retained below
> as deferred reference; it does not schedule runtime work in wtcraft.

## Outcome and current boundary

Produce a real contract/no-contract pilot, then a report covering at least 30
qualified paired tasks. Measure whether explicit task contracts change verified
outcomes. Wtcraft's protected authorization adoption is a separate question and
release track; neither a positive nor a null contract result settles it.

The stdlib validators, baselines, report writers, task builders, mutation/PBT,
and schedule/record interfaces exist. Worktree preparation, live check/verify
capture, and a real runner are not yet connected. The 2026-09-11 local full
suite passed, including 54 unit tests and additional smoke checks; this is
harness validation, not evidence of agent or product effectiveness.

## P0 — correct measurement and qualify a small task set

- [x] Preserve missing usage as unknown. Use consumption and successes from the
  same quota-observed cohort, report coverage, and never combine incompatible
  provider/window units. Current scoring can show zero cost for missing data.
- [x] Make run identity unique across task, arm, endpoint, model, configuration,
  and repetition; reject collisions before execution or writing records.
- [ ] Separate runnable verification commands from descriptions and test paths.
  Mutation records now separate the executable command from descriptive context;
  history units still need a known runner to materialize a command.
  Materialize history verification units through a known runner instead of
  attempting to execute directories or mutation annotations as shell commands.
- [ ] Rebuild or revalidate existing candidate artifacts using the current
  baseline/determinism checks. A scanner match or killed mutant is a candidate,
  not an admitted task. Check for harness failures and generated-copy drift.
- [ ] Admit 5–10 tasks whose buggy state fails and reference repair passes the
  same frozen oracle reproducibly. Record exclusions and task origin. Keep
  mutation families and history units from one commit identifiable as clusters.

Exit: the initial task set has runnable commands and reproducible admission
records; metric and identity regressions have focused tests. Any schema changes
update constants, validators, schemas, and agreement tests together.

## P0 — execute one fixed configuration in both arms

- [ ] Connect the bounded executor described in [executor.md](executor.md):
  prepare an isolated workspace, invoke one configured agent or a recorded
  human-assisted run, collect outcomes, and persist records.
- [ ] Freeze prompt, base revision, toolchain, permissions, and budget. Randomize
  or counterbalance arm order. Keep scope and verification scoring identical;
  only the contract arm receives the explicit contract intervention.
- [ ] Keep the scoring contract and oracle outside agent-editable state. Re-score
  submitted changes with trusted inputs. Both arms receive the same task setup;
  neither may obtain reference repairs through files, Git history, or shared state.
- [ ] Complete 5–10 qualified tasks in both arms with one fixed configuration.
  Record wall time, failures, timeouts, repairs, and available usage. A missing
  quota adapter does not block success/scope measurement.
- [ ] Report all attempted runs, scoring coverage, and paired outcomes. Separate
  infrastructure errors from agent failures and never silently drop either.

Exit: a reproducible pilot report and traceable per-run evidence. The existing
ManualRunner stub or synthetic records do not satisfy this gate. Build only
what this experiment needs; no general launcher, router, or scheduling service.

## P1 — expand and publish the result

- [ ] Reach at least 30 qualified tasks with both arms recorded. Add 2–3 agent
  configurations only after the single-configuration pipeline is reliable.
- [ ] Report historical and mutation tasks separately. Show paired differences,
  discordant task outcomes, uncertainty, related-task clusters, failures, and
  missingness. Do not treat correlated mutants as independent real-world tasks.
- [ ] State sample size, single-codebase provenance where applicable, and the
  weak-test/weak-oracle limitation. Verified success means the declared tests
  passed, not semantic correctness.
- [ ] Keep real data private. Publish methodology and a privacy-reviewed
  aggregate report; wtcraft receives the contract-arm finding and report link.

Exit: evidence supports continuing, narrowing, or stopping. An early pilot or
negative finding may be reported before N=30 when labeled accordingly; it is
not the full experiment completion gate.

## P2 — only improvements demanded by the results

Improve oracle coverage, task diversity, or run reliability when failure analysis
shows a specific need. Do not expand the mutation/PBT framework for its own sake.
Additional providers, visualization backends, and telemetry integrations need a
measurement question the existing files cannot answer.

## Advisor resume gate

Advisor work remains deferred until real outcomes show repeatable, potentially
useful differences between routes, observed usage is sufficient for the intended
claims, and a recurring user decision needs help. A quota forecast additionally
requires calibrated held-out observations. Missing quota does not become a
forecast through API-price conversion.

The advisor phases below require a new explicit prioritization decision after
that gate. Their product-readiness requirements apply to advisor claims, not to
the capability pilot. GUI, quota prediction, and advisor runtime are not current
experiment dependencies.

## Deferred advisor reference

The earlier sequence is preserved for context. All phases in this section are
unscheduled; the active order above takes precedence.

### MVP outcome

The developer keeps TokenTracker as the existing subscription dashboard and
heavy desktop companion. Quota Cat adds a small distinct cat-and-jars overlay,
not another analytics client. The new vertical slice begins with a stable
read-only quota snapshot and a separate advisor command. The advisor path is enabled once per
workspace by installing or updating a short `AGENTS.md`/provider-instruction
line. Supported agents then call the analyzer for each fresh prompt or task:

```text
Recommended: Codex / executor / balanced-coding
Sequence: executor -> independent verifier
Why: bounded implementation; verification declared; quota headroom available
Reserve: one verification pass + one repair round
Confidence: 0.82

[Use] [Choose another] [Ignore]
```

The fixed advisor runs asynchronously and must not delay direct agent use or
pretend it can intercept prompts typed into arbitrary third-party clients.
TokenTracker never receives the prompt. Manual task feeding remains a fallback
for unsupported surfaces and debugging, not the intended daily path.

### Deferred advisor phase 0 — demand, baseline, and data gate

- Try TokenSize preview on a small, non-sensitive opt-in prompt set.
- Run the distinct open-source CodeRouter `route --json` command as a local
  baseline without adopting its launcher or daemon.
- Export local usage/quota data from TokenTracker and freeze representative
  configured, stale, exhausted, rate-limited, and unavailable JSON fixtures.
- Select 30–50 recent wtcraft/wtflow tasks.
- Confirm that decisions can be joined to check/verify outcomes.
- Record missing data and attribution confidence before writing a forecast.

Exit: confirm that the developer repeatedly wants the recommendation, identify
a measurable question existing prototypes do not already answer, and verify
that usable outcome data exists—or stop the standalone concept.

### Deferred advisor phase 1 — schemas and labeled dataset

The v1 schema, synthetic fixtures, deterministic baselines, and batch runner
are implemented. Human-reviewed labels and real outcomes are still the gate.

- Freeze decision/outcome schema v1.
- Human-label work kind, size, risk, and intended role sequence.
- Split chronologically into development and held-out sets.
- Add fixed-default and deterministic-rule baselines.
- Store redacted examples and labels locally.

Exit: label definitions are consistent and at least 30 examples are usable.

### Deferred advisor phase 2 — `wtcraft advise` dry run

- Accept prompt/stdin and emit human plus JSON output.
- Read task contract, stage, Git summary, role preferences, and endpoint
  capabilities.
- Run deterministic classification and record explicit uncertainty.
- Produce recommendations and reason codes without launching an agent.
- Record Accept/Override/Dismiss.

Exit: output is deterministic when the LLM path is disabled and no missing
source is fabricated.

### Deferred advisor phase 3 — fixed async advisor

- Add configured `advisor` role after role-models v2 is stable.
- Use an Agy/Gemini Flash-class route first with ordered configured fallback.
- Require versioned structured output.
- Support `always`, `low-confidence`, `shadow`, and `off` invocation modes.
- Use `always` for initial dogfood and run rules in shadow.
- Debounce follow-ups within the same task/stage.
- Record advisor latency and quota overhead separately.

Exit: all outputs validate; recursive self-routing is impossible; failures
degrade to deterministic/manual advice.

### Deferred advisor phase 4 — instruction integration and Quota Cat overlay

- Keep TokenTracker as the dashboard, menu-bar, widget, and desktop-pet
  surface. Do not rebuild those features in wtflow.
- Add a small optional Quota Cat overlay: one cat, a few labeled provider
  jars, remaining-water level, reset marker, stale/unknown state, and a locked
  verify/repair reserve.
- Keep the overlay renderer independent of TokenTracker storage; consume the
  canonical snapshot and recommendation JSON.
- Allow direct provider adapters or an explicit snapshot when TokenTracker is
  not installed.
- Add a workspace enable/disable toggle that prepares an auditable instruction
  patch for `AGENTS.md` or an equivalent provider instruction file.
- Show enabled, missing, drifted, and unsupported instruction states.
- Keep explicit task feeding via click/paste, drag, or configured hotkey as a
  fallback; never monitor the clipboard silently.
- Run `wtcraft advise` asynchronously.
- Initially render the recommendation in CLI/JSON. The cat may show a subtle
  recommendation/facing state, but full details remain on demand.
- Provide Use, Choose another, Ignore, and Copy/Open actions.
- Do not automate ACP/Cursor/Claude/Codex dispatch in the first slice.

Exit: integration changes no Git or agent state without a user action, never
blocks a prompt, preserves TokenTracker's no-prompt boundary, distinguishes
instruction state from quota state, and remains understandable with animation
disabled.

### Deferred advisor phase 5 — forecast and reservation

- Start with bucketed personal p50/p90 estimates.
- Predict reported tokens and subscription quota delta separately.
- Reserve expected capacity for verifier and repair roles.
- Backtest chronologically and report interval coverage.
- Return unavailable for unsupported providers.

Exit: forecasts are calibrated enough to be more informative than a wide
uninformative interval and never imply subscription billing precision.

### Deferred advisor phase 6 — outcome loop and public report

- Attach actual route, usage observation, check/verify result, repair rounds,
  and human completion.
- Compare fixed, rule, LLM, contract-grounded, TokenSize-preview, and
  CodeRouter-JSON baselines.
- Export OpenTelemetry traces and one LangSmith or Phoenix experiment.
- Publish metrics, failure cases, privacy limits, and adapter drift.

Exit: evidence supports continuing, narrowing, or stopping. A polished demo is
not a substitute for the report.

### MVP exclusions

- agent launch or automatic account switching;
- a provider gateway or billing service;
- generic session/token dashboards;
- a second dashboard, menu-bar app, widget suite, or achievement system;
- a generic pet clone; only the narrow cat-and-jars recommendation overlay is
  in scope;
- PR review or merge automation;
- ACP dependence;
- hidden clipboard/keystroke/terminal prompt capture;
- team SaaS, cloud synchronization, or multi-device state;
- claims that an unexecuted route would have succeeded.

### Advisor product-readiness gate

Implementation beyond the first vertical slice requires:

- held-out classifier results above simple baselines;
- measured p50/p90 coverage;
- at least two observation adapters or an explicit single-provider scope;
- deterministic outcome linkage;
- human override analysis;
- a documented comparison with TokenSize's available workflow;
- a documented TokenTracker schema/compatibility result;
- evidence that the feature is used repeatedly after the novelty wears off.
