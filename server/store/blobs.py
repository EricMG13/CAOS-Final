"""Bytes keyed by their own digest.

The database holds the digest, never the bytes (SYSTEM_SPEC section 2). Content
addressing buys two things this system needs: writing the same bytes twice is
one blob, so a replayed commit is harmless; and a read can check the name
against the contents, so tampering is caught rather than served.
"""

from __future__ import annotations

import contextlib
import hashlib
import uuid
from dataclasses import dataclass
from pathlib import Path

from server.digests import checked_digest
from server.refusals import Refusal, RefusalCode


@dataclass(frozen=True, slots=True)
class BlobStore:
    """A content-addressed store rooted at a directory.

    Every OSError is caught and answered with a typed code, raised clear of the
    handler: an OSError carries the path in `.filename`, and the blob root is
    the one thing a refusal here must not name. Only `FileNotFoundError` was
    caught at first, so an unreadable blob escaped with it.
    """

    root: Path

    def put(self, payload: bytes) -> str:
        """Store bytes under their digest; the same bytes again change nothing.

        Written to a unique temporary name and renamed into place, so a reader
        never sees a half-written blob and two writers of the same bytes never
        share a file to truncate. Unique also means a failed write leaks a
        file rather than reusing one, so the partial is always removed -- in
        `finally`, so an interrupt leaves none behind either.
        """
        digest = hashlib.sha256(payload).hexdigest()
        blob = self._path(digest)
        if blob.exists():
            return digest
        partial = blob.with_name(f"{digest}.{uuid.uuid4().hex}.partial")
        failed = False
        try:
            blob.parent.mkdir(parents=True, exist_ok=True)
            partial.write_bytes(payload)
            partial.replace(blob)
        except OSError:
            failed = True
        finally:
            with contextlib.suppress(OSError):
                partial.unlink(missing_ok=True)
        if failed:
            raise Refusal(RefusalCode.BLOB_IO_FAILED)
        return digest

    def get(self, digest: str) -> bytes:
        """Return the bytes, or refuse: unknown, unreadable, no digest, no match."""
        blob = self._path(checked_digest(digest))
        failure: RefusalCode | None = None
        try:
            payload = blob.read_bytes()
        except FileNotFoundError:
            failure = RefusalCode.BLOB_NOT_FOUND
        except OSError:
            failure = RefusalCode.BLOB_IO_FAILED
        if failure is not None:
            raise Refusal(failure)
        if hashlib.sha256(payload).hexdigest() != digest:
            raise Refusal(RefusalCode.BLOB_DIGEST_MISMATCH)
        return payload

    def _path(self, digest: str) -> Path:
        # Two-character fanout: one directory per 256 blobs, not one per million.
        return self.root / digest[:2] / digest
