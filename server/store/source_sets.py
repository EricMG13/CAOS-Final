"""Pinning an immutable, versioned set of a case's sources.

Split from `sources.py`, which admits documents. The two share only the store
and a refusal code: admission is ingestion's, and pinning is the plan gate's.
They change for different reasons and at different phases.

Version allocation takes the case row lock before reading the current version,
so two pins cannot allocate the same one (`SYSTEM_SPEC.md` §5).
"""

from __future__ import annotations

from psycopg import errors

from server.boundary_text import BoundaryText
from server.digests import checked_uuid
from server.refusals import Refusal, RefusalCode
from server.store import Store
from server.store.sources import code_for


def pin_source_set(
    store: Store, *, case_id: BoundaryText, source_ids: tuple[str, ...]
) -> int:
    """Pin an immutable, versioned set of this case's sources; return its version.

    A set is a set: naming a source twice pins it once. Naming none is refused --
    a run pinned to no evidence is a mistake worth making early.
    """
    members = tuple(
        dict.fromkeys(
            checked_uuid(source_id, refusal=RefusalCode.SOURCE_NOT_IN_CASE)
            for source_id in source_ids
        )
    )
    if not members:
        raise Refusal(RefusalCode.SOURCE_SET_EMPTY)
    try:
        return _pin(store, case_id=case_id, members=members)
    except errors.IntegrityError as violation:
        code = code_for(violation.diag.constraint_name)
    raise Refusal(code)


def _pin(store: Store, *, case_id: BoundaryText, members: tuple[str, ...]) -> int:
    with store.transaction():
        # The case row lock is taken before the current version is read, so two
        # pins cannot allocate the same one.
        store.execute(
            "SELECT case_id FROM cases WHERE case_id = %s FOR UPDATE",
            (case_id.value,),
        )
        # count(column) skips NULLs, so the second number is how many are withdrawn.
        mine = store.execute(
            "SELECT count(*), count(withdrawn_at) FROM sources"
            " WHERE case_id = %s AND source_id = ANY(%s)",
            (case_id.value, list(members)),
        ).fetchone()
        if mine is None or mine[0] != len(members):
            raise Refusal(RefusalCode.SOURCE_NOT_IN_CASE)
        if mine[1]:
            # Pinning is a use (invariant 1): a set naming a withdrawn source is
            # one the run could never read in full, refused here rather than one
            # read at a time later. A person is pinning, so this may say why; a
            # module reading is told only that it was not given the block.
            raise Refusal(RefusalCode.SOURCE_WITHDRAWN)
        allocated = store.execute(
            "INSERT INTO source_sets (case_id, version)"
            " SELECT %s, coalesce(max(version), 0) + 1 FROM source_sets"
            " WHERE case_id = %s RETURNING version",
            (case_id.value, case_id.value),
        ).fetchone()
        if allocated is None:  # pragma: no cover - RETURNING always yields a row
            raise Refusal(RefusalCode.SOURCE_NOT_IN_CASE)
        version = int(allocated[0])
        with store.cursor() as cursor:
            cursor.executemany(
                "INSERT INTO source_set_members (case_id, version, source_id)"
                " VALUES (%s, %s, %s)",
                [(case_id.value, version, source_id) for source_id in members],
            )
    return version


def pinned_evidence(
    store: Store, *, case_id: BoundaryText, source_set_version: int
) -> tuple[tuple[str, int], ...]:
    """Every block of every source in a pinned set, as `(document_sha256, block_id)`.

    What a node is handed. Every block, because `source_mode` -- the registry
    field that would narrow it -- is one nothing reads yet (CLAUDE.md, Phase 5).
    Ordered, so two machines assemble the same prompt from the same set: the
    order a join returns rows in is not something a reservation or a digest may
    depend on. Coordinates only -- the text is `read_evidence`'s to deliver,
    and to refuse. Read through `live_sources`: a withdrawn source's blocks are
    reads the node would make and the host would refuse, one by one.
    """
    rows = store.execute(
        "SELECT s.sha256, b.block_id FROM source_set_members m"
        " JOIN live_sources s ON s.source_id = m.source_id AND s.case_id = m.case_id"
        " JOIN source_blocks b ON b.source_id = m.source_id"
        " WHERE m.case_id = %s AND m.version = %s"
        " ORDER BY s.sha256, b.block_id",
        (case_id.value, source_set_version),
    ).fetchall()
    return tuple((str(digest), int(block_id)) for digest, block_id in rows)
