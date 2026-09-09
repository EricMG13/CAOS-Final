#!/usr/bin/env python3
"""Refuse an identifier that spells a CONTEXT.md term by one of its synonyms.

Naming inconsistency is ~2x more frequent in agent-written code
(docs/AI_CODE_QUALITY.md section 1). CONTEXT.md is the single glossary; this
check is what makes it binding on code rather than on intention.

Only identifiers are examined -- never prose, never string literals -- because
the defect being prevented is two spellings of one concept minting two lineages.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from collections.abc import Iterator
from pathlib import Path

from tracked import tracked_python

REPO = Path(__file__).resolve().parents[1]
CONTEXT_MD = REPO / "CONTEXT.md"

# Synonyms with no plausible non-domain meaning in this repository. An
# identifier containing one of these is always the wrong word.
ENFORCED = frozenset(
    {
        "deal",
        "corpus",
        "chunk",
        "fragment",
        "passage",
        "footnote",
        "pipeline",
        "workflow",
        "ready_set",
    }
)

# Synonyms that also carry an ordinary technical meaning here. Enforcing them on
# identifiers would refuse `file_path`, `node_states`, `response_model` and the
# `users` table, so each is exempt for a stated reason instead of silently.
NOT_ENFORCED = {
    "project": "Python packaging metadata is a [project] table",
    "file": "a filesystem file is a file",
    "upload": "an HTTP multipart upload is an upload",
    "attachment": "email and docx attachments are attachments",
    "pack": "an intake pack is admitted or refused as a whole (SYSTEM_SPEC 5)",
    "reference": "reference_files is the bundle's own field name",
    "agent": "an agent module is the bundle's own word for CP-CF and CP-DR",
    "step": "a build step or CI step is a step",
    "task": "an asyncio task is a task",
    "graph": "no domain use; retained for the frontend dependency drawing",
    "queue": "a work queue for model builds is a queue (SYSTEM_SPEC 1)",
    "result": "subprocess and DB cursor results are results",
    "response": "an HTTP response is a response",
    "version": "source-set and schema versions are versions (SYSTEM_SPEC 5)",
    "state": "node_states is the bundle's own word (CONTEXT.md node states)",
    "model_run": "multi-word; `model` and `run` are both live domain terms",
    "draft": "deliverable_drafts is the spec's own table (SYSTEM_SPEC 2)",
    "report": "a scanner report is a report (scan_floors.py)",
    "output": "max_output_tokens is the registry's own field name",
    "export": "static export and workbook export are the spec's words",
    "approval": "plan_approval is the registry's own field name",
    "sign_off_of_the_deliverable": "multi-word prose, not an identifier shape",
    "publication": "deliverable_publications is the spec's own table",
    "release": "a Deploy V release is a release (DECISIONS.md 6)",
}


def _normalise(phrase: str) -> str:
    """Lower-case a phrase or identifier to underscore-joined word tokens."""
    spaced = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", phrase)
    return re.sub(r"[^a-z0-9]+", "_", spaced.lower()).strip("_")


def banned_terms(context_md: str) -> dict[str, str]:
    """Map every synonym in CONTEXT.md's Domain table to the term it displaces."""
    banned: dict[str, str] = {}
    for line in context_md.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 3 or not cells[0].startswith("**"):
            continue
        term = cells[0].strip("*")
        for phrase in cells[2].split(","):
            token = _normalise(phrase)
            if token:
                banned[token] = term
    return banned


def unclassified(banned: dict[str, str]) -> tuple[set[str], set[str]]:
    """Synonyms CONTEXT.md declares but this file does not classify, and vice versa."""
    classified = set(ENFORCED) | set(NOT_ENFORCED)
    return set(banned) - classified, classified - set(banned)


def identifiers(tree: ast.Module) -> Iterator[tuple[int, str]]:
    """Every name this module defines: functions, classes, arguments, targets."""
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            yield node.lineno, node.name
        elif isinstance(node, ast.arg):
            yield node.lineno, node.arg
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            yield node.lineno, node.id
        elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Store):
            yield node.lineno, node.attr
        elif isinstance(node, ast.alias):
            yield node.lineno, node.asname or node.name
        elif isinstance(node, ast.ExceptHandler | ast.MatchAs) and node.name:
            yield node.lineno, node.name


def violations(path: Path, banned: dict[str, str]) -> Iterator[str]:
    """One line per identifier that uses a synonym, naming the term to use instead."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    named = [(1, path.stem), *identifiers(tree)]
    for lineno, name in named:
        normalised = _normalise(name)
        words = set(normalised.split("_"))
        # `chunks` is the same wrong word as `chunk`; plural collection
        # names are the shape agent-written code reaches for most.
        words |= {word[:-1] for word in words if word.endswith("s")}
        for token in ENFORCED:
            # A multi-word synonym is matched on word boundaries: `already_set`
            # contains `ready_set` as a substring and is not that concept.
            if "_" in token:
                pattern = rf"(?:^|_){re.escape(token)}s?(?:_|$)"
                hit = re.search(pattern, normalised) is not None
            else:
                hit = token in words
            if hit:
                yield f"{path}:{lineno}: {name!r} says {token!r}; use {banned[token]!r}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path)
    args = parser.parse_args(argv)

    banned = banned_terms(CONTEXT_MD.read_text(encoding="utf-8"))
    missing, stale = unclassified(banned)
    if missing or stale:
        print(
            "CONTEXT.md and check_vocabulary.py disagree. "
            f"unclassified: {sorted(missing)}; not in CONTEXT.md: {sorted(stale)}",
            file=sys.stderr,
        )
        return 2

    paths = args.paths or tracked_python(REPO)
    if not paths:
        print(
            "scanned no files; a scan that scanned nothing is a failure",
            file=sys.stderr,
        )
        return 2

    found = [line for path in paths for line in violations(path, banned)]
    for line in found:
        print(line)
    return 1 if found else 0


if __name__ == "__main__":
    raise SystemExit(main())
