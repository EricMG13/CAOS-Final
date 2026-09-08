#!/usr/bin/env python3
"""Command-line entry point for the CP-MODEL v3 clean-sheet generator.

A successful run writes the governed CP-MODEL workbook-export payload to
stdout. A failed run cannot satisfy that schema because no ``output_file``
exists; it instead writes a documented diagnostic payload with the locked
module identity, requested inputs, and blocking error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

sys.dont_write_bytecode = True

from cp_model_v3 import (
    BuildRequest,
    BuildResult,
    BundlePaths,
    CpModelV3Error,
    build_cp_model,
)


def _path(value: str) -> Path:
    return Path(value).expanduser().resolve()


def _success_payload(result: BuildResult) -> dict[str, object]:
    """Return the schema-governed payload for a published workbook."""

    return {
        "module_id": "CP-MODEL",
        "module_name": "CreditSnapshotModelWorkbook",
        "owned_object": "credit_snapshot_model_workbook",
        "schema_family": "Infrastructure",
        "output_class": "WORKBOOK_EXPORT",
        "runtime_output": {
            "quarter_periods": result.quarter_periods,
            "annual_periods": result.annual_periods,
            "analysis_columns": result.analysis_columns,
            "formulas_validated": result.formulas_validated,
            "semantic_checks": result.semantic_checks,
        },
        "renderer_version": result.renderer_version,
        "renderer_sha256": result.renderer_sha256,
        "calculation_engine": result.calculation_engine,
        "output_file": result.output.name,
        "source_manifest": result.source_manifest,
        "limitation_flags": result.limitation_flags,
        "qa_status": "Passed",
        "validation_warnings": result.validation_warnings,
        "downstream_consumers": [],
    }


def _blocked_payload(error: Exception, request: BuildRequest) -> dict[str, object]:
    """Return a non-governed diagnostic when no workbook can be published."""

    return {
        "status": "blocked",
        "module_id": "CP-MODEL",
        "module_name": "CreditSnapshotModelWorkbook",
        "owned_object": "credit_snapshot_model_workbook",
        "schema_family": "Infrastructure",
        "output_class": "WORKBOOK_EXPORT",
        "qa_status": "Blocked",
        "limitation_flags": ["WORKBOOK_NOT_EXPORTED"],
        "validation_warnings": [],
        "requested_output_dir": str(request.output_dir),
        "source_artifacts": [
            {
                "module_id": module_id,
                "artifact": path.name,
                "availability": "present" if path.is_file() else "missing",
            }
            for module_id, path in request.bundle.by_module().items()
        ],
        "error_type": type(error).__name__,
        "error": str(error),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build CP-MODEL v3 from validated canonical handoffs."
    )
    parser.add_argument("--cp1", required=True, type=_path)
    parser.add_argument("--cp1a", required=True, type=_path)
    parser.add_argument("--cp1b", required=True, type=_path)
    parser.add_argument("--cp2", required=True, type=_path)
    parser.add_argument("--cp2a", "--cp2b", dest="cp2b", required=True, type=_path,
                        help="CP-2A handoff; --cp2b is a legacy option alias")
    parser.add_argument("--cp2g", type=_path)
    parser.add_argument("--quarter-count", type=int)
    parser.add_argument("--soffice", type=_path)
    parser.add_argument("--output-dir", required=True, type=_path)
    arguments = parser.parse_args(argv)
    request = BuildRequest(
        bundle=BundlePaths(
            arguments.cp1,
            arguments.cp1a,
            arguments.cp1b,
            arguments.cp2,
            arguments.cp2b,
            arguments.cp2g,
        ),
        output_dir=arguments.output_dir,
        quarter_count=arguments.quarter_count,
        soffice_path=arguments.soffice,
    )
    try:
        result = build_cp_model(request)
    except (CpModelV3Error, OSError) as exc:
        print(json.dumps(_blocked_payload(exc, request), indent=2))
        return 2
    print(json.dumps(_success_payload(result), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
