"""The blob store: bytes keyed by their own digest.

SYSTEM_SPEC section 2 — the database holds the digest, never the bytes. Content
addressing is what makes a replayed write harmless and a tampered read
detectable, so both are asserted here rather than assumed.
"""

from __future__ import annotations

import hashlib
import threading
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


def test_two_writers_of_the_same_bytes_do_not_share_a_temp_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Both writers pick a temp path before either has written. A path derived
    # from the digest alone is the same path for both: the second writer
    # truncates the file the first one is about to rename into place, and a
    # reader in that window gets a blob that does not hash to its name.
    store = BlobStore(tmp_path)
    chosen: list[Path] = []
    both_ready = threading.Barrier(2, timeout=10)
    write_bytes = Path.write_bytes

    def racing(self: Path, data: bytes) -> int:
        chosen.append(self)
        both_ready.wait()
        return write_bytes(self, data)

    monkeypatch.setattr(Path, "write_bytes", racing)
    writers = [threading.Thread(target=store.put, args=(PAYLOAD,)) for _ in range(2)]
    for writer in writers:
        writer.start()
    for writer in writers:
        writer.join(timeout=10)
        assert not writer.is_alive()

    assert len(chosen) == 2
    assert len(set(chosen)) == 2
    monkeypatch.undo()
    assert store.get(DIGEST) == PAYLOAD


def test_a_write_that_fails_leaves_no_partial_behind(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The temp name is unique per call, so a failure that leaves one behind
    # leaves one behind forever -- nothing ever reuses that name.
    store = BlobStore(tmp_path)

    def refusing(self: Path, target: Path) -> None:
        raise OSError

    monkeypatch.setattr(Path, "replace", refusing)
    with pytest.raises(OSError):
        store.put(PAYLOAD)

    monkeypatch.undo()
    assert list(tmp_path.rglob("*.partial")) == []
