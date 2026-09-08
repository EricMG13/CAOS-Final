#!/usr/bin/env python3
"""CP-3C funding gap: maturities due in a window vs liquidity and forecast FCF.

CP-3C maps the maturity wall (T3D.2) and assesses liquidity/market access
(T3D.3) but never subtracts one from the other, so "refinancing pressure" is
argued qualitatively when it is an arithmetic question: how much falls due
inside the window, and how much of it the issuer can meet from its own
resources.

The module's own traps are the ones this encodes:

  - "Debt=BS carrying value(current+long-term, net issuance costs); log gross
     delta" — gross is recorded next to carrying value, never reconciled to it.
  - "Subsequent event: flag date; never blend into period figures" — the
     as-of-date view and the pro-forma view are computed separately and
     labelled, never merged.
  - "null≠zero" — an instrument with no supported amount blocks the total
     instead of contributing nothing to it.
  - A revolver cannot fund a maturity that falls after the revolver itself
     expires. That one is not in the entry text and is the error the arithmetic
     makes visible.

    python3 funding_gap.py --json '{"horizon_years": 2, "currency": "USD", "instruments": [...]}'
"""
import argparse
import json
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cp_tables import parse_figure  # noqa: E402

NOT_CALCULABLE = "Not Calculable"
_NULL_WORDS = {"null", "n/a", "na", "none", "not disclosed", "not available",
               "not calculable", "unknown", "tbd", "insufficient information"}
MATERIAL_GROSS_DELTA = 0.05


def _num(value, where):
    if value is None:
        return None
    text = str(value).strip()
    if text == "" or text.casefold() in _NULL_WORDS:
        return None
    return parse_figure(value, where)


def _currency_guard(items, label):
    ccy = {str(i.get("currency")).strip().upper() for i in items if i.get("currency")}
    if len(ccy) > 1:
        return (f"{label} span multiple currencies {sorted(ccy)}; convert at a disclosed "
                "rate before totalling")
    return None


def maturity_wall(instruments, horizon_years):
    """Amount falling due inside the horizon, with the gross/carrying delta logged."""
    due, beyond, unresolved, conflicts = [], [], [], []
    for inst in instruments:
        name = inst.get("instrument")
        amount = _num(inst.get("amount"), f"instruments[{name}].amount")
        years = _num(inst.get("years_to_maturity"), f"instruments[{name}].years_to_maturity")
        gross = _num(inst.get("gross_principal"), f"instruments[{name}].gross_principal")
        if gross is not None and amount not in (None, 0) and \
                abs(gross - amount) / abs(amount) >= MATERIAL_GROSS_DELTA:
            # Both figures recorded, neither chosen. Canon Core item 6.
            conflicts.append({"instrument": name, "carrying_value": amount,
                              "gross_principal": gross,
                              "note": "materially different bases; log both in the Definition "
                                      "Conflict Register, do not reconcile"})
        row = {"instrument": name, "amount": amount, "years_to_maturity": years,
               "currency": inst.get("currency")}
        if amount is None or years is None:
            row["status"] = NOT_CALCULABLE
            unresolved.append(row)
        elif years <= horizon_years:
            due.append(row)
        else:
            beyond.append(row)

    ccy_note = _currency_guard(due, "maturities inside the horizon")
    if unresolved or ccy_note:
        total = None
    else:
        total = round(sum(r["amount"] for r in due), 6)
    return {
        "horizon_years": horizon_years,
        "due_within_horizon": due,
        "beyond_horizon": beyond,
        "unresolved": unresolved,
        "total_due": total,
        "definition_conflicts": conflicts,
        "status": "complete" if total is not None else NOT_CALCULABLE,
        "reason": (ccy_note if ccy_note else
                   (None if not unresolved else
                    "instruments without a supported amount or maturity are excluded from the "
                    "total; the wall is Not Calculable, not the sum of what happens to be known")),
    }


def available_liquidity(cash=None, facilities=(), horizon_years=None, cash_currency=None):
    """Cash plus undrawn committed capacity that survives the horizon.

    An undrawn revolver expiring inside the window cannot fund a maturity that
    falls after it expires. Counting it whole is the standard overstatement, so
    a facility maturing before the horizon end is excluded and reported.
    """
    rows, usable, excluded = [], [], []
    for f in facilities:
        name = f.get("facility")
        limit = _num(f.get("commitment"), f"facilities[{name}].commitment")
        drawn = _num(f.get("drawn"), f"facilities[{name}].drawn")
        expiry = _num(f.get("years_to_expiry"), f"facilities[{name}].years_to_expiry")
        committed = f.get("committed")
        undrawn = None if (limit is None or drawn is None) else round(limit - drawn, 6)
        row = {"facility": name, "commitment": limit, "drawn": drawn,
               "undrawn": undrawn, "years_to_expiry": expiry,
               "committed": committed, "currency": f.get("currency")}
        if undrawn is None:
            row["counted"], row["reason"] = False, "undrawn capacity not calculable"
        elif committed is not True:
            # Uncommitted lines are withdrawable at the lender's discretion; a
            # refinancing analysis cannot lean on them. `committed` absent is not
            # an assertion that it is committed.
            row["counted"], row["reason"] = False, (
                "not asserted committed; uncommitted capacity is withdrawable and is not "
                "counted as available liquidity")
        elif horizon_years is not None and expiry is None:
            row["counted"], row["reason"] = False, "expiry not supplied; cannot test against horizon"
        elif horizon_years is not None and expiry < horizon_years:
            row["counted"], row["reason"] = False, (
                f"expires at {expiry}y, inside the {horizon_years}y horizon; it cannot fund "
                "maturities falling after its own expiry")
        else:
            row["counted"], row["reason"] = True, None
        rows.append(row)
        (usable if row["counted"] else excluded).append(row)

    # Cash carries a currency too. Leaving it out let a EUR revolver be added to
    # a USD cash balance without the guard noticing.
    ccy_note = _currency_guard(usable + [{"currency": cash_currency}],
                               "cash and the counted facilities")
    if cash is None or ccy_note:
        total = None
    else:
        total = round(cash + sum(r["undrawn"] for r in usable), 6)
    return {
        "cash": cash,
        "facilities": rows,
        "counted_facilities": [r["facility"] for r in usable],
        "excluded_facilities": [{"facility": r["facility"], "reason": r["reason"]}
                                for r in excluded],
        "total_available": total,
        "status": "complete" if total is not None else NOT_CALCULABLE,
        "reason": ccy_note or (None if cash is not None else "no supported cash balance"),
    }


def gap(total_due, liquidity_total, forecast_fcf=None):
    """Sources minus uses. Negative coverage is the finding, not an error."""
    if total_due is None or liquidity_total is None:
        return {"status": NOT_CALCULABLE,
                "reason": "the maturity wall or available liquidity is not calculable; "
                          "a gap computed from a partial total would understate it"}
    # Forecast FCF absent is not zero FCF -- but a gap against liquidity alone is
    # still a real, narrower statement, so it is reported with the basis named.
    sources = liquidity_total + (forecast_fcf or 0.0)
    shortfall = round(total_due - sources, 6)
    return {
        "maturities_due": total_due,
        "liquidity": liquidity_total,
        "forecast_fcf": forecast_fcf,
        "total_sources": round(sources, 6),
        "funding_gap": shortfall if shortfall > 0 else 0.0,
        "surplus": round(-shortfall, 6) if shortfall < 0 else 0.0,
        "coverage_ratio": None if total_due == 0 else round(sources / total_due, 6),
        "basis": ("liquidity plus forecast free cash flow" if forecast_fcf is not None
                  else "liquidity only — no forecast FCF supplied, which is not the same as "
                       "zero forecast FCF; the gap below is an upper bound on internal coverage"),
        "status": "complete",
        "finding": ("internally coverable" if shortfall <= 0 else
                    "external refinancing required for the shortfall"),
    }


def compute(payload):
    horizon = _num(payload.get("horizon_years"), "horizon_years")
    if horizon is None:
        raise ValueError("horizon_years is required: a funding gap is only meaningful over a "
                         "stated window")
    if horizon < 0:
        raise ValueError("horizon_years must be nonnegative")
    fcf = _num(payload.get("forecast_fcf"), "forecast_fcf")
    currency = payload.get("currency")
    if not isinstance(currency, str) or len(currency.strip()) != 3 or not currency.strip().isascii() or not currency.strip().isalpha():
        raise ValueError("currency must explicitly name the three-letter reporting currency")
    currency = currency.strip().upper()

    def view(instruments, cash_key="cash", fac_key="facilities"):
        # Omitted row currencies inherit the explicitly declared reporting basis.
        instruments = [dict(item, currency=item.get("currency", currency)) for item in instruments]
        facilities = [dict(item, currency=item.get("currency", currency))
                      for item in payload.get(fac_key) or ()]
        cash_currency = payload.get(cash_key + "_currency", currency)
        wall = maturity_wall(instruments, horizon)
        liq = available_liquidity(_num(payload.get(cash_key), cash_key),
                                  facilities, horizon, cash_currency)
        currencies = wall["due_within_horizon"] + [row for row in liq["facilities"] if row["counted"]]
        currencies += [{"currency": cash_currency}, {"currency": currency}]
        if fcf is not None:
            currencies.append({"currency": payload.get("forecast_fcf_currency", currency)})
        invalid = any(not isinstance(row["currency"], str) or not row["currency"].strip()
                      for row in currencies)
        reason = ("a monetary input has no stated currency" if invalid else
                  _currency_guard(currencies, "debt, liquidity and forecast FCF"))
        funding = ({"status": NOT_CALCULABLE, "reason": reason} if reason else
                   gap(wall["total_due"], liq["total_available"], fcf))
        funding["currency"] = currency
        return {"maturity_wall": wall, "liquidity": liq,
                "gap": funding}

    result = {"as_of_balance_sheet_date": view(payload.get("instruments") or [])}
    if payload.get("pro_forma_instruments"):
        # Canon Core item 7: a post-balance-sheet refinancing is a separate,
        # labelled view. Never blended into the as-of figures above.
        # A refinancing usually changes the facilities and the cash balance too,
        # so both can be restated; absent, the as-of figures carry over.
        result["pro_forma_for_subsequent_events"] = view(
            payload["pro_forma_instruments"],
            cash_key="pro_forma_cash" if "pro_forma_cash" in payload else "cash",
            fac_key="pro_forma_facilities" if "pro_forma_facilities" in payload else "facilities")
        result["pro_forma_note"] = (
            "computed on the post-event capital structure supplied separately; flag the event "
            "date in the Subsequent Events entry. The two views are never blended.")
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", dest="json_input", nargs="?", const="-")
    args = ap.parse_args(argv)
    raw = sys.stdin.read() if (args.json_input in (None, "-")) else args.json_input
    try:
        result = compute(json.loads(raw))
        output = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    except (ValueError, OverflowError) as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}), file=sys.stderr)
        return 2
    print(output)
    return 0


def _self_check():
    inst = [
        {"instrument": "RCF", "amount": 100.0, "years_to_maturity": 1.5, "currency": "USD"},
        {"instrument": "TLB", "amount": 400.0, "years_to_maturity": 4.0, "currency": "USD"},
    ]
    w = maturity_wall(inst, 2.0)
    assert w["total_due"] == 100.0 and len(w["beyond_horizon"]) == 1, w

    # null != zero: an unresolved instrument blocks the total
    w = maturity_wall(inst + [{"instrument": "Notes", "amount": None,
                               "years_to_maturity": 1.0}], 2.0)
    assert w["total_due"] is None and w["status"] == NOT_CALCULABLE, w

    # gross vs carrying value: both logged, neither chosen
    w = maturity_wall([{"instrument": "TLB", "amount": 400.0, "gross_principal": 440.0,
                        "years_to_maturity": 1.0}], 2.0)
    assert w["definition_conflicts"][0]["gross_principal"] == 440.0
    assert w["total_due"] == 400.0, "the carrying value is the canonical basis"
    # an immaterial delta is not a conflict
    assert maturity_wall([{"instrument": "TLB", "amount": 400.0, "gross_principal": 401.0,
                           "years_to_maturity": 1.0}], 2.0)["definition_conflicts"] == []

    # currencies are not summed
    w = maturity_wall([{"instrument": "A", "amount": 100.0, "years_to_maturity": 1.0, "currency": "USD"},
                       {"instrument": "B", "amount": 100.0, "years_to_maturity": 1.0, "currency": "EUR"}], 2.0)
    assert w["total_due"] is None and "multiple currencies" in w["reason"]

    # a revolver expiring inside the horizon is excluded, and says why
    liq = available_liquidity(50.0, [{"facility": "RCF", "commitment": 200.0, "drawn": 50.0,
                                      "years_to_expiry": 1.0, "committed": True}],
                              horizon_years=3.0)
    assert liq["total_available"] == 50.0, liq
    assert "cannot fund maturities falling after its own expiry" in liq["excluded_facilities"][0]["reason"]

    # one surviving the horizon counts its undrawn portion
    liq = available_liquidity(50.0, [{"facility": "RCF", "commitment": 200.0, "drawn": 50.0,
                                      "years_to_expiry": 5.0, "committed": True}],
                              horizon_years=3.0)
    assert liq["total_available"] == 200.0, liq

    # uncommitted capacity is never counted, and absent != committed
    liq = available_liquidity(50.0, [{"facility": "Uncommitted", "commitment": 100.0,
                                      "drawn": 0.0, "years_to_expiry": 5.0}], horizon_years=3.0)
    assert liq["total_available"] == 50.0 and "withdrawable" in liq["excluded_facilities"][0]["reason"]

    # a facility in another currency is not added to the cash balance
    liq = available_liquidity(50.0, [{"facility": "EUR RCF", "commitment": 100.0, "drawn": 0.0,
                                      "years_to_expiry": 5.0, "committed": True,
                                      "currency": "EUR"}],
                              horizon_years=3.0, cash_currency="USD")
    assert liq["total_available"] is None and "multiple currencies" in liq["reason"], liq

    # the gap itself
    g = gap(400.0, 150.0, 50.0)
    assert g["funding_gap"] == 200.0 and g["surplus"] == 0.0
    assert abs(g["coverage_ratio"] - 0.5) < 1e-9 and "external refinancing" in g["finding"]
    g = gap(100.0, 150.0, 50.0)
    assert g["funding_gap"] == 0.0 and g["surplus"] == 100.0 and g["finding"] == "internally coverable"

    # absent forecast FCF is stated as a basis, not silently taken as zero
    g = gap(400.0, 150.0)
    assert g["forecast_fcf"] is None and "not the same as" in g["basis"]

    # a partial wall never produces a gap
    assert gap(None, 150.0, 0.0)["status"] == NOT_CALCULABLE

    # as-of and pro-forma stay separate
    r = compute({"horizon_years": 2.0, "currency": "USD", "cash": 50.0, "instruments": inst,
                 "pro_forma_instruments": [{"instrument": "TLB", "amount": 400.0,
                                            "years_to_maturity": 6.0}]})
    assert r["as_of_balance_sheet_date"]["gap"]["funding_gap"] == 50.0
    assert r["pro_forma_for_subsequent_events"]["maturity_wall"]["total_due"] == 0.0
    assert "never blended" in r["pro_forma_note"]

    # a refinancing that also changed the cash balance restates it in the
    # pro-forma view only; the as-of view keeps the balance-sheet-date figure
    r = compute({"horizon_years": 2.0, "currency": "USD", "cash": 50.0, "instruments": inst,
                 "pro_forma_cash": 500.0,
                 "pro_forma_instruments": [{"instrument": "TLB", "amount": 400.0,
                                            "years_to_maturity": 6.0}]})
    assert r["as_of_balance_sheet_date"]["liquidity"]["cash"] == 50.0
    assert r["pro_forma_for_subsequent_events"]["liquidity"]["cash"] == 500.0

    try:
        compute({"cash": 50.0, "instruments": inst})
    except ValueError as exc:
        assert "horizon_years is required" in str(exc)
    else:
        raise AssertionError("a gap with no window must be refused")

    print("funding_gap self-check: OK")


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        _self_check()
    else:
        raise SystemExit(main())
