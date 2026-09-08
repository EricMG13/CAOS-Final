"""Typed refusals. The code travels; the offending text never does.

Error handling is ~2x worse in agent-written code (docs/AI_CODE_QUALITY.md
section 1) and the failure is always the same shape: an exception string
carrying a document's contents, a vendor's name or a filesystem path into a log
line or an HTTP body. A Refusal carries a code from a closed set and nothing
else, so there is no string to leak.
"""

from __future__ import annotations

from enum import StrEnum


class RefusalCode(StrEnum):
    """Every reason the host declines. Public-safe by construction."""

    BOUNDARY_TEXT_INVALID = "BOUNDARY_TEXT_INVALID"
    BOUNDARY_TEXT_TOO_LONG = "BOUNDARY_TEXT_TOO_LONG"
    BLOB_DIGEST_MISMATCH = "BLOB_DIGEST_MISMATCH"
    RUN_NOT_FOUND = "RUN_NOT_FOUND"
    RUN_NOT_RUNNING = "RUN_NOT_RUNNING"


class Refusal(Exception):
    """A declined operation. Its only payload is the code."""

    def __init__(self, code: RefusalCode) -> None:
        super().__init__(code.value)
        self.code = code

    def __repr__(self) -> str:
        return f"Refusal({self.code.value})"
