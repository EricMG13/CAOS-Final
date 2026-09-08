#!/usr/bin/env python3
"""Compute the CP Confidence Score exactly as CANON_SHARED.md defines it.

Canon calls the score "deterministic", requires it in every handoff's YAML
envelope, and requires CP-5A to recompute and audit it. So the same arithmetic
is performed at least twice per artifact by a language model, and the two
results must agree -- along with the band and the qa_status derived from them.
Three coupled values, each cheap to get subtly wrong, checked against each other
by hand.

    score = clamp( (0.6 * E + 0.4 * C) * S - P , 0 , 100 )

    E  mean strongest lineage weight over material claims, x100
    C  required_fields_present / required_fields_total x100
    S  source gate: pass 1.0 | partial 0.7 | fail 0.0
    P  QA findings: CRITICAL -40 | MATERIAL -15 | MINOR -3

The judgment stays with the analyst: classifying a claim's lineage, deciding
which claims are material, deciding a finding's severity. Only the arithmetic,
the caps and the band lookup move here -- the parts with a single right answer.

The hard caps are the reason this matters most. An unresolved CRITICAL forces
score <= 39 AND qa_status Blocked; a MATERIAL forces <= 59 AND Restricted. A
score computed correctly but capped inconsistently produces an artifact whose
envelope says Passed while its findings say otherwise.

Usage:
    python3 confidence_score.py --lineage "Directly Sourced:8,Calculated:2,Assumption-Based:2" \\
                                --fields-present 19 --fields-total 20 \\
                                --source-gate pass --findings MINOR:1
    python3 confidence_score.py --json '{"lineage": {...}, ...}'      # or on stdin
"""
import argparse
import json
import sys

# CANON_SHARED.md § CP_CONFIDENCE_SCORE.md -- lineage_class -> weight
LINEAGE_WEIGHTS = {
    "directly sourced": 1.0,
    "calculated": 0.9,
    "assumption-based": 0.5,
    "analyst inference": 0.4,
    "weak lineage": 0.3,
    "untraced": 0.0,
    "conflicting": 0.0,
    "insufficient information": 0.0,
}
SOURCE_GATE = {"pass": 1.0, "partial": 0.7, "fail": 0.0}
PENALTIES = {"critical": 40, "material": 15, "minor": 3}

BANDS = [(80, "High"), (60, "Medium"), (40, "Low"), (0, "Insufficient Information")]


def band_for(score):
    for threshold, name in BANDS:
        if score >= threshold:
            return name
    return BANDS[-1][1]


def evidence_quality(lineage_counts):
    """E: mean strongest weight over material claims, x100.

    lineage_counts maps lineage_class -> number of material claims whose
    STRONGEST evidence is of that class.
    """
    total = 0
    weighted = 0.0
    for cls, count in lineage_counts.items():
        key = str(cls).strip().casefold()
        if key not in LINEAGE_WEIGHTS:
            raise ValueError(
                f"unknown lineage_class {cls!r}; canon defines: "
                + ", ".join(sorted(LINEAGE_WEIGHTS))
            )
        if count < 0:
            raise ValueError(f"negative claim count for {cls!r}")
        weighted += LINEAGE_WEIGHTS[key] * count
        total += count
    if total == 0:
        # No material claims is not "perfect evidence". Canon's Insufficient
        # Information band is the honest answer, and returning 100 here would
        # let an empty analysis score High.
        return 0.0, 0
    return (weighted / total) * 100.0, total


def compute(lineage_counts, fields_present, fields_total, source_gate, findings):
    gate = str(source_gate).strip().casefold()
    if gate not in SOURCE_GATE:
        raise ValueError(f"source_gate must be one of {sorted(SOURCE_GATE)}, got {source_gate!r}")
    if fields_total <= 0:
        raise ValueError("fields_total must be positive")
    if not 0 <= fields_present <= fields_total:
        raise ValueError(f"fields_present {fields_present} outside 0..{fields_total}")

    e, claims = evidence_quality(lineage_counts)
    c = (fields_present / fields_total) * 100.0
    s = SOURCE_GATE[gate]

    penalty = 0
    counts = {}
    for severity, count in (findings or {}).items():
        key = str(severity).strip().casefold()
        if key not in PENALTIES:
            raise ValueError(f"unknown finding severity {severity!r}; expected {sorted(PENALTIES)}")
        if count < 0:
            raise ValueError(f"negative finding count for {severity!r}")
        penalty += PENALTIES[key] * count
        counts[key] = count

    raw = (0.6 * e + 0.4 * c) * s - penalty
    score = max(0, min(100, raw))

    # Hard caps. Applied after clamping, and they lower the score -- they never
    # raise it, so a Blocked artifact cannot be promoted by a generous cap.
    if counts.get("critical"):
        score = min(score, 39)
        qa_status = "Blocked"
    elif counts.get("material"):
        score = min(score, 59)
        qa_status = "Restricted"
    else:
        qa_status = "Passed"

    score = int(round(score))
    return {
        "E": round(e, 4),
        "C": round(c, 4),
        "S": s,
        "P": penalty,
        "material_claims": claims,
        "raw_score": round(raw, 4),
        "confidence_score": score,
        "confidence_band": band_for(score),
        "qa_status": qa_status,
        "working": (
            f"score = clamp((0.6*{e:.4g} + 0.4*{c:.4g}) * {s} - {penalty}, 0, 100) "
            f"= {raw:.4g} -> {score}"
        ),
    }


def _parse_counts(text, what):
    out = {}
    if not text:
        return out
    for part in text.split(","):
        if not part.strip():
            continue
        if ":" not in part:
            raise ValueError(f"{what} entry {part!r} must be NAME:COUNT")
        name, _, count = part.rpartition(":")
        out[name.strip()] = int(count)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lineage", help='e.g. "Directly Sourced:8,Calculated:2"')
    ap.add_argument("--fields-present", type=int)
    ap.add_argument("--fields-total", type=int)
    ap.add_argument("--source-gate", choices=sorted(SOURCE_GATE))
    ap.add_argument("--findings", default="", help='e.g. "MATERIAL:1,MINOR:2"')
    ap.add_argument("--json", dest="json_input", nargs="?", const="-",
                    help="read all inputs as one JSON object ('-' or omitted value = stdin)")
    args = ap.parse_args(argv)

    try:
        if args.json_input:
            raw = sys.stdin.read() if args.json_input == "-" else args.json_input
            payload = json.loads(raw)
            result = compute(
                payload["lineage"], payload["fields_present"], payload["fields_total"],
                payload["source_gate"], payload.get("findings", {}),
            )
        else:
            missing = [n for n in ("lineage", "fields_present", "fields_total", "source_gate")
                       if getattr(args, n.replace("-", "_")) in (None, "")]
            if missing:
                ap.error(f"missing required argument(s): {', '.join('--' + m for m in missing)}")
            result = compute(
                _parse_counts(args.lineage, "lineage"),
                args.fields_present, args.fields_total, args.source_gate,
                _parse_counts(args.findings, "findings"),
            )
    except (ValueError, KeyError) as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}), file=sys.stderr)
        return 2

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def _self_check():
    """Canon's own worked example, plus the cap and boundary behaviour."""
    got = compute({"Directly Sourced": 8, "Calculated": 2, "Assumption-Based": 2},
                  95, 100, "pass", {"MINOR": 1})
    assert got["E"] == 90.0, got
    assert got["C"] == 95.0, got
    assert got["confidence_score"] == 89, got
    assert got["confidence_band"] == "High", got
    assert got["qa_status"] == "Passed", got

    capped = compute({"Directly Sourced": 10}, 100, 100, "pass", {"CRITICAL": 1})
    assert capped["confidence_score"] <= 39 and capped["qa_status"] == "Blocked", capped
    restricted = compute({"Directly Sourced": 10}, 100, 100, "pass", {"MATERIAL": 1})
    assert restricted["confidence_score"] <= 59 and restricted["qa_status"] == "Restricted", restricted

    assert compute({"Directly Sourced": 1}, 1, 1, "fail", {})["confidence_score"] == 0
    assert compute({}, 1, 1, "pass", {})["confidence_score"] == 40  # no claims -> E=0
    assert band_for(80) == "High" and band_for(79) == "Medium"
    assert band_for(60) == "Medium" and band_for(59) == "Low"
    assert band_for(40) == "Low" and band_for(39) == "Insufficient Information"
    print("confidence_score self-check: OK")


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        _self_check()
    else:
        raise SystemExit(main())
