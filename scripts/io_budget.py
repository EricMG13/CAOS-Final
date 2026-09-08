#!/usr/bin/env python3
"""Refuse an I/O budget that no test asserts.

Excessive I/O is the largest single multiple in the measurements behind
docs/AI_CODE_QUALITY.md (~8x), and the predecessor had exactly that defect:
evidence blocks lived in one JSON column, so `read_evidence` parsed every block
of a source on every call.

A module whose cost matters declares `IO_BUDGET`, the number of store
round-trips one call of its path may make. A number nothing asserts is a number
in a comment, so this gate holds the other half of that bargain: every declared
budget must be named by a test that asserts it.
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DECLARATION = "IO_BUDGET"


def declares_budget(source: str, filename: str) -> bool:
    """True when a module assigns `IO_BUDGET` at module level."""
    tree = ast.parse(source, filename=filename)
    targets = (
        target
        for node in tree.body
        if isinstance(node, ast.Assign | ast.AnnAssign)
        for target in (node.targets if isinstance(node, ast.Assign) else [node.target])
    )
    return any(isinstance(t, ast.Name) and t.id == DECLARATION for t in targets)


def declaring_modules(server: Path) -> list[Path]:
    """Every module under `server` that declares a budget."""
    return [
        module
        for module in sorted(server.rglob("*.py"))
        if declares_budget(module.read_text(encoding="utf-8"), str(module))
    ]


def asserted_modules(tests: Path, root: Path) -> set[Path]:
    """The modules whose budget some test both imports and asserts.

    Both halves are required, and per module. Searching the whole suite for the
    string "assert IO_BUDGET" would let one module's assertion vouch for every
    other module's budget, which is a gate that passes because it found
    something rather than because it checked something.
    """
    asserted: set[Path] = set()
    if not tests.is_dir():
        return asserted
    for path in sorted(tests.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        if DECLARATION not in source:
            continue
        tree = ast.parse(source, filename=str(path))
        if not _asserts_budget(tree, source):
            continue
        asserted |= {
            root / f"{dotted.replace('.', '/')}.py" for dotted in _sources(tree)
        }
    return asserted


def _asserts_budget(tree: ast.Module, source: str) -> bool:
    return any(
        DECLARATION in (ast.get_source_segment(source, node) or "")
        for node in ast.walk(tree)
        if isinstance(node, ast.Assert)
    )


def _sources(tree: ast.Module) -> set[str]:
    """The modules a test imports `IO_BUDGET` from."""
    return {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module
        and any(alias.name == DECLARATION for alias in node.names)
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assert", dest="assert_", action="store_true")
    parser.add_argument("--root", type=Path, default=REPO)
    args = parser.parse_args(argv)

    server = args.root / "server"
    if not server.is_dir():
        print("no server yet; nothing to budget")
        return 0

    declared = declaring_modules(server)
    if not declared:
        print(f"no module under {server} declares {DECLARATION}")
        return 0

    asserted = asserted_modules(args.root / "tests", args.root)
    missing = [module for module in declared if module not in asserted]
    for module in missing:
        print(
            f"{module}: declares {DECLARATION} and no test asserts it",
            file=sys.stderr,
        )
    if missing and args.assert_:
        return 1
    print(f"{len(declared) - len(missing)} of {len(declared)} budget(s) asserted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
