#!/usr/bin/env python3
"""Tests for scripts/seed_mutations.py: unit helpers plus an end-to-end run
against a throwaway git repo, proving that a killed mutant becomes a real
base/oracle commit pair with a patch and a branch reference."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import seed_mutations as sm  # noqa: E402

SEED_SCRIPT = ROOT / "scripts" / "seed_mutations.py"


def _git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)


def _make_repo(root: Path) -> Path:
    repo = root / "repo"
    repo.mkdir()
    _git(["init", "-q", "-b", "main"], repo)
    (repo / "checker.py").write_text(
        "def is_adult(age):\n    return age >= 18\n\n\ndef is_even(n):\n    return n % 2 == 0\n",
        encoding="utf-8",
    )
    tests = repo / "tests"
    tests.mkdir()
    (tests / "test_checker.py").write_text(
        "import unittest\nfrom checker import is_adult, is_even\n\n\n"
        "class T(unittest.TestCase):\n"
        "    def test_adult(self):\n"
        "        self.assertTrue(is_adult(18))\n"
        "        self.assertFalse(is_adult(17))\n\n"
        "    def test_even(self):\n"
        "        self.assertTrue(is_even(2))\n"
        "        self.assertFalse(is_even(3))\n",
        encoding="utf-8",
    )
    _git(["add", "-A"], repo)
    _git(["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "init"], repo)
    return repo


class SeedMutationsUnitTests(unittest.TestCase):
    def test_extract_failing_test_unittest(self) -> None:
        output = "FAIL: test_adult (test_checker.T.test_adult)\nAssertionError: True is not false\n"
        self.assertEqual(sm._extract_failing_test(output), "test_adult")

    def test_extract_failing_test_pytest(self) -> None:
        output = "FAILED tests/test_checker.py::T::test_even - assert False\n"
        self.assertEqual(sm._extract_failing_test(output), "tests/test_checker.py::T::test_even")

    def test_extract_failing_test_none(self) -> None:
        self.assertIsNone(sm._extract_failing_test("all good\n"))

    def test_classify_verification(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            status, proc = sm._classify_verification(
                f"{sys.executable} -c 'import sys; sys.exit(1)'", cwd=cwd
            )
            self.assertEqual(status, "fail")
            self.assertIsNotNone(proc)
            self.assertNotEqual(proc.returncode, 0)

            status, proc = sm._classify_verification(f"{sys.executable} -c 'pass'", cwd=cwd)
            self.assertEqual(status, "pass")
            self.assertEqual(proc.returncode, 0)

            status, proc = sm._classify_verification("sleep 2", cwd=cwd, timeout=0.2)
            self.assertEqual(status, "timeout")
            self.assertIsNone(proc)


class SeedMutationsEndToEndTests(unittest.TestCase):
    def test_seeds_killed_mutants_as_commits(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = _make_repo(root)
            out = root / "out"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(SEED_SCRIPT),
                    "--repo", str(repo),
                    "--files", "checker.py",
                    "--test-cmd", f"{sys.executable} -m unittest discover -s tests -q",
                    "--max-mutants", "10",
                    "--out", str(out),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)

            payload = json.loads((out / "seed-tasks.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["tool"], "seed_mutations")
            self.assertGreaterEqual(payload["n_tasks"], 1)
            self.assertEqual(payload["n_tasks"], len(payload["tasks"]))

            # Construction metrics are persisted.
            self.assertIs(payload["baseline"]["pass"], True)
            self.assertEqual(payload["baseline"]["status"], "pass")
            self.assertEqual(payload["baseline"]["exit_code"], 0)
            self.assertEqual(payload["task_yield"], round(payload["n_tasks"] / payload["n_sites"], 4))
            self.assertEqual(len(payload["records"]), payload["n_sites"])
            self.assertEqual(
                sum(1 for r in payload["records"] if r["status"] == "survived"),
                payload["counts"]["survived"],
            )

            for task in payload["tasks"]:
                self.assertEqual(task["origin"], "mutation")
                self.assertEqual(task["task"]["origin"], "mutation")
                self.assertEqual(task["task"]["verification_declared"], True)
                self.assertIsInstance(task["deterministic"], bool)
                self.assertNotEqual(task["task"]["base_revision"], task["task"]["oracle_revision"])
                # The mutant commit really exists and is kept alive by a branch.
                _git(["cat-file", "-e", task["task"]["base_revision"]], repo)
                branches = _git(["branch", "--list", f"wteval/{task['task_id']}"], repo).stdout
                self.assertIn(f"wteval/{task['task_id']}", branches)
                self.assertTrue((out / task["patch"]).is_file())

            # No leftover worktrees after the run.
            wt = subprocess.run(
                ["git", "-C", str(repo), "worktree", "list"], capture_output=True, text=True
            )
            self.assertEqual(len(wt.stdout.strip().splitlines()), 1)

    def test_refuses_red_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = _make_repo(root)
            # Break the baseline and commit it as HEAD: the oracle no longer passes.
            (repo / "checker.py").write_text(
                "def is_adult(age):\n    return age > 18\n\n\ndef is_even(n):\n    return n % 2 == 0\n",
                encoding="utf-8",
            )
            _git(["add", "-A"], repo)
            _git(["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "break"], repo)
            out = root / "out"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(SEED_SCRIPT),
                    "--repo", str(repo),
                    "--files", "checker.py",
                    "--test-cmd", f"{sys.executable} -m unittest discover -s tests -q",
                    "--max-mutants", "10",
                    "--out", str(out),
                ],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("does not pass", proc.stderr)


if __name__ == "__main__":
    unittest.main()
