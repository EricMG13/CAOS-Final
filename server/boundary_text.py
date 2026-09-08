"""The type every string crossing into pinned state must be.

A bare `str` reaching pinned state, a revision, a frozen payload or an audit
event is a defect. NFC-normalised before the length bound, so what is measured
is what is stored; then refused if it carries a lone surrogate, a Cc control
other than CR/LF/TAB, or a bidirectional override or isolate.

The bidi controls are the reason the type exists rather than a length check:
U+202E makes an audit event render backwards while the bytes say something else,
so the sentence a human approves and the sentence the store holds differ.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass

from server.refusals import Refusal, RefusalCode

DEFAULT_LIMIT = 4096

# LRE, RLE, PDF, LRO, RLO (U+202A-U+202E), then the isolates LRI, RLI, FSI,
# PDI (U+2066-U+2069). Written as code points on purpose: a literal bidi
# control here would make this file itself render deceptively, which is the
# trojan-source class (CVE-2021-42574) this module exists to refuse.
_BIDI = frozenset(map(chr, [*range(0x202A, 0x202F), *range(0x2066, 0x206A)]))
_KEPT_CONTROLS = frozenset("\r\n\t")


def _is_refused(character: str) -> bool:
    if character in _KEPT_CONTROLS:
        return False
    return character in _BIDI or unicodedata.category(character) in {"Cc", "Cs"}


@dataclass(frozen=True, slots=True)
class BoundaryText:
    """Text that has passed the boundary. Construct it with `of`, never directly."""

    value: str

    @classmethod
    def of(cls, raw: str, *, limit: int = DEFAULT_LIMIT) -> BoundaryText:
        normalised = unicodedata.normalize("NFC", raw)
        if any(_is_refused(character) for character in normalised):
            raise Refusal(RefusalCode.BOUNDARY_TEXT_INVALID)
        if len(normalised) > limit:
            raise Refusal(RefusalCode.BOUNDARY_TEXT_TOO_LONG)
        return cls(normalised)
