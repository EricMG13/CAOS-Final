"""Shared canonical completeness and current-lineage acceptance for navigation/publication."""
from pathlib import Path

from validate_handoff import validate_text
from completeness_check import check
from . import envelope
from .routing import expected_upstream_digests
from .research import validate_dossier, validate_adoptions

ROOT = Path(__file__).resolve().parents[4]


def content_errors(candidate, module):
    result = validate_text(candidate.text, filename=candidate.name)
    errors = list(result.errors) + list(result.identity_mismatches)
    if result.exit_code and not errors:
        errors.append("canonical handoff is blocked")
    if errors:
        return errors
    skill = ROOT / module["skill_md"]
    if module["artifact_contract"].get("required_table_ids"):
        errors.extend(check(skill.read_text(encoding="utf-8"), candidate.text, module["module_id"])[0])
    return errors


def accept_snapshot(candidates, cp0, route, authority_digest, readiness=None, *, predicates=None):
    """Return accepted occurrence hashes and an explicit reason for each rejected file.

    Evaluate producers first, with no filename/time heuristic for competing attempts.
    A missing, incomplete, ambiguous or changed producer invalidates its consumers.
    """
    try:
        anchor = envelope.read_anchor(cp0.fields)
    except envelope.EnvelopeError as exc:
        raise ValueError(str(exc)) from exc
    if anchor["authority_bundle_sha256"] != authority_digest:
        raise ValueError("CP-0 authority differs from the verified package; start a new run")
    if (anchor["profile_id"], anchor["selection_id"]) != (route.profile_id, route.selection_id):
        raise ValueError("CP-0 profile/selection differs from the dependency plan")
    accepted, accepted_candidates, problems = {}, {}, {}
    route.research_unresolved.clear()
    by_module = {}
    for candidate in candidates:
        if candidate.name == f"RESEARCH_{anchor['run_id']}.json":
            continue
        fields = candidate.fields or {}
        if fields.get("credit_os_run_id") != anchor["run_id"]:
            problems[candidate.name] = "missing or different run anchor"
            continue
        module_id = fields.get("module_id")
        if not isinstance(module_id, str):
            problems[candidate.name] = "module_id must be a canonical string"
            continue
        if module_id not in route.by_module:
            problems[candidate.name] = "module is outside the selected CP-0 plan"
            continue
        by_module.setdefault(module_id, []).append(candidate)
    for node in route.nodes:
        module_id, occurrence = node["module_id"], node["route_node_id"]
        matches = by_module.get(module_id, [])
        if len(matches) != 1:
            for candidate in matches:
                problems[candidate.name] = f"AMBIGUOUS_RETRY: multiple artifacts claim {module_id}"
            continue
        candidate = matches[0]
        fields = candidate.fields or {}
        try:
            if readiness is not None and module_id != "CP-0" and readiness.get(module_id) not in {"READY", "READY_WITH_LIMITATIONS"}:
                raise ValueError("CP-0 source gate is not runnable for this module")
            errors = content_errors(candidate, route.modules[module_id])
            if errors:
                raise ValueError("; ".join(str(error) for error in errors))
            for key in ("credit_os_profile_id", "credit_os_selection_id", "credit_os_authority_bundle_sha256",
                        "reporting_period", "issuer_id", "issuer_name"):
                if fields.get(key) != cp0.fields.get(key):
                    raise ValueError(f"{key} does not match the selected CP-0 anchor")
            if fields.get("module_name") != node["module_name"]:
                raise ValueError("module name differs from the catalog")
            if module_id == "CP-DR":
                if route.research_brief is None:
                    raise ValueError("linked research requires its current research brief")
                findings = validate_dossier(candidate, route.research_brief)
            elif fields.get("scope_key") != cp0.fields.get("scope_key"):
                raise ValueError("scope_key does not match the selected CP-0 anchor")
            upstream = expected_upstream_digests(route, occurrence, accepted, predicates=predicates, readiness=readiness)
            cp0_occurrence = route.by_module["CP-0"]["route_node_id"]
            cp0_digest = envelope.ZERO_SHA256 if module_id == "CP-0" else accepted.get(cp0_occurrence)
            if cp0_digest is None:
                raise ValueError("missing accepted CP-0 lineage")
            declared = fields.get("upstream_artifacts_used", ())
            expected_records = {route.by_node[key]["module_id"]: accepted_candidates[key] for key in upstream}
            if len(declared) != len(expected_records) or {item.get("module_id") for item in declared} != set(expected_records):
                raise ValueError("upstream_artifacts_used does not match the active dependency plan")
            for item in declared:
                producer = expected_records[item["module_id"]]
                if item.get("run_id") != producer.fields.get("run_id") or item.get("period") != producer.fields.get("reporting_period"):
                    raise ValueError(f"stale upstream identity: {item['module_id']}")
                if item.get("sha256", producer.sha256) != producer.sha256:
                    raise ValueError(f"stale upstream content: {item['module_id']}")
                if item["module_id"] == "CP-DR":
                    validate_adoptions(candidate, producer, route.research_brief)
            envelope.reproduce_and_match(
                fields, run_id=anchor["run_id"], profile_id=route.profile_id,
                selection_id=route.selection_id, route_node_id=occurrence,
                module_id=module_id, module_name=node["module_name"],
                expected_output_filename=candidate.name, authority_bundle_sha256=authority_digest,
                accepted_cp0_sha256=cp0_digest, required_upstream_digests=upstream,
                parent_run_id=anchor["parent_run_id"], upgrade_source_sha256=anchor["upgrade_source_sha256"], ordinal=None,
            )
        except (ValueError, TypeError, KeyError, envelope.EnvelopeError) as exc:
            problems[candidate.name] = str(exc)
            continue
        accepted[occurrence] = candidate.sha256
        accepted_candidates[occurrence] = candidate
        if module_id == "CP-DR":
            unresolved = {f["question_id"] for f in findings if f["resolution_status"] == "UNRESOLVED"}
            route.research_unresolved = {q["consumer_module_id"] for q in route.research_brief["questions"] if q["question_id"] in unresolved}
    return accepted, problems
