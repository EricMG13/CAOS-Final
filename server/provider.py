"""The provider boundary: where a module's authority meets a model.

`SYSTEM_SPEC.md` §4. One non-streaming answer per node, priced from what the
provider reported using rather than from a flat guess -- which is what lets the
budget ledger record a call instead of an estimate.

Three deliberate departures from the Anthropic SDK's own defaults:

**No server-side `fallbacks`.** The SDK recommends enabling them so a policy
refusal is retried on another model. A run here is bound to a provider identity
(`REBUILD_PLAN.md` Phase 10), and a silent switch would make two runs of the same
pinned route incomparable and an artifact unattributable. A refusal is a typed
refusal.

**A credential means an environment variable.** The SDK would also resolve an
`ant` profile from disk, which would let a developer's machine spend money in a
suite that is meant to be free. See the known-gaps ledger.

**No SDK retries.** The default is two, each a fresh provider call under the
same attempt row and reservation -- the crash-after-billing case `DECISIONS.md`
§21 closed, reopened inside one call. Host retries are the only retries (§37).
"""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from decimal import ROUND_CEILING, Decimal

import anthropic

from server.refusals import Refusal, RefusalCode

# Pinned, and not a dated snapshot: the id is complete as it stands.
MODEL = "claude-opus-5"

# Anthropic first-party list price per million tokens for `claude-opus-5`, as
# checked 2026-06-24. A price change here is a charge change everywhere; the
# ledger is Decimal on every money path (invariant 7) and these never float.
INPUT_PER_MTOK = Decimal("5.00")
OUTPUT_PER_MTOK = Decimal("25.00")
_PER_MTOK = Decimal(1_000_000)

# What the SDK reads. Checked here rather than left to the SDK so that "no
# credential" is a decision this host makes, not one a profile on disk makes.
_CREDENTIAL_VARIABLES = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")


@dataclass(frozen=True, slots=True)
class ProviderCall:
    """One node's request. Authority in `system`, the node's task in `prompt`."""

    system: str
    prompt: str
    max_output_tokens: int


@dataclass(frozen=True, slots=True)
class Completion:
    """What came back, and what it cost to get."""

    text: str
    model: str
    input_tokens: int
    output_tokens: int
    request_id: str | None


type Provider = Callable[[ProviderCall], Completion]


def price_of(completion: Completion) -> Decimal:
    """What one completion costs, in Decimal, from reported usage."""
    return (
        INPUT_PER_MTOK * completion.input_tokens
        + OUTPUT_PER_MTOK * completion.output_tokens
    ) / _PER_MTOK


# What the API counts around the bytes a call sends: role and turn markers, and
# whatever else it counts that is not content. Single digits in practice; 256 is
# the margin over that, not an estimate of it. The one number in the ceiling not
# derived from the call, and `test_the_live_provider_returns_a_completion` is
# where it is checked against the tokenizer.
_FRAMING_TOKENS = 256

# Every money column is numeric(18, 6), and Postgres rounds what it is given.
_LEDGER_SCALE = Decimal("0.000001")


def input_token_bound(call: ProviderCall) -> int:
    """The most input tokens a call can be counted as, from the bytes it sends.

    A token is at least one byte, so the bytes sent bound the tokens counted.
    That is the one claim the reservation rests on.
    """
    sent = len(call.system.encode("utf-8")) + len(call.prompt.encode("utf-8"))
    return sent + _FRAMING_TOKENS


def ceiling_of(call: ProviderCall) -> Decimal:
    """The most a call can cost: its reservation, and the ceiling on its charge.

    Output is bounded exactly -- `max_tokens` caps thinking and text together.
    Input is bounded by its bytes. Invariant 8 wants the ceiling before the
    call, and this is everything the host knows before one. Rounded up to the
    ledger's scale, so what is stored is never below what was computed: a
    ceiling that rounds down is not a ceiling.
    """
    exact = (
        INPUT_PER_MTOK * input_token_bound(call)
        + OUTPUT_PER_MTOK * call.max_output_tokens
    ) / _PER_MTOK
    return exact.quantize(_LEDGER_SCALE, rounding=ROUND_CEILING)


class RecordedProvider:
    """A provider that answers from a script and refuses once it runs out.

    Running out is a refusal rather than a repeat: a test that executes one more
    node than it recorded should fail, not silently reuse an answer.
    """

    def __init__(self, *answers: Completion) -> None:
        self._answers = list(answers)
        self.calls: list[ProviderCall] = []

    def __call__(self, call: ProviderCall) -> Completion:
        self.calls.append(call)
        if not self._answers:
            raise Refusal(RefusalCode.PROVIDER_UNAVAILABLE)
        return self._answers.pop(0)


def provider_using(client: anthropic.Anthropic) -> Provider:
    """A provider bound to a client. The seam a test drives without a network."""

    def call(request: ProviderCall) -> Completion:
        return _complete(client, request)

    return call


def live_provider_or_none() -> Provider | None:
    """The real provider, or None when no credential is configured.

    None rather than a provider that fails at call time, so a suite without a
    credential skips visibly instead of failing deep inside a node.
    """
    client = live_client()
    return None if client is None else provider_using(client)


def live_client() -> anthropic.Anthropic | None:
    """The client the host calls with, or None when no credential is configured.

    A credential means an environment variable: the SDK would also read an
    `ant` profile from disk, and this is the one place that refuses it. No
    retries: a retry is a provider call, and a provider call needs a
    reservation of its own (`DECISIONS.md` §21, §37).
    """
    if not any(os.environ.get(name) for name in _CREDENTIAL_VARIABLES):
        return None
    return anthropic.Anthropic(max_retries=0)


def _complete(client: anthropic.Anthropic, call: ProviderCall) -> Completion:
    """One streamed answer. Streaming because authority runs to ~125 KB."""
    failure: RefusalCode | None = None
    try:
        with client.messages.stream(
            model=MODEL,
            max_tokens=call.max_output_tokens,
            system=call.system,
            thinking={"type": "adaptive"},
            output_config={"effort": "high"},
            messages=[{"role": "user", "content": call.prompt}],
        ) as streamed:
            answer = streamed.get_final_message()
    except (
        anthropic.AuthenticationError,
        anthropic.BadRequestError,
        anthropic.ConflictError,
        anthropic.NotFoundError,
        anthropic.PermissionDeniedError,
        anthropic.RequestTooLargeError,
        anthropic.UnprocessableEntityError,
    ):
        # Permanent: the call itself is wrong -- a bad key, a prompt the API
        # will not take -- and no retry mends it. PROVIDER_UNAVAILABLE is the
        # retry-worthy code (§37); a retry policy fed these under it would
        # spend a reservation on every attempt and never succeed.
        failure = RefusalCode.PROVIDER_CALL_INVALID
    except (anthropic.APIStatusError, anthropic.APIConnectionError):
        failure = RefusalCode.PROVIDER_UNAVAILABLE
    if failure is not None:
        # Raised clear of the handler: the SDK's exception carries the API's
        # own message, which can echo the prompt that produced it.
        raise Refusal(failure)
    if answer.stop_reason == "refusal":
        raise Refusal(RefusalCode.PROVIDER_REFUSED)
    if answer.stop_reason == "max_tokens":
        # HTTP 200, a full charge, and no answer: the ceiling failed, not the
        # module. Typed so the remedy reads as "raise max_output_tokens" rather
        # than the ENVELOPE_INVALID a stopped-mid-object answer would earn.
        raise Refusal(RefusalCode.PROVIDER_OUTPUT_TRUNCATED)
    return Completion(
        text="".join(b.text for b in answer.content if b.type == "text"),
        model=answer.model,
        input_tokens=answer.usage.input_tokens,
        output_tokens=answer.usage.output_tokens,
        # A streamed answer is a ParsedMessage, which carries no `_request_id`
        # -- reading it directly raised AttributeError on every live call.
        request_id=getattr(answer, "_request_id", None),
    )
