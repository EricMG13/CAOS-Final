"""The ASGI app: routes, and what a refusal becomes on the wire.

One process, one connection, one instance (`docs/SYSTEM_SPEC.md` §11). A
refusal is a code from a closed set and travels as exactly that; the two codes
an outsider could use to tell a run that exists from one that does not are
served as one 404 with one body (§8).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse

from server.api.events import event_tail, last_seen, poll_events, reserve_tail
from server.api.identity import Environment, identify
from server.api.runs import RunView, run_view
from server.api.wire import RefusalBody
from server.refusals import Refusal, RefusalCode
from server.store import Store
from server.store.blobs import BlobStore

type _Next = Callable[[Request], Awaitable[Response]]

_STATUS = {
    RefusalCode.RUN_NOT_FOUND: 404,
    RefusalCode.STANDING_INSUFFICIENT: 404,
    RefusalCode.STREAM_CEILING_EXCEEDED: 429,
}
# Both 404s say this and only this: neither that the run exists nor that the
# asker is not on its case. Every other refusal on a read is the host's own.
_PRIVATE = RefusalBody(code=RefusalCode.RUN_NOT_FOUND)
# A proxy that buffers a stream defeats it, and one that caches it serves a
# member's events to whoever asks next. `SYSTEM_SPEC.md` §11 puts one in front.
_STREAM = {"x-accel-buffering": "no"}
# Every answer here is one member's. A shared cache keys on method and URI, so
# without these it could hand one member's document to whoever asks next, and
# `SYSTEM_SPEC.md` §11 puts a reverse proxy in front of this process.
_PRIVATE_TO_ONE_MEMBER = {
    "cache-control": "no-store",
    "vary": "X-Forwarded-User, X-Caos-Member",
}


def create_app(store: Store, *, blobs: BlobStore, environment: Environment) -> FastAPI:
    """The app over one open store connection. Serves nothing but named models."""
    # No generated docs: three routes nobody reads, and a contract test that
    # names every route this app serves.
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    app.add_exception_handler(Refusal, _refused)

    @app.middleware("http")
    async def _uncacheable(request: Request, call_next: _Next) -> Response:
        # Here rather than per route, so a route added later cannot forget.
        answer = await call_next(request)
        answer.headers.update(_PRIVATE_TO_ONE_MEMBER)
        return answer

    @app.get("/api/runs/{run_id}", response_model=RunView)
    async def get_run(request: Request, run_id: str) -> RunView:
        # ponytail: a synchronous store on the event loop, so requests are
        # served one at a time on the one connection; a pool and a threadpool
        # the day a second analyst waits on the first.
        identity = identify(request.headers.items(), environment=environment)
        return run_view(store, blobs=blobs, identity=identity, run_id=run_id)

    @app.get("/api/runs/{run_id}/events")
    async def get_run_events(request: Request, run_id: str) -> Response:
        # SSE is §9's one carve-out from a named model. The first poll happens
        # here rather than inside the tail, so a stranger is refused with the
        # private 404 instead of being handed a stream that shuts immediately.
        identity = identify(request.headers.items(), environment=environment)
        if identity is None:
            raise Refusal(RefusalCode.STANDING_INSUFFICIENT)
        # Nobody at all is refused before a header of theirs is parsed; a
        # caller with a name but no standing still reaches `last_seen`, which
        # is why that is bounded rather than merely typed.
        after = last_seen(request.headers.items())
        first = poll_events(store, identity=identity, run_id=run_id, after=after)
        if first.terminal and not first.events:
            # Nothing will ever follow. A stream that merely ends makes
            # `EventSource` reconnect a few seconds later and ask again, for
            # as long as the tab is open; 204 is what closes it.
            return Response(status_code=204)
        reserve_tail(identity)
        return StreamingResponse(
            event_tail(
                store, identity=identity, run_id=run_id, after=after, first=first
            ),
            media_type="text/event-stream",
            headers=_STREAM,
        )

    return app


def _refused(request: Request, refused: Exception) -> Response:
    if not isinstance(refused, Refusal):  # pragma: no cover - registered for Refusal
        raise refused
    status = _STATUS.get(refused.code, 500)
    body = _PRIVATE if status == 404 else RefusalBody(code=refused.code)
    return JSONResponse(status_code=status, content=body.model_dump(mode="json"))
