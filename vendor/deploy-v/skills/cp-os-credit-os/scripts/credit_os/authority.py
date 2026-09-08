"""Authority-bundle verification for the packaged runtime.

The runtime reads only validated authorities. It never parses routing prose, a
command guide, or an attached registry. Startup fails closed on a missing,
altered, unknown-version or internally inconsistent bundle, because a control
plane that silently accepts a changed route is worse than one that refuses.

Standard library only, no repository imports.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

SUPPORTED_SCHEMA_VERSIONS = frozenset({"1.0"})


class AuthorityError(Exception):
    """The authority bundle could not be trusted."""


def canonical(payload: object) -> bytes:
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(64 * 1024):
            hasher.update(chunk)
    return hasher.hexdigest()


def load_bundle(path: Path) -> dict:
    try:
        bundle = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise AuthorityError(f"authority bundle unreadable: {exc.strerror}") from exc
    except ValueError as exc:
        raise AuthorityError(f"authority bundle is not valid JSON: {exc}") from exc

    if not isinstance(bundle, dict):
        raise AuthorityError("authority bundle must be a JSON object")
    version = bundle.get("schema_version")
    if version not in SUPPORTED_SCHEMA_VERSIONS:
        raise AuthorityError(f"unsupported authority bundle version: {version!r}")

    components = bundle.get("components")
    if not isinstance(components, dict):
        raise AuthorityError("authority bundle components must be a JSON object")
    for name, component in components.items():
        if not isinstance(name, str) or not isinstance(component, dict):
            raise AuthorityError("every authority component must be a named object")
        path = component.get("path")
        digest = component.get("sha256")
        if not isinstance(path, str) or not path:
            raise AuthorityError(f"{name}: component path must be a non-empty string")
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            raise AuthorityError(f"{name}: component sha256 is malformed")
        if "runtime_required" in component and not isinstance(
            component["runtime_required"], bool
        ):
            raise AuthorityError(f"{name}: runtime_required must be boolean")

    recomputed = hashlib.sha256(canonical(components)).hexdigest()
    if recomputed != bundle.get("authority_bundle_sha256"):
        raise AuthorityError(
            "authority bundle digest does not match its own components; "
            "it was edited after generation"
        )
    return bundle


def verify(bundle_path: Path, *, search_roots: list[Path]) -> dict:
    """Verify every deployed runtime component still hashes as declared.

    `search_roots` lets the same bundle verify in the repository (paths relative
    to the repo root) and in the installed package (files flattened beside the
    bundle). Nothing else about resolution differs.

    Build-only components remain pinned in the bundle digest for provenance and
    CI drift detection, but are deliberately absent from the installed package.
    Older bundles have no ``runtime_required`` field, so they retain the previous
    fail-closed behaviour and require every component.
    """
    bundle = load_bundle(bundle_path)
    results: dict[str, str] = {}
    problems: list[str] = []

    for name, component in sorted(bundle["components"].items()):
        if not component.get("runtime_required", True):
            continue
        declared = component["sha256"]
        candidates = [root / component["path"] for root in search_roots]
        candidates.append(bundle_path.parent / Path(component["path"]).name)

        found = next((c for c in candidates if c.is_file()), None)
        if found is None:
            problems.append(f"{name}: component file not found")
            continue
        actual = sha256_file(found)
        if actual != declared:
            problems.append(f"{name}: digest changed since the bundle was generated")
            continue
        results[name] = actual

    if problems:
        raise AuthorityError("; ".join(problems))
    return {
        "authority_bundle_sha256": bundle["authority_bundle_sha256"],
        "target_profile": bundle.get("target_profile"),
        "components_verified": len(results),
        "components_pinned": len(bundle["components"]),
    }
