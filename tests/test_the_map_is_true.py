"""Every path `CLAUDE.md` names either exists or is marked as not yet present.

`CLAUDE.md` is the first thing an agent reads, so a map naming a directory the
repository does not have costs more than no map at all. Five of the six original
entries pointed at paths that never existed -- `engine/runtime.py`, `storage/`,
`methodology/`, `models/`, `frontend/` -- while `server/evidence/`, which holds
two invariants, was unlisted.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CONTRACT = (REPO / "CLAUDE.md").read_text(encoding="utf-8")
SECTION = CONTRACT[
    CONTRACT.index("## Where things live") : CONTRACT.index("## Rules of work")
]
# The paragraph that lists what a later phase adds; those paths are not here yet.
PRESENT, _, PLANNED = SECTION.partition("Arriving with their phase")

# A backticked path: has a slash or a .py, and no spaces or wildcards.
PATH = re.compile(r"`([A-Za-z0-9_./-]+(?:/|\.py))`")


def _named(text: str) -> set[str]:
    return {m for m in PATH.findall(text) if not m.startswith("docs/")}


def test_every_path_the_map_names_exists() -> None:
    missing = sorted(p for p in _named(PRESENT) if not (REPO / p).exists())
    assert missing == [], f"CLAUDE.md names paths that do not exist: {missing}"


def test_the_map_names_every_server_package() -> None:
    named = _named(PRESENT)
    packages = {
        f"{d.relative_to(REPO)}/"
        for d in (REPO / "server").iterdir()
        if d.is_dir() and not d.name.startswith(("_", "."))
    }
    unlisted = sorted(
        p for p in packages if not any(n.startswith(p.rstrip("/")) for n in named)
    )
    assert unlisted == [], f"server packages the map does not mention: {unlisted}"


def test_the_planned_paths_are_marked_as_absent() -> None:
    # If one of these arrives, it moves into the list above and stops being a
    # promise -- which this test is what forces.
    still_absent = [p for p in _named(PLANNED) if not (REPO / p).exists()]
    assert sorted(still_absent) == sorted(_named(PLANNED)), (
        "a planned path now exists; move it into the map above"
    )
