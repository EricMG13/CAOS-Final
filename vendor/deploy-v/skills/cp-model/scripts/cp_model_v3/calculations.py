"""Independent semantic calculations for CP-MODEL v3."""

from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Mapping

from .domain import CpModelV3Error, CreditModelIR, Period, SENIOR_DEBT_CLASSES


ZERO = Decimal("0")
RECONCILIATION_TOLERANCE = Decimal("0.001")


@dataclass(frozen=True)
class SemanticCheck:
    check_id: str
    status: str
    period_id: str
    actual: Decimal
    expected: Decimal
    difference: Decimal
    tolerance: Decimal
    detail: str


@dataclass(frozen=True)
class PeriodCalculation:
    period: Period
    values: Mapping[str, Decimal]
    segment_values: Mapping[str, Decimal]
    addback_values: Mapping[str, Decimal]
    debt_values: Mapping[str, Decimal | None]
    growth: Mapping[str, Decimal | None]
    kpis: Mapping[str, Decimal | None]


@dataclass(frozen=True)
class AnalysisColumn:
    column_id: str
    group: str
    label: str
    end_date: date
    fiscal_year: int | None
    component_period_ids: tuple[str, ...]
    balance_period_id: str | None
    source_period_id: str | None = None
    comparison_column_id: str | None = None
    rollforward_column_id: str | None = None
    forecast_period_id: str | None = None
    case: str = "ACTUAL"
    day_count: int = 0
    available: bool = True


@dataclass(frozen=True)
class ColumnCalculation:
    column: AnalysisColumn
    values: Mapping[str, Decimal]
    segment_values: Mapping[str, Decimal]
    addback_values: Mapping[str, Decimal]
    debt_values: Mapping[str, Decimal | None]
    growth: Mapping[str, Decimal | None]
    credit_metrics: Mapping[str, Decimal | None]


@dataclass(frozen=True)
class CalculationBook:
    periods: Mapping[str, PeriodCalculation]
    checks: tuple[SemanticCheck, ...]
    columns: tuple[AnalysisColumn, ...]
    column_calculations: Mapping[str, ColumnCalculation]

    def for_period(self, period_id: str) -> PeriodCalculation:
        try:
            return self.periods[period_id]
        except KeyError as exc:
            raise CpModelV3Error(f"missing calculation for {period_id}") from exc

    def for_column(self, column_id: str) -> ColumnCalculation:
        try:
            return self.column_calculations[column_id]
        except KeyError as exc:
            raise CpModelV3Error(f"missing calculation for column {column_id}") from exc


def _check(
    check_id: str,
    period_id: str,
    actual: Decimal,
    expected: Decimal,
    detail: str,
) -> SemanticCheck:
    difference = actual - expected
    status = (
        "PASS"
        if abs(difference) <= RECONCILIATION_TOLERANCE
        else "BLOCK"
    )
    return SemanticCheck(
        check_id,
        status,
        period_id,
        actual,
        expected,
        difference,
        RECONCILIATION_TOLERANCE,
        detail,
    )


def _ratio(numerator: Decimal, denominator: Decimal, *, positive: bool = False) -> Decimal | None:
    if denominator == ZERO or (positive and denominator <= ZERO):
        return None
    return numerator / denominator


def _growth(current: Decimal, prior: Decimal) -> Decimal | None:
    if prior == ZERO:
        return None
    return current / prior - Decimal("1")


def _calculate_period(
    model: CreditModelIR, period: Period
) -> tuple[PeriodCalculation, tuple[SemanticCheck, ...]]:
    period_id = period.period_id
    scale = period.scale_to_millions

    def source(metric_id: str) -> Decimal:
        return model.account(metric_id, period_id).value * scale

    segment_values: dict[str, Decimal] = {}
    for series in model.segments:
        point = series.values.get(period_id)
        if point is not None:
            segment_values[series.series_id] = point.value * scale

    addback_values: dict[str, Decimal] = {}
    for series in model.addbacks:
        point = series.values.get(period_id)
        if point is not None:
            addback_values[series.series_id] = point.value * scale

    debt_values: dict[str, Decimal | None] = {}
    debt_total = ZERO
    secured_debt = ZERO
    unsecured_debt = ZERO
    other_debt = ZERO
    senior_debt = ZERO
    senior_secured_debt = ZERO
    for facility in model.debt:
        point = facility.values.get(period_id)
        if point is None:
            debt_values[facility.facility_id] = None
            continue

        carrying_value = point.carrying_value.value * scale
        debt_values[facility.facility_id] = carrying_value
        debt_total += carrying_value

        if point.secured_status == "SECURED":
            secured_debt += carrying_value
        elif point.secured_status == "UNSECURED":
            unsecured_debt += carrying_value
        else:
            other_debt += carrying_value

        if point.seniority in SENIOR_DEBT_CLASSES:
            senior_debt += carrying_value
            if point.secured_status == "SECURED":
                senior_secured_debt += carrying_value

    segment_total = sum(segment_values.values(), ZERO)

    revenue = source("revenue")
    cogs = source("cogs")
    gross_profit = revenue + cogs
    opex = source("opex_including_da")
    ebit = gross_profit + opex
    depreciation = source("depreciation_amortization")
    ebitda = ebit + depreciation
    total_addbacks = sum(addback_values.values(), ZERO)
    realized_addbacks = sum(
        (addback_values.get(series.series_id, ZERO) for series in model.addbacks
         if series.realization_status == "REALIZED"),
        ZERO,
    )
    unrealized_addbacks = sum(
        (addback_values.get(series.series_id, ZERO) for series in model.addbacks
         if series.realization_status == "UNREALIZED"),
        ZERO,
    )
    not_stated_addbacks = total_addbacks - realized_addbacks - unrealized_addbacks
    adjusted_ebitda = ebitda + total_addbacks
    cfo = source("cfo_ncfo")
    working_capital = source("working_capital_change")
    ffo = cfo - working_capital
    cash_interest = source("cash_interest_paid")
    leases = source("cash_lease_payments")
    cash_taxes = source("cash_taxes_paid")
    ffo_other = ffo - adjusted_ebitda - cash_interest - leases - cash_taxes
    cfo_calc = ffo + working_capital
    cfo_variance = cfo - cfo_calc
    capex = source("capex_and_intangible_investment")
    fcf = cfo + capex
    acquisitions = source("acquisitions_disposals")
    debt_issue_repay = source("net_debt_issue_repay")
    equity_issue_repay = source("net_equity_issue_repay")
    dividends = source("dividends_paid")
    other_investing_financing = source("other_investing_financing")
    ncf = (
        fcf
        + acquisitions
        + debt_issue_repay
        + equity_issue_repay
        + dividends
        + other_investing_financing
    )
    reported_debt = source("total_debt")
    reported_ebitda = source("ebitda")
    reported_adjusted_ebitda = source("adjusted_ebitda")
    reported_net_cash_change = source("net_cash_change")
    ebitda_variance = ebitda - reported_ebitda
    adjusted_ebitda_variance = adjusted_ebitda - reported_adjusted_ebitda
    debt_variance = debt_total - reported_debt
    ncf_variance = ncf - reported_net_cash_change
    segment_variance = segment_total - revenue if model.segments else ZERO

    values = {
        "revenue": revenue,
        "cogs": cogs,
        "gross_profit": gross_profit,
        "gross_margin": _ratio(gross_profit, revenue) or ZERO,
        "opex_including_da": opex,
        "ebit": ebit,
        "depreciation_amortization": depreciation,
        "ebitda_calc": ebitda,
        "ebitda_reported": reported_ebitda,
        "ebitda_variance": ebitda_variance,
        "total_addbacks": total_addbacks,
        "realized_addbacks": realized_addbacks,
        "unrealized_addbacks": unrealized_addbacks,
        "not_stated_addbacks": not_stated_addbacks,
        "adjusted_ebitda_calc": adjusted_ebitda,
        "cash_flow_adjusted_ebitda": adjusted_ebitda,
        "adjusted_ebitda_reported": reported_adjusted_ebitda,
        "adjusted_ebitda_variance": adjusted_ebitda_variance,
        "adjusted_ebitda_margin": _ratio(adjusted_ebitda, revenue) or ZERO,
        "cash_interest_paid": cash_interest,
        "cash_lease_payments": leases,
        "cash_taxes_paid": cash_taxes,
        "working_capital_change": working_capital,
        "ffo": ffo,
        "ffo_other": ffo_other,
        "cfo_ncfo": cfo,
        "cfo_reported": cfo,
        "cfo_calc": cfo_calc,
        "cfo_variance": cfo_variance,
        "capex_and_intangible_investment": capex,
        "fcf": fcf,
        "acquisitions_disposals": acquisitions,
        "net_debt_issue_repay": debt_issue_repay,
        "net_equity_issue_repay": equity_issue_repay,
        "dividends_paid": dividends,
        "other_investing_financing": other_investing_financing,
        "ncf": ncf,
        "net_cash_change": reported_net_cash_change,
        "ncf_variance": ncf_variance,
        "cash_and_equivalents": source("cash_and_equivalents"),
        "rcf_commitment": source("rcf_commitment"),
        "total_debt_calc": debt_total,
        "total_debt_reported": reported_debt,
        "total_debt_variance": debt_variance,
        "secured_debt": secured_debt,
        "unsecured_debt": unsecured_debt,
        "other_debt": other_debt,
        "senior_debt": senior_debt,
        "senior_secured_debt": senior_secured_debt,
        "net_accounts_receivable": source("net_accounts_receivable"),
        "inventory": source("inventory"),
        "accounts_payable": source("accounts_payable"),
        "segment_variance": segment_variance,
    }
    segment_check_actual = segment_total if model.segments else revenue
    segment_check_detail = (
        "Canonical segment schedule reconciles to reported revenue."
        if model.segments
        else "Segment reconciliation is not applicable because no segment schedule was supplied."
    )
    checks = (
        _check(
            "segment_revenue",
            period_id,
            segment_check_actual,
            revenue,
            segment_check_detail,
        ),
        _check(
            "ebitda",
            period_id,
            ebitda,
            reported_ebitda,
            "Calculated EBITDA reconciles to CP-1.",
        ),
        _check(
            "adjusted_ebitda",
            period_id,
            adjusted_ebitda,
            reported_adjusted_ebitda,
            "Calculated adjusted EBITDA reconciles to CP-1.",
        ),
        _check(
            "total_debt",
            period_id,
            debt_total,
            reported_debt,
            "Facility carrying values reconcile to reported total debt.",
        ),
        _check(
            "net_cash_change",
            period_id,
            ncf,
            reported_net_cash_change,
            "Cash-flow bridge reconciles to reported net cash movement.",
        ),
    )
    return (
        PeriodCalculation(
            period,
            values,
            segment_values,
            addback_values,
            debt_values,
            {},
            {},
        ),
        checks,
    )


def _quarter_kpis(
    model: CreditModelIR,
    calculations: Mapping[str, PeriodCalculation],
    index: int,
) -> dict[str, Decimal | None]:
    if index < 3:
        return {
            "total_leverage": None,
            "senior_secured_leverage": None,
            "senior_leverage": None,
            "net_leverage": None,
            "interest_coverage": None,
            "fcf_percent_debt": None,
            "capex_percent_revenue": None,
            "cash_conversion": None,
            "gross_margin": None,
            "adjusted_ebitda_margin": None,
            "dso": None,
            "dsi": None,
            "dpo": None,
        }
    periods = model.quarters[index - 3 : index + 1]
    current = calculations[periods[-1].period_id]
    ltm_adjusted_ebitda = sum(
        calculations[period.period_id].values["adjusted_ebitda_calc"]
        for period in periods
    )
    ltm_interest = sum(
        calculations[period.period_id].values["cash_interest_paid"]
        for period in periods
    )
    ltm_fcf = sum(
        calculations[period.period_id].values["fcf"] for period in periods
    )
    ltm_capex = sum(
        calculations[period.period_id].values["capex_and_intangible_investment"]
        for period in periods
    )
    ltm_revenue = sum(
        calculations[period.period_id].values["revenue"] for period in periods
    )
    ltm_gross_profit = sum(
        calculations[period.period_id].values["gross_profit"]
        for period in periods
    )
    ltm_cogs = sum(
        calculations[period.period_id].values["cogs"] for period in periods
    )
    day_count = Decimal(sum(period.day_count for period in periods))
    debt = current.values["total_debt_reported"]
    cash = current.values["cash_and_equivalents"]
    return {
        "senior_secured_leverage": _ratio(
            current.values["senior_secured_debt"],
            ltm_adjusted_ebitda,
            positive=True,
        ),
        "senior_leverage": _ratio(
            current.values["senior_debt"],
            ltm_adjusted_ebitda,
            positive=True,
        ),
        "total_leverage": _ratio(debt, ltm_adjusted_ebitda, positive=True),
        "net_leverage": _ratio(
            debt - cash, ltm_adjusted_ebitda, positive=True
        ),
        "interest_coverage": _ratio(
            ltm_adjusted_ebitda, abs(ltm_interest), positive=True
        ),
        "fcf_percent_debt": _ratio(ltm_fcf, debt, positive=True),
        "capex_percent_revenue": _ratio(
            abs(ltm_capex), ltm_revenue, positive=True
        ),
        "cash_conversion": _ratio(
            ltm_fcf,
            ltm_adjusted_ebitda,
            positive=True,
        ),
        "gross_margin": _ratio(ltm_gross_profit, ltm_revenue, positive=True),
        "adjusted_ebitda_margin": _ratio(
            ltm_adjusted_ebitda,
            ltm_revenue,
            positive=True,
        ),
        "dso": (
            _ratio(
                current.values["net_accounts_receivable"] * day_count,
                ltm_revenue,
                positive=True,
            )
            if current.values["net_accounts_receivable"] > ZERO
            else None
        ),
        "dsi": (
            _ratio(
                current.values["inventory"] * day_count,
                abs(ltm_cogs),
                positive=True,
            )
            if current.values["inventory"] > ZERO
            else None
        ),
        "dpo": (
            _ratio(
                current.values["accounts_payable"] * day_count,
                abs(ltm_cogs),
                positive=True,
            )
            if current.values["accounts_payable"] > ZERO
            else None
        ),
    }


def _annual_kpis(calculation: PeriodCalculation) -> dict[str, Decimal | None]:
    values = calculation.values
    adjusted_ebitda = values["adjusted_ebitda_calc"]
    debt = values["total_debt_reported"]
    cash = values["cash_and_equivalents"]
    days = Decimal(calculation.period.day_count)
    return {
        "senior_secured_leverage": _ratio(
            values["senior_secured_debt"], adjusted_ebitda, positive=True
        ),
        "senior_leverage": _ratio(
            values["senior_debt"], adjusted_ebitda, positive=True
        ),
        "total_leverage": _ratio(debt, adjusted_ebitda, positive=True),
        "net_leverage": _ratio(
            debt - cash, adjusted_ebitda, positive=True
        ),
        "interest_coverage": _ratio(
            adjusted_ebitda, abs(values["cash_interest_paid"]), positive=True
        ),
        "fcf_percent_debt": _ratio(values["fcf"], debt, positive=True),
        "capex_percent_revenue": _ratio(
            abs(values["capex_and_intangible_investment"]),
            values["revenue"],
            positive=True,
        ),
        "cash_conversion": _ratio(
            values["fcf"], adjusted_ebitda, positive=True
        ),
        "gross_margin": _ratio(
            values["gross_profit"], values["revenue"], positive=True
        ),
        "adjusted_ebitda_margin": _ratio(
            adjusted_ebitda, values["revenue"], positive=True
        ),
        "dso": (
            _ratio(
                values["net_accounts_receivable"] * days,
                values["revenue"],
                positive=True,
            )
            if values["net_accounts_receivable"] > ZERO
            else None
        ),
        "dsi": (
            _ratio(
                values["inventory"] * days,
                abs(values["cogs"]),
                positive=True,
            )
            if values["inventory"] > ZERO
            else None
        ),
        "dpo": (
            _ratio(
                values["accounts_payable"] * days,
                abs(values["cogs"]),
                positive=True,
            )
            if values["accounts_payable"] > ZERO
            else None
        ),
    }


def _period_growth(
    current: PeriodCalculation,
    comparison: PeriodCalculation | None,
) -> dict[str, Decimal | None]:
    growth: dict[str, Decimal | None] = {
        "revenue": None,
        "adjusted_ebitda": None,
    }
    growth.update(
        {f"segment::{series_id}": None for series_id in current.segment_values}
    )
    if comparison is None:
        return growth
    growth["revenue"] = _growth(
        current.values["revenue"], comparison.values["revenue"]
    )
    growth["adjusted_ebitda"] = _growth(
        current.values["adjusted_ebitda_calc"],
        comparison.values["adjusted_ebitda_calc"],
    )
    for series_id, value in current.segment_values.items():
        prior_value = comparison.segment_values.get(series_id)
        if prior_value is not None:
            growth[f"segment::{series_id}"] = _growth(value, prior_value)
    return growth


def _compose_values(
    primitive: Mapping[str, Decimal],
    segment_values: Mapping[str, Decimal],
    addback_values: Mapping[str, Decimal],
    model: CreditModelIR,
) -> dict[str, Decimal]:
    revenue = primitive["revenue"]
    cogs = primitive["cogs"]
    gross_profit = revenue + cogs
    opex = primitive["opex_including_da"]
    ebit = gross_profit + opex
    depreciation = primitive["depreciation_amortization"]
    ebitda = ebit + depreciation
    total_addbacks = sum(addback_values.values(), ZERO)
    realized_addbacks = sum(
        (
            addback_values.get(series.series_id, ZERO)
            for series in model.addbacks
            if series.realization_status == "REALIZED"
        ),
        ZERO,
    )
    unrealized_addbacks = sum(
        (
            addback_values.get(series.series_id, ZERO)
            for series in model.addbacks
            if series.realization_status == "UNREALIZED"
        ),
        ZERO,
    )
    not_stated_addbacks = total_addbacks - realized_addbacks - unrealized_addbacks
    adjusted_ebitda = ebitda + total_addbacks
    reported_ebitda = primitive.get("ebitda_reported", ebitda)
    reported_adjusted_ebitda = primitive.get(
        "adjusted_ebitda_reported", adjusted_ebitda
    )
    cfo = primitive["cfo_reported"]
    working_capital = primitive["working_capital_change"]
    ffo = cfo - working_capital
    cash_interest = primitive["cash_interest_paid"]
    leases = primitive["cash_lease_payments"]
    cash_taxes = primitive["cash_taxes_paid"]
    ffo_other = ffo - adjusted_ebitda - cash_interest - leases - cash_taxes
    capex = primitive["capex_and_intangible_investment"]
    fcf = cfo + capex
    ncf = (
        fcf
        + primitive["acquisitions_disposals"]
        + primitive["net_debt_issue_repay"]
        + primitive["net_equity_issue_repay"]
        + primitive["dividends_paid"]
        + primitive["other_investing_financing"]
    )
    net_cash_change = primitive.get("net_cash_change", ncf)
    total_debt_calc = primitive["total_debt_calc"]
    total_debt_reported = primitive.get("total_debt_reported", total_debt_calc)
    segment_total = sum(segment_values.values(), ZERO)
    return {
        "revenue": revenue,
        "cogs": cogs,
        "gross_profit": gross_profit,
        "gross_margin": _ratio(gross_profit, revenue) or ZERO,
        "opex_including_da": opex,
        "ebit": ebit,
        "depreciation_amortization": depreciation,
        "ebitda_calc": ebitda,
        "ebitda_reported": reported_ebitda,
        "ebitda_variance": ebitda - reported_ebitda,
        "total_addbacks": total_addbacks,
        "realized_addbacks": realized_addbacks,
        "unrealized_addbacks": unrealized_addbacks,
        "not_stated_addbacks": not_stated_addbacks,
        "adjusted_ebitda_calc": adjusted_ebitda,
        "cash_flow_adjusted_ebitda": adjusted_ebitda,
        "adjusted_ebitda_reported": reported_adjusted_ebitda,
        "adjusted_ebitda_variance": adjusted_ebitda - reported_adjusted_ebitda,
        "adjusted_ebitda_margin": _ratio(adjusted_ebitda, revenue) or ZERO,
        "cash_interest_paid": cash_interest,
        "cash_lease_payments": leases,
        "cash_taxes_paid": cash_taxes,
        "working_capital_change": working_capital,
        "ffo": ffo,
        "ffo_other": ffo_other,
        "cfo_ncfo": cfo,
        "cfo_reported": cfo,
        "cfo_calc": ffo + working_capital,
        "cfo_variance": cfo - (ffo + working_capital),
        "capex_and_intangible_investment": capex,
        "fcf": fcf,
        "acquisitions_disposals": primitive["acquisitions_disposals"],
        "net_debt_issue_repay": primitive["net_debt_issue_repay"],
        "net_equity_issue_repay": primitive["net_equity_issue_repay"],
        "dividends_paid": primitive["dividends_paid"],
        "other_investing_financing": primitive["other_investing_financing"],
        "ncf": ncf,
        "net_cash_change": net_cash_change,
        "ncf_variance": ncf - net_cash_change,
        "cash_and_equivalents": primitive["cash_and_equivalents"],
        "rcf_commitment": primitive["rcf_commitment"],
        "total_debt_calc": total_debt_calc,
        "total_debt_reported": total_debt_reported,
        "total_debt_variance": total_debt_calc - total_debt_reported,
        "secured_debt": primitive["secured_debt"],
        "unsecured_debt": primitive["unsecured_debt"],
        "other_debt": primitive["other_debt"],
        "senior_debt": primitive["senior_debt"],
        "senior_secured_debt": primitive["senior_secured_debt"],
        "net_accounts_receivable": primitive["net_accounts_receivable"],
        "inventory": primitive["inventory"],
        "accounts_payable": primitive["accounts_payable"],
        "segment_variance": segment_total - revenue if model.segments else ZERO,
    }


def _primitive_from_components(
    calculations: Mapping[str, PeriodCalculation],
    component_ids: tuple[str, ...],
    balance_period_id: str,
) -> dict[str, Decimal]:
    flow_keys = (
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
    )
    result = {
        key: sum((calculations[item].values[key] for item in component_ids), ZERO)
        for key in flow_keys
    }
    balance = calculations[balance_period_id].values
    for key in (
        "cash_and_equivalents",
        "rcf_commitment",
        "total_debt_calc",
        "total_debt_reported",
        "secured_debt",
        "unsecured_debt",
        "other_debt",
        "senior_debt",
        "senior_secured_debt",
        "net_accounts_receivable",
        "inventory",
        "accounts_payable",
    ):
        result[key] = balance[key]
    return result


def _aggregate_column(
    model: CreditModelIR,
    calculations: Mapping[str, PeriodCalculation],
    column: AnalysisColumn,
) -> ColumnCalculation:
    if column.source_period_id is not None:
        period = calculations[column.source_period_id]
        return ColumnCalculation(
            column,
            dict(period.values),
            dict(period.segment_values),
            dict(period.addback_values),
            dict(period.debt_values),
            dict(period.growth),
            dict(period.kpis),
        )
    if not column.available or column.balance_period_id is None:
        return ColumnCalculation(column, {}, {}, {}, {}, {}, {})
    segment_values = {
        series.series_id: sum(
            (
                calculations[period_id].segment_values.get(series.series_id, ZERO)
                for period_id in column.component_period_ids
            ),
            ZERO,
        )
        for series in model.segments
    }
    addback_values = {
        series.series_id: sum(
            (
                calculations[period_id].addback_values.get(series.series_id, ZERO)
                for period_id in column.component_period_ids
            ),
            ZERO,
        )
        for series in model.addbacks
    }
    balance = calculations[column.balance_period_id]
    primitive = _primitive_from_components(
        calculations,
        column.component_period_ids,
        column.balance_period_id,
    )
    return ColumnCalculation(
        column,
        _compose_values(primitive, segment_values, addback_values, model),
        segment_values,
        addback_values,
        dict(balance.debt_values),
        {},
        {},
    )


def _column_credit_metrics(
    calculation: ColumnCalculation,
) -> dict[str, Decimal | None]:
    if not calculation.values:
        return {}
    values = calculation.values
    column = calculation.column
    annualization = (
        Decimal("365") / Decimal(column.day_count)
        if column.group == "YTD" and column.day_count > 0
        else Decimal("1")
    )
    adjusted_ebitda = values["adjusted_ebitda_calc"] * annualization
    fcf = values["fcf"] * annualization
    interest = values["cash_interest_paid"] * annualization
    debt = values["total_debt_reported"]
    cash = values["cash_and_equivalents"]
    days = Decimal(column.day_count or 365)
    return {
        "senior_secured_leverage": _ratio(
            values["senior_secured_debt"], adjusted_ebitda, positive=True
        ),
        "senior_leverage": _ratio(
            values["senior_debt"], adjusted_ebitda, positive=True
        ),
        "total_leverage": _ratio(debt, adjusted_ebitda, positive=True),
        "net_leverage": _ratio(debt - cash, adjusted_ebitda, positive=True),
        "interest_coverage": _ratio(
            adjusted_ebitda, abs(interest), positive=True
        ),
        "fcf_percent_debt": _ratio(fcf, debt, positive=True),
        "capex_percent_revenue": _ratio(
            abs(values["capex_and_intangible_investment"]),
            values["revenue"],
            positive=True,
        ),
        "cash_conversion": _ratio(fcf, adjusted_ebitda, positive=True),
        "gross_margin": _ratio(
            values["gross_profit"], values["revenue"], positive=True
        ),
        "adjusted_ebitda_margin": _ratio(
            values["adjusted_ebitda_calc"], values["revenue"], positive=True
        ),
        "dso": (
            _ratio(
                values["net_accounts_receivable"] * days,
                values["revenue"],
                positive=True,
            )
            if values["net_accounts_receivable"] > ZERO
            else None
        ),
        "dsi": (
            _ratio(
                values["inventory"] * days,
                abs(values["cogs"]),
                positive=True,
            )
            if values["inventory"] > ZERO
            else None
        ),
        "dpo": (
            _ratio(
                values["accounts_payable"] * days,
                abs(values["cogs"]),
                positive=True,
            )
            if values["accounts_payable"] > ZERO
            else None
        ),
    }


def _forecast_driver_lookup(
    model: CreditModelIR,
) -> dict[tuple[str, str, str, str], Decimal]:
    return {
        (driver.case, driver.period_id, driver.driver_id, driver.slot_id): driver.value
        for driver in model.forecast_drivers
        if driver.value is not None
    }


def _active_forecast_slots(model: CreditModelIR) -> frozenset[str]:
    if not model.segments:
        return frozenset({"DIVISION_1"})

    segment_ids = {segment.series_id for segment in model.segments}
    missing = sorted(segment_ids.difference(model.segment_forecast_slots))
    if missing:
        raise CpModelV3Error(
            f"forecast allocation missing canonical segments: {missing}"
        )
    return frozenset(
        model.segment_forecast_slots[segment_id]
        for segment_id in segment_ids
    )


def _forecast_period_ready(
    model: CreditModelIR,
    case: str,
    period_id: str,
) -> bool:
    ready_growth_slots = {
        driver.slot_id
        for driver in model.forecast_drivers
        if driver.case == case
        and driver.period_id == period_id
        and driver.driver_id == "division_growth"
        and driver.value is not None
    }
    return _active_forecast_slots(model).issubset(ready_growth_slots)


def _forecast_column(
    model: CreditModelIR,
    column: AnalysisColumn,
    prior: ColumnCalculation,
    pro_forma: ColumnCalculation,
    drivers: Mapping[tuple[str, str, str, str], Decimal],
) -> ColumnCalculation:
    if not column.available or not prior.values or not pro_forma.values:
        return ColumnCalculation(column, {}, {}, {}, {}, {}, {})

    driver_period_id = column.forecast_period_id or column.column_id
    segment_values: dict[str, Decimal] = {}
    for series in model.segments:
        slot = model.segment_forecast_slots[series.series_id]
        growth = drivers[(column.case, driver_period_id, "division_growth", slot)]
        segment_values[series.series_id] = (
            prior.segment_values.get(series.series_id, ZERO) * (Decimal("1") + growth)
        )
    revenue = sum(segment_values.values(), ZERO)
    if not segment_values:
        growth = drivers[
            (column.case, driver_period_id, "division_growth", "DIVISION_1")
        ]
        revenue = prior.values["revenue"] * (Decimal("1") + growth)

    pf_revenue = pro_forma.values["revenue"]

    def pf_ratio(key: str, denominator: Decimal = pf_revenue) -> Decimal:
        if denominator == ZERO:
            return ZERO
        return pro_forma.values[key] / denominator

    cogs = revenue * pf_ratio("cogs")
    opex = revenue * pf_ratio("opex_including_da")
    depreciation = revenue * pf_ratio("depreciation_amortization")
    addback_values = dict(pro_forma.addback_values)
    gross_profit = revenue + cogs
    ebit = gross_profit + opex
    ebitda = ebit + depreciation
    adjusted_ebitda = ebitda + sum(addback_values.values(), ZERO)
    cash_interest = (
        pro_forma.values["cash_interest_paid"]
        / pro_forma.values["total_debt_reported"]
        * prior.values["total_debt_reported"]
        if pro_forma.values["total_debt_reported"] != ZERO
        else ZERO
    )
    leases = revenue * pf_ratio("cash_lease_payments")
    cash_taxes = revenue * pf_ratio("cash_taxes_paid")
    working_capital = revenue * pf_ratio("working_capital_change")
    ffo_other = revenue * pf_ratio("ffo_other")
    ffo = adjusted_ebitda + cash_interest + leases + cash_taxes + ffo_other
    cfo = ffo + working_capital
    capex = revenue * pf_ratio("capex_and_intangible_investment")

    def driver(driver_id: str) -> Decimal:
        return drivers.get((column.case, driver_period_id, driver_id, ""), ZERO)

    acquisitions = driver("acquisitions_disposals")
    debt_issue_repay = ZERO
    equity_issue_repay = driver("net_equity_issue_repay")
    dividends = driver("dividends_paid")
    other_investing_financing = driver("other_investing_financing")
    ncf = (
        cfo
        + capex
        + acquisitions
        + debt_issue_repay
        + equity_issue_repay
        + dividends
        + other_investing_financing
    )
    debt_values = dict(pro_forma.debt_values)
    primitive = {
        "revenue": revenue,
        "cogs": cogs,
        "opex_including_da": opex,
        "depreciation_amortization": depreciation,
        "ebitda_reported": ebitda,
        "adjusted_ebitda_reported": adjusted_ebitda,
        "cash_interest_paid": cash_interest,
        "cash_lease_payments": leases,
        "cash_taxes_paid": cash_taxes,
        "cfo_reported": cfo,
        "working_capital_change": working_capital,
        "capex_and_intangible_investment": capex,
        "acquisitions_disposals": acquisitions,
        "net_debt_issue_repay": debt_issue_repay,
        "net_equity_issue_repay": equity_issue_repay,
        "dividends_paid": dividends,
        "other_investing_financing": other_investing_financing,
        "net_cash_change": ncf,
        "cash_and_equivalents": prior.values["cash_and_equivalents"] + ncf,
        "rcf_commitment": prior.values["rcf_commitment"],
        "total_debt_calc": prior.values["total_debt_calc"],
        "total_debt_reported": prior.values["total_debt_reported"],
        "secured_debt": prior.values["secured_debt"],
        "unsecured_debt": prior.values["unsecured_debt"],
        "other_debt": prior.values["other_debt"],
        "senior_debt": prior.values["senior_debt"],
        "senior_secured_debt": prior.values["senior_secured_debt"],
        "net_accounts_receivable": revenue
        * pf_ratio("net_accounts_receivable"),
        "inventory": abs(cogs)
        * (
            pro_forma.values["inventory"] / abs(pro_forma.values["cogs"])
            if pro_forma.values["cogs"] != ZERO
            else ZERO
        ),
        "accounts_payable": abs(cogs)
        * (
            pro_forma.values["accounts_payable"] / abs(pro_forma.values["cogs"])
            if pro_forma.values["cogs"] != ZERO
            else ZERO
        ),
    }
    values = _compose_values(primitive, segment_values, addback_values, model)
    return ColumnCalculation(
        column,
        values,
        segment_values,
        addback_values,
        debt_values,
        {},
        {},
    )


def _analysis_columns(model: CreditModelIR) -> tuple[AnalysisColumn, ...]:
    columns: list[AnalysisColumn] = []
    for index, period in enumerate(model.quarters):
        columns.append(
            AnalysisColumn(
                period.period_id,
                "QUARTER",
                period.display_label,
                period.end_date,
                period.fiscal_year,
                (period.period_id,),
                period.period_id,
                source_period_id=period.period_id,
                comparison_column_id=(
                    model.quarters[index - 4].period_id if index >= 4 else None
                ),
                day_count=period.day_count,
            )
        )

    latest_quarter = model.quarters[-1]
    latest_q = latest_quarter.fiscal_quarter or 4
    latest_fiscal_year = latest_quarter.fiscal_year

    def comparable_end_date(fiscal_year: int) -> date:
        calendar_year = (
            latest_quarter.end_date.year + fiscal_year - latest_fiscal_year
        )
        return date(
            calendar_year,
            latest_quarter.end_date.month,
            min(
                latest_quarter.end_date.day,
                monthrange(calendar_year, latest_quarter.end_date.month)[1],
            ),
        )

    ytd_columns: list[AnalysisColumn] = []
    for fiscal_year in (latest_fiscal_year - 1, latest_fiscal_year):
        components = tuple(
            period
            for period in model.quarters
            if period.fiscal_year == fiscal_year
            and (period.fiscal_quarter or 0) <= latest_q
        )
        available = tuple(period.fiscal_quarter for period in components) == tuple(
            range(1, latest_q + 1)
        )
        end = components[-1] if available else None
        ytd_columns.append(
            AnalysisColumn(
                f"YTD_{fiscal_year}_Q{latest_q}",
                "YTD",
                f"YTD Q{latest_q} FY{fiscal_year % 100:02d}",
                end.end_date if end is not None else comparable_end_date(fiscal_year),
                fiscal_year,
                tuple(period.period_id for period in components) if available else (),
                end.period_id if end is not None else None,
                comparison_column_id=(
                    ytd_columns[0].column_id if ytd_columns else None
                ),
                day_count=(
                    sum(period.day_count for period in components) if available else 0
                ),
                available=available,
            )
        )
    columns.extend(ytd_columns)

    for index, period in enumerate(model.annuals):
        prior = model.annuals[index - 1] if index else None
        comparison_id = (
            prior.period_id
            if prior is not None and prior.fiscal_year == period.fiscal_year - 1
            else None
        )
        columns.append(
            AnalysisColumn(
                period.period_id,
                "FY",
                period.display_label,
                period.end_date,
                period.fiscal_year,
                (period.period_id,),
                period.period_id,
                source_period_id=period.period_id,
                comparison_column_id=comparison_id,
                day_count=period.day_count,
            )
        )

    prior_ltm_year = latest_fiscal_year - 1
    prior_ltm_end = next(
        (
            period
            for period in model.quarters
            if period.fiscal_year == prior_ltm_year
            and period.fiscal_quarter == latest_q
        ),
        None,
    )
    prior_ltm_components: tuple[Period, ...] = ()
    if prior_ltm_end is not None:
        prior_end_index = model.quarters.index(prior_ltm_end)
        if prior_end_index >= 3:
            prior_ltm_components = model.quarters[
                prior_end_index - 3 : prior_end_index + 1
            ]
    prior_ltm_id = (
        f"LTM_{prior_ltm_end.period_id}"
        if prior_ltm_end is not None
        else f"LTM_PRIOR_{prior_ltm_year}_Q{latest_q}"
    )
    prior_ltm = AnalysisColumn(
        prior_ltm_id,
        "LTM",
        f"LTM Q{latest_q} FY{prior_ltm_year % 100:02d}",
        (
            prior_ltm_end.end_date
            if prior_ltm_end is not None
            else comparable_end_date(prior_ltm_year)
        ),
        prior_ltm_year,
        tuple(period.period_id for period in prior_ltm_components),
        prior_ltm_end.period_id if prior_ltm_components else None,
        day_count=sum(period.day_count for period in prior_ltm_components),
        available=bool(prior_ltm_components),
    )
    latest_ltm_components = model.quarters[-4:]
    latest_ltm_end = latest_ltm_components[-1]
    latest_ltm = AnalysisColumn(
        f"LTM_{latest_ltm_end.period_id}",
        "LTM",
        f"LTM {latest_ltm_end.display_label}",
        latest_ltm_end.end_date,
        latest_ltm_end.fiscal_year,
        tuple(period.period_id for period in latest_ltm_components),
        latest_ltm_end.period_id,
        comparison_column_id=prior_ltm.column_id,
        day_count=sum(period.day_count for period in latest_ltm_components),
    )
    ltm_columns = [prior_ltm, latest_ltm]
    columns.extend(ltm_columns)
    pf_column = AnalysisColumn(
        f"PF_{latest_quarter.period_id}",
        "PF",
        "PF (LTM / current debt)",
        latest_quarter.end_date,
        latest_quarter.fiscal_year,
        latest_ltm.component_period_ids,
        latest_quarter.period_id,
        rollforward_column_id=latest_ltm.column_id,
        case="PRO_FORMA",
        day_count=latest_ltm.day_count,
    )
    columns.append(pf_column)

    fiscal_year_end = (
        model.annuals[-1].end_date
        if model.annuals
        else next(
            (
                period.end_date
                for period in reversed(model.quarters)
                if period.fiscal_quarter == 4
            ),
            latest_quarter.end_date,
        )
    )

    forecast_periods = sorted(
        {
            (driver.case, driver.fiscal_year, driver.period_id)
            for driver in model.forecast_drivers
        },
        key=lambda item: (
            0 if item[0] == "BASE" else 1,
            item[1],
            item[2],
        ),
    )
    if not forecast_periods:
        last_historical_year = max(
            latest_quarter.fiscal_year,
            model.annuals[-1].fiscal_year if model.annuals else latest_quarter.fiscal_year,
        )
        forecast_periods = [
            (case, year, f"{case}_FY{year % 100:02d}")
            for case in ("BASE", "DOWNSIDE")
            for year in range(last_historical_year + 1, last_historical_year + 4)
        ]

    def forecast_end_date(fiscal_year: int) -> date:
        return date(
            fiscal_year,
            fiscal_year_end.month,
            min(
                fiscal_year_end.day,
                monthrange(fiscal_year, fiscal_year_end.month)[1],
            ),
        )

    previous_column_by_case: dict[str, str] = {}
    previous_available_by_case: dict[str, bool] = {}
    for case, fiscal_year, period_id in forecast_periods:
        column_id = f"{case}::{period_id}"
        previous_column_id = previous_column_by_case.get(case)
        drivers_ready = bool(model.forecast_drivers) and _forecast_period_ready(
            model,
            case,
            period_id,
        )
        available = drivers_ready and previous_available_by_case.get(case, True)
        columns.append(
            AnalysisColumn(
                column_id,
                case,
                f"{case.title()} FY{fiscal_year % 100:02d}",
                forecast_end_date(fiscal_year),
                fiscal_year,
                (),
                None,
                comparison_column_id=previous_column_id,
                rollforward_column_id=(
                    previous_column_id or pf_column.column_id
                ),
                forecast_period_id=period_id,
                case=case,
                day_count=365,
                available=available,
            )
        )
        previous_column_by_case[case] = column_id
        previous_available_by_case[case] = available
    return tuple(columns)


def _build_column_calculations(
    model: CreditModelIR,
    periods: Mapping[str, PeriodCalculation],
    columns: tuple[AnalysisColumn, ...],
) -> dict[str, ColumnCalculation]:
    result: dict[str, ColumnCalculation] = {}
    pro_forma: ColumnCalculation | None = None
    drivers = _forecast_driver_lookup(model)
    for column in columns:
        if column.group in {"BASE", "DOWNSIDE"}:
            if pro_forma is None:
                raise CpModelV3Error("forecast columns require a pro-forma column")
            prior_id = column.rollforward_column_id or pro_forma.column.column_id
            prior = result[prior_id]
            calculation = _forecast_column(
                model,
                column,
                prior,
                pro_forma,
                drivers,
            )
        else:
            calculation = _aggregate_column(model, periods, column)
        if column.group == "PF":
            pro_forma = calculation
        result[column.column_id] = calculation

    for column in columns:
        calculation = result[column.column_id]
        if not calculation.values:
            continue
        comparison = (
            result.get(column.comparison_column_id)
            if column.comparison_column_id
            else None
        )
        has_yoy_comparison = bool(
            comparison is not None
            and comparison.values
            and (
                column.group in {"QUARTER", "YTD", "FY", "LTM"}
                or (
                    column.group in {"BASE", "DOWNSIDE"}
                    and comparison.column.group == column.group
                )
            )
        )
        growth = {
            "revenue": (
                _growth(calculation.values["revenue"], comparison.values["revenue"])
                if has_yoy_comparison and comparison is not None
                else None
            ),
            "adjusted_ebitda": (
                _growth(
                    calculation.values["adjusted_ebitda_calc"],
                    comparison.values["adjusted_ebitda_calc"],
                )
                if has_yoy_comparison and comparison is not None
                else None
            ),
        }
        for series in model.segments:
            prior_value = (
                comparison.segment_values.get(series.series_id)
                if has_yoy_comparison and comparison is not None
                else None
            )
            growth[f"segment::{series.series_id}"] = (
                _growth(
                    calculation.segment_values.get(series.series_id, ZERO),
                    prior_value,
                )
                if prior_value is not None
                else None
            )
        metrics = (
            dict(calculation.credit_metrics)
            if calculation.credit_metrics
            else _column_credit_metrics(calculation)
        )
        result[column.column_id] = ColumnCalculation(
            column,
            calculation.values,
            calculation.segment_values,
            calculation.addback_values,
            calculation.debt_values,
            growth,
            metrics,
        )
    return result


def calculate(model: CreditModelIR) -> CalculationBook:
    """Calculate and reconcile every selected period independently of Excel."""

    if model.forecast_drivers:
        _active_forecast_slots(model)

    periods: dict[str, PeriodCalculation] = {}
    checks: list[SemanticCheck] = []
    for period in model.periods:
        calculation, period_checks = _calculate_period(model, period)
        periods[period.period_id] = calculation
        checks.extend(period_checks)

    blocking = [check for check in checks if check.status == "BLOCK"]
    if blocking:
        details = "; ".join(
            f"{check.period_id}/{check.check_id}: {check.difference}"
            for check in blocking
        )
        raise CpModelV3Error(f"semantic reconciliation failed: {details}")

    for index, period in enumerate(model.quarters):
        prior = periods[period.period_id]
        comparison = (
            periods[model.quarters[index - 4].period_id]
            if index >= 4
            else None
        )
        periods[period.period_id] = PeriodCalculation(
            prior.period,
            prior.values,
            prior.segment_values,
            prior.addback_values,
            prior.debt_values,
            _period_growth(prior, comparison),
            _quarter_kpis(model, periods, index),
        )
    for index, period in enumerate(model.annuals):
        prior = periods[period.period_id]
        preceding = model.annuals[index - 1] if index else None
        comparison = (
            periods[preceding.period_id]
            if preceding is not None
            and preceding.fiscal_year == period.fiscal_year - 1
            else None
        )
        periods[period.period_id] = PeriodCalculation(
            prior.period,
            prior.values,
            prior.segment_values,
            prior.addback_values,
            prior.debt_values,
            _period_growth(prior, comparison),
            _annual_kpis(prior),
        )
    columns = _analysis_columns(model)
    column_calculations = _build_column_calculations(model, periods, columns)
    return CalculationBook(periods, tuple(checks), columns, column_calculations)
