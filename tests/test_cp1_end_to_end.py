"""CP-1 end to end: authority in, a verified artifact out.

The Phase 5 exit test. Every piece the phase built meets here -- the bundle's
authority, the provider, the bundle's own envelope schema, and coordinate
anchoring bound to what the node was actually handed.

No live provider. `RecordedProvider` supplies the answer, because the question
these tests ask is what the host does with an answer, not what a model writes.
"""

from __future__ import annotations

import json
from dataclasses import replace
from decimal import Decimal

import pytest

from methodology.envelope import MAX_CITATIONS
from methodology.registry import assemble_authority
from server.boundary_text import BoundaryText
from server.engine.node import ModuleRequest, ModuleResult, execute_module
from server.evidence.citations import Citation
from server.provider import MODEL, Completion, RecordedProvider
from server.refusals import Refusal, RefusalCode
from server.store import Store
from server.store.blobs import BlobStore
from server.store.runs import start_run
from server.store.source_sets import pin_source_set
from server.store.sources import Block, SourceDocument, Token, admit_pack

CASE = BoundaryText.of("acme")
NODE = "RN-FULL_CREDIT_32-COVENANT_REFINANCING-02-CP-1"
DIGEST = "a" * 64
OTHER = "b" * 64
QUOTE = "net leverage was 4.2x"


def _tokens(text: str) -> tuple[Token, ...]:
    return tuple(
        Token(
            page=1,
            region_id=0,
            line_id=0,
            ordinal=n,
            text=word,
            x0=Decimal(n * 10),
            y0=Decimal(100),
            x1=Decimal(n * 10 + 9),
            y1=Decimal(110),
        )
        for n, word in enumerate(text.split())
    )


def _document(digest: str) -> SourceDocument:
    return SourceDocument(
        sha256=digest,
        tokens=_tokens(QUOTE),
        blocks=(Block(block_id=0, page=1, text=QUOTE),),
    )


def _envelope(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "module_id": "CP-1",
        "module_name": "CanonicalDataFoundation",
        "owned_object": "canonical_data_foundation",
        "schema_family": "Nested",
        "output_class": "CANONICAL_MARKDOWN",
        "runtime_output": {"tables": []},
        "evidence_trace": {
            "citations": [{"document_sha256": DIGEST, "page": 1, "matched_text": QUOTE}]
        },
        "confidence_score": 80,
        "confidence_band": "High",
        "limitation_flags": [],
        "qa_status": "Passed",
        "validation_warnings": [],
        "downstream_consumers": ["CP-2"],
    }
    payload.update(overrides)
    return payload


def _answering(payload: object) -> RecordedProvider:
    text = payload if isinstance(payload, str) else json.dumps(payload)
    return RecordedProvider(
        Completion(
            text=text,
            model=MODEL,
            input_tokens=40_000,
            output_tokens=2_000,
            request_id="req_x",
        )
    )


@pytest.fixture
def request_for(store: Store) -> ModuleRequest:
    admit_pack(store, case_id=CASE, documents=(_document(DIGEST), _document(OTHER)))
    admitted = [
        str(row[0])
        for row in store.execute(
            "SELECT source_id FROM sources ORDER BY sha256"
        ).fetchall()
    ]
    version = pin_source_set(store, case_id=CASE, source_ids=tuple(admitted))
    return ModuleRequest(
        run_id=start_run(store, case_id=CASE, ceiling=Decimal("100")),
        route_node_id=NODE,
        module_id="CP-1",
        case_id=CASE,
        source_set_version=version,
        evidence=((DIGEST, 0),),
    )


def _stored(blobs: BlobStore) -> int:
    """Blobs actually written. `.partial` files are a failed write, not a blob."""
    return len(
        [p for p in blobs.root.rglob("*") if p.is_file() and p.suffix != ".partial"]
    )


def test_cp1_produces_canonical_envelope_with_anchored_citations(
    store: Store, request_for: ModuleRequest, blobs: BlobStore
) -> None:
    """The Phase 5 exit test."""
    provider = _answering(_envelope())
    result: ModuleResult = execute_module(
        store, request=request_for, provider=provider, blobs=blobs
    )

    # The artifact is the envelope, canonically, and it is retrievable.
    stored = json.loads(blobs.get(result.artifact_sha256))
    assert stored["module_id"] == "CP-1"

    # Every quote carries coordinates the host derived, not ones it was given.
    assert len(result.citations) == 1
    anchored: Citation = result.citations[0]
    assert anchored.document_sha256 == DIGEST
    assert anchored.page == 1
    assert anchored.matched_text == QUOTE
    assert anchored.bboxes, "a citation with no rectangle anchors nothing"

    # The charge is what the provider reported using, not a flat guess.
    assert result.charge == Decimal("0.25")

    # CP-1's authority reached the model, and the evidence with it.
    call = provider.calls[0]
    assert "CP-1" in call.system
    assert QUOTE in call.prompt
    # Every authority file reaches the model -- including the shared canon,
    # without which SKILL.md's instruction to open it cannot be followed.
    authority = assemble_authority("CP-1")
    assert [name for name, _ in authority.files][-1] == "CANON_SHARED.md"
    assert all(text in call.system for _, text in authority.files)


def test_an_envelope_with_an_undeclared_field_is_refused(
    store: Store, request_for: ModuleRequest, blobs: BlobStore
) -> None:
    """Invariant 9. `additionalProperties: false` is the bundle's own rule."""
    with pytest.raises(Refusal) as refused:
        execute_module(
            store,
            request=request_for,
            provider=_answering(_envelope(smuggled="value")),
            blobs=blobs,
        )
    assert refused.value.code is RefusalCode.ENVELOPE_INVALID


@pytest.mark.parametrize(
    "broken",
    [
        {"qa_status": "Excellent"},
        {"confidence_score": 101},
        {"output_class": "MARKDOWN"},
        {"confidence_band": ""},
        {"module_name": ""},
    ],
)
def test_an_envelope_outside_the_bundles_schema_is_refused(
    store: Store,
    request_for: ModuleRequest,
    blobs: BlobStore,
    broken: dict[str, object],
) -> None:
    with pytest.raises(Refusal) as refused:
        execute_module(
            store,
            request=request_for,
            provider=_answering(_envelope(**broken)),
            blobs=blobs,
        )
    assert refused.value.code is RefusalCode.ENVELOPE_INVALID


def test_a_missing_required_field_is_refused(
    store: Store, request_for: ModuleRequest, blobs: BlobStore
) -> None:
    payload = _envelope()
    del payload["qa_status"]
    with pytest.raises(Refusal) as refused:
        execute_module(
            store, request=request_for, provider=_answering(payload), blobs=blobs
        )
    assert refused.value.code is RefusalCode.ENVELOPE_INVALID


def test_output_that_is_not_json_is_refused_without_quoting_it(
    store: Store, request_for: ModuleRequest, blobs: BlobStore
) -> None:
    prose = "I could not comply. The issuer's leverage is confidential."
    with pytest.raises(Refusal) as refused:
        execute_module(
            store, request=request_for, provider=_answering(prose), blobs=blobs
        )
    assert refused.value.code is RefusalCode.ENVELOPE_INVALID
    assert "confidential" not in " ".join(str(a) for a in refused.value.args)


def test_a_module_cannot_claim_to_be_another_module(
    store: Store, request_for: ModuleRequest, blobs: BlobStore
) -> None:
    """Provider-claimed identity never survives (invariant 3)."""
    with pytest.raises(Refusal) as refused:
        execute_module(
            store,
            request=request_for,
            provider=_answering(_envelope(module_id="CP-2")),
            blobs=blobs,
        )
    assert refused.value.code is RefusalCode.ENVELOPE_INVALID


def test_a_citation_of_evidence_never_delivered_is_refused(
    store: Store, request_for: ModuleRequest, blobs: BlobStore
) -> None:
    """The half of invariant 9 the delivered ledger existed for and nothing read.

    The other document is in the same case and the same pinned set, and its
    text contains the quote -- so anchoring alone would happily locate it. Only
    the delivered ledger says this node was never handed it.
    """
    citing_other = _envelope(
        evidence_trace={
            "citations": [{"document_sha256": OTHER, "page": 1, "matched_text": QUOTE}]
        }
    )
    with pytest.raises(Refusal) as refused:
        execute_module(
            store, request=request_for, provider=_answering(citing_other), blobs=blobs
        )
    assert refused.value.code is RefusalCode.CITATION_NOT_DELIVERED


def test_a_quote_the_document_does_not_carry_stops_the_artifact(
    store: Store, request_for: ModuleRequest, blobs: BlobStore
) -> None:
    invented = _envelope(
        evidence_trace={
            "citations": [
                {
                    "document_sha256": DIGEST,
                    "page": 1,
                    "matched_text": "net leverage was 9.9x",
                }
            ]
        }
    )
    with pytest.raises(Refusal) as refused:
        execute_module(
            store, request=request_for, provider=_answering(invented), blobs=blobs
        )
    assert refused.value.code is RefusalCode.CITATION_NOT_LOCATABLE


def test_a_module_may_not_supply_its_own_rectangles(
    store: Store, request_for: ModuleRequest, blobs: BlobStore
) -> None:
    """Invariant 3: where a quote sits is the host's derivation, not a claim."""
    with_boxes = _envelope(
        evidence_trace={
            "citations": [
                {
                    "document_sha256": DIGEST,
                    "page": 1,
                    "matched_text": QUOTE,
                    "bboxes": [[0, 0, 1, 1]],
                }
            ]
        }
    )
    with pytest.raises(Refusal) as refused:
        execute_module(
            store, request=request_for, provider=_answering(with_boxes), blobs=blobs
        )
    assert refused.value.code is RefusalCode.ENVELOPE_INVALID


def test_a_refused_envelope_writes_no_artifact(
    store: Store, request_for: ModuleRequest, blobs: BlobStore
) -> None:
    """A module that cannot support its claims leaves nothing behind.

    Counted in the blob store, which is what `execute_module` writes -- the
    earlier version counted `artifacts`, a table this code never touches, so it
    could not fail whatever the code did.
    """
    assert _stored(blobs) == 0
    with pytest.raises(Refusal):
        execute_module(
            store,
            request=request_for,
            provider=_answering(_envelope(smuggled="x")),
            blobs=blobs,
        )
    assert _stored(blobs) == 0, "a refused envelope reached the blob store"

    execute_module(
        store, request=request_for, provider=_answering(_envelope()), blobs=blobs
    )
    assert _stored(blobs) == 1, "the accepted envelope did not reach it either"


def test_a_non_finite_number_never_reaches_the_artifact(
    store: Store, request_for: ModuleRequest, blobs: BlobStore
) -> None:
    """Invariant 7: refused before use, not stored and regretted.

    `runtime_output` is typed only as an object, so the schema looks no further.
    `1e999` parses to inf and re-serialises as the literal `Infinity`, which no
    strict JSON reader accepts -- an artifact corrupt for every consumer that is
    not Python.
    """
    for literal in ("1e999", "-1e999", "NaN", "Infinity"):
        text = (
            json.dumps(_envelope())[:-1]
            + ', "runtime_output": {"ratio": '
            + literal
            + "}}"
        )
        with pytest.raises(Refusal) as refused:
            execute_module(
                store, request=request_for, provider=_answering(text), blobs=blobs
            )
        assert refused.value.code is RefusalCode.ENVELOPE_INVALID, literal
    assert _stored(blobs) == 0


def test_a_superseded_module_id_is_named_as_its_live_owner(
    store: Store, request_for: ModuleRequest, blobs: BlobStore
) -> None:
    """CP-2C assembles CP-1A's methodology, so the artifact says CP-1A.

    Running one module's methodology under another module's name is what
    invariant 3 forbids, and the base schema's enum accepts both spellings --
    so only the host can tell them apart.
    """
    aliased = replace(request_for, module_id="CP-2C")
    provider = _answering(_envelope(module_id="CP-1A", module_name="FactPack"))
    result = execute_module(store, request=aliased, provider=provider, blobs=blobs)
    assert json.loads(blobs.get(result.artifact_sha256))["module_id"] == "CP-1A"
    assert "CP-1A" in provider.calls[0].prompt

    with pytest.raises(Refusal) as refused:
        execute_module(
            store,
            request=aliased,
            provider=_answering(_envelope(module_id="CP-2C")),
            blobs=blobs,
        )
    assert refused.value.code is RefusalCode.ENVELOPE_INVALID


def test_more_citations_than_the_ceiling_are_refused(
    store: Store, request_for: ModuleRequest, blobs: BlobStore
) -> None:
    """Every claim costs two store reads to anchor (invariant 8)."""
    flood = _envelope(
        evidence_trace={
            "citations": [
                {"document_sha256": DIGEST, "page": 1, "matched_text": QUOTE}
                for _ in range(MAX_CITATIONS + 1)
            ]
        }
    )
    with pytest.raises(Refusal) as refused:
        execute_module(
            store, request=request_for, provider=_answering(flood), blobs=blobs
        )
    assert refused.value.code is RefusalCode.ENVELOPE_INVALID


def test_the_same_envelope_stores_at_the_same_digest(
    store: Store, request_for: ModuleRequest, blobs: BlobStore
) -> None:
    """Replay (invariant 10): the artifact's bytes are canonical."""
    first = execute_module(
        store, request=request_for, provider=_answering(_envelope()), blobs=blobs
    )
    again = execute_module(
        store,
        request=replace(request_for, run_id=start_run(store, case_id=CASE)),
        provider=_answering(_envelope()),
        blobs=blobs,
    )
    assert first.artifact_sha256 == again.artifact_sha256
