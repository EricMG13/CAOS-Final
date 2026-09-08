#!/usr/bin/env python3
"""Refuse a public function or class that no test names.

Logic and correctness errors are ~75% more frequent in agent-written code
(docs/AI_CODE_QUALITY.md section 1), and the control is a test that was watched
to fail. This gate cannot see whether a test was written first; it can and does
refuse the case where no test mentions the symbol at all.

Scope is module-level definitions. Methods are covered through the class that
holds them -- see the known-gaps ledger in CLAUDE.md.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

from tracked import tracked_python

REPO = Path(__file__).resolve().parents[1]

# CLI entry points are exercised end to end by driving the script as a
# subprocess, which names the file rather than the function.
EXEMPT = frozenset({"main"})


def public_definitions(source: str, filename: str) -> list[tuple[int, str]]:
    """Module-level functions and classes that form a file's public surface."""
    tree = ast.parse(source, filename=filename)
    definitions = (
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef)
    )
    return [
        (node.lineno, node.name)
        for node in definitions
        if not node.name.startswith("_") and node.name not in EXEMPT
    ]


def _named_in(tests_dir: Path) -> str:
    """Every byte of the test suite, as one haystack to search for symbol names."""
    return "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(tests_dir.rglob("*.py"))
    )


def untested(path: Path, haystack: str) -> list[str]:
    """One line per public definition in `path` that the suite never names."""
    source = path.read_text(encoding="utf-8")
    return [
        f"{path}:{lineno}: {name!r} has no test naming it"
        for lineno, name in public_definitions(source, str(path))
        if not re.search(rf"\b{re.escape(name)}\b", haystack)
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument("--tests", type=Path, default=REPO / "tests")
    args = parser.parse_args(argv)

    tests_dir = args.tests.resolve()
    paths = args.paths or [
        p for p in tracked_python(REPO) if not p.is_relative_to(tests_dir)
    ]
    if not paths:
        print(
            "scanned no files; a scan that scanned nothing is a failure",
            file=sys.stderr,
        )
        return 2

    haystack = _named_in(tests_dir) if tests_dir.is_dir() else ""
    found = [line for path in paths for line in untested(path, haystack)]
    for line in found:
        print(line)
    return 1 if found else 0


if __name__ == "__main__":
    raise SystemExit(main())
