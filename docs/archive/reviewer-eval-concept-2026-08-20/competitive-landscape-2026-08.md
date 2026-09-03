# Competitive landscape — August 2026

## Executive conclusion

The original wteval idea sits at the intersection of several already crowded
markets:

1. AI pull-request review;
2. local coder/reviewer agent loops;
3. coding-agent session capture and Git provenance;
4. spec, policy, and agent governance;
5. LLM tracing and evaluation platforms.

No individual feature in the current proposal is a defensible standalone
product boundary. The closest competitors already cover not only PR comments,
but also local review before push, worktrees, re-review after new commits,
debounce/cooldown, cross-agent fix loops, task or issue context, session
transcripts, Git-linked checkpoints, OpenTelemetry traces, datasets, human
labels, and experiment comparison.

Therefore:

> Do not build wteval as another local daemon, agent launcher, PR reviewer,
> session recorder, or generic eval dashboard.

The viable residue is much smaller: a **wtcraft-specific evaluation lab** that
turns authoritative task-policy and deterministic verification records into a
reproducible dataset, imports findings from existing reviewers, and measures
which reviewer configuration actually helps. This can remain a portfolio
project and research artifact; it does not yet justify a separate product.

## Market map

### 1. AI PR review platforms

| Product | Relevant capabilities | Consequence for wteval |
| --- | --- | --- |
| [GitHub Copilot code review](https://docs.github.com/en/copilot/concepts/agents/code-review) | Automatic reviews through rulesets, repository context, custom instructions, `AGENTS.md`, skills, MCP, and suggested fixes. | GitHub-native review, instructions, and automatic triggering are commodities. |
| [CodeRabbit](https://docs.coderabbit.ai/overview/pull-request-review) | Incremental PR review, codebase context, linters, issue acceptance criteria, custom pre-merge checks, and feedback learning. Its [Codex integration](https://docs.coderabbit.ai/cli/codex-integration) explicitly supports implement → structured review → fix loops and reads `AGENTS.md`. | “Codex writes and another system reviews until fixed” is already a documented workflow. |
| [Cursor Bugbot](https://cursor.com/guides/ai-code-review) | PR and local review, repository rules, incremental review, fixes, and learned rules. | Local-to-PR review continuity and rule files are not differentiators. |
| [Claude Code Review](https://support.claude.com/en/articles/14233555-set-up-code-review-for-claude-code) | Multi-agent review with a verifier, automatic review on PR open or push, deduplicated inline findings, and severity. | A reviewer graph plus verifier is already a first-party feature. |
| [Greptile](https://www.greptile.com/docs/introduction) | Whole-codebase graph, automatic PR review, inline findings, and suggested fixes. | Repository-aware review is an established category. |
| [Graphite Agent](https://graphite.com/docs/ai-reviews) | Automatic full-PR review, custom rules, codebase context, and finding-quality metrics. | Reviewer acceptance metrics are already commercialized. |
| [Qodo Merge](https://docs.qodo.ai/code-review) | Multi-agent review, repository and PR history, tickets, organization rules, local review, governance, and handoff to coding agents for fixes. | Ticket context plus centralized policy is not unique to a task file. |

### 2. Direct local coder/reviewer-loop competitors

These are the closest substitutes for the manual workflow that motivated
wteval.

#### coding-review-agent-loop

[coding-review-agent-loop](https://github.com/wwind123/coding-review-agent-loop)
is almost a direct implementation of the proposed Codex ↔ Claude/Agy loop. It
is a standalone local CLI that reuses authenticated `claude`, `codex`,
`gemini`, `agy`, and `gh` accounts. It can start from a task, issue, or existing
PR; reverse coder and reviewer roles; run plan review; use multiple reviewers;
iterate implementation and findings; persist resumable GitHub state; cap
rounds; detect deadlock or `needs-human`; run tests and CI gates; and optionally
merge.

This eliminates “cross-provider reviewer orchestration” as a wteval thesis.
If orchestration is needed, integration or contribution is cheaper than a new
runner.

#### reviewd

[reviewd](https://pypi.org/project/reviewd/) is a local review assistant for
GitHub and Bitbucket that invokes Claude, Gemini, or Codex CLI. It already uses
isolated worktrees, runs real tests and linters, emits structured findings,
stores state in SQLite, supports one-shot and continuous modes, skips already
reviewed commits, re-reviews new commits, and exposes polling intervals,
minimum-diff thresholds, cooldowns, and auto-approval.

This eliminates the proposed watcher, worktree reviewer, debounce/cooldown,
and “review on push” machinery as differentiation.

#### First-party/local integrations

CodeRabbit's CLI exposes structured agent output and committed, uncommitted,
and untracked review scopes. Cursor offers local review before PR review. These
make a custom local reviewer adapter useful only as glue, not as a product.

### 3. Session evidence and Git provenance

| Product | Relevant capabilities | Consequence for wteval |
| --- | --- | --- |
| [Entire](https://docs.entire.io/agents/overview) | Installs coding-agent lifecycle hooks and writes full transcripts, file changes, tokens, and tool calls as Git-linked checkpoints on an `entire/checkpoints/v1` branch. Supports Claude Code, Codex, Copilot CLI, Cursor, Factory, Gemini, OpenCode, and external plugins. | The proposed “immutable agent evidence bundle tied to a commit” is already a product. Do not recreate transcript capture. |
| [SpecStory](https://specstory.com/lore) | Captures sessions across Claude Code, Codex, Cursor, and Antigravity locally, then mines evidence-backed workflows into reusable skills. | Cross-agent local session history and evidence mining are covered. |
| [GitHub agent sessions](https://docs.github.com/en/copilot/how-tos/copilot-on-github/use-copilot-agents/manage-and-track-agents) | Session logs expose tools, validation, token usage, and duration; agent commits link back to their session logs; users can query prior sessions. | Cloud-agent provenance and auditability are moving into the host platform. |
| [Harness AI Engineering Insights](https://developer.harness.io/docs/software-engineering-insights/harness-sei/insights/ai-engineering/) | Local agent telemetry correlated to commits, AI code attribution, ship rate, cost, errors, PR outcomes, and organization dashboards. | Generic agent-usage and productivity analytics are an enterprise category. |

The only evidence Entire does not inherently own is **wtcraft's authority
semantics**: allowed paths, off-limits paths, protected policy source, and the
separation between deterministic gate, advisory finding, and human decision.
That belongs in wtcraft's protocol or an adapter, not a second recorder.

### 4. Specs, task context, policy, and governance

| Product | Relevant capabilities | Consequence for wteval |
| --- | --- | --- |
| wtcraft itself | Git-native task contract, protected policy authority, scope checking, deterministic verification, and JSON protocol. | This is the strongest unique asset. Duplicating it in wteval weakens the boundary. |
| [Kiro](https://kiro.dev/docs/) | Requirements/design/task specs, steering, hooks, permissions, custom agents, skills, checkpoints, headless mode, CI, and a unified harness across IDE/CLI/Web/Mobile. | Spec + hooks + agent lifecycle is a mature first-party harness surface. |
| [Tessl](https://tessl.io/) | Versioned and evaluated agent skills, registry, activation measurement, security scanning, audit logs, and cross-agent governance. | Generic “govern and evaluate agent instructions” is already an enterprise platform. |
| CodeRabbit and Qodo | Consume repository instructions, tickets, acceptance criteria, and organization rules during review. | A `.worktree-task.md` by itself is not differentiation. Authority and tamper-resistance may be. |

### 5. LLM observability and evaluation

| Platform | Relevant capabilities |
| --- | --- |
| [LangSmith](https://docs.langchain.com/langsmith/evaluation) | Traces, datasets, offline and online evaluators, experiments, human feedback, and model/prompt/tool comparisons. |
| [Arize Phoenix](https://arize.com/docs/phoenix) | Open-source OpenTelemetry/OpenInference tracing, datasets, experiments, human labels, and deterministic or LLM evaluators. |
| [Braintrust](https://www.braintrust.dev/docs/evaluate) | Versioned datasets and experiments, scorers, production-log sampling, human feedback, and CI evaluation. |
| [W&B Weave](https://docs.wandb.ai/weave/concepts/what-is-weave) | Tracing, datasets, evaluation, versioning, prompt/model comparison, feedback, and monitoring. |
| [Langfuse](https://langfuse.com/docs/api-and-data-platform/features/experiments-api) | Traces, experiments, scores, datasets, and user feedback. |
| [Harness AgentTrace](https://www.harness.io/products/platform/agent-trace) | OTel-native execution graphs connected to eval scores; open-source collection and evaluator layers. |

Building another trace store, generic evaluator abstraction, experiment UI, or
dashboard would be undifferentiated. OpenTelemetry should be an export format;
Phoenix or LangSmith should be a backend. LangGraph is justified only if a real
conditional evaluator workflow emerges—it should not be added to decorate the
resume.

## Feature-level collision check

| Proposed wteval feature | Collision | Decision |
| --- | --- | --- |
| Launch Claude/Codex/Agy headlessly | coding-review-agent-loop, native agent CLIs, Kiro | Do not build. |
| Executor → reviewer → fixer loop | coding-review-agent-loop, CodeRabbit + Codex, Claude Code Review | Do not build. Integrate if useful. |
| Worktree-isolated review | reviewd, wtcraft/wtflow | Do not duplicate. |
| Commit/push/PR triggers and debounce | reviewd, Cursor, Git hooks/CI | Treat as configuration glue only. |
| PR summaries and inline comments | Copilot, CodeRabbit, Cursor, Claude, Qodo, Greptile, Graphite | Do not build. |
| Agent transcripts and tool-call capture | Entire, SpecStory, GitHub sessions | Import or link; do not own capture. |
| OTel traces and eval dashboard | Phoenix, LangSmith, Braintrust, Weave, Langfuse, Harness | Export to an existing backend. |
| Task/spec context | Kiro, Tessl, tickets, `AGENTS.md`, reviewer rules | Not enough by itself. |
| Tamper-aware task authorization plus deterministic scope evidence | wtcraft | Keep in wtcraft; expose a stable evidence schema. |
| Human-labeled comparison of reviewer findings on identical wtcraft changes | Partly served by eval platforms, but not packaged for wtcraft semantics | Viable experiment/lab scope. |

## Recommended repositioning

### Keep the three-project boundary simple

```text
wtcraft  = authority and deterministic evidence protocol
wtflow   = worktree/task user interface
wteval   = optional experiment package that measures reviewer quality
```

Wtcraft and wtflow should not require wteval. If wteval survives, it may depend
on wtcraft's evidence protocol, but remains a lab and reference integration—not
a third runtime service.

### Smallest credible artifact

The useful portfolio project is a reproducible evaluation study:

1. Freeze 10–20 real or carefully redacted wtcraft task/change fixtures.
2. Store task authority, base/head, changed paths, `check --json`, and
   `verify --json` in a versioned schema.
3. Import structured findings from two existing reviewer paths rather than
   implementing the reviewers—for example Codex/Claude via
   `coding-review-agent-loop`, plus CodeRabbit CLI or plain local review.
4. Label findings as valid, invalid, duplicate, style-only, unsupported, or
   fixed; preserve the human rationale.
5. Compare valid-finding yield, false-positive rate, deterministic violations
   missed, latency, cost/quota use, and rounds-to-convergence.
6. Export runs through OpenTelemetry/OpenInference to Phoenix or LangSmith and
   publish a short results report.

This demonstrates real AI-engineering skills—evaluation design, structured
outputs, telemetry, datasets, human feedback, and evidence-grounded analysis—
without pretending to have invented another reviewer.

### Implementation shape

Prefer a small Python package or even an initial scripts-and-schema lab. Python
has the shortest path to LangSmith, Phoenix/OpenInference, and analysis tooling.
Rust is appropriate for wtcraft's deterministic binary, but offers no product
advantage for this experiment.

Suggested first surface:

```text
wteval dataset add <run-bundle>
wteval import <reviewer-output>
wteval label <run-id>
wteval compare --group-by reviewer,model,prompt
wteval export --backend phoenix|langsmith
```

There is intentionally no `watch`, `serve`, `agent launch`, `review PR`, or
custom dashboard command in the first version.

## Build / borrow / avoid

### Build

- wtcraft evidence schema and redacted fixture format;
- normalizer from deterministic evidence and reviewer findings;
- human-label record with finding lineage across revisions;
- metrics specific to policy/scope violations and reviewer quality;
- one reproducible comparison report.

### Borrow or integrate

- agent execution and cross-agent loops;
- reviewer outputs;
- transcript capture and Git session provenance;
- OpenTelemetry/OpenInference instrumentation;
- trace storage, experiment UI, and charts.

### Avoid

- ACP-specific launcher code;
- a background observer daemon;
- generic PR review comments;
- model subscriptions or routing;
- a custom tracing backend;
- an eval UI;
- forced LangChain/LangGraph usage without a graph-shaped problem.

## Go / no-go test

Run one manual pilot before writing a framework. Use five recent wtcraft or
wtflow changes, two reviewer configurations, and human labels. Continue only if
the pilot reveals a repeatable result that existing review UIs do not expose,
such as:

- one reviewer consistently misses out-of-scope changes represented by
  wtcraft evidence;
- reviewer choice changes after false positives and unsupported claims are
  labeled;
- task-policy evidence materially shortens adjudication;
- finding lineage across fix rounds exposes convergence or regression.

If the result is only “both tools found some bugs and produced comments,” stop
the standalone project. Keep the schema/exporter as a wtcraft example or
contribute the wtcraft evidence adapter to an existing local review-loop
project.
