Real labeled tasks stay here and are gitignored.

Start from a synthetic fixture in `tests/fixtures/examples/`, redact or
fingerprint the prompt, fill labels before scoring, and write the file here.
See [harness](../docs/harness.md#adding-a-real-example).

Validate locally:

```bash
python3 scripts/validate.py datasets/private
```

Prompt text is never stored; fingerprints hash the feature snapshot. Keep
`split` as `unassigned` until a chronological cut is frozen. Do not invent
quota or check/verify outcomes.

Optional local draft helpers (for example `scripts/draft_private_examples.py`)
stay gitignored and are not part of the public repo.
