# Archived concepts

This directory preserves superseded wteval planning. Archived documents are
historical research, not the current product plan.

## reviewer-eval-concept-2026-08-20

[Open archive](reviewer-eval-concept-2026-08-20/README.md).

The archived concept explored:

- an evidence-first agent-run recorder;
- a bounded LLM reviewer graph;
- cross-agent executor/reviewer loops;
- Git hooks and debounce policies;
- GitHub PR mode;
- run bundles, trace export, and reviewer-quality evaluation.

It was archived because the market scan found mature overlap across AI PR
review, local cross-agent review loops, Git-linked transcript/evidence capture,
task/spec governance, and generic LLM evaluation platforms. Its durable lessons
remain valid:

- deterministic wtcraft checks are authoritative;
- LLM review is advisory;
- human decisions are separate records;
- all results bind to immutable Git evidence;
- stale revisions cannot satisfy a current gate.

Those lessons may inform wtcraft protocols or wteval datasets, but the archived
daemon, reviewer, hook, and PR designs must not be implemented as the current
wteval direction.

