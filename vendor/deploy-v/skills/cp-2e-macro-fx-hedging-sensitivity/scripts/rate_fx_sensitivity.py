#!/usr/bin/env python3
"""CP-2E rate, FX and cost sensitivity arithmetic.

CP-2E already orders this to be scripted (SKILL.md "Calculation Rules" 1: "Use
Python for all rate sensitivity, gross/hedged/unhedged floating-rate debt,
unhedged debt percentage, FX sensitivity, commodity/raw-material cost
sensitivity, inflation sensitivity, and FCF impact calculations") and ships no
script. Definitions are taken verbatim from the module's own Core Calculation
Definitions:

    Unhedged floating-rate debt = Gross floating-rate debt - Hedged floating-rate debt
    Unhedged debt percentage    = Unhedged floating-rate debt / Total debt
    +100 bps cash-interest impact = Unhedged floating-rate debt x 1.00%

What deliberately stays with the analyst: deciding whether a disclosed hedge is
economically effective. CP-2E is explicit that notional alone does not count --
"Do not treat notional hedge amount as effective cash-flow protection unless
instrument, covered exposure, rate/strike, maturity, and coverage period are
sufficiently disclosed". That is a documentary-sufficiency judgment about a
credit agreement, and it is the analysis. This script takes the hedged figure
the analyst has already qualified and does the arithmetic on it.

The guard that earns its place here: hedged debt exceeding gross floating-rate
debt is rejected rather than clamped. It means the two figures came from
different perimeters (or a hedge was double-counted), and silently flooring
unhedged exposure at zero would report an issuer as fully protected precisely
when the inputs are least trustworthy.

Percentages are returned as decimals, per Calculation Rule 8.

    python3 rate_fx_sensitivity.py --json '{"gross_floating_rate_debt": 500, ...}'
"""
import argparse
import json
import sys

import os
# Never leave bytecode inside a shipped skill folder. These scripts import a
# sibling (cp_tables), and Python writes __pycache__/*.pyc next to an imported
# module -- so running one from inside the distributed package pollutes the
# package itself, and any integrity check over the tree then reports drift
# against files the build never emitted. Same reason, same line, as the
# packaged CLIs (credit_os_v_cli.py, export_cp_model_v3.py).
sys.dont_write_bytecode = True

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cp_tables import parse_figure, AmbiguousFigure  # noqa: E402

BPS_SHOCK = 0.01  # +100 bps, per the module's definition


_NULL_WORDS = {"null", "n/a", "na", "none", "not disclosed", "unknown", "tbd",
              "insufficient information"}


def _num(value, where):
    """Delegates to cp_tables.parse_figure so every module shares one notation
    policy -- in particular the refusal to guess whether `5,2` means 5.2 or 52."""
    if value is None:
        return None
    text = str(value).strip()
    if text == "" or text.casefold() in _NULL_WORDS:
        return None
    return parse_figure(value, where)


def compute(inputs):
    gross = _num(inputs.get("gross_floating_rate_debt"), "gross_floating_rate_debt")
    hedged = _num(inputs.get("hedged_floating_rate_debt"), "hedged_floating_rate_debt")
    total_debt = _num(inputs.get("total_debt"), "total_debt")

    for name, value in (("gross_floating_rate_debt", gross),
                        ("hedged_floating_rate_debt", hedged),
                        ("total_debt", total_debt)):
        if value is not None and value < 0:
            raise ValueError(f"{name} is negative ({value})")

    if gross is not None and hedged is not None and hedged > gross:
        raise ValueError(
            f"hedged floating-rate debt ({hedged}) exceeds gross floating-rate debt "
            f"({gross}) -- perimeters differ or a hedge is double-counted; "
            "resolve the inputs rather than reporting zero unhedged exposure"
        )

    unhedged = gross - hedged if (gross is not None and hedged is not None) else None

    if unhedged is not None and total_debt:
        unhedged_pct = round(unhedged / total_debt, 6)
    else:
        unhedged_pct = None

    rate_impact = round(unhedged * BPS_SHOCK, 6) if unhedged is not None else None

    gaps = [n for n, v in (("gross_floating_rate_debt", gross),
                           ("hedged_floating_rate_debt", hedged),
                           ("total_debt", total_debt)) if v is None]

    fx = []
    for row in inputs.get("fx_exposures", []) or []:
        exposure = _num(row.get("net_exposure"), "fx_exposures.net_exposure")
        move = _num(row.get("adverse_move_pct"), "fx_exposures.adverse_move_pct")
        if move is not None and abs(move) > 1:
            # Rule 8: decimals. 10 would be a 1000% move.
            raise ValueError(
                f"fx adverse_move_pct {move} must be a decimal (0.10 = 10%), per "
                "CP-2E calculation rule 8"
            )
        impact = round(exposure * move, 6) if (exposure is not None and move is not None) else None
        fx.append({
            "currency": row.get("currency"),
            "net_exposure": exposure,
            "adverse_move_pct": move,
            "impact": impact,
        })

    cost = []
    for row in inputs.get("cost_exposures", []) or []:
        spend = _num(row.get("annual_spend"), "cost_exposures.annual_spend")
        move = _num(row.get("adverse_move_pct"), "cost_exposures.adverse_move_pct")
        if move is not None and abs(move) > 1:
            raise ValueError(
                f"cost adverse_move_pct {move} must be a decimal (0.10 = 10%), per "
                "CP-2E calculation rule 8"
            )
        impact = round(spend * move, 6) if (spend is not None and move is not None) else None
        cost.append({
            "input": row.get("input"),
            "annual_spend": spend,
            "adverse_move_pct": move,
            "impact": impact,
        })

    known = [x["impact"] for x in fx + cost if x["impact"] is not None]
    incomplete = any(x["impact"] is None for x in fx + cost)
    combined = None
    if rate_impact is not None and not incomplete:
        combined = round(rate_impact + sum(known), 6)

    return {
        "gross_floating_rate_debt": gross,
        "hedged_floating_rate_debt": hedged,
        "unhedged_floating_rate_debt": unhedged,
        "unhedged_debt_percentage": unhedged_pct,
        "rate_shock_bps": 100,
        "cash_interest_impact_plus_100bps": rate_impact,
        "fx_sensitivity": fx,
        "cost_sensitivity": cost,
        "combined_adverse_annual_impact": combined,
        "null_inputs": gaps,
        "status": "complete" if not gaps and not incomplete else "incomplete",
    }


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
    return 0 if result["status"] == "complete" else 1


def _self_check():
    r = compute({
        "gross_floating_rate_debt": 500.0, "hedged_floating_rate_debt": 300.0,
        "total_debt": 1000.0,
        "fx_exposures": [{"currency": "EUR", "net_exposure": 120.0, "adverse_move_pct": 0.10}],
        "cost_exposures": [{"input": "energy", "annual_spend": 80.0, "adverse_move_pct": 0.25}],
    })
    assert r["unhedged_floating_rate_debt"] == 200.0, r
    assert r["unhedged_debt_percentage"] == 0.2, r
    assert r["cash_interest_impact_plus_100bps"] == 2.0, r
    assert r["fx_sensitivity"][0]["impact"] == 12.0, r
    assert r["cost_sensitivity"][0]["impact"] == 20.0, r
    assert r["combined_adverse_annual_impact"] == 34.0, r
    assert r["status"] == "complete"

    # null total_debt: percentage null, but the rate impact still computes
    r = compute({"gross_floating_rate_debt": 500.0, "hedged_floating_rate_debt": 300.0,
                 "total_debt": None})
    assert r["unhedged_debt_percentage"] is None and r["cash_interest_impact_plus_100bps"] == 2.0
    assert r["status"] == "incomplete"

    # fully hedged is legitimate
    assert compute({"gross_floating_rate_debt": 100.0, "hedged_floating_rate_debt": 100.0,
                    "total_debt": 500.0})["unhedged_floating_rate_debt"] == 0.0

    for bad, why in (
        ({"gross_floating_rate_debt": 100.0, "hedged_floating_rate_debt": 150.0,
          "total_debt": 500.0}, "over-hedged must raise, not clamp to zero"),
        ({"gross_floating_rate_debt": -1.0, "hedged_floating_rate_debt": 0.0,
          "total_debt": 5.0}, "negative debt must raise"),
        ({"gross_floating_rate_debt": 1.0, "hedged_floating_rate_debt": 0.0, "total_debt": 5.0,
          "fx_exposures": [{"currency": "EUR", "net_exposure": 10, "adverse_move_pct": 10}]},
         "percent-as-integer must raise"),
    ):
        try:
            compute(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(why)

    # zero total debt must not divide
    assert compute({"gross_floating_rate_debt": 0.0, "hedged_floating_rate_debt": 0.0,
                    "total_debt": 0.0})["unhedged_debt_percentage"] is None
    print("rate_fx_sensitivity self-check: OK")


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        _self_check()
    else:
        raise SystemExit(main())
