# MVP plan: TokenTracker-backed advisor, Quota Cat overlay, and offline proof

> Status: proposed dogfood sequence. Runtime work belongs in wtcraft/wtflow;
> evaluation work belongs here.

## MVP outcome

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

## Phase 0 — demand, baseline, and data gate

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

## Phase 1 — schemas and labeled dataset

The v1 schema, synthetic fixtures, deterministic baselines, and batch runner
are sketched in this repository. Real labeled tasks are still the gate.

- Freeze decision/outcome schema v1.
- Human-label work kind, size, risk, and intended role sequence.
- Split chronologically into development and held-out sets.
- Add fixed-default and deterministic-rule baselines.
- Store redacted examples and labels locally.

Exit: label definitions are consistent and at least 30 examples are usable.

## Phase 2 — `wtcraft advise` dry run

- Accept prompt/stdin and emit human plus JSON output.
- Read task contract, stage, Git summary, role preferences, and endpoint
  capabilities.
- Run deterministic classification and record explicit uncertainty.
- Produce recommendations and reason codes without launching an agent.
- Record Accept/Override/Dismiss.

Exit: output is deterministic when the LLM path is disabled and no missing
source is fabricated.

## Phase 3 — fixed async advisor

- Add configured `advisor` role after role-models v2 is stable.
- Use an Agy/Gemini Flash-class route first with ordered configured fallback.
- Require versioned structured output.
- Support `always`, `low-confidence`, `shadow`, and `off` invocation modes.
- Use `always` for initial dogfood and run rules in shadow.
- Debounce follow-ups within the same task/stage.
- Record advisor latency and quota overhead separately.

Exit: all outputs validate; recursive self-routing is impossible; failures
degrade to deterministic/manual advice.

## Phase 4 — instruction integration and Quota Cat overlay

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

## Phase 5 — forecast and reservation

- Start with bucketed personal p50/p90 estimates.
- Predict reported tokens and subscription quota delta separately.
- Reserve expected capacity for verifier and repair roles.
- Backtest chronologically and report interval coverage.
- Return unavailable for unsupported providers.

Exit: forecasts are calibrated enough to be more informative than a wide
uninformative interval and never imply subscription billing precision.

## Phase 6 — outcome loop and public report

- Attach actual route, usage observation, check/verify result, repair rounds,
  and human completion.
- Compare fixed, rule, LLM, contract-grounded, TokenSize-preview, and
  CodeRouter-JSON baselines.
- Export OpenTelemetry traces and one LangSmith or Phoenix experiment.
- Publish metrics, failure cases, privacy limits, and adapter drift.

Exit: evidence supports continuing, narrowing, or stopping. A polished demo is
not a substitute for the report.

## MVP exclusions

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

## Resume gate

Implementation beyond the first vertical slice requires:

- held-out classifier results above simple baselines;
- measured p50/p90 coverage;
- at least two observation adapters or an explicit single-provider scope;
- deterministic outcome linkage;
- human override analysis;
- a documented comparison with TokenSize's available workflow;
- a documented TokenTracker schema/compatibility result;
- evidence that the feature is used repeatedly after the novelty wears off.
