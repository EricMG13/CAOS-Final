#!/usr/bin/env python3
"""CP-4A covenant headroom, incremental debt capacity and basket capacity.

The sign flip is why this is script work. CP-4A states two formulas that look
almost identical and are opposites:

    REF_CP-4A_STEPS.md "Core Formulas (Where Legally Supported)":
      "Maintenance headroom = covenant threshold - current tested ratio
       (max-ratio tests)."
      "Coverage headroom = current tested ratio - covenant threshold
       (min-ratio tests)."

A leverage covenant is a ceiling (higher is worse); a coverage covenant is a
floor (higher is better). Apply one formula to both and the number still looks
like headroom -- right magnitude, right units, wrong sign -- so a breach reads
as cushion. Nothing downstream catches it, because a plausible number is exactly
what a reader expects there.

So `test_type` is a REQUIRED input with no default and no inference. Guessing it
from the test's name ("leverage" -> max-ratio) would reintroduce the failure
this module exists to remove, on the one input where being wrong is invisible.

What stays with the analyst, because CP-4A reserves it:
  - which EBITDA definition governs. Step 04 instruction 5: "Apply Calculation
    Rules: use governing legal definitions, not reported EBITDA." The caller
    passes the ratio computed on the governing basis; this module never derives
    it from reported figures.
  - whether baskets may be stacked. "Do not add overlapping baskets unless the
    legal document permits independent use" and "If capacity can be used through
    multiple routes, record each but do not sum as independent capacity." This
    module therefore refuses to total a set of baskets unless the caller has
    asserted independence per basket.
  - severity. The Severity Framework is definitional prose (Low/Moderate/High/
    Critical) with no numeric thresholds anywhere in the module; assigning it is
    an interpretation of creditor outcome.
  - whether a capacity figure is legally supported at all. Canon Core 9: "Never
    infer covenant capacity; absent inputs = `Not Calculable`."

    python3 covenant_headroom.py --json '{"tests": [...], "baskets": [...]}'
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

MAX_RATIO = "max-ratio"   # ceiling: leverage, net debt/EBITDA -- higher is worse
MIN_RATIO = "min-ratio"   # floor: interest coverage, FCCR -- higher is better
TEST_TYPES = {MAX_RATIO, MIN_RATIO}

# Accepted spellings for the two directions. Deliberately explicit: an
# unrecognised value raises rather than defaulting to either direction.
TEST_TYPE_ALIASES = {
    "max-ratio": MAX_RATIO, "max_ratio": MAX_RATIO, "maximum": MAX_RATIO,
    "maintenance": MAX_RATIO, "ceiling": MAX_RATIO, "incurrence-max": MAX_RATIO,
    "min-ratio": MIN_RATIO, "min_ratio": MIN_RATIO, "minimum": MIN_RATIO,
    "coverage": MIN_RATIO, "floor": MIN_RATIO, "incurrence-min": MIN_RATIO,
}

# CP-4A uses two literals for "no number here", in different places, and they
# are not interchangeable:
#   headroom, missing inputs -> Step 04 instruction 4: "If exact headroom
#     unsupported, state [Insufficient Information] and identify whether the
#     missing item is: current tested ratio, covenant definition, denominator,
#     numerator, threshold, or basket usage."
#   capacity, absent inputs  -> Canon Core 9: "Never infer covenant capacity;
#     absent inputs=`Not Calculable`."
# Each is used where its own source says to use it.
NOT_CALCULABLE = "Not Calculable"
INSUFFICIENT = "[Insufficient Information]"


_NULL_WORDS = {"null", "n/a", "na", "none", "not disclosed", "not available",
              "not calculable", "unknown", "tbd", "insufficient information",
              "[insufficient information]"}


def _num(value, where):
    """Delegates to cp_tables.parse_figure so every module shares one notation
    policy -- in particular the refusal to guess whether `5,2` means 5.2 or 52."""
    if value is None:
        return None
    text = str(value).strip()
    if text == "" or text.casefold() in _NULL_WORDS:
        return None
    return parse_figure(value, where)


def normalise_test_type(raw, where):
    if raw is None:
        raise ValueError(
            f"{where}: test_type is required and has no default. A max-ratio "
            "(leverage-style ceiling) and a min-ratio (coverage-style floor) "
            "headroom differ only in sign, so an assumed direction produces a "
            "plausible number with the wrong sign"
        )
    key = str(raw).strip().casefold().replace(" ", "-")
    if key in TEST_TYPE_ALIASES:
        return TEST_TYPE_ALIASES[key]
    raise ValueError(
        f"{where}: unrecognised test_type {raw!r}; use one of "
        f"{sorted(TEST_TYPES)} (aliases: {sorted(TEST_TYPE_ALIASES)})"
    )


def headroom(test):
    """One row of T4C.4.

    Headroom is signed and expressed in the same units as the ratio: positive
    means compliant, negative means the test is already breached, zero means
    exactly at the threshold. Zero is reported as `At threshold` rather than
    folded into compliant -- a covenant tested at exactly its limit has no
    cushion, and calling that compliant is the reading that gets people paged.
    """
    name = test.get("test") or "(unnamed test)"
    where = f"tests[{name}]"
    test_type = normalise_test_type(test.get("test_type"), where)
    threshold = _num(test.get("threshold"), f"{where}.threshold")
    current = _num(test.get("current_ratio"), f"{where}.current_ratio")

    row = {
        "test": name,
        "test_type": test_type,
        "threshold": threshold,
        "current_ratio": current,
        "formula": ("threshold - current" if test_type == MAX_RATIO
                    else "current - threshold"),
    }

    if threshold is None or current is None:
        missing = [k for k, v in (("threshold", threshold), ("current tested ratio", current))
                   if v is None]
        row.update({
            "headroom": None,
            "headroom_display": INSUFFICIENT,
            "status": INSUFFICIENT,
            # Step 04 instruction 4 requires naming WHICH input is missing.
            "missing_inputs": missing,
        })
        return row

    value = threshold - current if test_type == MAX_RATIO else current - threshold
    value = round(_num(value, f"{where}.headroom"), 6)
    row["headroom"] = value
    row["headroom_display"] = value
    row["status"] = ("Breached" if value < 0 else
                     "At threshold" if value == 0 else "Compliant")
    return row


def max_additional_debt(test):
    """Incremental debt before a max-ratio leverage test breaches.

    At the limit:  (current_debt + x) / governing_ebitda = threshold
                => x = threshold * governing_ebitda - current_debt

    Only defined for a max-ratio test against an EBITDA-denominated ratio, and
    only where the caller supplies the GOVERNING EBITDA -- the covenant's own
    definition, not reported EBITDA (Step 04 instruction 5).
    """
    name = test.get("test") or "(unnamed test)"
    where = f"tests[{name}]"
    test_type = normalise_test_type(test.get("test_type"), where)
    if test_type != MAX_RATIO:
        return None
    ebitda = _num(test.get("governing_ebitda"), f"{where}.governing_ebitda")
    debt = _num(test.get("current_debt"), f"{where}.current_debt")
    threshold = _num(test.get("threshold"), f"{where}.threshold")
    if None in (ebitda, debt, threshold):
        return {"value": None, "status": INSUFFICIENT, "missing_inputs": [
            k for k, v in (("governing_ebitda", ebitda), ("current_debt", debt),
                           ("threshold", threshold)) if v is None]}
    if ebitda <= 0:
        # Solving against a non-positive denominator yields a negative or
        # infinite "capacity". There is no incremental-debt answer here; the
        # honest output is that the test cannot be solved.
        return {"value": None, "status": NOT_CALCULABLE, "note": (
            f"governing EBITDA is {ebitda}; a leverage threshold cannot be solved "
            "for incremental debt on a non-positive denominator")}
    value = round(threshold * ebitda - debt, 6)
    return {
        "value": value,
        "formula": "threshold * governing_ebitda - current_debt",
        "status": "capacity" if value > 0 else "already beyond the threshold",
        "note": None if value >= 0 else (
            "negative: current debt already exceeds what the threshold supports"),
    }


def trigger_headroom(trigger):
    """CP-2H T2R.4: signed headroom to a rating-agency trigger, across cases.

    Same sign hazard as a covenant test, so the same implementation rather than a
    second one: CP-2H's method says "For quantitative triggers preserve
    directionality. A maximum leverage trigger and a minimum coverage trigger
    require different headroom formulas." Direction comes from the register's own
    `trigger direction` column — required, never inferred.

    Two rules the module states that a per-period headroom alone would miss:

      "An agency phrase such as 'sustained' requires multi-period testing; a
       point-in-time breach is not automatically a trigger."
      "Where the agency supplies a range rather than a hard threshold, show
       distance to both bounds."

    `sustained_periods` optionally names the ordered observation window required
    by the governing agency rule (at least two distinct period labels). Every
    period in that window must breach within the SAME case. Without that rule,
    repeated breaches are observations, not proof that a sustained trigger holds.
    """
    name = trigger.get("trigger") or "(unnamed trigger)"
    where = f"triggers[{name}]"
    direction = normalise_test_type(trigger.get("trigger_direction"), where)

    lower = _num(trigger.get("threshold_lower"), f"{where}.threshold_lower")
    upper = _num(trigger.get("threshold_upper"), f"{where}.threshold_upper")
    point = _num(trigger.get("threshold"), f"{where}.threshold")
    if point is None and lower is None and upper is None:
        raise ValueError(f"{where}: supply `threshold`, or `threshold_lower`/`threshold_upper` for a range")
    if point is not None and (lower is not None or upper is not None):
        raise ValueError(f"{where}: supply either a point threshold or a range, not both")

    bounds = {"threshold": point} if point is not None else {
        k: v for k, v in (("lower", lower), ("upper", upper)) if v is not None}

    def signed(value, threshold):
        difference = threshold - value if direction == MAX_RATIO else value - threshold
        return round(_num(difference, f"{where}.headroom"), 6)

    window = trigger.get("sustained_periods")
    if window is not None and (
        not isinstance(window, list) or len(window) < 2
        or any(not isinstance(period, str) or not period.strip() for period in window)
        or len(set(window)) != len(window)
    ):
        raise ValueError(f"{where}.sustained_periods must name at least two distinct ordered periods")

    binding = min(bounds.values()) if direction == MAX_RATIO else max(bounds.values())
    periods, breaches, cases = [], {}, {}
    for row in trigger.get("cases", []) or []:
        label = row.get("period") or row.get("case") or "(unlabelled)"
        case = row.get("case") or "default"
        if not isinstance(label, str) or not isinstance(case, str):
            raise ValueError(f"{where}: period and case labels must be strings")
        observations = cases.setdefault(case, {})
        if label in observations:
            raise ValueError(f"{where}: duplicate period {label!r} in case {case!r}")
        value = _num(row.get("value"), f"{where}.cases[{label}].value")
        if value is None:
            observations[label] = INSUFFICIENT
            periods.append({"period": label, "case": case, "value": None, "headroom": None,
                            "status": INSUFFICIENT})
            continue
        entry = {"period": label, "case": case, "value": value,
                 "headroom": {k: signed(value, t) for k, t in bounds.items()}}
        # Breach against the binding bound: for a max-ratio trigger the tighter
        # bound is the lower number; for a min-ratio trigger it is the higher.
        h = signed(value, binding)
        entry["binding_threshold"] = binding
        entry["binding_headroom"] = h
        entry["status"] = "Breached" if h < 0 else "At threshold" if h == 0 else "Compliant"
        observations[label] = entry["status"]
        if h < 0:
            breaches[label] = None
        periods.append(entry)

    sustained_cases = [case for case, observations in cases.items() if window and all(
        observations.get(period) == "Breached" for period in window
    )]
    unknown = not periods or any(row["status"] == INSUFFICIENT for row in periods)
    if window:
        unknown = unknown or any(
            period not in observations for observations in cases.values() for period in window
        )
    repeated = any(sum(status == "Breached" for status in observations.values()) > 1
                   for observations in cases.values())
    sustained = (True if sustained_cases else None if unknown or (repeated and window is None) else False)
    classification = ("sustained breach" if sustained else
                      "multiple-period breaches — sustained duration not established" if repeated and window is None else
                      "point-in-time breach — not automatically a trigger" if breaches else
                      "insufficient information" if unknown else "no breach")
    return {
        "trigger": name,
        "trigger_direction": direction,
        "thresholds": bounds,
        "is_range": point is None,
        "periods": periods,
        "breach_periods": list(breaches),
        # "a point-in-time breach is not automatically a trigger"
        "classification": classification,
        "sustained": sustained,
        "sustained_periods": window,
        "sustained_cases": sustained_cases,
        "note": (None if not point else
                 "point threshold; agencies often publish a range — confirm before treating "
                 "this as a hard bound"),
    }


def basket_capacity(basket):
    """One row of T4C.5.

    Grower basket: "greater of fixed amount and % of applicable base".
    Builder basket: "retained ECF/CNI/available amount build-up + permitted
    additions - documented usage". Fixed: "fixed amount - documented utilization".
    """
    name = basket.get("basket") or "(unnamed basket)"
    where = f"baskets[{name}]"
    if "type" not in basket:
        raise ValueError(
            f"{where}: basket `type` is required (fixed | grower | builder). It used to "
            "default to 'fixed', which reads a grower basket as its fixed component "
            "alone and silently understates capacity")
    kind = str(basket.get("type")).strip().casefold()

    # Usage must be stated, and an absent usage is NOT zero usage.
    #
    # Every basket formula in CP-4A subtracts "documented utilization". Reading
    # an unknown utilisation as 0 reports the entire basket as available -- the
    # largest possible capacity figure, produced from the least information, in
    # the direction that understates creditor risk. Canon Core 9 is explicit:
    # "Never infer covenant capacity; absent inputs = `Not Calculable`."
    #
    # `permitted_additions` deliberately keeps a 0 default: omitting it
    # UNDERSTATES capacity, which is the safe direction and matches "no
    # additions documented".
    usage_stated = "usage" in basket
    usage = _num(basket.get("usage"), f"{where}.usage")
    if usage is not None and usage < 0:
        raise ValueError(f"{where}: usage is negative ({usage})")

    row = {"basket": name, "type": kind, "usage": usage}
    if usage is None:
        row["usage_display"] = NOT_CALCULABLE
        row["missing_inputs"] = ["usage" if usage_stated else "usage (not supplied)"]

    if kind == "fixed":
        gross = _num(basket.get("fixed_amount"), f"{where}.fixed_amount")
        row["formula"] = "fixed_amount - usage"
    elif kind == "grower":
        # "Grower basket = greater of fixed amount and % of applicable base
        # (or exact formulation as drafted)." The parenthetical matters: plain
        # greater-of is the common drafting, not the only one, and reading a
        # builder-style or capped grower as a greater-of silently changes the
        # capacity. Whether the clause IS a plain greater-of is a reading of the
        # document, so the caller states it; a non-standard formulation must
        # arrive as an explicit drafted amount rather than be approximated.
        formulation = str(basket.get("formulation", "greater-of")).strip().casefold()
        if formulation not in {"greater-of", "as-drafted"}:
            raise ValueError(
                f"{where}: formulation {formulation!r} must be 'greater-of' (plain "
                "greater-of drafting) or 'as-drafted' (supply drafted_amount)")
        if formulation == "as-drafted":
            gross = _num(basket.get("drafted_amount"), f"{where}.drafted_amount")
            if gross is None:
                raise ValueError(
                    f"{where}: formulation is 'as-drafted' but no drafted_amount was "
                    "supplied -- the clause's own formulation governs and cannot be "
                    "inferred from a fixed amount and a percentage")
            row.update({"formula": "as drafted (analyst-supplied), less usage"})
        else:
            fixed = _num(basket.get("fixed_amount"), f"{where}.fixed_amount")
            pct = _num(basket.get("percentage"), f"{where}.percentage")
            base = _num(basket.get("base_amount"), f"{where}.base_amount")
            if pct is not None and abs(pct) > 1:
                raise ValueError(
                    f"{where}: percentage {pct} must be a decimal (0.10 = 10%)")
            grown = pct * base if (pct is not None and base is not None) else None
            gross = None if (fixed is None or grown is None) else max(fixed, grown)
            row.update({"fixed_component": fixed, "grown_component": grown,
                        "formula": "greater of fixed_amount and (percentage * base_amount), less usage"})
        row["formulation"] = formulation
    elif kind == "builder":
        parts = {
            "build_up": _num(basket.get("build_up"), f"{where}.build_up"),
            "permitted_additions": _num(basket.get("permitted_additions"),
                                        f"{where}.permitted_additions") or 0.0,
        }
        gross = (None if parts["build_up"] is None
                 else parts["build_up"] + parts["permitted_additions"])
        row.update({"components": parts,
                    "formula": "build_up + permitted_additions - usage"})
    else:
        raise ValueError(f"{where}: unknown basket type {kind!r}; expected fixed, grower or builder")

    if gross is not None:
        row["gross_capacity"] = round(gross, 6)
    if gross is None or usage is None:
        row.setdefault("gross_capacity", None)
        row.update({"remaining_capacity": None, "remaining_display": NOT_CALCULABLE,
                    "status": NOT_CALCULABLE})
        missing = row.get("missing_inputs", [])
        if gross is None:
            missing = missing + ["basket amount inputs"]
        row["missing_inputs"] = missing
        return row

    remaining = round(gross - usage, 6)
    row.update({
        "remaining_capacity": remaining,
        "remaining_display": remaining,
        # Usage exceeding the basket is a real state (reclassification,
        # retesting, or a documented overrun). Reporting max(0, x) would erase
        # it; the negative is the finding.
        "status": ("available" if remaining > 0 else
                   "exhausted" if remaining == 0 else "over-utilised"),
    })
    if remaining < 0:
        row["note"] = "documented usage exceeds the basket -- verify reclassification or shared caps"
    return row


def aggregate_capacity(rows, baskets):
    """Total only where the caller has asserted each basket is independently usable.

    "Do not add overlapping baskets unless the legal document permits
    independent use" / "If capacity can be used through multiple routes, record
    each but do not sum as independent capacity."

    So independence is opt-in per basket, and a set with even one unasserted
    basket produces no total at all -- a partial sum labelled as a total is the
    error this guard exists to prevent.
    """
    independent, dependent = [], []
    for row, basket in zip(rows, baskets):
        (independent if basket.get("independently_usable") is True
         else dependent).append(row["basket"])

    if dependent:
        return {
            "total_capacity": None,
            "status": NOT_CALCULABLE,
            "reason": (
                "not summed: " + ", ".join(sorted(dependent)) +
                " are not asserted independently usable. CP-4A forbids adding "
                "overlapping baskets unless the document permits independent use; "
                "each route is recorded above, not totalled"),
            "independently_usable": sorted(independent),
        }

    currencies = {str(b.get("currency")).strip().upper()
                  for b in baskets if b.get("currency")}
    if len(currencies) > 1:
        # "Currency must be consistent ... or exchange rates disclosed." Adding
        # a EUR basket to a USD basket produces a number in no currency at all.
        return {
            "total_capacity": None, "status": NOT_CALCULABLE,
            "reason": f"baskets span multiple currencies {sorted(currencies)}; "
                      "convert at a disclosed rate before totalling",
            "currencies": sorted(currencies),
        }

    values = [r["remaining_capacity"] for r in rows]
    if any(v is None for v in values):
        return {"total_capacity": None, "status": NOT_CALCULABLE,
                "reason": "at least one basket has no calculable remaining capacity"}
    return {
        "total_capacity": round(sum(values), 6),
        "status": "summed",
        "reason": "every basket asserted independently usable by the analyst",
        "independently_usable": sorted(independent),
    }


def compute(payload):
    tests = payload.get("tests") or []
    baskets = payload.get("baskets") or []

    headroom_rows = [headroom(t) for t in tests]
    debt_rows = []
    for t in tests:
        result = max_additional_debt(t)
        if result is not None:
            debt_rows.append(dict(result, test=t.get("test") or "(unnamed test)"))

    basket_rows = [basket_capacity(b) for b in baskets]
    aggregate = aggregate_capacity(basket_rows, baskets) if basket_rows else None

    breached = [r["test"] for r in headroom_rows if r["status"] == "Breached"]
    at_threshold = [r["test"] for r in headroom_rows if r["status"] == "At threshold"]
    incomplete = [r["test"] for r in headroom_rows if r["status"] == INSUFFICIENT]

    return {
        "headroom": headroom_rows,
        "max_additional_debt": debt_rows,
        "basket_capacity": basket_rows,
        "aggregate": aggregate,
        "breached_tests": breached,
        "tests_at_threshold": at_threshold,
        "tests_with_missing_inputs": incomplete,
        "severity_note": (
            "Severity (Low/Moderate/High/Critical) is not assigned here: CP-4A "
            "defines it by creditor outcome, with no numeric thresholds. Assign it "
            "from the analysis."),
        "status": "complete" if not incomplete else "incomplete",
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
    # THE sign case: identical numbers, opposite test types, opposite verdicts.
    lev = headroom({"test": "Total Net Leverage", "test_type": "max-ratio",
                    "threshold": 5.0, "current_ratio": 4.0})
    cov = headroom({"test": "Interest Coverage", "test_type": "min-ratio",
                    "threshold": 5.0, "current_ratio": 4.0})
    assert lev["headroom"] == 1.0 and lev["status"] == "Compliant", lev
    assert cov["headroom"] == -1.0 and cov["status"] == "Breached", cov
    # and the mirror image, so neither direction is hard-coded to a verdict
    assert headroom({"test": "L", "test_type": "max-ratio",
                     "threshold": 4.0, "current_ratio": 5.0})["status"] == "Breached"
    assert headroom({"test": "C", "test_type": "min-ratio",
                     "threshold": 4.0, "current_ratio": 5.0})["status"] == "Compliant"

    # exactly at the threshold is not cushion
    at = headroom({"test": "L", "test_type": "max-ratio", "threshold": 5.0,
                   "current_ratio": 5.0})
    assert at["headroom"] == 0.0 and at["status"] == "At threshold", at

    # missing test_type must raise -- never assume a direction
    for bad in ({"test": "x", "threshold": 5.0, "current_ratio": 4.0},
                {"test": "x", "test_type": "sideways", "threshold": 5.0, "current_ratio": 4.0}):
        try:
            headroom(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"must raise on {bad}")

    # missing inputs are named, not silently zeroed
    miss = headroom({"test": "L", "test_type": "max-ratio", "threshold": None,
                     "current_ratio": 4.0})
    assert miss["headroom"] is None and miss["missing_inputs"] == ["threshold"]
    assert miss["status"] == INSUFFICIENT

    # incremental debt
    d = max_additional_debt({"test": "L", "test_type": "max-ratio", "threshold": 5.0,
                             "governing_ebitda": 100.0, "current_debt": 400.0})
    assert d["value"] == 100.0 and d["status"] == "capacity", d
    d = max_additional_debt({"test": "L", "test_type": "max-ratio", "threshold": 5.0,
                             "governing_ebitda": 100.0, "current_debt": 600.0})
    assert d["value"] == -100.0 and "already beyond" in d["status"]
    # negative EBITDA cannot be solved
    d = max_additional_debt({"test": "L", "test_type": "max-ratio", "threshold": 5.0,
                             "governing_ebitda": -10.0, "current_debt": 100.0})
    assert d["value"] is None and d["status"] == NOT_CALCULABLE
    # not defined for a coverage test
    assert max_additional_debt({"test": "C", "test_type": "min-ratio", "threshold": 2.0}) is None

    # baskets
    assert basket_capacity({"basket": "F", "type": "fixed", "fixed_amount": 100.0,
                            "usage": 30.0})["remaining_capacity"] == 70.0
    g = basket_capacity({"basket": "G", "type": "grower", "fixed_amount": 100.0,
                         "percentage": 0.25, "base_amount": 500.0, "usage": 25.0})
    assert g["gross_capacity"] == 125.0 and g["remaining_capacity"] == 100.0, g
    # grower takes the GREATER of the two, not the percentage
    g = basket_capacity({"basket": "G", "type": "grower", "fixed_amount": 200.0,
                         "percentage": 0.10, "base_amount": 500.0, "usage": 0.0})
    assert g["gross_capacity"] == 200.0, g
    b = basket_capacity({"basket": "B", "type": "builder", "build_up": 80.0,
                         "permitted_additions": 20.0, "usage": 60.0})
    assert b["remaining_capacity"] == 40.0, b
    # over-utilisation is reported, not floored at zero
    o = basket_capacity({"basket": "F", "type": "fixed", "fixed_amount": 50.0, "usage": 80.0})
    assert o["remaining_capacity"] == -30.0 and o["status"] == "over-utilised"

    # UNKNOWN usage is not zero usage. Reading it as zero reports the whole
    # basket as available -- the largest capacity figure from the least
    # information, in the direction that understates creditor risk.
    for absent in ({"basket": "RP", "type": "fixed", "fixed_amount": 100.0},
                   {"basket": "RP", "type": "fixed", "fixed_amount": 100.0, "usage": None},
                   {"basket": "RP", "type": "fixed", "fixed_amount": 100.0, "usage": "n/a"}):
        u = basket_capacity(absent)
        assert u["remaining_capacity"] is None, u
        assert u["status"] == NOT_CALCULABLE, u
        assert "usage" in " ".join(u["missing_inputs"]), u
    # explicit zero usage is a real figure and still computes
    z = basket_capacity({"basket": "RP", "type": "fixed", "fixed_amount": 100.0, "usage": 0.0})
    assert z["remaining_capacity"] == 100.0 and z["status"] == "available", z
    # a basket with no calculable remaining capacity blocks the total
    agg = compute({"tests": [], "baskets": [
        {"basket": "A", "type": "fixed", "fixed_amount": 100.0, "independently_usable": True},
        {"basket": "B", "type": "fixed", "fixed_amount": 50.0, "usage": 0.0,
         "independently_usable": True}]})["aggregate"]
    assert agg["total_capacity"] is None and agg["status"] == NOT_CALCULABLE, agg
    # percent-as-integer must raise
    try:
        basket_capacity({"basket": "G", "type": "grower", "fixed_amount": 1.0,
                         "percentage": 25, "base_amount": 100.0, "usage": 0.0})
    except ValueError:
        pass
    else:
        raise AssertionError("percentage must be a decimal")

    # grower: the drafted formulation governs; a non-standard clause must arrive
    # as an explicit amount rather than be approximated as a greater-of
    d = basket_capacity({"basket": "G", "type": "grower", "formulation": "as-drafted",
                         "drafted_amount": 175.0, "usage": 25.0})
    assert d["gross_capacity"] == 175.0 and d["remaining_capacity"] == 150.0, d
    try:
        basket_capacity({"basket": "G", "type": "grower", "formulation": "as-drafted",
                         "fixed_amount": 100.0, "percentage": 0.25,
                         "base_amount": 500.0, "usage": 0.0})
    except ValueError:
        pass
    else:
        raise AssertionError("as-drafted without drafted_amount must raise")

    # CP-2H trigger headroom: same sign rule, so the same code
    lev = trigger_headroom({"trigger": "Max leverage", "trigger_direction": "max-ratio",
                            "threshold": 5.0,
                            "cases": [{"period": "FY24", "value": 4.0},
                                      {"period": "FY25", "value": 5.5}]})
    assert lev["periods"][0]["status"] == "Compliant", lev
    assert lev["periods"][1]["status"] == "Breached", lev
    assert lev["breach_periods"] == ["FY25"] and lev["sustained"] is False
    assert "point-in-time" in lev["classification"]

    cov = trigger_headroom({"trigger": "Min coverage", "trigger_direction": "min-ratio",
                            "threshold": 5.0,
                            "cases": [{"period": "FY24", "value": 4.0},
                                      {"period": "FY25", "value": 5.5}]})
    # identical numbers, opposite direction -> opposite verdicts
    assert cov["periods"][0]["status"] == "Breached" and cov["periods"][1]["status"] == "Compliant"

    sust = trigger_headroom({"trigger": "L", "trigger_direction": "max-ratio", "threshold": 5.0,
                             "sustained_periods": ["FY24", "FY25"],
                             "cases": [{"period": "FY24", "value": 5.5},
                                       {"period": "FY25", "value": 6.0}]})
    assert sust["sustained"] is True and sust["classification"] == "sustained breach"

    rng = trigger_headroom({"trigger": "L", "trigger_direction": "max-ratio",
                            "threshold_lower": 4.5, "threshold_upper": 5.5,
                            "cases": [{"period": "FY24", "value": 5.0}]})
    assert rng["is_range"] and set(rng["periods"][0]["headroom"]) == {"lower", "upper"}
    assert rng["periods"][0]["binding_threshold"] == 4.5, rng
    assert rng["periods"][0]["status"] == "Breached", rng   # inside the range, past the tight bound

    for bad, why in (
        ({"trigger": "x", "threshold": 5.0, "cases": []}, "missing direction must raise"),
        ({"trigger": "x", "trigger_direction": "max-ratio", "cases": []}, "no threshold must raise"),
        ({"trigger": "x", "trigger_direction": "max-ratio", "threshold": 5.0,
          "threshold_lower": 4.0, "cases": []}, "point+range must raise"),
    ):
        try:
            trigger_headroom(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(why)

    # basket type must be explicit
    try:
        basket_capacity({"basket": "G", "fixed_amount": 100.0, "percentage": 0.25,
                         "base_amount": 500.0, "usage": 0.0})
    except ValueError:
        pass
    else:
        raise AssertionError("missing basket type must raise, not default to fixed")

    # never total across currencies
    mixed = compute({"tests": [], "baskets": [
        {"basket": "A", "type": "fixed", "fixed_amount": 100.0, "usage": 0.0,
         "currency": "EUR", "independently_usable": True},
        {"basket": "B", "type": "fixed", "fixed_amount": 50.0, "usage": 0.0,
         "currency": "USD", "independently_usable": True}]})["aggregate"]
    assert mixed["total_capacity"] is None and "currencies" in mixed, mixed

    # double-counting discipline: no total unless every basket is asserted independent
    baskets = [{"basket": "A", "type": "fixed", "fixed_amount": 100.0, "usage": 0.0},
               {"basket": "B", "type": "fixed", "fixed_amount": 50.0, "usage": 0.0}]
    agg = compute({"tests": [], "baskets": baskets})["aggregate"]
    assert agg["total_capacity"] is None and agg["status"] == NOT_CALCULABLE, agg
    assert "independent" in agg["reason"]
    # one asserted, one not -> still no total (a partial sum labelled total is the bug)
    agg = compute({"tests": [], "baskets": [dict(baskets[0], independently_usable=True),
                                            baskets[1]]})["aggregate"]
    assert agg["total_capacity"] is None
    # all asserted -> summed
    agg = compute({"tests": [], "baskets": [dict(b, independently_usable=True)
                                            for b in baskets]})["aggregate"]
    assert agg["total_capacity"] == 150.0 and agg["status"] == "summed"

    # severity is never assigned by the script
    full = compute({"tests": [{"test": "L", "test_type": "max-ratio", "threshold": 5.0,
                               "current_ratio": 4.0}], "baskets": []})
    assert "Severity" in full["severity_note"] and full["status"] == "complete"
    assert full["breached_tests"] == []
    print("covenant_headroom self-check: OK")


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        _self_check()
    else:
        raise SystemExit(main())
