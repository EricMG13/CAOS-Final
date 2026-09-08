"""Admitting a source is typed, all-or-nothing, and says nothing about vendors.

"Admit a pack or refuse it, in one transaction" (docs/REBUILD_PLAN.md Phase 2),
and the standing rule that only typed refusals cross the boundary: a caller must
never receive a driver exception whose string names a constraint, a table or
PostgreSQL itself.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from server.refusals import Refusal, RefusalCode
from server.store import Store
from server.store.sources import SourceDocument, Token, admit_pack

DIGEST = "d" * 64


def _token(ordinal: int, text: str) -> Token:
    return Token(
        page=1,
        region_id=1,
        line_id=1,
        ordinal=ordinal,
        text=text,
        x0=Decimal(72),
        y0=Decimal(700),
        x1=Decimal(120),
        y1=Decimal(712),
    )


def _admit(store: Store, tokens: list[Token]) -> None:
    admit_pack(
        store,
        case_id="acme",
        documents=(SourceDocument(sha256=DIGEST, tokens=tuple(tokens), blocks=()),),
    )


def test_the_same_document_is_admitted_to_a_case_only_once(store: Store) -> None:
    _admit(store, [_token(0, "x")])
    with pytest.raises(Refusal) as caught:
        _admit(store, [_token(0, "x")])
    assert caught.value.code is RefusalCode.SOURCE_ALREADY_ADMITTED


def test_a_token_index_with_a_repeated_position_is_refused(store: Store) -> None:
    with pytest.raises(Refusal) as caught:
        _admit(store, [_token(0, "x"), _token(0, "y")])
    assert caught.value.code is RefusalCode.SOURCE_TOKEN_INDEX_INVALID


def test_a_refused_admission_leaves_nothing_behind(store: Store) -> None:
    with pytest.raises(Refusal):
        _admit(store, [_token(0, "x"), _token(0, "y")])
    store.rollback()
    remaining = store.execute(
        "SELECT (SELECT count(*) FROM sources), (SELECT count(*) FROM source_tokens)"
    ).fetchone()
    assert remaining == (0, 0)


def test_a_refusal_names_no_constraint_table_or_vendor(store: Store) -> None:
    _admit(store, [_token(0, "x")])
    with pytest.raises(Refusal) as caught:
        _admit(store, [_token(0, "x")])
    rendered = f"{caught.value!r} {caught.value!s} {caught.value.args}"
    for leak in ("sources", "psycopg", "duplicate key", "postgres", "sha256"):
        assert leak not in rendered.lower()
    # No text is returned on refusal -- not in the exception chain either.
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None
