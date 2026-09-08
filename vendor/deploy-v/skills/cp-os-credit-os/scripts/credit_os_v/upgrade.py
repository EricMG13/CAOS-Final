"""Validated, linked LITE-to-FULL upgrade planning."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, NamedTuple
from weakref import WeakKeyDictionary

from .identity import (
    FULL_PROFILE,
    LITE_PROFILE,
    RUN_ID,
    SHA256,
    IdentityError,
    new_run_id,
    parse_route_node,
    require,
)
from .reconcile import (
    Observation,
    ReconcileError,
    RunView,
    accepted_artifact_provenance,
)

UPGRADE_OUTCOMES = frozenset({"FULL_UPGRADE_RECOMMENDED", "FULL_UPGRADE_REQUIRED"})
UPGRADE_TARGETS = {
    "CP-L10": frozenset({"CP-1", "CP-1B"}),
    "CP-L20": frozenset({"CP-2", "CP-2C", "CP-2F"}),
    "CP-L23": frozenset({"CP-2D", "CP-2E", "CP-2G"}),
    "CP-L30": frozenset({"CP-3", "CP-3A", "CP-3D"}),
    "CP-L40": frozenset({"CP-4", "CP-4A", "CP-4B"}),
}

CHILD_SCHEMA_REGISTRY_NAME = "CP_DEPLOY_V_CHILD_SCHEMA_REGISTRY_v1.json"
CHILD_SCHEMA_REGISTRY_CANDIDATES = (
    Path(__file__).resolve().parents[2] / "references" / CHILD_SCHEMA_REGISTRY_NAME,
    Path(__file__).resolve().parents[2]
    / "Co-Pilot Agents"
    / "CP-OS"
    / "references"
    / "deploy_v"
    / CHILD_SCHEMA_REGISTRY_NAME,
)


def trusted_child_schema_registry(path: Path | None = None) -> dict:
    """Load the immutable V child-schema registry and fail closed on drift."""
    selected = path
    if selected is None:
        selected = next(
            (candidate for candidate in CHILD_SCHEMA_REGISTRY_CANDIDATES if candidate.is_file()),
            None,
        )
    if selected is None:
        raise UpgradeError("trusted V child-schema registry is unavailable")
    try:
        registry = json.loads(selected.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise UpgradeError("trusted V child-schema registry is unreadable") from exc
    if not isinstance(registry, dict):
        raise UpgradeError("trusted V child-schema registry is malformed")
    if (
        registry.get("schema_version") != "1.0"
        or registry.get("authority") != "CP_DEPLOY_V_CHILD_SCHEMA_REGISTRY_v1"
        or registry.get("deployment_scope") != ["V"]
    ):
        raise UpgradeError("trusted V child-schema registry identity is invalid")
    base = registry.get("base_schema")
    modules = registry.get("modules")
    if not isinstance(base, dict) or not isinstance(modules, list):
        raise UpgradeError("trusted V child-schema registry is incomplete")
    expected = set(UPGRADE_TARGETS)
    records = {row.get("module_id"): row for row in modules if isinstance(row, dict)}
    if set(records) != expected or len(records) != len(modules):
        raise UpgradeError("trusted V child-schema registry module set is invalid")
    if base.get("module_id") != "CP-LITE-BASE":
        raise UpgradeError("trusted V child-schema registry base schema is invalid")
    repository_root = Path(__file__).resolve().parents[2]
    registry_schema = selected.parent / "CP_DEPLOY_V_CHILD_SCHEMA_REGISTRY_v1.schema.json"
    if not registry_schema.is_file():
        raise UpgradeError("trusted V child-schema registry schema is unavailable")
    try:
        schema_document = json.loads(registry_schema.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise UpgradeError("trusted V child-schema registry schema is unreadable") from exc
    if not isinstance(schema_document, dict) or schema_document.get("$id") != "CP_DEPLOY_V_CHILD_SCHEMA_REGISTRY_v1.schema.json":
        raise UpgradeError("trusted V child-schema registry schema is invalid")
    for module_id, row in {"CP-LITE-BASE": base, **records}.items():
        if (
            module_id != "CP-LITE-BASE"
            and row.get("validator") != "validate_cp_l_payload"
        ) or (
            not isinstance(row.get("package_path"), str)
            or Path(row["package_path"]).is_absolute()
            or Path(row["package_path"]).parts[0:1] != ("references",)
            or ".." in Path(row["package_path"]).parts
            or len(Path(row["package_path"]).parts) != 2
            or not re.fullmatch(r"[0-9a-f]{64}", str(row.get("sha256", "")))
        ):
            raise UpgradeError(f"trusted child schema entry is invalid for {module_id}")
        source_path = row.get("source_path")
        if (
            not isinstance(source_path, str)
            or Path(source_path).is_absolute()
            or ".." in Path(source_path).parts
        ):
            raise UpgradeError(f"trusted child schema source path is unsafe for {module_id}")
        source = (repository_root / source_path).resolve()
        if repository_root not in source.parents:
            raise UpgradeError(f"trusted child schema source path escapes the repository for {module_id}")
        package_schema = selected.parent / Path(row["package_path"]).name
        candidates = [candidate for candidate in (package_schema, source) if candidate is not None and candidate.is_file()]
        if not candidates:
            raise UpgradeError(f"trusted child schema bytes are unavailable for {module_id}")
        for candidate in candidates:
            import hashlib

            actual = hashlib.sha256(candidate.read_bytes()).hexdigest()
            if actual != row["sha256"]:
                raise UpgradeError(f"trusted child schema digest is stale for {module_id}")
    return registry


def trusted_child_schema_record(module_id: str) -> dict:
    registry = trusted_child_schema_registry()
    try:
        return registry["modules"][next(
            index
            for index, row in enumerate(registry["modules"])
            if row.get("module_id") == module_id
        )]
    except (StopIteration, KeyError, TypeError):
        raise UpgradeError(f"no trusted child schema is registered for {module_id}") from None

LITE_CONTRACTS = {
    "CP-L10": {
        "module_name": "LiteFinancialChangeScreen",
        "owned_object": "lite_financial_change_screen",
        "topics": (
            "SOURCE_BASIS", "EARNINGS_MARGIN_CHANGE", "CASH_CONVERSION",
            "LEVERAGE_COVERAGE", "LIQUIDITY_MATURITIES", "KPI_COMPARABILITY",
        ),
        "owners": {
            "SOURCE_BASIS": ("CP-1", "CP-1B"),
            "EARNINGS_MARGIN_CHANGE": ("CP-1B",), "CASH_CONVERSION": ("CP-1", "CP-1B"),
            "LEVERAGE_COVERAGE": ("CP-1", "CP-1B"), "LIQUIDITY_MATURITIES": ("CP-1", "CP-1B"),
            "KPI_COMPARABILITY": ("CP-1", "CP-1B"),
        },
        "postures": ("IMPROVING", "STABLE", "DETERIORATING", "MIXED", "INSUFFICIENT_INFORMATION"),
        "forbidden": "canonical_financial_history",
    },
    "CP-L20": {
        "module_name": "LiteFundamentalCreditScreen", "owned_object": "lite_fundamental_credit_screen",
        "topics": ("BUSINESS_DURABILITY", "MARGIN_FCF_RESILIENCE", "LEVERAGE_REFINANCING_CONTEXT", "GOVERNANCE_SPONSOR_BEHAVIOR", "FINANCIAL_POLICY_CAPITAL_ALLOCATION", "ESG_TRANSITION"),
        "owners": {"BUSINESS_DURABILITY": ("CP-2",), "MARGIN_FCF_RESILIENCE": ("CP-2",), "LEVERAGE_REFINANCING_CONTEXT": ("CP-2",), "GOVERNANCE_SPONSOR_BEHAVIOR": ("CP-2C",), "FINANCIAL_POLICY_CAPITAL_ALLOCATION": ("CP-2", "CP-2C"), "ESG_TRANSITION": ("CP-2F",)},
        "postures": ("SUPPORTIVE", "BALANCED", "PRESSURED", "MIXED", "INSUFFICIENT_INFORMATION"),
        "forbidden": "committee_memo",
    },
    "CP-L23": {
        "module_name": "LiteLiquiditySensitivityScreen", "owned_object": "lite_liquidity_sensitivity_screen",
        "topics": ("ACCESSIBLE_LIQUIDITY_USES", "WORKING_CAPITAL_CAPEX_CASH_BURN", "RATES_HEDGES", "FX_COMMODITY_INFLATION", "BASE_DOWNSIDE_TRAJECTORY", "BREAKPOINTS_REFINANCING"),
        "owners": {"ACCESSIBLE_LIQUIDITY_USES": ("CP-2D",), "WORKING_CAPITAL_CAPEX_CASH_BURN": ("CP-2D",), "RATES_HEDGES": ("CP-2E",), "FX_COMMODITY_INFLATION": ("CP-2E",), "BASE_DOWNSIDE_TRAJECTORY": ("CP-2G",), "BREAKPOINTS_REFINANCING": ("CP-2D", "CP-2E", "CP-2G")},
        "postures": ("ADEQUATE_SCREEN", "WATCH", "PRESSURED", "MIXED", "INSUFFICIENT_INFORMATION"),
        "forbidden": "twelve_month_liquidity_bridge",
    },
    "CP-L30": {
        "module_name": "LiteMarketRecoveryOpportunityScreen", "owned_object": "lite_market_recovery_opportunity_screen",
        "topics": ("DATED_MARKET_SNAPSHOT", "CURVE_COMPARABLE_COMPENSATION", "LIQUIDITY_TECHNICALS", "STRUCTURAL_RECOVERY_PROTECTION", "DOWNSIDE_LME_EXPOSURE", "INTEGRATED_SCREENING_POSTURE"),
        "owners": {"DATED_MARKET_SNAPSHOT": ("CP-3D",), "CURVE_COMPARABLE_COMPENSATION": ("CP-3D", "CP-3"), "LIQUIDITY_TECHNICALS": ("CP-3D",), "STRUCTURAL_RECOVERY_PROTECTION": ("CP-3A",), "DOWNSIDE_LME_EXPOSURE": ("CP-3A", "CP-3"), "INTEGRATED_SCREENING_POSTURE": ("CP-3D", "CP-3A", "CP-3")},
        "postures": ("ESCALATE_FOR_FULL_SELECTION", "MONITOR", "DEPRIORITIZE", "INSUFFICIENT_INFORMATION"),
        "forbidden": "buy_sell_hold",
    },
    "CP-L40": {
        "module_name": "LiteLegalStructureCapacityScreen", "owned_object": "lite_legal_structure_capacity_screen",
        "topics": ("CONTROLLING_DOCUMENT_AVAILABILITY", "PROTECTION_WEAKNESS_FLAGS", "ENTITY_GUARANTEE_COLLATERAL", "LEAKAGE_PRIMING_FLAGS", "CAPACITY_AVAILABILITY", "PRESSURE_POINT_UPGRADE_PRIORITY"),
        "owners": {"CONTROLLING_DOCUMENT_AVAILABILITY": ("CP-4",), "PROTECTION_WEAKNESS_FLAGS": ("CP-4",), "ENTITY_GUARANTEE_COLLATERAL": ("CP-4B",), "LEAKAGE_PRIMING_FLAGS": ("CP-4", "CP-4B"), "CAPACITY_AVAILABILITY": ("CP-4A",), "PRESSURE_POINT_UPGRADE_PRIORITY": ("CP-4A",)},
        "postures": ("LOWER_CONCERN", "WATCH", "HEIGHTENED_CONCERN", "MIXED", "INSUFFICIENT_INFORMATION"),
        "forbidden": "exact_capacity",
    },
}

_TOPIC_DISPOSITIONS = frozenset({"DEEPEN", "SUMMARIZE", "GAP_ONLY", "IMMATERIAL"})
_EVIDENCE_STATUSES = frozenset({"SUFFICIENT", "PARTIAL", "MISSING", "CONFLICTED"})
_MATERIALITIES = frozenset({"HIGH", "MEDIUM", "LOW", "NOT_ASSESSABLE"})
_TABLE_IDS = frozenset({"TL10.1", "TL10.2", "TL10.3", "TL10.4", "TL20.1", "TL20.2", "TL20.3", "TL20.4", "TL23.1", "TL23.2", "TL23.3", "TL23.4", "TL30.1", "TL30.2", "TL30.3", "TL30.4", "TL40.1", "TL40.2", "TL40.3", "TL40.4"})
UPGRADE_OWNED_OBJECTS = {
    "CP-L10": {"CP-1": "canonical_financial_data_kpis", "CP-1B": "earnings_delta"},
    "CP-L20": {"CP-2": "fundamental_credit_synthesis", "CP-2C": "governance_sponsor_score", "CP-2F": "esg_credit_risk"},
    "CP-L23": {"CP-2D": "liquidity_cash_flow_bridge", "CP-2E": "macro_fx_hedging_sensitivity", "CP-2G": "forward_credit_model"},
    "CP-L30": {"CP-3D": "market_implied_risk_map", "CP-3A": "recovery_instrument_assessment", "CP-3": "relative_value_assessment"},
    "CP-L40": {"CP-4": "legal_covenant_interpretation", "CP-4B": "structural_priority_map", "CP-4A": "covenant_capacity_calculation"},
}


def validate_cp_l_payload(payload: object, module_id: str) -> bool:
    """Validate the trusted CP-L instance contract used by upgrade routing."""
    try:
        contract = LITE_CONTRACTS[module_id]
        if not isinstance(payload, dict) or payload.get("module_id") != module_id:
            return False
        required = {"module_id", "module_name", "owned_object", "schema_family", "output_class", "runtime_output", "evidence_trace", "confidence_score", "confidence_band", "limitation_flags", "qa_status", "validation_warnings", "downstream_consumers"}
        if set(payload) != required or not required.issubset(payload) or payload.get("module_name") != contract["module_name"] or payload.get("owned_object") != contract["owned_object"] or payload.get("schema_family") != "Nested" or payload.get("output_class") != "CANONICAL_MARKDOWN":
            return False
        if type(payload["confidence_score"]) is not int or not 0 <= payload["confidence_score"] <= 100 or payload["confidence_band"] not in {"High", "Medium", "Low", "Insufficient Information"}:
            return False
        if payload["qa_status"] not in {"Not Reviewed", "Passed", "Restricted", "Blocked"}:
            return False
        if not isinstance(payload["evidence_trace"], dict) or not all(isinstance(value, str) for field in ("limitation_flags", "validation_warnings", "downstream_consumers") for value in payload[field]) or not all(isinstance(payload[field], list) for field in ("limitation_flags", "validation_warnings", "downstream_consumers")):
            return False
        runtime = payload["runtime_output"]
        common = {"decision_scope", "execution_basis", "screen_status", "screen_conclusion", "source_scope_gate", "topic_allocation", "cross_topic_synthesis", "upgrade_plan", "gaps_conflicts"}
        child = {"screening_posture", "decision_screen", "gap_upgrade_register", "table_inventory"}
        if not isinstance(runtime, dict) or set(runtime) - common.union(child, {"allocation_budget"}) or not common.union(child).issubset(runtime) or contract["forbidden"] in runtime:
            return False
        if runtime["decision_scope"] != "SCREENING_ONLY" or runtime["execution_basis"] not in {"SOURCE_DIRECT", "UPSTREAM_HANDOFFS", "MIXED"} or runtime["screen_status"] not in {"COMPLETE", "COMPLETE_WITH_GAPS", "BLOCKED_IDENTITY"} or runtime["screening_posture"] not in contract["postures"]:
            return False
        conclusion = runtime["screen_conclusion"]
        gate = runtime["source_scope_gate"]
        if not isinstance(conclusion, dict) or not isinstance(conclusion.get("summary"), str) or conclusion.get("outcome") not in {"LITE_COMPLETE", *UPGRADE_OUTCOMES} or not isinstance(gate, dict) or gate.get("status") not in {"COMPLETE", "PARTIAL", "BLOCKED_IDENTITY"} or not isinstance(gate.get("subject_identity"), str) or not gate["subject_identity"].strip():
            return False
        if (runtime["screen_status"] == "BLOCKED_IDENTITY") != (gate["status"] == "BLOCKED_IDENTITY"):
            return False
        topics = runtime["topic_allocation"]
        if not isinstance(topics, list) or len(topics) != 6 or {row.get("topic_id") for row in topics if isinstance(row, dict)} != set(contract["topics"]):
            return False
        saw_upgrade = False
        for row in topics:
            if not isinstance(row, dict) or set(row) - {"topic_id", "source_owner_modules", "materiality", "evidence_status", "disposition", "priority_rank", "budget_units", "summary", "source_refs", "upgrade_module_ids", "claim_count", "metric_count", "reader_word_count", "analytical_conclusion", "gap_detail", "immateriality_basis"}:
                return False
            topic = row["topic_id"]
            if tuple(row.get("source_owner_modules", ())) != tuple(contract["owners"][topic]) or row.get("materiality") not in _MATERIALITIES or row.get("evidence_status") not in _EVIDENCE_STATUSES or row.get("disposition") not in _TOPIC_DISPOSITIONS or type(row.get("priority_rank")) is not int or row["priority_rank"] < 1 or not isinstance(row.get("summary"), str) or not row["summary"].strip() or not isinstance(row.get("source_refs"), list) or any(not isinstance(ref, str) or not ref.strip() for ref in row["source_refs"]):
                return False
            disposition = row["disposition"]
            upgrades = row.get("upgrade_module_ids")
            if not isinstance(upgrades, list) or len(upgrades) != len(set(upgrades)) or any(target not in UPGRADE_TARGETS[module_id] for target in upgrades):
                return False
            if disposition in {"DEEPEN", "SUMMARIZE"} and not upgrades:
                return False
            if disposition == "GAP_ONLY":
                gap = row.get("gap_detail")
                if not isinstance(gap, dict) or set(gap) != {"missing_evidence", "decision_impact", "required_source", "full_upgrade_module"} or any(not isinstance(gap[field], str) or not gap[field].strip() for field in ("missing_evidence", "decision_impact", "required_source")) or gap["full_upgrade_module"] not in UPGRADE_TARGETS[module_id] or row.get("analytical_conclusion") is not None or not upgrades:
                    return False
                saw_upgrade = True
            elif "gap_detail" in row:
                return False
            if disposition == "IMMATERIAL" and (row.get("evidence_status") not in {"SUFFICIENT", "PARTIAL"} or not isinstance(row.get("immateriality_basis"), str) or not row["immateriality_basis"].strip()):
                return False
            if disposition != "IMMATERIAL" and "immateriality_basis" in row:
                return False
            if disposition == "DEEPEN":
                saw_upgrade = True
            for optional, expected_type in (("budget_units", (int, float)), ("claim_count", int), ("metric_count", int), ("reader_word_count", int)):
                if optional in row and (type(row[optional]) not in expected_type or row[optional] < 0):
                    return False
            if "analytical_conclusion" in row and (not isinstance(row["analytical_conclusion"], str) or not row["analytical_conclusion"].strip()):
                return False
            if row["materiality"] == "HIGH" and row["evidence_status"] in {"MISSING", "CONFLICTED"} and disposition != "GAP_ONLY":
                return False
        if not isinstance(runtime["decision_screen"], list) or not runtime["decision_screen"] or sum(item.get("screen_item") == "OVERALL" for item in runtime["decision_screen"] if isinstance(item, dict)) != 1:
            return False
        screen_fields = {"screen_item", "assessment", "evidence", "credit_transmission", "screening_implication", "confidence", "source_refs"}
        if any(not isinstance(item, dict) or set(item) != screen_fields or item["confidence"] not in {"HIGH", "MEDIUM", "LOW", "INSUFFICIENT_INFORMATION"} or any(not isinstance(item[field], str) or not item[field].strip() for field in screen_fields - {"source_refs"}) or not isinstance(item["source_refs"], list) or any(not isinstance(ref, str) or not ref.strip() for ref in item["source_refs"]) for item in runtime["decision_screen"]):
            return False
        if not isinstance(runtime["gap_upgrade_register"], list) or any(not isinstance(item, dict) or set(item) != {"topic_id", "trigger", "missing_inputs", "decision_impact", "required_source", "target_full_module_id", "expected_owned_object", "blocking_for_full_decision"} or item["topic_id"] not in contract["topics"] or item["target_full_module_id"] not in UPGRADE_TARGETS[module_id] or item["expected_owned_object"] != UPGRADE_OWNED_OBJECTS[module_id][item["target_full_module_id"]] or not isinstance(item["missing_inputs"], list) or any(not isinstance(value, str) or not value.strip() for value in item["missing_inputs"]) or any(not isinstance(item[field], str) or not item[field].strip() for field in ("trigger", "decision_impact", "required_source", "expected_owned_object")) or not isinstance(item["blocking_for_full_decision"], bool) for item in runtime["gap_upgrade_register"]):
            return False
        plan = runtime["upgrade_plan"]
        if not isinstance(plan, list) or any(not isinstance(item, dict) for item in plan):
            return False
        for item in plan:
            if set(item) != {"topic_id", "target_full_module_id", "trigger", "missing_inputs", "expected_owned_object", "blocking_for_full_decision", "decision_impact", "required_source"}:
                return False
            if item["topic_id"] not in contract["topics"] or item["target_full_module_id"] not in UPGRADE_TARGETS[module_id] or item["expected_owned_object"] != UPGRADE_OWNED_OBJECTS[module_id][item["target_full_module_id"]] or not isinstance(item["missing_inputs"], list) or any(not isinstance(value, str) or not value.strip() for value in item["missing_inputs"]) or not isinstance(item["blocking_for_full_decision"], bool) or any(not isinstance(item[field], str) or not item[field].strip() for field in ("trigger", "expected_owned_object", "decision_impact", "required_source")):
                return False
        if saw_upgrade and conclusion["outcome"] == "LITE_COMPLETE":
            return False
        if conclusion["outcome"] in UPGRADE_OUTCOMES and not plan:
            return False
        table_inventory = runtime["table_inventory"]
        if not isinstance(table_inventory, list) or any(not isinstance(item, str) for item in table_inventory):
            return False
        ids = set(table_inventory)
        prefix = module_id[4:]
        return ids == {f"TL{prefix}.{index}" for index in range(1, 5)}
    except (KeyError, TypeError, AttributeError):
        return False


class UpgradeError(ValueError):
    pass


@dataclass(frozen=True, eq=False)
class UpgradeSignal:
    parent_run_id: str
    source_module_id: str
    source_sha256: str
    outcome: str
    targets: tuple[str, ...]


@dataclass(frozen=True, eq=False)
class UpgradeBootstrap:
    run_id: str
    profile_id: str
    parent_run_id: str
    upgrade_source_sha256: str


class _UpgradeSignalSnapshot(NamedTuple):
    """Canonical immutable provenance recorded when a signal is minted."""

    parent_run_id: str
    source_module_id: str
    source_sha256: str
    outcome: str
    targets: tuple[str, ...]


class _UpgradeBootstrapSnapshot(NamedTuple):
    """Canonical immutable linkage recorded when a bootstrap is minted."""

    run_id: str
    profile_id: str
    parent_run_id: str
    upgrade_source_sha256: str


_MINTED_SIGNALS: WeakKeyDictionary[UpgradeSignal, _UpgradeSignalSnapshot] = (
    WeakKeyDictionary()
)
_MINTED_BOOTSTRAPS: WeakKeyDictionary[
    UpgradeBootstrap, _UpgradeBootstrapSnapshot
] = WeakKeyDictionary()


def _signal_snapshot(signal: UpgradeSignal) -> _UpgradeSignalSnapshot | None:
    """Return a canonical snapshot only for exact primitive signal fields."""
    if (
        type(signal.parent_run_id) is not str
        or type(signal.source_module_id) is not str
        or type(signal.source_sha256) is not str
        or type(signal.outcome) is not str
        or type(signal.targets) is not tuple
        or any(type(target) is not str for target in signal.targets)
    ):
        return None
    return _UpgradeSignalSnapshot(
        parent_run_id=signal.parent_run_id,
        source_module_id=signal.source_module_id,
        source_sha256=signal.source_sha256,
        outcome=signal.outcome,
        targets=signal.targets,
    )


def _bootstrap_snapshot(bootstrap: UpgradeBootstrap) -> _UpgradeBootstrapSnapshot | None:
    """Return a canonical snapshot only for exact primitive bootstrap fields."""
    if (
        type(bootstrap.run_id) is not str
        or type(bootstrap.profile_id) is not str
        or type(bootstrap.parent_run_id) is not str
        or type(bootstrap.upgrade_source_sha256) is not str
    ):
        return None
    return _UpgradeBootstrapSnapshot(
        run_id=bootstrap.run_id,
        profile_id=bootstrap.profile_id,
        parent_run_id=bootstrap.parent_run_id,
        upgrade_source_sha256=bootstrap.upgrade_source_sha256,
    )


def _mint_signal(signal: UpgradeSignal) -> None:
    snapshot = _signal_snapshot(signal)
    if snapshot is None:  # Defensive: callers construct this only from validated values.
        raise UpgradeError("cannot mint an upgrade signal with non-canonical fields")
    _MINTED_SIGNALS[signal] = snapshot


def _mint_bootstrap(bootstrap: UpgradeBootstrap) -> None:
    snapshot = _bootstrap_snapshot(bootstrap)
    if snapshot is None:  # Defensive: callers construct this only from validated values.
        raise UpgradeError("cannot mint an upgrade bootstrap with non-canonical fields")
    _MINTED_BOOTSTRAPS[bootstrap] = snapshot


def _validated_signal_snapshot(signal: object) -> _UpgradeSignalSnapshot:
    if not isinstance(signal, UpgradeSignal):
        raise UpgradeError("upgrade signal was not minted by runtime validation")
    snapshot = _MINTED_SIGNALS.get(signal)
    if snapshot is None or _signal_snapshot(signal) != snapshot:
        raise UpgradeError("upgrade signal provenance changed after runtime validation")
    return snapshot


def _validated_bootstrap_snapshot(bootstrap: object) -> _UpgradeBootstrapSnapshot:
    if not isinstance(bootstrap, UpgradeBootstrap):
        raise UpgradeError("upgrade bootstrap was not minted by confirmed validation")
    snapshot = _MINTED_BOOTSTRAPS.get(bootstrap)
    if snapshot is None or _bootstrap_snapshot(bootstrap) != snapshot:
        raise UpgradeError("upgrade bootstrap linkage changed after confirmed validation")
    return snapshot


def require_validated_upgrade_signal(signal: object) -> UpgradeSignal:
    """Return only a signal minted by successful runtime validation."""
    _validated_signal_snapshot(signal)
    assert isinstance(signal, UpgradeSignal)
    return signal


def require_validated_upgrade_bootstrap(bootstrap: object) -> UpgradeBootstrap:
    """Return only a bootstrap minted by the confirmed upgrade path."""
    _validated_bootstrap_snapshot(bootstrap)
    assert isinstance(bootstrap, UpgradeBootstrap)
    return bootstrap


def validated_upgrade_signal_snapshot(signal: object) -> _UpgradeSignalSnapshot:
    """Validate a signal and expose only its immutable mint-time provenance."""
    return _validated_signal_snapshot(signal)


def validated_upgrade_bootstrap_snapshot(bootstrap: object) -> _UpgradeBootstrapSnapshot:
    """Validate a bootstrap and expose only its immutable mint-time linkage."""
    return _validated_bootstrap_snapshot(bootstrap)


def validated_upgrade_signal(
    view: RunView,
    observation: Observation,
    payload: object,
    *,
    schema_validator: Callable[[object, str], bool] | None = None,
) -> UpgradeSignal:
    """Validate schema first, then the routing fields allowed to activate upgrade UI."""
    if schema_validator is not None and schema_validator is not validate_cp_l_payload:
        raise UpgradeError("caller-supplied CP-L schema validators are not trusted")
    try:
        run, source = accepted_artifact_provenance(view, observation)
    except ReconcileError as exc:
        raise UpgradeError(str(exc)) from exc
    if run.profile_id != LITE_PROFILE:
        raise UpgradeError("only a LITE run may request a FULL upgrade")
    if source.module_id not in UPGRADE_TARGETS:
        raise UpgradeError("upgrade source must be a CP-L module")
    schema_record = trusted_child_schema_record(source.module_id)
    try:
        require(SHA256, view.authority_bundle_sha256, "C authority bundle sha256")
    except IdentityError as exc:
        raise UpgradeError("upgrade source has no verified C authority digest") from exc
    try:
        require(SHA256, source.sha256, "upgrade source sha256")
        node_profile, node_selection, _stage, node_module = parse_route_node(
            source.route_node_id
        )
    except IdentityError as exc:
        raise UpgradeError("upgrade source has no valid route occurrence") from exc
    if (node_profile, node_selection, node_module) != (
        run.profile_id,
        run.selection_id,
        source.module_id,
    ):
        raise UpgradeError("upgrade source route does not belong to this run")
    if schema_record.get("validator") != "validate_cp_l_payload":
        raise UpgradeError("selected child-schema validator is not trusted")
    try:
        schema_valid = validate_cp_l_payload(payload, source.module_id)
    except Exception as exc:
        raise UpgradeError(f"CP-L payload schema validation failed: {exc}") from exc
    if schema_valid is not True:
        raise UpgradeError("CP-L payload is not schema-valid")
    if not isinstance(payload, dict) or payload.get("module_id") != source.module_id:
        raise UpgradeError("structured payload identity does not match the accepted artifact")
    if payload.get("output_class") != "CANONICAL_MARKDOWN":
        raise UpgradeError("structured payload has no canonical output class")
    runtime = payload.get("runtime_output")
    if not isinstance(runtime, dict):
        raise UpgradeError("structured payload has no runtime_output")
    if runtime.get("decision_scope") != "SCREENING_ONLY":
        raise UpgradeError("structured payload is not a LITE screening result")
    conclusion = runtime.get("screen_conclusion")
    if not isinstance(conclusion, dict) or conclusion.get("outcome") not in UPGRADE_OUTCOMES:
        raise UpgradeError("structured outcome does not request a FULL upgrade")
    plan = runtime.get("upgrade_plan")
    if not isinstance(plan, list) or not plan:
        raise UpgradeError("structured upgrade plan must be non-empty")
    targets = []
    required = {
        "topic_id",
        "target_full_module_id",
        "trigger",
        "missing_inputs",
        "expected_owned_object",
        "blocking_for_full_decision",
    }
    for index, item in enumerate(plan):
        if not isinstance(item, dict) or not required.issubset(item):
            raise UpgradeError(f"upgrade_plan[{index}] is incomplete")
        target = item["target_full_module_id"]
        if target not in UPGRADE_TARGETS[source.module_id]:
            raise UpgradeError(
                f"upgrade_plan[{index}] target is not owned by {source.module_id}"
            )
        if not isinstance(item["missing_inputs"], list):
            raise UpgradeError(f"upgrade_plan[{index}].missing_inputs must be a list")
        if any(not isinstance(value, str) or not value.strip() for value in item["missing_inputs"]):
            raise UpgradeError(
                f"upgrade_plan[{index}].missing_inputs must contain non-empty strings"
            )
        if not isinstance(item["blocking_for_full_decision"], bool):
            raise UpgradeError(f"upgrade_plan[{index}].blocking_for_full_decision must be boolean")
        for field in ("topic_id", "trigger", "expected_owned_object"):
            if not isinstance(item[field], str) or not item[field].strip():
                raise UpgradeError(f"upgrade_plan[{index}].{field} must be non-empty")
        targets.append(target)
    signal = UpgradeSignal(
        parent_run_id=run.run_id,
        source_module_id=source.module_id,
        source_sha256=source.sha256,
        outcome=conclusion["outcome"],
        targets=tuple(dict.fromkeys(targets)),
    )
    _mint_signal(signal)
    return signal


def create_linked_full_run(
    *,
    view: RunView,
    observation: Observation,
    payload: object,
    schema_validator: Callable[[object, str], bool] | None = None,
    confirmed: bool,
    now: datetime | None = None,
) -> UpgradeBootstrap:
    """Validate and confirm a LITE artifact before minting a linked FULL run."""
    if confirmed is not True:
        raise UpgradeError("explicit user confirmation is required")
    signal = validated_upgrade_signal(
        view,
        observation,
        payload,
        schema_validator=schema_validator,
    )
    signal_snapshot = validated_upgrade_signal_snapshot(signal)
    try:
        require(RUN_ID, signal_snapshot.parent_run_id, "parent_run_id")
        require(SHA256, signal_snapshot.source_sha256, "upgrade_source_sha256")
    except IdentityError as exc:
        raise UpgradeError(f"upgrade linkage is invalid: {exc}") from exc
    bootstrap = UpgradeBootstrap(
        run_id=new_run_id(now=now),
        profile_id=FULL_PROFILE,
        parent_run_id=signal_snapshot.parent_run_id,
        upgrade_source_sha256=signal_snapshot.source_sha256,
    )
    _mint_bootstrap(bootstrap)
    return bootstrap
