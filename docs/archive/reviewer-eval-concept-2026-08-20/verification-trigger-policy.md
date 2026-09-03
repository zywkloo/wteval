# Verification trigger policy

> **Status:** Pre-market design note. Trigger/debounce machinery is not a
> differentiator and should not be implemented in wteval before the pilot. See
> [competitive-landscape-2026-08.md](competitive-landscape-2026-08.md).

## Separate the operations

Do not use `verify` as an ambiguous name for every expensive action. Wteval has
four distinct operations:

| Operation | Meaning | Cost/authority |
| --- | --- | --- |
| `capture` | Freeze task/policy, Git revision, and changed paths. | Cheap; no verdict. |
| `verify` | Run deterministic wtcraft scope checks and declared tests. | Potentially expensive; authoritative only at a protected boundary. |
| `review` | Ask an advisory model/reviewer for structured findings. | Network/cost/non-deterministic; never authoritative. |
| `adjudicate` | Label findings and record a human/repository decision. | Explicit human or protected-policy action. |

Each operation has its own triggers, debounce, timeout, and blocking policy.

## Recommended default: balanced

```text
commit created
  -> capture immediately
  -> schedule local verify after 10s quiet time
  -> schedule advisory review after 60s quiet time

another commit before a scheduled job starts
  -> cancel/supersede the old scheduled job
  -> capture the new SHA
  -> restart quiet timers

push requested
  -> check for a fresh deterministic result bound to the exact pushed SHA
  -> warn by default; strict mode may block known failures
  -> never start a required network LLM call inside pre-push

PR opened/updated/marked ready
  -> remote authorization + verification for exact head SHA
  -> optional advisory review
  -> cancel superseded runs for older PR heads
```

The local debounce key is `repository + worktree/branch + verification_loop`.
It is trailing-edge: the job runs only after no newer matching event has arrived
for the configured duration.

## Stale and cancellation rules

Every job captures an intended `head_sha` before it starts:

1. If HEAD changes while the job is queued, cancel it without running.
2. If HEAD changes during deterministic verification, allow safe child-process
   cancellation when possible; otherwise retain the result as `stale`.
3. If HEAD changes during a model call, do not attach its output to the new
   revision. Store or discard it according to retention policy as `stale`.
4. A stale result can be useful evaluation history but can never satisfy a
   fresh push or PR gate.

## GitHub behavior

GitHub Actions should implement latest-wins coalescing with a concurrency group
keyed by workflow and PR number/branch, using `cancel-in-progress: true`. This
prevents an old head from continuing after a newer `synchronize` event.

This is not a wall-clock debounce. Avoid keeping a hosted runner asleep merely
to wait for quiet time. A true server-side time debounce belongs in a GitHub App
or external queue later; the Actions MVP uses cancellation and exact-SHA stale
checks.

Example shape:

```yaml
concurrency:
  group: wteval-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true
```

## Configurable profiles

### `fast`

- capture on commit;
- deterministic checks only on explicit finish/push/PR;
- advisory review manual or PR-ready only;
- no blocking local hook.

### `balanced` (default)

- capture immediately on commit;
- local deterministic verify after 10 seconds quiet;
- advisory review after 60 seconds quiet with a five-minute cooldown;
- pre-push warns on missing/stale results and blocks only known deterministic
  failures when explicitly enabled;
- PR verification runs for every new head; advisory review runs for ready PRs.

### `strict`

- deterministic verify after every debounced commit;
- pre-push requires a fresh deterministic pass for the exact SHA;
- PR authorization/verification are required checks;
- accepted blocking findings must be re-verified before loop convergence;
- model availability still does not block Git unless repository policy
  explicitly and safely defines such a requirement.

## Draft configuration

```yaml
version: 1
profile: balanced

triggers:
  post_commit:
    capture: immediate
    verify:
      mode: async
      debounce: 10s
    review:
      mode: async
      debounce: 60s
      cooldown: 5m
      cancel_on_new_head: true

  pre_push:
    require_fresh: none        # none | deterministic
    known_failure: warn        # ignore | warn | block
    pending_review: warn       # ignore | warn; never block by default

  pull_request:
    events: [opened, synchronize, ready_for_review, reopened]
    verify: required
    review: when_ready         # never | when_ready | every_head | manual
    cancel_superseded: true

loop:
  max_rounds: 3
  require_verified_blocking_findings: true
```

Durations and modes require schema validation. Invalid policy fails closed for
remote required checks and falls back to manual-only for local advisory work.

## Configuration authority

Local preferences may tune debounce, cooldown, notifications, and advisory
review frequency. They cannot upgrade a local result into remote authority.

For GitHub required checks, enforcement configuration must be read from the
trusted base/protected configuration, not the PR head. An executor-controlled
branch must not be able to change `required` to `never` in the same PR it is
trying to authorize.

Recommended precedence:

```text
remote protected workflow/policy  # remote authority
explicit CLI flags                # one local invocation
repository wteval config          # local defaults
user config                       # personal defaults
built-in balanced profile
```

Task contracts may request a stricter local review, but cannot weaken protected
remote requirements.
