#!/usr/bin/env python3
"""Refuse a server that declares no I/O budget for its request paths.

Excessive I/O is the largest single multiple in the measurements behind
docs/AI_CODE_QUALITY.md (~8x), and the predecessor had exactly that defect:
evidence blocks lived in one JSON column, so `read_evidence` parsed every block
of a source on every call.

A module that serves a request path declares `IO_BUDGET`, the number of store
round-trips that path may cost. This gate is the floor: the moment `server/api/`
exists, at least one budget must be declared. A module with no request path --
the store, the methodology boundary -- has no round-trip budget to declare, so
the floor is the route directory, not the whole server.
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


def _budgeted_modules(api: Path) -> tuple[list[Path], list[Path]]:
    """Route modules split into those declaring a budget and those not."""
    modules = sorted(p for p in api.rglob("*.py") if p.name != "__init__.py")
    declared = [
        p for p in modules if declares_budget(p.read_text(encoding="utf-8"), str(p))
    ]
    return declared, modules


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assert", dest="assert_", action="store_true")
    parser.add_argument("--root", type=Path, default=REPO)
    args = parser.parse_args(argv)

    api = args.root / "server" / "api"
    if not api.is_dir():
        print("no request paths yet; nothing to budget")
        return 0

    declared, modules = _budgeted_modules(api)
    if not declared:
        print(
            f"{api}: {len(modules)} module(s), none declaring {DECLARATION}; "
            "every request path needs a declared I/O budget",
            file=sys.stderr,
        )
        return 1 if args.assert_ else 0
    print(f"{len(declared)} of {len(modules)} route module(s) declare {DECLARATION}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
