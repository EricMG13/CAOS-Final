"""Who is asking (`docs/SYSTEM_SPEC.md` §8).

Development trusts a header the client sends. Production reads what the OIDC
edge -- the one reverse proxy §11 puts in front of this process -- asserted,
and never the development header: two pairs on purpose, so what production
trusts can never be what a client wrote (`docs/DECISIONS.md` §50).

Identity is who. What they may do on a case is standing, read where the
decision commits; the role §8 derives from groups arrives with the first write.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum

from server.boundary_text import BoundaryText
from server.refusals import Refusal


class Environment(StrEnum):
    """Which header pair the edge reads."""

    DEVELOPMENT = "development"
    PRODUCTION = "production"


@dataclass(frozen=True, slots=True)
class Identity:
    """The authenticated person: a member id and the groups asserted for them."""

    member_id: BoundaryText
    groups: frozenset[str]


# The (member, groups) pair each environment reads, and the only one it reads:
# development's is this host's own; production's is what an OIDC-authenticating
# proxy forwards, and one it must overwrite on every request it lets through.
_HEADERS = {
    Environment.DEVELOPMENT: ("x-caos-member", "x-caos-groups"),
    Environment.PRODUCTION: ("x-forwarded-user", "x-forwarded-groups"),
}
# A member id is a name, not a document: the general bound is sixteen times too
# generous for something that reaches the audit chain on every governed write.
_MEMBER_LIMIT = 256


def identify(
    headers: Iterable[tuple[str, str]], *, environment: Environment
) -> Identity | None:
    """The person a request is from, or None for nobody.

    `headers` is every (name, value) pair the request carried. A name that
    appears twice is read as absent: a proxy that appends its assertion behind
    a client's copy leaves both, the client's first, and a framework's `get`
    returns the first. A member id the boundary refuses is no identity rather
    than an error: the answer to an outsider is the same 404 either way.
    """
    once: dict[str, str | None] = {}  # a name's one value, or None for two
    for name, value in headers:
        key = name.lower()
        once[key] = None if key in once else value
    member_header, groups_header = _HEADERS[environment]
    member = _sent(once.get(member_header))
    if not member:
        return None
    try:
        member_id = BoundaryText.of(member, limit=_MEMBER_LIMIT)
    except Refusal:
        return None
    groups = (_sent(once.get(groups_header)) or "").split(",")
    return Identity(member_id, frozenset(filter(None, map(str.strip, groups))))


def _sent(value: str | None) -> str | None:
    """The bytes the client sent, read as UTF-8.

    A header is bytes on the wire and the framework hands them over decoded
    latin-1, so a name outside ASCII arrives as mojibake and would never match
    the one the store granted. Bytes that are not UTF-8 are nobody, like a name
    the boundary refuses: no identity rather than an error.
    """
    if not value:
        return None
    try:
        return value.encode("latin-1").decode("utf-8")
    except UnicodeError:
        return None


def environment_from(environ: Mapping[str, str]) -> Environment:
    """Unset is production: trusting a client header is opted into, never fallen into.

    Chosen by `CAOS_ENV`; a value that is neither is refused at startup.
    """
    return Environment(environ.get("CAOS_ENV", Environment.PRODUCTION))
