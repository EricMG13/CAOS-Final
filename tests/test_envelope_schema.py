"""The envelope is the bundle's schema, not a copy of it (invariant 9).

`CP_MODULE_PAYLOAD_BASE.schema.txt` already carries the required list, the
closed enums and `additionalProperties: false`. Validating against a
hand-written model would be a second declaration, free to drift from the
authority it paraphrases -- and it is the drift, not the schema, that admits an
undeclared field.
"""

from __future__ import annotations

import pytest

from methodology.bundle import open_bundle
from methodology.envelope import claimed_citations, envelope_schema, parse_envelope
from server.refusals import Refusal, RefusalCode

VALID = {
    "module_id": "CP-1",
    "module_name": "CanonicalDataFoundation",
    "owned_object": "canonical_data_foundation",
    "schema_family": "Nested",
    "output_class": "CANONICAL_MARKDOWN",
    "runtime_output": {},
    "evidence_trace": {},
    "confidence_score": 80,
    "confidence_band": "High",
    "limitation_flags": [],
    "qa_status": "Passed",
    "validation_warnings": [],
    "downstream_consumers": [],
}


def test_the_schema_is_the_bundles_and_closes_the_object() -> None:
    schema = envelope_schema(open_bundle())
    assert schema["additionalProperties"] is False
    assert "qa_status" in schema["required"]
    assert schema["properties"]["output_class"]["const"] == "CANONICAL_MARKDOWN"


def test_a_valid_envelope_round_trips() -> None:
    import json

    assert parse_envelope(open_bundle(), json.dumps(VALID))["module_id"] == "CP-1"


@pytest.mark.parametrize(
    "text",
    ["", "null", "[]", '"a string"', "{", "not json at all", '{"module_id": "CP-1"}'],
)
def test_anything_that_is_not_an_envelope_is_refused(text: str) -> None:
    with pytest.raises(Refusal) as refused:
        parse_envelope(open_bundle(), text)
    assert refused.value.code is RefusalCode.ENVELOPE_INVALID


def test_a_pathologically_nested_answer_is_refused_not_crashed() -> None:
    # `json.loads` raises RecursionError, not ValueError, past its depth --
    # a RuntimeError nothing here caught, so a module answering with a
    # hundred-thousand-deep list crashed the node with a traceback instead of
    # the typed refusal this function promises. Depth is the one shape
    # `_bounded` never counted.
    deep = "[" * 300_000 + "]" * 300_000
    with pytest.raises(Refusal) as refused:
        parse_envelope(open_bundle(), deep)
    assert refused.value.code is RefusalCode.ENVELOPE_INVALID
    assert refused.value.__context__ is None


def test_an_exact_large_integer_is_finite() -> None:
    # Invariant 7 refuses non-finite values. A 400-digit integer is finite and
    # exact; casting every integer literal through float() to find out
    # overflowed it to inf and refused a valid envelope wholesale.
    import json

    huge = 10**400
    payload = json.dumps({**VALID, "runtime_output": {"n": huge}})
    assert parse_envelope(open_bundle(), payload)["runtime_output"]["n"] == huge


def test_a_malformed_bundle_schema_refuses_with_no_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # `raise ... from None` inside the handler suppresses the context for the
    # printer and leaves __context__ populated for anyone who reads it -- the
    # jsonschema SchemaError, whose message quotes the schema. Every other
    # refusal here raises clear of the handler; this one now does too.
    import json

    import methodology.envelope as envelope

    monkeypatch.setattr(envelope, "envelope_schema", lambda bundle: {"type": 12})
    with pytest.raises(Refusal) as refused:
        parse_envelope(open_bundle(), json.dumps(VALID))
    assert refused.value.code is RefusalCode.METHODOLOGY_BUNDLE_INVALID
    assert refused.value.__context__ is None


@pytest.mark.parametrize(
    "trace",
    [
        "not an object",
        {"citations": "not a list"},
        {"citations": [{"document_sha256": "a" * 64, "page": 1}]},
        {
            "citations": [
                {"document_sha256": "a" * 64, "page": True, "matched_text": "x"}
            ]
        },
        {"citations": [{"document_sha256": "a" * 64, "page": 1, "matched_text": 7}]},
        {
            "citations": [
                {
                    "document_sha256": "a" * 64,
                    "page": 1,
                    "matched_text": "x",
                    "bboxes": [],
                }
            ]
        },
    ],
)
def test_a_malformed_citation_claim_never_reaches_the_token_index(
    trace: object,
) -> None:
    """Shape first: a claim the host cannot read is refused before it is looked up."""
    with pytest.raises(Refusal) as refused:
        claimed_citations({**VALID, "evidence_trace": trace})
    assert refused.value.code is RefusalCode.ENVELOPE_INVALID


def test_an_envelope_with_no_citations_claims_none() -> None:
    assert claimed_citations(VALID) == []
