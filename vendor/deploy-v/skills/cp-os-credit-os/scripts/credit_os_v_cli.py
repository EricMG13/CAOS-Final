#!/usr/bin/env python3
"""Read-only CP-OS navigation CLI copied into generated packages."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping


HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from credit_os.authority import AuthorityError, load_bundle  # noqa: E402
from credit_os_v.navigation import (  # noqa: E402
    NavigationError,
    NavigationState,
    navigate,
)


BUNDLE_NAME = "CREDIT_OS_V_AUTHORITY_BUNDLE_v2.json"
BUNDLE_CANDIDATES = (
    HERE / "references" / BUNDLE_NAME,
    HERE.parent / "references" / BUNDLE_NAME,
    HERE.parent / "Co-Pilot Agents" / "CP-OS" / "references" / "deploy_v" / BUNDLE_NAME,
)
SEARCH_ROOTS = (HERE, HERE.parent, HERE.parent.parent, HERE.parent.parent.parent)
STATE_FIELDS = frozenset({
    "status", "context_key", "layer_index", "selection_fingerprint",
    "selection_count",
})
STATE_STATUSES = frozenset({
    "NO_CP0", "SELECT_RUN", "SHOW_LAYER", "FOLDER_ERROR", "STOPPED",
})
HEX_DIGEST_LENGTH = 64
JSON_OVERHEAD_BYTES = 1024 * 1024
FOLDER_ERROR_MAX_BYTES = 500
CONSUMED_JSON_COMPONENTS = frozenset({"resolved_catalog", "runtime_limits"})


class InputLimitExceeded(ValueError):
    """The serialized request or artifact snapshot exceeded a governed limit."""


class _BoundedTextReader:
    def __init__(self, stream: Any, maximum: int) -> None:
        self.stream = stream
        self.maximum = maximum
        self.spent = 0

    def read(self, size: int = -1) -> str:
        chunks: list[str] = []
        remaining = size
        while remaining != 0:
            request = 65536 if remaining < 0 else min(65536, remaining)
            chunk = self.stream.read(request)
            if not chunk:
                break
            self.spent += len(chunk.encode("utf-8"))
            if self.spent > self.maximum:
                raise InputLimitExceeded(
                    f"JSON input exceeds the bounded {self.maximum}-byte parser limit"
                )
            chunks.append(chunk)
            if remaining > 0:
                remaining -= len(chunk)
        return "".join(chunks)


def emit(payload: Mapping[str, object], *, success: bool) -> int:
    json.dump(
        dict(payload), sys.stdout, indent=2, sort_keys=True, ensure_ascii=False
    )
    sys.stdout.write("\n")
    return 0 if success else 1


class StructuredArgumentParser(argparse.ArgumentParser):
    """Keep command-shape failures on the same JSON error surface."""

    def error(self, message: str) -> None:
        raise SystemExit(emit(
            {"status": "BAD_INPUT_OR_AUTHORITY", "detail": message[:500]},
            success=False,
        ))


def _find(candidates: tuple[Path, ...], label: str) -> Path:
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise AuthorityError(f"{label} not found beside the V runtime")


@dataclass(frozen=True)
class VerifiedAuthority:
    bundle_path: Path
    bundle: Mapping[str, object]
    component_bytes: Mapping[str, bytes]
    result: Mapping[str, object]


def _read_component_bytes(path: Path) -> bytes:
    """Single read seam: hashing and parsing both consume these exact bytes."""
    return path.read_bytes()


def _component_path(bundle_path: Path, component: Mapping[str, object]) -> Path:
    declared_path = component["path"]
    assert isinstance(declared_path, str)
    candidates = [root / declared_path for root in SEARCH_ROOTS]
    candidates.append(bundle_path.parent / Path(declared_path).name)
    found = next((candidate for candidate in candidates if candidate.is_file()), None)
    if found is None:
        raise AuthorityError("runtime authority component file not found")
    return found


def verified_authority() -> VerifiedAuthority:
    """Verify and retain one immutable authority/component byte snapshot."""
    bundle_path = _find(BUNDLE_CANDIDATES, BUNDLE_NAME)
    bundle = load_bundle(bundle_path)
    component_bytes: dict[str, bytes] = {}
    problems: list[str] = []
    components_verified = 0
    for name, component in sorted(bundle["components"].items()):
        if not component.get("runtime_required", True):
            continue
        try:
            path = _component_path(bundle_path, component)
            body = _read_component_bytes(path)
        except (AuthorityError, OSError) as exc:
            problems.append(f"{name}: {exc}")
            continue
        observed_digest = hashlib.sha256(body).hexdigest()
        if observed_digest != component["sha256"]:
            problems.append(f"{name}: digest changed since the bundle was generated")
            continue
        components_verified += 1
        if name in CONSUMED_JSON_COMPONENTS:
            component_bytes[name] = body
    if problems:
        raise AuthorityError("; ".join(problems))
    result = {
        "authority_bundle_sha256": bundle["authority_bundle_sha256"],
        "components_verified": components_verified,
        "components_pinned": len(bundle["components"]),
    }
    return VerifiedAuthority(
        bundle_path=bundle_path,
        bundle=MappingProxyType(bundle),
        component_bytes=MappingProxyType(component_bytes),
        result=MappingProxyType(result),
    )


def _component_json(authority: VerifiedAuthority, name: str) -> dict[str, object]:
    body = authority.component_bytes.get(name)
    if body is None:
        raise AuthorityError(f"verified authority has no {name} bytes")
    try:
        parsed = json.loads(body)
    except (UnicodeError, ValueError) as exc:
        raise AuthorityError(f"{name} is not valid UTF-8 JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise AuthorityError(f"{name} must be a JSON object")
    return parsed


def verified_catalog(authority: VerifiedAuthority) -> dict[str, object]:
    catalog = _component_json(authority, "resolved_catalog")
    if not isinstance(catalog, dict) or not isinstance(catalog.get("navigation"), dict):
        raise AuthorityError("V catalog has no navigation authority")
    return catalog


def verified_limits(authority: VerifiedAuthority) -> dict[str, object]:
    document = _component_json(authority, "runtime_limits")
    limits = document.get("limits")
    if not isinstance(limits, dict):
        raise AuthorityError("runtime limits component has no limits object")
    return limits


def _digest_or_none(value: object, label: str) -> str | None:
    if value is None:
        return None
    if (
        not isinstance(value, str)
        or len(value) != HEX_DIGEST_LENGTH
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise TypeError(f"state {label} must be a lowercase SHA-256 digest or null")
    return value


def _navigation_state(raw: object) -> NavigationState | None:
    if raw is None:
        return None
    if not isinstance(raw, dict) or set(raw) != STATE_FIELDS:
        raise TypeError(
            "'state' must contain exactly status, context_key, layer_index, "
            "selection_fingerprint, and selection_count"
        )
    status = raw["status"]
    if not isinstance(status, str) or status not in STATE_STATUSES:
        raise TypeError("state status is not supported")
    layer_index = raw["layer_index"]
    if isinstance(layer_index, bool) or not isinstance(layer_index, int) or layer_index < 0:
        raise TypeError("state layer_index must be a non-negative integer")
    context_key = _digest_or_none(raw["context_key"], "context_key")
    fingerprint = _digest_or_none(
        raw["selection_fingerprint"], "selection_fingerprint"
    )
    selection_count = raw["selection_count"]
    if selection_count is not None and (
        isinstance(selection_count, bool)
        or not isinstance(selection_count, int)
        or selection_count < 1
    ):
        raise TypeError("state selection_count must be a positive integer or null")

    if status == "SHOW_LAYER":
        valid_shape = (
            context_key is not None
            and fingerprint is None
            and selection_count is None
        )
    elif status == "SELECT_RUN":
        valid_shape = (
            context_key is None
            and layer_index == 0
            and fingerprint is not None
            and selection_count is not None
        )
    else:
        valid_shape = (
            context_key is None
            and layer_index == 0
            and fingerprint is None
            and selection_count is None
        )
    if not valid_shape:
        raise TypeError(f"state fields are inconsistent with status {status}")
    return NavigationState(
        status=status,
        context_key=context_key,
        layer_index=layer_index,
        selection_fingerprint=fingerprint,
        selection_count=selection_count,
    )


def _input_payload(limits: Mapping[str, object]) -> tuple[
    dict[str, str], NavigationState | None, int | None, str | None
]:
    parser_limit = int(limits["bytes_per_refresh"]) + JSON_OVERHEAD_BYTES
    payload = json.load(_BoundedTextReader(sys.stdin, parser_limit))
    if not isinstance(payload, dict):
        raise TypeError("input must be a JSON object")
    allowed = {"artifacts", "state", "response", "folder_error"}
    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise TypeError("input contains unsupported fields: " + ", ".join(unknown))
    if "artifacts" not in payload or not isinstance(payload["artifacts"], dict):
        raise TypeError("'artifacts' must be a fresh object snapshot")
    if len(payload["artifacts"]) > int(limits["entries_per_run_folder"]):
        raise InputLimitExceeded(
            f"artifact count exceeds the {limits['entries_per_run_folder']}-entry refresh limit"
        )

    artifacts: dict[str, str] = {}
    total_bytes = 0
    single_limit = int(limits["markdown_or_control_file_bytes"])
    total_limit = int(limits["bytes_per_refresh"])
    for name, body in payload["artifacts"].items():
        if not isinstance(name, str) or not isinstance(body, str):
            raise TypeError("artifact names and bodies must be strings")
        body_bytes = len(body.encode("utf-8"))
        if body_bytes > single_limit:
            raise InputLimitExceeded(
                f"artifact body exceeds the {single_limit}-byte Markdown limit"
            )
        total_bytes += body_bytes
        if total_bytes > total_limit:
            raise InputLimitExceeded(
                f"artifact bodies exceed the {total_limit}-byte refresh limit"
            )
        artifacts[name] = body

    response = payload.get("response")
    if response is not None and (
        isinstance(response, bool) or not isinstance(response, int)
    ):
        raise TypeError("'response' must be an integer or null")
    folder_error = payload.get("folder_error")
    if folder_error is not None:
        if not isinstance(folder_error, str) or not folder_error.strip():
            raise TypeError("'folder_error' must be a non-empty string or null")
        if len(folder_error.encode("utf-8")) > FOLDER_ERROR_MAX_BYTES:
            raise InputLimitExceeded(
                f"folder_error exceeds the {FOLDER_ERROR_MAX_BYTES}-byte limit"
            )
        if artifacts:
            raise TypeError("'folder_error' requires an empty fresh artifacts snapshot")
        folder_error = folder_error.strip()
    return (
        artifacts,
        _navigation_state(payload.get("state")),
        response,
        folder_error,
    )


def cmd_verify(_args: argparse.Namespace) -> int:
    try:
        authority = verified_authority()
    except (AuthorityError, OSError, ValueError, KeyError, TypeError) as exc:
        return emit(
            {"status": "AUTHORITY_CHANGED", "detail": str(exc)[:500]},
            success=False,
        )
    return emit({"status": "OK", **authority.result}, success=True)


def cmd_navigate(_args: argparse.Namespace) -> int:
    try:
        authority = verified_authority()
        catalog = verified_catalog(authority)
        limits = verified_limits(authority)
    except (AuthorityError, OSError, ValueError, KeyError, TypeError) as exc:
        return emit(
            {"status": "AUTHORITY_CHANGED", "detail": str(exc)[:500]},
            success=False,
        )
    try:
        artifacts, state, response, folder_error = _input_payload(limits)
        result = navigate(
            catalog,
            artifacts,
            state=state,
            response=response,
            folder_error=folder_error,
            authority_digest=str(authority.result["authority_bundle_sha256"]),
        )
    except (
        InputLimitExceeded,
        NavigationError,
        OSError,
        UnicodeError,
        ValueError,
        KeyError,
        TypeError,
        json.JSONDecodeError,
    ) as exc:
        return emit(
            {"status": "BAD_INPUT_OR_AUTHORITY", "detail": str(exc)[:500]},
            success=False,
        )
    return emit(
        {
            "status": result.status,
            "card": result.card,
            "state": result.state.as_dict(),
        },
        success=True,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = StructuredArgumentParser(prog="credit_os_v_cli")
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("verify-authorities").set_defaults(func=cmd_verify)
    subcommands.add_parser("navigate").set_defaults(func=cmd_navigate)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
