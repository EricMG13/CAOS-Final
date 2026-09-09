"""The bundle is the methodology authority, verified on the bytes at use.

Invariant 4. `tests/test_bundle_pin.py` checks the vendored copy at rest against
the manifest it shipped with; this checks the bytes when a module is actually
handed them, which is the only moment that can refuse an execution.

The tests that need corrupt bytes work on a copy in `tmp_path`. Editing
`vendor/` is what invariant 4 forbids, and a test that leaves the worktree dirty
when it dies is worse than the defect it looks for.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from methodology.bundle import BUNDLE_ROOT, MANIFEST_NAME, Bundle, open_bundle
from methodology.registry import (
    Authority,
    ModuleSpec,
    assemble_authority,
    live_module_ids,
    module_spec,
    reference_files,
)
from server.refusals import Refusal, RefusalCode

CATALOG = "skills/cp-os-credit-os/references/CREDIT_OS_V_MODULE_CATALOG_v2.json"
RUNBOOK = "skills/cp-1-canonical-data-foundation/references/CP-1_RUNBOOK.md"


@pytest.fixture
def bundle_copy(tmp_path: Path) -> Path:
    """A writable copy of the vendored bundle, byte-identical to start with."""
    root = tmp_path / "deploy-v"
    shutil.copytree(BUNDLE_ROOT, root, symlinks=True)
    return root


def test_the_bundle_is_the_build_the_specification_was_written_against() -> None:
    """The build id is read from the manifest whose bytes the host pins.

    Nothing else has to assert it: `MANIFEST_SHA256` covers the whole file, so
    a different build cannot present itself under this one's id.
    """
    bundle: Bundle = open_bundle()
    assert bundle.build_id == (
        "a43cb903ca2751f79e77b6da71f6ea131b8462a32e1b549d65fd0f67389d185f"
    )
    assert bundle.root == BUNDLE_ROOT


def test_a_module_spec_names_its_folder_and_the_files_it_is_given() -> None:
    spec: ModuleSpec = module_spec("CP-1")
    assert spec.skill_slug == "cp-1-canonical-data-foundation"
    assert spec.reference_files[0] == ("skills/cp-1-canonical-data-foundation/SKILL.md")
    assert spec.reference_files[-1] == "CANON_SHARED.md"
    assert len(spec.reference_files) == 6


def test_authority_bytes_mismatch_refuses(bundle_copy: Path) -> None:
    """The Phase 5 exit test. One byte, and the module does not run."""
    assert assemble_authority("CP-1", root=bundle_copy).module_id == "CP-1"

    target = bundle_copy / RUNBOOK
    target.write_bytes(target.read_bytes().replace(b"CP-1", b"CP-2", 1))

    with pytest.raises(Refusal) as refused:
        assemble_authority("CP-1", root=bundle_copy)
    assert refused.value.code is RefusalCode.METHODOLOGY_AUTHORITY_MISMATCH


def test_a_tampered_manifest_refuses(bundle_copy: Path) -> None:
    """The manifest declares its own build id, so the host pins its bytes.

    Without this, editing a file *and* its manifest entry verifies clean and the
    bundle vouches for whatever it was last edited into.
    """
    manifest = bundle_copy / MANIFEST_NAME
    loaded = json.loads(manifest.read_text(encoding="utf-8"))
    loaded["build_id"] = "0" * 64
    manifest.write_text(json.dumps(loaded), encoding="utf-8")

    with pytest.raises(Refusal) as refused:
        assemble_authority("CP-1", root=bundle_copy)
    assert refused.value.code is RefusalCode.METHODOLOGY_BUNDLE_INVALID


def test_the_manifest_is_the_only_uncovered_vendored_file() -> None:
    """What `MANIFEST_NAME`'s pinned digest is the sole cover for.

    Every other vendored byte is covered by a manifest entry. The day upstream
    ships a second uncovered file, this fails rather than that file quietly
    becoming unverifiable.
    """
    bundle = open_bundle()
    on_disk = {
        path.relative_to(BUNDLE_ROOT).as_posix()
        for path in BUNDLE_ROOT.rglob("*")
        # What the bundle's own .gitignore excludes: a Finder visit or a manual
        # run of its verify_package.py leaves files that were never vendored.
        if path.is_file() and not _is_incidental(path.relative_to(BUNDLE_ROOT))
    }
    assert on_disk - set(bundle.digests) == {MANIFEST_NAME}


def _is_incidental(relative: Path) -> bool:
    return any(
        part == "__pycache__" or (part.startswith(".") and part != ".gitignore")
        for part in relative.parts
    )


def test_a_manifest_entry_with_no_file_on_disk_refuses(bundle_copy: Path) -> None:
    (bundle_copy / RUNBOOK).unlink()
    with pytest.raises(Refusal) as refused:
        assemble_authority("CP-1", root=bundle_copy)
    assert refused.value.code is RefusalCode.METHODOLOGY_AUTHORITY_MISMATCH


def test_a_symlinked_authority_file_is_refused(bundle_copy: Path) -> None:
    """No-follow handles (SYSTEM_SPEC 3), on the same bytes.

    The content is identical, so only the handle can refuse this.
    """
    target = bundle_copy / RUNBOOK
    elsewhere = bundle_copy.parent / "runbook.md"
    elsewhere.write_bytes(target.read_bytes())
    target.unlink()
    target.symlink_to(elsewhere)

    with pytest.raises(Refusal) as refused:
        assemble_authority("CP-1", root=bundle_copy)
    assert refused.value.code is RefusalCode.METHODOLOGY_AUTHORITY_MISMATCH


def test_a_refusal_carries_no_filesystem_detail(bundle_copy: Path) -> None:
    """The code travels; the path never does (docs/AI_CODE_QUALITY.md 1)."""
    (bundle_copy / RUNBOOK).unlink()
    with pytest.raises(Refusal) as refused:
        assemble_authority("CP-1", root=bundle_copy)

    leaked = []
    error: BaseException | None = refused.value
    while error is not None:
        leaked.extend([repr(error), str(error), *(str(arg) for arg in error.args)])
        error = error.__cause__ or error.__context__
    joined = " ".join(leaked)
    for secret in (str(bundle_copy), "CP-1_RUNBOOK", "deploy-v", "vendor"):
        assert secret not in joined


def test_the_os_skill_folder_is_not_a_live_module() -> None:
    """The catalog says what is live; the manifest only says what its bytes are.

    CP-OS ships as a skill folder and is not one of the catalog's modules. Were
    the live set taken from folder layout, `assemble_authority("CP-OS")` would
    hand a model the routing catalog itself -- authority reading its own map.
    """
    assert "CP-OS" in open_bundle().folders
    assert "CP-OS" not in live_module_ids()
    with pytest.raises(Refusal) as refused:
        assemble_authority("CP-OS")
    assert refused.value.code is RefusalCode.METHODOLOGY_MODULE_UNKNOWN


def test_an_unknown_module_id_is_refused() -> None:
    with pytest.raises(Refusal) as refused:
        assemble_authority("CP-NOT-A-MODULE")
    assert refused.value.code is RefusalCode.METHODOLOGY_MODULE_UNKNOWN


def test_cp_parse_receives_cp0_authority_under_its_own_identity() -> None:
    """The `docs/DECISIONS.md` 5 carve-out, wired.

    CP-PARSE is superseded upstream and runnable here. It gets the whole CP-0
    skill -- never a section slice, which the merged SKILL.md no longer carries
    -- and the digest still tells the two apart, so an artifact of one can never
    pass as the other.
    """
    assert {"CP-PARSE", "CP-0"} <= live_module_ids()
    parse = assemble_authority("CP-PARSE")
    zero = assemble_authority("CP-0")

    assert module_spec("CP-PARSE").skill_slug == module_spec("CP-0").skill_slug
    assert [name for name, _ in parse.files] == [name for name, _ in zero.files]
    assert parse.authority_digest != zero.authority_digest


def test_a_superseded_module_id_resolves_to_its_live_owner() -> None:
    """`_ALIASES`. CP-2C is an alternate command for CP-1A's workflow."""
    assert module_spec("CP-2C").module_id == "CP-1A"
    assert "CP-2C" not in live_module_ids()


def test_the_two_alias_sources_agree() -> None:
    """The catalog supersedes; the manifest also lists aliases. One or neither.

    They agree at build a43cb903 and the registry reads only the catalog. If a
    future bundle disagrees, that is a bundle question, not a silent divergence.
    """
    bundle = open_bundle()
    catalog = json.loads(
        bundle.read(
            "skills/cp-os-credit-os/references/CREDIT_OS_V_MODULE_CATALOG_v2.json"
        )
    )
    superseded = {
        alias: entry["absorbed_by"]
        for alias, entry in catalog["superseded_module_ids"].items()
    }
    assert superseded == bundle.aliases


def test_authority_never_carries_calculator_code() -> None:
    """A module asks for a calculation; it never supplies the code (SPEC 3)."""
    for module_id in sorted(live_module_ids()):
        for name, _ in assemble_authority(module_id).files:
            assert "/scripts/" not in name


def test_an_unrecognised_bundle_directory_is_not_authority() -> None:
    """An allowlist, because upstream rewrites its layout wholesale.

    One Deploy V release changed 175 files (`docs/DECISIONS.md` 6). A rule that
    named the directories to exclude would admit every directory the next
    release invents.
    """
    slug = "cp-model"
    covered = [
        "CANON_SHARED.md",
        "README.md",
        f"skills/{slug}/SKILL.md",
        f"skills/{slug}/references/CP-MODEL_RUNBOOK.md",
        f"skills/{slug}/scripts/build.py",
        f"skills/{slug}/agents/openai.yaml",
        f"skills/{slug}/bin/run.sh",
        "skills/cp-1-canonical-data-foundation/SKILL.md",
    ]
    assert reference_files(slug, covered) == (
        f"skills/{slug}/SKILL.md",
        f"skills/{slug}/references/CP-MODEL_RUNBOOK.md",
        "CANON_SHARED.md",
    )


def test_authority_digest_is_stable_and_binds_the_module_id() -> None:
    """Replay (invariant 10): same bundle, same module, same digest."""
    first = assemble_authority("CP-1")
    assert first.authority_digest == assemble_authority("CP-1").authority_digest
    assert first.authority_digest != assemble_authority("CP-2").authority_digest


def test_the_shared_canon_reaches_every_module() -> None:
    """23 of 25 SKILL.md tell the module to open `../../CANON_SHARED.md`.

    A module has no filesystem. If the host leaves it out, the instruction the
    bundle gives is one the module cannot follow.
    """
    for module_id in sorted(live_module_ids()):
        names = [name for name, _ in assemble_authority(module_id).files]
        assert "CANON_SHARED.md" in names


def test_the_authority_is_the_bytes_the_manifest_names() -> None:
    """`Authority.files` carries text, and it is the pinned text."""
    authority: Authority = assemble_authority("CP-1")
    bundle = open_bundle()
    for name, text in authority.files:
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        assert digest == bundle.digests[name]


def test_every_undelivered_reference_is_one_of_the_three_known_workbooks() -> None:
    """What the text allowlist withholds, named rather than silently dropped.

    Three `references/` entries are workbooks and no prompt can carry one. The
    assertion is over everything the allowlist excludes, not over `.xlsx`, so a
    reference arriving in a fourth format fails here rather than vanishing.
    """
    bundle = open_bundle()
    delivered = {
        name
        for module_id in live_module_ids()
        for name, _ in assemble_authority(module_id).files
    }
    covered = {
        name
        for name in bundle.digests
        if "/references/" in name and not name.startswith("skills/cp-os-")
    }
    assert sorted(covered - delivered) == [
        "skills/cp-3-relative-value-security-selection/references/"
        "REF_CP-3B_Portfolio_Constraints.xlsx",
        "skills/cp-3-relative-value-security-selection/references/"
        "REF_CP-3_Sector_RV.xlsx",
        "skills/cp-6-ic-debate-challenge/references/"
        "REF_CP-6A_Portfolio_Debate_Inputs.xlsx",
    ]
