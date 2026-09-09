"""Every path `CLAUDE.md` names either exists or is marked as not yet present,
and every exit test the plan names for an exited phase was written.

`CLAUDE.md` is the first thing an agent reads, so a map naming a directory the
repository does not have costs more than no map at all. Five of the six original
entries pointed at paths that never existed -- `engine/runtime.py`, `storage/`,
`methodology/`, `models/`, `frontend/` -- while `server/evidence/`, which holds
two invariants, was unlisted. `docs/REBUILD_PLAN.md` is the second thing, and
it decides what gets built next (`docs/DECISIONS.md` §36).
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CONTRACT = (REPO / "CLAUDE.md").read_text(encoding="utf-8")
PLAN = (REPO / "docs" / "REBUILD_PLAN.md").read_text(encoding="utf-8")
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
HEADING = re.compile(r"^## (.+)$", re.M)
PHASE_TITLE = re.compile(r"Phase (\d+)\b")
EXIT_TEST = re.compile(r"`(test_\w+)`")
DEFINITION = re.compile(r"^def (test_\w+)", re.M)


def _phases(plan: str) -> dict[int, set[str]]:
    """The exit tests the plan backticks, keyed by phase number.

    Split on every `##` heading and keep the ones titled `Phase N`, so the
    standing rules after the last phase are nobody's exit tests.
    """
    parts = HEADING.split(plan)
    phases: dict[int, set[str]] = {}
    for title, body in zip(parts[1::2], parts[2::2], strict=True):
        if numbered := PHASE_TITLE.match(title):
            phases[int(numbered[1])] = set(EXIT_TEST.findall(body))
    return phases


def _owed(phases: dict[int, set[str]], defined: set[str]) -> list[str]:
    """Exit tests of every phase below the highest started one that are unwritten.

    A phase has started once any test it names exists. The current phase may
    still owe its own; the ones before it may not.
    """
    started = [n for n, names in phases.items() if names & defined]
    if not started:
        return []
    return sorted(
        name
        for n, names in phases.items()
        if n < max(started)
        for name in names - defined
    )


def _defined() -> set[str]:
    return {
        name
        for path in (REPO / "tests").glob("test_*.py")
        for name in DEFINITION.findall(path.read_text(encoding="utf-8"))
    }


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


def test_a_phase_below_the_current_one_owes_no_exit_test() -> None:
    plan = (
        "## Phase 1 — a\n`test_one`\n## Phase 2 — b\n`test_two`\n"
        "## Standing rules\n`test_elsewhere`\n"
    )
    phases = _phases(plan)
    assert phases == {1: {"test_one"}, 2: {"test_two"}}, "only phase headings count"
    assert _owed(phases, {"test_two"}) == ["test_one"]
    assert _owed(phases, {"test_one"}) == [], "the current phase may still owe its own"
    assert _owed(phases, set()) == [], "nothing started, nothing owed"


def test_every_exit_test_of_an_exited_phase_exists() -> None:
    # The plan says a phase is done when its exit test passes, and the next
    # session starts at the lowest phase whose exit test does not pass. A phase
    # whose named test was never written is invisible to that rule: three
    # phases were exited with their deliverable still owed before this looked.
    owed = _owed(_phases(PLAN), _defined())
    assert owed == [], f"exit tests the plan names for exited phases, unwritten: {owed}"
