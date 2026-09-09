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
    BUDGET_CEILING_EXCEEDED = "BUDGET_CEILING_EXCEEDED"
    CHARGE_EXCEEDS_RESERVATION = "CHARGE_EXCEEDS_RESERVATION"
    BLOB_NOT_FOUND = "BLOB_NOT_FOUND"
    CITATION_AMBIGUOUS = "CITATION_AMBIGUOUS"
    CITATION_NOT_LOCATABLE = "CITATION_NOT_LOCATABLE"
    DIGEST_INVALID = "DIGEST_INVALID"
    EVIDENCE_NOT_DELIVERABLE = "EVIDENCE_NOT_DELIVERABLE"
    EVIDENCE_REQUEST_INVALID = "EVIDENCE_REQUEST_INVALID"
    METHODOLOGY_AUTHORITY_MISMATCH = "METHODOLOGY_AUTHORITY_MISMATCH"
    METHODOLOGY_CALCULATION_FAILED = "METHODOLOGY_CALCULATION_FAILED"
    METHODOLOGY_CALCULATOR_UNKNOWN = "METHODOLOGY_CALCULATOR_UNKNOWN"
    METHODOLOGY_INPUT_INVALID = "METHODOLOGY_INPUT_INVALID"
    METHODOLOGY_BUNDLE_INVALID = "METHODOLOGY_BUNDLE_INVALID"
    METHODOLOGY_MODULE_UNKNOWN = "METHODOLOGY_MODULE_UNKNOWN"
    NODE_ALREADY_ACCEPTED = "NODE_ALREADY_ACCEPTED"
    PROVIDER_CALL_INVALID = "PROVIDER_CALL_INVALID"
    PROVIDER_REFUSED = "PROVIDER_REFUSED"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    ROUTE_ALREADY_PINNED = "ROUTE_ALREADY_PINNED"
    ROUTE_EXTENSION_INCOMPLETE = "ROUTE_EXTENSION_INCOMPLETE"
    ROUTE_NOT_PINNED = "ROUTE_NOT_PINNED"
    ROUTE_NOT_RESOLVABLE = "ROUTE_NOT_RESOLVABLE"
    RUN_NOT_FOUND = "RUN_NOT_FOUND"
    RUN_NOT_RUNNING = "RUN_NOT_RUNNING"
    SOURCE_ALREADY_ADMITTED = "SOURCE_ALREADY_ADMITTED"
    SOURCE_NOT_ADMISSIBLE = "SOURCE_NOT_ADMISSIBLE"
    SOURCE_NOT_IN_CASE = "SOURCE_NOT_IN_CASE"
    SOURCE_SET_EMPTY = "SOURCE_SET_EMPTY"
    # A token here is an extracted text run, not a credential.
    SOURCE_TOKEN_INDEX_INVALID = "SOURCE_TOKEN_INDEX_INVALID"  # nosec B105


class Refusal(Exception):
    """A declined operation. Its only payload is the code."""

    def __init__(self, code: RefusalCode) -> None:
        super().__init__(code.value)
        self.code = code

    def __repr__(self) -> str:
        return f"Refusal({self.code.value})"
