"""The vendored Deploy V bundle, verified on the bytes at use (invariant 4).

`tests/test_bundle_pin.py` checks the vendored copy at rest. This is the other
half: nothing reads a bundle file except through `Bundle.read`, which hashes what
it just read against the manifest and refuses a difference. `build_id` is read
from the manifest whose bytes this module pins, so it is the build's own and not
a claim -- but no run records it yet, so nothing is refused for running under the
wrong build. See the known-gaps ledger.

`DEPLOY_V_INTEGRITY_v1.json` is the one vendored file no manifest entry covers --
it *is* the manifest -- so `MANIFEST_SHA256` is the only thing standing behind
it. What that buys is bounded: it refuses a partial edit, a bad merge and a
corrupt checkout. It does not refuse an author with commit rights, who edits this
constant and `vendor/` in the same commit.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from server.refusals import Refusal, RefusalCode

BUNDLE_ROOT = Path(__file__).resolve().parents[1] / "vendor" / "deploy-v"
MANIFEST_NAME = "DEPLOY_V_INTEGRITY_v1.json"
MANIFEST_SHA256 = "2fc17570822e33365722dbbab8c408babba1d3d3de0a267ab47009436eae2823"

# No-follow, so a symlink swapped in for an authority file is refused rather
# than read through (SYSTEM_SPEC.md 3).
_FLAGS = os.O_RDONLY | os.O_NOFOLLOW


@dataclass(frozen=True, slots=True)
class Bundle:
    """One verified view of the bundle: what it is, and what its bytes are."""

    root: Path
    build_id: str
    digests: Mapping[str, str]  # bundle-relative path -> sha256
    folders: Mapping[str, str]  # module id -> skill folder slug
    aliases: Mapping[str, str]  # superseded module id -> live module id

    def read(self, relative: str) -> str:
        """The pinned text at `relative`, or a refusal.

        `digests` is the allowlist as well as the expectation: a path the
        manifest does not cover is not authority and is never opened.
        """
        expected = self.digests.get(relative)
        if expected is not None:
            raw = _read_no_follow(self.root / relative)
            if raw is not None and hashlib.sha256(raw).hexdigest() == expected:
                text = _decode(raw)
                if text is not None:
                    return text
        # Raised here and not in an `except`: an OSError or UnicodeDecodeError
        # still being handled attaches its path to this refusal as __context__,
        # which `from None` hides from the printer but not from the object.
        raise Refusal(RefusalCode.METHODOLOGY_AUTHORITY_MISMATCH)


def open_bundle(root: Path = BUNDLE_ROOT) -> Bundle:
    """Verify the manifest's own bytes, then read the expectations it carries."""
    raw = _read_no_follow(root / MANIFEST_NAME)
    if raw is None or hashlib.sha256(raw).hexdigest() != MANIFEST_SHA256:
        raise Refusal(RefusalCode.METHODOLOGY_BUNDLE_INVALID)

    # The bytes are the manifest this host pins, so the parse cannot fail and
    # the build id is that build's -- not a claim needing re-verification.
    manifest: dict[str, Any] = json.loads(raw)
    digests = {
        name: str(entry["sha256"])
        for name, entry in manifest["root_file_hashes"].items()
    }
    folders: dict[str, str] = {}
    aliases: dict[str, str] = {}
    for skill in manifest["skills"]:
        module_id, slug = str(skill["module_id"]), str(skill["folder_slug"])
        folders[module_id] = slug
        aliases.update({str(alias): module_id for alias in skill["aliases"]})
        digests.update(
            {
                f"skills/{slug}/{name}": str(entry["sha256"])
                for name, entry in skill["relative_file_hashes"].items()
            }
        )
    return Bundle(
        root=root,
        build_id=str(manifest["build_id"]),
        digests=digests,
        folders=folders,
        aliases=aliases,
    )


def _read_no_follow(path: Path) -> bytes | None:
    """The bytes, or None -- ELOOP for a symlink, ENOENT for a missing file.

    None rather than a refusal so the caller can raise clear of the handler:
    the OSError holds the path, and an exception raised while it is being
    handled carries it along.
    """
    try:
        with os.fdopen(os.open(path, _FLAGS), "rb") as opened:
            return opened.read()
    except OSError:
        return None


def _decode(raw: bytes) -> str | None:
    """Authority is text. Bytes that are not are not authority."""
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return None
