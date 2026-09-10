"""The wire (`docs/SYSTEM_SPEC.md` §9): every JSON body serves a named model with
`extra="forbid"` both ways. A new field is a model change plus an updated pinned
key set in `tests/test_run_surface.py`."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from server.refusals import RefusalCode


class Wire(BaseModel):
    """What every wire model is: closed, and immutable once built."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class RefusalBody(Wire):
    """A declined request. Its only payload is the code, as `Refusal`'s is."""

    code: RefusalCode
