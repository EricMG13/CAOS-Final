#!/usr/bin/env python3
"""Refuse a scanner report that covered nothing, or that failed to parse a file.

bandit 1.7.10 reaches for `ast.Constant.s`, which newer interpreters no longer
provide: under Python 3.14 it skips every server file and exits 0. A green SAST
gate that scanned nothing is worse than a red one, because it is believed.
See docs/AI_CODE_QUALITY.md section 4.

That one is caught by `--no-parse-errors`: under 3.14 bandit still lists all 29
files in `metrics`, with their line counts, and files the 26 it choked on under
`errors` -- verified, not assumed. What no floor caught was the other shape, a
file the scan never reached at all. `--cover` names the directories it was
pointed at, `--unscanned` the ones deliberately left out, and every tracked .py
in the repository has to fall under one of them. A source package added in a
later phase cannot go unscanned quietly; somebody has to say which it is.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

# B405 and B314 below: bandit reads anything after the test id as another test
# id, so the reason is here. It is in `cobertura_metrics`, which is the only
# caller.
from xml.etree import ElementTree  # nosec B405

from tracked import tracked_python

REPO = Path(__file__).resolve().parents[1]


def covered_files(report: Mapping[str, object]) -> list[str]:
    """The files a bandit report actually measured, excluding its own totals row."""
    metrics = report.get("metrics")
    if not isinstance(metrics, dict):
        return []
    return [name for name in metrics if name != "_totals"]


def cobertura_metrics(report: str) -> Mapping[str, object]:
    """A Cobertura coverage report in the shape the floors already read.

    A coverage report is a scanner report, and it falls through the same floors:
    one that measured nothing, or that left out a file it was pointed at, is a
    report SonarQube imports as a number rather than as an error. Both formats
    state which files were measured and only where they state it differs, so
    this normalises rather than growing a second set of floors.

    The report is written by coverage.py in the same job that reads it, so the
    entity attacks B314 is about would have to come from a run that already had
    the machine. `ElementTree` over `defusedxml` for that reason: the dependency
    would buy nothing here and needs a decision entry of its own.
    """
    root = ElementTree.fromstring(report)  # nosec B314
    measured = (element.get("filename") for element in root.iter("class"))
    return {"metrics": {name: {} for name in measured if name is not None}}


def expected_files(repo: Path, directory: str) -> list[str]:
    """Repo-relative .py paths a scan of `directory` is expected to measure.

    `tracked_python` rather than a walk, so the floor and the two identifier
    gates all mean the same thing by "ours": what git tracks, minus vendor.
    """
    root = repo / directory
    return sorted(
        str(path.relative_to(repo))
        for path in tracked_python(repo)
        if path.is_relative_to(root)
    )


def unaccounted_files(repo: Path, directories: Sequence[str]) -> list[str]:
    """Tracked .py under `repo` that none of `directories` claims."""
    roots = [repo / directory for directory in directories]
    return sorted(
        str(path.relative_to(repo))
        for path in tracked_python(repo)
        if not any(path.is_relative_to(root) for root in roots)
    )


def _parse_errors(report: Mapping[str, object]) -> list[object]:
    errors = report.get("errors")
    return list(errors) if isinstance(errors, list) else []


def floor_failures(
    report: Mapping[str, object],
    *,
    min_files: int,
    no_parse_errors: bool,
    must_cover: Mapping[str, Sequence[str]] | None = None,
    unaccounted: Sequence[str] = (),
) -> list[str]:
    """One line per floor the report fell through.

    `must_cover` maps each directory the scan was pointed at to the tracked
    files it holds, so a target that holds none is itself a failure: expecting
    nothing is the vacuous floor this argument exists to replace.
    """
    failures = []
    covered = covered_files(report)
    if len(covered) < min_files:
        failures.append(
            f"scanned {len(covered)} files, floor is {min_files}; "
            "a scan that scanned nothing is a failure"
        )
    expected = must_cover or {}
    barren = sorted(name for name, files in expected.items() if not files)
    if barren:
        failures.append(
            f"targets holding no tracked .py: {barren}; "
            "a target that expects nothing is a floor that checks nothing"
        )
    wanted = {name for files in expected.values() for name in files}
    skipped = sorted(wanted - set(covered))
    if skipped:
        failures.append(
            f"did not measure {len(skipped)} of {len(wanted)} tracked files under "
            f"its targets: {skipped}; a scan that skipped a file is a failure"
        )
    if unaccounted:
        failures.append(
            f"{len(unaccounted)} tracked file(s) no target accounts for: "
            f"{list(unaccounted)}; scan them, or name their directory --unscanned"
        )
    errors = _parse_errors(report)
    if no_parse_errors and errors:
        failures.append(f"report carries {len(errors)} parse error(s)")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--min-files", type=int, default=1)
    parser.add_argument("--no-parse-errors", action="store_true")
    parser.add_argument(
        "--cover",
        nargs="+",
        default=[],
        metavar="DIR",
        help="the directories the scan was pointed at",
    )
    parser.add_argument(
        "--unscanned",
        nargs="+",
        default=[],
        metavar="DIR",
        help="directories deliberately left out; each needs a ledger entry",
    )
    parser.add_argument(
        "--cobertura",
        action="store_true",
        help="read a Cobertura coverage report rather than a bandit JSON one",
    )
    args = parser.parse_args(argv)

    text = args.report.read_text(encoding="utf-8")
    report = cobertura_metrics(text) if args.cobertura else json.loads(text)
    failures = floor_failures(
        report,
        min_files=args.min_files,
        no_parse_errors=args.no_parse_errors,
        must_cover={name: expected_files(REPO, name) for name in args.cover},
        # Only a caller that named its targets can be held to the whole tree.
        unaccounted=(
            unaccounted_files(REPO, [*args.cover, *args.unscanned])
            if args.cover
            else []
        ),
    )
    for line in failures:
        print(f"{args.report}: {line}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
