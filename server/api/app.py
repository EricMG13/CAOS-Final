"""The ASGI app: routes, and what a refusal becomes on the wire.

One process, one connection, one instance (`docs/SYSTEM_SPEC.md` §11). A
refusal is a code from a closed set and travels as exactly that; the two codes
an outsider could use to tell a run that exists from one that does not are
served as one 404 with one body (§8).
"""

from __future__ import annotations

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from server.api.identity import Environment, identify
from server.api.runs import RunView, run_view
from server.api.wire import RefusalBody
from server.refusals import Refusal, RefusalCode
from server.store import Store
from server.store.blobs import BlobStore

_STATUS = {RefusalCode.RUN_NOT_FOUND: 404, RefusalCode.STANDING_INSUFFICIENT: 404}
# Both 404s say this and only this: neither that the run exists nor that the
# asker is not on its case. Every other refusal on a read is the host's own.
_PRIVATE = RefusalBody(code=RefusalCode.RUN_NOT_FOUND)


def create_app(store: Store, *, blobs: BlobStore, environment: Environment) -> FastAPI:
    """The app over one open store connection. Serves nothing but named models."""
    # No generated docs: three routes nobody reads, and a contract test that
    # names every route this app serves.
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    app.add_exception_handler(Refusal, _refused)

    @app.get("/api/runs/{run_id}", response_model=RunView)
    async def get_run(request: Request, run_id: str) -> RunView:
        # ponytail: a synchronous store on the event loop, so requests are
        # served one at a time on the one connection; a pool and a threadpool
        # the day a second analyst waits on the first.
        identity = identify(request.headers.items(), environment=environment)
        return run_view(store, blobs=blobs, identity=identity, run_id=run_id)

    return app


def _refused(request: Request, refused: Exception) -> Response:
    if not isinstance(refused, Refusal):  # pragma: no cover - registered for Refusal
        raise refused
    status = _STATUS.get(refused.code, 500)
    body = _PRIVATE if status == 404 else RefusalBody(code=refused.code)
    return JSONResponse(status_code=status, content=body.model_dump(mode="json"))
