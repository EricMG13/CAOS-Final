"""The loop meets `execute_module`, and charges what the provider reported.

Phase 6 owes this to Phase 4 (`docs/REBUILD_PLAN.md`): the loop reserved a flat
1.00 per node, and no loop ever called a module. Here the executor is the real
one, the provider is recorded, and the ledger records `price_of` each answer.

Two things a flat price could not say. The reservation is taken from the bytes
the node actually sends -- the same `ProviderCall` the provider receives -- so
there is one statement of what a call contains, not a pricing copy beside a
sending copy. And every node is handed every block of the pinned source set,
because `source_mode` is a registry field nothing reads yet (CLAUDE.md, Phase 5).
"""

from __future__ import annotations

import json
import uuid
from decimal import Decimal
from pathlib import Path

import psycopg
import pytest

from server.boundary_text import BoundaryText
from server.engine.loop import run_route
from server.engine.node import module_executor
from server.engine.route import resolve_route
from server.provider import MODEL, Completion, RecordedProvider, ceiling_of, price_of
from server.refusals import Refusal, RefusalCode
from server.store import Store
from server.store.blobs import BlobStore
from server.store.routes import pin_route
from server.store.runs import start_run
from server.store.source_sets import pin_source_set
from server.store.sources import Block, SourceDocument, Token, admit_pack

CATALOG = json.loads(
    (
        Path(__file__).resolve().parents[1]
        / "vendor/deploy-v/skills/cp-os-credit-os/references"
        / "CREDIT_OS_V_MODULE_CATALOG_v2.json"
    ).read_text(encoding="utf-8")
)
CASE = BoundaryText.of("acme")
# CP-0 -> CP-8: the smallest real pathway in the catalog.
FULL, LEDGER = "FULL_CREDIT_32", "DECISION_LEDGER"
DIGEST = "a" * 64
QUOTE = "net leverage was 4.2x"


def _document(digest: str) -> SourceDocument:
    tokens = tuple(
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
        for n, word in enumerate(QUOTE.split())
    )
    return SourceDocument(
        sha256=digest, tokens=tokens, blocks=(Block(block_id=0, page=1, text=QUOTE),)
    )


def _envelope(module_id: str, module_name: str, **runtime: object) -> str:
    return json.dumps(
        {
            "module_id": module_id,
            "module_name": module_name,
            "owned_object": module_name.lower(),
            "schema_family": "Nested",
            "output_class": "CANONICAL_MARKDOWN",
            "runtime_output": runtime,
            "evidence_trace": {
                "citations": [
                    {"document_sha256": DIGEST, "page": 1, "matched_text": QUOTE}
                ]
            },
            "confidence_score": 80,
            "confidence_band": "High",
            "limitation_flags": [],
            "qa_status": "Passed",
            "validation_warnings": [],
            "downstream_consumers": [],
        }
    )


def _answer(text: str, *, input_tokens: int, output_tokens: int) -> Completion:
    return Completion(
        text=text,
        model=MODEL,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        request_id=None,
    )


# Two answers, priced differently from each other and from the old flat 1.00,
# so a ledger that recorded either constant would fail.
CP0 = _answer(
    _envelope(
        "CP-0", "SourceReadiness", readiness_summary={"overall_readiness": "READY"}
    ),
    input_tokens=30_000,
    output_tokens=1_000,
)
CP8 = _answer(
    _envelope("CP-8", "DecisionLedgerPostMortem"),
    input_tokens=50_000,
    output_tokens=3_000,
)


@pytest.fixture
def pinned(store: Store) -> str:
    """A run pinned to one document and to the CP-0 -> CP-8 route."""
    admitted = admit_pack(store, case_id=CASE, documents=(_document(DIGEST),))
    version = pin_source_set(store, case_id=CASE, source_ids=admitted)
    run_id = start_run(store, case_id=CASE, ceiling=Decimal("100"))
    pin_route(
        store,
        run_id=run_id,
        resolved=resolve_route(CATALOG, FULL, LEDGER),
        source_set_version=version,
    )
    store.commit()
    return run_id


def _run(store: Store, run_id: str, blobs: BlobStore) -> RecordedProvider:
    provider = RecordedProvider(CP0, CP8)
    execute = module_executor(store, run_id=run_id, provider=provider, blobs=blobs)
    run_route(store, run_id=run_id, blobs=blobs, execute=execute)
    return provider


def test_the_loop_charges_what_the_provider_reported(
    store: Store, pinned: str, blobs: BlobStore
) -> None:
    """The Phase 4 deliverable Phase 6 owes."""
    _run(store, pinned, blobs)

    charged = store.execute(
        "SELECT node_id, amount FROM budget_ledger WHERE run_id = %s ORDER BY node_id",
        (pinned,),
    ).fetchall()
    assert [(n[-4:], a) for n, a in charged] == [
        ("CP-0", price_of(CP0)),
        ("CP-8", price_of(CP8)),
    ]
    assert price_of(CP0) != price_of(CP8), "two answers, two prices"
    assert Decimal("1.00") not in {price_of(CP0), price_of(CP8)}, "not the flat guess"

    # Each node's accepted artifact is the envelope the provider returned, and
    # the loop read CP-0's readiness back out of it to release CP-8.
    artifacts = store.execute(
        "SELECT count(*) FROM artifacts WHERE run_id = %s", (pinned,)
    ).fetchone()
    assert artifacts == (2,)


def test_the_reservation_is_the_ceiling_of_the_bytes_that_were_sent(
    store: Store, pinned: str, blobs: BlobStore
) -> None:
    """One statement of what a call contains: the bytes priced are the bytes sent.

    Invariant 8 wants the ceiling before the call. The only thing the host knows
    before the call is what it is about to send, so that -- and nothing computed
    separately from it -- is what the reservation is taken from.
    """
    provider = _run(store, pinned, blobs)

    reserved = store.execute(
        "SELECT reserved FROM run_attempts WHERE run_id = %s ORDER BY route_node_id",
        (pinned,),
    ).fetchall()
    assert [r for (r,) in reserved] == [ceiling_of(call) for call in provider.calls]
    # And what was charged fit inside what was reserved, both times.
    assert price_of(CP0) <= ceiling_of(provider.calls[0])
    assert price_of(CP8) <= ceiling_of(provider.calls[1])


def test_every_node_is_handed_every_block_of_the_pinned_set(
    store: Store, pinned: str, blobs: BlobStore
) -> None:
    provider = _run(store, pinned, blobs)

    assert all(QUOTE in call.prompt for call in provider.calls)
    # Recorded as handed, per node -- the ledger `_anchor` checks citations
    # against, which is why both envelopes could cite the quote.
    delivered = store.execute(
        "SELECT count(DISTINCT node_id) FROM delivered_evidence WHERE run_id = %s",
        (pinned,),
    ).fetchone()
    assert delivered == (2,)


def test_every_acceptance_is_durable_when_the_loop_returns(
    store: Store,
    pinned: str,
    blobs: BlobStore,
    store_schema: str,
    postgres_dsn: str,
) -> None:
    """Invariant 6, read from a second connection, which sees only what committed.

    `accept` is the outermost transaction only when nothing is open. After a
    real node's `_complete` has read the store, one is -- so `accept` became a
    savepoint, and the last node's artifact and charge sat uncommitted until
    something else committed. Every assertion on the loop's own connection saw
    them regardless, which is why this one does not use it.
    """
    _run(store, pinned, blobs)

    with psycopg.connect(postgres_dsn, autocommit=True) as other:
        other.execute(f'SET search_path TO "{store_schema}"')
        counted = other.execute(
            "SELECT (SELECT count(*) FROM artifacts WHERE run_id = %s),"
            " (SELECT count(*) FROM budget_ledger WHERE run_id = %s)",
            (pinned, pinned),
        ).fetchone()
    assert counted == (2, 2), "an acceptance the loop returned without committing"


def test_the_executor_refuses_a_pin_over_no_evidence(
    store: Store, blobs: BlobStore
) -> None:
    """Invariant 1 has nothing to run against, and says so before any node.

    A version with no members is not "every read refused" -- it is no reads at
    all, and a module called over nothing, which an envelope citing nothing
    would then be accepted for. The gate refuses it before a run exists; a
    direct pin is refused when the executor is built.
    """
    run_id = start_run(store, case_id=CASE, ceiling=Decimal("100"))
    pin_route(
        store,
        run_id=run_id,
        resolved=resolve_route(CATALOG, FULL, LEDGER),
        source_set_version=7,
    )
    with pytest.raises(Refusal) as caught:
        module_executor(store, run_id=run_id, provider=RecordedProvider(), blobs=blobs)
    assert caught.value.code is RefusalCode.SOURCE_SET_EMPTY


def test_a_refused_reservation_leaves_no_delivery_behind(
    store: Store, blobs: BlobStore
) -> None:
    """Assembly records what a node was handed before the reservation can refuse.

    A node that never ran was handed nothing. The rows were only ever
    uncommitted, but a caller committing later for its own reasons would land
    them, so the loop discards them itself -- checked on the loop's own
    connection, where merely-uncommitted rows would still show.
    """
    admitted = admit_pack(store, case_id=CASE, documents=(_document(DIGEST),))
    version = pin_source_set(store, case_id=CASE, source_ids=admitted)
    run_id = start_run(store, case_id=CASE, ceiling=Decimal("0.01"))
    pin_route(
        store,
        run_id=run_id,
        resolved=resolve_route(CATALOG, FULL, LEDGER),
        source_set_version=version,
    )
    store.commit()
    execute = module_executor(
        store, run_id=run_id, provider=RecordedProvider(CP0, CP8), blobs=blobs
    )

    with pytest.raises(Refusal) as caught:
        run_route(store, run_id=run_id, blobs=blobs, execute=execute)
    assert caught.value.code is RefusalCode.BUDGET_CEILING_EXCEEDED
    delivered = store.execute(
        "SELECT count(*) FROM delivered_evidence WHERE run_id = %s", (run_id,)
    ).fetchone()
    assert delivered == (0,), "a node that never ran was recorded as handed evidence"


def test_the_executor_refuses_a_node_the_pin_does_not_name(
    store: Store, pinned: str, blobs: BlobStore
) -> None:
    execute = module_executor(
        store, run_id=pinned, provider=RecordedProvider(), blobs=blobs
    )
    with pytest.raises(Refusal) as caught:
        execute("RN-FULL_CREDIT_32-DECISION_LEDGER-99-CP-X")
    assert caught.value.code is RefusalCode.ROUTE_NOT_PINNED


def test_the_executor_refuses_an_unknown_run_before_reading_its_pin(
    store: Store, blobs: BlobStore
) -> None:
    # The order `reserve` answers in: an unknown run is RUN_NOT_FOUND, never a
    # question about a route it could not have.
    with pytest.raises(Refusal) as caught:
        module_executor(
            store, run_id=str(uuid.uuid4()), provider=RecordedProvider(), blobs=blobs
        )
    assert caught.value.code is RefusalCode.RUN_NOT_FOUND
