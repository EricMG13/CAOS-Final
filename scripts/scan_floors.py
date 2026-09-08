#!/usr/bin/env python3
"""Refuse a scanner report that covered nothing, or that failed to parse a file.

bandit 1.7.10 reaches for `ast.Constant.s`, which newer interpreters no longer
provide: under Python 3.14 it skips every server file and exits 0. A green SAST
gate that scanned nothing is worse than a red one, because it is believed.
See docs/AI_CODE_QUALITY.md section 4.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping
from pathlib import Path


def covered_files(report: Mapping[str, object]) -> list[str]:
    """The files a bandit report actually measured, excluding its own totals row."""
    metrics = report.get("metrics")
    if not isinstance(metrics, dict):
        return []
    return [name for name in metrics if name != "_totals"]


def _parse_errors(report: Mapping[str, object]) -> list[object]:
    errors = report.get("errors")
    return list(errors) if isinstance(errors, list) else []


def floor_failures(
    report: Mapping[str, object], *, min_files: int, no_parse_errors: bool
) -> list[str]:
    """One line per floor the report fell through."""
    failures = []
    covered = covered_files(report)
    if len(covered) < min_files:
        failures.append(
            f"scanned {len(covered)} files, floor is {min_files}; "
            "a scan that scanned nothing is a failure"
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
    args = parser.parse_args(argv)

    report = json.loads(args.report.read_text(encoding="utf-8"))
    failures = floor_failures(
        report, min_files=args.min_files, no_parse_errors=args.no_parse_errors
    )
    for line in failures:
        print(f"{args.report}: {line}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
