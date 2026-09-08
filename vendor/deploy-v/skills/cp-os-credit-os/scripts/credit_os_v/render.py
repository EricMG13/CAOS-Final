"""Numbered, profile-visible cards for the Deploy V control plane."""

from __future__ import annotations

from . import envelope as env
from .identity import FULL_PROFILE, LITE_PROFILE
from .reconcile import RunView
from .routing import Route, expected_upstream_digests, frontier
from .upgrade import (
    UpgradeBootstrap,
    UpgradeSignal,
    require_validated_upgrade_bootstrap,
    require_validated_upgrade_signal,
    validated_upgrade_bootstrap_snapshot,
    validated_upgrade_signal_snapshot,
)


def _numbered(values: list[str]) -> str:
    return "\n".join(f"{index}. {value}" for index, value in enumerate(values, 1))


def profile_selection_card() -> str:
    return "\n".join(
        (
            "Choose the assessment profile.",
            "",
            _numbered(
                [
                    f"{FULL_PROFILE} — complete governed assessment.",
                    f"{LITE_PROFILE} — consolidated screening with explicit FULL upgrade routing.",
                ]
            ),
        )
    )


def use_case_selection_card(catalog: dict, profile_id: str) -> str:
    pathways = catalog["profiles"][profile_id]["pathways"]
    labels = [
        f"{pathway['selection_id']} — {pathway['menu_label']}"
        for pathway in pathways.values()
    ]
    return f"Profile: {profile_id}\n\nChoose the use case.\n\n{_numbered(labels)}"


def first_run_card(
    *,
    catalog: dict,
    run_id: str,
    profile_id: str,
    selection_id: str,
    authority_bundle_sha256: str,
    expected_output_filename: str,
    upgrade: UpgradeBootstrap | None = None,
    ordinal: int = 1,
) -> str:
    route = Route(catalog, profile_id, selection_id)
    node = route.nodes[0]
    if node["module_id"] != "CP-0":
        raise ValueError("the selected pathway does not begin with CP-0")
    parent_run_id = None
    upgrade_source_sha256 = None
    if upgrade is not None:
        require_validated_upgrade_bootstrap(upgrade)
        bootstrap = validated_upgrade_bootstrap_snapshot(upgrade)
        if (
            profile_id != FULL_PROFILE
            or run_id != bootstrap.run_id
            or bootstrap.profile_id != FULL_PROFILE
        ):
            raise ValueError("a linked upgrade bootstrap must start its minted FULL run")
        parent_run_id = bootstrap.parent_run_id
        upgrade_source_sha256 = bootstrap.upgrade_source_sha256
    invocation = env.build(
        run_id=run_id,
        profile_id=profile_id,
        selection_id=selection_id,
        route_node_id=node["route_node_id"],
        module_id="CP-0",
        module_name=node["module_name"],
        expected_output_filename=expected_output_filename,
        authority_bundle_sha256=authority_bundle_sha256,
        accepted_cp0_sha256=env.ZERO_SHA256,
        parent_run_id=parent_run_id,
        upgrade_source_sha256=upgrade_source_sha256,
        ordinal=ordinal,
    )
    return "\n".join(
        (
            "🟢 START HERE: CP-0 — SourceReadiness",
            f"Profile: {profile_id}",
            f"Pathway: {selection_id}",
            "",
            "▶️ COPY INTO A SEPARATE SESSION",
            env.render_copy_block(invocation),
            "",
            _numbered(["CP-0 has been run; check the folder.", "Stop here."]),
        )
    )


# Compatibility export for callers of the previous renderer API. Its behavior
# now follows the canonical route and renders CP-0 as the first module.
cp0_first_run_card = first_run_card


def next_module_card(
    *,
    catalog: dict,
    route: Route,
    view: RunView,
    expected_output_filename: str,
    ordinal: int = 1,
) -> str:
    if view.authority_drifted:
        return (
            f"Profile: {view.profile_id}\nPathway: {view.selection_id}\n\n"
            "⚠️ Authority changed. Restart the run under the current verified authority."
        )
    ready = frontier(route, view.as_routing_state())
    if not ready:
        return f"Profile: {view.profile_id}\nPathway: {view.selection_id}\n\n✅ No runnable node remains."
    node = route.by_node[ready[0]]
    display = next(
        (item["display"] for item in catalog["modules"] if item["module_id"] == node["module_id"]),
        node["module_id"],
    )
    accepted = {
        item.route_node_id: item.sha256
        for item in view.accepted()
        if item.route_node_id and item.sha256
    }
    cp0 = next(
        (item for item in view.accepted() if item.module_id == "CP-0" and item.sha256),
        None,
    )
    accepted_cp0_sha256 = (
        env.ZERO_SHA256 if node["module_id"] in {"CP-0"} else None
    )
    if accepted_cp0_sha256 is None:
        if cp0 is None:
            raise ValueError("a downstream invocation requires an accepted CP-0 artifact")
        accepted_cp0_sha256 = cp0.sha256
    invocation = env.build(
        run_id=view.run_id,
        profile_id=view.profile_id,
        selection_id=view.selection_id,
        route_node_id=node["route_node_id"],
        module_id=node["module_id"],
        module_name=node["module_name"],
        expected_output_filename=expected_output_filename,
        authority_bundle_sha256=view.authority_bundle_sha256,
        accepted_cp0_sha256=accepted_cp0_sha256,
        required_upstream_digests=expected_upstream_digests(
            route, node["route_node_id"], accepted, readiness=view.source_readiness
        ),
        parent_run_id=view.parent_run_id,
        upgrade_source_sha256=view.upgrade_source_sha256,
        ordinal=ordinal,
    )
    return "\n".join(
        (
            f"🟢 NEXT: {display}",
            f"Profile: {view.profile_id}",
            f"Pathway: {view.selection_id}",
            f"Route node: {node['route_node_id']}",
            "",
            "▶️ COPY INTO A SEPARATE SESSION",
            env.render_copy_block(invocation),
            "",
            _numbered([f"{display} has been run; check the folder.", "Stop here."]),
        )
    )


def resume_card(view: RunView) -> str:
    return "\n".join(
        (
            "📁 RESUMING RUN",
            f"Run: {view.run_id}",
            f"Profile: {view.profile_id}",
            f"Pathway: {view.selection_id}",
            f"Accepted: {len(view.accepted())}",
            f"Not accepted: {len(view.problems())}",
            "",
            _numbered(["Continue with the next module.", "Stop here."]),
        )
    )


def upgrade_confirmation_card(*, signal: UpgradeSignal) -> str:
    require_validated_upgrade_signal(signal)
    validated = validated_upgrade_signal_snapshot(signal)
    return "\n".join(
        (
            "⚠️ FULL UPGRADE AVAILABLE",
            f"Validated source: {validated.source_module_id} ({validated.source_sha256})",
            "The current LITE run will remain unchanged. Confirmation creates a linked new FULL run.",
            "",
            _numbered(["Create the linked FULL run.", "Keep the current LITE run only."]),
        )
    )
