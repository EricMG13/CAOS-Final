"""The vendored bundle is the authority, and it is the one the spec was written
against.

Invariant 4: the bundle is the methodology authority, integrity checked on the
bytes. This is the pin -- every fact `docs/DECISIONS.md` §2 and §5 rest on,
asserted against the bytes in `vendor/`. A bundle swap that changes any of them
fails here rather than silently changing every route the system runs.

Verification at *use* is Phase 5. This is verification at rest: the vendored
copy is byte-identical to the manifest it shipped with.
"""

from __future__ import annotations

import collections
import hashlib
import json
from pathlib import Path

import pytest

BUNDLE = Path(__file__).resolve().parents[1] / "vendor" / "deploy-v"
CATALOG = (
    BUNDLE / "skills/cp-os-credit-os/references/CREDIT_OS_V_MODULE_CATALOG_v2.json"
)

# docs/DECISIONS.md §17. A run pinned to one build never executes under another.
BUILD_ID = "a43cb903ca2751f79e77b6da71f6ea131b8462a32e1b549d65fd0f67389d185f"


def _load(path: Path) -> dict[str, object]:
    return dict(json.loads(path.read_text(encoding="utf-8")))


@pytest.fixture(scope="module")
def catalog() -> dict[str, object]:
    return _load(CATALOG)


@pytest.fixture(scope="module")
def integrity() -> dict[str, object]:
    return _load(BUNDLE / "DEPLOY_V_INTEGRITY_v1.json")


def test_the_vendored_build_is_the_pinned_one(integrity: dict[str, object]) -> None:
    assert integrity["build_id"] == BUILD_ID


def test_every_vendored_byte_matches_the_manifest(integrity: dict[str, object]) -> None:
    roots = integrity["root_file_hashes"]
    skills = integrity["skills"]
    assert isinstance(roots, dict)
    assert isinstance(skills, list)

    expected: dict[Path, str] = {
        BUNDLE / name: str(entry["sha256"]) for name, entry in roots.items()
    }
    for skill in skills:
        folder = BUNDLE / "skills" / str(skill["folder_slug"])
        for name, entry in dict(skill["relative_file_hashes"]).items():
            expected[folder / name] = str(entry["sha256"])

    assert len(expected) > 300, "a manifest covering almost nothing is not a check"
    wrong = [
        path.relative_to(BUNDLE)
        for path, digest in expected.items()
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest
    ]
    assert wrong == [], f"vendored copy differs from its manifest: {wrong[:5]}"


def test_the_typed_edges_are_where_the_spec_says(catalog: dict[str, object]) -> None:
    profiles = catalog["profiles"]
    assert isinstance(profiles, dict)
    assert set(profiles) == {"FULL_CREDIT_32", "LITE_CREDIT_22"}

    counted = collections.Counter(
        edge["type"] for edge in profiles["FULL_CREDIT_32"]["edges"]
    )
    # docs/DECISIONS.md §2: the numbers the predecessor's defect was measured in.
    assert counted == {"REQUIRED": 44, "OPTIONAL": 25, "ADVISORY": 22, "QA_GATE": 1}


def test_navigation_dependencies_is_the_untyped_list_we_must_not_read(
    catalog: dict[str, object],
) -> None:
    navigation = catalog["navigation"]
    assert isinstance(navigation, dict)
    pairs = navigation["dependencies"]
    assert isinstance(pairs, list)
    assert len(pairs) == 97
    # It carries no type at all -- which is why reading it enforced 47 soft
    # edges as mandatory and made the one QA_GATE not gate.
    assert all("type" not in pair for pair in pairs)


def test_the_catalog_carries_eighteen_pathways(catalog: dict[str, object]) -> None:
    profiles = catalog["profiles"]
    assert isinstance(profiles, dict)
    assert sum(len(profile["pathways"]) for profile in profiles.values()) == 18


def test_cp_parse_is_superseded_upstream_and_stage_zero_is_not_runnable(
    catalog: dict[str, object],
) -> None:
    # Both premises of the DECISIONS.md §5 carve-out. If upstream ever stops
    # saying either, the carve-out needs revisiting rather than carrying on.
    superseded = catalog["superseded_module_ids"]
    assert isinstance(superseded, dict)
    assert superseded["CP-PARSE"]["absorbed_by"] == "CP-0"
    preparation = catalog["preparation_stage"]
    assert isinstance(preparation, dict)
    assert preparation == {
        "module_id": "CP-0",
        "phase": "preparation",
        "required_before": "CP-0 readiness phase",
        "runnable": False,
    }


def test_the_catalog_declares_no_conditional_edge(catalog: dict[str, object]) -> None:
    # CONDITIONAL is a live edge type in CONTEXT.md and no edge uses it today,
    # so predicate freezing has nothing to act on. Recorded, not assumed.
    profiles = catalog["profiles"]
    assert isinstance(profiles, dict)
    conditional = [
        edge
        for profile in profiles.values()
        for edge in profile["edges"]
        if edge["type"] == "CONDITIONAL"
    ]
    assert conditional == []
