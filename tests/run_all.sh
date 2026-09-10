#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=== Running wteval harness tests ==="
python3 -m unittest discover -s "${SCRIPT_DIR}" -p "test_*.py"

echo "=== Validating synthetic fixtures ==="
python3 "${ROOT}/scripts/validate.py" "${ROOT}/tests/fixtures/examples"

echo "=== Scoring synthetic capability fixtures ==="
python3 "${ROOT}/scripts/run_capability.py" --runs "${ROOT}/tests/fixtures/runs" --out "${ROOT}/reports/local/capability-smoke"

echo "=== PBT demo smoke ==="
python3 "${ROOT}/scripts/run_pbt.py"

echo "=== Mutation gate smoke (wteval self-test) ==="
python3 "${ROOT}/scripts/run_mutation.py" \
  --repo "${ROOT}" \
  --files "wteval/metrics.py" \
  --test-cmd "python3 -m unittest discover -s tests -p test_metrics.py -q" \
  --max-mutants 8

echo "=================================="
echo "All tests passed successfully!"
