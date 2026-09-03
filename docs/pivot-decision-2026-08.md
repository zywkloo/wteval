# Pivot decision: reviewer harness to advisor evaluation lab

> Decision date: 2026-08-20.
>
> Status: current product reasoning. Revisit after the manual dataset pilot and
> a direct TokenSize comparison.

## Executive decision

Wteval is not a standalone runtime product. It is an offline evaluation lab for
a possible quota-aware preflight advisor implemented in wtcraft. TokenTracker
is the selected first telemetry/visibility dependency; wtflow rendering is
optional after the advisor proves useful.

The advisor concept remains useful for personal dogfooding and AI-engineering
portfolio evidence, but the scan invalidated “recommend an agent and model
before execution” as a unique feature thesis. TokenSize is an almost
feature-for-feature implementation precedent; CodeRoute and smaller routers
overlap the classification, budget, repository-risk, and outcome-feedback
loop. They do **not** yet demonstrate a mature competitor, user base, or market.

Proceed only as a measured experiment:

```text
useful personal workflow + defensible evaluation evidence
                       !=
          assumption of a standalone market moat
```

## How the concept changed

### Hypothesis 1 — agent-run reviewer and evaluator

The first concept captured task contracts, Git revisions, deterministic
verification, model findings, and human decisions. It also explored hooks, PR
mode, a local review daemon, and a bounded executor/reviewer loop.

That thesis was rejected because direct substitutes already provide:

- PR and local AI review;
- cross-agent coder/reviewer loops;
- worktree isolation and re-review after commits;
- session transcripts tied to Git;
- task/spec context and repository rules;
- generic traces, datasets, experiments, and human feedback.

The complete historical design is retained in
[the archive](archive/reviewer-eval-concept-2026-08-20/README.md).

### Hypothesis 2 — token and subscription usage dashboard

The original wtcraft motivation also included auditing which provider consumed
tokens or subscription allowance. That is a real user need, but not a useful
new product boundary.

TokenTracker, Tokscale, CodeBurn, OpenUsage, ccusage, token-stats, and
coding-agent usage trackers already parse many local agents, display
token/cost/quota windows, and export machine-readable data. TokenTracker also
ships native menu-bar/system-tray apps, widgets, achievements, skills syncing,
and a desktop pet. CodeBurn additionally classifies activity, compares models,
tracks Git yield, forecasts budget, and guards sessions.

Decision: use TokenTracker as the preferred first source and seek a stable,
versioned read-only JSON contract. Do not recreate dozens of mutable vendor
parsers or its polished dashboard/pet surfaces in wtcraft, wtflow, or wteval.

### Hypothesis 3 — pre-execution quota-aware advisor

The next concept moved the decision earlier:

```text
prompt + task contract + repo state + quota state
                         |
                         v
          work kind / size / risk classification
                         |
                         v
        role sequence + agent/model recommendation
                         |
                         v
               predicted quota range
```

This is stronger than a retrospective dashboard because it changes a decision
before scarce allowance is spent. Passive quota awareness remains in
TokenTracker. Model/role advice should be triggered by an enable-once workspace
instruction where possible, so the user's normal agent session calls the
independent quota analyzer on each new prompt or task. Manual “feed a task”
remains only a fallback for unsupported surfaces, demos, and debugging.

However, the second scan found direct concept collision:

- TokenSize discovers local coding agents and subscriptions, reads allowance,
  gives an explainable task route, enforces permission ceilings, executes
  locally, and records runs and verification.
- CodeRoute classifies coding steps, incorporates repository impact, routes
  across cost/capability tiers, and consumes execution feedback.
- pi-smart-router models subscription-window scarcity, cache economics, model
  tiers, and degraded-path escalation inside one coding harness.
- Cursor Auto and other native model selectors make basic immediate-task model
  choice a platform feature.

Therefore custom companion UI is no longer an MVP. TokenTracker already owns
that interface category; the remaining experiment is the decision engine and
its measured routing/reservation value.

### Market interpretation — overlap is not traction

The routing prototypes must not be over-weighted:

- the public TokenSize client and the unrelated open-source CodeRouter each had
  one GitHub star at the time of review;
- CodeRoute exposed a public service but no public core repository or adoption
  evidence was found;
- the visible repositories were driven primarily by one contributor;
- vendor sites describe capabilities and benchmarks, not independently
  verified active users, retention, revenue, or workflow pull.

These are prototype neighbors, not proven market competitors. Their existence
reduces feature novelty but does not prove that developers want a separate
preflight advisor.

By contrast, retrospective usage tools show materially stronger open-source
traction: CodeBurn had roughly 9.6k stars, Tokscale 5.1k, and ccusage 18k on
2026-08-20. That supports demand for visibility into usage; it does not prove
demand for another decision step before every coding task.

The primary product risk is therefore **unvalidated demand**, not incumbent
competition. The MVP must test whether the developer repeatedly accepts or
misses the advisor after novelty wears off.

The interaction risk is equally important: a repeated manual task-feeding step
is likely too much friction for daily use. The product should therefore test a
low-friction instruction path before concluding that the advisor itself has no
pull.

## Remaining narrow wedge

The following combination is not proven unique, but is narrower and testable:

1. **Explicit lifecycle advice.** Recommend `planning`, `execution`,
   `verification`, `repair`, or a multi-role sequence—not only a model.
2. **Wtcraft contract grounding.** Use Scope, Off-limits, declared
   verification, stage, and Git facts rather than prompt text alone.
3. **Personal subscription calibration.** Forecast provider-observed quota
   delta as p50/p90 ranges learned from one developer's history; keep it
   separate from API-equivalent cost.
4. **Capacity reservation.** Plan the complete task budget, including an
   independent verifier and likely repair cycle, instead of optimizing the next
   inference request in isolation.
5. **Deterministic outcome labels.** Evaluate recommendations against exact
   `wtcraft check` / `verify` results, repair rounds, and human overrides.
6. **Fully inspectable local policy.** No hosted judgment service, universal
   proxy, hidden model leaderboard, or automatic account switching.

TokenSize overlaps several of these items. The purpose of wteval is to discover
whether the remaining combination changes outcomes enough to matter.

## Why this can still help the AI Engineer pivot

Product novelty and portfolio value are different questions.

The work becomes credible AI-engineering evidence if it includes:

- a versioned structured-output classifier;
- a deterministic baseline and a labeled dataset;
- chronological held-out evaluation rather than a demo-only prompt list;
- calibrated uncertainty and explicit missing-data states;
- an optional LangGraph conditional/human-decision flow;
- OpenTelemetry traces and one LangSmith or Phoenix experiment;
- real cross-provider usage adapters;
- outcome linkage to deterministic engineering verification;
- a written error analysis showing where the advisor was wrong.

It has little AI-engineering resume value if it stops at a menu-bar token
counter, a few prompt keywords, a static role table, or an attractive animated
pet. The pet can still demonstrate thoughtful local-product and frontend UX.

## Runtime ownership decision

The possible runtime is split deliberately:

| Concern | Owner |
| --- | --- |
| Fixed advisor route and role/model policy | wtcraft configuration |
| Prompt/task/repository feature extraction | `wtcraft advise` |
| Instruction enable/disable and optional minimal advice rendering | wtflow |
| Provider quota snapshots and passive visibility | TokenTracker first; other adapters optional |
| Agent execution | Codex, Claude, Agy, Cursor, or another configured endpoint |
| Dataset construction and comparison | wteval |

The advisor route and recommended route are different facts. Initial dogfood
preference is a configured Agy/Gemini Flash-class advisor with ordered Cursor
Composer, Claude Haiku, and GPT-5.4-class fallbacks. Concrete model names remain
user configuration, not product constants. Cursor cannot be an automatic
fallback until a stable invocation adapter exists.

Role preference and endpoint capability must also remain distinct. A human
role matrix says what is preferred; a generated capability matrix says whether
an endpoint can run headlessly, honor model selection, return structured
output, expose quota, and authenticate successfully.

## Build, borrow, avoid

### Build only if the pilot passes

- task-contract feature extraction;
- decision/outcome schemas that join wtcraft stages and verification;
- a deterministic classifier baseline;
- personal forecast calibration and reservation policy;
- evaluator and error-analysis reports;
- a stable TokenTracker adapter plus the smallest workspace-instruction and
  CLI/JSON advice path; wtflow rendering only after measured pull.

### Borrow or integrate

- token/quota observations from TokenTracker through a versioned JSON contract,
  with other established local tools as fallback adapters;
- LangSmith or Phoenix for experiment visualization;
- OpenTelemetry/OpenInference conventions;
- existing agent launchers, ACP adapters, and model gateways;
- public routing baselines such as RouteLLM where methodologically applicable.

### Avoid

- another token dashboard or provider-log parser collection;
- hosted model resale or an OpenAI-compatible proxy;
- generic agent dispatch and account rotation;
- hidden prompt capture, clipboard watching, keystroke interception, or
  terminal scraping;
- PR review, review loops, session recording, or worktree orchestration;
- claiming an optimal route from one observed execution;
- turning opaque subscription quota into a precise dollar conversion.

## Stop conditions

Stop the standalone effort or reduce it to a wtcraft example if any of these
remain true after the pilot:

- TokenSize already solves the personal workflow well enough;
- task-contract features do not beat a prompt-only or fixed-role baseline;
- quota observations cannot be attributed to tasks with useful confidence;
- p50/p90 forecasts are not calibrated after enough personal runs;
- recommendations do not change user choices or verified outcomes;
- the enable-once instruction path cannot be made reliable enough and manual
  feeding is ignored in real work;
- maintaining provider adapters dominates the evaluation work;
- the result cannot be explained without product-novelty claims that the
  competitive evidence contradicts.

## Evidence required to resume implementation

1. Label 30–50 real tasks with work kind, size, risk, and intended role
   sequence.
2. Capture selected route, advisor route, user override, observed usage,
   verification result, and repair rounds.
3. Compare fixed-default, deterministic-rule, prompt-only LLM, and
   contract-grounded advisor baselines.
4. Run a small opt-in comparison against TokenSize on the same task prompts.
5. Publish metrics and failure examples before adding an agent launcher,
   dashboard, or additional framework dependency.
