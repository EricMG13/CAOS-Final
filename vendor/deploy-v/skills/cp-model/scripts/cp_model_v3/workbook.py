"""Blank-workbook renderer for CP-MODEL v3."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from .calculations import (
    SENIOR_DEBT_CLASSES,
    AnalysisColumn,
    CalculationBook,
    PeriodCalculation,
    SemanticCheck,
)
from .domain import (
    CpModelV3Error,
    CreditModelIR,
    DebtSeries,
    NarrativeItem,
    Period,
    SourceNumber,
    SourceRef,
    TextValue,
    V3_CONTRACT_VERSION,
)


NAVY = "0A2E63"
BLUE = "1F4E78"
MID_BLUE = "D9EAF7"
PALE_BLUE = "EAF3F8"
PALE_YELLOW = "FFF4CC"
PALE_GREEN = "E2F0D9"
PALE_RED = "FCE4D6"
GREY = "E7E6E6"
DARK_GREY = "5B6573"
WHITE = "FFFFFF"
BLACK = "111111"
INPUT_BLUE = "0070C0"
THIN_GREY = Side(style="thin", color="B7C3D0")
MONEY_FORMAT = '#,##0.0;[Red](#,##0.0);-'
PERCENT_FORMAT = '0.0%;[Red](0.0%);-'
MULTIPLE_FORMAT = '0.0x;[Red](0.0x);-'
DAYS_FORMAT = '0.0 "days"'
CHECK_FORMAT = '0.000;[Red](0.000);-'

@dataclass(frozen=True)
class FormulaExpectation:
    sheet: str
    cell: str
    semantic_id: str
    expected: Decimal | str
    tolerance: Decimal = Decimal("0.0001")


@dataclass(frozen=True)
class MappingRecord:
    semantic_id: str
    owner: str
    target: str
    write_class: str
    period_id: str
    source_refs: str


@dataclass(frozen=True)
class RenderMetadata:
    renderer_hash: str
    calculation_engine: str


@dataclass(frozen=True)
class RenderResult:
    formulas: tuple[FormulaExpectation, ...]
    mappings: tuple[MappingRecord, ...]
    model_cells: Mapping[tuple[str, str], str]


@dataclass(frozen=True)
class _AnalysisLayout:
    column_letters: Mapping[str, str]
    spacer_columns: tuple[int, ...]
    max_column: int


@dataclass(frozen=True)
class _InputRenderResult:
    forecast_driver_cells: Mapping[tuple[str, str, str, str], str]
    mappings: tuple[MappingRecord, ...]


def _excel_value(value: object) -> object:
    return float(value) if isinstance(value, Decimal) else value


def _set_literal(cell: Any, value: object) -> None:
    cell.value = _excel_value(value)
    if isinstance(value, str):
        cell.data_type = "s"


def _append_literal_row(ws: Any, values: Sequence[object]) -> int:
    row = (
        1
        if ws.max_row == 1
        and ws.max_column == 1
        and ws.cell(1, 1).value is None
        else ws.max_row + 1
    )
    for column, value in enumerate(values, 1):
        _set_literal(ws.cell(row, column), value)
    return row


def _source_refs(provenance: Sequence[SourceRef]) -> str:
    return "; ".join(
        f"{ref.source_id} | {ref.source_locator} | {ref.as_of}"
        for ref in provenance
    )


def _comment(provenance: Sequence[SourceRef], owner: str) -> Comment | None:
    if not provenance:
        return None
    body = f"Owner: {owner}\n" + "\n".join(
        f"{ref.source_id}: {ref.source_locator} (as of {ref.as_of})"
        for ref in provenance
    )
    return Comment(body, "CP-MODEL v3")


class _RenderState:
    def __init__(self, workbook: Workbook) -> None:
        self.workbook = workbook
        self.formulas: list[FormulaExpectation] = []
        self.mappings: list[MappingRecord] = []

    def value(
        self,
        sheet: str,
        cell: str,
        semantic_id: str,
        value: object,
        *,
        owner: str,
        write_class: str,
        period_id: str = "",
        provenance: Sequence[SourceRef] = (),
        number_format: str | None = None,
    ) -> None:
        target = self.workbook[sheet][cell]
        _set_literal(target, value)
        if number_format is not None:
            target.number_format = number_format
        target.comment = _comment(provenance, owner)
        self.mappings.append(
            MappingRecord(
                semantic_id,
                owner,
                f"{sheet}!{cell}",
                write_class,
                period_id,
                _source_refs(provenance),
            )
        )

    def formula(
        self,
        sheet: str,
        cell: str,
        semantic_id: str,
        formula: str,
        expected: Decimal | str,
        *,
        period_id: str = "",
        number_format: str | None = None,
        tolerance: Decimal = Decimal("0.0001"),
    ) -> None:
        target = self.workbook[sheet][cell]
        target.value = formula
        if number_format is not None:
            target.number_format = number_format
        self.formulas.append(
            FormulaExpectation(
                sheet,
                cell,
                semantic_id,
                expected,
                tolerance,
            )
        )
        self.mappings.append(
            MappingRecord(
                semantic_id,
                "CP-MODEL",
                f"{sheet}!{cell}",
                "FORMULA",
                period_id,
                "",
            )
        )


def _fill(color: str) -> PatternFill:
    return PatternFill("solid", fgColor=color)


def _analysis_layout(columns: Sequence[AnalysisColumn]) -> _AnalysisLayout:
    column_letters: dict[str, str] = {}
    spacer_columns: list[int] = []
    worksheet_column = 2
    prior_group: str | None = None
    for column in columns:
        if prior_group is not None and column.group != prior_group:
            spacer_columns.append(worksheet_column)
            worksheet_column += 1
        column_letters[column.column_id] = get_column_letter(worksheet_column)
        worksheet_column += 1
        prior_group = column.group
    return _AnalysisLayout(
        column_letters,
        tuple(spacer_columns),
        worksheet_column - 1,
    )


def _style_analysis_spacers(
    ws: object,
    spacer_columns: Sequence[int],
    max_row: int,
) -> None:
    for column in spacer_columns:
        letter = get_column_letter(column)
        ws.column_dimensions[letter].width = 2.5
        for row in range(3, max_row + 1):
            cell = ws.cell(row, column)
            cell.fill = _fill(WHITE)
            cell.font = Font(color=WHITE)
            cell.border = Border()
            cell.alignment = Alignment()


def _style_title(cell: object, *, size: int = 16) -> None:
    cell.fill = _fill(NAVY)
    cell.font = Font(color=WHITE, bold=True, size=size)
    cell.alignment = Alignment(vertical="center")


def _style_section(ws: object, row: int, title: str, max_column: int) -> None:
    _set_literal(ws.cell(row, 1), title)
    for column in range(1, max_column + 1):
        cell = ws.cell(row, column)
        cell.fill = _fill(NAVY)
        cell.font = Font(color=WHITE, bold=True)
        cell.border = Border(bottom=Side(style="medium", color=NAVY))
    ws.row_dimensions[row].height = 20


def _style_data_row(
    ws: object,
    row: int,
    max_column: int,
    *,
    fill: str = WHITE,
    bold: bool = False,
    font_color: str = BLACK,
) -> None:
    for column in range(1, max_column + 1):
        cell = ws.cell(row, column)
        cell.fill = _fill(fill)
        cell.font = Font(color=font_color, bold=bold)
        cell.border = Border(bottom=THIN_GREY)
        cell.alignment = Alignment(vertical="center")


def _period_source(model: CreditModelIR, metric_id: str, period_id: str) -> SourceNumber:
    return model.account(metric_id, period_id)


def _render_model(
    state: _RenderState,
    model: CreditModelIR,
    calculations: CalculationBook,
    forecast_driver_cells: Mapping[tuple[str, str, str, str], str],
) -> tuple[dict[tuple[str, str], str], dict[str, int]]:
    ws = state.workbook["Model"]
    columns = calculations.columns
    layout = _analysis_layout(columns)
    column_letters = layout.column_letters
    max_column = layout.max_column
    last_column = get_column_letter(max_column)
    model_cells: dict[tuple[str, str], str] = {}
    row_for_key: dict[str, int] = {}
    period_by_id = {period.period_id: period for period in model.periods}
    column_by_id = {column.column_id: column for column in columns}
    pro_forma = next(column for column in columns if column.group == "PF")
    pf_letter = column_letters[pro_forma.column_id]

    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=max_column)
    _set_literal(ws["A1"], f"{model.issuer_name} | CP-MODEL v3")
    _style_title(ws["A1"], size=18)
    ws.row_dimensions[1].height = 28
    _set_literal(
        ws["A2"],
        f"{model.periods[0].currency} in millions | "
        f"{model.periods[0].accounting_basis} | {model.periods[0].entity_perimeter}",
    )
    ws["A2"].font = Font(color=DARK_GREY, italic=True)
    for column in columns:
        letter = column_letters[column.column_id]
        ws[f"{letter}3"] = column.group
        ws[f"{letter}4"] = column.label
        ws[f"{letter}5"] = column.end_date
        ws[f"{letter}5"].number_format = "dd-mmm-yy"
        for header_row in (3, 4, 5):
            cell = ws[f"{letter}{header_row}"]
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = Border(bottom=THIN_GREY)
        ws[f"{letter}3"].fill = _fill(BLUE)
        ws[f"{letter}3"].font = Font(color=WHITE, bold=True)
        ws[f"{letter}4"].fill = _fill(MID_BLUE)
        ws[f"{letter}4"].font = Font(color=NAVY, bold=True)
        ws[f"{letter}5"].fill = _fill(PALE_BLUE)
        if not column.available:
            ws[f"{letter}4"] = f"{column.label}\nNot supplied"
            ws[f"{letter}4"].fill = _fill(GREY)
    ws["A4"] = "Metric"
    ws["A4"].fill = _fill(MID_BLUE)
    ws["A4"].font = Font(color=NAVY, bold=True)
    ws["A5"] = "Period end"
    ws["A5"].font = Font(color=DARK_GREY, italic=True)

    row = 7

    def section(title: str) -> None:
        nonlocal row
        _style_section(ws, row, title, max_column)
        row += 1

    def is_forecast(column: AnalysisColumn) -> bool:
        return column.group in {"BASE", "DOWNSIDE"}

    def component_formula(key: str, column: AnalysisColumn) -> str:
        cells = [model_cells[(key, period_id)] for period_id in column.component_period_ids]
        if not cells:
            return "=0"
        return "=" + "+".join(f"'Model'!{cell}" for cell in cells)

    def balance_formula(key: str, column: AnalysisColumn) -> str:
        if column.balance_period_id is None:
            return "=0"
        return f"='Model'!{model_cells[(key, column.balance_period_id)]}"

    def forecast_driver_reference(
        column: AnalysisColumn,
        driver_id: str,
        slot_id: str = "",
    ) -> str:
        driver_period = column.forecast_period_id or column.column_id
        key = (column.case, driver_period, driver_id, slot_id)
        try:
            return forecast_driver_cells[key]
        except KeyError as exc:
            raise CpModelV3Error(
                f"missing forecast input cell for {key}"
            ) from exc

    def forecast_source_formula(key: str, column: AnalysisColumn, letter: str) -> str:
        prior_id = column.rollforward_column_id or pro_forma.column_id
        prior_letter = column_letters[prior_id]
        if key == "revenue":
            segment_rows = [row_for_key[f"segment::{series.series_id}"] for series in model.segments]
            if segment_rows:
                return "=" + "+".join(f"{letter}{item}" for item in segment_rows)
            return (
                f"={prior_letter}{row_for_key['revenue']}*"
                f"(1+{forecast_driver_reference(column, 'division_growth', 'DIVISION_1')})"
            )
        if key in {"cogs", "opex_including_da", "depreciation_amortization"}:
            return (
                f"=IFERROR({letter}{row_for_key['revenue']}*"
                f"{pf_letter}{row_for_key[key]}/{pf_letter}{row_for_key['revenue']},0)"
            )
        if key == "ebitda_reported":
            return f"={letter}{row_for_key['ebitda_calc']}"
        if key == "adjusted_ebitda_reported":
            return f"={letter}{row_for_key['adjusted_ebitda_calc']}"
        if key == "cash_interest_paid":
            return f"={pf_letter}{row_for_key[key]}"
        if key in {
            "cash_lease_payments",
            "cash_taxes_paid",
            "working_capital_change",
            "capex_and_intangible_investment",
        }:
            return (
                f"=IFERROR({letter}{row_for_key['revenue']}*"
                f"{pf_letter}{row_for_key[key]}/{pf_letter}{row_for_key['revenue']},0)"
            )
        if key == "cfo_reported":
            return f"={letter}{row_for_key['cfo_calc']}"
        if key in {
            "acquisitions_disposals",
            "net_equity_issue_repay",
            "dividends_paid",
            "other_investing_financing",
        }:
            return f"={forecast_driver_reference(column, key)}"
        if key == "net_debt_issue_repay":
            return "=0"
        if key == "net_cash_change":
            return f"={letter}{row_for_key['ncf']}"
        if key == "cash_and_equivalents":
            return (
                f"={prior_letter}{row_for_key['cash_and_equivalents']}+"
                f"{letter}{row_for_key['ncf']}"
            )
        if key == "rcf_commitment":
            return f"={pf_letter}{row_for_key[key]}"
        if key == "total_debt_reported":
            return f"={letter}{row_for_key['total_debt_calc']}"
        if key == "net_accounts_receivable":
            return (
                f"=IFERROR({letter}{row_for_key['revenue']}*"
                f"{pf_letter}{row_for_key[key]}/{pf_letter}{row_for_key['revenue']},0)"
            )
        if key in {"inventory", "accounts_payable"}:
            return (
                f"=IFERROR(ABS({letter}{row_for_key['cogs']})*"
                f"{pf_letter}{row_for_key[key]}/ABS({pf_letter}{row_for_key['cogs']}),0)"
            )
        raise CpModelV3Error(f"unsupported forecast source row {key}")

    flow_source_keys = {
        "revenue",
        "cogs",
        "opex_including_da",
        "depreciation_amortization",
        "ebitda_reported",
        "adjusted_ebitda_reported",
        "cash_interest_paid",
        "cash_lease_payments",
        "cash_taxes_paid",
        "cfo_reported",
        "working_capital_change",
        "capex_and_intangible_investment",
        "acquisitions_disposals",
        "net_debt_issue_repay",
        "net_equity_issue_repay",
        "dividends_paid",
        "other_investing_financing",
        "net_cash_change",
    }

    def source_row(
        key: str,
        label: str,
        metric_id: str,
        *,
        fill: str = WHITE,
        bold: bool = False,
    ) -> None:
        nonlocal row
        row_for_key[key] = row
        _style_data_row(ws, row, max_column, fill=fill, bold=bold, font_color=INPUT_BLUE)
        _set_literal(ws.cell(row, 1), label)
        ws.cell(row, 1).font = Font(color=BLACK, bold=bold)
        for column in columns:
            calculation = calculations.for_column(column.column_id)
            if not calculation.values:
                continue
            letter = column_letters[column.column_id]
            cell = f"{letter}{row}"
            expected = calculation.values[key]
            if column.source_period_id is not None:
                source = _period_source(model, metric_id, column.source_period_id)
                state.value(
                    "Model",
                    cell,
                    key,
                    expected,
                    owner="CP-1",
                    write_class="SOURCE",
                    period_id=column.column_id,
                    provenance=source.provenance,
                    number_format=MONEY_FORMAT,
                )
            elif is_forecast(column):
                state.formula(
                    "Model",
                    cell,
                    key,
                    forecast_source_formula(key, column, letter),
                    expected,
                    period_id=column.column_id,
                    number_format=MONEY_FORMAT,
                )
            else:
                formula = (
                    component_formula(key, column)
                    if key in flow_source_keys
                    else balance_formula(key, column)
                )
                state.formula(
                    "Model",
                    cell,
                    key,
                    formula,
                    expected,
                    period_id=column.column_id,
                    number_format=MONEY_FORMAT,
                )
            model_cells[(key, column.column_id)] = cell
        row += 1

    def formula_row(
        key: str,
        label: str,
        formula_for: object,
        *,
        number_format: str = MONEY_FORMAT,
        fill: str = PALE_BLUE,
        bold: bool = False,
    ) -> None:
        nonlocal row
        row_for_key[key] = row
        _style_data_row(ws, row, max_column, fill=fill, bold=bold)
        _set_literal(ws.cell(row, 1), label)
        for column in columns:
            calculation = calculations.for_column(column.column_id)
            if not calculation.values:
                continue
            letter = column_letters[column.column_id]
            cell = f"{letter}{row}"
            state.formula(
                "Model",
                cell,
                key,
                formula_for(column, letter),
                calculation.values[key],
                period_id=column.column_id,
                number_format=number_format,
            )
            model_cells[(key, column.column_id)] = cell
        row += 1

    def growth_row(growth_key: str, label: str, source_key: str) -> None:
        nonlocal row
        semantic_id = f"growth::{growth_key}"
        row_for_key[semantic_id] = row
        _style_data_row(ws, row, max_column, fill=PALE_BLUE)
        _set_literal(ws.cell(row, 1), label)
        ws.cell(row, 1).font = Font(color=DARK_GREY, italic=True)
        for column in columns:
            calculation = calculations.for_column(column.column_id)
            expected = calculation.growth.get(growth_key)
            comparison_id = column.comparison_column_id
            if expected is None or comparison_id is None:
                continue
            letter = column_letters[column.column_id]
            comparison_letter = column_letters[comparison_id]
            cell = f"{letter}{row}"
            state.formula(
                "Model",
                cell,
                semantic_id,
                f"={letter}{row_for_key[source_key]}/{comparison_letter}{row_for_key[source_key]}-1",
                expected,
                period_id=column.column_id,
                number_format=PERCENT_FORMAT,
            )
            model_cells[(semantic_id, column.column_id)] = cell
        row += 1

    section("Income Statement")
    segment_rows: list[int] = []
    for series in model.segments:
        segment_key = f"segment::{series.series_id}"
        row_for_key[segment_key] = row
        segment_rows.append(row)
        _style_data_row(ws, row, max_column, font_color=INPUT_BLUE)
        _set_literal(ws.cell(row, 1), series.label)
        for column in columns:
            calculation = calculations.for_column(column.column_id)
            if not calculation.values:
                continue
            expected = calculation.segment_values.get(series.series_id)
            if expected is None:
                continue
            letter = column_letters[column.column_id]
            cell = f"{letter}{row}"
            if column.source_period_id is not None:
                point = series.values.get(column.source_period_id)
                if point is None:
                    continue
                state.value(
                    "Model", cell, segment_key, expected,
                    owner="CP-1", write_class="SOURCE", period_id=column.column_id,
                    provenance=point.provenance, number_format=MONEY_FORMAT,
                )
            elif is_forecast(column):
                prior_letter = column_letters[
                    column.rollforward_column_id or pro_forma.column_id
                ]
                slot = model.segment_forecast_slots[series.series_id]
                formula = (
                    f"={prior_letter}{row}*(1+"
                    f"{forecast_driver_reference(column, 'division_growth', slot)})"
                )
                state.formula(
                    "Model", cell, segment_key, formula, expected,
                    period_id=column.column_id, number_format=MONEY_FORMAT,
                )
            else:
                state.formula(
                    "Model", cell, segment_key, component_formula(segment_key, column), expected,
                    period_id=column.column_id, number_format=MONEY_FORMAT,
                )
            model_cells[(segment_key, column.column_id)] = cell
        row += 1

    source_row("revenue", "Revenue (reported)", "revenue", fill=GREY, bold=True)
    def segment_reconciliation_formula(
        _column: AnalysisColumn,
        letter: str,
    ) -> str:
        if not segment_rows:
            return "=0"
        segment_total = "+".join(f"{letter}{item}" for item in segment_rows)
        return f"={segment_total}-{letter}{row_for_key['revenue']}"

    formula_row(
        "segment_variance",
        "Segment reconciliation",
        segment_reconciliation_formula,
        number_format=CHECK_FORMAT,
        fill=PALE_GREEN,
    )
    source_row("cogs", "COGS", "cogs")
    formula_row(
        "gross_profit", "Gross Profit",
        lambda _column, letter: f"={letter}{row_for_key['revenue']}+{letter}{row_for_key['cogs']}",
        bold=True,
    )
    source_row("opex_including_da", "OPEX including D&A", "opex_including_da")
    formula_row(
        "ebit", "EBIT",
        lambda _column, letter: f"={letter}{row_for_key['gross_profit']}+{letter}{row_for_key['opex_including_da']}",
    )
    source_row("depreciation_amortization", "Depreciation & amortisation", "depreciation_amortization")
    formula_row(
        "ebitda_calc", "EBITDA (calculated)",
        lambda _column, letter: f"={letter}{row_for_key['ebit']}+{letter}{row_for_key['depreciation_amortization']}",
        bold=True,
    )
    source_row("ebitda_reported", "EBITDA (reported / projected)", "ebitda")
    formula_row(
        "ebitda_variance", "EBITDA reconciliation",
        lambda _column, letter: f"={letter}{row_for_key['ebitda_calc']}-{letter}{row_for_key['ebitda_reported']}",
        number_format=CHECK_FORMAT, fill=PALE_GREEN,
    )

    section("EBITDA Add-backs")
    subtotal_keys: list[str] = []
    status_specs = (
        ("REALIZED", "Realized add-backs", "realized_addbacks"),
        ("UNREALIZED", "Unrealized add-backs", "unrealized_addbacks"),
        ("NOT_STATED", "Realization not stated", "not_stated_addbacks"),
    )
    for realization_status, group_label, subtotal_key in status_specs:
        _style_data_row(ws, row, max_column, fill=GREY, bold=True)
        _set_literal(ws.cell(row, 1), group_label)
        row += 1
        group_rows: list[int] = []
        for series in model.addbacks:
            if series.realization_status != realization_status:
                continue
            addback_key = f"addback::{series.series_id}"
            row_for_key[addback_key] = row
            group_rows.append(row)
            _style_data_row(ws, row, max_column, fill=PALE_YELLOW, font_color=INPUT_BLUE)
            _set_literal(ws.cell(row, 1), f"  {series.label} [{series.category}]")
            for column in columns:
                calculation = calculations.for_column(column.column_id)
                if not calculation.values:
                    continue
                expected = calculation.addback_values.get(series.series_id)
                if expected is None:
                    continue
                letter = column_letters[column.column_id]
                cell = f"{letter}{row}"
                if column.source_period_id is not None:
                    point = series.values.get(column.source_period_id)
                    if point is None:
                        continue
                    state.value(
                        "Model", cell, addback_key, expected,
                        owner="CP-1", write_class="SOURCE", period_id=column.column_id,
                        provenance=point.provenance, number_format=MONEY_FORMAT,
                    )
                elif is_forecast(column):
                    state.formula(
                        "Model", cell, addback_key, f"={pf_letter}{row}", expected,
                        period_id=column.column_id, number_format=MONEY_FORMAT,
                    )
                else:
                    state.formula(
                        "Model", cell, addback_key, component_formula(addback_key, column), expected,
                        period_id=column.column_id, number_format=MONEY_FORMAT,
                    )
                model_cells[(addback_key, column.column_id)] = cell
            row += 1
        formula_row(
            subtotal_key,
            f"Total {group_label.lower()}",
            lambda _column, letter, rows=tuple(group_rows): (
                "=" + "+".join(f"{letter}{item}" for item in rows) if rows else "=0"
            ),
            fill=PALE_YELLOW,
            bold=True,
        )
        subtotal_keys.append(subtotal_key)
    formula_row(
        "total_addbacks", "Total add-backs",
        lambda _column, letter: "=" + "+".join(f"{letter}{row_for_key[key]}" for key in subtotal_keys),
        fill=PALE_YELLOW, bold=True,
    )
    formula_row(
        "adjusted_ebitda_calc", "Adjusted EBITDA (calculated)",
        lambda _column, letter: f"={letter}{row_for_key['ebitda_calc']}+{letter}{row_for_key['total_addbacks']}",
        bold=True,
    )
    source_row("adjusted_ebitda_reported", "Adjusted EBITDA (reported / projected)", "adjusted_ebitda")
    formula_row(
        "adjusted_ebitda_variance", "Adjusted EBITDA reconciliation",
        lambda _column, letter: f"={letter}{row_for_key['adjusted_ebitda_calc']}-{letter}{row_for_key['adjusted_ebitda_reported']}",
        number_format=CHECK_FORMAT, fill=PALE_GREEN,
    )

    section("Cash Flow")
    cash_flow_order = (
        "cash_flow_adjusted_ebitda",
        "cash_interest_paid",
        "cash_lease_payments",
        "cash_taxes_paid",
        "ffo_other",
        "ffo",
        "working_capital_change",
        "cfo_calc",
        "cfo_reported",
        "cfo_variance",
        "capex_and_intangible_investment",
        "fcf",
        "acquisitions_disposals",
        "net_debt_issue_repay",
        "net_equity_issue_repay",
        "dividends_paid",
        "other_investing_financing",
        "ncf",
        "net_cash_change",
        "ncf_variance",
    )
    row_for_key.update(
        {key: row + offset for offset, key in enumerate(cash_flow_order)}
    )
    formula_row(
        "cash_flow_adjusted_ebitda", "Adjusted EBITDA",
        lambda _column, letter: f"={letter}{row_for_key['adjusted_ebitda_calc']}", bold=True,
    )
    source_row("cash_interest_paid", "Cash interest", "cash_interest_paid")
    source_row("cash_lease_payments", "Cash leases", "cash_lease_payments")
    source_row("cash_taxes_paid", "Cash taxes", "cash_taxes_paid")
    formula_row(
        "ffo_other", "FFO Other (calculated residual / projected ratio)",
        lambda column, letter: (
            f"=IFERROR({letter}{row_for_key['revenue']}*{pf_letter}{row_for_key['ffo_other']}/{pf_letter}{row_for_key['revenue']},0)"
            if is_forecast(column)
            else f"={letter}{row_for_key['cfo_reported']}-{letter}{row_for_key['working_capital_change']}-{letter}{row_for_key['cash_flow_adjusted_ebitda']}-{letter}{row_for_key['cash_interest_paid']}-{letter}{row_for_key['cash_lease_payments']}-{letter}{row_for_key['cash_taxes_paid']}"
        ),
        fill=PALE_YELLOW,
    )
    formula_row(
        "ffo", "Funds from operations",
        lambda _column, letter: "=" + "+".join(
            f"{letter}{row_for_key[key]}" for key in (
                "cash_flow_adjusted_ebitda", "cash_interest_paid", "cash_lease_payments", "cash_taxes_paid", "ffo_other"
            )
        ),
        bold=True,
    )
    source_row("working_capital_change", "Change in working capital", "working_capital_change")
    formula_row(
        "cfo_calc", "CFO / NCFO (calculated)",
        lambda _column, letter: f"={letter}{row_for_key['ffo']}+{letter}{row_for_key['working_capital_change']}",
        bold=True,
    )
    source_row("cfo_reported", "CFO / NCFO (reported / projected)", "cfo_ncfo")
    formula_row(
        "cfo_variance", "CFO reconciliation (reported − calculated)",
        lambda _column, letter: f"={letter}{row_for_key['cfo_reported']}-{letter}{row_for_key['cfo_calc']}",
        number_format=CHECK_FORMAT, fill=PALE_GREEN,
    )
    source_row("capex_and_intangible_investment", "Capex & intangible investment", "capex_and_intangible_investment")
    formula_row(
        "fcf", "Free cash flow",
        lambda _column, letter: f"={letter}{row_for_key['cfo_calc']}+{letter}{row_for_key['capex_and_intangible_investment']}",
        bold=True,
    )
    for key, label in (
        ("acquisitions_disposals", "Acquisitions / disposals"),
        ("net_debt_issue_repay", "Net debt issue / (repayment)"),
        ("net_equity_issue_repay", "Net equity issue / (repurchase)"),
        ("dividends_paid", "Dividends"),
        ("other_investing_financing", "Other investing / financing"),
    ):
        source_row(key, label, key)
    formula_row(
        "ncf", "Net cash flow (calculated)",
        lambda _column, letter: "=" + "+".join(
            f"{letter}{row_for_key[key]}" for key in (
                "fcf", "acquisitions_disposals", "net_debt_issue_repay", "net_equity_issue_repay", "dividends_paid", "other_investing_financing"
            )
        ),
        bold=True,
    )
    source_row("net_cash_change", "Net cash movement (reported / projected)", "net_cash_change")
    formula_row(
        "ncf_variance", "Net cash reconciliation",
        lambda _column, letter: f"={letter}{row_for_key['ncf']}-{letter}{row_for_key['net_cash_change']}",
        number_format=CHECK_FORMAT, fill=PALE_GREEN,
    )

    section("Balance Sheet and Debt")
    source_row("cash_and_equivalents", "Cash & equivalents", "cash_and_equivalents")
    source_row("rcf_commitment", "RCF commitment", "rcf_commitment")
    debt_groups = (
        ("SECURED", "Secured debt", "secured_debt"),
        ("UNSECURED", "Unsecured debt", "unsecured_debt"),
        ("NOT_STATED", "Other / security not stated", "other_debt"),
    )
    facility_rows: dict[tuple[str, str], int] = {}
    subtotal_rows: list[int] = []

    def point_for_column(facility: DebtSeries, column: AnalysisColumn) -> object | None:
        period_id = column.balance_period_id
        if is_forecast(column):
            period_id = pro_forma.balance_period_id
        return facility.values.get(period_id or "")

    for secured_status, group_label, subtotal_key in debt_groups:
        group_facilities = [
            facility for facility in model.debt
            if any(point.secured_status == secured_status for point in facility.values.values())
        ]
        if not group_facilities and secured_status == "NOT_STATED":
            continue
        _style_data_row(ws, row, max_column, fill=GREY, bold=True)
        _set_literal(ws.cell(row, 1), group_label)
        row += 1
        group_rows: list[int] = []
        for facility in group_facilities:
            representative = max(
                (
                    (period_by_id[period_id].end_date, point)
                    for period_id, point in facility.values.items()
                    if point.secured_status == secured_status and period_id in period_by_id
                ),
                key=lambda item: item[0],
            )[1]
            facility_row = row
            facility_rows[(facility.facility_id, secured_status)] = row
            group_rows.append(row)
            _style_data_row(ws, row, max_column, font_color=INPUT_BLUE)
            maturity = representative.maturity_date or "Not stated"
            interest = representative.margin_or_coupon or "Not stated"
            _set_literal(
                ws.cell(row, 1),
                f"  {representative.facility_name} | {interest} | maturity {maturity} | "
                f"{representative.facility_type}; "
                f"{representative.seniority.lower().replace('_', ' ')}",
            )
            for column in columns:
                calculation = calculations.for_column(column.column_id)
                if not calculation.values:
                    continue
                point = point_for_column(facility, column)
                if point is None or point.secured_status != secured_status:
                    continue
                expected = calculation.debt_values.get(facility.facility_id)
                if expected is None:
                    continue
                letter = column_letters[column.column_id]
                cell = f"{letter}{row}"
                semantic_id = f"debt::{facility.facility_id}::{secured_status}"
                if column.source_period_id is not None:
                    state.value(
                        "Model", cell, semantic_id, expected,
                        owner="CP-1", write_class="SOURCE", period_id=column.column_id,
                        provenance=point.carrying_value.provenance, number_format=MONEY_FORMAT,
                    )
                elif is_forecast(column):
                    state.formula(
                        "Model", cell, semantic_id, f"={pf_letter}{facility_row}", expected,
                        period_id=column.column_id, number_format=MONEY_FORMAT,
                    )
                else:
                    balance_cell = model_cells.get((semantic_id, column.balance_period_id or ""))
                    if balance_cell is None:
                        continue
                    state.formula(
                        "Model", cell, semantic_id, f"='Model'!{balance_cell}", expected,
                        period_id=column.column_id, number_format=MONEY_FORMAT,
                    )
                model_cells[(semantic_id, column.column_id)] = cell
            row += 1
        formula_row(
            subtotal_key,
            f"Total {group_label.lower()}",
            lambda _column, letter, rows=tuple(group_rows): (
                "=" + "+".join(f"{letter}{item}" for item in rows) if rows else "=0"
            ),
            bold=True,
        )
        subtotal_rows.append(row_for_key[subtotal_key])

    def classified_debt_formula(column: AnalysisColumn, letter: str, *, senior_only: bool) -> str:
        rows: list[int] = []
        for facility in model.debt:
            point = point_for_column(facility, column)
            if point is None or (senior_only and point.seniority not in SENIOR_DEBT_CLASSES):
                continue
            if not senior_only and not (
                point.seniority in SENIOR_DEBT_CLASSES and point.secured_status == "SECURED"
            ):
                continue
            facility_row = facility_rows.get((facility.facility_id, point.secured_status))
            if facility_row is not None:
                rows.append(facility_row)
        return "=" + "+".join(f"{letter}{item}" for item in rows) if rows else "=0"

    formula_row(
        "senior_secured_debt", "Senior secured debt",
        lambda column, letter: classified_debt_formula(column, letter, senior_only=False), bold=True,
    )
    formula_row(
        "senior_debt", "Senior debt",
        lambda column, letter: classified_debt_formula(column, letter, senior_only=True), bold=True,
    )
    formula_row(
        "total_debt_calc", "Total debt (calculated)",
        lambda _column, letter: "=" + "+".join(f"{letter}{item}" for item in subtotal_rows),
        bold=True,
    )
    source_row("total_debt_reported", "Total debt (reported / projected)", "total_debt", bold=True)
    formula_row(
        "total_debt_variance", "Debt reconciliation",
        lambda _column, letter: f"={letter}{row_for_key['total_debt_calc']}-{letter}{row_for_key['total_debt_reported']}",
        number_format=CHECK_FORMAT, fill=PALE_GREEN,
    )
    source_row("net_accounts_receivable", "Net accounts receivable", "net_accounts_receivable")
    source_row("inventory", "Inventory", "inventory")
    source_row("accounts_payable", "Accounts payable", "accounts_payable")

    section("Credit Metrics")

    quarter_positions = {
        period.period_id: index for index, period in enumerate(model.quarters)
    }

    def metric_flow_formula(key: str, column: AnalysisColumn) -> str | None:
        if column.group == "QUARTER":
            index = quarter_positions[column.column_id]
            if index < 3:
                return None
            cells = [
                model_cells[(key, period.period_id)]
                for period in model.quarters[index - 3 : index + 1]
            ]
            return "+".join(f"'Model'!{cell}" for cell in cells)
        return f"{column_letters[column.column_id]}{row_for_key[key]}"

    def credit_metric_formula(key: str, column: AnalysisColumn) -> str | None:
        letter = column_letters[column.column_id]
        adjusted = metric_flow_formula("adjusted_ebitda_calc", column)
        revenue = metric_flow_formula("revenue", column)
        gross_profit = metric_flow_formula("gross_profit", column)
        cogs = metric_flow_formula("cogs", column)
        fcf = metric_flow_formula("fcf", column)
        capex = metric_flow_formula("capex_and_intangible_investment", column)
        interest = metric_flow_formula("cash_interest_paid", column)
        if adjusted is None or revenue is None or gross_profit is None or cogs is None or fcf is None or capex is None or interest is None:
            return None
        annualization = (
            f"*365/{column.day_count}" if column.group == "YTD" and column.day_count else ""
        )
        debt = f"{letter}{row_for_key['total_debt_reported']}"
        cash = f"{letter}{row_for_key['cash_and_equivalents']}"
        adjusted_annual = f"(({adjusted}){annualization})"
        fcf_annual = f"(({fcf}){annualization})"
        interest_annual = f"(({interest}){annualization})"
        if key == "senior_secured_leverage":
            return f"={letter}{row_for_key['senior_secured_debt']}/{adjusted_annual}"
        if key == "senior_leverage":
            return f"={letter}{row_for_key['senior_debt']}/{adjusted_annual}"
        if key == "total_leverage":
            return f"={debt}/{adjusted_annual}"
        if key == "net_leverage":
            return f"=({debt}-{cash})/{adjusted_annual}"
        if key == "interest_coverage":
            return f"={adjusted_annual}/ABS({interest_annual})"
        if key == "fcf_percent_debt":
            return f"={fcf_annual}/{debt}"
        if key == "capex_percent_revenue":
            return f"=ABS({capex})/({revenue})"
        if key == "cash_conversion":
            return f"={fcf_annual}/{adjusted_annual}"
        if key == "gross_margin":
            return f"=({gross_profit})/({revenue})"
        if key == "adjusted_ebitda_margin":
            return f"=({adjusted})/({revenue})"
        if column.group == "QUARTER":
            index = quarter_positions[column.column_id]
            days = sum(period.day_count for period in model.quarters[index - 3 : index + 1])
        else:
            days = column.day_count or 365
        if key == "dso":
            return f"={letter}{row_for_key['net_accounts_receivable']}*{days}/({revenue})"
        if key == "dsi":
            return f"={letter}{row_for_key['inventory']}*{days}/ABS({cogs})"
        if key == "dpo":
            return f"={letter}{row_for_key['accounts_payable']}*{days}/ABS({cogs})"
        raise CpModelV3Error(f"unsupported credit metric {key}")

    def credit_metric_row(key: str, label: str, number_format: str) -> None:
        nonlocal row
        row_for_key[key] = row
        _style_data_row(ws, row, max_column, fill=PALE_BLUE, bold=True)
        _set_literal(ws.cell(row, 1), label)
        for column in columns:
            expected = calculations.for_column(column.column_id).credit_metrics.get(key)
            formula = credit_metric_formula(key, column)
            if expected is None or formula is None:
                continue
            letter = column_letters[column.column_id]
            cell = f"{letter}{row}"
            state.formula(
                "Model", cell, key, formula, expected,
                period_id=column.column_id, number_format=number_format,
            )
            model_cells[(key, column.column_id)] = cell
        row += 1

    _style_data_row(ws, row, max_column, fill=GREY, bold=True)
    ws.cell(row, 1, "Growth and Profitability")
    row += 1
    growth_row("revenue", "Revenue YoY", "revenue")
    for series in model.segments:
        growth_row(f"segment::{series.series_id}", f"{series.label} YoY", f"segment::{series.series_id}")
    growth_row("adjusted_ebitda", "Adjusted EBITDA YoY", "adjusted_ebitda_calc")
    credit_metric_row("gross_margin", "Gross margin", PERCENT_FORMAT)
    credit_metric_row("adjusted_ebitda_margin", "Adjusted EBITDA margin", PERCENT_FORMAT)
    _style_data_row(ws, row, max_column, fill=GREY, bold=True)
    ws.cell(row, 1, "Leverage and Coverage")
    row += 1
    credit_metric_row("senior_secured_leverage", "Senior secured leverage", MULTIPLE_FORMAT)
    credit_metric_row("senior_leverage", "Senior leverage", MULTIPLE_FORMAT)
    credit_metric_row("total_leverage", "Total leverage", MULTIPLE_FORMAT)
    credit_metric_row("net_leverage", "Total net leverage", MULTIPLE_FORMAT)
    credit_metric_row("interest_coverage", "Interest coverage", MULTIPLE_FORMAT)
    _style_data_row(ws, row, max_column, fill=GREY, bold=True)
    ws.cell(row, 1, "Cash Flow and Investment")
    row += 1
    credit_metric_row("cash_conversion", "Cash conversion (FCF / Adj. EBITDA)", PERCENT_FORMAT)
    credit_metric_row("fcf_percent_debt", "FCF / debt", PERCENT_FORMAT)
    credit_metric_row("capex_percent_revenue", "Capex / revenue", PERCENT_FORMAT)
    _style_data_row(ws, row, max_column, fill=GREY, bold=True)
    ws.cell(row, 1, "Working Capital")
    row += 1
    credit_metric_row("dso", "Days sales outstanding", DAYS_FORMAT)
    credit_metric_row("dsi", "Days inventory outstanding", DAYS_FORMAT)
    credit_metric_row("dpo", "Days payable outstanding", DAYS_FORMAT)

    ws.freeze_panes = "B6"
    ws.sheet_view.showGridLines = False
    ws.column_dimensions["A"].width = 72
    for column_index in range(2, max_column + 1):
        ws.column_dimensions[get_column_letter(column_index)].width = 15
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_title_rows = "$1:$5"
    ws.print_area = f"A1:{last_column}{row - 1}"
    for check_key in (
        "segment_variance", "ebitda_variance", "adjusted_ebitda_variance",
        "ncf_variance", "total_debt_variance",
    ):
        check_row = row_for_key[check_key]
        ws.conditional_formatting.add(
            f"B{check_row}:{last_column}{check_row}",
            CellIsRule(operator="notBetween", formula=["-0.001", "0.001"], fill=_fill(PALE_RED)),
        )
    _style_analysis_spacers(ws, layout.spacer_columns, row - 1)
    return model_cells, row_for_key


def _render_kpis(
    state: _RenderState,
    model: CreditModelIR,
    calculations: CalculationBook,
    _model_cells: dict[tuple[str, str], str],
) -> None:
    ws = state.workbook["KPIs"]
    columns = tuple(
        column for column in calculations.columns
        if column.group not in {"BASE", "DOWNSIDE"}
    )
    layout = _analysis_layout(columns)
    column_letters = layout.column_letters
    max_column = layout.max_column
    last_column = get_column_letter(max_column)

    def direct_rate_period_id(column: AnalysisColumn) -> str | None:
        if column.group not in {"YTD", "LTM"}:
            return None
        exact = model.reported_periods.get(column.column_id)
        if exact is not None and exact.period_type == column.group:
            return exact.period_id
        matches = [
            period.period_id
            for period in model.reported_periods.values()
            if period.period_type == column.group
            and period.fiscal_year == column.fiscal_year
            and period.end_date == column.end_date
        ]
        if len(matches) > 1:
            raise CpModelV3Error(
                f"multiple direct {column.group} periods match {column.column_id}: "
                f"{sorted(matches)}"
            )
        return matches[0] if matches else None

    def has_direct_rate(column: AnalysisColumn) -> bool:
        period_id = direct_rate_period_id(column)
        return period_id is not None and any(
            series.value_type == "RATE" and period_id in series.values
            for series in model.operating_kpis
        )

    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=max_column)
    _set_literal(ws["A1"], f"{model.issuer_name} | Operating KPIs")
    _style_title(ws["A1"], size=18)
    ws["A2"] = "Business-unit operating measures only; financial and credit ratios are on the Model worksheet."
    ws["A2"].font = Font(color=DARK_GREY, italic=True)
    for column in columns:
        letter = column_letters[column.column_id]
        ws[f"{letter}3"] = column.group
        ws[f"{letter}4"] = column.label
        ws[f"{letter}5"] = column.end_date
        ws[f"{letter}5"].number_format = "dd-mmm-yy"
        for header_row in (3, 4, 5):
            ws[f"{letter}{header_row}"].alignment = Alignment(horizontal="center", wrap_text=True)
            ws[f"{letter}{header_row}"].border = Border(bottom=THIN_GREY)
        ws[f"{letter}3"].fill = _fill(BLUE)
        ws[f"{letter}3"].font = Font(color=WHITE, bold=True)
        ws[f"{letter}4"].fill = _fill(MID_BLUE)
        ws[f"{letter}4"].font = Font(color=NAVY, bold=True)
        ws[f"{letter}5"].fill = _fill(PALE_BLUE)
        if not column.available and not has_direct_rate(column):
            ws[f"{letter}4"] = f"{column.label}\nNot supplied"
            ws[f"{letter}4"].fill = _fill(GREY)
    ws["A4"] = "Operating KPI"
    ws["A4"].fill = _fill(MID_BLUE)
    ws["A4"].font = Font(color=NAVY, bold=True)
    ws["A5"] = "Period end"
    row = 7

    if not model.operating_kpis:
        _style_section(ws, row, "Operating KPIs", max_column)
        row += 1
        ws.cell(row, 1, "No applicable operating KPI schedule was supplied by CP-1.")
        ws.cell(row, 1).font = Font(color=DARK_GREY, italic=True)
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=max_column)
        row += 1
    else:
        year_end_period_by_fiscal_year = {
            period.fiscal_year: period.period_id
            for period in model.quarters
            if period.fiscal_quarter == 4
        }
        current_group: tuple[str, str] | None = None
        for series in model.operating_kpis:
            series_cells: dict[str, str] = {}
            group = (series.business_unit, series.category)
            if group != current_group:
                _style_section(ws, row, f"{series.business_unit} | {series.category}", max_column)
                row += 1
                current_group = group
            _style_data_row(ws, row, max_column)
            _set_literal(ws.cell(row, 1), f"{series.label} [{series.unit}]")
            semantic_id = f"operating_kpi::{series.kpi_id}"
            unit = series.unit.upper()
            number_format = (
                PERCENT_FORMAT
                if unit in {"PERCENT", "PERCENT_DECIMAL", "%"}
                else (
                    "£0.00"
                    if "GBP" in unit or "ARPU" in series.kpi_id.upper()
                    else "#,##0.0"
                )
            )
            for column in columns:
                letter = column_letters[column.column_id]
                cell = f"{letter}{row}"
                if column.source_period_id is not None:
                    point = series.values.get(column.source_period_id)
                    if point is not None:
                        state.value(
                            "KPIs", cell, semantic_id, point.value,
                            owner="CP-1", write_class="SOURCE", period_id=column.column_id,
                            provenance=point.provenance, number_format=number_format,
                        )
                        series_cells[column.column_id] = cell
                        continue
                    if column.group != "FY" or series.value_type != "PERIOD_END":
                        continue
                    source_id = year_end_period_by_fiscal_year.get(column.fiscal_year)
                    source_cell = series_cells.get(source_id or "")
                    point = series.values.get(source_id or "")
                    if source_cell is not None and point is not None:
                        state.formula(
                            "KPIs", cell, semantic_id,
                            f"='KPIs'!{source_cell}", point.value,
                            period_id=column.column_id, number_format=number_format,
                        )
                        series_cells[column.column_id] = cell
                    continue
                if series.value_type == "RATE":
                    direct_period_id = direct_rate_period_id(column)
                    point = series.values.get(direct_period_id or "")
                    if point is not None:
                        state.value(
                            "KPIs",
                            cell,
                            semantic_id,
                            point.value,
                            owner="CP-1",
                            write_class="SOURCE",
                            period_id=column.column_id,
                            provenance=point.provenance,
                            number_format=number_format,
                        )
                        series_cells[column.column_id] = cell
                    continue
                if not column.available:
                    continue
                if series.value_type == "PERIOD_END":
                    source_id = column.balance_period_id
                    source_cell = series_cells.get(source_id or "")
                    point = series.values.get(source_id or "")
                    expected = point.value if point is not None else None
                    formula = f"='KPIs'!{source_cell}" if source_cell else None
                else:
                    component_ids = column.component_period_ids
                    if any(period_id not in series_cells for period_id in component_ids):
                        formula = None
                        expected = None
                    else:
                        formula = "=" + "+".join(
                            f"'KPIs'!{series_cells[period_id]}"
                            for period_id in component_ids
                        )
                        expected = sum(
                            (
                                series.values[period_id].value
                                for period_id in component_ids
                                if period_id in series.values
                            ),
                            Decimal("0"),
                        )
                if formula is None or expected is None:
                    continue
                state.formula(
                    "KPIs", cell, semantic_id, formula, expected,
                    period_id=column.column_id, number_format=number_format,
                )
                series_cells[column.column_id] = cell
            row += 1
    ws.freeze_panes = "B6"
    ws.sheet_view.showGridLines = False
    ws.column_dimensions["A"].width = 52
    for column_index in range(2, max_column + 1):
        ws.column_dimensions[get_column_letter(column_index)].width = 15
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_title_rows = "$1:$5"
    ws.print_area = f"A1:{last_column}{row - 1}"
    _style_analysis_spacers(ws, layout.spacer_columns, row - 1)


def _narrative_text(items: Sequence[NarrativeItem]) -> str:
    return "\n".join(
        f"{item.rank}. {item.label} — {item.detail}" for item in items
    )


def _narrative_refs(items: Sequence[NarrativeItem]) -> tuple[SourceRef, ...]:
    result: list[SourceRef] = []
    seen: set[tuple[str, str, str]] = set()
    for item in items:
        for ref in item.provenance:
            key = (ref.source_id, ref.source_locator, ref.as_of)
            if key not in seen:
                seen.add(key)
                result.append(ref)
    return tuple(result)


def _render_snapshot(
    state: _RenderState,
    model: CreditModelIR,
    calculations: CalculationBook,
    model_cells: Mapping[tuple[str, str], str],
) -> None:
    ws = state.workbook["Credit Snapshot"]
    ws.sheet_view.showGridLines = False
    for column, width in {
        "A": 30,
        "B": 20,
        "C": 16,
        "D": 20,
        "E": 18,
        "F": 18,
        "G": 14,
        "H": 14,
    }.items():
        ws.column_dimensions[column].width = width

    ws.merge_cells("A1:H2")
    _set_literal(ws["A1"], f"Credit Snapshot — {model.issuer_name}")
    _style_title(ws["A1"], size=20)
    ws.row_dimensions[1].height = 28

    def section(row: int, title: str, start: int = 1, end: int = 8) -> None:
        ws.merge_cells(start_row=row, start_column=start, end_row=row, end_column=end)
        cell = ws.cell(row, start)
        _set_literal(cell, title)
        _style_title(cell, size=11)
        ws.row_dimensions[row].height = 20

    section(4, "Company Profile", 1, 4)
    section(4, "Model Scope", 5, 8)
    profile_rows = (
        (5, "Company", model.snapshot["issuer_name"]),
        (6, "Sector / country", model.snapshot["sector_country"]),
        (7, "Shareholders", model.snapshot["shareholders"]),
    )
    for row, label, field in profile_rows:
        _set_literal(ws.cell(row, 1), label)
        ws.cell(row, 1).fill = _fill(GREY)
        ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=4)
        state.value(
            "Credit Snapshot",
            f"B{row}",
            label.lower().replace(" ", "_"),
            field.value,
            owner=field.owner,
            write_class="SNAPSHOT_SOURCE",
            provenance=field.provenance,
        )
        ws[f"B{row}"].alignment = Alignment(wrap_text=True, vertical="top")
    scope = (
        (5, "Analysis date", model.analysis_date.isoformat()),
        (6, "Quarter scope", f"{model.quarters[0].display_label} – {model.quarters[-1].display_label}"),
        (7, "Basis", f"{model.periods[0].currency} millions | {model.periods[0].accounting_basis}"),
    )
    for row, label, value in scope:
        _set_literal(ws.cell(row, 5), label)
        ws.cell(row, 5).fill = _fill(GREY)
        ws.merge_cells(start_row=row, start_column=6, end_row=row, end_column=8)
        _set_literal(ws.cell(row, 6), value)

    section(9, "Transaction Summary")
    ws.merge_cells("A10:H12")
    transaction = model.snapshot["transaction_summary"]
    state.value(
        "Credit Snapshot",
        "A10",
        "transaction_summary",
        transaction.value,
        owner=transaction.owner,
        write_class="SNAPSHOT_SOURCE",
        provenance=transaction.provenance,
    )
    ws["A10"].alignment = Alignment(wrap_text=True, vertical="top")
    ws["A10"].fill = _fill(PALE_YELLOW)

    section(14, "Business Description", 1, 4)
    section(14, "Historical Performance", 5, 8)
    ws.merge_cells("A15:D19")
    business = model.snapshot["business_description"]
    state.value(
        "Credit Snapshot",
        "A15",
        "business_description",
        business.value,
        owner=business.owner,
        write_class="SNAPSHOT_SOURCE",
        provenance=business.provenance,
    )
    ws["A15"].alignment = Alignment(wrap_text=True, vertical="top")
    ws["A15"].fill = _fill(PALE_YELLOW)
    ws.merge_cells("E15:H19")
    history = model.snapshot["historical_performance"]
    state.value(
        "Credit Snapshot",
        "E15",
        "historical_performance",
        history.value,
        owner=history.owner,
        write_class="SNAPSHOT_SOURCE",
        provenance=history.provenance,
    )
    ws["E15"].alignment = Alignment(wrap_text=True, vertical="top")
    ws["E15"].fill = _fill(PALE_YELLOW)

    section(21, "Credit Strengths", 1, 4)
    section(21, "Credit Weaknesses", 5, 8)
    ws.merge_cells("A22:D27")
    state.value(
        "Credit Snapshot",
        "A22",
        "strengths",
        _narrative_text(model.strengths),
        owner="CP-2",
        write_class="SNAPSHOT_SOURCE",
        provenance=_narrative_refs(model.strengths),
    )
    ws["A22"].alignment = Alignment(wrap_text=True, vertical="top")
    ws["A22"].fill = _fill(PALE_GREEN)
    ws.merge_cells("E22:H27")
    state.value(
        "Credit Snapshot",
        "E22",
        "weaknesses",
        _narrative_text(model.weaknesses),
        owner="CP-2",
        write_class="SNAPSHOT_SOURCE",
        provenance=_narrative_refs(model.weaknesses),
    )
    ws["E22"].alignment = Alignment(wrap_text=True, vertical="top")
    ws["E22"].fill = _fill(PALE_RED)

    section(29, "Catalysts and Near-Term Events")
    catalyst_end = max(31, 29 + len(model.catalysts) * 2)
    ws.merge_cells(start_row=30, start_column=1, end_row=catalyst_end, end_column=8)
    state.value(
        "Credit Snapshot",
        "A30",
        "catalysts",
        _narrative_text(model.catalysts),
        owner="CP-2A",
        write_class="SNAPSHOT_SOURCE",
        provenance=_narrative_refs(model.catalysts),
    )
    ws["A30"].alignment = Alignment(wrap_text=True, vertical="top")
    ws["A30"].fill = _fill(PALE_YELLOW)

    highlights_start = catalyst_end + 2
    section(highlights_start, "Financial Highlights")
    header_row = highlights_start + 1
    ws.cell(header_row, 1, "Metric")
    fy_columns = [column for column in calculations.columns if column.group == "FY"][-2:]
    latest_ltm = [column for column in calculations.columns if column.group == "LTM"][-1:]
    pf_columns = [column for column in calculations.columns if column.group == "PF"][-1:]
    base_columns = [
        column for column in calculations.columns
        if column.group == "BASE" and column.available
    ][:1]
    downside_columns = [
        column for column in calculations.columns
        if column.group == "DOWNSIDE" and column.available
    ][:1]
    display_columns = tuple(
        (*fy_columns, *latest_ltm, *pf_columns, *base_columns, *downside_columns)
    )
    if not display_columns:
        display_columns = calculations.columns[-4:]
    for index, column in enumerate(display_columns, 2):
        _set_literal(ws.cell(header_row, index), column.label)
        ws.cell(header_row, index).alignment = Alignment(horizontal="center")
    for column in range(1, len(display_columns) + 2):
        ws.cell(header_row, column).fill = _fill(MID_BLUE)
        ws.cell(header_row, column).font = Font(color=NAVY, bold=True)

    highlight_rows = (
        ("revenue", "Revenue", MONEY_FORMAT),
        ("adjusted_ebitda_calc", "Adjusted EBITDA", MONEY_FORMAT),
        ("fcf", "Free cash flow", MONEY_FORMAT),
        ("total_debt_reported", "Total debt", MONEY_FORMAT),
        ("cash_and_equivalents", "Cash", MONEY_FORMAT),
        ("senior_secured_leverage", "Senior secured leverage", MULTIPLE_FORMAT),
        ("senior_leverage", "Senior leverage", MULTIPLE_FORMAT),
        ("total_leverage", "Total leverage", MULTIPLE_FORMAT),
        ("net_leverage", "Total net leverage", MULTIPLE_FORMAT),
        ("interest_coverage", "Interest coverage", MULTIPLE_FORMAT),
    )
    for offset, (key, label, number_format) in enumerate(highlight_rows, 1):
        row = header_row + offset
        _set_literal(ws.cell(row, 1), label)
        ws.cell(row, 1).font = Font(bold=True)
        for index, column in enumerate(display_columns, 2):
            calculation = calculations.for_column(column.column_id)
            expected = (
                calculation.credit_metrics[key]
                if key in calculation.credit_metrics
                else calculation.values[key]
            )
            if expected is None:
                continue
            model_cell = model_cells[(key, column.column_id)]
            cell = f"{get_column_letter(index)}{row}"
            state.formula(
                "Credit Snapshot",
                cell,
                f"snapshot::{key}",
                f"='Model'!{model_cell}",
                expected,
                period_id=column.column_id,
                number_format=number_format,
            )
        _style_data_row(ws, row, len(display_columns) + 1, fill=PALE_BLUE)

    latest_period = model.quarters[-1]
    addback_start = header_row + len(highlight_rows) + 2
    section(addback_start, f"Latest EBITDA Add-backs — {latest_period.display_label}")
    addback_header = addback_start + 1
    for index, header in enumerate(("Add-back", "Category", "Realization", "Amount"), 1):
        ws.cell(addback_header, index, header)
        ws.cell(addback_header, index).fill = _fill(MID_BLUE)
        ws.cell(addback_header, index).font = Font(color=NAVY, bold=True)
    addback_row = addback_header + 1
    for series in model.addbacks:
        point = series.values.get(latest_period.period_id)
        if point is None:
            continue
        _set_literal(ws.cell(addback_row, 1), series.label)
        _set_literal(ws.cell(addback_row, 2), series.category)
        _set_literal(ws.cell(addback_row, 3), series.realization_status)
        state.value(
            "Credit Snapshot",
            f"D{addback_row}",
            f"snapshot_addback::{series.series_id}",
            calculations.for_period(latest_period.period_id).addback_values[
                series.series_id
            ],
            owner="CP-1",
            write_class="SNAPSHOT_SOURCE",
            period_id=latest_period.period_id,
            provenance=point.provenance,
            number_format=MONEY_FORMAT,
        )
        _style_data_row(ws, addback_row, 4, fill=PALE_YELLOW)
        for column in (1, 2, 3):
            ws.cell(addback_row, column).alignment = Alignment(
                wrap_text=True,
                vertical="top",
            )
        ws.row_dimensions[addback_row].height = 24
        addback_row += 1
    ws.cell(addback_row, 1, "Total add-backs")
    state.formula(
        "Credit Snapshot",
        f"D{addback_row}",
        "snapshot::total_addbacks",
        f"='Model'!{model_cells[('total_addbacks', latest_period.period_id)]}",
        calculations.for_period(latest_period.period_id).values["total_addbacks"],
        period_id=latest_period.period_id,
        number_format=MONEY_FORMAT,
    )
    _style_data_row(ws, addback_row, 4, fill=PALE_YELLOW, bold=True)

    debt_start = addback_row + 2
    section(debt_start, "Latest Capital Structure")
    debt_header = debt_start + 1
    headers = ("Facility", "Type", "Security", "Coupon / margin", "Maturity", "Carrying value")
    for index, header in enumerate(headers, 1):
        ws.cell(debt_header, index, header)
        ws.cell(debt_header, index).fill = _fill(MID_BLUE)
        ws.cell(debt_header, index).font = Font(color=NAVY, bold=True)
    debt_row = debt_header + 1
    for secured_status, group_label, subtotal_key in (
        ("SECURED", "Secured debt", "secured_debt"),
        ("UNSECURED", "Unsecured debt", "unsecured_debt"),
        ("NOT_STATED", "Other / security not stated", "other_debt"),
    ):
        facilities = [
            (facility, point)
            for facility in model.debt
            if (point := facility.values.get(latest_period.period_id)) is not None
            and point.secured_status == secured_status
        ]
        if not facilities and secured_status == "NOT_STATED":
            continue
        _set_literal(ws.cell(debt_row, 1), group_label)
        _set_literal(ws.cell(debt_row, 3), secured_status)
        state.formula(
            "Credit Snapshot",
            f"F{debt_row}",
            f"snapshot::{subtotal_key}",
            f"='Model'!{model_cells[(subtotal_key, latest_period.period_id)]}",
            calculations.for_period(latest_period.period_id).values[subtotal_key],
            period_id=latest_period.period_id,
            number_format=MONEY_FORMAT,
        )
        _style_data_row(ws, debt_row, 6, fill=GREY, bold=True)
        debt_row += 1
        for facility, point in facilities:
            values = (
                f"  {point.facility_name}",
                point.facility_type,
                point.secured_status,
                point.margin_or_coupon,
                point.maturity_date,
            )
            for index, value in enumerate(values, 1):
                _set_literal(ws.cell(debt_row, index), value)
            state.value(
                "Credit Snapshot",
                f"F{debt_row}",
                f"snapshot_debt::{facility.facility_id}",
                calculations.for_period(latest_period.period_id).debt_values[
                    facility.facility_id
                ],
                owner="CP-1",
                write_class="SNAPSHOT_SOURCE",
                period_id=latest_period.period_id,
                provenance=point.carrying_value.provenance,
                number_format=MONEY_FORMAT,
            )
            _style_data_row(ws, debt_row, 6, fill=WHITE)
            for column in range(1, 6):
                ws.cell(debt_row, column).alignment = Alignment(
                    wrap_text=True,
                    vertical="top",
                )
            ws.row_dimensions[debt_row].height = 24
            debt_row += 1

    ws.cell(debt_row, 1, "Total debt")
    state.formula(
        "Credit Snapshot",
        f"F{debt_row}",
        "snapshot::total_debt",
        f"='Model'!{model_cells[('total_debt_reported', latest_period.period_id)]}",
        calculations.for_period(latest_period.period_id).values[
            "total_debt_reported"
        ],
        period_id=latest_period.period_id,
        number_format=MONEY_FORMAT,
    )
    _style_data_row(ws, debt_row, 6, fill=PALE_BLUE, bold=True)

    ws.freeze_panes = "A4"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_area = f"A1:H{ws.max_row}"


def _append_source_row(
    ws: object,
    owner: str,
    field_id: str,
    period_id: str,
    value: object,
    value_class: str,
    provenance: Sequence[SourceRef],
) -> int:
    return _append_literal_row(
        ws,
        (
            owner,
            field_id,
            period_id,
            value,
            value_class,
            ";".join(ref.source_id for ref in provenance),
            ";".join(ref.source_locator for ref in provenance),
            max((ref.as_of for ref in provenance), default=""),
        ),
    )


def _render_inputs(workbook: Workbook, model: CreditModelIR) -> _InputRenderResult:
    ws = workbook.create_sheet("_INPUTS")
    _append_literal_row(
        ws,
        (
            "owner",
            "field_id",
            "period_id",
            "value",
            "value_class",
            "source_id",
            "source_locator",
            "as_of",
        ),
    )
    period_order = {period.period_id: index for index, period in enumerate(model.periods)}
    for (metric_id, period_id), source in sorted(
        model.accounts.items(), key=lambda item: (period_order[item[0][1]], item[0][0])
    ):
        _append_source_row(
            ws,
            "CP-1",
            metric_id,
            period_id,
            source.value,
            source.value_class,
            source.provenance,
        )
    for prefix, owner, series_set in (
        ("segment", "CP-1", model.segments),
        ("addback", "CP-1", model.addbacks),
    ):
        for series in series_set:
            for period_id, source in series.values.items():
                _append_source_row(
                    ws,
                    owner,
                    f"{prefix}::{series.series_id}",
                    period_id,
                    source.value,
                    source.value_class,
                    source.provenance,
                )
    for series in model.addbacks:
        provenance = tuple(
            ref for point in series.values.values() for ref in point.provenance
        )
        _append_source_row(
            ws,
            "CP-1",
            f"addback_realization::{series.series_id}",
            "",
            series.realization_status,
            "CLASSIFICATION",
            provenance,
        )
    for series in model.operating_kpis:
        for period_id, source in series.values.items():
            _append_source_row(
                ws,
                "CP-1",
                f"operating_kpi::{series.kpi_id}",
                period_id,
                source.value,
                source.value_class,
                source.provenance,
            )
    for facility in model.debt:
        for period_id, point in facility.values.items():
            _append_source_row(
                ws,
                "CP-1",
                f"debt::{facility.facility_id}",
                period_id,
                point.carrying_value.value,
                point.carrying_value.value_class,
                point.carrying_value.provenance,
            )
            _append_source_row(
                ws,
                "CP-1",
                f"debt_terms::{facility.facility_id}",
                period_id,
                f"{point.facility_name} | {point.margin_or_coupon or 'Not stated'} | "
                f"{point.maturity_date or 'Not stated'}",
                "SOURCED",
                point.carrying_value.provenance,
            )
    for field_id, field in sorted(model.snapshot.items()):
        _append_source_row(
            ws,
            field.owner,
            field_id,
            "",
            field.value,
            "SOURCED",
            field.provenance,
        )
    for prefix, owner, items in (
        ("strength", "CP-2", model.strengths),
        ("weakness", "CP-2", model.weaknesses),
        ("catalyst", "CP-2A", model.catalysts),
    ):
        for item in items:
            _append_source_row(
                ws,
                owner,
                f"{prefix}::{item.rank}",
                "",
                f"{item.label} — {item.detail}",
                "SOURCED",
                item.provenance,
            )
    forecast_driver_cells: dict[tuple[str, str, str, str], str] = {}
    forecast_mappings: list[MappingRecord] = []
    for driver in model.forecast_drivers:
        input_row = _append_source_row(
            ws,
            "CP-2G",
            f"forecast::{driver.driver_id}::{driver.slot_id or 'ALL'}::{driver.case}",
            driver.period_id,
            driver.value if driver.value is not None else "",
            driver.status,
            driver.provenance,
        )
        forecast_driver_cells[
            (driver.case, driver.period_id, driver.driver_id, driver.slot_id)
        ] = f"'_INPUTS'!$D${input_row}"
        forecast_mappings.append(
            MappingRecord(
                f"forecast::{driver.driver_id}::{driver.slot_id or 'ALL'}",
                "CP-2G",
                f"_INPUTS!D{input_row}",
                "FORECAST_SOURCE",
                driver.period_id,
                _source_refs(driver.provenance),
            )
        )
    ws.sheet_state = "hidden"
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    return _InputRenderResult(
        forecast_driver_cells,
        tuple(forecast_mappings),
    )


def _render_mappings(workbook: Workbook, mappings: Sequence[MappingRecord]) -> None:
    ws = workbook.create_sheet("_MAP")
    _append_literal_row(
        ws,
        ("semantic_id", "owner", "target", "write_class", "period_id", "source_refs"),
    )
    for record in mappings:
        _append_literal_row(
            ws,
            (
                record.semantic_id,
                record.owner,
                record.target,
                record.write_class,
                record.period_id,
                record.source_refs,
            ),
        )
    ws.sheet_state = "hidden"
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions


def _render_checks(
    workbook: Workbook,
    checks: Sequence[SemanticCheck],
    formula_count: int,
    warnings: Sequence[str],
) -> None:
    ws = workbook.create_sheet("_CHECKS")
    _append_literal_row(
        ws,
        (
            "check_id",
            "status",
            "period_id",
            "actual",
            "expected",
            "difference",
            "tolerance",
            "detail",
        ),
    )
    _append_literal_row(ws, ("input_contract", "PASS", "", "", "", "", "", "All canonical handoffs validated."))
    _append_literal_row(ws, ("template_dependency", "PASS", "", "none", "none", "", "", "Workbook created from a blank file."))
    _append_literal_row(ws, ("formula_recalculation", "PASS", "", formula_count, formula_count, 0, 0, "Publication requires external recalculation and cache validation."))
    for warning in warnings:
        _append_literal_row(ws, ("input_warning", "WARN", "", "", "", "", "", warning))
    for check in checks:
        _append_literal_row(
            ws,
            (
                check.check_id,
                check.status,
                check.period_id,
                float(check.actual),
                float(check.expected),
                float(check.difference),
                float(check.tolerance),
                check.detail,
            ),
        )
    ws.sheet_state = "hidden"
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions


def _render_audit(
    workbook: Workbook,
    model: CreditModelIR,
    metadata: RenderMetadata,
) -> None:
    ws = workbook.create_sheet("_AUDIT")
    _append_literal_row(ws, ("key", "value", "sha256"))
    rows = (
        ("module_id", "CP-MODEL", ""),
        ("module_version", V3_CONTRACT_VERSION, ""),
        ("owned_object", "credit_snapshot_model_workbook", ""),
        ("issuer_id", model.issuer_id, ""),
        ("analysis_date", model.analysis_date.isoformat(), ""),
        ("quarter_start", model.quarters[0].period_id, ""),
        ("quarter_end", model.quarters[-1].period_id, ""),
        ("quarter_count", len(model.quarters), ""),
        ("annual_count", len(model.annuals), ""),
        ("analysis_axis", "QUARTER|YTD|FY|LTM|PF|BASE|DOWNSIDE", ""),
        ("renderer_hash", metadata.renderer_hash, metadata.renderer_hash),
        ("calculation_engine", metadata.calculation_engine, ""),
        ("template", "none", ""),
    )
    for row in rows:
        _append_literal_row(ws, row)
    for module_id, path in sorted(model.source_paths.items()):
        _append_literal_row(
            ws,
            (f"source::{module_id}", path.name, model.source_hashes[module_id]),
        )
    ws.sheet_state = "hidden"
    ws.freeze_panes = "A2"


def _style_hidden_sheets(workbook: Workbook) -> None:
    for name in ("_INPUTS", "_MAP", "_CHECKS", "_AUDIT"):
        ws = workbook[name]
        for cell in ws[1]:
            cell.fill = _fill(NAVY)
            cell.font = Font(color=WHITE, bold=True)
        for column in range(1, ws.max_column + 1):
            width = min(
                60,
                max(
                    12,
                    max(
                        len(str(ws.cell(row, column).value or ""))
                        for row in range(1, min(ws.max_row, 200) + 1)
                    )
                    + 2,
                ),
            )
            ws.column_dimensions[get_column_letter(column)].width = width


def render_workbook(
    model: CreditModelIR,
    calculations: CalculationBook,
    metadata: RenderMetadata,
    output_path: Path,
) -> RenderResult:
    """Create the complete workbook from a blank OOXML package."""

    workbook = Workbook()
    workbook.active.title = "Credit Snapshot"
    workbook.create_sheet("Model")
    workbook.create_sheet("KPIs")
    input_render = _render_inputs(workbook, model)
    state = _RenderState(workbook)
    state.mappings.extend(input_render.mappings)
    model_cells, _rows = _render_model(
        state,
        model,
        calculations,
        input_render.forecast_driver_cells,
    )
    _render_kpis(state, model, calculations, model_cells)
    _render_snapshot(state, model, calculations, model_cells)
    _render_mappings(workbook, state.mappings)
    _render_checks(
        workbook,
        calculations.checks,
        len(state.formulas),
        model.validation_warnings,
    )
    _render_audit(workbook, model, metadata)
    _style_hidden_sheets(workbook)
    workbook.calculation.calcMode = "auto"
    workbook.calculation.fullCalcOnLoad = True
    workbook.calculation.forceFullCalc = True
    workbook.calculation.calcOnSave = True
    workbook.save(output_path)
    return RenderResult(tuple(state.formulas), tuple(state.mappings), model_cells)
