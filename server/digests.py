"""A digest, checked before it is used as a path or a key.

Content addressing only fails closed if the address is an address. `BlobStore`
joins a digest onto its root, and `pathlib` lets an absolute segment replace the
root outright -- so an unchecked digest is an arbitrary-file read, a disclosure
of the blob root through an OSError, and an existence oracle in the difference
between "missing" and "digest mismatch".
"""

from __future__ import annotations

import re

from server.refusals import Refusal, RefusalCode

# Lower-case hex, exactly 64 characters. Nothing else is a sha256.
_SHA256 = re.compile(r"[0-9a-f]{64}")


def checked_digest(value: str) -> str:
    """Return the digest, or refuse anything that is not one."""
    if _SHA256.fullmatch(value) is None:
        raise Refusal(RefusalCode.DIGEST_INVALID)
    return value
