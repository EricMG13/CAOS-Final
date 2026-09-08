"""The blob store: bytes keyed by their own digest.

SYSTEM_SPEC section 2 — the database holds the digest, never the bytes. Content
addressing is what makes a replayed write harmless and a tampered read
detectable, so both are asserted here rather than assumed.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from server.refusals import Refusal, RefusalCode
from server.store.blobs import BlobStore

PAYLOAD = b"CP-1 accepted artifact"
DIGEST = hashlib.sha256(PAYLOAD).hexdigest()


def test_put_returns_the_digest_of_the_bytes(tmp_path: Path) -> None:
    assert BlobStore(tmp_path).put(PAYLOAD) == DIGEST


def test_get_returns_exactly_what_was_put(tmp_path: Path) -> None:
    store = BlobStore(tmp_path)
    assert store.get(store.put(PAYLOAD)) == PAYLOAD


def test_putting_the_same_bytes_twice_writes_one_blob(tmp_path: Path) -> None:
    store = BlobStore(tmp_path)
    assert store.put(PAYLOAD) == store.put(PAYLOAD)
    assert len(list(tmp_path.rglob("*"))) == len(list(tmp_path.rglob("*")))
    assert sum(1 for path in tmp_path.rglob("*") if path.is_file()) == 1


def test_a_tampered_blob_is_refused_on_read(tmp_path: Path) -> None:
    store = BlobStore(tmp_path)
    digest = store.put(PAYLOAD)
    blob = next(path for path in tmp_path.rglob("*") if path.is_file())
    blob.write_bytes(b"something else entirely")

    with pytest.raises(Refusal) as caught:
        store.get(digest)
    assert caught.value.code is RefusalCode.BLOB_DIGEST_MISMATCH
