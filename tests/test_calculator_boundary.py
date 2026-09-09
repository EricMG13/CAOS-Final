"""The calculator execution boundary (SYSTEM_SPEC 3).

A module asks for a calculation; it never supplies the code. The host owns
selection, verifies the bytes it is about to run, bounds what model-authored
input may cost, and runs the result where it can reach nothing.
"""

from __future__ import annotations

import ast
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

from methodology.bundle import BUNDLE_ROOT
from methodology.calculators import (
    MAX_PERIODS,
    CalculatorLimits,
    CalculatorSpec,
    _execute,
    _kill_group,
    calculator_spec,
    run_calculator,
)
from server.refusals import Refusal, RefusalCode

METRICS = "credit_metrics"
ONE_PERIOD = {
    "periods": {
        "FY24": {
            "revenue": 1000.0,
            "ebitda": 200.0,
            "total_debt": 800.0,
            "cash_and_equivalents": 100.0,
            "cash_interest_paid": 50.0,
        }
    }
}


@pytest.fixture
def bundle_copy(tmp_path: Path) -> Path:
    root = tmp_path / "deploy-v"
    shutil.copytree(BUNDLE_ROOT, root, symlinks=True)
    return root


def test_credit_metrics_runs_and_returns_what_the_host_asked_for() -> None:
    """The round trip. Not the vendor's arithmetic -- upstream tests that."""
    result = run_calculator("CP-1", METRICS, ONE_PERIOD)
    assert set(result) == {"periods"}
    kpis = result["periods"]["FY24"]["kpis"]
    assert kpis["total_leverage"] == 4.0
    assert kpis["net_leverage"] == 3.5


def test_an_undeclared_calculator_pair_is_refused() -> None:
    with pytest.raises(Refusal) as refused:
        run_calculator("CP-1", "not_a_calculator", ONE_PERIOD)
    assert refused.value.code is RefusalCode.METHODOLOGY_CALCULATOR_UNKNOWN


def test_a_module_cannot_select_another_modules_calculator() -> None:
    """Selection is the pair, not the id: CP-2 has no `credit_metrics`."""
    with pytest.raises(Refusal) as refused:
        run_calculator("CP-2", METRICS, ONE_PERIOD)
    assert refused.value.code is RefusalCode.METHODOLOGY_CALCULATOR_UNKNOWN


def test_a_superseded_module_id_selects_its_live_owners_calculator() -> None:
    """The registry resolves aliases everywhere else; selection is no exception."""
    spec: CalculatorSpec = calculator_spec("CP-1E", "confidence_score")
    assert spec.module_id == "CP-1D"
    assert spec.skill_slug == "cp-1d-earnings-quality"
    assert spec.entry == "scripts/confidence_score.py"
    assert spec.helpers == ()


def test_a_calculators_declared_helpers_travel_with_it() -> None:
    spec: CalculatorSpec = calculator_spec("CP-1", METRICS)
    assert spec.entry == "scripts/credit_metrics.py"
    assert spec.helpers == (
        "scripts/cp_tables.py",
        "scripts/validate_handoff.py",
    )


def test_a_tampered_calculator_refuses_before_it_runs(bundle_copy: Path) -> None:
    """Invariant 4, on the code path that executes rather than prompts."""
    entry = (
        bundle_copy / "skills/cp-1-canonical-data-foundation/scripts/credit_metrics.py"
    )
    entry.write_text(entry.read_text() + "\n# tampered\n", encoding="utf-8")
    with pytest.raises(Refusal) as refused:
        run_calculator("CP-1", METRICS, ONE_PERIOD, root=bundle_copy)
    assert refused.value.code is RefusalCode.METHODOLOGY_AUTHORITY_MISMATCH


def test_a_tampered_helper_refuses_too(bundle_copy: Path) -> None:
    """`credit_metrics` imports `cp_tables`, which imports `validate_handoff`.

    Verifying the entry alone would run tampered arithmetic through a clean
    front door.
    """
    helper = (
        bundle_copy
        / "skills/cp-1-canonical-data-foundation/scripts/validate_handoff.py"
    )
    helper.write_text(helper.read_text() + "\n# tampered\n", encoding="utf-8")
    with pytest.raises(Refusal) as refused:
        run_calculator("CP-1", METRICS, ONE_PERIOD, root=bundle_copy)
    assert refused.value.code is RefusalCode.METHODOLOGY_AUTHORITY_MISMATCH


def test_the_declared_helpers_are_closed_under_the_entrys_imports() -> None:
    """The declared set must cover what the code actually imports.

    Declared rather than discovered, because the bundle is frozen -- but a
    declaration nobody checks is a comment. This walks the real import graph.
    """
    spec = calculator_spec("CP-1", METRICS)
    folder = BUNDLE_ROOT / "skills" / spec.skill_slug
    declared = {Path(name).stem for name in (spec.entry, *spec.helpers)}
    seen: set[str] = set()
    pending = [spec.entry]
    while pending:
        current = pending.pop()
        if current in seen:
            continue
        seen.add(current)
        tree = ast.parse((folder / current).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                sibling = folder / "scripts" / f"{node.module}.py"
                if sibling.is_file():
                    assert node.module in declared, f"undeclared helper: {node.module}"
                    pending.append(f"scripts/{node.module}.py")


def test_work_factor_is_enforced_before_the_vendor_script() -> None:
    """A looser script must never widen what model-authored input may cost."""
    too_many = {"periods": {f"P{n}": {"revenue": 1.0} for n in range(MAX_PERIODS + 1)}}
    with pytest.raises(Refusal) as refused:
        run_calculator("CP-1", METRICS, too_many)
    assert refused.value.code is RefusalCode.METHODOLOGY_INPUT_INVALID


def test_an_oversized_payload_is_refused_before_anything_is_read() -> None:
    huge = {"periods": {"FY24": {"revenue": "9" * (CalculatorLimits.MAX_INPUT_BYTES)}}}
    with pytest.raises(Refusal) as refused:
        run_calculator("CP-1", METRICS, huge)
    assert refused.value.code is RefusalCode.METHODOLOGY_INPUT_INVALID


def test_the_calculator_cannot_import_the_hosts_own_dependencies() -> None:
    """`-I` alone leaves the venv's site-packages on the child's path.

    A calculator that can import the store's driver is a calculator that can
    open a socket to the store. Driven through the real execution path with a
    synthetic calculator, because asserting the flag string would pass while
    the sandbox did nothing.
    """
    probe = (
        "import json,sys\n"
        "try:\n"
        "    import psycopg\n"
        "    reached = True\n"
        "except ImportError:\n"
        "    reached = False\n"
        "sys.stdin.read()\n"
        'print(json.dumps({"reached": reached}))\n'
    )
    assert _execute({"probe.py": probe}, "probe.py", "{}") == {"reached": False}


def test_a_calculator_that_never_returns_is_killed() -> None:
    """A ceiling that does not stop the work is bookkeeping (invariant 8)."""
    forever = "import time\ntime.sleep(600)\n"
    started = time.monotonic()
    with pytest.raises(Refusal) as refused:
        _execute({"slow.py": forever}, "slow.py", "{}")
    assert refused.value.code is RefusalCode.METHODOLOGY_CALCULATION_FAILED
    assert time.monotonic() - started < CalculatorLimits.TIMEOUT_SECONDS + 5


def test_output_beyond_the_ceiling_is_refused_without_being_read() -> None:
    # Valid JSON, so only the size ceiling can refuse it. Garbage output would
    # be refused by the parser and this would pass with no ceiling at all.
    size = CalculatorLimits.MAX_OUTPUT_BYTES + 1
    flood = (
        "import json, sys\n"
        "sys.stdin.read()\n"
        f"print(json.dumps({{'pad': 'x' * {size}}}))\n"
    )
    with pytest.raises(Refusal) as refused:
        _execute({"flood.py": flood}, "flood.py", "{}")
    assert refused.value.code is RefusalCode.METHODOLOGY_CALCULATION_FAILED


def test_a_calculator_failure_carries_no_vendor_text() -> None:
    """The vendor writes `{"error": str(exc)}` to stderr, echoing our input."""
    with pytest.raises(Refusal) as refused:
        run_calculator(
            "CP-1", METRICS, {"periods": {"FY24": {"revenue": "not a number"}}}
        )
    assert refused.value.code is RefusalCode.METHODOLOGY_CALCULATION_FAILED
    joined = " ".join(str(part) for part in refused.value.args)
    assert "not a number" not in joined
    assert "credit_metrics" not in joined


def test_calculator_output_is_json_the_host_can_name() -> None:
    """Whatever the vendor prints, the host returns a mapping or refuses."""
    result = run_calculator("CP-1", METRICS, ONE_PERIOD)
    assert isinstance(result, dict)
    json.dumps(result)  # returned shape is serialisable, not a live object


def test_killing_the_group_tolerates_a_child_that_already_exited() -> None:
    """The child can exit between the timeout and the kill.

    A `ProcessLookupError` escaping there would replace the typed refusal with
    an untyped one, which is the failure `server/refusals.py` exists to stop.
    """
    finished = subprocess.Popen(
        [sys.executable, "-I", "-S", "-c", ""], start_new_session=True
    )
    finished.wait()
    _kill_group(finished.pid)  # must not raise


def test_a_calculator_that_leaves_a_read_only_directory_still_returns() -> None:
    """Cleanup must not turn a finished calculation into an error."""
    litter = (
        "import json, os, sys\n"
        "sys.stdin.read()\n"
        "os.mkdir('locked')\n"
        "open('locked/f', 'w').write('x')\n"
        "os.chmod('locked', 0o500)\n"
        'print(json.dumps({"ok": True}))\n'
    )
    assert _execute({"litter.py": litter}, "litter.py", "{}") == {"ok": True}
