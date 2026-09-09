"""A source set is versioned under the case row lock, and immutable once pinned.

"Version allocation locks the case row before reading the current version"
(`SYSTEM_SPEC.md` §5). Editing a pinned set would change what an
already-executed run was pinned to, so the store refuses it rather than the
callers remembering not to.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import psycopg
import pytest

from server.boundary_text import BoundaryText
from server.refusals import Refusal, RefusalCode
from server.store import Store
from server.store.source_sets import pin_source_set
from server.store.sources import Block, SourceDocument, Token, admit_pack

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


@pytest.mark.parametrize("source_id", ["not-a-uuid", "urn:uuid:" + "0" * 32])
def test_a_source_id_that_is_no_id_is_refused_by_code(
    store: Store, source_id: str
) -> None:
    # `ANY(%s)` against a uuid column would otherwise hand the driver's own
    # complaint -- type, column, vendor -- to whoever pinned with a bad id.
    _document("a" * 64)
    admit_pack(store, case_id=CASE, documents=(_document("a" * 64),))
    with pytest.raises(Refusal) as caught:
        pin_source_set(store, case_id=CASE, source_ids=(source_id,))
    assert caught.value.code is RefusalCode.SOURCE_NOT_IN_CASE
    assert caught.value.__context__ is None


def test_pinning_into_an_unknown_case_is_refused(store: Store) -> None:
    (admitted,) = admit_pack(store, case_id=CASE, documents=(_document("a" * 64),))
    with pytest.raises(Refusal) as caught:
        pin_source_set(store, case_id=NOBODY, source_ids=(admitted,))
    assert caught.value.code is RefusalCode.SOURCE_NOT_IN_CASE
