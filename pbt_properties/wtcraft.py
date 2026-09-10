"""PBT properties against wtcraft's policy-envelope evaluator (the oracle).

These are black-box properties: they recombine wtcraft's committed contract
fixtures (``tests/contracts/policy-envelope/*``) into generated policy/change
pairs and assert the evaluator behaves like a deterministic oracle should:

- ``policy_evaluator_determinism`` — the same (policy, change) pair yields the
  same exit code and byte-identical stdout every time;
- ``policy_evaluator_no_crash`` — generated inputs never crash the evaluator
  with a Python traceback (it may reject them cleanly, but must not explode).

A failing property is a *finding*, not just a red test: it points at a real
nondeterminism or crash in the oracle, which is exactly the kind of bug the
capability experiment wants ground truth for.

The target repo is ``$WTCRAFT_REPO`` (default ``../wtcraft``). Run with:

    python3 scripts/run_pbt.py --properties pbt_properties/wtcraft.py
"""

from __future__ import annotations

import json
import os
import random
import subprocess
import sys
import tempfile
from pathlib import Path

from wteval.pbt import Failure

SEED = 20260910
DEFAULT_N = 60

# Hostile literals mixed into the generated inputs, beyond what the committed
# fixtures contain.
_HOSTILE_STRINGS = ["", "*", "**", "**/*", "../escape", "☃", "a" * 200, "src/**/**"]


def _repo() -> Path:
    env = os.environ.get("WTCRAFT_REPO")
    root = Path(__file__).resolve().parents[1]
    return (Path(env) if env else root.parent / "wtcraft").resolve()


def _evaluator(repo: Path) -> Path:
    return repo / "scripts" / "policy_evaluator.py"


def _load_pool(repo: Path) -> dict:
    """Derive generation pools from wtcraft's committed contract fixtures."""
    contract_dir = repo / "tests" / "contracts" / "policy-envelope"
    allowed: list[str] = []
    off: list[str] = []
    changed: list[str] = []
    verifications: list[dict] = []
    for policy_f in sorted(contract_dir.glob("*/policy.json")):
        policy = json.loads(policy_f.read_text(encoding="utf-8"))
        allowed.extend(policy.get("allowed_paths", []))
        off.extend(policy.get("off_limits", []))
        verifications.extend(policy.get("verification", []))
    for change_f in sorted(contract_dir.glob("*/change.json")):
        change = json.loads(change_f.read_text(encoding="utf-8"))
        changed.extend(change.get("changed_files", []))
    return {
        "allowed": _dedup(allowed),
        "off": _dedup(off),
        "changed": _dedup(changed),
        "verifications": verifications,
    }


def _dedup(values: list) -> list:
    """Deduplicate by JSON form so deliberately nested (invalid) values survive."""
    seen: set[str] = set()
    out: list = []
    for value in values:
        key = json.dumps(value, sort_keys=True, default=str)
        if key not in seen:
            seen.add(key)
            out.append(value)
    return out


def _pick(rng: random.Random, pool: list[str], lo: int, hi: int) -> list[str]:
    count = rng.randint(lo, hi)
    return [rng.choice(pool) for _ in range(count)]


def _hex(rng: random.Random, n: int = 40) -> str:
    return "".join(rng.choice("0123456789abcdef") for _ in range(n))


def _generate(pool: dict, n: int, seed: int) -> list[tuple[dict, dict]]:
    rng = random.Random(seed)
    allowed_pool = pool["allowed"] + _HOSTILE_STRINGS
    off_pool = pool["off"] + _HOSTILE_STRINGS
    changed_pool = pool["changed"] + _HOSTILE_STRINGS
    head_refs = ["refs/heads/feat/x", "refs/heads/☃", "refs/tags/v1", "", "main"]
    verifications = pool["verifications"] or [{"name": "unit", "command": "bash tests/run_all.sh", "timeout_seconds": 900}]

    pairs: list[tuple[dict, dict]] = []
    for _ in range(n):
        head_ref = rng.choice(head_refs)
        repository = rng.choice(["acme/widget", "acme/widget", "☃/☃", ""])
        policy = {
            "schema_version": 1,
            "policy_id": f"gen-{_hex(rng, 8)}",
            "task_id": f"generated task {_hex(rng, 6)}",
            "repository": repository,
            "head_ref": head_ref,
            "base_sha": _hex(rng),
            "allowed_paths": _pick(rng, allowed_pool, 0, 3),
            "off_limits": _pick(rng, off_pool, 0, 3),
            "verification": [rng.choice(verifications) for _ in range(rng.randint(0, 2))],
        }
        change = {
            "repository": repository,
            "head_ref": head_ref,
            "merge_base_sha": _hex(rng),
            "changed_files": _pick(rng, changed_pool, 0, 4),
        }
        pairs.append((policy, change))
    return pairs


def _run(repo: Path, evaluator: Path, policy: dict, change: dict) -> tuple[int, str]:
    with tempfile.TemporaryDirectory(prefix="wteval-pbt-") as tmp:
        p = Path(tmp) / "policy.json"
        c = Path(tmp) / "change.json"
        p.write_text(json.dumps(policy), encoding="utf-8")
        c.write_text(json.dumps(change), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(evaluator), "--policy", str(p), "--change", str(c)],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return proc.returncode, proc.stdout


def _first_failure(predicate, examples, name: str) -> Failure | None:
    for example in examples:
        try:
            holds = bool(predicate(example))
        except Exception:
            holds = False
        if not holds:
            return Failure(property_name=name, original=example, counterexample=example, shrinks=0)
    return None


def _determinism_predicate(repo: Path, evaluator: Path):
    def pred(pair: tuple[dict, dict]) -> bool:
        first = _run(repo, evaluator, *pair)
        second = _run(repo, evaluator, *pair)
        return first == second

    return pred


def _no_crash_predicate(repo: Path, evaluator: Path):
    def pred(pair: tuple[dict, dict]) -> bool:
        _code, stdout = _run(repo, evaluator, *pair)
        return "Traceback" not in stdout

    return pred


def properties() -> list[dict]:
    repo = _repo()
    evaluator = _evaluator(repo)
    if not evaluator.is_file():
        raise RuntimeError(
            f"wtcraft evaluator not found at {evaluator}; set WTCRAFT_REPO to the wtcraft checkout"
        )
    pool = _load_pool(repo)
    n = int(os.environ.get("WTEVAL_PBT_N", DEFAULT_N))
    pairs = _generate(pool, n, SEED)
    return [
        {
            "name": "policy_evaluator_determinism",
            "shape": "determinism",
            "failure": _first_failure(
                _determinism_predicate(repo, evaluator), pairs, "policy_evaluator_determinism"
            ),
        },
        {
            "name": "policy_evaluator_no_crash",
            "shape": "invariant",
            "failure": _first_failure(
                _no_crash_predicate(repo, evaluator), pairs, "policy_evaluator_no_crash"
            ),
        },
    ]
