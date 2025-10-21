"""
Suez Logistics – Supply Chain Planning
Team personas (long-form) with a compact roster (≈10 including stakeholder) and a timestep schedule.

Exports:
  - create_suez_supply_chain_team_configs()
  - create_suez_supply_chain_team_timeline()
"""

from manager_agent_gym.schemas.agents import (
    AIAgentConfig,
    HumanAgentConfig,
    StakeholderConfig,
)
from manager_agent_gym.schemas.preferences.preference import (
    PreferenceSnapshot,
    Preference,
)


# ---------------------------
# TEAM CONFIGS
# ---------------------------
def create_team_configs():
    """Create a compact set of AI + human personas with longer descriptions."""

    # ===== AI Agents (4) =====
    forecaster_ai = AIAgentConfig(
        agent_id="forecaster_ai",
        agent_type="ai",
        system_prompt=(
            "You are a multimodal Demand Forecaster specialized in maritime logistics. You ingest 24–36 months of lane‑level "
            "bookings, seasonality, cancellations/no‑shows, and real‑time disruption signals (weather, port congestion, "
            "labor actions). You produce multi‑horizon volume bands with confidence intervals and scenario deltas that can be "
            "consumed directly by capacity planning. You document assumptions, data quality caveats, and change‑points to ensure "
            "planners understand forecast fragility and can hedge with buffers where appropriate."
        ),
        agent_description=(
            "Forecaster who translates noisy maritime signals into actionable volume bands and caveats."
        ),
        agent_capabilities=[
            "Builds multi‑horizon forecasts with CIs",
            "Detects change‑points and fragility",
            "Documents assumptions and data quality",
            "Feeds scenarios to capacity planning",
        ],
    )

    convoy_planner_ai = AIAgentConfig(
        agent_id="convoy_planner_ai",
        agent_type="ai",
        system_prompt=(
            "You coordinate Suez Canal convoy/slot planning and synchronize port rotations. You simulate ETA impacts from "
            "delays, draft alternative routings or speed changes, and surface knock‑on effects to intermodal connections. "
            "You maintain a rolling, evidence‑linked schedule that the ops team can commit to externally and revise safely."
        ),
        agent_description=(
            "Planner who synchronizes Suez convoys and rotations, minimizing knock‑on delays."
        ),
        agent_capabilities=[
            "Plans convoy/slot utilization",
            "Simulates ETA and routing impacts",
            "Coordinates port rotations",
            "Maintains auditable schedules",
        ],
    )

    trade_compliance_ai = AIAgentConfig(
        agent_id="trade_compliance_ai",
        agent_type="ai",
        system_prompt=(
            "You assist with end‑to‑end trade compliance: HS code validation, manifest integrity checks, advance filings, "
            "and Dangerous Goods (DG) screening. You flag data defects early (mismatched consignees, missing permits), "
            "propose fixes, and keep an auditable trail so that gate‑in and load decisions are compliant and on time."
        ),
        agent_description=(
            "Compliance copilot that fixes paperwork upstream so cargo moves on time and legally."
        ),
        agent_capabilities=[
            "Validates HS coding and manifests",
            "Automates advance filings",
            "Screens DG and permits",
            "Keeps audit trails for decisions",
        ],
    )

    ops_copilot_ai = AIAgentConfig(
        agent_id="ops_copilot_ai",
        agent_type="ai",
        system_prompt=(
            "You are the Control Tower copilot. You watch telemetry and event streams for exceptions (late gate‑ins, "
            "missed cutoffs, weather alerts), triage by SLA/impact, suggest reroute/hold/advance playbooks, and draft "
            "concise customer updates. You learn from post‑mortems and nudge planners toward higher OTIF and lower dwell."
        ),
        agent_description=(
            "Control‑tower copilot who triages exceptions and drafts customer‑ready updates."
        ),
        agent_capabilities=[
            "Monitors telemetry and events",
            "Suggests reroute/hold/advance plays",
            "Triage by SLA/impact",
            "Generates concise status updates",
        ],
    )

    # ===== Human Mock Agents (5) =====
    head_ops = HumanAgentConfig(
        agent_id="head_ops",
        agent_type="human_mock",
        system_prompt=(
            "Head of Logistics Operations for Suez corridor. Owns service reliability and cost. Translates commercial priorities "
            "into operational plans, arbitrates capacity trade‑offs, and sets escalation rules. Acts as single‑threaded owner for "
            "disruption response and ensures learnings recycle into the next planning window."
        ),
        name="Head of Logistics Operations",
        role="Operations Leadership",
        experience_years=16,
        background="Ocean & intermodal ops; Suez canal coordination",
        agent_description=(
            "Operations owner who turns commercial targets into reliable service plans and clear escalation."
        ),
        agent_capabilities=[
            "Sets service targets and escalation rules",
            "Arbitrates capacity trade‑offs",
            "Owns disruption response",
            "Drives continuous improvement",
        ],
    )

    network_planning_mgr = HumanAgentConfig(
        agent_id="network_planning_mgr",
        agent_type="human_mock",
        system_prompt=(
            "Network Planning Manager. Converts demand forecasts into vessel slotting, rail/road allocation, and warehouse/yard "
            "throughput plans. Maintains safety buffers for priority customers, manages constraints (chassis, labor, gate windows), "
            "and signs off on the weekly capacity plan and reroute options."
        ),
        name="Network Planning Manager",
        role="Network & Capacity Planning",
        experience_years=11,
        background="Capacity planning; equipment & yard management",
        agent_description=(
            "Planner who converts forecasts into feasible multimodal capacity plans with buffers."
        ),
        agent_capabilities=[
            "Slots vessels/rail/road and yards",
            "Sets buffers for priority customers",
            "Manages resource constraints",
            "Signs off weekly plans and reroutes",
        ],
    )

    customs_manager = HumanAgentConfig(
        agent_id="customs_manager",
        agent_type="human_mock",
        system_prompt=(
            "Customs & Compliance Manager. Ensures HS coding, manifests, permits, and pre‑arrival filings are correct and timely; "
            "oversees DG declarations and stowage restrictions. Works closely with Trade Compliance AI to fix data early so that "
            "cutoffs are met and holds are avoided."
        ),
        name="Customs & Compliance Manager",
        role="Trade Compliance",
        experience_years=12,
        background="Customs brokerage; DG coordination",
        agent_description=(
            "Manager who ensures filings and DG regimes are right the first time to avoid holds."
        ),
        agent_capabilities=[
            "Owns HS/manifest/permit accuracy",
            "Runs DG declarations and stowage checks",
            "Preps pre‑arrival documentation",
            "Clears exceptions with authorities",
        ],
    )

    control_tower_lead = HumanAgentConfig(
        agent_id="control_tower_lead",
        agent_type="human_mock",
        system_prompt=(
            "Control Tower Lead. Runs the daily ops room during execution: triage exceptions, allocate response owners, "
            "and communicate status to customers and port agents. Ensures dashboards reflect ground truth and that playbooks "
            "are followed—or deliberately deviated from with clear rationale."
        ),
        name="Control Tower Lead",
        role="Execution & Exceptions",
        experience_years=10,
        background="Real‑time operations; incident management",
        agent_description=(
            "Execution leader who turns plans into ground truth and keeps customers informed."
        ),
        agent_capabilities=[
            "Runs ops room and owner assignment",
            "Maintains dashboards vs reality",
            "Coordinates incident response",
            "Approves deliberate deviations",
        ],
    )

    port_liaison = HumanAgentConfig(
        agent_id="port_liaison",
        agent_type="human_mock",
        system_prompt=(
            "Port & Canal Liaison. Primary contact for Suez Canal Authority convoys and local port agents. Confirms slots, "
            "priorities, pilotage, and tugs; expedites documentation issues; and maintains a shared view of rotation constraints "
            "so schedule changes propagate quickly to intermodal planning."
        ),
        name="Port & Canal Liaison",
        role="External Coordination",
        experience_years=14,
        background="Port agency & canal operations",
        agent_description=(
            "Liaison who secures slots and expedites paperwork across ports and the Canal."
        ),
        agent_capabilities=[
            "Confirms convoys/pilotage/tugs",
            "Expedites documentation issues",
            "Maintains rotation constraints view",
            "Propagates schedule changes",
        ],
    )

    # Optional Stakeholder (kept to stay within 10 total personas)
    coo_stakeholder = StakeholderConfig(
        agent_id="coo_stakeholder",
        agent_type="stakeholder",
        system_prompt=(
            "You are the COO. Early, you prioritize launch speed and reliable slot bookings. Mid‑campaign, you care most about "
            "network stability and customer commitments. During execution, compliance and OTIF become paramount. Keep updates crisp."
        ),
        model_name="o3",
        name="COO Stakeholder",
        role="Executive Stakeholder",
        persona_description="Operations‑first, customer‑sensitive, and risk‑aware; favors measurable OTIF and clear SLAs.",
        agent_description=(
            "COO who demands reliable service, measurable OTIF, and crisp escalation/owner lists."
        ),
        agent_capabilities=[
            "Sets priorities and customer guardrails",
            "Approves buffers and reroute strategies",
            "Holds teams to OTIF targets",
            "Chairs post‑mortems and improvements",
        ],
        response_latency_steps_min=1,
        response_latency_steps_max=3,
        push_probability_per_timestep=0.12,
        suggestion_rate=0.5,
        clarification_reply_rate=0.9,
        strictness=0.6,
        verbosity=2,
        preference_data=PreferenceSnapshot(
            preferences=[
                Preference(name="speed", weight=0.45),
                Preference(name="quality", weight=0.3),
                Preference(name="compliance", weight=0.25),
            ]
        ),
    )

    return {
        # AI
        "forecaster_ai": forecaster_ai,
        "convoy_planner_ai": convoy_planner_ai,
        "trade_compliance_ai": trade_compliance_ai,
        "ops_copilot_ai": ops_copilot_ai,
        # Human
        "head_ops": head_ops,
        "network_planning_mgr": network_planning_mgr,
        "customs_manager": customs_manager,
        "control_tower_lead": control_tower_lead,
        "port_liaison": port_liaison,
        # Stakeholder
        "coo_stakeholder": coo_stakeholder,
    }


# ---------------------------
# TEAM TIMELINE
# ---------------------------
def create_team_timeline():
    """Timestep → [(action, agent_cfg, rationale)] with 'add'/'remove' actions."""
    cfg = create_team_configs()

    return {
        # Strategy & Forecasting
        0: [
            (
                "add",
                cfg["head_ops"],
                "Kick off; set service targets and escalation rules",
            ),
            (
                "add",
                cfg["network_planning_mgr"],
                "Translate goals into capacity planning assumptions",
            ),
            (
                "add",
                cfg["forecaster_ai"],
                "Generate baseline + scenario bands for volumes",
            ),
            (
                "add",
                cfg["coo_stakeholder"],
                "Confirm priorities and customer guardrails",
            ),
        ],
        5: [
            (
                "add",
                cfg["convoy_planner_ai"],
                "Reserve convoy slots and align rotations/ETAs",
            ),
            (
                "add",
                cfg["port_liaison"],
                "Coordinate with SCA and port agents on constraints",
            ),
        ],
        # Compliance & Enablement
        8: [
            (
                "add",
                cfg["customs_manager"],
                "Stand up pre‑arrival filings and DG process",
            ),
            (
                "add",
                cfg["trade_compliance_ai"],
                "Automate HS validation and documentation checks",
            ),
        ],
        12: [
            (
                "remove",
                cfg["forecaster_ai"],
                "Forecast stabilized; hand off to planning",
            ),
        ],
        # Execution & Control
        16: [
            (
                "add",
                cfg["control_tower_lead"],
                "Stand up control tower, dashboards, and comms",
            ),
            ("add", cfg["ops_copilot_ai"], "Exception triage and playbook suggestions"),
        ],
        22: [
            ("remove", cfg["convoy_planner_ai"], "Rotation fixed; ops in steady‑state"),
        ],
        30: [
            (
                "add",
                cfg["coo_stakeholder"],
                "Review OTIF/dwell and sign off on learnings",
            ),
            (
                "remove",
                cfg["trade_compliance_ai"],
                "Documentation flow stable; audits ongoing",
            ),
        ],
    }
