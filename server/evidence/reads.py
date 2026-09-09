"""`read_evidence`: the only way a module sees a document.

Invariant 2: every read is validated at the host boundary and refuses with a
typed code. No text is returned on refusal -- not in the exception chain, the
delivered set, or the ledger -- so a refusal cannot be used to probe what a case
holds. Every wrong argument produces the same code for the same reason: a module
asking for a block it was not given learns only that it was not given it.

The predecessor kept every block of a source in one JSON column, so one read
parsed the whole source: ~17 ms per read at the ceiling, ~1.4 s per run. A block
is one row, addressed directly, and IO_BUDGET is what holds it there.
"""

from __future__ import annotations

from dataclasses import dataclass

from server.boundary_text import BoundaryText
from server.digests import checked_digest, checked_uuid
from server.refusals import Refusal, RefusalCode
from server.store import Store
from server.store.sources import Block

# One row fetch for the block, one row recording that it was delivered. Never a
# whole-source parse: docs/AI_CODE_QUALITY.md section 1, the ~8x failure mode.
IO_BUDGET = 2

# Postgres integer. A block id outside it is a malformed request, not a miss.
_MAX_BLOCK_ID = 2**31 - 1


@dataclass(frozen=True, slots=True)
class EvidenceRequest:
    """One module's request for one block, as the host will check it."""

    case_id: BoundaryText
    source_set_version: int
    document_sha256: str
    block_id: int
    run_id: str
    node_id: BoundaryText


def _checked(request: EvidenceRequest) -> tuple[str, str]:
    """The request's run id and digest, once every field is found well-formed.

    Shape is checked before the store is touched, so a malformed request never
    reaches SQL: a driver's own complaint about a bad uuid or an out-of-range
    integer would name the type, the column and the vendor. The run id comes
    back in the store's own spelling, so the check and the query agree.
    """
    if not 0 <= request.block_id <= _MAX_BLOCK_ID:
        raise Refusal(RefusalCode.EVIDENCE_REQUEST_INVALID)
    if request.source_set_version <= 0:
        raise Refusal(RefusalCode.EVIDENCE_REQUEST_INVALID)
    run_id = checked_uuid(request.run_id, refusal=RefusalCode.EVIDENCE_REQUEST_INVALID)
    return run_id, checked_digest(request.document_sha256)


def read_evidence(store: Store, request: EvidenceRequest) -> Block:
    """Deliver one block of one pinned source, or refuse without saying why.

    The single statement is the boundary: a block is reachable only through the
    source set its case pinned, by a run belonging to that same case, so
    membership, case ownership, run ownership and existence are one question
    with one answer. Splitting them would answer four, and the differences
    between those answers are what a module would read the case with.
    Withdrawal is checked live at this use as invariant 1 asks, by reading the
    source through `live_sources` -- the one view every use of a source goes
    through -- so a withdrawn block is refused as any block the module was not
    given.
    """
    run_id, digest = _checked(request)
    with store.transaction():
        found = store.execute(
            "SELECT b.source_id, b.block_id, b.page, b.text"
            " FROM source_blocks b"
            " JOIN live_sources s ON s.source_id = b.source_id"
            " JOIN source_set_members m ON m.source_id = b.source_id"
            " JOIN runs r ON r.run_id = %s AND r.case_id = m.case_id"
            " WHERE m.case_id = %s AND m.version = %s"
            " AND s.case_id = %s AND s.sha256 = %s AND b.block_id = %s",
            (
                run_id,
                request.case_id.value,
                request.source_set_version,
                request.case_id.value,
                digest,
                request.block_id,
            ),
        ).fetchone()
        if found is None:
            raise Refusal(RefusalCode.EVIDENCE_NOT_DELIVERABLE)
        source_id, block_id, page, text = found
        store.execute(
            "INSERT INTO delivered_evidence (run_id, node_id, source_id, block_id)"
            " VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
            (run_id, request.node_id.value, source_id, block_id),
        )
    return Block(block_id=block_id, page=page, text=text)
