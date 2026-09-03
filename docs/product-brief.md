# Product brief: quota-aware advisor evaluation

> Status: current cross-project brief; implementation is not authorized by this
> document.

## Product statement

Wteval evaluates a local coding-agent advisor that recommends the next
lifecycle role, agent/harness, and model tier before a developer spends scarce
subscription capacity.

The possible runtime experience uses TokenTracker for telemetry/visibility and
belongs to wtcraft for prompt-aware advice:

```text
TokenTracker renders provider headroom, burn, dashboard, and pet
              |
       user enables workspace instruction once
              |
              v
supported agent calls analyzer on each new prompt/task
              |
              v
wtcraft classifies task + reads repo/task/quota facts
              |
              v
CLI/JSON returns a recommended role, agent, and model tier
              |
     click for reasons / accept / override / ignore
              |
              v
developer executes in an existing coding agent
              |
              v
usage + check/verify + repair outcome return to the dataset
```

Wteval asks whether that loop improves decisions. It does not own TokenTracker,
the instruction patch UI, agent launch, or provider account.

## User problem

One developer may have several coding-agent subscriptions with different
strengths and rolling limits. Before starting a task, they currently make an
intuition-based choice:

- Is this discovery, planning, implementation, verification, or repair?
- Does it require a frontier reasoning model or a fast execution model?
- Which subscribed agent is available now?
- Will this task consume the capacity needed for independent verification?
- Was the last similar choice actually successful, or merely cheap?

Usage dashboards answer what happened. Generic routers answer which API model
fits a prompt. The research question is whether explicit engineering-task and
verification evidence improves the whole-task allocation decision.

## Target user and moment

Initial user: the wtcraft author, working locally across Codex, Claude/Agy,
Cursor, and related tools.

Passive moment: during normal work, without requiring a task prompt. Active
advice moment: after a workspace-level instruction causes a supported agent to
call the analyzer for a fresh prompt or task. Manual task feeding is a fallback
for unsupported surfaces, demos, and debugging. Follow-up prompts within the
same task/stage are debounced.

This is deliberately a personal dogfood problem first. No team or enterprise
claim is justified yet.

## Recommendation contract

The recommendation contains:

- `work_kind`: discovery, planning, execution, verification, repair, finishing;
- size, risk, confidence, and missing information;
- recommended role sequence;
- preferred agent/harness and semantic model/reasoning tier;
- current availability and quota-source confidence;
- token and subscription-quota p50/p90 ranges when supported;
- reserved capacity for verification and repair;
- auditable reason codes and fallback route;
- advisor route and advisor overhead, recorded separately;
- Accept, Override, or Dismiss decision.

It never claims that one unexecuted alternative would definitely have been
better.

## Telemetry and rendering contract

TokenTracker remains the passive usage/quota interface and does not receive
prompts from Quota Cat. Quota Cat consumes a minimum read-only structured
snapshot containing observed facts:

- remaining provider allowance and reset window;
- current burn pace and source freshness;
- active/idle agent sessions when a reliable source exists;
- reserved capacity for verification/repair;
- unknown or stale data as an explicit state.

The preferred active control is a one-click workspace enable/disable toggle.
When enabled, wtcraft prepares a short, auditable instruction for `AGENTS.md` or
the equivalent provider instruction file:

```text
For each new user prompt or task, call the configured quota analyzer first.
Treat the result as advisory context. Continue normally if the analyzer is
missing, slow, or unavailable.
```

The exact instruction is generated from local configuration and may differ by
agent surface. The integration must show whether the instruction is enabled,
missing, drifted, or unsupported. Manual stdin/paste/task feeding remains a
fallback, not the primary daily workflow. Advice first appears as human-readable
CLI plus JSON; wtflow or a small TokenTracker renderer is optional only after
the decision engine proves useful.

## Fixed advisor runtime

The initial dogfood configuration may use a fixed lightweight advisor route:

```text
primary: configured Agy / Gemini Flash-class endpoint
fallback: Cursor Composer -> Claude Haiku -> configured GPT-5.4-class endpoint
```

Names are configuration, not constants. An endpoint enters the automatic
fallback chain only after its availability, headless/async invocation, model
selection, and structured-output behavior are verified.

`advisor_route` is the model making the recommendation.
`recommended_route` is the agent/model/role proposed for the actual task. They
must never be collapsed.

## Product boundaries

| Build/evaluate | Borrow | Do not build |
| --- | --- | --- |
| Task-contract features, lifecycle labels, decision/outcome schema, personal calibration, reservation policy, instruction freshness checks, error analysis. | TokenTracker quota/usage facts and existing UI, agent launch, model gateways, trace UI, experiment UI. | Token dashboard, provider parser zoo, second pet/widget/menu-bar client, PR reviewer, ACP router, hosted gateway, auto account switcher, clipboard/keylogger prompt capture. |

## Success criteria

The pilot succeeds only if:

- task labels are reliable enough for a held-out comparison;
- contract grounding beats a fixed/default or prompt-only baseline;
- forecast intervals have measured coverage;
- recommendation reasons never fabricate quota or capability facts;
- at least some recommendations change after outcome feedback;
- the enable-once instruction path changes a real user choice without becoming
  interruptive or brittle;
- advisor overhead is small relative to avoided retries or preserved capacity.

## Honest positioning

The direct workflow is described by TokenSize and adjacent prototypes, but no
strong independent adoption signal was found. The safe claim is therefore
about evaluation quality, local inspectability, and wtcraft-specific outcome
grounding—not invention of coding-agent routing or entry into a validated
market.

If built and measured:

> Built and dogfooded a local quota-aware advisor for coding-agent tasks,
> evaluating role/model recommendations against personal subscription usage,
> human overrides, and deterministic Git verification outcomes.
