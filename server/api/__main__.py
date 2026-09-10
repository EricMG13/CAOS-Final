"""`python -m server.api`: the one process `docs/SYSTEM_SPEC.md` §11 runs."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg
import uvicorn

from server.api.app import create_app
from server.api.identity import environment_from
from server.store import apply_schema
from server.store.blobs import BlobStore


def main() -> None:
    environment = environment_from(os.environ)
    connection = psycopg.connect(os.environ["CAOS_POSTGRES_URL"], autocommit=False)
    with connection.transaction():
        # A drifted store is refused before it is changed (DECISIONS.md 27).
        apply_schema(connection)
    root = Path(os.environ["CAOS_BLOB_ROOT"]).resolve()
    if not root.is_dir():
        # Refused here, as a drifted store is: the alternative is every view of
        # a run with an accepted artifact answering 500 and nothing saying why.
        sys.exit(f"CAOS_BLOB_ROOT is not a directory: {root}")
    blobs = BlobStore(root=root)
    app = create_app(connection, blobs=blobs, environment=environment)
    # No access log and no forwarded client address: uvicorn's own logging is
    # not the redacting logger SYSTEM_SPEC 10 wants, and every connection here
    # is the proxy's, so a client's X-Forwarded-For would only be its claim.
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        access_log=False,
        server_header=False,
        proxy_headers=False,
    )


if __name__ == "__main__":
    main()
