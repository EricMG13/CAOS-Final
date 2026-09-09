"""Case membership: who may act on a case, and the standing they hold.

`docs/SYSTEM_SPEC.md` §8: case standing is rechecked at commit time, not only
at the request. The check therefore lives in the store call that commits a
human decision, and this module is what that call reads. The table holds the
current membership and nothing else -- a grant inserts or moves a row, a
revocation deletes it -- because the history of who changed it belongs to the
audit chain, not to a second copy here.

Standing is a case's own thing. It is not the global role §8 derives from an
OIDC group or a development header; that is an edge this repository does not
have yet, and nothing here stands in for it.
"""

from __future__ import annotations

from enum import StrEnum

from server.boundary_text import BoundaryText
from server.refusals import Refusal, RefusalCode
from server.store import Store


class Standing(StrEnum):
    """The four case standings `docs/SYSTEM_SPEC.md` §8 names, and no others."""

    READER = "READER"
    WRITER = "WRITER"
    APPROVER = "APPROVER"
    ADMIN = "ADMIN"


def grant_membership(
    store: Store, *, case_id: BoundaryText, member_id: BoundaryText, standing: Standing
) -> None:
    """Give a member this standing on the case, replacing whatever they held.

    Selecting the case rather than naming it is what refuses an unknown one by
    code: an insert against a missing case writes nothing instead of raising
    `case_members_case_id_fkey`. Membership does not mint a case.
    """
    with store.transaction():
        granted = store.execute(
            "INSERT INTO case_members (case_id, member_id, standing)"
            " SELECT case_id, %s, %s FROM cases WHERE case_id = %s"
            " ON CONFLICT (case_id, member_id) DO UPDATE"
            "    SET standing = EXCLUDED.standing, granted_at = now()",
            (member_id.value, standing.value, case_id.value),
        )
        if granted.rowcount == 0:
            raise Refusal(RefusalCode.CASE_NOT_FOUND)


def revoke_membership(
    store: Store, *, case_id: BoundaryText, member_id: BoundaryText
) -> bool:
    """Remove a member from the case. True when a membership was there to remove.

    Waits behind any release that is reading this row `FOR SHARE`, so the
    revocation lands before or after that decision and never inside it.
    """
    with store.transaction():
        revoked = store.execute(
            "DELETE FROM case_members WHERE case_id = %s AND member_id = %s",
            (case_id.value, member_id.value),
        )
    return revoked.rowcount == 1


def require_standing(
    store: Store, *, case_id: str, member_id: BoundaryText, allowed: frozenset[Standing]
) -> None:
    """Refuse unless the member holds one of the allowed standings on the case.

    Wants an open transaction, like `lock_run`: a row that qualifies is taken
    `FOR SHARE`, so a revocation or a change of standing waits until the
    transaction that read it has committed, and the lock goes when that
    transaction ends. Called outside one it checks and holds nothing.

    `case_id` is a `str` where every write path takes `BoundaryText`, because
    it is the store's own value -- read back by `lock_run` under the run row
    lock -- and never a caller's. The store decides which standings qualify,
    so no standing is decoded here: one refusal for a member without the
    standing and for no member at all.
    """
    found = store.execute(
        "SELECT 1 FROM case_members"
        " WHERE case_id = %s AND member_id = %s AND standing = ANY(%s) FOR SHARE",
        (case_id, member_id.value, [standing.value for standing in allowed]),
    ).fetchone()
    if found is None:
        raise Refusal(RefusalCode.STANDING_INSUFFICIENT)
