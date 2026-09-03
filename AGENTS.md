# Agent notes

This repository is an offline evaluation lab. Do not add a runtime, agent
launcher, token dashboard, or PR reviewer here.

- Schemas and validators are frozen together. If you change a field, update
  `wteval/constants.py`, `wteval/validate.py`, `schemas/`, and
  `tests/test_schema_agreement.py` in the same change.
- Commit only synthetic fixtures. Real labeled tasks belong in
  `datasets/private/`.
- Do not report counterfactual savings from observed routes.
- Public `wtcraft` must not grow an `eval/` tree for this experiment. See
  `docs/lab-boundary.md`.
- Competitive, fork/upstream, and TokenTracker integration strategy docs do
  not belong in this repository.
