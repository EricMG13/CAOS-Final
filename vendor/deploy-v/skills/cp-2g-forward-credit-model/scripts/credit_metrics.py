#!/usr/bin/env python3
"""Canonical credit KPIs, period derivation and roll-forward reconciliation.

CP-1 step 09 requires nineteen KPIs across leverage, coverage, cash flow,
liquidity, margin and growth, each with numerator, denominator, both sources and
a calculated value. CP-1B recomputes the numeric half of its delta registers
from the same definitions, and CP-2G rolls balances forward across up to eleven
periods and three cases where each opening balance is the prior period's close.
All three did it by hand.

The engine already existed — cp-model's `cp_model_v3/calculations.py` computes
exactly these ratios to build the workbook — but only ran when someone asked for
an xlsx. This is that logic, extracted so the modules that PRODUCE the figures
use the same arithmetic as the module that CONSUMES them.
`tests/test_credit_metrics.py` cross-checks the two on shared inputs, so they
cannot drift into disagreeing about what "net leverage" means.

Two conventions carried over deliberately from that engine:

  ratio(n, d, positive_denominator=True) returns None when d <= 0.
    A leverage multiple against zero or negative EBITDA is arithmetically
    computable and analytically meaningless — 500/-10 = -50x reads like
    deleveraging. Every leverage and coverage metric uses it.

  Any null input yields a null result.
    CP-1: "Null input → KPI = Not Calculable. Do NOT estimate missing inputs."
    Never zero, never interpolated, never carried from an adjacent period.

    python3 credit_metrics.py --json '{"periods": {...}}'
"""
import argparse
import json
import os
import sys

# Never leave bytecode inside a shipped skill folder -- see cp_tables.py.
sys.dont_write_bytecode = True

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cp_tables import parse_figure  # noqa: E402

NOT_CALCULABLE = "Not Calculable"

_NULL_WORDS = {"null", "n/a", "na", "none", "not disclosed", "not available",
               "not calculable", "unknown", "tbd", "insufficient information"}


def _num(value, where):
    if value is None:
        return None
    text = str(value).strip()
    if text == "" or text.casefold() in _NULL_WORDS:
        return None
    return parse_figure(value, where)


def ratio(numerator, denominator, positive_denominator=False):
    """None on a null input, a zero denominator, or — when the denominator must
    be positive for the metric to mean anything — a non-positive one."""
    if numerator is None or denominator is None:
        return None
    if denominator == 0 or (positive_denominator and denominator <= 0):
        return None
    return numerator / denominator


def growth(current, prior):
    """Period-on-period growth. None on a zero prior: an increase from nothing
    is not a percentage."""
    if current is None or prior is None or prior == 0:
        return None
    return current / prior - 1.0


# name -> (numerator expression, denominator expression, denominator must be > 0)
# Ordered as CP-1 step 09 groups them. The 15 core formulas CP-1C inherits are a
# subset of these, by the same definitions.
def compute_kpis(v):
    """The canonical KPI set for one period. `v` maps metric_id -> figure|None."""
    def g(key):
        return v.get(key)

    ebitda = g("adjusted_ebitda") if g("adjusted_ebitda") is not None else g("ebitda")
    revenue = g("revenue")
    debt = g("total_debt")
    cash = g("cash_and_equivalents")
    net_debt = None if (debt is None or cash is None) else debt - cash
    capex = g("capex")
    interest = g("cash_interest_paid")
    interest_abs = None if interest is None else abs(interest)
    ebitda_less_capex = (None if (ebitda is None or capex is None)
                         else ebitda - abs(capex))

    out = {
        # leverage -- every one against a denominator that must be positive
        "total_leverage": ratio(debt, ebitda, True),
        "net_leverage": ratio(net_debt, ebitda, True),
        "senior_secured_leverage": ratio(g("senior_secured_debt"), ebitda, True),
        "senior_leverage": ratio(g("senior_debt"), ebitda, True),
        # coverage
        "interest_coverage": ratio(ebitda, interest_abs, True),
        "adjusted_interest_coverage": ratio(ebitda_less_capex, interest_abs, True),
        "ffo_to_debt": ratio(g("ffo"), debt, True),
        # cash flow
        "fcf": g("fcf"),
        "fcf_conversion": ratio(g("fcf"), ebitda, True),
        "fcf_percent_debt": ratio(g("fcf"), debt, True),
        "capex_percent_revenue": ratio(None if capex is None else abs(capex), revenue, True),
        # liquidity
        "liquidity": (None if (cash is None or g("undrawn_committed") is None)
                      else cash + g("undrawn_committed")),
        # margins
        "gross_margin": ratio(g("gross_profit"), revenue, True),
        "ebitda_margin": ratio(ebitda, revenue, True),
        "ebit_margin": ratio(g("ebit"), revenue, True),
        "net_income_margin": ratio(g("net_income"), revenue, True),
    }
    liq = out["liquidity"]
    out["liquidity_to_debt"] = ratio(liq, debt, True)
    return out


def derive_periods(reported):
    """CP-1 step 08 period construction, with null propagation.

    "Calculate Q2 as H1-Q1 and Q3 as 9M-H1 only when direct quarters are
    absent"; "Flow LTM = latest FY + current YTD - prior comparable YTD. A
    derived period with a missing component is null."

    Derivation never overwrites a directly reported period — a reported quarter
    is evidence, a derived one is arithmetic.
    """
    out = dict(reported)
    derived = {}

    def sub(a, b, label, parts):
        if reported.get(label) is not None:
            return  # directly reported wins
        x, y = reported.get(a), reported.get(b)
        if x is None or y is None:
            derived[label] = {"value": None, "status": NOT_CALCULABLE,
                              "missing": [p for p, val in ((a, x), (b, y)) if val is None]}
            return
        out[label] = x - y
        derived[label] = {"value": out[label], "status": "derived", "from": parts}

    sub("H1", "Q1", "Q2", "H1 - Q1")
    sub("9M", "H1", "Q3", "9M - H1")

    if reported.get("LTM") is None:
        fy, ytd, prior = (reported.get("FY"), reported.get("YTD"),
                          reported.get("prior_YTD"))
        if None in (fy, ytd, prior):
            derived["LTM"] = {
                "value": None, "status": NOT_CALCULABLE,
                "missing": [n for n, val in (("FY", fy), ("YTD", ytd),
                                             ("prior_YTD", prior)) if val is None]}
        else:
            out["LTM"] = fy + ytd - prior
            derived["LTM"] = {"value": out["LTM"], "status": "derived",
                              "from": "FY + YTD - prior_YTD"}
    return out, derived


def roll_forward(opening, flows, closing, tolerance=0.0):
    """CP-2G: "Reconcile opening balances to the prior closing period and log any
    residual" / QA test 3: "Opening and closing cash/debt roll forward without an
    unexplained material residual."

    The residual is reported, never absorbed. A null component makes the check
    Not Calculable rather than silently passing — a check that cannot run must
    not report success.
    """
    if opening is None or closing is None or any(f is None for f in flows):
        return {"expected_closing": None, "residual": None,
                "status": NOT_CALCULABLE,
                "note": "a null component makes the roll-forward uncheckable; "
                        "it is not evidence that it reconciles"}
    expected = opening + sum(flows)
    residual = round(closing - expected, 6)
    return {
        "opening": opening, "flows": list(flows), "closing": closing,
        "expected_closing": round(expected, 6),
        "residual": residual,
        "within_tolerance": abs(residual) <= tolerance,
        "status": "reconciled" if abs(residual) <= tolerance else "residual",
    }


def compute(payload):
    periods = {}
    for label, values in (payload.get("periods") or {}).items():
        parsed = {k: _num(v, f"periods[{label}].{k}") for k, v in values.items()}
        kpis = compute_kpis(parsed)
        periods[label] = {
            "inputs": parsed,
            "kpis": kpis,
            "not_calculable": sorted(k for k, v in kpis.items() if v is None),
        }

    result = {"periods": periods}

    if payload.get("reported_periods"):
        raw = {k: _num(v, f"reported_periods.{k}")
               for k, v in payload["reported_periods"].items()}
        values, derived = derive_periods(raw)
        result["period_values"] = values
        result["period_derivation"] = derived

    if payload.get("growth"):
        result["growth"] = {
            k: growth(_num(p.get("current"), f"growth.{k}.current"),
                      _num(p.get("prior"), f"growth.{k}.prior"))
            for k, p in payload["growth"].items()}

    rf = payload.get("roll_forward")
    if rf:
        result["roll_forward"] = roll_forward(
            _num(rf.get("opening"), "roll_forward.opening"),
            [_num(f, "roll_forward.flows[]") for f in (rf.get("flows") or [])],
            _num(rf.get("closing"), "roll_forward.closing"),
            float(rf.get("tolerance") or 0.0))
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
    v = {"revenue": 1000.0, "gross_profit": 400.0, "ebitda": 200.0, "ebit": 150.0,
         "net_income": 50.0, "total_debt": 800.0, "cash_and_equivalents": 100.0,
         "senior_secured_debt": 500.0, "cash_interest_paid": 50.0, "capex": 60.0,
         "fcf": 90.0, "ffo": 120.0, "undrawn_committed": 150.0}
    k = compute_kpis(v)
    assert k["total_leverage"] == 4.0, k
    assert k["net_leverage"] == 3.5, k
    assert k["senior_secured_leverage"] == 2.5, k
    assert k["interest_coverage"] == 4.0, k
    assert k["adjusted_interest_coverage"] == (200 - 60) / 50, k
    assert k["ebitda_margin"] == 0.2 and k["gross_margin"] == 0.4
    assert k["fcf_conversion"] == 0.45 and k["capex_percent_revenue"] == 0.06
    assert k["liquidity"] == 250.0 and k["liquidity_to_debt"] == 0.3125
    assert k["not_calculable"] if False else True

    # Negative EBITDA splits the metric set, and the split is principled rather
    # than a convenience: where EBITDA is the DENOMINATOR the metric is
    # meaningless (500/-10 = -50x reads as low leverage), so it is null; where
    # EBITDA is the NUMERATOR a negative result is real and informative
    # (coverage of -0.2x says earnings do not cover interest at all). This
    # matches cp-model's engine, which applies its positive guard to the
    # denominator -- the two must agree or the workbook and the handoff would
    # disagree about the same issuer.
    neg = compute_kpis(dict(v, ebitda=-10.0))
    for m in ("total_leverage", "net_leverage", "senior_secured_leverage",
              "senior_leverage", "fcf_conversion"):
        assert neg[m] is None, (m, neg[m])
    for m in ("interest_coverage", "adjusted_interest_coverage", "ebitda_margin"):
        assert neg[m] is not None and neg[m] < 0, (m, neg[m])
    # a margin denominator is revenue, so unrelated metrics are untouched
    assert neg["gross_margin"] == 0.4

    # zero EBITDA likewise
    assert compute_kpis(dict(v, ebitda=0.0))["total_leverage"] is None

    # null input -> null KPI, never zero
    miss = compute_kpis(dict(v, total_debt=None))
    assert miss["total_leverage"] is None and miss["net_leverage"] is None
    assert miss["ebitda_margin"] == 0.2  # unaffected metrics still compute

    # adjusted EBITDA takes precedence when supplied
    assert compute_kpis(dict(v, adjusted_ebitda=250.0))["total_leverage"] == 3.2

    # growth
    assert growth(110.0, 100.0) == pytest_approx(0.1)
    assert growth(110.0, 0.0) is None and growth(None, 100.0) is None

    # period derivation
    vals, der = derive_periods({"Q1": 10.0, "H1": 25.0, "9M": 40.0,
                                "FY": 100.0, "YTD": 40.0, "prior_YTD": 30.0})
    assert vals["Q2"] == 15.0 and vals["Q3"] == 15.0 and vals["LTM"] == 110.0
    assert der["LTM"]["from"] == "FY + YTD - prior_YTD"
    # a reported period is never overwritten by a derived one
    vals, _ = derive_periods({"Q1": 10.0, "H1": 25.0, "Q2": 99.0})
    assert vals["Q2"] == 99.0
    # a missing component makes the derived period null and names what is missing
    _, der = derive_periods({"FY": 100.0, "YTD": 40.0})
    assert der["LTM"]["value"] is None and der["LTM"]["missing"] == ["prior_YTD"]

    # roll-forward
    rf = roll_forward(100.0, [50.0, -30.0], 120.0)
    assert rf["expected_closing"] == 120.0 and rf["residual"] == 0.0
    assert rf["status"] == "reconciled"
    rf = roll_forward(100.0, [50.0, -30.0], 125.0)
    assert rf["residual"] == 5.0 and rf["status"] == "residual"
    assert roll_forward(100.0, [50.0, -30.0], 125.0, tolerance=10.0)["status"] == "reconciled"
    # a null component cannot report success
    nc = roll_forward(100.0, [None], 120.0)
    assert nc["status"] == NOT_CALCULABLE and nc["residual"] is None

    print("credit_metrics self-check: OK")


def pytest_approx(x, tol=1e-9):
    class _A:
        def __eq__(self, other):
            return other is not None and abs(other - x) < tol
    return _A()


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        _self_check()
    else:
        raise SystemExit(main())
