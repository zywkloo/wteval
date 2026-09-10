"""Unified task formatting for history-derived verification units.

Maps the output of ``scan_verifications.py`` onto the same task shape the
mutation seeder uses, so one executor can consume both pools side by side.
"""

from __future__ import annotations

from typing import Any


def build_task(unit: dict[str, Any], index: int) -> dict[str, Any]:
    verification = unit["verification"]
    return {
        "task_id": f"hist-{index:03d}-{unit['kind']}",
        "origin": "history",
        "task": {
            "repository": unit["repo"],
            "base_revision": unit["base_sha"],
            "oracle_revision": unit["oracle_sha"],
            "prompt_fingerprint": f"history:{unit['kind']}:{verification}",
            "verification_declared": True,
            "verification": verification,
            "origin": "history",
        },
        "verification_unit": {"kind": unit["kind"], "path": verification},
        "subject": unit["subject"],
        "author_date": unit["author_date"],
    }
