#!/usr/bin/env python3
"""CP-3D bond analytics: yield, spread, and break-even default.

CP-3D names the conventions and supplies no formula:

    "Lock settlement date, day count, compounding, clean/dirty price, accrued
     interest, yield-to-maturity/worst/call, benchmark curve, OAS/z-spread/
     discount-margin convention, duration and FX basis."
    "Break-even default/loss calculations must disclose recovery, horizon,
     discounting, timing and whether default is one-period or cumulative."

These are the highest-error-rate calculations in credit and the ones where a
wrong answer is least visible: a 120bp break-even and a 180bp break-even both
look plausible. Yield-to-worst across a call schedule is the worst of them,
because it is a minimum over several yields and picking the wrong one is
invisible in the output.

Conventions are stated in the output, never assumed silently — CP-3D requires
them disclosed, and two desks using different day counts get different yields
from the same price.

    python3 bond_analytics.py --json '{"price": 98.5, "coupon": 6.0, ...}'
"""
import argparse
import json
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cp_tables import parse_figure  # noqa: E402

NOT_CALCULABLE = "Not Calculable"
_NULL_WORDS = {"null", "n/a", "na", "none", "not disclosed", "not available",
               "not calculable", "unknown", "tbd", "insufficient information"}

# Actual/365 fixed. Named, not assumed: CP-3D requires the day count disclosed,
# and a different convention gives a different yield from the same price.
DEFAULT_CONVENTION = {
    "day_count": "ACT/365F",
    "compounding": "semi-annual",
    "price_basis": "clean price per 100 nominal at coupon-date settlement; zero accrued interest",
}


def _num(value, where):
    if value is None:
        return None
    text = str(value).strip()
    if text == "" or text.casefold() in _NULL_WORDS:
        return None
    return parse_figure(value, where)


def _pv(rate, cashflows):
    """Present value of (time_in_years, amount) at a semi-annual rate."""
    if rate <= -1:
        return float("inf")
    return sum(cf / (1 + rate / 2) ** (2 * t) for t, cf in cashflows)


def yield_to(price, cashflows, tol=1e-10, lo=-0.99, hi=10.0):
    """Solve for the semi-annual-compounded yield by bisection.

    Bisection rather than Newton: it cannot diverge, and a bond price is
    monotonic in yield so the bracket is guaranteed. A failed solve returns None
    rather than the last iterate.
    """
    if price is None or price <= 0 or not cashflows:
        return None
    f_lo, f_hi = _pv(lo, cashflows) - price, _pv(hi, cashflows) - price
    if f_lo * f_hi > 0:
        return None  # no sign change: the price is outside any solvable yield
    for _ in range(400):
        mid = (lo + hi) / 2
        f_mid = _pv(mid, cashflows) - price
        if abs(f_mid) < tol:
            return mid
        if f_lo * f_mid < 0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid
    return (lo + hi) / 2


def _schedule(coupon, years, redemption=100.0, freq=2):
    """(time, cashflow) pairs to a redemption date, per 100 nominal."""
    if years <= 0 or coupon < 0 or redemption <= 0:
        raise ValueError("schedule requires positive years/redemption and a nonnegative coupon")
    periods = years * freq
    # ponytail: regular schedules only, capped at 1000 payments; use dated cash flows for stubs.
    if not math.isfinite(periods) or periods > 1000 or not math.isclose(periods, round(periods), rel_tol=0, abs_tol=1e-9):
        raise ValueError("unsupported schedule: supply a regular semiannual coupon-date horizon, without stub periods")
    n = round(periods)
    per = coupon / freq
    return [((i / freq), per + (redemption if i == n else 0.0)) for i in range(1, n + 1)]


def compute(payload):
    conv = dict(DEFAULT_CONVENTION)
    supplied = payload.get("convention", {})
    if not isinstance(supplied, dict) or any(conv.get(key) != value for key, value in supplied.items()):
        raise ValueError("unsupported convention: only ACT/365F, semiannual compounding and zero-accrued coupon-date prices are supported")
    accrued = _num(payload.get("accrued_interest", 0), "accrued_interest")
    if accrued != 0 or payload.get("settlement_date") is not None:
        raise ValueError("dated settlement and accrued interest require a dated cash-flow engine")

    price = _num(payload.get("price"), "price")
    coupon = _num(payload.get("coupon"), "coupon")
    years = _num(payload.get("years_to_maturity"), "years_to_maturity")
    if coupon is None or price is None:
        return {"status": NOT_CALCULABLE, "convention": conv,
                "missing": [k for k, v in (("price", price), ("coupon", coupon))
                            if v is None]}
    if price <= 0:
        raise ValueError("price must be positive")

    ytm = (yield_to(price, _schedule(coupon, years)) if years is not None else None)

    # Yield to worst across the call schedule. The minimum is the point: a
    # premium bond's worst case is usually the earliest call, and reporting YTM
    # there overstates the return an investor can actually be held to.
    calls, worst = [], None
    for c in payload.get("call_schedule", []) or []:
        cy = _num(c.get("years"), "call_schedule.years")
        cp = _num(c.get("price"), "call_schedule.price")
        if cy is None or cp is None:
            calls.append({"years": cy, "call_price": cp, "yield": None,
                          "status": NOT_CALCULABLE})
            continue
        y = yield_to(price, _schedule(coupon, cy, redemption=cp))
        calls.append({"years": cy, "call_price": cp, "yield": y})
    candidates = [c["yield"] for c in calls if c.get("yield") is not None]
    if ytm is not None:
        candidates.append(ytm)
    if candidates and ytm is not None and all(c.get("yield") is not None for c in calls):
        worst = min(candidates)

    benchmark = _num(payload.get("benchmark_yield"), "benchmark_yield")
    spread = (round((worst - benchmark) * 10000, 2)
              if (worst is not None and benchmark is not None) else None)

    # Break-even default rate: the annual default probability at which the
    # spread exactly compensates for expected loss. CP-3D requires recovery,
    # horizon and whether the rate is annual or cumulative all disclosed.
    recovery = _num(payload.get("recovery_assumption"), "recovery_assumption")
    if recovery is not None and not 0 <= recovery <= 1:
        raise ValueError(f"recovery_assumption {recovery} must be a decimal between 0 and 1")
    breakeven = None
    if spread is not None and recovery is not None:
        lgd = 1 - recovery
        if lgd != 0:
            annual = (spread / 10000) / lgd
            if not 0 <= annual <= 1:
                raise ValueError("spread and recovery imply a break-even default rate outside 0 to 1; this probability model does not apply")
            breakeven = round(annual, 6)

    horizon = _num(payload.get("horizon_years"), "horizon_years")
    if horizon is not None and horizon < 0:
        raise ValueError("horizon_years must be nonnegative")
    cumulative = (None if (breakeven is None or horizon is None)
                  else round(1 - (1 - breakeven) ** horizon, 6))

    return {
        "convention": conv,
        "price": price,
        "yield_to_maturity": None if ytm is None else round(ytm, 6),
        "call_schedule": calls,
        "yield_to_worst": None if worst is None else round(worst, 6),
        "worst_is_maturity": bool(worst is not None and ytm is not None and worst == ytm),
        "benchmark_yield": benchmark,
        "spread_bps": spread,
        "recovery_assumption": recovery,
        "breakeven_default_annual": breakeven,
        "breakeven_default_cumulative": cumulative,
        "horizon_years": horizon,
        "disclosure": (
            "Break-even is the annual default rate at which the spread exactly offsets "
            "expected loss at the stated recovery; the cumulative figure compounds it over "
            "the stated horizon. It is a break-even, not a forecast, and not a probability "
            "the market is quoting."),
        "status": "complete" if worst is not None else NOT_CALCULABLE,
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
    # a par bond yields its coupon
    r = compute({"price": 100.0, "coupon": 6.0, "years_to_maturity": 5.0})
    assert abs(r["yield_to_maturity"] - 0.06) < 1e-6, r["yield_to_maturity"]

    # discount bond yields more than coupon; premium yields less
    assert compute({"price": 95.0, "coupon": 6.0, "years_to_maturity": 5.0})["yield_to_maturity"] > 0.06
    assert compute({"price": 105.0, "coupon": 6.0, "years_to_maturity": 5.0})["yield_to_maturity"] < 0.06

    # yield to worst on a premium bond is the early call, not maturity
    r = compute({"price": 105.0, "coupon": 6.0, "years_to_maturity": 5.0,
                 "call_schedule": [{"years": 1.0, "price": 102.0}]})
    assert r["yield_to_worst"] < r["yield_to_maturity"], r
    assert r["worst_is_maturity"] is False

    # on a discount bond maturity IS the worst; the flag says so
    r = compute({"price": 95.0, "coupon": 6.0, "years_to_maturity": 5.0,
                 "call_schedule": [{"years": 1.0, "price": 102.0}]})
    assert r["worst_is_maturity"] is True, r

    # spread and break-even
    r = compute({"price": 100.0, "coupon": 6.0, "years_to_maturity": 5.0,
                 "benchmark_yield": 0.04, "recovery_assumption": 0.4,
                 "horizon_years": 5.0})
    assert abs(r["spread_bps"] - 200.0) < 0.5, r["spread_bps"]
    assert abs(r["breakeven_default_annual"] - (0.02 / 0.6)) < 1e-6, r
    assert 0 < r["breakeven_default_cumulative"] < 1
    assert r["breakeven_default_cumulative"] > r["breakeven_default_annual"]

    # 100% recovery means no loss to compensate: no break-even exists
    r = compute({"price": 100.0, "coupon": 6.0, "years_to_maturity": 5.0,
                 "benchmark_yield": 0.04, "recovery_assumption": 1.0})
    assert r["breakeven_default_annual"] is None, r

    # recovery must be a decimal
    try:
        compute({"price": 100.0, "coupon": 6.0, "years_to_maturity": 5.0,
                 "benchmark_yield": 0.04, "recovery_assumption": 40})
    except ValueError:
        pass
    else:
        raise AssertionError("recovery outside 0-1 must raise")

    # missing inputs are Not Calculable, never defaulted
    assert compute({"coupon": 6.0})["status"] == NOT_CALCULABLE
    r = compute({"price": 100.0, "coupon": 6.0, "years_to_maturity": 5.0})
    assert r["spread_bps"] is None and r["breakeven_default_annual"] is None

    # the convention is always reported
    assert r["convention"]["day_count"] == "ACT/365F"
    try:
        compute({"price": 100.0, "coupon": 6.0, "years_to_maturity": 5.0,
                 "convention": {"day_count": "30/360"}})
    except ValueError:
        pass
    else:
        raise AssertionError("unsupported conventions must not be echoed as calculated")

    print("bond_analytics self-check: OK")


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        _self_check()
    else:
        raise SystemExit(main())
