# Mutation testing and property-based testing

> Two instruments for the "acceptance must be deterministic" half of the
> generation/acceptance split. Both live in wteval and both are stdlib-only.

## Why these two

| Instrument | Governs | Question it answers |
| --- | --- | --- |
| Mutation testing | the tests themselves (L4) | "Do the tests kill an injected bug, or only run green?" |
| Property-based testing | the oracle (L5) | "Does an invariant hold over generated inputs, not just a fixed corpus?" |

They share one frame: **generation is probabilistic, acceptance is
deterministic.** A mutant is accepted only if the test suite kills it; a
property is accepted only if no generated input refutes it.

## Mutation testing

`scripts/run_mutation.py` copies a target repo to a temp dir, injects one
single-token bug at a time, runs the test command, and classifies each mutant:

- `stillborn` — the mutated source no longer compiles (excluded from score);
- `killed` — tests exit non-zero;
- `survived` — tests still pass (a gap in the suite).

Mutation score = `killed / (killed + survived)`.

```bash
python3 scripts/run_mutation.py \
  --repo . \
  --files "wteval/*.py" \
  --test-cmd "python3 -m unittest discover -s tests -p test_metrics.py -q" \
  --max-mutants 40
```

Catalog (`wteval/mutation.py`): comparison flips (`>`↔`>=`, `<`↔`<=`,
`==`↔`!=`), logical flips (`and`↔`or`), boolean flips (`True`↔`False`), and
`+`→`-`. Text-level, not AST-level — the honest framing is "same shape as
mutmut/mut.py, without AST precision".

The same injector doubles as the **bug seeder** for capability-eval tasks: a
`killed` mutant is a task with known ground truth ("make the tests pass again",
base = mutated tree, oracle = original). `scripts/seed_mutations.py` is that
half, made concrete:

```bash
python3 scripts/seed_mutations.py \
  --repo ../wtcraft \
  --files "scripts/policy_evaluator.py" \
  --test-cmd "python3 tests/contract_policy_envelope.py" \
  --max-mutants 20 \
  --out datasets/private/mutations
```

Pick a fast, deterministic `--test-cmd`: wtcraft's contract runner (~0.5s,
10 known-answer cases) beats the full e2e suite for seeding, since the command
runs once per mutant.

For every mutant the suite kills, the seeder commits it on a detached worktree,
keeps it alive as a `wteval/mut-*` branch in the target repo, and emits
`seed-tasks.json` plus one `mutations/*.patch` per task. Each task's `task`
object is drop-in for the capability-run schema's `task`: `base_revision` is
the mutated commit SHA, `oracle_revision` is the pre-mutation `HEAD`, and
`verification` is the failing test extracted from the run output. A survived
mutant is a test-suite gap, not a task; a timeout counts as killed (verification
did not pass). The catalog sets `task.origin = "mutation"` so reports can keep
synthetic seeded tasks honest against historical ones.

## Property-based testing

`wteval/pbt.py` provides the three property shapes from the deterministic-oracle
taxonomy over a seeded RNG, with greedy shrinking to a minimal counterexample:

- `invariant(predicate, examples)` — property holds for every example;
- `round_trip(encode, decode, examples)` — decode∘encode == identity
  (the `sameBytes` byte-identity shape, now over generated inputs);
- `idempotent(f, examples)` — f∘f == f.

```bash
python3 scripts/run_pbt.py
```

The demo runs four green properties (utf-8 byte round-trip, JSON round-trip,
`sorted` idempotence, mean-bounds invariant) plus one intentionally naive
median property that fails, to show counterexample discovery and shrinking.

Real properties live in `pbt_properties/`. `pbt_properties/wtcraft.py`
recombines wtcraft's committed `policy-envelope` contract fixtures into
generated policy/change pairs and asserts the evaluator behaves like a
deterministic oracle:

```bash
python3 scripts/run_pbt.py --properties pbt_properties/wtcraft.py
```

Two properties: `policy_evaluator_determinism` (same input → byte-identical
verdict every time) and `policy_evaluator_no_crash` (generated inputs never
produce a Python traceback). A failing property is a *finding*: it points at
real nondeterminism or a crash in the oracle — the exact bug the capability
experiment wants ground truth for. The target repo is `$WTCRAFT_REPO`
(default `../wtcraft`); `WTEVAL_PBT_N` tunes the input count. Gate mode exits
non-zero on any failure.

This is the "random generator" answer to the question "your fixed corpus is
fine, but where is the random generation?" — it is deliberately small and does
not claim Hypothesis-scale shrinking.

## Honest limits

- Text-level mutation produces stillborn mutants; real tools use AST mutations.
- The PBT harness is seeded-random and greedy-shrinking, not Hypothesis.
- Both measure *their own* targets; neither proves semantic correctness, only
  that the declared test/oracle fired or held.
- Seeded mutants are synthetic: a task that starts from an injected bug is not
  a claim about real-world difficulty. The `task.origin` field (`history`,
  `mutation`, `pbt`, `fixture`) exists so reports can say so explicitly.
