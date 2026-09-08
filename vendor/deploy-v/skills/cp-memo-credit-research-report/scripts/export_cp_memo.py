#!/usr/bin/env python3
"""CLI for CP-MEMO — CreditResearchReport."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True

SCRIPT_DIR = Path(__file__).resolve().parent
SKILLS_ROOT = SCRIPT_DIR.parents[1]
CP_OS_SKILL = SKILLS_ROOT / "cp-os-credit-os"
CP_OS_SCRIPTS = CP_OS_SKILL / "scripts"
if CP_OS_SCRIPTS.is_dir():
    sys.path.insert(0, str(CP_OS_SCRIPTS))
sys.path.insert(0, str(SCRIPT_DIR))

from credit_os.authority import sha256_file, verify  # noqa: E402
from cp_memo.inventory import inventory_snapshot  # noqa: E402


def _json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected one JSON object")
    return data


def _default_catalog() -> Path:
    return CP_OS_SKILL / "references" / "CREDIT_OS_V_MODULE_CATALOG_v2.json"


def _default_bundle() -> Path:
    return CP_OS_SKILL / "references" / "CREDIT_OS_V_AUTHORITY_BUNDLE_v2.json"


def _verified_authority_and_catalog(bundle_path: Path, catalog_path: Path) -> tuple[str, dict]:
    verified = verify(
        bundle_path,
        search_roots=[CP_OS_SCRIPTS, CP_OS_SKILL, SKILLS_ROOT, SKILLS_ROOT.parent],
    )
    bundle = _json(bundle_path)
    declared = bundle.get("components", {}).get("resolved_catalog", {}).get("sha256")
    if sha256_file(catalog_path) != declared:
        raise ValueError("module catalog digest does not match the verified authority bundle")
    return str(verified["authority_bundle_sha256"]), _json(catalog_path)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=_default_catalog())
    parser.add_argument("--bundle", type=Path, default=_default_bundle())
    sub = parser.add_subparsers(dest="command", required=True)
    inventory = sub.add_parser("inventory")
    inventory.add_argument("snapshot", type=Path)
    inventory.add_argument("--run-id")
    draft = sub.add_parser("draft")
    draft.add_argument("snapshot", type=Path)
    draft.add_argument("--output-dir", type=Path, required=True)
    draft.add_argument("--publication-date", required=True)
    draft.add_argument("--run-id")
    draft.add_argument("--confidentiality", default="Confidential")
    publish = sub.add_parser("publish")
    publish.add_argument("session", type=Path)
    publish.add_argument("--visual-approved", action="store_true")
    args = parser.parse_args(argv)
    authority, catalog = _verified_authority_and_catalog(args.bundle, args.catalog)
    if args.command == "inventory":
        result = inventory_snapshot(_json(args.snapshot), catalog, authority, args.run_id)
        payload = result.public_dict()
        code = 0 if result.status in {"READY", "SELECT_RUN"} else 2
    elif args.command == "draft":
        from cp_memo.builder import build_draft
        result = build_draft(_json(args.snapshot), catalog, authority, args.output_dir, args.publication_date, args.confidentiality, args.run_id)
        payload = result.as_dict()
        code = 0 if result.status == "DRAFT_READY" else 2
    else:
        from cp_memo.builder import publish_draft
        result = publish_draft(args.session, args.visual_approved)
        payload = result.as_dict()
        code = 0 if result.status == "PUBLISHED" else 2
    print(json.dumps(payload, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
