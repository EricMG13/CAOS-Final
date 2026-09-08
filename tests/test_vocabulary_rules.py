"""Unit rules behind the vocabulary gate.

CONTEXT.md is the only glossary. These assert that the gate reads it rather than
carrying a second copy, that it refuses to run when the two have drifted, and
that it looks at identifiers rather than at prose.
"""

from __future__ import annotations

import ast
from pathlib import Path

import check_vocabulary

REPO = Path(__file__).resolve().parents[1]
CONTEXT_MD = (REPO / "CONTEXT.md").read_text(encoding="utf-8")


def test_banned_terms_reads_the_domain_table() -> None:
    banned = check_vocabulary.banned_terms(CONTEXT_MD)
    assert banned["deal"] == "case"
    assert banned["chunk"] == "block"
    assert banned["ready_set"] == "frontier"
    # Node-state and edge-type prose is not a table and must not be harvested.
    assert "restricted" not in banned


def test_every_context_synonym_is_classified() -> None:
    missing, stale = check_vocabulary.unclassified(
        check_vocabulary.banned_terms(CONTEXT_MD)
    )
    assert missing == set(), f"CONTEXT.md synonyms nothing classifies: {missing}"
    assert stale == set(), f"classified synonyms CONTEXT.md no longer lists: {stale}"


def test_a_new_context_synonym_is_unclassified_until_someone_decides() -> None:
    doctored = CONTEXT_MD + "\n| **case** | one engagement | matter |\n"
    missing, _ = check_vocabulary.unclassified(check_vocabulary.banned_terms(doctored))
    assert missing == {"matter"}


def test_identifiers_ignores_prose_and_string_literals() -> None:
    tree = ast.parse('DOC = "the deal chunk"\n')
    found = {name for _, name in check_vocabulary.identifiers(tree)}
    assert found == {"DOC"}


def test_violations_reads_camel_case_as_words(tmp_path: Path) -> None:
    module = tmp_path / "m.py"
    module.write_text("def loadDealChunks() -> None: ...\n", encoding="utf-8")
    reported = list(
        check_vocabulary.violations(module, check_vocabulary.banned_terms(CONTEXT_MD))
    )
    # Two wrong words in one name, each reported against the term it displaces.
    assert {line.rsplit("use ", 1)[1] for line in reported} == {"'case'", "'block'"}


def test_violations_reads_the_file_name_too(tmp_path: Path) -> None:
    module = tmp_path / "deal_store.py"
    module.write_text("x = 1\n", encoding="utf-8")
    reported = list(
        check_vocabulary.violations(module, check_vocabulary.banned_terms(CONTEXT_MD))
    )
    assert len(reported) == 1
    assert "'case'" in reported[0]


def test_identifiers_includes_imported_names() -> None:
    tree = ast.parse("import chunker\nfrom x import y as fragment_reader\n")
    found = {name for _, name in check_vocabulary.identifiers(tree)}
    assert found == {"chunker", "fragment_reader"}


def test_violations_catches_a_plural_synonym(tmp_path: Path) -> None:
    module = tmp_path / "m.py"
    module.write_text("def read_chunks() -> None: ...\n", encoding="utf-8")
    reported = list(
        check_vocabulary.violations(module, check_vocabulary.banned_terms(CONTEXT_MD))
    )
    assert len(reported) == 1
    assert "'block'" in reported[0]
