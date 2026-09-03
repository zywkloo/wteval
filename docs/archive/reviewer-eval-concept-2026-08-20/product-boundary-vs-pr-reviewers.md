# Product boundary versus AI PR reviewers

## Decision

Do not position wteval as another AI pull-request reviewer.

Do not position its local executor/reviewer loop, watcher, debounce policy, or
session evidence bundle as unique either. Direct substitutes now cover those
surfaces. The broader evidence is recorded in
[competitive-landscape-2026-08.md](competitive-landscape-2026-08.md).

Automatic PR summaries, bug comments, codebase-aware suggestions, incremental
re-review, and one-click fixes are mature product surfaces served by GitHub
Copilot, CodeRabbit, Greptile, and similar tools. Reimplementing that interface
is not a credible differentiator for wteval.

Wteval should instead evaluate **agent-assisted change runs and reviewer
quality**:

```text
AI PR reviewer
  asks: "What looks wrong in this diff?"

wteval
  asks: "What was authorized, what deterministic evidence exists, which
  reviewer findings were valid, and did this agent/reviewer configuration
  improve over the previous one?"
```

## Where the overlap is real

Do not claim these as unique wteval features:

- triggering automatically on a pull request or new push;
- summarizing a diff;
- generating bug, style, security, or performance comments;
- using whole-repository context;
- accepting repository instructions or issue context;
- assigning severity to findings;
- collecting thumbs-up/down feedback;
- suggesting or applying a fix;
- displaying an Actions/PR status.

These may be adapter or display conveniences, but they are not the product
thesis.

## Wteval's narrower domain

The product remains worthwhile only if it delivers the intersection below:

1. **Git-bound evidence:** freeze task/policy, base/head revision, changed paths,
   deterministic checks, verification, and evidence hashes in one run bundle.
2. **Authorization distinction:** keep local task intent, protected policy
   authorization, CI verification, advisory AI findings, and human merge
   decision separate.
3. **Cross-provider evaluation:** replay the same frozen change through Copilot,
   Claude, Codex, or another reviewer configuration without turning model
   selection into a routing product.
4. **Finding-level human labels:** record whether each finding was valid,
   invalid, duplicate, style-only, unverifiable, or fixed before merge.
5. **Reviewer regression:** compare valid-finding rate, false positives,
   unsupported claims, hard-rule violations, latency, cost, and human override
   rate across graph/prompt/model versions.
6. **Local and remote parity:** evaluate pre-PR local commits and GitHub PRs
   using the same change-subject and evidence contracts.

LangSmith can store traces, datasets, and experiments, but wteval supplies the
coding-change-specific run schema, Git/policy evidence adapters, finding labels,
and hard rules. LangSmith is an optional experiment backend, not the product
boundary.

## Existing reviewers should become inputs

Wteval does not need to own every reviewer. It can ingest standard GitHub review
comments and normalize them into findings:

```text
GitHub Copilot review ----+
CodeRabbit review --------+--> normalized findings --> human labels
Claude/Codex local review +                          --> metrics/replay
```

This enables a useful dogfood question:

> On my last 20 wtcraft/wtflow changes, which reviewer produced the highest
> rate of valid, non-duplicate findings, and which findings changed my merge
> decision?

The primary local workflow is described in
[cross-agent-verification-loop.md](cross-agent-verification-loop.md). It tracks
findings across multiple immutable revisions instead of producing unrelated
fresh comments after every fix.

The MVP can start with one local reviewer adapter. GitHub review ingestion comes
after the run and finding schemas are stable.

## Kill criterion

If wteval only produces summaries and AI review comments, stop or reduce it to
an example integration; existing products already solve that problem.

Continue only if dogfooding proves at least one of these:

- task/policy evidence catches a scope or provenance failure a generic reviewer
  did not represent;
- human-labeled replay changes the chosen reviewer/prompt/model;
- the evidence bundle materially shortens review or incident reconstruction;
- cross-provider reviewer metrics expose a repeatable quality difference.

## Positioning

Preferred:

> A local-first evaluation harness for agent-generated code changes, binding Git
> revisions to authorization and verification evidence and benchmarking
> reviewer quality with human-labeled findings.

Avoid:

> An AI bot that automatically reviews pull requests and suggests fixes.
