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


def _run(script: str, *args: str, cwd: Path = REPO) -> subprocess.CompletedProcess[str]:
    # `cwd` matters to scan_floors: it reads a report only from under the
    # directory it was invoked in, so a test that writes one to tmp_path runs
    # the script from there. What it holds the report *to* is REPO regardless.
    return subprocess.run(
        [sys.executable, str(REPO / "scripts" / script), *args],
        cwd=cwd,
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
        "scan_floors.py",
        _report(tmp_path, files=[], errors=[]),
        "--min-files",
        "1",
        cwd=tmp_path,
    )
    assert result.returncode != 0
    assert "0 files" in result.stdout + result.stderr


def test_scan_floor_refuses_a_report_with_parse_errors(tmp_path: Path) -> None:
    report = _report(tmp_path, files=["server/api.py"], errors=["syntax error"])
    result = _run(
        "scan_floors.py", report, "--min-files", "1", "--no-parse-errors", cwd=tmp_path
    )
    assert result.returncode != 0
    assert "parse error" in result.stdout + result.stderr


def test_scan_floor_accepts_a_report_that_covered_a_file(tmp_path: Path) -> None:
    report = _report(tmp_path, files=["server/api.py"], errors=[])
    result = _run(
        "scan_floors.py", report, "--min-files", "1", "--no-parse-errors", cwd=tmp_path
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_io_budget_passes_while_no_request_paths_exist(tmp_path: Path) -> None:
    result = _run("io_budget.py", "--assert", "--root", str(tmp_path))
    assert result.returncode == 0, result.stdout + result.stderr


def test_io_budget_refuses_a_declared_budget_no_test_asserts(tmp_path: Path) -> None:
    # A budget nothing asserts is a number in a comment. This is the half of
    # io_budget.py's own contract that was written down and never implemented.
    server = tmp_path / "server"
    server.mkdir(parents=True)
    (server / "reads.py").write_text("IO_BUDGET = 2\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    result = _run("io_budget.py", "--assert", "--root", str(tmp_path))
    assert result.returncode != 0
    assert "reads.py" in result.stdout + result.stderr


def test_io_budget_accepts_a_budget_a_test_asserts(tmp_path: Path) -> None:
    server = tmp_path / "server"
    server.mkdir(parents=True)
    (server / "reads.py").write_text("IO_BUDGET = 2\n", encoding="utf-8")
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_reads.py").write_text(
        "from server.reads import IO_BUDGET\n\n"
        "def test_io_budget_reads() -> None:\n"
        "    assert statements == IO_BUDGET\n",
        encoding="utf-8",
    )
    assert _run("io_budget.py", "--assert", "--root", str(tmp_path)).returncode == 0


def test_io_budget_says_so_when_nothing_declares_a_budget(tmp_path: Path) -> None:
    (tmp_path / "server").mkdir()
    assert _run("io_budget.py", "--assert", "--root", str(tmp_path)).returncode == 0


def test_io_budget_reports_without_asserting(tmp_path: Path) -> None:
    server = tmp_path / "server"
    server.mkdir(parents=True)
    (server / "reads.py").write_text("IO_BUDGET = 2\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
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


def test_one_asserted_budget_does_not_cover_another_module(tmp_path: Path) -> None:
    # The first version of this gate searched the whole suite for the string
    # "assert IO_BUDGET", so any one assertion satisfied every module.
    server = tmp_path / "server"
    server.mkdir(parents=True)
    (server / "reads.py").write_text("IO_BUDGET = 2\n", encoding="utf-8")
    (server / "citations.py").write_text("IO_BUDGET = 2\n", encoding="utf-8")
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_reads.py").write_text(
        "from server.reads import IO_BUDGET\n\n"
        "def test_io_budget_reads() -> None:\n"
        "    assert statements == IO_BUDGET\n",
        encoding="utf-8",
    )
    result = _run("io_budget.py", "--assert", "--root", str(tmp_path))
    assert result.returncode != 0
    output = result.stdout + result.stderr
    assert "citations.py" in output
    assert "reads.py" not in output


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


def test_untested_does_not_accept_a_name_that_only_prose_mentions(
    tmp_path: Path,
) -> None:
    """A comment or a docstring is not a test. Both named a real definition."""
    module = tmp_path / "m.py"
    module.write_text("def accept() -> None: ...\n", encoding="utf-8")
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_x.py").write_text(
        '"""the gate must accept it."""\n# accept is named here too.\n',
        encoding="utf-8",
    )
    assert check_tested.main([str(module), "--tests", str(tests_dir)]) == 1


def test_tracked_python_keeps_a_path_containing_a_space(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "my file.py").write_text("x = 1\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True)
    assert tracked.tracked_python(tmp_path) == [tmp_path / "my file.py"]


def test_declaring_modules_finds_every_budget_under_the_server(
    tmp_path: Path,
) -> None:
    server = tmp_path / "server"
    (server / "evidence").mkdir(parents=True)
    (server / "evidence" / "reads.py").write_text("IO_BUDGET = 2\n", encoding="utf-8")
    (server / "quiet.py").write_text("x = 1\n", encoding="utf-8")
    assert io_budget.declaring_modules(server) == [server / "evidence" / "reads.py"]


def test_asserted_modules_needs_both_the_import_and_the_assertion(
    tmp_path: Path,
) -> None:
    tests = tmp_path / "tests"
    tests.mkdir(parents=True)
    (tests / "test_imports_only.py").write_text(
        "from server.reads import IO_BUDGET\n\ndef test_x() -> None:\n    pass\n",
        encoding="utf-8",
    )
    assert io_budget.asserted_modules(tests, tmp_path) == set()

    (tests / "test_asserts.py").write_text(
        "from server.reads import IO_BUDGET\n\n"
        "def test_x() -> None:\n    assert n == IO_BUDGET\n",
        encoding="utf-8",
    )
    assert io_budget.asserted_modules(tests, tmp_path) == {
        tmp_path / "server" / "reads.py"
    }


def test_tracked_python_ignores_vendored_upstream_code(tmp_path: Path) -> None:
    # The methodology bundle is vendored verbatim and never edited, so our gates
    # must not judge it: a vocabulary or coverage finding there is unactionable.
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "ours.py").write_text("x = 1\n", encoding="utf-8")
    vendored = tmp_path / "vendor" / "deploy-v" / "skills"
    vendored.mkdir(parents=True)
    (vendored / "routing.py").write_text(
        "def get_deal_chunks(): ...\n", encoding="utf-8"
    )
    subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True)

    assert tracked.tracked_python(tmp_path) == [tmp_path / "ours.py"]


def _tracked_under(*directories: str) -> list[str]:
    """What a bandit run over `directories` is expected to have measured."""
    return sorted(
        name
        for directory in directories
        for name in scan_floors.expected_files(REPO, directory)
    )


def test_scan_floor_refuses_a_report_that_skipped_a_file_it_should_have_covered(
    tmp_path: Path,
) -> None:
    # --min-files 1 is the floor `make security` used, and it passes on a report
    # that measured one file out of twenty-nine. The failure scan_floors exists
    # to catch -- bandit silently skipping files on a new interpreter -- is
    # partial, not total, so the floor has to name the file that went unscanned.
    expected = _tracked_under("scripts")
    skipped = expected[0]
    report = _report(tmp_path, files=expected[1:], errors=[])

    result = _run("scan_floors.py", report, "--cover", "scripts", cwd=tmp_path)

    assert result.returncode != 0
    assert skipped in result.stdout + result.stderr


def test_scan_floor_accepts_a_report_that_covered_every_file_it_should_have(
    tmp_path: Path,
) -> None:
    covered = ["scripts", "server", "methodology"]
    report = _report(tmp_path, files=_tracked_under(*covered), errors=[])
    result = _run(
        "scan_floors.py",
        report,
        "--cover",
        *covered,
        "--unscanned",
        "tests",
        cwd=tmp_path,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_scan_floor_refuses_a_tracked_file_that_no_target_accounts_for(
    tmp_path: Path,
) -> None:
    # The floor bandit actually needs. Its 3.14 failure puts every file in
    # `metrics` and lists them under `errors`, so --no-parse-errors is what
    # catches that one. What nothing catches is a source directory nobody
    # pointed the scanner at -- `models/` in Phase 7, and Python either way.
    report = _report(tmp_path, files=_tracked_under("scripts"), errors=[])

    result = _run("scan_floors.py", report, "--cover", "scripts", cwd=tmp_path)

    assert result.returncode != 0
    output = result.stdout + result.stderr
    assert "server/refusals.py" in output
    assert "methodology/bundle.py" in output


def test_unaccounted_files_is_empty_once_every_directory_is_named() -> None:
    every = ["scripts", "server", "methodology", "tests"]
    assert scan_floors.unaccounted_files(REPO, every) == []
    assert "tests/conftest.py" in scan_floors.unaccounted_files(REPO, ["scripts"])


def test_expected_files_names_what_git_tracks_under_the_scanned_directories() -> None:
    expected = scan_floors.expected_files(REPO, "scripts")
    assert "scripts/scan_floors.py" in expected
    assert all(name.startswith("scripts/") for name in expected)


def test_scan_floor_refuses_a_target_directory_that_holds_no_tracked_file(
    tmp_path: Path,
) -> None:
    # A mistyped --cover would expect nothing, and expecting nothing is the
    # vacuous floor this flag replaced. It has to fail closed on its own typo.
    report = _report(tmp_path, files=_tracked_under("scripts"), errors=[])
    result = _run("scan_floors.py", report, "--cover", "srcipts", cwd=tmp_path)
    assert result.returncode != 0
    assert "srcipts" in result.stdout + result.stderr


def test_scan_floor_refuses_a_report_outside_the_directory_it_was_invoked_from(
    tmp_path: Path,
) -> None:
    """The report path is the one argument that reaches the filesystem.

    The third reviewer traced `parse_args` to `read_text` and called it path
    traversal, and for a script an agent invokes it is: nothing stopped
    `scan_floors.py ../../etc/passwd --cobertura` from reading it and then
    reporting on it. A scanner report is a build output of the tree being
    scanned, so the one place it may be read from is under the directory the
    gate was run in -- which is the repository root in the Makefile and in CI.
    """
    inside = tmp_path / "inside"
    inside.mkdir()
    outside = tmp_path / "outside.json"
    outside.write_text('{"metrics": {"server/api.py": {}}}', encoding="utf-8")

    result = _run("scan_floors.py", str(outside), "--min-files", "1", cwd=inside)

    # The report would pass every floor if it were read, so a non-zero exit is
    # the refusal itself and not a floor it fell through.
    assert result.returncode != 0
    assert "outside" in result.stderr


def test_report_within_refuses_a_path_that_escapes_the_base(tmp_path: Path) -> None:
    base = tmp_path / "base"
    base.mkdir()
    (base / "coverage.xml").write_text("", encoding="utf-8")
    (tmp_path / "escaped.xml").write_text("", encoding="utf-8")

    assert (
        scan_floors.report_within(base / "coverage.xml", base)
        == (base / "coverage.xml").resolve()
    )
    for escaping in (tmp_path / "escaped.xml", base / ".." / "escaped.xml"):
        with pytest.raises(ValueError, match="outside"):
            scan_floors.report_within(escaping, base)


def _coverage_report(tmp_path: Path, *, files: list[str]) -> str:
    """A Cobertura report shaped as coverage.py writes one, measuring `files`."""
    classes = "".join(
        f'<class name="{Path(name).name}" filename="{name}"/>' for name in files
    )
    path = tmp_path / "coverage.xml"
    path.write_text(
        '<?xml version="1.0" ?><coverage line-rate="0.5"><sources><source>.'
        f"</source></sources><packages><package><classes>{classes}"
        "</classes></package></packages></coverage>",
        encoding="utf-8",
    )
    return str(path)


def test_cobertura_metrics_names_the_files_the_coverage_run_measured() -> None:
    """The floors read one shape; only where the two formats say it differs."""
    report = (
        '<coverage><packages><package><classes><class filename="server/api.py"/>'
        "</classes></package></packages></coverage>"
    )
    assert scan_floors.covered_files(scan_floors.cobertura_metrics(report)) == [
        "server/api.py"
    ]


def test_the_coverage_floor_refuses_a_report_that_measured_nothing(
    tmp_path: Path,
) -> None:
    """A coverage report is a scanner report: one that scanned nothing fails.

    SonarQube reads this file and reports whatever it finds. A run that wrote an
    empty report imports as no coverage rather than as an error, which is the
    same silent pass `--min-files` exists to refuse for bandit.
    """
    result = _run(
        "scan_floors.py",
        _coverage_report(tmp_path, files=[]),
        "--cobertura",
        cwd=tmp_path,
    )
    assert result.returncode != 0
    assert "0 files" in result.stdout + result.stderr


def test_the_coverage_floor_refuses_a_report_that_left_out_a_tracked_file(
    tmp_path: Path,
) -> None:
    """Partial, not total, is the shape this catches.

    A module no test imports is the one coverage.py would leave out of the
    report entirely, and a file absent from the report is not a file at zero
    per cent -- it raises the percentage of everything else instead.
    """
    expected = _tracked_under("scripts")
    left_out = expected[0]

    result = _run(
        "scan_floors.py",
        _coverage_report(tmp_path, files=expected[1:]),
        "--cobertura",
        "--cover",
        "scripts",
        cwd=tmp_path,
    )

    assert result.returncode != 0
    assert left_out in result.stdout + result.stderr


def test_the_coverage_floor_accepts_a_report_that_measured_every_tracked_file(
    tmp_path: Path,
) -> None:
    covered = ["scripts", "server", "methodology"]
    report = _coverage_report(tmp_path, files=_tracked_under(*covered))
    result = _run(
        "scan_floors.py",
        report,
        "--cobertura",
        "--cover",
        *covered,
        "--unscanned",
        "tests",
        cwd=tmp_path,
    )
    assert result.returncode == 0, result.stdout + result.stderr
