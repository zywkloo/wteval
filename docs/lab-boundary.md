# Lab boundary: wteval, not public `wtcraft/eval/`

> Decision date: 2026-09-03.
>
> Status: current. Revisit only if the advisor becomes a shipped wtcraft
> command with a public methodology report.

## Decision

Keep datasets, experiment configs, metrics, batch runs, and reports in this
sibling repository. Do not add an `eval/` tree to public
[wtcraft](https://github.com/zywkloo/wtcraft).

| Surface | Owns |
| --- | --- |
| `wteval` (this repo) | Frozen schemas, synthetic fixtures, baselines, metrics, batch runner, private labeled data, experiment reports. |
| `wtcraft` | Runtime governance. Later, `wtcraft advise` if evidence supports it. |
| `wtcraft` docs | A pointer to this lab. No personal tasks, quota snapshots, or redacted prompts. |

## Why not `wtcraft/eval/`

Public wtcraft is a Git-native governance core with CI and interview-visible
scope. Putting the advisor experiment there would:

- widen the public product story into quota routing before the go/no-go gate;
- mix personal dogfood labels and quota observations into a public tree;
- make CI claim experiment code that is not part of the shipped CLI;
- make a negative result look like a product feature that failed.

Interview-visible artifacts, if any, are a later methodology report or a
redacted public extract. They are not a reason to grow wtcraft's scope.

## Why a sibling GitHub repo

The lab needs versioned schemas, CI on the harness, and a place to run
experiments without widening wtcraft's shipped CLI scope. A sibling folder
without git cannot do that. A public `wtcraft/eval/` directory can, but at
the wrong scope cost.

This repository is public for methodology and harness code. Personal dogfood
labels stay under gitignored `datasets/private/` and are never committed.
Local draft helpers such as `scripts/draft_private_examples.py` are gitignored
too. Committed fixtures are synthetic only.

Competitive research, fork/upstream strategy, and TokenTracker integration
plans are maintained outside this repository.
