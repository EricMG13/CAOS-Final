#!/usr/bin/env python3
"""CP-4C / CP-3A claims waterfall, fulcrum identification and EV sensitivity.

CP-4C specifies a waterfall in prose:

    "Use low/base/high enterprise values and show sensitivity to both operating
     metric/cash flow and valuation multiple/discount rate. Deduct supported
     administrative, DIP/new-money, secured priority and transaction costs in
     the order supported by governing evidence. Allocate residual value by
     entity and class."
    "Waterfalls roll without negative/unallocated unexplained value."
    "Do not add a guaranteed claim at multiple entities without eliminating
     double recovery."

The fulcrum — "the class receiving the marginal reorganised equity/value after
senior claims" — is a threshold-crossing result. It flips to a different
security on small arithmetic errors, and the flip IS the module's output. A
two-axis sensitivity over a multi-entity waterfall is a spreadsheet, not a prose
task.

What stays with the analyst: the enterprise value range, the deduction order
(which "the governing evidence" supports, not a convention), whether a claim is
guaranteed at more than one entity, and what the fulcrum means. This computes
the allocation once those are stated.

    python3 recovery_waterfall.py --json '{"enterprise_value": 500, "claims": [...]}'
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


def _num(value, where):
    if value is None:
        return None
    text = str(value).strip()
    if text == "" or text.casefold() in _NULL_WORDS:
        return None
    return parse_figure(value, where)


def waterfall(enterprise_value, claims, costs=()):
    """Allocate value in the supplied claim order, after supported costs.

    A repeated claim_id is rejected to prevent double recovery. An unsupported
    claim amount makes that claim and every junior recovery unknown. The first
    partial recovery identifies the fulcrum; a boundary or zero recovery does not.
    """
    enterprise_value = _num(enterprise_value, "enterprise_value")
    if enterprise_value is None:
        return {"status": NOT_CALCULABLE, "note": "no enterprise value supplied"}
    if enterprise_value < 0:
        raise ValueError("enterprise_value must be nonnegative")

    seen = set()
    for claim in claims:
        claim_id = claim.get("claim_id")
        if not isinstance(claim_id, str) or not claim_id.strip():
            raise ValueError("claim_id must be a non-empty string")
        if claim_id in seen:
            raise ValueError(
                f"claim_id {claim_id!r} appears twice. A claim guaranteed at several entities is "
                "supplied once with its entities listed; repeating it double-counts recovery, "
                "which CP-4C forbids")
        seen.add(claim_id)

    remaining = enterprise_value
    cost_rows = []
    for cost in costs:
        amount = _num(cost.get("amount"), "costs.amount")
        if amount is None:
            return {"status": NOT_CALCULABLE,
                    "note": f"cost {cost.get('label')!r} has no supported amount"}
        if amount < 0:
            raise ValueError("costs.amount must be nonnegative")
        applied = min(amount, max(remaining, 0.0))
        remaining -= applied
        cost_rows.append({"label": cost.get("label"), "amount": amount,
                          "applied": round(applied, 6),
                          "shortfall": round(amount - applied, 6),
                          "remaining_after": round(max(remaining, 0.0), 6)})

    rows, fulcrum = [], None
    for claim in claims:
        claim_id = claim.get("claim_id")
        amount = _num(claim.get("amount"), f"claims[{claim_id}].amount")
        if amount is not None and amount < 0:
            raise ValueError(f"claims[{claim_id}].amount must be nonnegative")
        row = {"claim_id": claim_id, "class": claim.get("class")}
        if amount is None or remaining is None:
            row.update(amount=amount, recovered=None, recovery_pct=None,
                       status=NOT_CALCULABLE, is_fulcrum=None)
            remaining = None
        else:
            recovered = min(amount, max(remaining, 0.0))
            remaining -= recovered
            is_fulcrum = fulcrum is None and 0 < recovered < amount
            if is_fulcrum:
                fulcrum = claim_id
            row.update(
                entities=claim.get("entities"), amount=amount,
                recovered=round(recovered, 6),
                recovery_pct=None if amount == 0 else round(recovered / amount, 6),
                status=("full" if recovered == amount else
                        "partial" if recovered > 0 else "no recovery"),
                is_fulcrum=is_fulcrum,
            )
        rows.append(row)

    incomplete = remaining is None
    residual = None if incomplete else round(max(remaining, 0.0), 6)
    if incomplete:
        allocation = "unknown"
    elif all(row["status"] == "full" for row in rows):
        allocation = "fully repaid"
    elif fulcrum is not None:
        allocation = "partial recovery"
    elif any(row["recovered"] > 0 for row in rows):
        allocation = "class boundary"
    else:
        allocation = "zero recovery"
    return {
        "enterprise_value": enterprise_value,
        "costs": cost_rows,
        "claims": rows,
        "fulcrum_claim_id": fulcrum,
        "residual_to_equity": residual,
        "fully_allocated": None if residual is None else residual == 0.0,
        "allocation_state": allocation,
        "status": NOT_CALCULABLE if incomplete else "complete",
        "note": (None if not incomplete else
                 "one or more claims lack a supported amount; the fulcrum below them is "
                 "not established"),
    }


def sensitivity(claims, ev_cases, costs=()):
    """The two-axis grid CP-4C asks for, reported as fulcrum by EV case.

    The point is not the recovery percentages: it is whether the fulcrum MOVES.
    A fulcrum that is stable across the range is a different finding from one
    that flips between cases, and the prose version tends to report only the
    base case.
    """
    out, fulcra, allocations, computed = [], set(), set(), 0
    for case in ev_cases:
        label = case.get("label") or "(unlabelled)"
        ev = _num(case.get("enterprise_value"), f"ev_cases[{label}]")
        result = waterfall(ev, claims, costs)
        out.append({"case": label, "enterprise_value": ev,
                    "fulcrum_claim_id": result.get("fulcrum_claim_id"),
                    "residual_to_equity": result.get("residual_to_equity"),
                    "allocation_state": result.get("allocation_state", "unknown"),
                    "status": result.get("status")})
        if result.get("status") == "complete":
            computed += 1
            fulcra.add(result.get("fulcrum_claim_id"))
            allocations.add(result["allocation_state"])

    if not computed:
        # Nothing was computed, so nothing is known about stability. Reporting
        # `stable` here would be the strongest claim the module makes, drawn
        # from no arithmetic at all.
        return {"cases": out, "distinct_fulcra": [], "fulcrum_stable": None,
                "status": NOT_CALCULABLE,
                "note": "no case produced a complete waterfall; whether the fulcrum moves "
                        "across the range is not established"}
    if fulcra != {None}:
        note = ("the fulcrum MOVES across the enterprise-value range — the instrument "
                "receiving marginal value depends on which case holds, and a single-case "
                "answer would be misleading" if len(fulcra) > 1 else
                "the fulcrum holds across every case computed")
    elif allocations == {"fully repaid"}:
        note = "no case has a fulcrum: every class is whole in every complete case"
        note += (", with residual value reaching equity" if all(
            row["residual_to_equity"] > 0 for row in out if row["status"] == "complete"
        ) else "; at least one complete case has no residual for equity")
    else:
        note = ("no case has a partial-recovery fulcrum; complete cases show "
                + ", ".join(sorted(allocations)) + ". See each case's allocation state.")
    return {
        "cases": out,
        "distinct_fulcra": sorted(f for f in fulcra if f is not None),
        "fulcrum_stable": None if fulcra == {None} else len(fulcra) == 1,
        "cases_computed": computed,
        "status": "complete" if computed == len(out) else "partial",
        "note": note,
    }


def compute(payload):
    claims = payload.get("claims") or []
    costs = payload.get("costs") or []
    result = {}
    if payload.get("enterprise_value") is not None:
        result["base"] = waterfall(_num(payload["enterprise_value"], "enterprise_value"),
                                   claims, costs)
    if payload.get("ev_cases"):
        result["sensitivity"] = sensitivity(claims, payload["ev_cases"], costs)
    if not result:
        raise ValueError("supply `enterprise_value`, `ev_cases`, or both")
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
    claims = [
        {"claim_id": "RCF", "class": "Super Senior", "amount": 50.0},
        {"claim_id": "TLB", "class": "Senior Secured", "amount": 300.0},
        {"claim_id": "SUN", "class": "Senior Unsecured", "amount": 200.0},
        {"claim_id": "EQ", "class": "Equity", "amount": 0.0},
    ]
    # EV 400: RCF whole, TLB whole, SUN partial -> SUN is the fulcrum
    r = waterfall(400.0, claims)
    assert r["fulcrum_claim_id"] == "SUN", r["fulcrum_claim_id"]
    assert r["claims"][1]["status"] == "full"
    assert abs(r["claims"][2]["recovery_pct"] - 0.25) < 1e-9, r["claims"][2]
    assert r["residual_to_equity"] == 0.0 and r["status"] == "complete"

    # EV 200: TLB is now the fulcrum -- the flip the module exists to surface
    assert waterfall(200.0, claims)["fulcrum_claim_id"] == "TLB"

    # EV above the stack: everyone whole, residual to equity, no fulcrum
    r = waterfall(700.0, claims)
    assert r["fulcrum_claim_id"] is None and r["residual_to_equity"] == 150.0
    assert r["fully_allocated"] is False

    # costs come off the top and are reported with any shortfall
    r = waterfall(400.0, claims, costs=[{"label": "admin", "amount": 20.0}])
    assert r["costs"][0]["applied"] == 20.0 and r["costs"][0]["shortfall"] == 0.0
    assert r["claims"][2]["recovered"] == 30.0, r["claims"][2]

    # double recovery is refused, not silently summed
    try:
        waterfall(400.0, claims + [{"claim_id": "TLB", "class": "Senior Secured", "amount": 300.0}])
    except ValueError as exc:
        assert "double-counts" in str(exc)
    else:
        raise AssertionError("a repeated claim_id must raise")

    # a claim with no supported amount blocks the fulcrum below it
    r = waterfall(400.0, [{"claim_id": "RCF", "class": "SS", "amount": None},
                          {"claim_id": "TLB", "class": "SEN", "amount": 300.0}])
    assert r["status"] == NOT_CALCULABLE and "not established" in r["note"]

    # the sensitivity grid reports whether the fulcrum moves
    s = sensitivity(claims, [{"label": "low", "enterprise_value": 200.0},
                             {"label": "base", "enterprise_value": 400.0},
                             {"label": "high", "enterprise_value": 700.0}])
    assert s["fulcrum_stable"] is False and "MOVES" in s["note"]
    assert s["distinct_fulcra"] == ["SUN", "TLB"], s["distinct_fulcra"]

    stable = sensitivity(claims, [{"label": "a", "enterprise_value": 380.0},
                                  {"label": "b", "enterprise_value": 400.0}])
    assert stable["fulcrum_stable"] is True and "holds across" in stable["note"]

    # nothing computed -> stability is unknown, never "stable"
    blocked = sensitivity([{"claim_id": "A", "amount": None}],
                          [{"label": "low", "enterprise_value": None}])
    assert blocked["fulcrum_stable"] is None and blocked["status"] == NOT_CALCULABLE
    assert "not established" in blocked["note"]

    # every class whole in every case is not the same as a stable fulcrum
    whole = sensitivity(claims, [{"label": "a", "enterprise_value": 900.0},
                                 {"label": "b", "enterprise_value": 800.0}])
    assert whole["distinct_fulcra"] == [] and "no case has a fulcrum" in whole["note"]

    # a partially computable grid says so rather than reporting on the subset
    partial = sensitivity(claims, [{"label": "a", "enterprise_value": 400.0},
                                   {"label": "b", "enterprise_value": None}])
    assert partial["status"] == "partial" and partial["cases_computed"] == 1

    print("recovery_waterfall self-check: OK")


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        _self_check()
    else:
        raise SystemExit(main())
