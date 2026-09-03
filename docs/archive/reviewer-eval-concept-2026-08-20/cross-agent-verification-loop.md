# Cross-agent verification loop

> **Status:** Evaluation scenario, not a wteval orchestration plan. Existing
> tools should execute the loop; wteval may import its rounds and findings. See
> [competitive-landscape-2026-08.md](competitive-landscape-2026-08.md).

## Product thesis

Wteval does not need to be the reviewer. It coordinates and evaluates a bounded
verification loop between an executor and an independent reviewer:

```text
Codex implements -> Claude reviews -> Codex fixes -> Claude verifies

or

Claude implements -> Codex reviews -> Claude fixes -> Codex verifies
```

CodeRabbit, Copilot, or another review service can occupy the reviewer role as
an adapter. The durable product is the evidence-bound loop and its evaluation,
not a proprietary set of review comments.

## Why task context alone is not differentiation

Linked issues, acceptance criteria, repository instructions, and AI pre-merge
checks are already common review inputs. `.worktree-task.md` is useful because
it supplies local task intent, but its filename or existence is not a moat.

Wteval adds value only when task intent is turned into explicit, measurable
loop invariants:

- the contract/policy digest remains fixed across the loop;
- each round is bound to an exact Git head revision;
- allowed/off-limits paths and deterministic verification remain visible;
- every reviewer finding has evidence and a lifecycle;
- an executor cannot silently mark its own disputed finding resolved;
- convergence is defined by rules and human judgment, not by two models saying
  "looks good" to each other.

## Data model

```text
VerificationLoop
  loop_id
  task_id
  contract_or_policy_digest
  base_sha
  executor_provider
  reviewer_provider
  max_rounds
  rounds[]
  final_human_decision

Round
  round_number
  head_sha
  changed_files
  check_result
  verify_result
  reviewer_run
  findings[]

Finding
  finding_id
  severity
  claim
  evidence_refs[]
  reviewer_provider
  introduced_round
  executor_response
  human_label
  resolution
  verified_in_round
```

Suggested finding lifecycle:

```text
open
  -> accepted -> fixed -> verified
  -> rejected -> human_confirmed_rejection
  -> duplicate
  -> style_only
  -> cannot_verify
```

`fixed` is an executor claim. `verified` requires evidence from a later frozen
round or an explicit human decision.

## Convergence rules

A loop may be called `converged` only when:

1. the captured contract or protected policy has not changed;
2. the current Git revision has a passing deterministic scope gate;
3. required verification passes;
4. every accepted blocking finding is verified fixed;
5. remaining rejected or ambiguous blocking findings have a human decision;
6. the configured maximum round count has not been exceeded.

The loop stops as `needs_human` when models disagree, evidence is missing, the
contract changes, or the round limit is reached. No unbounded model-to-model
argument is allowed.

## Proposed local workflow

```bash
wteval loop start \
  --task feat/session-cancel \
  --executor codex \
  --reviewer claude \
  --max-rounds 3

# Executor commits a candidate change.
wteval round review --commit HEAD

# Findings are accepted/rejected and the executor applies fixes.
wteval round advance --commit HEAD

# Reviewer verifies prior findings against the new frozen revision.
wteval loop status
```

Round creation and review can be manual or driven by the configurable
[verification trigger policy](verification-trigger-policy.md). A new commit
always creates a new candidate revision; debounce determines when its
deterministic verify and advisory review begin.

The first implementation may export a `review-packet.json` / Markdown prompt
for manual use in Codex or Claude and import structured findings afterward.
Headless adapters are optional conveniences, so ACP or vendor CLI breakage does
not corrupt the loop protocol.

## Review packet

Each reviewer receives bounded, explicit input:

- immutable task/policy digest and relevant task text;
- base/head revision and changed-file list;
- scoped diff or diff references;
- raw wtcraft check/verify evidence;
- open findings from prior rounds;
- requested output schema;
- instruction not to modify Git or expand task scope.

Later rounds should ask first whether earlier accepted findings are actually
resolved, then inspect new regressions. This avoids producing a fresh unrelated
review on every iteration.

## What gets evaluated

Across real wtcraft/wtflow tasks, build an executor-reviewer matrix:

| Executor | Reviewer | Useful measures |
| --- | --- | --- |
| Codex | Claude | valid-finding rate, rounds to convergence, missed defects, latency/cost |
| Claude | Codex | same frozen-task measures |
| Codex | CodeRabbit | same measures after normalizing structured findings |
| Claude | CodeRabbit | same measures |

Human labels are the reference signal. A reviewer is not better merely because
it emits more findings or causes more rounds.

## CodeRabbit as an adapter, not an enemy

Where available, CodeRabbit's structured agent output can be normalized into
the same `Finding` schema. Wteval then contributes:

- binding findings to task/policy and exact revisions;
- tracking accepted/rejected/fixed/verified lifecycle across rounds;
- comparing CodeRabbit with Codex or Claude on the same labeled bundles;
- retaining a portable, local-first history independent of one review vendor.

This boundary also provides a clear kill condition: if the loop schema,
evidence binding, and cross-reviewer comparison are not useful, use CodeRabbit
or Copilot directly instead of maintaining wteval.
