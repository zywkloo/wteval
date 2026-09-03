#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=== Running wteval harness tests ==="
python3 -m unittest discover -s "${SCRIPT_DIR}" -p "test_*.py"

echo "=== Validating synthetic fixtures ==="
python3 "${ROOT}/scripts/validate.py" "${ROOT}/tests/fixtures/examples"

echo "=================================="
echo "All tests passed successfully!"
