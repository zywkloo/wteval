# GitHub pull-request mode

> **Status:** Contingent design note. Do not build a new PR reviewer before the
> manual pilot in
> [competitive-landscape-2026-08.md](competitive-landscape-2026-08.md).

## The missing local task file is expected

`.worktree-task.md` is clone-local, mutable working state. A GitHub Actions
clone normally cannot see it, and an executor-controlled copy would not be an
authoritative source of approval anyway. Remote PR evaluation must not depend
on that file.

Instead, wteval normalizes both local and remote inputs into a frozen change
subject:

```text
ChangeSubject
  source: local_worktree | github_pr
  repository
  base_sha
  merge_base_sha
  head_sha
  head_ref
  changed_files
```

The evaluation pipeline consumes this subject plus whatever evidence is
available. It does not require the PR clone to be a linked Git worktree.

## Remote authority source

For a protected authorization verdict, use wtcraft's Policy Envelope v1 rather
than the local task file. The envelope is read only from the configured,
protected `refs/heads/wtcraft-policy` branch and binds:

- repository identity;
- expected implementation `head_ref`;
- exact merge-base `base_sha`;
- allowed and off-limits paths;
- reviewed verification commands.

The policy record lives at:

```text
.wtcraft/policies/<policy-id>.json
```

The task branch cannot authorize itself by adding or widening a policy copy.
The evidence must name the resolved policy commit and canonical digest.

## Two honest operating modes

### Advisory PR review

Useful for immediate dogfooding without repository policy setup:

```text
Authorization: UNAVAILABLE
Changed files: captured
Ordinary CI: captured when available
AI review: available
Human decision: pending
```

wteval may review the diff and test results, but it cannot say the change was
authorized or within approved scope. An advisory job may succeed as a report,
provided the missing authorization is visually explicit.

### Protected PR gate

Used after the repository has a protected policy ref and required checks:

```text
Authorization: PASS | BLOCKED
Policy: <policy-id>, <protected commit>, <digest>
Verification: PASS | FAIL | NOT_EXECUTED
AI review: advisory
Human/repository decision: external
```

In enforcing mode, missing, ambiguous, stale, or malformed policy evidence
fails closed. An authorization pass must not be presented as a verification
pass; those are separate jobs and evidence fields.

## Proposed Action flow

```text
GitHub pull request event
          |
          +--> trusted authorization job
          |      trusted base workflow
          |      protected wtcraft-policy ref
          |      PR head object, never executed
          |      -> wtcraft policy evidence
          |
          +--> ordinary unprivileged CI
          |      checkout PR head
          |      run tests/lint/build without privileged secrets
          |      -> verification evidence
          |
          +--> wteval aggregate/review
                 bind all evidence to head_sha
                 optional bounded AI review
                 render job summary + upload run bundle
```

The trusted authorization job must not execute code from the PR. The ordinary
CI job may run PR code only with ordinary least-privilege permissions. A later
aggregator combines evidence by exact `head_sha`; it must reject stale results.

## CLI and Action surface

Local worktree mode remains:

```bash
wteval review --repo /path/to/repo --worktree feat/task
```

GitHub Actions should use event and evidence files rather than trying to
reconstruct a local task:

```bash
wteval review-pr \
  --event "$GITHUB_EVENT_PATH" \
  --policy-evidence wtcraft-policy-evidence.json \
  --verification-evidence ci-evidence.json
```

Advisory mode may omit policy evidence explicitly:

```bash
wteval review-pr --event "$GITHUB_EVENT_PATH" --advisory
```

## Result display on GitHub

MVP output requires no bot comment or GitHub App:

- the Actions job name supplies the PR check status;
- `$GITHUB_STEP_SUMMARY` renders deterministic gate, advisory findings, and
  evidence references;
- `wteval-run-<head-sha>` is uploaded as a downloadable run-bundle artifact;
- full or redacted OpenTelemetry/LangSmith export remains opt-in.

PR comments, inline annotations, and a dedicated GitHub App come later because
they require write permissions and a larger security surface.

## Local-to-remote promotion

A future wtcraft command can transform local planning state into a **policy
proposal**, not an approval:

```text
.worktree-task.md
        |
        v
wtcraft policy propose
        |
        v
.wtcraft/policies/<policy-id>.json on a policy-review branch
        |
        v
review and merge into protected wtcraft-policy
```

This is intentionally a separate review step. Copying the task file into the
implementation PR would preserve information but would not establish trusted
authorization.
