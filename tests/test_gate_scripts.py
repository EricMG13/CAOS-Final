"""The two gates that guard against a control passing vacuously.

`scan_floors` refuses a scanner report that covered nothing; `io_budget` refuses
a server that declares no I/O budget. Excessive I/O is the largest single
multiple in the measurements behind docs/AI_CODE_QUALITY.md (~8x), and the
predecessor's `read_evidence` had exactly that defect.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import check_tested
import io_budget
import pytest
import scan_floors
import tracked

REPO = Path(__file__).resolve().parents[1]


def _run(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(REPO / "scripts" / script), *args],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )


def _report(tmp_path: Path, *, files: list[str], errors: list[str]) -> str:
    metrics: dict[str, dict[str, int]] = {name: {"loc": 1} for name in files}
    metrics["_totals"] = {"loc": len(files)}
    path = tmp_path / "bandit.json"
    path.write_text(
        json.dumps({"errors": errors, "metrics": metrics}), encoding="utf-8"
    )
    return str(path)


def test_scan_floor_refuses_a_report_that_covered_no_files(tmp_path: Path) -> None:
    result = _run(
        "scan_floors.py", _report(tmp_path, files=[], errors=[]), "--min-files", "1"
    )
    assert result.returncode != 0
    assert "0 files" in result.stdout + result.stderr


def test_scan_floor_refuses_a_report_with_parse_errors(tmp_path: Path) -> None:
    report = _report(tmp_path, files=["server/api.py"], errors=["syntax error"])
    result = _run("scan_floors.py", report, "--min-files", "1", "--no-parse-errors")
    assert result.returncode != 0
    assert "parse error" in result.stdout + result.stderr


def test_scan_floor_accepts_a_report_that_covered_a_file(tmp_path: Path) -> None:
    report = _report(tmp_path, files=["server/api.py"], errors=[])
    result = _run("scan_floors.py", report, "--min-files", "1", "--no-parse-errors")
    assert result.returncode == 0, result.stdout + result.stderr


def test_io_budget_passes_while_no_request_paths_exist(tmp_path: Path) -> None:
    result = _run("io_budget.py", "--assert", "--root", str(tmp_path))
    assert result.returncode == 0, result.stdout + result.stderr


def test_io_budget_refuses_a_route_module_that_declares_no_budget(
    tmp_path: Path,
) -> None:
    api = tmp_path / "server" / "api"
    api.mkdir(parents=True)
    (api / "routes.py").write_text("def list_cases() -> None: ...\n", encoding="utf-8")
    result = _run("io_budget.py", "--assert", "--root", str(tmp_path))
    assert result.returncode != 0
    assert "IO_BUDGET" in result.stdout + result.stderr


def test_io_budget_ignores_a_server_with_no_request_paths(tmp_path: Path) -> None:
    # Phase 1 ships a store and no routes: there is nothing to budget yet.
    store = tmp_path / "server" / "store"
    store.mkdir(parents=True)
    (store / "runs.py").write_text("def start_run() -> None: ...\n", encoding="utf-8")
    assert _run("io_budget.py", "--assert", "--root", str(tmp_path)).returncode == 0


def test_covered_files_excludes_the_totals_row() -> None:
    report: dict[str, object] = {"metrics": {"server/api.py": {}, "_totals": {}}}
    assert scan_floors.covered_files(report) == ["server/api.py"]


def test_floor_failures_reports_each_floor_separately() -> None:
    report: dict[str, object] = {"metrics": {"_totals": {}}, "errors": ["boom"]}
    failures = scan_floors.floor_failures(report, min_files=1, no_parse_errors=True)
    assert len(failures) == 2


def test_declares_budget_accepts_an_annotated_declaration() -> None:
    assert io_budget.declares_budget("IO_BUDGET: int = 3\n", "m.py")
    assert io_budget.declares_budget("IO_BUDGET = 3\n", "m.py")
    assert not io_budget.declares_budget("io_budget = 3\n", "m.py")


def test_public_definitions_skips_private_names_and_entry_points() -> None:
    source = "def _helper(): ...\ndef main(): ...\nclass Ledger: ...\n"
    assert check_tested.public_definitions(source, "m.py") == [(3, "Ledger")]


def test_tracked_python_returns_what_git_tracks() -> None:
    found = tracked.tracked_python(REPO)
    assert REPO / "scripts" / "tracked.py" in found
    assert all(p.suffix == ".py" for p in found)


def test_untested_does_not_accept_a_name_buried_in_a_longer_word(
    tmp_path: Path,
) -> None:
    module = tmp_path / "m.py"
    module.write_text("def run() -> None: ...\n", encoding="utf-8")
    assert check_tested.untested(module, "the runner runs\n")


def test_tracked_python_keeps_a_path_containing_a_space(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "my file.py").write_text("x = 1\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True)
    assert tracked.tracked_python(tmp_path) == [tmp_path / "my file.py"]


def test_io_budget_reports_without_asserting(tmp_path: Path) -> None:
    api = tmp_path / "server" / "api"
    api.mkdir(parents=True)
    (api / "routes.py").write_text("def list_cases() -> None: ...\n", encoding="utf-8")
    assert _run("io_budget.py", "--root", str(tmp_path)).returncode == 0
    assert _run("io_budget.py", "--assert", "--root", str(tmp_path)).returncode != 0


def test_tracked_python_skips_a_file_that_is_no_longer_on_disk(
    tmp_path: Path,
) -> None:
    # A tracked file can be absent mid-rebase, mid-checkout, or after a delete
    # that is not staged yet. A gate must not stack-trace on it.
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "gone.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "here.py").write_text("y = 2\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True)
    (tmp_path / "gone.py").unlink()

    assert tracked.tracked_python(tmp_path) == [tmp_path / "here.py"]


def test_tracked_python_fails_closed_on_an_unreadable_path(tmp_path: Path) -> None:
    # Path.is_file() returns False for every OSError on 3.14, not only for a
    # missing path, so a permission error would drop a tracked file from the
    # scan silently. A gate that scanned less than it should is a failed gate.
    if os.geteuid() == 0:
        pytest.skip("root ignores the directory mode this test relies on")
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    locked = tmp_path / "locked"
    locked.mkdir()
    (locked / "hidden.py").write_text("x = 1\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True)
    locked.chmod(0o000)
    try:
        with pytest.raises(PermissionError):
            tracked.tracked_python(tmp_path)
    finally:
        locked.chmod(0o755)
