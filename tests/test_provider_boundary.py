"""The provider boundary: the only place a module's authority meets a model.

`SYSTEM_SPEC.md` §4 -- `run_node` reserves budget, resolves the provider,
executes, validates the envelope. This is the resolve-and-execute half.

No live call runs in this suite. `test_a_live_call_needs_a_credential_and_says_so`
is what stops that from being a vacuous pass: it asserts the live test is
skipped for a stated reason rather than quietly absent.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from decimal import Decimal

import httpx2 as httpx
import pytest
from anthropic import Anthropic

from server.provider import (
    MODEL,
    Completion,
    ProviderCall,
    RecordedProvider,
    live_client,
    live_provider_or_none,
    price_of,
    provider_using,
)
from server.refusals import Refusal, RefusalCode

CALL = ProviderCall(
    system="You are CP-1.",
    prompt="Produce the canonical envelope.",
    max_output_tokens=1024,
)


def test_a_recorded_provider_answers_without_a_network() -> None:
    """What the loop's tests run against. The shape, not the model."""
    provider = RecordedProvider(
        Completion(
            text='{"module_id": "CP-1"}',
            model=MODEL,
            input_tokens=1000,
            output_tokens=50,
            request_id="req_test",
        )
    )
    answered = provider(CALL)
    assert answered.text == '{"module_id": "CP-1"}'
    assert provider.calls == [CALL]


def test_a_recorded_provider_refuses_when_it_has_nothing_left() -> None:
    """A test that runs one more node than it recorded must fail, not repeat."""
    provider = RecordedProvider()
    with pytest.raises(Refusal) as refused:
        provider(CALL)
    assert refused.value.code is RefusalCode.PROVIDER_UNAVAILABLE


def test_the_charge_is_what_the_provider_reported_using() -> None:
    """Invariant 8: the ledger records the call, not a flat guess.

    Phase 4 priced every node at 1.00 because nothing had quoted one.
    """
    charge = price_of(
        Completion(
            text="{}",
            model=MODEL,
            input_tokens=1_000_000,
            output_tokens=1_000_000,
            request_id=None,
        )
    )
    assert charge == Decimal("30.00")
    assert isinstance(charge, Decimal)


def test_a_zero_token_completion_costs_nothing_and_stays_decimal() -> None:
    nothing = Completion(
        text="", model=MODEL, input_tokens=0, output_tokens=0, request_id=None
    )
    assert price_of(nothing) == Decimal("0")


def test_the_model_is_pinned_and_is_not_a_dated_snapshot() -> None:
    """A run is bound to a provider identity (REBUILD_PLAN Phase 10).

    A floating alias or a date-suffixed guess would make two runs of the same
    pinned route incomparable.
    """
    assert MODEL == "claude-opus-5"


def test_a_live_call_needs_a_credential_and_says_so(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The non-vacuity guard, in the shape `test_recalc_unavailable` uses.

    With no credential the live provider is absent rather than silently
    degraded, so a green suite never means a live call was made.
    """
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    assert live_client() is None, "the client itself refuses, not only the wrapper"
    assert live_provider_or_none() is None


def test_the_live_client_never_retries_on_its_own(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Invariant 8 and `docs/DECISIONS.md` §35: host retries are the only retries.

    The SDK's default is two, and each one is a provider call under the same
    attempt row and the same reservation. Read from the client the host builds,
    not from a mock: `_client_answering` sets zero itself, so the mock suite
    could never notice the default.
    """
    monkeypatch.setenv("ANTHROPIC_API_KEY", "not-a-real-key")
    client = live_client()
    assert client is not None
    assert client.max_retries == 0


@pytest.mark.live_provider
def test_the_live_provider_returns_a_completion() -> None:
    """Opt-in, and the only test in this repository that spends money.

    Skipped without a credential. Nothing else in the suite touches a network.
    """
    provider = live_provider_or_none()
    if provider is None:
        pytest.skip("no Anthropic credential configured")
    answered = provider(
        ProviderCall(
            system="Answer with the single word: ready.",
            prompt="Are you there?",
            max_output_tokens=16,
        )
    )
    assert answered.model.startswith("claude-opus-5")
    assert answered.output_tokens > 0
    assert price_of(answered) > Decimal("0")


def _client_answering(handler: Callable[[httpx.Request], httpx.Response]) -> Anthropic:
    """A real SDK client whose wire is a function. No network, no credential."""
    return Anthropic(
        api_key="not-a-real-key",
        max_retries=0,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )


def _sse(*events: tuple[str, dict[str, object]]) -> httpx.Response:
    body = "".join(
        f"event: {name}\ndata: {json.dumps(payload)}\n\n" for name, payload in events
    )
    return httpx.Response(200, text=body, headers={"content-type": "text/event-stream"})


def _message(stop_reason: str) -> list[tuple[str, dict[str, object]]]:
    return [
        (
            "message_start",
            {
                "type": "message_start",
                "message": {
                    "id": "msg_1",
                    "type": "message",
                    "role": "assistant",
                    "model": MODEL,
                    "content": [],
                    "stop_reason": None,
                    "stop_sequence": None,
                    "usage": {"input_tokens": 1200, "output_tokens": 0},
                },
            },
        ),
        (
            "content_block_start",
            {
                "type": "content_block_start",
                "index": 0,
                "content_block": {"type": "text", "text": ""},
            },
        ),
        (
            "content_block_delta",
            {
                "type": "content_block_delta",
                "index": 0,
                "delta": {"type": "text_delta", "text": '{"module_id":"CP-1"}'},
            },
        ),
        ("content_block_stop", {"type": "content_block_stop", "index": 0}),
        (
            "message_delta",
            {
                "type": "message_delta",
                "delta": {"stop_reason": stop_reason, "stop_sequence": None},
                "usage": {"output_tokens": 40},
            },
        ),
        ("message_stop", {"type": "message_stop"}),
    ]


def test_the_request_carries_the_model_the_authority_and_adaptive_thinking() -> None:
    """Drives the real SDK to a fake wire, so the body is the one it would send.

    Without this the live path would ship having never been executed at all.
    """
    sent: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        sent.update(json.loads(request.content))
        return _sse(*_message("end_turn"))

    answered = provider_using(_client_answering(handler))(CALL)

    assert sent["model"] == MODEL
    assert sent["system"] == CALL.system
    assert sent["max_tokens"] == CALL.max_output_tokens
    assert sent["thinking"] == {"type": "adaptive"}
    assert sent["output_config"] == {"effort": "high"}
    assert sent["stream"] is True
    # The run must stay attributable to one provider identity.
    assert "fallbacks" not in sent
    assert answered.text == '{"module_id":"CP-1"}'
    assert answered.input_tokens == 1200
    assert answered.output_tokens == 40


def test_a_policy_refusal_is_a_typed_refusal_not_an_empty_answer() -> None:
    """`stop_reason: refusal` returns HTTP 200 -- nothing raises on its own."""

    def handler(request: httpx.Request) -> httpx.Response:
        return _sse(*_message("refusal"))

    with pytest.raises(Refusal) as refused:
        provider_using(_client_answering(handler))(CALL)
    assert refused.value.code is RefusalCode.PROVIDER_REFUSED


@pytest.mark.parametrize(
    ("status", "code"),
    [
        (400, RefusalCode.PROVIDER_CALL_INVALID),
        (404, RefusalCode.PROVIDER_CALL_INVALID),
        (429, RefusalCode.PROVIDER_UNAVAILABLE),
        (500, RefusalCode.PROVIDER_UNAVAILABLE),
        (529, RefusalCode.PROVIDER_UNAVAILABLE),
    ],
)
def test_every_provider_failure_becomes_a_typed_code(
    status: int, code: RefusalCode
) -> None:
    """And carries none of the API's own message, which can echo the prompt."""
    secret = "leveraged-buyout-of-a-named-issuer"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status,
            json={"type": "error", "error": {"type": "x", "message": secret}},
        )

    with pytest.raises(Refusal) as refused:
        provider_using(_client_answering(handler))(CALL)
    assert refused.value.code is code

    leaked = []
    error: BaseException | None = refused.value
    while error is not None:
        leaked.append(repr(error))
        error = error.__cause__ or error.__context__
    assert secret not in " ".join(leaked)
