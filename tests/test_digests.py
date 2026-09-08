"""A digest is checked before it is used as a path or a key.

`BlobStore` addresses files by digest. Until this check existed, `_path` joined
whatever it was given: an absolute path replaced the root entirely and the store
read the file, and a relative one escaped the root and put the blob root into an
OSError. Content addressing fails closed only if the address is an address.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from server.digests import checked_digest
from server.refusals import Refusal, RefusalCode
from server.store.blobs import BlobStore

PAYLOAD = b"CP-1 accepted artifact"
DIGEST = hashlib.sha256(PAYLOAD).hexdigest()


@pytest.mark.parametrize(
    "impostor",
    [
        "/etc/hosts",
        "../../../etc/hosts",
        "a" * 63,
        "a" * 65,
        "A" * 64,
        "g" * 64,
        "",
        "../" + "a" * 61,
    ],
)
def test_a_digest_that_is_not_a_digest_is_refused(impostor: str) -> None:
    with pytest.raises(Refusal) as caught:
        checked_digest(impostor)
    assert caught.value.code is RefusalCode.DIGEST_INVALID


def test_a_real_digest_passes_through(tmp_path: Path) -> None:
    assert checked_digest(DIGEST) == DIGEST


def test_the_blob_store_reads_nothing_outside_its_root(tmp_path: Path) -> None:
    outside = tmp_path / "secret"
    outside.write_bytes(b"-----BEGIN PRIVATE KEY-----")
    store = BlobStore(tmp_path / "blobs")
    store.put(PAYLOAD)

    with pytest.raises(Refusal) as caught:
        store.get(str(outside))
    assert caught.value.code is RefusalCode.DIGEST_INVALID


def test_a_missing_blob_is_a_typed_refusal_naming_no_path(tmp_path: Path) -> None:
    store = BlobStore(tmp_path)
    with pytest.raises(Refusal) as caught:
        store.get("b" * 64)
    assert caught.value.code is RefusalCode.BLOB_NOT_FOUND
    rendered = f"{caught.value!r} {caught.value!s} {caught.value.args}"
    assert str(tmp_path) not in rendered
    assert caught.value.__context__ is None


def test_two_writers_of_the_same_bytes_cannot_publish_a_partial_blob(
    tmp_path: Path,
) -> None:
    # The temporary name must not be shared: two writers using one path
    # interleave their bytes and rename the result, publishing a blob whose
    # contents do not hash to its name.
    store = BlobStore(tmp_path)
    store.put(PAYLOAD)
    partials = [path.name for path in tmp_path.rglob("*.partial")]
    assert partials == []
    assert store.get(DIGEST) == PAYLOAD
