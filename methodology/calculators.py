"""The calculator execution boundary (SYSTEM_SPEC 3).

A module asks for a calculation; it never supplies the code. The host owns
selection, verifies the bytes at use, bounds what model-authored input may cost,
and runs the result where it can reach nothing of ours.

Selection is a host rule rather than a host list: a module may select a
calculator its **own** skill folder ships, and nothing else. That is stronger
than enumerating pairs -- `confidence_score` ships in 22 folders, and a list of
25 rows drifts from the bundle the first time upstream moves one -- and it
refuses the case the rule exists for, a module reaching into another module's
scripts.

Execution copies the verified bytes into a private directory and runs them
there, so what executes is exactly what was hashed rather than a path that was
hashed a moment ago. `-I -S` is what makes the sandbox real: `-I` alone leaves
the host venv's site-packages on the child's path, which means the store's own
driver, which means a socket.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess  # nosec B404
import sys
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

from methodology.bundle import BUNDLE_ROOT, open_bundle
from methodology.registry import module_spec
from server.refusals import Refusal, RefusalCode

# Ceilings on model-authored input, enforced before the vendor script's own
# guards so a looser script can never widen what a calculation may cost.
MAX_PERIODS: Final = 40
MAX_KEYS_PER_PERIOD: Final = 64
MAX_GROWTH_ENTRIES: Final = 64
MAX_ROLL_FORWARD_FLOWS: Final = 256
MAX_COUNT_ENTRIES: Final = 64


class CalculatorLimits:
    """What one calculation may cost the host, whatever it asks for."""

    MAX_INPUT_BYTES: Final = 1 << 20
    MAX_OUTPUT_BYTES: Final = 1 << 22
    TIMEOUT_SECONDS: Final = 30.0


@dataclass(frozen=True, slots=True)
class CalculatorSpec:
    """A selected calculator: whose folder it came from, and what it needs."""

    module_id: str
    skill_slug: str
    entry: str
    helpers: tuple[str, ...]


# Declared per calculator, not per pair. `helpers` is the transitive sibling set
# -- `credit_metrics` imports `cp_tables`, which imports `validate_handoff` --
# and `test_the_declared_helpers_are_closed_under_the_entrys_imports` walks the
# real import graph so a declaration nobody checks cannot become a comment.
_HELPERS: Final[dict[str, tuple[str, ...]]] = {
    "credit_metrics": ("scripts/cp_tables.py", "scripts/validate_handoff.py"),
    "confidence_score": (),
}


def calculator_spec(
    module_id: str, calculator_id: str, *, root: Path = BUNDLE_ROOT
) -> CalculatorSpec:
    """Resolve a `(module, calculator)` selection, or refuse it."""
    helpers = _HELPERS.get(calculator_id)
    if helpers is None:
        raise Refusal(RefusalCode.METHODOLOGY_CALCULATOR_UNKNOWN)
    spec = module_spec(module_id, root=root)
    entry = f"scripts/{calculator_id}.py"
    if f"skills/{spec.skill_slug}/{entry}" not in open_bundle(root).digests:
        # The module's own folder does not ship it, so it is not its to select.
        raise Refusal(RefusalCode.METHODOLOGY_CALCULATOR_UNKNOWN)
    return CalculatorSpec(spec.module_id, spec.skill_slug, entry, helpers)


def run_calculator(
    module_id: str,
    calculator_id: str,
    payload: Mapping[str, Any],
    *,
    root: Path = BUNDLE_ROOT,
) -> dict[str, Any]:
    """Run a verified calculator over host-checked input and return its result."""
    spec = calculator_spec(module_id, calculator_id, root=root)
    request = _checked_input(calculator_id, payload)
    bundle = open_bundle(root)
    sources = {
        Path(name).name: bundle.read(f"skills/{spec.skill_slug}/{name}")
        for name in (spec.entry, *spec.helpers)
    }
    return _execute(sources, Path(spec.entry).name, request)


def _interpreter_argv(entry: str) -> list[str]:
    """`-I` isolates, `-S` drops site-packages -- and only `-S` drops psycopg.

    The scripts put their own folder on `sys.path`, which is why `-I` implying
    `-P` costs nothing here.
    """
    return [sys.executable, "-I", "-S", entry, "--json", "-"]


def _checked_input(calculator_id: str, payload: Mapping[str, Any]) -> str:
    """Serialise and bound the request. Refuses before any byte is read."""
    try:
        request = json.dumps(payload, allow_nan=False)
    except (TypeError, ValueError):
        request = ""
    if not request or len(request) > CalculatorLimits.MAX_INPUT_BYTES:
        raise Refusal(RefusalCode.METHODOLOGY_INPUT_INVALID)
    _enforce_work_factor(calculator_id, payload)
    return request


def _enforce_work_factor(calculator_id: str, payload: Mapping[str, Any]) -> None:
    """Host ceilings, checked before the vendor script's own guards."""
    if calculator_id == "credit_metrics":
        _credit_metrics_work_factor(payload)
    elif calculator_id == "confidence_score":
        _confidence_score_work_factor(payload)
    else:
        # A declared calculator with no ceiling does not run.
        raise Refusal(RefusalCode.METHODOLOGY_CALCULATOR_UNKNOWN)


def _bounded(value: object, ceiling: int) -> None:
    if not isinstance(value, dict | list) or len(value) > ceiling:
        raise Refusal(RefusalCode.METHODOLOGY_INPUT_INVALID)


def _credit_metrics_work_factor(payload: Mapping[str, Any]) -> None:
    """Bounds `compute()`'s actual shape: periods, growth and a roll-forward."""
    for key in ("periods", "reported_periods"):
        if key in payload:
            _bounded(payload[key], MAX_PERIODS)
    for values in (payload.get("periods") or {}).values():
        _bounded(values, MAX_KEYS_PER_PERIOD)
    if "growth" in payload:
        _bounded(payload["growth"], MAX_GROWTH_ENTRIES)
    roll_forward = payload.get("roll_forward")
    if isinstance(roll_forward, dict) and "flows" in roll_forward:
        _bounded(roll_forward["flows"], MAX_ROLL_FORWARD_FLOWS)


def _confidence_score_work_factor(payload: Mapping[str, Any]) -> None:
    for key in ("lineage", "findings"):
        if key in payload:
            _bounded(payload[key], MAX_COUNT_ENTRIES)


def _execute(sources: Mapping[str, str], entry: str, request: str) -> dict[str, Any]:
    """Write the verified bytes somewhere private and run them there."""
    with tempfile.TemporaryDirectory() as workspace:
        directory = Path(workspace)
        for name, text in sources.items():
            (directory / name).write_text(text, encoding="utf-8")
        (directory / "stdin.json").write_text(request, encoding="utf-8")
        return _parse(_captured(directory, entry))


def _captured(directory: Path, entry: str) -> Path:
    """Run to completion, or kill the whole process group and refuse.

    stdout goes to a file rather than a pipe: nothing can deadlock on a full
    buffer, and the size is known before a byte is read into this process.
    """
    output = directory / "stdout.json"
    with (
        (directory / "stdin.json").open("rb") as request,
        output.open("wb") as captured,
    ):
        child = subprocess.Popen(  # nosec B603
            _interpreter_argv(entry),
            cwd=directory,
            env={},
            stdin=request,
            stdout=captured,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        try:
            code = child.wait(timeout=CalculatorLimits.TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            code = None
            os.killpg(os.getpgid(child.pid), signal.SIGKILL)
            child.wait()
    if code != 0:
        # The vendor's blocked path prints the offending input to stderr, which
        # is why stderr is discarded rather than reported.
        raise Refusal(RefusalCode.METHODOLOGY_CALCULATION_FAILED)
    return output


def _parse(output: Path) -> dict[str, Any]:
    """Bounded by size before it is read, and a mapping or nothing after."""
    if output.stat().st_size > CalculatorLimits.MAX_OUTPUT_BYTES:
        raise Refusal(RefusalCode.METHODOLOGY_CALCULATION_FAILED)
    try:
        result = json.loads(output.read_text(encoding="utf-8"))
    except (ValueError, UnicodeDecodeError):
        result = None
    if not isinstance(result, dict):
        raise Refusal(RefusalCode.METHODOLOGY_CALCULATION_FAILED)
    return result
