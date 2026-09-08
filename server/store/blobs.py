"""Bytes keyed by their own digest.

The database holds the digest, never the bytes (SYSTEM_SPEC section 2). Content
addressing buys two things this system needs: writing the same bytes twice is
one blob, so a replayed commit is harmless; and a read can check the name
against the contents, so tampering is caught rather than served.
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from pathlib import Path

from server.digests import checked_digest
from server.refusals import Refusal, RefusalCode


@dataclass(frozen=True, slots=True)
class BlobStore:
    """A content-addressed store rooted at a directory."""

    root: Path

    def put(self, payload: bytes) -> str:
        """Store bytes and return their digest. Storing them again changes nothing."""
        digest = hashlib.sha256(payload).hexdigest()
        blob = self._path(digest)
        if not blob.exists():
            blob.parent.mkdir(parents=True, exist_ok=True)
            # Write then rename: a reader never sees a half-written blob. The
            # temporary name is unique, so two writers of the same bytes cannot
            # interleave into one file and publish it under a digest it no
            # longer matches.
            partial = blob.with_name(f"{digest}.{uuid.uuid4().hex}.partial")
            partial.write_bytes(payload)
            partial.replace(blob)
        return digest

    def get(self, digest: str) -> bytes:
        """Return the bytes, or refuse: unknown, not a digest, or not matching."""
        blob = self._path(checked_digest(digest))
        try:
            payload = blob.read_bytes()
        except FileNotFoundError:
            missing = True
        else:
            missing = False
        # Raised outside the handler: an OSError carries the path in .filename
        # and would ride along as __context__.
        if missing:
            raise Refusal(RefusalCode.BLOB_NOT_FOUND)
        if hashlib.sha256(payload).hexdigest() != digest:
            raise Refusal(RefusalCode.BLOB_DIGEST_MISMATCH)
        return payload

    def _path(self, digest: str) -> Path:
        # Two-character fanout: one directory per 256 blobs, not one per million.
        return self.root / digest[:2] / digest
