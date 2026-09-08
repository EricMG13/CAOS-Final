"""`read_evidence`: validated at the boundary, fails closed, returns no text.

Invariant 2 (CLAUDE.md): every read is validated at the host boundary and
refuses with a typed code. **No text is returned on refusal** -- not in the
exception chain, the delivered set, or the ledger.

And the ~8x defect: the predecessor kept every block of a source in one JSON
column, so one read parsed the whole source -- 17 ms per read at the ceiling.
One read is one row fetch, and `test_io_budget_read_evidence` measures it.
"""

from __future__ import annotations

from dataclasses import replace

import pytest
from conftest import Counter

from server.boundary_text import BoundaryText
from server.evidence.reads import IO_BUDGET, EvidenceRequest, read_evidence
from server.refusals import Refusal, RefusalCode
from server.store import Store
from server.store.runs import start_run
from server.store.source_sets import pin_source_set
from server.store.sources import Block, SourceDocument, admit_pack

CASE = BoundaryText.of("acme")
NODE = BoundaryText.of("CP-1")
DIGEST = "a" * 64
SECRET = "Net leverage was 4.2x and the covenant is 4.50x"


def _document(digest: str = DIGEST, blocks: int = 1) -> SourceDocument:
    return SourceDocument(
        sha256=digest,
        tokens=(),
        blocks=tuple(
            Block(block_id=n, page=1, text=f"{SECRET} [{n}]") for n in range(blocks)
        ),
    )


@pytest.fixture
def delivered(store: Store) -> EvidenceRequest:
    admit_pack(store, case_id=CASE, documents=(_document(),))
    admitted = store.execute("SELECT source_id FROM sources").fetchall()
    version = pin_source_set(
        store, case_id=CASE, source_ids=tuple(str(row[0]) for row in admitted)
    )
    return EvidenceRequest(
        case_id=CASE,
        source_set_version=version,
        document_sha256=DIGEST,
        block_id=0,
        run_id=start_run(store, case_id=CASE),
        node_id=NODE,
    )


def test_a_delivered_block_is_returned(
    store: Store, delivered: EvidenceRequest
) -> None:
    assert read_evidence(store, delivered).text == f"{SECRET} [0]"


REFUSED: dict[str, list[object]] = {
    "document_sha256": ["not-a-digest", "b" * 64, "", "../" + "a" * 61],
    "block_id": [-1, 99, 2**31],
    "source_set_version": [0, -1, 999],
    "case_id": [BoundaryText.of("rival"), BoundaryText.of("nobody")],
    "run_id": ["00000000-0000-0000-0000-000000000000", "not-a-uuid"],
}


@pytest.mark.parametrize(
    ("field", "bad"),
    [(field, bad) for field, values in REFUSED.items() for bad in values],
)
def test_evidence_refusals_return_no_text(
    store: Store, delivered: EvidenceRequest, field: str, bad: object
) -> None:
    with pytest.raises(Refusal) as caught:
        # The types are deliberately wrong: this asserts what the host does
        # when a caller ignores the contract, which is the whole point.
        read_evidence(store, replace(delivered, **{field: bad}))  # type: ignore[arg-type]

    rendered = f"{caught.value!r} {caught.value!s} {caught.value.args}"
    assert SECRET not in rendered, f"{field}={bad!r} leaked the block's text"
    assert "leverage" not in rendered
    # Not in the exception chain either.
    assert caught.value.__context__ is None
    assert caught.value.__cause__ is None
    assert isinstance(caught.value.code, RefusalCode)


def test_a_refused_read_is_not_recorded_as_delivered(
    store: Store, delivered: EvidenceRequest
) -> None:
    with pytest.raises(Refusal):
        read_evidence(store, replace(delivered, block_id=99))
    assert store.execute("SELECT count(*) FROM delivered_evidence").fetchone() == (0,)


def test_a_delivered_block_is_recorded_once_per_node(
    store: Store, delivered: EvidenceRequest
) -> None:
    read_evidence(store, delivered)
    read_evidence(store, delivered)
    assert store.execute("SELECT count(*) FROM delivered_evidence").fetchone() == (1,)


def test_io_budget_read_evidence(
    store: Store, delivered: EvidenceRequest, count_io: Counter
) -> None:
    # The predecessor's read parsed every block of a source. Reading one block
    # of a five-hundred-block source must cost what reading one block costs.
    admit_pack(store, case_id=CASE, documents=(_document("c" * 64, blocks=500),))
    big = store.execute(
        "SELECT source_id FROM sources WHERE sha256 = %s", ("c" * 64,)
    ).fetchone()
    assert big is not None
    version = pin_source_set(store, case_id=CASE, source_ids=(str(big[0]),))
    store.commit()

    with count_io(store) as tally:
        read_evidence(
            store,
            replace(
                delivered,
                document_sha256="c" * 64,
                source_set_version=version,
                block_id=250,
            ),
        )

    assert tally.statements == IO_BUDGET
    assert tally.rows == 1, "one block of a 500-block source is one row"
