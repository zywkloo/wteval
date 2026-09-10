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
base = mutated tree, oracle = original).

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

This is the "random generator" answer to the question "your fixed corpus is
fine, but where is the random generation?" — it is deliberately small and does
not claim Hypothesis-scale shrinking.

## Honest limits

- Text-level mutation produces stillborn mutants; real tools use AST mutations.
- The PBT harness is seeded-random and greedy-shrinking, not Hypothesis.
- Both measure *their own* targets; neither proves semantic correctness, only
  that the declared test/oracle fired or held.
