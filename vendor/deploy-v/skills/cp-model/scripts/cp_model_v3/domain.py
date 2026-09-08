"""Typed, template-independent input model for CP-MODEL v3."""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping

from validate_cp_model_inputs import (
    CP1A_SNAPSHOT_TABLE,
    CP1B_SNAPSHOT_TABLE,
    CP1_OPERATING_KPI_TABLE,
    CP1_SEGMENT_ALLOCATION_TABLE,
    CP2B_SNAPSHOT_TABLE,
    CP2G_FORECAST_TABLE,
    CP2_SNAPSHOT_TABLE,
    SENIOR_DEBT_CLASSES,
    parse_stable_tables,
    validate_common_handoff,
    validate_cp_model_bundle,
)


V3_CONTRACT_VERSION = "3.0"
NULL_TEXT = {"", "null", "n/a", "not available", "not calculable", "-"}
SAFE_OUTPUT_TOKEN = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?$")
REQUIRED_ACCOUNT_METRICS = frozenset(
    {
        "revenue",
        "cogs",
        "opex_including_da",
        "depreciation_amortization",
        "ebitda",
        "adjusted_ebitda",
        "cash_interest_paid",
        "cash_lease_payments",
        "cash_taxes_paid",
        "cfo_ncfo",
        "working_capital_change",
        "capex_and_intangible_investment",
        "acquisitions_disposals",
        "net_debt_issue_repay",
        "net_equity_issue_repay",
        "dividends_paid",
        "other_investing_financing",
        "net_cash_change",
        "cash_and_equivalents",
        "rcf_commitment",
        "total_debt",
        "net_accounts_receivable",
        "inventory",
        "accounts_payable",
    }
)


class CpModelV3Error(ValueError):
    """Raised when v3 cannot build and publish a trustworthy workbook."""


@dataclass(frozen=True)
class BundlePaths:
    """Canonical handoff paths accepted by the v3 build interface."""

    cp1: Path
    cp1a: Path
    cp1b: Path
    cp2: Path
    cp2b: Path
    cp2g: Path | None = None

    def by_module(self) -> dict[str, Path]:
        result = {
            "CP-1": self.cp1,
            "CP-1A": self.cp1a,
            "CP-1B": self.cp1b,
            "CP-2": self.cp2,
            "CP-2A": self.cp2b,
        }
        if self.cp2g is not None:
            result["CP-2G"] = self.cp2g
        return result


@dataclass(frozen=True)
class SourceRef:
    source_id: str
    source_locator: str
    as_of: str


@dataclass(frozen=True)
class SourceNumber:
    value: Decimal
    value_class: str
    provenance: tuple[SourceRef, ...]


@dataclass(frozen=True)
class TextValue:
    value: str
    owner: str
    provenance: tuple[SourceRef, ...]


@dataclass(frozen=True)
class Period:
    period_id: str
    fiscal_year: int
    fiscal_quarter: int | None
    period_type: str
    start_date: date
    end_date: date
    day_count: int
    audit_status: str
    currency: str
    unit: str
    accounting_basis: str
    entity_perimeter: str
    provenance: tuple[SourceRef, ...]

    @property
    def scale_to_millions(self) -> Decimal:
        try:
            return {
                "MILLIONS": Decimal("1"),
                "THOUSANDS": Decimal("0.001"),
                "UNITS": Decimal("0.000001"),
            }[self.unit]
        except KeyError as exc:
            raise CpModelV3Error(
                f"{self.period_id}: unsupported unit {self.unit!r}"
            ) from exc

    @property
    def display_label(self) -> str:
        if self.period_type == "QUARTER" and self.fiscal_quarter is not None:
            return f"Q{self.fiscal_quarter} FY{self.fiscal_year % 100:02d}"
        if self.period_type == "FY":
            return f"FY{self.fiscal_year % 100:02d}"
        return self.period_id


@dataclass(frozen=True)
class Series:
    series_id: str
    label: str
    category: str
    display_priority: int
    values: Mapping[str, SourceNumber]


@dataclass(frozen=True)
class AddbackSeries:
    series_id: str
    label: str
    category: str
    realization_status: str
    display_priority: int
    values: Mapping[str, SourceNumber]


@dataclass(frozen=True)
class OperatingKpiSeries:
    kpi_id: str
    label: str
    business_unit: str
    category: str
    display_priority: int
    unit: str
    value_type: str
    values: Mapping[str, SourceNumber]


@dataclass(frozen=True)
class DebtPoint:
    carrying_value: SourceNumber
    facility_name: str
    facility_type: str
    secured_status: str
    seniority: str
    margin_or_coupon: str
    maturity_date: str


@dataclass(frozen=True)
class DebtSeries:
    facility_id: str
    label: str
    display_priority: int
    values: Mapping[str, DebtPoint]


@dataclass(frozen=True)
class NarrativeItem:
    item_id: str
    label: str
    detail: str
    rank: int
    owner: str
    provenance: tuple[SourceRef, ...]


@dataclass(frozen=True)
class ForecastDriver:
    driver_id: str
    slot_id: str
    case: str
    period_id: str
    fiscal_year: int
    value: Decimal | None
    unit: str
    status: str
    provenance: tuple[SourceRef, ...]


@dataclass(frozen=True)
class CreditModelIR:
    issuer_id: str
    issuer_name: str
    reporting_period: str
    analysis_date: date
    quarters: tuple[Period, ...]
    annuals: tuple[Period, ...]
    reported_periods: Mapping[str, Period]
    accounts: Mapping[tuple[str, str], SourceNumber]
    segments: tuple[Series, ...]
    segment_forecast_slots: Mapping[str, str]
    addbacks: tuple[AddbackSeries, ...]
    operating_kpis: tuple[OperatingKpiSeries, ...]
    debt: tuple[DebtSeries, ...]
    snapshot: Mapping[str, TextValue]
    strengths: tuple[NarrativeItem, ...]
    weaknesses: tuple[NarrativeItem, ...]
    catalysts: tuple[NarrativeItem, ...]
    forecast_drivers: tuple[ForecastDriver, ...]
    source_paths: Mapping[str, Path]
    source_hashes: Mapping[str, str]
    limitation_flags: tuple[str, ...]
    upstream_validation_warnings: tuple[str, ...]
    validation_warnings: tuple[str, ...]

    @property
    def periods(self) -> tuple[Period, ...]:
        return (*self.quarters, *self.annuals)

    @property
    def period_ids(self) -> tuple[str, ...]:
        return tuple(period.period_id for period in self.periods)

    def account(self, metric_id: str, period_id: str) -> SourceNumber:
        try:
            return self.accounts[(metric_id, period_id)]
        except KeyError as exc:
            raise CpModelV3Error(
                f"missing account {metric_id!r} for {period_id!r}"
            ) from exc


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_text_and_hash(path: Path) -> tuple[str, str]:
    payload = path.read_bytes()
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CpModelV3Error(f"handoff is not UTF-8: {path}") from exc
    return text, hashlib.sha256(payload).hexdigest()


def _decimal(value: str, field: str) -> Decimal:
    text = value.strip()
    if text.lower() in NULL_TEXT:
        raise CpModelV3Error(f"{field}: numeric value is required")
    negative = text.startswith("(") and text.endswith(")")
    cleaned = text.strip("()").replace(",", "").replace("$", "")
    percent = cleaned.endswith("%")
    if percent:
        cleaned = cleaned[:-1]
    try:
        result = Decimal(cleaned)
    except InvalidOperation as exc:
        raise CpModelV3Error(f"{field}: invalid numeric value {value!r}") from exc
    if not math.isfinite(float(result)):
        raise CpModelV3Error(f"{field}: numeric value must be finite")
    if negative:
        result = -result
    return result / Decimal("100") if percent else result


def _integer(value: str, field: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise CpModelV3Error(f"{field}: integer required") from exc


def _date(value: str, field: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise CpModelV3Error(f"{field}: ISO date required") from exc


def _ref(row: Mapping[str, str], *, as_of: str) -> SourceRef:
    source_id = row.get("source_id", "").strip()
    source_locator = row.get("source_locator", "").strip()
    if not source_id or not source_locator:
        raise CpModelV3Error("source_id and source_locator are required")
    return SourceRef(source_id, source_locator, as_of)


def _unique_refs(*groups: tuple[SourceRef, ...]) -> tuple[SourceRef, ...]:
    seen: set[tuple[str, str, str]] = set()
    result: list[SourceRef] = []
    for group in groups:
        for item in group:
            key = (item.source_id, item.source_locator, item.as_of)
            if key not in seen:
                seen.add(key)
                result.append(item)
    return tuple(result)


def _identity(markdown: str, module_id: str) -> dict[str, Any]:
    result = validate_common_handoff(markdown, expected_module=module_id)
    if result.errors or result.identity_mismatches or result.fields is None:
        details = (*result.errors, *result.identity_mismatches)
        raise CpModelV3Error(f"{module_id} identity invalid: {'; '.join(details)}")
    return result.fields


def _load_texts(paths: BundlePaths) -> tuple[dict[str, str], dict[str, str]]:
    texts: dict[str, str] = {}
    hashes: dict[str, str] = {}
    for module_id, path in paths.by_module().items():
        if not path.is_file():
            raise CpModelV3Error(f"{module_id} handoff not found: {path}")
        texts[module_id], hashes[module_id] = _read_text_and_hash(path)
    return texts, hashes


def _parse_periods(
    rows: list[dict[str, str]], quarter_count: int | None
) -> tuple[tuple[Period, ...], tuple[Period, ...], dict[str, Period]]:
    parsed: list[Period] = []
    for row in rows:
        period_type = row["period_type"].strip()
        quarter_text = row["fiscal_quarter"].strip()
        fiscal_quarter = None if quarter_text.lower() in NULL_TEXT else _integer(
            quarter_text,
            f"{row['period_id']} fiscal_quarter",
        )
        end = _date(row["end_date"], f"{row['period_id']} end_date")
        parsed.append(
            Period(
                period_id=row["period_id"].strip(),
                fiscal_year=_integer(row["fiscal_year"], f"{row['period_id']} fiscal_year"),
                fiscal_quarter=fiscal_quarter,
                period_type=period_type,
                start_date=_date(row["start_date"], f"{row['period_id']} start_date"),
                end_date=end,
                day_count=_integer(
                    row["day_count"], f"{row['period_id']} day_count"
                ),
                audit_status=row["audit_status"].strip(),
                currency=row["currency"].strip().upper(),
                unit=row["unit"].strip().upper(),
                accounting_basis=row["accounting_basis"].strip(),
                entity_perimeter=row["entity_perimeter"].strip(),
                provenance=(_ref(row, as_of=end.isoformat()),),
            )
        )
    quarters = sorted(
        (period for period in parsed if period.period_type == "QUARTER"),
        key=lambda period: period.end_date,
    )
    annuals = sorted(
        (period for period in parsed if period.period_type == "FY"),
        key=lambda period: period.end_date,
    )
    if quarter_count is not None:
        if quarter_count < 4:
            raise CpModelV3Error("quarter_count must be at least 4")
        if quarter_count > len(quarters):
            raise CpModelV3Error(
                f"quarter_count {quarter_count} exceeds available history {len(quarters)}"
            )
        quarters = quarters[-quarter_count:]
    if len(quarters) < 4:
        raise CpModelV3Error("at least four discrete quarters are required")
    previous = quarters[0].fiscal_year * 4 + (quarters[0].fiscal_quarter or 0)
    for period in quarters[1:]:
        current = period.fiscal_year * 4 + (period.fiscal_quarter or 0)
        if current != previous + 1:
            raise CpModelV3Error("selected quarterly periods must be consecutive")
        previous = current
    selected = (*quarters, *annuals)
    for field in ("currency", "unit", "accounting_basis", "entity_perimeter"):
        values = {getattr(period, field) for period in selected}
        if len(values) != 1:
            raise CpModelV3Error(f"selected periods have conflicting {field}: {sorted(values)}")
    return (
        tuple(quarters),
        tuple(annuals),
        {period.period_id: period for period in parsed},
    )


def _parse_accounts(
    rows: list[dict[str, str]], periods: Mapping[str, Period]
) -> dict[tuple[str, str], SourceNumber]:
    result: dict[tuple[str, str], SourceNumber] = {}
    for row in rows:
        period_id = row["period_id"].strip()
        if period_id not in periods:
            continue
        metric_id = row["metric_id"].strip()
        key = (metric_id, period_id)
        if key in result:
            raise CpModelV3Error(f"duplicate account key {key}")
        result[key] = SourceNumber(
            _decimal(row["value"], f"{metric_id}/{period_id}"),
            row.get("value_class", "SOURCED").strip() or "SOURCED",
            (_ref(row, as_of=periods[period_id].end_date.isoformat()),),
        )
    for period_id in periods:
        missing = sorted(
            metric_id
            for metric_id in REQUIRED_ACCOUNT_METRICS
            if (metric_id, period_id) not in result
        )
        if missing:
            raise CpModelV3Error(f"{period_id}: missing required accounts {missing}")
    return result


def _parse_series(
    rows: list[dict[str, str]],
    periods: Mapping[str, Period],
    *,
    id_field: str,
    label_field: str,
    category_field: str,
    value_field: str,
) -> tuple[Series, ...]:
    definitions: dict[str, tuple[str, str, int]] = {}
    values: dict[str, dict[str, SourceNumber]] = {}
    for row in rows:
        period_id = row["period_id"].strip()
        if period_id not in periods:
            continue
        series_id = row[id_field].strip()
        definition = (
            row[label_field].strip(),
            row[category_field].strip(),
            _integer(row["display_priority"], f"{series_id} display_priority"),
        )
        prior = definitions.setdefault(series_id, definition)
        if prior != definition:
            raise CpModelV3Error(f"{series_id}: definition changes across periods")
        series_values = values.setdefault(series_id, {})
        if period_id in series_values:
            raise CpModelV3Error(f"duplicate {series_id}/{period_id}")
        series_values[period_id] = SourceNumber(
            _decimal(row[value_field], f"{series_id}/{period_id}"),
            row.get("status", "SOURCED").strip() or "SOURCED",
            (_ref(row, as_of=periods[period_id].end_date.isoformat()),),
        )
    result = [
        Series(series_id, label, category, priority, values[series_id])
        for series_id, (label, category, priority) in definitions.items()
    ]
    return tuple(sorted(result, key=lambda item: (item.display_priority, item.series_id)))


def _parse_segment_forecast_slots(
    rows: list[dict[str, str]],
    segments: tuple[Series, ...],
    *,
    required: bool,
) -> dict[str, str]:
    segment_ids = {segment.series_id for segment in segments}
    if not segment_ids:
        return {}
    if not rows:
        if required:
            raise CpModelV3Error(
                f"{CP1_SEGMENT_ALLOCATION_TABLE} is required when CP-2G "
                "forecasts issuer segments"
            )
        return {}

    slots_by_segment: dict[str, str] = {}
    for row in rows:
        slot_id = row["slot_id"].strip()
        component_ids = (
            component.strip()
            for component in row["component_segment_ids"].split(";")
            if component.strip()
        )
        for segment_id in component_ids:
            if segment_id not in segment_ids:
                raise CpModelV3Error(
                    f"{CP1_SEGMENT_ALLOCATION_TABLE}: unknown segment {segment_id!r}"
                )
            if (
                segment_id in slots_by_segment
                and slots_by_segment[segment_id] != slot_id
            ):
                raise CpModelV3Error(
                    f"{CP1_SEGMENT_ALLOCATION_TABLE}: segment {segment_id!r} "
                    "is assigned more than once"
                )
            slots_by_segment[segment_id] = slot_id
    missing = sorted(segment_ids.difference(slots_by_segment))
    if missing:
        raise CpModelV3Error(
            f"{CP1_SEGMENT_ALLOCATION_TABLE}: missing segments {missing}"
        )
    return slots_by_segment


def _parse_addbacks(
    rows: list[dict[str, str]], periods: Mapping[str, Period]
) -> tuple[AddbackSeries, ...]:
    definitions: dict[str, tuple[str, str, str, int]] = {}
    values: dict[str, dict[str, SourceNumber]] = {}
    for row in rows:
        period_id = row["period_id"].strip()
        if period_id not in periods:
            continue
        series_id = row["addback_id"].strip()
        definition = (
            row["addback_label"].strip(),
            row["addback_classification"].strip(),
            row["realization_status"].strip(),
            _integer(row["display_priority"], f"{series_id} display_priority"),
        )
        prior = definitions.setdefault(series_id, definition)
        if prior != definition:
            raise CpModelV3Error(
                f"{series_id}: add-back definition changes across periods"
            )
        series_values = values.setdefault(series_id, {})
        if period_id in series_values:
            raise CpModelV3Error(f"duplicate {series_id}/{period_id}")
        series_values[period_id] = SourceNumber(
            _decimal(row["value"], f"{series_id}/{period_id}"),
            row.get("status", "SOURCED").strip() or "SOURCED",
            (_ref(row, as_of=periods[period_id].end_date.isoformat()),),
        )
    result = [
        AddbackSeries(
            series_id,
            label,
            category,
            realization_status,
            priority,
            values[series_id],
        )
        for series_id, (
            label,
            category,
            realization_status,
            priority,
        ) in definitions.items()
    ]
    return tuple(sorted(result, key=lambda item: (item.display_priority, item.series_id)))


def _parse_operating_kpis(
    rows: list[dict[str, str]], periods: Mapping[str, Period]
) -> tuple[OperatingKpiSeries, ...]:
    definitions: dict[str, tuple[str, str, str, int, str, str]] = {}
    values: dict[str, dict[str, SourceNumber]] = {}
    for row in rows:
        period_id = row["period_id"].strip()
        if period_id not in periods:
            continue
        kpi_id = row["kpi_id"].strip()
        definition = (
            row["kpi_label"].strip(),
            row["business_unit"].strip(),
            row["kpi_category"].strip(),
            _integer(row["display_priority"], f"{kpi_id} display_priority"),
            row["unit"].strip(),
            row["value_type"].strip(),
        )
        prior = definitions.setdefault(kpi_id, definition)
        if prior != definition:
            raise CpModelV3Error(
                f"{kpi_id}: operating KPI definition changes across periods"
            )
        series_values = values.setdefault(kpi_id, {})
        if period_id in series_values:
            raise CpModelV3Error(f"duplicate operating KPI {kpi_id}/{period_id}")
        series_values[period_id] = SourceNumber(
            _decimal(row["value"], f"{kpi_id}/{period_id}"),
            row.get("status", "SOURCED").strip() or "SOURCED",
            (_ref(row, as_of=periods[period_id].end_date.isoformat()),),
        )
    result = [
        OperatingKpiSeries(
            kpi_id,
            label,
            business_unit,
            category,
            priority,
            unit,
            value_type,
            values[kpi_id],
        )
        for kpi_id, (
            label,
            business_unit,
            category,
            priority,
            unit,
            value_type,
        ) in definitions.items()
    ]
    return tuple(
        sorted(
            result,
            key=lambda item: (
                item.business_unit,
                item.category,
                item.display_priority,
                item.kpi_id,
            ),
        )
    )


def _parse_debt(
    rows: list[dict[str, str]], periods: Mapping[str, Period]
) -> tuple[DebtSeries, ...]:
    values: dict[str, dict[str, DebtPoint]] = {}
    latest: dict[str, tuple[date, str]] = {}
    for row in rows:
        period_id = row["period_id"].strip()
        period = periods.get(period_id)
        if period is None:
            continue
        facility_id = row["facility_id"].strip()
        series_values = values.setdefault(facility_id, {})
        if period_id in series_values:
            raise CpModelV3Error(f"duplicate debt facility key {(facility_id, period_id)}")
        series_values[period_id] = DebtPoint(
            carrying_value=SourceNumber(
                _decimal(row["carrying_value"], f"{facility_id}/{period_id}"),
                "SOURCED",
                (_ref(row, as_of=period.end_date.isoformat()),),
            ),
            facility_name=row["facility_name"].strip(),
            facility_type=row["facility_type"].strip(),
            secured_status=row["secured_status"].strip(),
            seniority=row["seniority"].strip(),
            margin_or_coupon=row["margin_or_coupon"].strip(),
            maturity_date=row["maturity_date"].strip(),
        )
        if facility_id not in latest or period.end_date > latest[facility_id][0]:
            latest[facility_id] = (period.end_date, row["facility_name"].strip())
    result = [
        DebtSeries(
            facility_id,
            latest[facility_id][1] or facility_id,
            index,
            series_values,
        )
        for index, (facility_id, series_values) in enumerate(
            sorted(values.items(), key=lambda item: item[0]), 1
        )
    ]
    return tuple(result)


def _parse_snapshot(tables: Mapping[str, Mapping[str, list[dict[str, str]]]]) -> dict[str, TextValue]:
    result: dict[str, TextValue] = {}
    for owner, table_id in (
        ("CP-1A", CP1A_SNAPSHOT_TABLE),
        ("CP-1B", CP1B_SNAPSHOT_TABLE),
    ):
        for row in tables[owner][table_id]:
            field_id = row["field_id"].strip()
            result[field_id] = TextValue(
                row["value"].strip(),
                owner,
                (_ref(row, as_of=row["as_of"].strip()),),
            )
    sector = result["sector"]
    country = result["country"]
    result["sector_country"] = TextValue(
        f"{sector.value} / {country.value}",
        "CP-1A",
        _unique_refs(sector.provenance, country.provenance),
    )
    return result


def _parse_credit_items(
    rows: list[dict[str, str]], direction: str
) -> tuple[NarrativeItem, ...]:
    items = [row for row in rows if row["direction"].strip() == direction]
    result = [
        NarrativeItem(
            f"{direction.lower()}::{row['rank'].strip()}",
            row["label"].strip(),
            row["mechanism"].strip(),
            _integer(row["rank"], f"{direction} rank"),
            "CP-2",
            (_ref(row, as_of=row["as_of"].strip()),),
        )
        for row in items
    ]
    return tuple(sorted(result, key=lambda item: item.rank))


def _parse_catalysts(rows: list[dict[str, str]]) -> tuple[NarrativeItem, ...]:
    result = [
        NarrativeItem(
            f"catalyst::{row['rank'].strip()}",
            f"{row['event_date_or_window'].strip()}: {row['event'].strip()}",
            row["credit_relevance"].strip(),
            _integer(row["rank"], "catalyst rank"),
            "CP-2A",
            (_ref(row, as_of=row["as_of"].strip()),),
        )
        for row in rows
    ]
    return tuple(sorted(result, key=lambda item: item.rank))


def _parse_forecast(
    tables: Mapping[str, Mapping[str, list[dict[str, str]]]]
) -> tuple[ForecastDriver, ...]:
    if "CP-2G" not in tables:
        return ()
    result: list[ForecastDriver] = []
    for row in tables["CP-2G"][CP2G_FORECAST_TABLE]:
        status = row["status"].strip()
        result.append(
            ForecastDriver(
                driver_id=row["driver_id"].strip(),
                slot_id=row["slot_id"].strip(),
                case=row["case"].strip(),
                period_id=row["period_id"].strip(),
                fiscal_year=_integer(row["fiscal_year"], "forecast fiscal_year"),
                value=(
                    _decimal(row["value"], "forecast value")
                    if status == "READY"
                    else None
                ),
                unit=row["unit"].strip(),
                status=status,
                provenance=(
                    (_ref(row, as_of=row["as_of"].strip()),)
                    if status == "READY"
                    else ()
                ),
            )
        )
    return tuple(
        sorted(
            result,
            key=lambda item: (
                item.case,
                item.fiscal_year,
                item.driver_id,
                item.slot_id,
            ),
        )
    )


def build_ir(paths: BundlePaths, *, quarter_count: int | None = None) -> CreditModelIR:
    """Validate canonical handoffs and return a typed, layout-free model."""

    source_paths = paths.by_module()
    texts, hashes = _load_texts(paths)
    validation = validate_cp_model_bundle(
        texts["CP-1"],
        texts["CP-1A"],
        texts["CP-1B"],
        texts["CP-2"],
        texts["CP-2A"],
        texts.get("CP-2G"),
        require_segment_allocation=True,
    )
    if validation.errors:
        raise CpModelV3Error("input contract failed: " + "; ".join(validation.errors))

    identities: dict[str, dict[str, Any]] = {}
    for module_id, text in texts.items():
        identities[module_id] = _identity(text, module_id)

    cp1_identity = identities["CP-1"]
    issuer_id = str(cp1_identity["issuer_id"])
    if SAFE_OUTPUT_TOKEN.fullmatch(issuer_id) is None or len(issuer_id) > 100:
        raise CpModelV3Error(f"unsafe issuer_id for output filename: {issuer_id!r}")

    tables = {
        module_id: parse_stable_tables(text)
        for module_id, text in texts.items()
    }
    cp1_tables = tables["CP-1"]
    cp2_tables = tables["CP-2"]
    cp2b_tables = tables["CP-2A"]

    quarters, annuals, reported_periods = _parse_periods(
        cp1_tables["cp1.model_period_register"],
        quarter_count,
    )
    selected_periods = (*quarters, *annuals)
    periods = {period.period_id: period for period in selected_periods}

    accounts = _parse_accounts(
        cp1_tables["cp1.model_account_register"],
        periods,
    )
    segments = _parse_series(
        cp1_tables["cp1.segment_revenue_schedule"],
        periods,
        id_field="segment_id",
        label_field="segment_name",
        category_field="segment_type",
        value_field="revenue",
    )
    segment_forecast_slots = _parse_segment_forecast_slots(
        cp1_tables.get(CP1_SEGMENT_ALLOCATION_TABLE, []),
        segments,
        required=paths.cp2g is not None,
    )
    addbacks = _parse_addbacks(
        cp1_tables["cp1.adjusted_ebitda_bridge"],
        periods,
    )
    operating_kpis = _parse_operating_kpis(
        cp1_tables.get(CP1_OPERATING_KPI_TABLE, []),
        reported_periods,
    )
    debt = _parse_debt(
        cp1_tables["cp1.debt_facility_register"],
        periods,
    )
    snapshot = _parse_snapshot(tables)
    strengths = _parse_credit_items(
        cp2_tables[CP2_SNAPSHOT_TABLE],
        "STRENGTH",
    )
    weaknesses = _parse_credit_items(
        cp2_tables[CP2_SNAPSHOT_TABLE],
        "WEAKNESS",
    )
    catalysts = _parse_catalysts(cp2b_tables[CP2B_SNAPSHOT_TABLE])
    forecast_drivers = _parse_forecast(tables)

    issuer_name = str(cp1_identity["issuer_name"])
    try:
        snapshot_issuer_name = snapshot["issuer_name"].value
    except KeyError as exc:
        raise CpModelV3Error(
            "CP-1A snapshot is missing required issuer_name"
        ) from exc
    if snapshot_issuer_name != issuer_name:
        raise CpModelV3Error(
            "CP-1A issuer_name does not match envelope: "
            f"{snapshot_issuer_name!r} != {issuer_name!r}"
        )

    return CreditModelIR(
        issuer_id=issuer_id,
        issuer_name=issuer_name,
        reporting_period=str(cp1_identity["reporting_period"]),
        analysis_date=_date(str(cp1_identity["analysis_date"]), "analysis_date"),
        quarters=quarters,
        annuals=annuals,
        reported_periods=reported_periods,
        accounts=accounts,
        segments=segments,
        segment_forecast_slots=segment_forecast_slots,
        addbacks=addbacks,
        operating_kpis=operating_kpis,
        debt=debt,
        snapshot=snapshot,
        strengths=strengths,
        weaknesses=weaknesses,
        catalysts=catalysts,
        forecast_drivers=forecast_drivers,
        source_paths=source_paths,
        source_hashes=hashes,
        limitation_flags=tuple(
            dict.fromkeys(
                flag
                for module_id in sorted(identities)
                for flag in identities[module_id].get("limitation_flags", [])
            )
        ),
        upstream_validation_warnings=tuple(
            dict.fromkeys(
                warning
                for module_id in sorted(identities)
                for warning in identities[module_id].get("validation_warnings", [])
            )
        ),
        validation_warnings=validation.warnings,
    )
