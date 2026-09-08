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
            # temp name is unique per writer, not per digest -- two writers of
            # the same bytes would otherwise share one file, and the second
            # truncates what the first is renaming into place.
            partial = blob.with_name(f"{digest}.{uuid.uuid4().hex}.partial")
            try:
                partial.write_bytes(payload)
                partial.replace(blob)
            finally:
                partial.unlink(missing_ok=True)
        return digest

    def get(self, digest: str) -> bytes:
        """Return the bytes, or refuse if they no longer hash to their name."""
        payload = self._path(digest).read_bytes()
        if hashlib.sha256(payload).hexdigest() != digest:
            raise Refusal(RefusalCode.BLOB_DIGEST_MISMATCH)
        return payload

    def _path(self, digest: str) -> Path:
        # Two-character fanout: one directory per 256 blobs, not one per million.
        return self.root / digest[:2] / digest
