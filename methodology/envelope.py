"""The strict canonical envelope (invariant 9).

The bundle already declares it: `CP_MODULE_PAYLOAD_BASE.schema.txt` carries the
required field list, the closed enums and `additionalProperties: false`. So the
host validates against *that*, read through `Bundle.read` and therefore
digest-checked at use -- not against a model hand-copied from it, which would be
a second declaration free to drift from the authority it paraphrases.

Where the base schema stops is `evidence_trace`, which it types only as an
object. Citations are the host's territory (invariant 11), so the shape inside
it is a host contract: `docs/DECISIONS.md` §29.
"""

from __future__ import annotations

import json
from typing import Any

import jsonschema

from methodology.bundle import Bundle
from server.refusals import Refusal, RefusalCode

BASE_SCHEMA = "CP_MODULE_PAYLOAD_BASE.schema.txt"

# `runtime_output` and `evidence_trace` are typed only as objects, so nothing in
# the schema looks inside them. A module writing 1e999 there parses to inf,
# validates cleanly, and re-serialises as the literal `Infinity` -- an artifact
# no strict JSON reader accepts. Invariant 7 refuses non-finite values before
# use, and this is the boundary they arrive at.
MAX_CITATIONS = 256

# Where a module puts the quotes it wants anchored. The base schema leaves
# `evidence_trace` open; this is the host's declaration of what it reads there.
CITATIONS = "citations"


def envelope_schema(bundle: Bundle) -> dict[str, Any]:
    """The bundle's own payload schema, verified on the bytes at use."""
    loaded: dict[str, Any] = json.loads(bundle.read(BASE_SCHEMA))
    return loaded


def parse_envelope(bundle: Bundle, text: str) -> dict[str, Any]:
    """A module's output as a validated envelope, or a typed refusal.

    Everything a module produced is untrusted text: a parse failure, a wrong
    type, a missing field and an undeclared one all end the same way, carrying
    no fragment of what was wrong with them.
    """
    try:
        parsed: object = json.loads(
            text, parse_float=_finite, parse_int=_finite, parse_constant=_refuse
        )
    except ValueError:
        parsed = None
    valid = False
    if isinstance(parsed, dict):
        try:
            jsonschema.validate(parsed, envelope_schema(bundle))
            valid = True
        except jsonschema.SchemaError:
            # The schema, not the module. A bundle whose own payload schema is
            # malformed is unexecutable, and saying ENVELOPE_INVALID would blame
            # whichever module happened to run first.
            raise Refusal(RefusalCode.METHODOLOGY_BUNDLE_INVALID) from None
        except jsonschema.ValidationError:
            valid = False
    if not isinstance(parsed, dict) or not valid:
        # Raised clear of the handler: a ValidationError quotes the offending
        # instance, which is module-authored text.
        raise Refusal(RefusalCode.ENVELOPE_INVALID)
    payload: dict[str, Any] = parsed
    return payload


def _finite(literal: str) -> float | int:
    """Reject a numeric literal that is not finite, before it becomes a value."""
    number = float(literal)
    if number != number or number in (float("inf"), float("-inf")):
        raise ValueError
    return int(literal) if literal.lstrip("-").isdigit() else number


def _refuse(literal: str) -> float:
    """`Infinity`, `-Infinity` and `NaN` are literals `json` accepts by default."""
    raise ValueError(literal)


def claimed_citations(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """The quotes a module asked to have anchored, checked for shape only.

    Whether they are true is `anchor_citation`'s question; whether they are
    even well-formed is this one, and a malformed claim never reaches the host's
    token index.
    """
    trace = payload.get("evidence_trace")
    if not isinstance(trace, dict):
        raise Refusal(RefusalCode.ENVELOPE_INVALID)
    claimed = trace.get(CITATIONS, [])
    if not isinstance(claimed, list) or len(claimed) > MAX_CITATIONS:
        # Every claim costs two store reads to anchor. Invariant 8: the ceiling
        # refuses before the work, not after it.
        raise Refusal(RefusalCode.ENVELOPE_INVALID)
    for claim in claimed:
        if not isinstance(claim, dict) or not _well_formed(claim):
            raise Refusal(RefusalCode.ENVELOPE_INVALID)
    return list(claimed)


def _well_formed(claim: dict[str, Any]) -> bool:
    """`{document_sha256, page, matched_text}` -- the host derives the rest.

    A module never supplies rectangles. Invariant 3: what it claims about where
    its quote sits is an expectation, and the host re-derives it.
    """
    return (
        isinstance(claim.get("document_sha256"), str)
        and isinstance(claim.get("page"), int)
        and not isinstance(claim.get("page"), bool)
        and isinstance(claim.get("matched_text"), str)
        and set(claim) == {"document_sha256", "page", "matched_text"}
    )
