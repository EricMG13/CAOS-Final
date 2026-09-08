"""Deep build interface and publication gate for CP-MODEL v3."""

from __future__ import annotations

import errno
import hashlib
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping, Sequence

from openpyxl import load_workbook

from .calculations import calculate
from .domain import (
    V3_CONTRACT_VERSION,
    BundlePaths,
    CpModelV3Error,
    build_ir,
    sha256,
)
from .workbook import FormulaExpectation, RenderMetadata, render_workbook


VISIBLE_SHEETS = ("Credit Snapshot", "Model", "KPIs")
CONTROL_SHEETS = ("_INPUTS", "_MAP", "_CHECKS", "_AUDIT")
FORMULA_ERROR_VALUES = {
    "#NULL!",
    "#DIV/0!",
    "#VALUE!",
    "#REF!",
    "#NAME?",
    "#NUM!",
    "#N/A",
}


@dataclass(frozen=True)
class BuildRequest:
    bundle: BundlePaths
    output_dir: Path
    quarter_count: int | None = None
    soffice_path: Path | None = None


@dataclass(frozen=True)
class BuildResult:
    output: Path
    quarter_periods: tuple[str, ...]
    annual_periods: tuple[str, ...]
    formulas_validated: int
    semantic_checks: int
    sha256: str
    renderer_version: str
    renderer_sha256: str
    calculation_engine: str
    analysis_columns: tuple[Mapping[str, object], ...] = ()
    source_manifest: tuple[Mapping[str, str], ...] = ()
    limitation_flags: tuple[str, ...] = ()
    validation_warnings: tuple[str, ...] = ()


def _renderer_hash() -> str:
    digest = hashlib.sha256()
    package = Path(__file__).resolve().parent
    dependencies = (
        *(package / name for name in ("domain.py", "calculations.py", "workbook.py", "builder.py")),
        package.parent / "validate_cp_model_inputs.py",
        package.parent / "validate_handoff.py",
    )
    for dependency in dependencies:
        digest.update(dependency.name.encode("utf-8"))
        digest.update(dependency.read_bytes())
    return digest.hexdigest()


def _resolve_soffice(explicit: Path | None) -> Path:
    if explicit is not None:
        candidate = explicit.expanduser().resolve()
        if not candidate.is_file():
            raise CpModelV3Error(f"calculation engine not found: {candidate}")
        return candidate
    discovered = shutil.which("soffice") or shutil.which("libreoffice")
    if discovered is None:
        raise CpModelV3Error(
            "LibreOffice/soffice is required to recalculate and validate formulas"
        )
    return Path(discovered).resolve()


def _engine_version(soffice: Path) -> str:
    try:
        completed = subprocess.run(
            [str(soffice), "--version"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise CpModelV3Error(f"cannot execute calculation engine: {exc}") from exc
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise CpModelV3Error(f"calculation engine version probe failed: {detail}")
    return completed.stdout.strip() or soffice.name


def _recalculate(
    soffice: Path,
    draft: Path,
    destination: Path,
    profile: Path,
) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    profile.mkdir(parents=True, exist_ok=True)
    command = [
        str(soffice),
        "--headless",
        f"-env:UserInstallation={profile.resolve().as_uri()}",
        "--convert-to",
        "xlsx",
        "--outdir",
        str(destination),
        str(draft),
    ]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=90,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise CpModelV3Error(f"workbook recalculation failed: {exc}") from exc
    recalculated = destination / draft.name
    if completed.returncode != 0 or not recalculated.is_file():
        detail = " | ".join(
            part.strip()
            for part in (completed.stdout, completed.stderr)
            if part.strip()
        )
        raise CpModelV3Error(
            f"workbook recalculation failed with status {completed.returncode}: {detail}"
        )
    return recalculated


def _numeric(value: object, expectation: FormulaExpectation) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CpModelV3Error(
            f"{expectation.sheet}!{expectation.cell}: expected numeric formula result, "
            f"found {value!r}"
        )
    result = Decimal(str(value))
    if not result.is_finite():
        raise CpModelV3Error(
            f"{expectation.sheet}!{expectation.cell}: formula result is not finite"
        )
    return result


def _is_formula_error(value: object) -> bool:
    return isinstance(value, str) and (
        value.startswith("#") or value.upper() in FORMULA_ERROR_VALUES
    )


def _index_expectations(
    expectations: Sequence[FormulaExpectation],
) -> dict[tuple[str, str], FormulaExpectation]:
    tracked: dict[tuple[str, str], FormulaExpectation] = {}
    duplicates: set[tuple[str, str]] = set()
    for expectation in expectations:
        key = (expectation.sheet, expectation.cell)
        if key in tracked:
            duplicates.add(key)
        else:
            tracked[key] = expectation
    if duplicates:
        raise CpModelV3Error(
            f"duplicate formula expectations: {sorted(duplicates)[:10]}"
        )
    return tracked


def _validate_sheet_registry(formula_book: Any, value_book: Any) -> None:
    expected_sheets = (*VISIBLE_SHEETS, *CONTROL_SHEETS)
    formula_sheets = tuple(formula_book.sheetnames)
    value_sheets = tuple(value_book.sheetnames)
    if formula_sheets != expected_sheets:
        raise CpModelV3Error(
            f"worksheet registry mismatch: expected {expected_sheets}, "
            f"found {formula_sheets}"
        )
    if value_sheets != expected_sheets:
        raise CpModelV3Error(
            f"cached-value worksheet registry mismatch: expected {expected_sheets}, "
            f"found {value_sheets}"
        )
    if any(formula_book[name].sheet_state != "visible" for name in VISIBLE_SHEETS):
        raise CpModelV3Error("all public sheets must be visible")
    if any(formula_book[name].sheet_state != "hidden" for name in CONTROL_SHEETS):
        raise CpModelV3Error("all control sheets must be hidden")


def _enumerate_formula_cells(
    formula_book: Any,
    value_book: Any,
) -> set[tuple[str, str]]:
    formula_cells: set[tuple[str, str]] = set()
    for ws in formula_book.worksheets:
        cached = value_book[ws.title]
        for row in ws.iter_rows():
            for cell in row:
                if cell.data_type == "f":
                    key = (ws.title, cell.coordinate)
                    formula_cells.add(key)
                    value = cached[cell.coordinate].value
                    if _is_formula_error(value):
                        raise CpModelV3Error(
                            f"{ws.title}!{cell.coordinate}: formula evaluated to {value}"
                        )
                    if value is None:
                        raise CpModelV3Error(
                            f"{ws.title}!{cell.coordinate}: formula has no calculated value"
                        )
    return formula_cells


def _validate_draft_formula_inventory(
    path: Path,
    expectations: Sequence[FormulaExpectation],
) -> None:
    tracked = _index_expectations(expectations)
    try:
        formula_book = load_workbook(path, data_only=False, read_only=True)
    except (OSError, ValueError) as exc:
        raise CpModelV3Error(f"draft workbook cannot be reopened: {exc}") from exc
    try:
        formula_cells = {
            (ws.title, cell.coordinate)
            for ws in formula_book.worksheets
            for row in ws.iter_rows()
            for cell in row
            if cell.data_type == "f"
        }
        _validate_formula_inventory(formula_cells, tracked)
    finally:
        formula_book.close()


def _validate_formula_inventory(
    formula_cells: set[tuple[str, str]],
    tracked: Mapping[tuple[str, str], FormulaExpectation],
) -> None:
    tracked_cells = set(tracked)
    untracked = formula_cells - tracked_cells
    missing = tracked_cells - formula_cells
    if untracked:
        raise CpModelV3Error(f"untracked formula cells: {sorted(untracked)[:10]}")
    if missing:
        raise CpModelV3Error(f"expected formula cells missing: {sorted(missing)[:10]}")


def _validate_formula_values(
    value_book: Any,
    tracked: Mapping[tuple[str, str], FormulaExpectation],
) -> None:
    for expectation in tracked.values():
        actual = value_book[expectation.sheet][expectation.cell].value
        if isinstance(expectation.expected, str):
            if actual != expectation.expected:
                raise CpModelV3Error(
                    f"{expectation.sheet}!{expectation.cell}: expected "
                    f"{expectation.expected!r}, found {actual!r}"
                )
            continue
        actual_number = _numeric(actual, expectation)
        if abs(actual_number - expectation.expected) > expectation.tolerance:
            raise CpModelV3Error(
                f"{expectation.sheet}!{expectation.cell}: formula mismatch; "
                f"expected {expectation.expected}, found {actual_number}"
            )


def _validate_recalculated(
    path: Path,
    expectations: Sequence[FormulaExpectation],
) -> None:
    tracked = _index_expectations(expectations)
    try:
        formula_book = load_workbook(path, data_only=False, read_only=True)
        try:
            value_book = load_workbook(path, data_only=True, read_only=True)
        except (OSError, ValueError):
            formula_book.close()
            raise
    except (OSError, ValueError) as exc:
        raise CpModelV3Error(
            f"recalculated workbook cannot be reopened: {exc}"
        ) from exc

    try:
        _validate_sheet_registry(formula_book, value_book)
        formula_cells = _enumerate_formula_cells(formula_book, value_book)
        _validate_formula_inventory(formula_cells, tracked)
        _validate_formula_values(value_book, tracked)
    finally:
        value_book.close()
        formula_book.close()


def _publish_exclusive(source: Path, destination: Path) -> None:
    try:
        os.link(source, destination)
        return
    except FileExistsError as exc:
        raise CpModelV3Error(f"refusing to overwrite existing output: {destination}") from exc
    except OSError as exc:
        if exc.errno not in {errno.EXDEV, errno.EPERM, errno.ENOTSUP}:
            raise CpModelV3Error(f"cannot publish workbook: {exc}") from exc

    descriptor: int | None = None
    try:
        descriptor = os.open(
            destination,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )
        with os.fdopen(descriptor, "wb") as output, source.open("rb") as input_file:
            descriptor = None
            shutil.copyfileobj(input_file, output)
            output.flush()
            os.fsync(output.fileno())
    except FileExistsError as exc:
        raise CpModelV3Error(f"refusing to overwrite existing output: {destination}") from exc
    except OSError as exc:
        if descriptor is not None:
            os.close(descriptor)
        destination.unlink(missing_ok=True)
        raise CpModelV3Error(f"cannot publish workbook: {exc}") from exc


def build_cp_model(request: BuildRequest) -> BuildResult:
    """Build, recalculate, validate, and exclusively publish CP-MODEL v3."""

    model = build_ir(request.bundle, quarter_count=request.quarter_count)
    calculations = calculate(model)
    soffice = _resolve_soffice(request.soffice_path)
    engine = _engine_version(soffice)
    renderer_hash = _renderer_hash()
    output_dir = request.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    first = model.quarters[0].period_id
    last = model.quarters[-1].period_id
    output_name = (
        f"{model.issuer_id}_CP-MODEL-v3_{first}-{last}_"
        f"{model.analysis_date:%Y%m%d}.xlsx"
    )
    output_path = output_dir / output_name
    if output_path.exists():
        raise CpModelV3Error(f"refusing to overwrite existing output: {output_path}")

    with tempfile.TemporaryDirectory(
        dir=output_dir,
        prefix=f".{model.issuer_id}-cp-model-v3-",
    ) as temporary:
        workspace = Path(temporary)
        draft = workspace / output_name
        render = render_workbook(
            model,
            calculations,
            RenderMetadata(renderer_hash, engine),
            draft,
        )
        _validate_draft_formula_inventory(draft, render.formulas)
        recalculated = _recalculate(
            soffice,
            draft,
            workspace / "recalculated",
            workspace / "libreoffice-profile",
        )
        _validate_recalculated(recalculated, render.formulas)
        _publish_exclusive(recalculated, output_path)

    if not output_path.is_file():
        raise CpModelV3Error("publication failed without creating an output")
    analysis_columns = tuple(
        {
            "column_id": column.column_id,
            "group": column.group,
            "label": column.label,
            "end_date": column.end_date.isoformat(),
            "fiscal_year": column.fiscal_year,
            "component_period_ids": column.component_period_ids,
            "balance_period_id": column.balance_period_id,
            "source_period_id": column.source_period_id,
            "comparison_column_id": column.comparison_column_id,
            "growth_comparison_column_id": column.comparison_column_id,
            "rollforward_column_id": column.rollforward_column_id,
            "forecast_period_id": column.forecast_period_id,
            "case": column.case,
            "day_count": column.day_count,
            "available": column.available,
        }
        for column in calculations.columns
    )
    return BuildResult(
        output=output_path,
        quarter_periods=tuple(period.period_id for period in model.quarters),
        annual_periods=tuple(period.period_id for period in model.annuals),
        formulas_validated=len(render.formulas),
        semantic_checks=len(calculations.checks),
        sha256=sha256(output_path),
        renderer_version=V3_CONTRACT_VERSION,
        renderer_sha256=renderer_hash,
        calculation_engine=engine,
        analysis_columns=analysis_columns,
        source_manifest=tuple(
            {
                "module_id": module_id,
                "artifact": model.source_paths[module_id].name,
                "sha256": model.source_hashes[module_id],
                "status": "ready",
            }
            for module_id in sorted(model.source_paths)
        ),
        limitation_flags=model.limitation_flags,
        validation_warnings=tuple(
            dict.fromkeys(
                (*model.upstream_validation_warnings, *model.validation_warnings)
            )
        ),
    )
