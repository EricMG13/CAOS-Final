"""Run-local research requests and the evidence/adoption contract; no I/O effects."""
from datetime import date
import json
import re

from cp_tables import parse_tables
from . import envelope
from .identity import RUN_ID, require

SCHEMA = "CP_DR_RESEARCH_BRIEF_V1"
QUESTION_COLUMNS = ("question_id", "question", "decision_relevance", "consumer_module_id", "after_module_id", "evidence_needed", "completion_test")
EVIDENCE_COLUMNS = ("evidence_id", "question_id", "claim", "claim_type", "source", "source_locator", "source_date", "source_type", "independence_family", "entity_period_unit_perimeter")
FINDING_COLUMNS = ("question_id", "answer", "evidence_ids", "contrary_evidence", "resolution_status", "uncertainty", "proposed_consequence")
ADOPTION_COLUMNS = ("question_id", "research_sha256", "disposition", "reason", "analytical_effect")


def validate_brief(brief, *, cp0=None):
    if not isinstance(brief, dict) or brief.get("schema") != SCHEMA:
        raise ValueError("research brief has an unsupported schema")
    require(RUN_ID, brief.get("run_id"), "research run_id")
    if brief.get("mode") not in {"linked", "standalone"}:
        raise ValueError("research mode must be linked or standalone")
    if brief.get("scope_type") not in {"issuer", "sector"} or not re.fullmatch(r"[A-Za-z0-9]+(?:[.-][A-Za-z0-9]+)*", str(brief.get("scope_key", ""))):
        raise ValueError("research scope is invalid")
    for field in ("subject_name", "decision_context", "time_horizon", "authorization_basis", "exclusions"):
        if not isinstance(brief.get(field), str) or not brief[field].strip():
            raise ValueError(f"research brief requires {field}")
    if date.fromisoformat(brief.get("as_of_date", "")).isoformat() != brief["as_of_date"]:
        raise ValueError("research as_of_date must be YYYY-MM-DD")
    if brief.get("source_mode") not in {"supplied_only", "web_only", "hybrid"} or brief.get("budget") not in {"standard", "extended"}:
        raise ValueError("research source mode or budget is invalid")
    if cp0 is not None:
        fields = cp0.fields
        expected = {"mode": "linked", "run_id": fields["credit_os_run_id"], "cp0_sha256": cp0.sha256,
                    "authority_sha256": fields["credit_os_authority_bundle_sha256"],
                    "scope_type": "issuer", "scope_key": str(fields["issuer_id"]), "subject_name": fields["issuer_name"]}
        if any(brief.get(k) != v for k, v in expected.items()):
            raise ValueError("research brief differs from the selected CP-0 identity or anchor")
    elif brief["mode"] != "standalone":
        raise ValueError("linked research requires the current CP-0 anchor")
    questions = brief.get("questions")
    if not isinstance(questions, list) or not 1 <= len(questions) <= 32:
        raise ValueError("research brief requires 1–32 bounded questions")
    seen = set()
    for row in questions:
        if not isinstance(row, dict) or set(row) != set(QUESTION_COLUMNS) or any(not isinstance(v, str) or not v.strip() for v in row.values()):
            raise ValueError("research question fields are missing or malformed")
        qid = row["question_id"]
        if not re.fullmatch(r"RQ-[A-Za-z0-9-]{1,40}", qid) or qid in seen:
            raise ValueError("research question IDs must be unique RQ-* identifiers")
        seen.add(qid)
        if brief["mode"] == "standalone" and (row["consumer_module_id"], row["after_module_id"]) != ("NONE", "NONE"):
            raise ValueError("standalone questions use NONE for consumer and predecessor")
    return brief


def brief_from_snapshot(candidates, cp0):
    name = f"RESEARCH_{cp0.fields['credit_os_run_id']}.json"
    matches = [a for a in candidates if a.name == name]
    if len(matches) > 1:
        raise ValueError("multiple current research briefs")
    if matches and len(matches[0].text.encode("utf-8")) > 65536:
        raise ValueError("research brief exceeds 64 KiB")
    return validate_brief(json.loads(matches[0].text), cp0=cp0) if matches else None


def rows(text, table_id, columns):
    table = parse_tables(text).get(table_id)
    if table is None or tuple(table.columns) != columns or not table.rows:
        raise ValueError(f"{table_id}: required nonempty register/columns missing")
    if any(not value.strip() for row in table.rows for value in row.values()):
        raise ValueError(f"{table_id}: empty register cell")
    if any(value.strip().casefold() in {"tbd", "n/a", "unknown", "requires_analyst_decision", "[insufficient information]", "—"}
           for row in table.rows for value in row.values()):
        raise ValueError(f"{table_id}: unresolved placeholder in register")
    return table.rows


def validate_dossier(candidate, brief):
    """Verify fixed question coverage, usable evidence, and a finding per question."""
    fields = candidate.fields
    if fields.get("approved_plan_hash") != "sha256:" + envelope.digest(brief):
        raise ValueError("research approved plan hash differs from the current brief")
    for key in ("scope_type", "scope_key", "subject_name", "source_mode"):
        if fields.get(key) != brief[key]:
            raise ValueError(f"research {key} differs from its brief")
    if fields.get("research_mode") != brief["mode"] or fields.get("run_id") != brief["run_id"]:
        raise ValueError("research mode or run identity differs from its brief")
    if brief["mode"] == "standalone" and any(key.startswith("credit_os_") for key in fields):
        raise ValueError("standalone research cannot declare issuer-workflow lineage")
    questions = rows(candidate.text, "cpdr.questions", QUESTION_COLUMNS)
    if questions != brief["questions"]:
        raise ValueError("research questions differ from the locked coverage denominator")
    wanted = {q["question_id"] for q in questions}
    by_id = {}
    for row in rows(candidate.text, "cpdr.evidence", EVIDENCE_COLUMNS):
        if row["evidence_id"] in by_id or row["question_id"] not in wanted:
            raise ValueError("research evidence IDs are duplicated or refer to an unknown question")
        if row["claim_type"] not in {"fact", "source_characterisation", "inference", "analyst_judgment"}:
            raise ValueError("research claim_type is invalid")
        if row["source_type"] not in {"primary", "independent_secondary", "attributed_view", "gap"}:
            raise ValueError("research source_type is invalid")
        if row["source_type"] != "gap":
            source_date = date.fromisoformat(row["source_date"])
            if source_date.isoformat() != row["source_date"] or source_date > date.fromisoformat(brief["as_of_date"]):
                raise ValueError("research source date is invalid or after the brief's as-of boundary")
            if brief["source_mode"] == "web_only" and not re.match(r"https?://", row["source"]):
                raise ValueError("web-only research requires retrievable source URLs")
        by_id[row["evidence_id"]] = row
    findings = rows(candidate.text, "cpdr.findings", FINDING_COLUMNS)
    if len(findings) != len(wanted) or {r["question_id"] for r in findings} != wanted:
        raise ValueError("research requires exactly one finding for every locked question")
    answered = 0
    for row in findings:
        sources = [by_id.get(evidence_id.strip()) for evidence_id in row["evidence_ids"].split(";")]
        if any(source is None or source["question_id"] != row["question_id"] for source in sources):
            raise ValueError("research finding cites unknown or cross-question evidence")
        if row["resolution_status"] not in {"ANSWERED", "UNRESOLVED"}:
            raise ValueError("research finding resolution_status is invalid")
        if row["resolution_status"] == "ANSWERED":
            families = {source["independence_family"] for source in sources if source["source_type"] == "independent_secondary"}
            if not any(source["source_type"] in {"primary", "attributed_view"} for source in sources) and len(families) < 2:
                raise ValueError("answered research needs primary evidence, an explicitly attributed view, or two independent sources")
            answered += 1
    coverage = (100 * answered + len(wanted) // 2) // len(wanted)
    if fields.get("coverage_score") != coverage:
        raise ValueError(f"research coverage_score must be {coverage} from the locked questions")
    expected_status = "Complete" if answered == len(wanted) else "Complete with Gaps"
    if fields.get("research_status") != expected_status:
        raise ValueError(f"research_status must be {expected_status}")
    return findings


def validate_adoptions(candidate, producer, brief):
    questions = {q["question_id"] for q in brief["questions"] if q["consumer_module_id"] == candidate.fields["module_id"]}
    adopted = rows(candidate.text, "cpdr.adoptions", ADOPTION_COLUMNS)
    if len(adopted) != len(questions) or {r["question_id"] for r in adopted} != questions:
        raise ValueError("research adoption must address every question assigned to this consumer")
    for row in adopted:
        if row["research_sha256"] != producer.sha256:
            raise ValueError("research adoption refers to stale research content")
        if row["disposition"] not in {"ACCEPTED", "REJECTED", "QUALIFIED"}:
            raise ValueError("research adoption disposition is invalid")
