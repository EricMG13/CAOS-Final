#!/usr/bin/env python3
"""CP-1C peer statistics, outlier recomputation and implied enterprise value.

Why this is script work: CP-1C gates every summary statistic behind a minimum
peer count, and the counts differ per statistic --

    REF_CP-1C_STEPS.md "Peer Statistic Rules -- ACTIVE_PROMPT Thresholds":
      "Min 3 for median, 4 for quartile, 5 for average. <2 -> no statistics.
       Exclude non-comparable. State N. Outlier distorts average -> median
       alongside + flag."
    REF_CP-1C_STEPS.md "Peer Statistic Rules":
      "Do not calculate average, median, quartile, range, standard deviation,
       or percentile unless sufficient comparable datapoints exist (minimum 2
       for any 'range'/'average' label; minimum 3 for a meaningful sector
       multiple)."

The package states two threshold sets and marks neither superseded, so which
one governs is settled by the entry itself: SKILL.md's "#### Peer Statistic
Rules" points by NAME at the second one --

    "Per `REF_CP-1C_ValuationAndOutlierRules.md` §Peer Statistic Rules —
     ACTIVE_PROMPT Thresholds."   (cp-1c SKILL.md:196-197)

-- so 3/4/5 with an absolute floor of 2 is the named authority, not merely the
stricter reading. It also happens to be the stricter one everywhere the two
differ. Because the ambiguity is real and documented, the governing set is
named in the output under `threshold_set`, rather than left implicit.

Then:

    "if an outlier distorts peer statistics, recalculate the statistic
     excluding it and show both versions"

-- which doubles the arithmetic and, with it, the chance of a transcription
slip, on a peer set small enough that one datapoint moves the median.

What stays with the analyst, because CP-1C reserves it:
  - which entities are comparable at all ("Exclude non-comparable datapoints
    from summary statistics and state why"; "Comparability-Before-Statistics:
    Assign status before any aggregate"). The caller passes an already-classified
    peer set; this module never decides comparability.
  - which datapoints are outliers, and why ("Assess whether the outlier reflects
    (a) genuine operational difference, (b) data-quality issue, (c) comparability
    misalignment, or (d) one-off event"). The caller flags them; this module only
    recomputes without them.
  - whether trading and transaction multiples may be blended ("Do not blend
    trading multiples and transaction multiples in the same average or median
    without flagging").

Quantile convention: CP-1C does NOT specify one, and the common choices
disagree materially on small N -- exactly the N this module operates at. Rather
than pick silently, the convention is named in the output under
`convention`, so a reader can see which one produced the number.
Median of an even count is the mean of the two central values; quartiles use
the inclusive (Excel PERCENTILE.INC / R type 7) linear interpolation that
stdlib `statistics.quantiles(method="inclusive")` implements.

    python3 peer_statistics.py --json '{"metric": "EV/EBITDA", "peers": [...]}'
"""
import argparse
import json
import statistics
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

# Stricter of the two stated rule sets, per statistic.
MIN_N = {
    "range": 2,
    "minimum": 2,
    "maximum": 2,
    "median": 3,
    "quartiles": 4,
    "average": 5,
    "stdev": 5,
}
# Below this, CP-1C permits no statistics of any kind.
ABSOLUTE_MIN_N = 2
# "Sector multiples require a minimum of 3 comparable datapoints to be meaningful."
MIN_N_MEANINGFUL_MULTIPLE = 3

NOT_CALCULABLE = "Not Calculable"

# REF_CP-1C_STEPS.md "Label Taxonomies (closed sets -- use only these values)":
#   Comparability Status: `Comparable` | `Comparable with Limitations` |
#   `Not Comparable` | `Insufficient Information`.
# Validated rather than pattern-matched: silently treating an unrecognised
# status as non-comparable would drop a peer out of the statistics on a typo,
# and the only visible effect would be a smaller N.
COMPARABILITY_INCLUDED = {"comparable", "comparable with limitations"}
COMPARABILITY_EXCLUDED = {"not comparable", "insufficient information"}

# REF_CP-1C_STEPS.md:275 -- Calculation Status closed set.
CALCULATION_STATUSES = {
    "reported", "calculated", "derived", "provisional",
    "not comparable", "insufficient information",
}
# CANON_SHARED.md, "Controlled Public-Web Exception — CP-1C": "A material
# secondary-source figure requires primary-source confirmation or independent
# reputable corroboration; otherwise it remains `Provisional` and is excluded
# from aggregate statistics."
#
# This is a SECOND exclusion filter on N, independent of comparability, and it
# lives in canon rather than in CP-1C's own references -- which is why it is
# easy to miss when reading only the skill folder.
STATUS_EXCLUDED_FROM_AGGREGATES = {"provisional", "not comparable", "insufficient information"}

# "Stale multiples (more than 12 months old) must be labelled as such."
STALE_AFTER_MONTHS = 12
THRESHOLD_SET = (
    "ACTIVE_PROMPT Thresholds (median 3, quartile 4, average 5, none below 2), "
    "named by cp-1c SKILL.md #### Peer Statistic Rules. The base 'Peer Statistic "
    "Rules' passage states minimum 2 for an average; it is not marked superseded, "
    "so the governing set is stated here."
)
CONVENTION = (
    "median: mean of the two central values when N is even; "
    "quartiles: inclusive linear interpolation (Excel PERCENTILE.INC / R type 7); "
    "stdev: sample standard deviation (n-1). CP-1C does not specify a quantile "
    "convention, so it is stated here rather than chosen silently."
)


_NULL_WORDS = {"null", "n/a", "na", "none", "not disclosed", "not available",
              "not calculable", "unknown", "tbd", "insufficient information"}


def _num(value, where):
    """Delegates to cp_tables.parse_figure so every module shares one notation
    policy -- in particular the refusal to guess whether `5,2` means 5.2 or 52."""
    if value is None:
        return None
    text = str(value).strip()
    if text == "" or text.casefold() in _NULL_WORDS:
        return None
    return parse_figure(value, where)


def _describe(values):
    """Summary statistics, each gated on its own minimum N.

    A statistic below its threshold is Not Calculable -- not omitted silently
    and not computed anyway with a caveat. `statistics` module functions would
    happily return a median of two points or a stdev of one; the gate is the
    whole point of doing this in code.
    """
    n = len(values)
    out = {"n": n}
    if n < ABSOLUTE_MIN_N:
        out["status"] = f"no statistics: N={n} is below the absolute minimum of {ABSOLUTE_MIN_N}"
        for key in ("minimum", "maximum", "range", "median", "average", "stdev", "q1", "q3"):
            out[key] = None
        return out

    ordered = sorted(values)
    out["status"] = "calculated"
    out["minimum"] = ordered[0] if n >= MIN_N["minimum"] else None
    out["maximum"] = ordered[-1] if n >= MIN_N["maximum"] else None
    out["range"] = (ordered[-1] - ordered[0]) if n >= MIN_N["range"] else None
    out["median"] = statistics.median(ordered) if n >= MIN_N["median"] else None
    out["average"] = statistics.fmean(ordered) if n >= MIN_N["average"] else None
    out["stdev"] = statistics.stdev(ordered) if n >= MIN_N["stdev"] else None
    if n >= MIN_N["quartiles"]:
        q1, _, q3 = statistics.quantiles(ordered, n=4, method="inclusive")
        out["q1"], out["q3"] = q1, q3
    else:
        out["q1"] = out["q3"] = None

    out["suppressed"] = sorted(
        name for name, floor in MIN_N.items()
        if n < floor and name not in ("minimum", "maximum")
    )
    return out


def analyse(payload):
    """Peer statistics for one metric, with and without flagged outliers."""
    metric = payload.get("metric") or "(unnamed metric)"
    peers = payload.get("peers") or []
    if not isinstance(peers, list):
        raise ValueError("peers must be a list")

    included, excluded_non_comparable, null_valued, outliers = [], [], [], []
    limited, stale = [], []
    currencies, multiple_types = set(), set()
    excluded_by_status = []
    for i, peer in enumerate(peers):
        name = peer.get("name") or f"peer[{i}]"
        value = _num(peer.get("value"), f"peers[{i}].value")
        # Comparability is the analyst's call; this only honours it -- but the
        # value must be one the taxonomy defines, or a typo would quietly drop
        # the peer and show up only as a smaller N.
        if "comparability" not in peer:
            raise ValueError(
                f"peers[{i}] ({name}): comparability is required. CP-1C's execution rule 3 is "
                "\"Comparability-Before-Statistics: Assign status before any aggregate\" -- "
                "defaulting to Comparable would put an unassessed peer into the statistics")
        comparability = str(peer.get("comparability")).strip()
        key = comparability.casefold()
        if key not in COMPARABILITY_INCLUDED | COMPARABILITY_EXCLUDED:
            raise ValueError(
                f"peers[{i}] ({name}): comparability {comparability!r} is outside CP-1C's "
                f"closed set {sorted(COMPARABILITY_INCLUDED | COMPARABILITY_EXCLUDED)}"
            )
        if key in COMPARABILITY_EXCLUDED:
            excluded_non_comparable.append({"name": name, "comparability": comparability})
            continue

        status = peer.get("calculation_status")
        if status is not None:
            skey = str(status).strip().casefold()
            if skey not in CALCULATION_STATUSES:
                raise ValueError(
                    f"peers[{i}] ({name}): calculation_status {status!r} is outside CP-1C's "
                    f"closed set {sorted(CALCULATION_STATUSES)}")
            if skey in STATUS_EXCLUDED_FROM_AGGREGATES:
                excluded_by_status.append({"name": name, "calculation_status": status})
                continue
        if key == "comparable with limitations":
            limited.append(name)

        if peer.get("currency"):
            currencies.add(str(peer["currency"]).strip().upper())
        if peer.get("multiple_type"):
            multiple_types.add(str(peer["multiple_type"]).strip().casefold())

        months = _num(peer.get("age_months"), f"peers[{i}].age_months")
        if months is not None and months > STALE_AFTER_MONTHS:
            stale.append({"name": name, "age_months": months})
        if value is None:
            null_valued.append(name)
            continue
        entry = {"name": name, "value": value, "outlier": bool(peer.get("outlier", False))}
        included.append(entry)
        if entry["outlier"]:
            outliers.append(name)

    values = [e["value"] for e in included]
    with_outliers = _describe(values)

    # "if an outlier distorts peer statistics, recalculate the statistic
    # excluding it and show both versions" -- both are always reported when any
    # outlier is flagged, so the reader sees the sensitivity rather than being
    # handed whichever version the author preferred.
    if outliers:
        kept = [e["value"] for e in included if not e["outlier"]]
        ex_outliers = _describe(kept)
        # Excluding outliers can drop N below a threshold that the full set
        # cleared. That is a real finding about the peer set, not an error --
        # but it must be visible, or the ex-outlier column silently loses rows.
        lost = sorted(set(ex_outliers.get("suppressed") or [])
                      - set(with_outliers.get("suppressed") or []))
        ex_outliers["newly_suppressed_by_exclusion"] = lost
        # "Outlier distorts average -> median alongside + flag." The median is
        # always emitted above (subject to its own N gate); this is the flag.
        if with_outliers.get("average") is not None:
            with_outliers["outlier_distortion_flag"] = (
                "an outlier is present in this average; the median is shown alongside "
                "and the excluding-outlier version is reported")
    else:
        ex_outliers = None

    return {
        "metric": metric,
        "convention": CONVENTION,
        "threshold_set": THRESHOLD_SET,
        "n_supplied": len(peers),
        "n_included": len(included),
        "excluded_non_comparable": excluded_non_comparable,
        "excluded_null_value": null_valued,
        # Uncorroborated secondary-source figures stay Provisional and are kept
        # out of aggregates (CANON_SHARED, public-web exception).
        "excluded_by_calculation_status": excluded_by_status,
        # AP11 admits "Comparable with Limitations" as well as "Comparable".
        # Both enter the statistics, but a set carrying limited comparables is
        # a weaker basis than one that does not, and the reader cannot see that
        # from N alone -- so name them rather than silently blending them in.
        "included_comparable_with_limitations": limited,
        # "Stale multiples (more than 12 months old) must be labelled as such."
        # Comparing an as-of date against the analysis date for every peer is a
        # mechanical check that degrades badly when done by eye across a long
        # peer table -- and an unlabelled stale multiple reads as current.
        "stale_over_12_months": stale,
        # "Currency must be consistent across all valuation calculations, or
        # exchange rates disclosed." Unitless multiples are unaffected; absolute
        # metrics silently become a number in no currency at all.
        "currencies": sorted(currencies),
        "mixed_currency_warning": (
            f"peer values span {sorted(currencies)}; for an absolute metric these are "
            "not additive or comparable without a disclosed exchange rate"
            if len(currencies) > 1 else None),
        # "Do not blend trading multiples and transaction multiples in the same
        # average or median without flagging." This is the flag.
        "multiple_types": sorted(multiple_types),
        "blended_multiple_warning": (
            f"the set blends {sorted(multiple_types)} multiples; CP-1C requires this to be "
            "flagged wherever they share an average or median"
            if len(multiple_types) > 1 else None),
        "outliers_flagged": outliers,
        "statistics_including_outliers": with_outliers,
        "statistics_excluding_outliers": ex_outliers,
        "meaningful_as_sector_multiple": len(included) >= MIN_N_MEANINGFUL_MULTIPLE,
    }


def implied_ev(payload, stats=None, use_ex_outliers=False):
    """Implied EV Low / Median / High from the peer multiple distribution.

    CP-1C: "Low = minimum peer multiple x borrower metric; Median = median peer
    multiple x borrower metric; High = maximum peer multiple x borrower metric."

    Low and High are the extremes of the multiple distribution, so a flagged
    outlier sets one of them outright -- which is exactly the case the
    "recalculate excluding it and show both versions" rule is about. When
    outliers are flagged, compute() reports both this and the ex-outlier range.
    """
    borrower_metric = _num(payload.get("borrower_metric"), "borrower_metric")
    if borrower_metric is None:
        return None
    stats = stats or analyse(payload)
    base = (stats["statistics_excluding_outliers"] if use_ex_outliers
            else stats["statistics_including_outliers"])
    if base is None:
        return None

    def scale(multiple):
        return round(multiple * borrower_metric, 6) if multiple is not None else None

    warnings = []
    if borrower_metric <= 0:
        # An EV/EBITDA multiple applied to negative or zero EBITDA is
        # arithmetically fine and analytically meaningless: it yields a negative
        # "value" that reads like a valuation. Compute nothing rather than
        # publish a number whose sign is an artefact.
        warnings.append(
            f"borrower metric is {borrower_metric}; a multiple-based implied EV is "
            "not meaningful on a non-positive denominator basis -- no implied EV computed"
        )
        return {
            "borrower_metric": borrower_metric,
            "low": None, "median": None, "high": None,
            "status": NOT_CALCULABLE, "warnings": warnings,
        }
    if use_ex_outliers:
        warnings.append("computed excluding the flagged outlier(s)")
    if not stats["meaningful_as_sector_multiple"]:
        warnings.append(
            f"N={stats['n_included']} comparable datapoints; CP-1C requires a minimum of "
            f"{MIN_N_MEANINGFUL_MULTIPLE} for a sector multiple to be meaningful"
        )
    if base["median"] is None:
        warnings.append(
            f"median suppressed at N={base['n']} (minimum {MIN_N['median']}), so the "
            "central implied EV is Not Calculable"
        )

    return {
        "borrower_metric": borrower_metric,
        "low": scale(base["minimum"]),
        "median": scale(base["median"]),
        "high": scale(base["maximum"]),
        "multiple_low": base["minimum"],
        "multiple_median": base["median"],
        "multiple_high": base["maximum"],
        "status": "indicative context only, not a valuation or recovery estimate",
        "warnings": warnings,
    }


def compute(payload):
    stats = analyse(payload)
    result = dict(stats)
    if payload.get("borrower_metric") is not None:
        result["implied_ev"] = implied_ev(payload, stats)
        # Low/High ARE the extremes of the multiple distribution, so a flagged
        # outlier defines one of them. Both versions, per CP-1C.
        if stats["statistics_excluding_outliers"] is not None:
            result["implied_ev_excluding_outliers"] = implied_ev(
                payload, stats, use_ex_outliers=True)
    borrower_value = _num(payload.get("borrower_value"), "borrower_value")
    if borrower_value is not None:
        base = stats["statistics_including_outliers"]
        result["borrower_positioning"] = {
            "borrower_value": borrower_value,
            "vs_median": (round(borrower_value - base["median"], 6)
                          if base["median"] is not None else None),
            "vs_average": (round(borrower_value - base["average"], 6)
                           if base["average"] is not None else None),
            "inside_peer_range": (
                None if base["minimum"] is None
                else base["minimum"] <= borrower_value <= base["maximum"]
            ),
        }
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", dest="json_input", nargs="?", const="-",
                    help="peer payload as JSON ('-' or omitted = stdin)")
    args = ap.parse_args(argv)
    raw = sys.stdin.read() if (args.json_input in (None, "-")) else args.json_input
    try:
        result = compute(json.loads(raw))
        output = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    except (ValueError, OverflowError) as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}), file=sys.stderr)
        return 2
    print(output)
    return 0 if result["statistics_including_outliers"]["status"] == "calculated" else 1


def _self_check():
    five = {"metric": "EV/EBITDA", "peers": [
        {"name": "A", "value": 5.0, "comparability": "Comparable"}, {"name": "B", "value": 6.0, "comparability": "Comparable"},
        {"name": "C", "value": 7.0, "comparability": "Comparable"}, {"name": "D", "value": 8.0, "comparability": "Comparable"},
        {"name": "E", "value": 9.0, "comparability": "Comparable"},
    ]}
    r = analyse(five)
    s = r["statistics_including_outliers"]
    assert s["n"] == 5 and s["median"] == 7.0 and s["average"] == 7.0
    assert s["minimum"] == 5.0 and s["maximum"] == 9.0 and s["range"] == 4.0
    assert s["q1"] == 6.0 and s["q3"] == 8.0, s
    assert s["suppressed"] == [], s

    # N=4: average and stdev suppressed (need 5), median and quartiles allowed
    four = {"metric": "m", "peers": [{"name": c, "value": v, "comparability": "Comparable"}
            for c, v in zip("ABCD", (4.0, 6.0, 8.0, 10.0))]}
    s = analyse(four)["statistics_including_outliers"]
    assert s["median"] == 7.0 and s["q1"] is not None
    assert s["average"] is None and s["stdev"] is None
    assert set(s["suppressed"]) == {"average", "stdev"}, s

    # N=3: quartiles also suppressed
    s = analyse({"metric": "m", "peers": [{"name": c, "value": v, "comparability": "Comparable"}
                for c, v in zip("ABC", (4.0, 6.0, 8.0))]})["statistics_including_outliers"]
    assert s["median"] == 6.0 and s["q1"] is None and s["average"] is None

    # N=2: range only, no median
    s = analyse({"metric": "m", "peers": [{"name": "A", "value": 4.0, "comparability": "Comparable"},
                {"name": "B", "value": 8.0, "comparability": "Comparable"}]})["statistics_including_outliers"]
    assert s["range"] == 4.0 and s["median"] is None and s["status"] == "calculated"

    # N=1: nothing at all
    s = analyse({"metric": "m", "peers": [{"name": "A", "value": 4.0, "comparability": "Comparable"}]})["statistics_including_outliers"]
    assert s["range"] is None and s["minimum"] is None and "below the absolute minimum" in s["status"]

    # non-comparable peers are excluded from the aggregate and named
    r = analyse({"metric": "m", "peers": [
        {"name": "A", "value": 5.0, "comparability": "Comparable"}, {"name": "B", "value": 6.0, "comparability": "Comparable"},
        {"name": "C", "value": 7.0, "comparability": "Comparable"}, {"name": "D", "value": 8.0, "comparability": "Comparable"},
        {"name": "Z", "value": 99.0, "comparability": "Not Comparable"},
    ]})
    assert r["n_included"] == 4 and r["excluded_non_comparable"][0]["name"] == "Z"
    assert r["statistics_including_outliers"]["maximum"] == 8.0

    # both versions reported when an outlier is flagged, and the exclusion
    # dropping N below a threshold is surfaced rather than hidden
    r = analyse({"metric": "m", "peers": [
        {"name": "A", "value": 5.0, "comparability": "Comparable"}, {"name": "B", "value": 6.0, "comparability": "Comparable"},
        {"name": "C", "value": 7.0, "comparability": "Comparable"}, {"name": "D", "value": 8.0, "comparability": "Comparable"},
        {"name": "E", "value": 50.0, "outlier": True, "comparability": "Comparable"},
    ]})
    inc, exc = r["statistics_including_outliers"], r["statistics_excluding_outliers"]
    assert inc["average"] == 15.2 and inc["n"] == 5
    assert exc is not None and exc["n"] == 4 and exc["average"] is None
    assert exc["newly_suppressed_by_exclusion"] == ["average", "stdev"], exc

    # null values drop out, are named, and do NOT count toward N
    r = analyse({"metric": "m", "peers": [
        {"name": "A", "value": 5.0, "comparability": "Comparable"}, {"name": "B", "value": None, "comparability": "Comparable"},
        {"name": "C", "value": "n/a", "comparability": "Comparable"}, {"name": "D", "value": 7.0, "comparability": "Comparable"},
    ]})
    assert r["n_included"] == 2 and sorted(r["excluded_null_value"]) == ["B", "C"]

    # implied EV
    ev = compute(dict(five, borrower_metric=100.0))["implied_ev"]
    assert ev["low"] == 500.0 and ev["median"] == 700.0 and ev["high"] == 900.0
    assert ev["warnings"] == [], ev

    # negative EBITDA: a multiple times a negative base is not a valuation
    ev = compute(dict(five, borrower_metric=-50.0))["implied_ev"]
    assert ev["low"] is None and ev["status"] == NOT_CALCULABLE
    assert "not meaningful" in ev["warnings"][0]

    # too few peers for a meaningful sector multiple -> warned, not silent
    ev = compute({"metric": "m", "borrower_metric": 100.0, "peers": [
        {"name": "A", "value": 5.0, "comparability": "Comparable"}, {"name": "B", "value": 7.0, "comparability": "Comparable"}]})["implied_ev"]
    assert any("minimum of 3" in w for w in ev["warnings"]), ev
    assert ev["median"] is None and any("median suppressed" in w for w in ev["warnings"])

    # a Provisional figure is kept out of the aggregate, and named
    r = analyse({"metric": "m", "peers": [
        {"name": "A", "value": 5.0, "comparability": "Comparable"},
        {"name": "B", "value": 6.0, "comparability": "Comparable"},
        {"name": "P", "value": 99.0, "comparability": "Comparable",
         "calculation_status": "Provisional"}]})
    assert r["n_included"] == 2, r
    assert r["excluded_by_calculation_status"][0]["name"] == "P", r
    assert r["statistics_including_outliers"]["maximum"] == 6.0, r
    # a corroborated one is included
    r = analyse({"metric": "m", "peers": [
        {"name": "A", "value": 5.0, "comparability": "Comparable"},
        {"name": "B", "value": 6.0, "comparability": "Comparable",
         "calculation_status": "Reported"}]})
    assert r["n_included"] == 2, r
    try:
        analyse({"metric": "m", "peers": [{"name": "A", "value": 5.0,
                 "comparability": "Comparable", "calculation_status": "maybe"}]})
    except ValueError:
        pass
    else:
        raise AssertionError("calculation_status outside the closed set must raise")

    # implied EV is reported both ways when an outlier is flagged, because the
    # outlier sets Low or High outright
    both = compute({"metric": "m", "borrower_metric": 100.0, "peers": [
        {"name": "A", "value": 5.0, "comparability": "Comparable"}, {"name": "B", "value": 6.0, "comparability": "Comparable"},
        {"name": "C", "value": 7.0, "comparability": "Comparable"}, {"name": "D", "value": 8.0, "comparability": "Comparable"},
        {"name": "E", "value": 50.0, "outlier": True, "comparability": "Comparable"}]})
    assert both["implied_ev"]["high"] == 5000.0, both["implied_ev"]
    assert both["implied_ev_excluding_outliers"]["high"] == 800.0, both["implied_ev_excluding_outliers"]
    assert any("excluding the flagged outlier" in w
               for w in both["implied_ev_excluding_outliers"]["warnings"])

    # borrower positioning
    pos = compute(dict(five, borrower_value=10.0))["borrower_positioning"]
    assert pos["vs_median"] == 3.0 and pos["inside_peer_range"] is False

    # a peer value that is not a figure must raise, not be silently dropped
    try:
        analyse({"metric": "m", "peers": [{"name": "A", "value": "roughly 5", "comparability": "Comparable"}]})
    except ValueError:
        pass
    else:
        raise AssertionError("unparseable peer value must raise")

    print("peer_statistics self-check: OK")


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        _self_check()
    else:
        raise SystemExit(main())
