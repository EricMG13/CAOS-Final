"""Ingestion: a pack is admitted whole, and a source set is versioned under lock.

"Admit or refuse the whole pack in one transaction" and "version allocation
locks the case row before reading the current version" (SYSTEM_SPEC section 5).
Ingestion is the only way bytes enter a case; web discovery is structurally
absent, so there is no code path to it to test.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import psycopg
import pytest

from server.boundary_text import BoundaryText
from server.refusals import Refusal, RefusalCode
from server.store import Store
from server.store.sources import (
    Block,
    SourceDocument,
    Token,
    admit_pack,
    pin_source_set,
)

CASE = BoundaryText.of("acme")
RIVAL = BoundaryText.of("rival")
NOBODY = BoundaryText.of("nobody")


def _token(text: str) -> Token:
    return Token(
        page=1,
        region_id=1,
        line_id=1,
        ordinal=0,
        text=text,
        x0=Decimal(72),
        y0=Decimal(700),
        x1=Decimal(120),
        y1=Decimal(712),
    )


def _document(digest: str, text: str = "Net leverage was 4.2x") -> SourceDocument:
    return SourceDocument(
        sha256=digest,
        tokens=(_token(text),),
        blocks=(Block(block_id=0, page=1, text=text),),
    )


def test_a_pack_is_admitted_whole(store: Store) -> None:
    admitted = admit_pack(
        store, case_id=CASE, documents=(_document("a" * 64), _document("b" * 64))
    )
    assert len(admitted) == 2
    counted = store.execute(
        "SELECT (SELECT count(*) FROM sources), (SELECT count(*) FROM source_blocks)"
    ).fetchone()
    assert counted == (2, 2)


def test_a_pack_carrying_one_bad_document_admits_none_of_it(store: Store) -> None:
    admit_pack(store, case_id=CASE, documents=(_document("a" * 64),))
    store.commit()
    with pytest.raises(Refusal) as caught:
        # The second document is already in the case; the first is new and must
        # not survive the refusal.
        admit_pack(
            store,
            case_id=CASE,
            documents=(_document("c" * 64), _document("a" * 64)),
        )
    assert caught.value.code is RefusalCode.SOURCE_ALREADY_ADMITTED
    store.rollback()
    remaining = store.execute("SELECT count(*) FROM sources").fetchone()
    assert remaining == (1,)


def test_a_block_is_one_row_keyed_by_source_and_block(store: Store) -> None:
    # The predecessor kept every block of a source in one JSON column, so one
    # read parsed the whole source: the ~8x I/O defect. One row per block is
    # what makes a single block a single row fetch.
    key = store.execute(
        "SELECT a.attname FROM pg_index i"
        " JOIN pg_attribute a ON a.attrelid = i.indrelid"
        " AND a.attnum = ANY(i.indkey)"
        " WHERE i.indrelid = 'source_blocks'::regclass AND i.indisprimary"
        " ORDER BY a.attname"
    ).fetchall()
    assert [name for (name,) in key] == ["block_id", "source_id"]


def test_source_set_versions_start_at_one_and_increment(store: Store) -> None:
    admitted = admit_pack(store, case_id=CASE, documents=(_document("a" * 64),))
    assert pin_source_set(store, case_id=CASE, source_ids=admitted) == 1
    assert pin_source_set(store, case_id=CASE, source_ids=admitted) == 2


def test_versions_are_allocated_under_the_case_lock(
    store: Store, store_schema: str, postgres_dsn: str
) -> None:
    admitted = admit_pack(store, case_id=CASE, documents=(_document("a" * 64),))
    store.commit()

    def pin(_: int) -> int:
        with psycopg.connect(postgres_dsn, autocommit=False) as connection:
            connection.execute(f'SET search_path TO "{store_schema}"')
            return pin_source_set(connection, case_id=CASE, source_ids=admitted)

    with ThreadPoolExecutor(max_workers=4) as pool:
        versions = sorted(pool.map(pin, range(4)))
    assert versions == [1, 2, 3, 4]


def test_a_pinned_source_set_is_immutable(store: Store) -> None:
    admitted = admit_pack(store, case_id=CASE, documents=(_document("a" * 64),))
    pin_source_set(store, case_id=CASE, source_ids=admitted)
    for statement in (
        "UPDATE source_sets SET version = 9",
        "DELETE FROM source_set_members",
    ):
        with pytest.raises(psycopg.errors.RaiseException):
            store.execute(statement)
        store.rollback()


def test_a_source_set_naming_a_source_from_another_case_is_refused(
    store: Store,
) -> None:
    mine = admit_pack(store, case_id=CASE, documents=(_document("a" * 64),))
    theirs = admit_pack(store, case_id=RIVAL, documents=(_document("b" * 64),))
    with pytest.raises(Refusal) as caught:
        pin_source_set(store, case_id=CASE, source_ids=(*mine, *theirs))
    assert caught.value.code is RefusalCode.SOURCE_NOT_IN_CASE


def test_an_empty_source_set_is_refused(store: Store) -> None:
    # A run pinned to no sources has no evidence; pinning one is a mistake made
    # early rather than a run that refuses everything later.
    admit_pack(store, case_id=CASE, documents=(_document("a" * 64),))
    with pytest.raises(Refusal) as caught:
        pin_source_set(store, case_id=CASE, source_ids=())
    assert caught.value.code is RefusalCode.SOURCE_SET_EMPTY


def test_pinning_the_same_source_twice_pins_it_once(store: Store) -> None:
    (admitted,) = admit_pack(store, case_id=CASE, documents=(_document("a" * 64),))
    version = pin_source_set(store, case_id=CASE, source_ids=(admitted, admitted))
    members = store.execute(
        "SELECT count(*) FROM source_set_members WHERE version = %s", (version,)
    ).fetchone()
    assert members == (1,)


def test_pinning_into_an_unknown_case_is_refused(store: Store) -> None:
    (admitted,) = admit_pack(store, case_id=CASE, documents=(_document("a" * 64),))
    with pytest.raises(Refusal) as caught:
        pin_source_set(store, case_id=NOBODY, source_ids=(admitted,))
    assert caught.value.code is RefusalCode.SOURCE_NOT_IN_CASE


def test_a_document_the_store_refuses_is_a_typed_refusal(store: Store) -> None:
    # A block on page 0 violates a CHECK, not a UNIQUE. Every integrity failure
    # must reach the caller as a code, never as a driver exception.
    impossible = SourceDocument(
        sha256="d" * 64,
        tokens=(_token("x"),),
        blocks=(Block(block_id=0, page=0, text="x"),),
    )
    with pytest.raises(Refusal) as caught:
        admit_pack(store, case_id=CASE, documents=(impossible,))
    assert caught.value.code is RefusalCode.SOURCE_NOT_ADMISSIBLE
    assert caught.value.__context__ is None


def test_a_case_id_is_stored_as_boundary_text_normalised_it(store: Store) -> None:
    # Proof that the value reaching pinned state went through the boundary:
    # "e" + U+0301 is two code points in, one out. A bare str would store two.
    admit_pack(
        store,
        case_id=BoundaryText.of("étude"),
        documents=(_document("a" * 64),),
    )
    assert store.execute("SELECT case_id FROM cases").fetchone() == ("étude",)


def test_a_case_id_carrying_a_bidi_override_never_reaches_the_store() -> None:
    with pytest.raises(Refusal) as caught:
        BoundaryText.of("acme‮")
    assert caught.value.code is RefusalCode.BOUNDARY_TEXT_INVALID


def test_a_document_digest_that_is_not_a_digest_is_refused(store: Store) -> None:
    impostor = SourceDocument(sha256="not-a-digest", tokens=(), blocks=())
    with pytest.raises(Refusal) as caught:
        admit_pack(store, case_id=CASE, documents=(impostor,))
    assert caught.value.code is RefusalCode.DIGEST_INVALID
