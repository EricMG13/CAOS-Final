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

# A backticked path: contains a slash, and no spaces or wildcards. Matching on
# a suffix instead silently skips whatever suffix the list forgot -- the first
# version required `/` or `.py` and so never checked `server/store/schema.sql`,
# which this map names.
PATH = re.compile(r"`([A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*/?)`")


def _lists(named: set[str], package: str) -> bool:
    """True when some named path is inside `package`.

    The trailing slash is load-bearing: comparing against the bare directory
    name would let `server/eng/` count as listed because
    `server/engine/route.py` starts with it.
    """
    return any(name.startswith(package) for name in named)


def _named(text: str) -> set[str]:
    found = {m for m in PATH.findall(text) if "/" in m}
    return {m for m in found if not m.startswith("docs/")}


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
    unlisted = sorted(p for p in packages if not _lists(named, p))
    assert unlisted == [], f"server packages the map does not mention: {unlisted}"


def test_the_map_check_covers_every_backticked_path_not_only_python() -> None:
    # The first version matched on suffix, so a .sql path the map names was
    # never verified. A path is a path whatever it ends in.
    named = _named(PRESENT)
    assert "server/store/schema.sql" in named
    assert "server/store/" in named


def test_a_package_whose_name_prefixes_a_listed_one_is_not_counted_as_listed() -> None:
    named = {"server/engine/route.py"}
    assert _lists(named, "server/engine/")
    assert not _lists(named, "server/eng/")


def test_the_planned_paths_are_marked_as_absent() -> None:
    # If one of these arrives, it moves into the list above and stops being a
    # promise -- which this test is what forces.
    still_absent = [p for p in _named(PLANNED) if not (REPO / p).exists()]
    assert sorted(still_absent) == sorted(_named(PLANNED)), (
        "a planned path now exists; move it into the map above"
    )
