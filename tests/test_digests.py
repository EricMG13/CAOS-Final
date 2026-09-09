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

from server.digests import checked_digest, checked_uuid
from server.refusals import Refusal, RefusalCode
from server.store.blobs import BlobStore

PAYLOAD = b"CP-1 accepted artifact"
DIGEST = hashlib.sha256(PAYLOAD).hexdigest()
ID = "0f4b6c1e-2d3a-4e5f-8a9b-0c1d2e3f4a5b"


@pytest.mark.parametrize(
    "spelling",
    [
        ID,
        ID.upper(),
        "{" + ID + "}",
        "urn:uuid:" + ID,
        ID.replace("-", ""),
    ],
)
def test_a_uuid_comes_back_in_the_store_s_spelling(spelling: str) -> None:
    # Python's parser is looser than PostgreSQL's: braces, `urn:uuid:` and
    # missing hyphens all parse here and not all of them parse there. The
    # check hands back the one spelling both accept, so it and the query agree.
    assert checked_uuid(spelling, refusal=RefusalCode.RUN_NOT_FOUND) == ID


@pytest.mark.parametrize("impostor", ["", "not-a-uuid", ID[:-1], ID + "0", "0" * 31])
def test_a_uuid_that_is_not_one_is_refused_with_the_caller_s_code(
    impostor: str,
) -> None:
    with pytest.raises(Refusal) as caught:
        checked_uuid(impostor, refusal=RefusalCode.SOURCE_NOT_IN_CASE)
    assert caught.value.code is RefusalCode.SOURCE_NOT_IN_CASE
    assert caught.value.__context__ is None, "the parser's own error is not attached"


@pytest.mark.parametrize("impostor", [None, 42, b"0f4b6c1e"])
def test_a_uuid_check_refuses_what_is_not_even_text(impostor: object) -> None:
    # A boundary that fails closed on the wrong string has to fail closed on
    # the wrong type too: `uuid.UUID(None)` is a TypeError, not a ValueError.
    with pytest.raises(Refusal) as caught:
        checked_uuid(impostor, refusal=RefusalCode.RUN_NOT_FOUND)  # type: ignore[arg-type]
    assert caught.value.code is RefusalCode.RUN_NOT_FOUND
    assert caught.value.__context__ is None


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
