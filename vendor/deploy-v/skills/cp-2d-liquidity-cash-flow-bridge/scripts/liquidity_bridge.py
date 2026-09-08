#!/usr/bin/env python3
"""CP-2D liquidity bridge, cash burn, runway and Months to Empty.

CP-2D's method already orders this to be scripted --

    REF_CP-2D_STEPS.md:91   "Use Python for all bridge arithmetic."
    REF_CP-2D_STEPS.md:106  "Months to Empty = Beginning accessible liquidity /
                             average monthly cash burn. Use Python for calculation."
    REF_CP-2D_STEPS.md:219  "Use Python for all liquidity runway, bridge total,
                             average monthly cash burn, revolver availability,
                             cash-use, headroom, and Months to Empty calculations."

-- but ships no script, so the code is re-authored from scratch on every run.
This is that script: the same computation, written once, tested, with the null
discipline enforced rather than remembered.

    Ending accessible liquidity =
        beginning accessible liquidity
      + operating cash flow
      + working capital movement
      - cash interest
      - cash taxes
      - mandatory capex
      - debt amortisation and maturities
      - other cash uses
      + committed inflows

Null discipline is the part most worth mechanising. CP-2D is explicit: "Store
unavailable numeric values as null ... not zero". A missing line silently read
as 0 turns an unknown into a favourable fact, and the resulting bridge total
looks entirely plausible. Here, any null component makes the dependent total
null and is reported as a gap.

Months to Empty is null unless burn is genuinely positive: a cash-generative
issuer has no runway to exhaust, and dividing by a negative or zero burn yields
a number that reads like a runway and is not one.

    python3 liquidity_bridge.py --json '{"beginning_accessible_liquidity": 250, ...}'
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

# (field, sign) in bridge order. Sign is how the component enters the total.
BRIDGE_COMPONENTS = [
    ("operating_cash_flow", +1),
    ("working_capital_movement", +1),
    ("cash_interest", -1),
    ("cash_taxes", -1),
    ("mandatory_capex", -1),
    ("debt_amortisation_and_maturities", -1),
    ("other_cash_uses", -1),
    ("committed_inflows", +1),
]

NOT_CALCULABLE = "Not Calculable"


_NULL_WORDS = {"null", "n/a", "na", "none", "not disclosed", "not calculable",
              "unknown", "tbd"}


def _num(value, where):
    """Delegates to cp_tables.parse_figure so every module shares one notation
    policy -- in particular the refusal to guess whether `5,2` means 5.2 or 52."""
    if value is None:
        return None
    text = str(value).strip()
    if text == "" or text.casefold() in _NULL_WORDS:
        return None
    return parse_figure(value, where)


def compute(inputs, period_months=None):
    beginning = _num(inputs.get("beginning_accessible_liquidity"),
                     "beginning_accessible_liquidity")

    components, gaps, total, total_calculable = [], [], 0.0, True
    for field, sign in BRIDGE_COMPONENTS:
        value = _num(inputs.get(field), field)
        components.append({"component": field, "sign": sign, "value": value})
        if value is None:
            gaps.append(field)
            total_calculable = False
        elif total_calculable:
            total += sign * value

    net_movement = round(total, 6) if total_calculable else None
    ending = (round(beginning + net_movement, 6)
              if (beginning is not None and net_movement is not None) else None)

    months = _num(period_months if period_months is not None
                  else inputs.get("period_months"), "period_months")
    if months is not None and months <= 0:
        raise ValueError("period_months must be positive")

    # Burn is net cash CONSUMED per month: positive means depleting.
    if net_movement is not None and months:
        average_monthly_burn = round(-net_movement / months, 6)
    else:
        average_monthly_burn = None

    if (beginning is not None and average_monthly_burn is not None
            and average_monthly_burn > 0):
        months_to_empty = round(beginning / average_monthly_burn, 2)
        mte_note = None
    else:
        months_to_empty = None
        if average_monthly_burn is not None and average_monthly_burn <= 0:
            mte_note = ("no runway to exhaust: the period is cash-generative or flat "
                        "(average monthly burn <= 0)")
        else:
            mte_note = "insufficient inputs"

    return {
        "beginning_accessible_liquidity": beginning,
        "components": components,
        "net_movement": net_movement,
        "ending_accessible_liquidity": ending,
        "period_months": months,
        "average_monthly_burn": average_monthly_burn,
        "months_to_empty": months_to_empty,
        "months_to_empty_note": mte_note,
        "null_components": gaps,
        "status": "complete" if not gaps and ending is not None else "incomplete",
        "display": {
            "ending_accessible_liquidity": NOT_CALCULABLE if ending is None else ending,
            "months_to_empty": NOT_CALCULABLE if months_to_empty is None else months_to_empty,
        },
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", dest="json_input", nargs="?", const="-",
                    help="bridge inputs as a JSON object ('-' or omitted = stdin)")
    ap.add_argument("--period-months", type=float)
    args = ap.parse_args(argv)

    raw = sys.stdin.read() if (args.json_input in (None, "-")) else args.json_input
    try:
        result = compute(json.loads(raw), args.period_months)
        output = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    except (ValueError, OverflowError) as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}), file=sys.stderr)
        return 2
    print(output)
    return 0 if result["status"] == "complete" else 1


def _self_check():
    full = {
        "beginning_accessible_liquidity": 250.0,
        "operating_cash_flow": 60.0, "working_capital_movement": -20.0,
        "cash_interest": 30.0, "cash_taxes": 5.0, "mandatory_capex": 40.0,
        "debt_amortisation_and_maturities": 25.0, "other_cash_uses": 10.0,
        "committed_inflows": 0.0, "period_months": 12,
    }
    r = compute(full)
    # 60 - 20 - 30 - 5 - 40 - 25 - 10 + 0 = -70
    assert r["net_movement"] == -70.0, r
    assert r["ending_accessible_liquidity"] == 180.0, r
    assert r["average_monthly_burn"] == round(70 / 12, 6), r
    assert r["months_to_empty"] == round(250 / (70 / 12), 2), r
    assert r["status"] == "complete"

    # a null component must poison the total, never be read as zero
    missing = dict(full, cash_taxes=None)
    r = compute(missing)
    assert r["net_movement"] is None and r["ending_accessible_liquidity"] is None, r
    assert r["display"]["ending_accessible_liquidity"] == NOT_CALCULABLE
    assert r["null_components"] == ["cash_taxes"], r
    assert r["status"] == "incomplete"

    # zero is a real figure and must NOT be treated as missing
    zeroed = dict(full, cash_taxes=0.0)
    assert compute(zeroed)["net_movement"] == -65.0

    # cash-generative: no runway, and no bogus negative Months to Empty
    generative = dict(full, operating_cash_flow=200.0)
    r = compute(generative)
    assert r["net_movement"] == 70.0 and r["average_monthly_burn"] < 0
    assert r["months_to_empty"] is None and "cash-generative" in r["months_to_empty_note"]

    # string nulls parse as null, string figures parse as figures
    assert compute(dict(full, other_cash_uses="n/a"))["net_movement"] is None
    assert compute(dict(full, other_cash_uses="1,010"))["net_movement"] == -1070.0

    try:
        compute(dict(full, period_months=0))
    except ValueError:
        pass
    else:
        raise AssertionError("period_months=0 must raise, not divide")

    print("liquidity_bridge self-check: OK")


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        _self_check()
    else:
        raise SystemExit(main())
