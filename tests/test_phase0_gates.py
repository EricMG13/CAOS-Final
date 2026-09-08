"""Phase 0 exit test.

One function that is unformatted, misnamed and untested must be refused by four
gates *separately*: formatting, lint, vocabulary, and the untested-public-
function check. Separately matters -- a single gate that swallows all four
reasons cannot tell an author which control they tripped, and a gate that
refuses everything is worth as little as one that refuses nothing. So each gate
is also driven against a clean equivalent and must accept it.

Invariant protected: the controls in docs/AI_CODE_QUALITY.md section 1 exist and
bite before any application code depends on them.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]

# Unformatted (spaces inside the parentheses, doubled space after `return`),
# misnamed (`deal` is a synonym for `case`, `chunk` for `block` -- CONTEXT.md),
# unannotated, and named by nothing under the tests root.
OFFENDING = "def summarise_deal_chunks( rows ):\n    return  [r for r in rows]\n"

# The same function with every one of those four defects removed.
CLEAN = (
    "def summarise_case_blocks(rows: list[str]) -> list[str]:\n"
    "    return [r for r in rows]\n"
)
CLEAN_TEST = (
    "def test_summarise_case_blocks() -> None:\n    summarise_case_blocks([])\n"
)

# --config is explicit because the offending file is written outside the repo
# tree, where ruff would otherwise discover no configuration and pass it.
_RUFF = [sys.executable, "-m", "ruff"]
_CONFIG = ["--config", str(REPO / "pyproject.toml")]

GATES = ("format", "lint", "vocabulary", "tested")

# Substring each gate must emit, so that a non-zero exit for an unrelated reason
# (a crash, a missing file) cannot be mistaken for a refusal.
REASONS = {
    "format": "would be reformatted",
    "lint": "ANN201",
    "vocabulary": "deal",
    "tested": "summarise_deal_chunks",
}


def _argv(gate: str, target: Path, tests_dir: Path) -> list[str]:
    if gate == "format":
        return [*_RUFF, "format", *_CONFIG, "--check", str(target)]
    if gate == "lint":
        return [*_RUFF, "check", *_CONFIG, "--no-cache", str(target)]
    script = {"vocabulary": "check_vocabulary.py", "tested": "check_tested.py"}[gate]
    argv = [sys.executable, str(REPO / "scripts" / script), str(target)]
    if gate == "tested":
        argv += ["--tests", str(tests_dir)]
    return argv


def _run(gate: str, target: Path, tests_dir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        _argv(gate, target, tests_dir),
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture
def offending(tmp_path: Path) -> tuple[Path, Path]:
    src = tmp_path / "src"
    src.mkdir()
    (src / "offending.py").write_text(OFFENDING, encoding="utf-8")
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    return src / "offending.py", tests_dir


@pytest.fixture
def clean(tmp_path: Path) -> tuple[Path, Path]:
    src = tmp_path / "src"
    src.mkdir()
    (src / "clean.py").write_text(CLEAN, encoding="utf-8")
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_clean.py").write_text(CLEAN_TEST, encoding="utf-8")
    return src / "clean.py", tests_dir


@pytest.mark.parametrize("gate", GATES)
def test_gate_refuses_the_offending_function(
    gate: str, offending: tuple[Path, Path]
) -> None:
    target, tests_dir = offending
    result = _run(gate, target, tests_dir)
    output = result.stdout + result.stderr
    assert result.returncode != 0, f"{gate} accepted the offending function:\n{output}"
    assert REASONS[gate] in output, f"{gate} refused for the wrong reason:\n{output}"


@pytest.mark.parametrize("gate", GATES)
def test_gate_accepts_the_clean_function(gate: str, clean: tuple[Path, Path]) -> None:
    target, tests_dir = clean
    result = _run(gate, target, tests_dir)
    output = result.stdout + result.stderr
    assert result.returncode == 0, f"{gate} refused the clean function:\n{output}"
