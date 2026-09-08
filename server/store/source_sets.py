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
    members = tuple(dict.fromkeys(source_ids))
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
        mine = store.execute(
            "SELECT count(*) FROM sources WHERE case_id = %s AND source_id = ANY(%s)",
            (case_id.value, list(members)),
        ).fetchone()
        if mine is None or mine[0] != len(members):
            raise Refusal(RefusalCode.SOURCE_NOT_IN_CASE)
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
