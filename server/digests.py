"""A digest or an id, checked before it is used as a path, a key or a parameter.

Content addressing only fails closed if the address is an address. `BlobStore`
joins a digest onto its root, and `pathlib` lets an absolute segment replace the
root outright -- so an unchecked digest is an arbitrary-file read, a disclosure
of the blob root through an OSError, and an existence oracle in the difference
between "missing" and "digest mismatch".

An id is the same idea one layer down: a run or source id that reaches the
driver in a spelling PostgreSQL does not parse comes back as the driver's own
complaint, naming the type and the vendor, where a refusal should be.
"""

from __future__ import annotations

import re
import uuid

from server.refusals import Refusal, RefusalCode

# Lower-case hex, exactly 64 characters. Nothing else is a sha256.
_SHA256 = re.compile(r"[0-9a-f]{64}")


def checked_digest(value: str) -> str:
    """Return the digest, or refuse anything that is not one."""
    if _SHA256.fullmatch(value) is None:
        raise Refusal(RefusalCode.DIGEST_INVALID)
    return value


def checked_uuid(value: str, *, refusal: RefusalCode) -> str:
    """Return the id in the store's own spelling, or refuse with the caller's code.

    `uuid.UUID` accepts braces, `urn:uuid:` and missing hyphens; PostgreSQL's
    parser accepts fewer. A value that passed as text here could still reach
    the driver as a spelling it names in its complaint, so the check hands
    back the one spelling both sides agree on.
    """
    try:
        parsed = uuid.UUID(value)
    except (AttributeError, TypeError, ValueError):
        # Not text at all is refused like the wrong text: None is a TypeError,
        # bytes an AttributeError, and neither may reach the driver either.
        parsed = None
    if parsed is None:
        raise Refusal(refusal)
    return str(parsed)
