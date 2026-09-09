"""Running one module node: authority in, a verified artifact out.

`SYSTEM_SPEC.md` §4 -- reserve, resolve the provider, execute, validate the
envelope, verify citations. Reservation and acceptance belong to the loop; this
is the part between them, and it either produces an artifact every claim of
which the host has re-derived, or it produces nothing.

The order matters. Nothing is written until every citation has been anchored,
so a module that quotes what it cannot support costs a reservation and leaves
no artifact -- rather than leaving a half-checked one behind.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from methodology.bundle import BUNDLE_ROOT, open_bundle
from methodology.envelope import claimed_citations, parse_envelope
from methodology.registry import assemble_authority
from server.boundary_text import BoundaryText
from server.evidence.citations import Citation, anchor_citation
from server.evidence.reads import EvidenceRequest, read_evidence
from server.provider import Provider, ProviderCall, price_of
from server.refusals import Refusal, RefusalCode
from server.store import Store
from server.store.blobs import BlobStore

# ponytail: one ceiling for every module until one needs its own. SYSTEM_SPEC 3
# lists `max_output_tokens` per ModuleSpec; no module differs yet.
MAX_OUTPUT_TOKENS = 16_000


@dataclass(frozen=True, slots=True)
class ModuleRequest:
    """One node's execution: who is running, over which pinned evidence."""

    run_id: str
    route_node_id: str
    module_id: str
    case_id: BoundaryText
    source_set_version: int
    evidence: tuple[tuple[str, int], ...]


@dataclass(frozen=True, slots=True)
class ModuleResult:
    """What a node produced, and what the host verified about it."""

    artifact_sha256: str
    charge: Decimal
    citations: tuple[Citation, ...]


def execute_module(
    store: Store,
    *,
    request: ModuleRequest,
    provider: Provider,
    blobs: BlobStore,
    root: Path = BUNDLE_ROOT,
) -> ModuleResult:
    """Assemble, ask, validate, anchor, store. Refusing at the first failure."""
    bundle = open_bundle(root)
    authority = assemble_authority(request.module_id, root=root)
    blocks = _deliver(store, request)
    answer = provider(
        ProviderCall(
            system="\n\n".join(text for _, text in authority.files),
            prompt=_prompt(request, blocks),
            max_output_tokens=MAX_OUTPUT_TOKENS,
        )
    )
    payload = parse_envelope(bundle, answer.text)
    _check_identity(request, payload)
    anchored = _anchor(store, request, claimed_citations(payload))
    return ModuleResult(
        artifact_sha256=blobs.put(_canonical(payload)),
        charge=price_of(answer),
        citations=anchored,
    )


def _deliver(store: Store, request: ModuleRequest) -> list[str]:
    """Every block this node was handed, recorded as handed by `read_evidence`."""
    return [
        read_evidence(
            store,
            EvidenceRequest(
                case_id=request.case_id,
                source_set_version=request.source_set_version,
                document_sha256=digest,
                block_id=block_id,
                run_id=request.run_id,
                node_id=BoundaryText.of(request.route_node_id),
            ),
        ).text
        for digest, block_id in request.evidence
    ]


def _prompt(request: ModuleRequest, blocks: list[str]) -> str:
    """The node's task and the evidence it may cite. Nothing else."""
    return "\n\n".join(
        [
            f"Run the {request.module_id} workflow over the evidence below.",
            "Return the canonical payload envelope as JSON and nothing else.",
            *(f"[{n}] {text}" for n, text in enumerate(blocks)),
        ]
    )


def _check_identity(request: ModuleRequest, payload: dict[str, object]) -> None:
    """Provider-claimed identity never survives (invariant 3)."""
    if payload.get("module_id") != request.module_id:
        raise Refusal(RefusalCode.ENVELOPE_INVALID)


def _delivered_digests(store: Store, request: ModuleRequest) -> set[str]:
    rows = store.execute(
        "SELECT s.sha256 FROM delivered_evidence d"
        " JOIN sources s ON s.source_id = d.source_id"
        " WHERE d.run_id = %s AND d.node_id = %s",
        (request.run_id, request.route_node_id),
    ).fetchall()
    return {str(row[0]) for row in rows}


def _anchor(
    store: Store, request: ModuleRequest, claims: list[dict[str, object]]
) -> tuple[Citation, ...]:
    """Re-locate every quote, and refuse one naming evidence never delivered.

    The delivered ledger was written and not read until here: without this a
    module could cite a document it was never handed, which is the half of
    invariant 9 that `read_evidence` alone does not close.
    """
    delivered = _delivered_digests(store, request)
    anchored = []
    for claim in claims:
        digest = str(claim["document_sha256"])
        if digest not in delivered:
            raise Refusal(RefusalCode.CITATION_NOT_DELIVERED)
        anchored.append(
            anchor_citation(
                store,
                case_id=request.case_id,
                document_sha256=digest,
                page=int(str(claim["page"])),
                matched_text=str(claim["matched_text"]),
            )
        )
    return tuple(anchored)


def _canonical(payload: dict[str, object]) -> bytes:
    """The artifact's bytes. Same envelope, same digest, on any machine."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
