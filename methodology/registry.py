"""The registry: the only seam between the host and the bundle (SYSTEM_SPEC 3).

What is live comes from the catalog's own `modules` list, never from folder
layout. The bundle ships 25 skill folders and the catalog declares 24 modules;
the extra folder is CP-OS, the credit OS itself, whose references include the
routing catalog. Deriving the live set from folders would let a module be handed
the map that routes it.

The manifest then says what that module's bytes are, and the host declares one
carve-out: CP-PARSE, superseded upstream and runnable here, carrying the whole
CP-0 skill (`docs/DECISIONS.md` 5). Never a section slice of `SKILL.md` -- the
merged skill no longer carries the marker that would be sliced on.

Which files a module receives is an allowlist, not a denylist. One Deploy V
release changed 175 files (`docs/DECISIONS.md` 6); a rule naming what to exclude
would admit every directory the next release invents.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from methodology.bundle import BUNDLE_ROOT, Bundle, open_bundle
from server.refusals import Refusal, RefusalCode

CATALOG = "skills/cp-os-credit-os/references/CREDIT_OS_V_MODULE_CATALOG_v2.json"

# 23 of 25 SKILL.md tell the module to open `../../CANON_SHARED.md` to resolve a
# named ambiguity. A module has no filesystem, so the host includes it or the
# instruction is one the module cannot follow.
SHARED_CANON = "CANON_SHARED.md"

# The bundle's text formats. Three `references/` entries are `.xlsx` workbooks,
# which no prompt can carry -- see the known-gaps ledger in CLAUDE.md.
TEXT_SUFFIXES = frozenset({"md", "txt", "json"})

# The host carve-out `_ALIASES` does not get to override: a superseded id that
# is a live module here, and the folder whose authority it carries.
_CARVE_OUTS = {"CP-PARSE": "CP-0"}


@dataclass(frozen=True, slots=True)
class ModuleSpec:
    """One live module: its identity, its folder, and what it is given."""

    module_id: str
    skill_slug: str
    reference_files: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Authority:
    """The verified text a module runs under, and the digest that binds it."""

    module_id: str
    build_id: str
    files: tuple[tuple[str, str], ...]
    authority_digest: str


def reference_files(skill_slug: str, covered: Iterable[str]) -> tuple[str, ...]:
    """The files a module is given, in the order it is given them.

    `SKILL.md`, then its own `references/`, then the shared canon. Nothing else:
    `scripts/` is calculator code the host selects and never puts in a prompt,
    and an unrecognised directory is not authority until somebody says it is.
    """
    folder = f"skills/{skill_slug}/"
    skill = f"{folder}SKILL.md"
    references = f"{folder}references/"
    names = sorted(covered)
    return (
        *(name for name in names if name == skill),
        *(name for name in names if name.startswith(references) and _is_text(name)),
        SHARED_CANON,
    )


def _is_text(name: str) -> bool:
    """Authority reaches a module as prompt text, so only text qualifies."""
    return name.rsplit(".", 1)[-1].casefold() in TEXT_SUFFIXES


def live_module_ids(*, root: Path = BUNDLE_ROOT) -> frozenset[str]:
    """Every module that can be routed and run under this build."""
    bundle = open_bundle(root)
    return frozenset(_live(bundle, _catalog(bundle)))


def module_spec(module_id: str, *, root: Path = BUNDLE_ROOT) -> ModuleSpec:
    """The spec for a live module, resolving a superseded id to its owner."""
    return _spec(open_bundle(root), module_id)


def assemble_authority(module_id: str, *, root: Path = BUNDLE_ROOT) -> Authority:
    """Read every authority file for a module, verifying each on the bytes."""
    bundle = open_bundle(root)
    spec = _spec(bundle, module_id)
    return Authority(
        module_id=spec.module_id,
        build_id=bundle.build_id,
        files=tuple((name, bundle.read(name)) for name in spec.reference_files),
        authority_digest=_authority_digest(bundle, spec),
    )


def _catalog(bundle: Bundle) -> dict[str, Any]:
    loaded: dict[str, Any] = json.loads(bundle.read(CATALOG))
    return loaded


def _live(bundle: Bundle, catalog: dict[str, Any]) -> dict[str, str]:
    """Module id to skill folder, for everything runnable under this build."""
    try:
        live = {
            str(module["module_id"]): bundle.folders[str(module["module_id"])]
            for module in catalog["modules"]
        }
        live.update(
            {alias: bundle.folders[owner] for alias, owner in _CARVE_OUTS.items()}
        )
    except KeyError:
        # A catalog module with no skill folder is a bundle we cannot execute.
        raise Refusal(RefusalCode.METHODOLOGY_BUNDLE_INVALID) from None
    return live


def _aliases(catalog: dict[str, Any]) -> dict[str, str]:
    return {
        str(alias): str(entry["absorbed_by"])
        for alias, entry in catalog["superseded_module_ids"].items()
        if alias not in _CARVE_OUTS
    }


def _spec(bundle: Bundle, module_id: str) -> ModuleSpec:
    catalog = _catalog(bundle)
    resolved = _aliases(catalog).get(module_id, module_id)
    slug = _live(bundle, catalog).get(resolved)
    if slug is None:
        raise Refusal(RefusalCode.METHODOLOGY_MODULE_UNKNOWN)
    return ModuleSpec(resolved, slug, reference_files(slug, bundle.digests))


def _authority_digest(bundle: Bundle, spec: ModuleSpec) -> str:
    """Same bundle, same module, same digest -- on any machine (invariant 10).

    The module id is in the payload, so CP-0 and CP-PARSE are told apart despite
    holding byte-identical authority.
    """
    payload = {
        "build_id": bundle.build_id,
        "module_id": spec.module_id,
        "files": [[name, bundle.digests[name]] for name in spec.reference_files],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
