"""
US Co‑op Bank — Internal Risk & Solvency Assessment (ORSA‑style) Team
Personas (AI + human) and a timestep-based schedule aligned to the workflow phases.

Mirrors existing example patterns:
  - Uses AIAgentConfig / HumanAgentConfig / StakeholderConfig
  - Timeline: Dict[int, List[Tuple[action, agent_cfg, rationale]]]
  - Optional stakeholder with initial PreferenceWeights (kept to speed/quality/compliance for schema parity)
"""

from manager_agent_gym.schemas.workflow_agents import (
    AIAgentConfig,
    HumanAgentConfig,
    StakeholderConfig,
)
from manager_agent_gym.schemas.preferences.preference import (
    PreferenceWeights,
    Preference,
)


# ---------------------------
# TEAM CONFIGS
# ---------------------------
def create_team_configs():
    """Create AI and human mock agent configurations for the ORSA-style assessment."""

    # ===== AI Agents =====
    project_coordinator_ai = AIAgentConfig(
        agent_id="project_coordinator_ai",
        agent_type="ai",
        system_prompt=(
            "You coordinate the assessment calendar, RAID log (risks/assumptions/issues/decisions), and dependencies; "
            "maintain documentation index and version control across artifacts."
        ),
        agent_description=(
            "Coordinator who keeps the calendar, RAID, and dependencies tight with version‑controlled artifacts."
        ),
        agent_capabilities=[
            "Maintains assessment calendar and RAID",
            "Tracks dependencies and owners",
            "Manages documentation index/versioning",
            "Publishes status and blocker lists",
        ],
    )

    model_inventory_ai = AIAgentConfig(
        agent_id="model_inventory_ai",
        agent_type="ai",
        system_prompt=(
            "You compile and normalize the model inventory per SR 11‑7, map inputs/outputs, controls, and monitoring; "
            "generate validation/challenger plan candidates."
        ),
        agent_description=(
            "Inventory builder who normalizes SR 11‑7 model data and drafts validation plans."
        ),
        agent_capabilities=[
            "Compiles model inventory",
            "Maps inputs/outputs/controls",
            "Drafts validation/challenger plans",
            "Prepares governance‑ready summaries",
        ],
    )

    scenario_designer_ai = AIAgentConfig(
        agent_id="scenario_designer_ai",
        agent_type="ai",
        system_prompt=(
            "You draft baseline/adverse/severe macro paths, idiosyncratic shocks, and climate overlays; "
            "produce variable books and documentation suitable for governance review."
        ),
        agent_description=(
            "Designer who crafts plausible yet severe scenarios, including climate overlays, with clear documentation."
        ),
        agent_capabilities=[
            "Drafts macro paths and shocks",
            "Builds climate/idiosyncratic overlays",
            "Prepares variable books",
            "Aligns with governance reviewers",
        ],
    )

    credit_modeler_ai = AIAgentConfig(
        agent_id="credit_modeler_ai",
        agent_type="ai",
        system_prompt=(
            "You assist with credit loss projections (PD/LGD/EAD or proxy), overlays, and sensitivity analysis; "
            "prepare challenger comparisons and backtests."
        ),
        agent_description=(
            "Credit modeler who projects losses with overlay logic and backtests for credibility."
        ),
        agent_capabilities=[
            "Builds PD/LGD/EAD projections",
            "Designs overlays and sensitivities",
            "Prepares challenger comparisons",
            "Runs backtests and attribution",
        ],
    )

    irrbb_modeler_ai = AIAgentConfig(
        agent_id="irrbb_modeler_ai",
        agent_type="ai",
        system_prompt=(
            "You support ALM/IRRBB modeling for NII and EVE sensitivities under rate shocks/ramps; "
            "produce laddered reports and attribution notes."
        ),
        agent_description=(
            "ALM modeler who quantifies NII/EVE and explains movements under shocks/ramps."
        ),
        agent_capabilities=[
            "Computes NII/EVE sensitivities",
            "Builds laddered reports",
            "Performs attribution analysis",
            "Checks behavioral assumptions",
        ],
    )

    liquidity_stress_ai = AIAgentConfig(
        agent_id="liquidity_stress_ai",
        agent_type="ai",
        system_prompt=(
            "You generate liquidity stress profiles and contingency funding plan triggers; "
            "produce survival horizon analysis and funding playbooks."
        ),
        agent_description=(
            "Liquidity modeler who derives survival horizons and actionable CFP triggers."
        ),
        agent_capabilities=[
            "Builds liquidity stress profiles",
            "Drafts contingency funding triggers",
            "Computes survival horizons",
            "Publishes funding playbooks",
        ],
    )

    operational_risk_ai = AIAgentConfig(
        agent_id="operational_risk_ai",
        agent_type="ai",
        system_prompt=(
            "You summarize operational risk exposures, loss data, and scenario add‑ons; "
            "link control gaps to remediation tasks and capital add‑ons."
        ),
        agent_description=(
            "Operational risk analyst who links loss data to control gaps and capital add‑ons."
        ),
        agent_capabilities=[
            "Summarizes OR exposures and loss data",
            "Builds scenario add‑ons",
            "Links control gaps to remediation",
            "Quantifies capital impacts",
        ],
    )

    validator_ai = AIAgentConfig(
        agent_id="validator_ai",
        agent_type="ai",
        system_prompt=(
            "You assist model validation with conceptual soundness checks, outcomes analysis, and ongoing monitoring design; "
            "capture evidence of 'effective challenge'."
        ),
        agent_description=(
            "Validation assistant who evidences conceptual soundness and outcomes analysis, and designs monitoring."
        ),
        agent_capabilities=[
            "Runs conceptual soundness checks",
            "Performs outcomes analysis",
            "Designs ongoing monitoring",
            "Captures effective challenge evidence",
        ],
    )

    documentation_ai = AIAgentConfig(
        agent_id="documentation_ai",
        agent_type="ai",
        system_prompt=(
            "You compile the Internal Risk & Solvency Assessment report with citations to evidence; "
            "ensure reproducibility and audit trail completeness."
        ),
        agent_description=(
            "Editor who compiles a traceable report with evidence links and reproducibility."
        ),
        agent_capabilities=[
            "Assembles report with citations",
            "Ensures reproducibility",
            "Maintains audit trail completeness",
            "Coordinates approvals",
        ],
    )

    dashboard_ai = AIAgentConfig(
        agent_id="dashboard_ai",
        agent_type="ai",
        system_prompt=(
            "You build executive dashboards and board packs: key findings, capital decisions, and remediation trackers."
        ),
        agent_description=(
            "Communicator who builds executive dashboards and board packs with decisions front‑and‑center."
        ),
        agent_capabilities=[
            "Builds executive dashboards",
            "Prepares board materials",
            "Summarizes key findings and decisions",
            "Tracks remediation owners and ETAs",
        ],
    )

    # ===== Human Mock Agents =====
    cro = HumanAgentConfig(
        agent_id="cro",
        agent_type="human_mock",
        system_prompt=(
            "Chief Risk Officer: owns risk framework, scenario selection, and board engagement."
        ),
        name="Chief Risk Officer",
        role="Risk Leadership",
        experience_years=18,
        background="Enterprise risk; capital planning",
        agent_description=(
            "Risk chief who sets posture, selects scenarios, and engages the board."
        ),
        agent_capabilities=[
            "Owns risk framework and appetite",
            "Approves scenario selection",
            "Engages board and executives",
            "Signs final decisions",
        ],
    )

    cfo = HumanAgentConfig(
        agent_id="cfo",
        agent_type="human_mock",
        system_prompt=(
            "Chief Financial Officer: aligns assessment with budget/plan; approves buffer policy."
        ),
        name="Chief Financial Officer",
        role="Finance Leadership",
        experience_years=17,
        background="Finance; liquidity/ALM oversight",
        agent_description=(
            "Finance chief who aligns assessment with plan/budget and buffer policy."
        ),
        agent_capabilities=[
            "Aligns with budget/plan",
            "Approves buffer policy",
            "Chairs finance reviews",
            "Owns financial disclosures",
        ],
    )

    treasurer = HumanAgentConfig(
        agent_id="treasurer",
        agent_type="human_mock",
        system_prompt=(
            "Owns ALM/IRRBB modeling, funding strategy, and liquidity governance."
        ),
        name="Treasurer",
        role="Treasury/ALM",
        experience_years=14,
        background="ALM/IRRBB; liquidity risk",
        agent_description=(
            "ALM owner for IRRBB and liquidity who links models to funding strategy."
        ),
        agent_capabilities=[
            "Owns ALM/IRRBB modeling",
            "Coordinates funding strategy",
            "Confirms ownership and data feeds",
            "Presents treasury actions",
        ],
    )

    head_credit_risk = HumanAgentConfig(
        agent_id="head_credit_risk",
        agent_type="human_mock",
        system_prompt=(
            "Owns credit risk models/overlays; portfolio segmentation and loss projections."
        ),
        name="Head of Credit Risk",
        role="Credit Risk",
        experience_years=15,
        background="Retail/Commercial credit risk",
        agent_description=(
            "Credit risk owner who validates portfolio segmentation, models, and overlays."
        ),
        agent_capabilities=[
            "Oversees credit models/overlays",
            "Leads segmentation and loss drivers",
            "Approves assumptions",
            "Presents results to governance",
        ],
    )

    liquidity_risk_manager = HumanAgentConfig(
        agent_id="liquidity_risk_manager",
        agent_type="human_mock",
        system_prompt=(
            "Runs liquidity stress testing and contingency funding plans; coordinates with Treasurer."
        ),
        name="Liquidity Risk Manager",
        role="Liquidity Risk",
        experience_years=10,
        background="Liquidity stress testing & funding",
        agent_description=(
            "Liquidity risk owner who runs stress testing and CFPs in lockstep with Treasury."
        ),
        agent_capabilities=[
            "Runs liquidity stress tests",
            "Maintains CFP triggers",
            "Coordinates with Treasurer",
            "Reports survival horizons",
        ],
    )

    orm_lead = HumanAgentConfig(
        agent_id="operational_risk_lead",
        agent_type="human_mock",
        system_prompt=(
            "Owns operational risk taxonomy, loss data, KRIs, and scenario add‑ons; third‑party and fraud posture."
        ),
        name="Operational Risk Lead",
        role="Operational Risk",
        experience_years=11,
        background="Operational risk & controls",
        agent_description=(
            "Operational risk lead who keeps taxonomy, KRIs, and scenario posture current."
        ),
        agent_capabilities=[
            "Owns OR taxonomy and KRIs",
            "Manages loss data and scenarios",
            "Coordinates third‑party/fraud posture",
            "Presents OR add‑ons",
        ],
    )

    mrm_lead = HumanAgentConfig(
        agent_id="model_risk_lead",
        agent_type="human_mock",
        system_prompt=(
            "Model Risk Manager: SR 11‑7 inventory/validation; ensures effective challenge"
        ),
        name="Model Risk/Validation Lead",
        role="Model Risk",
        experience_years=12,
        background="Model validation & governance",
        agent_description=(
            "Model risk lead who ensures inventory, validation, and effective challenge."
        ),
        agent_capabilities=[
            "Owns SR 11‑7 inventory",
            "Plans validations/challengers",
            "Documents effective challenge",
            "Sets monitoring requirements",
        ],
    )

    internal_audit = HumanAgentConfig(
        agent_id="internal_audit",
        agent_type="human_mock",
        system_prompt=(
            "Provides independent assurance on governance, controls, and documentation/audit trail."
        ),
        name="Internal Audit",
        role="Assurance",
        experience_years=16,
        background="Internal audit; financial services",
        agent_description=(
            "Assurance function that validates governance, controls, and audit trail."
        ),
        agent_capabilities=[
            "Audits process and controls",
            "Checks documentation and evidence",
            "Issues findings and follow‑ups",
            "Confirms remediation",
        ],
    )

    board_risk_committee = HumanAgentConfig(
        agent_id="board_risk_committee",
        agent_type="human_mock",
        system_prompt=(
            "Board Risk Committee: reviews, challenges, and approves the assessment."
        ),
        name="Board Risk Committee",
        role="Board Oversight",
        experience_years=20,
        background="Board governance",
        agent_description=(
            "Board committee that challenges, approves, and documents oversight."
        ),
        agent_capabilities=[
            "Challenges methods and results",
            "Approves buffer and action choices",
            "Signs governance approvals",
            "Tracks management actions",
        ],
    )

    regulatory_liaison = HumanAgentConfig(
        agent_id="regulatory_liaison",
        agent_type="human_mock",
        system_prompt=(
            "Coordinates with supervisors; ensures the package is exam‑ready and timely."
        ),
        name="Regulatory Liaison",
        role="Regulatory Affairs",
        experience_years=13,
        background="Regulatory relations",
        agent_description=(
            "Liaison to supervisors who ensures exam‑ready packaging and timely communications."
        ),
        agent_capabilities=[
            "Coordinates with supervisors",
            "Preps exam‑ready packages",
            "Manages communications",
            "Tracks commitments and responses",
        ],
    )

    data_gov_lead = HumanAgentConfig(
        agent_id="data_governance_lead",
        agent_type="human_mock",
        system_prompt=(
            "Owns data lineage, quality controls, and change management for risk data."
        ),
        name="Data Governance Lead",
        role="Data Governance",
        experience_years=10,
        background="Data management & controls",
        agent_description=(
            "Data governance owner who keeps lineage, quality, and change control tight."
        ),
        agent_capabilities=[
            "Owns data lineage and QC",
            "Runs change management",
            "Ensures risk data governance",
            "Preps data audit evidence",
        ],
    )

    # Optional stakeholder (CRO) with initial preferences for parity with examples
    stakeholder = StakeholderConfig(
        agent_id="cro_stakeholder",
        agent_type="stakeholder",
        system_prompt=(
            "You are the CRO. Early: prioritize speed to stand up governance/data foundations; "
            "mid: emphasize quality of quantification and governance; late: emphasize compliance/auditability for Board sign‑off."
        ),
        model_name="o3",
        name="CRO Stakeholder",
        role="Executive Stakeholder",
        persona_description="Rigorous, governance‑minded, documentation‑first; expects reproducibility and challenge evidence.",
        agent_description=(
            "CRO stakeholder who sets posture early, then emphasizes quality and auditability before approval."
        ),
        agent_capabilities=[
            "Sets priorities across phases",
            "Approves scenario and validation scope",
            "Demands reproducible evidence",
            "Grants final approvals",
        ],
        response_latency_steps_min=1,
        response_latency_steps_max=3,
        push_probability_per_timestep=0.1,
        suggestion_rate=0.5,
        clarification_reply_rate=0.9,
        strictness=0.7,
        verbosity=2,
        initial_preferences=PreferenceWeights(
            preferences=[
                Preference(name="speed", weight=0.45),
                Preference(name="quality", weight=0.35),
                Preference(name="compliance", weight=0.20),
            ]
        ),
    )

    return {
        # AI
        "project_coordinator_ai": project_coordinator_ai,
        "model_inventory_ai": model_inventory_ai,
        "scenario_designer_ai": scenario_designer_ai,
        "credit_modeler_ai": credit_modeler_ai,
        "irrbb_modeler_ai": irrbb_modeler_ai,
        "liquidity_stress_ai": liquidity_stress_ai,
        "operational_risk_ai": operational_risk_ai,
        "validator_ai": validator_ai,
        "documentation_ai": documentation_ai,
        "dashboard_ai": dashboard_ai,
        # Human
        "cro": cro,
        "cfo": cfo,
        "treasurer": treasurer,
        "head_credit_risk": head_credit_risk,
        "liquidity_risk_manager": liquidity_risk_manager,
        "operational_risk_lead": orm_lead,
        "model_risk_lead": mrm_lead,
        "internal_audit": internal_audit,
        "board_risk_committee": board_risk_committee,
        "regulatory_liaison": regulatory_liaison,
        "data_governance_lead": data_gov_lead,
        # Stakeholder
        "stakeholder": stakeholder,
    }


# ---------------------------
# TEAM TIMELINE
# ---------------------------
def create_team_timeline():
    """Timestep → [(action, agent_cfg, rationale)] with 'add'/'remove' actions."""
    cfg = create_team_configs()

    return {
        # Phase 1: Governance & foundations
        0: [
            ("add", cfg["cro"], "Launch assessment; approve scope and proportionality"),
            (
                "add",
                cfg["project_coordinator_ai"],
                "Stand up calendar, RAID, and evidence index",
            ),
            (
                "add",
                cfg["data_governance_lead"],
                "Establish data lineage and QC policy",
            ),
            ("add", cfg["cfo"], "Align with budget/plan and board calendar"),
        ],
        5: [
            (
                "add",
                cfg["model_inventory_ai"],
                "Compile SR 11‑7 model inventory and plan validations",
            ),
            ("add", cfg["model_risk_lead"], "Define validation and challenger scope"),
            (
                "add",
                cfg["treasurer"],
                "Confirm ALM/IRRBB model ownership and data feeds",
            ),
        ],
        # Phase 2: Risk ID & scenario design
        10: [
            ("add", cfg["head_credit_risk"], "Portfolio segmentation and loss-drivers"),
            ("add", cfg["operational_risk_lead"], "Operational risk taxonomy and KRIs"),
        ],
        14: [
            (
                "add",
                cfg["scenario_designer_ai"],
                "Draft macro paths and idiosyncratic/climate overlays",
            ),
            (
                "add",
                cfg["regulatory_liaison"],
                "Sanity-check scenario plausibility for supervisors",
            ),
        ],
        # Phase 3: Quantification
        20: [
            ("add", cfg["credit_modeler_ai"], "Project credit losses and overlays"),
            ("add", cfg["irrbb_modeler_ai"], "NII/EVE sensitivity and attribution"),
            ("add", cfg["liquidity_stress_ai"], "Liquidity survival horizon and CFP"),
        ],
        26: [
            ("add", cfg["dashboard_ai"], "Build executive views for interim results"),
        ],
        30: [
            (
                "add",
                cfg["validator_ai"],
                "Run validation/challenger testing and monitoring design",
            ),
            (
                "remove",
                cfg["model_inventory_ai"],
                "Inventory stabilized; handoff to validation",
            ),
        ],
        35: [
            ("add", cfg["cfo"], "Review capital buffer options vs RBC/CCULR"),
            ("add", cfg["cro"], "Set management buffer; finalize decisions"),
        ],
        # Phase 4: Controls, documentation, governance
        40: [
            ("add", cfg["documentation_ai"], "Compile report with evidence links"),
            (
                "add",
                cfg["internal_audit"],
                "Independent assurance on controls and audit trail",
            ),
        ],
        45: [
            ("add", cfg["board_risk_committee"], "Board challenge and approval"),
            (
                "remove",
                cfg["scenario_designer_ai"],
                "Scenario set finalized; quant complete",
            ),
        ],
        50: [
            (
                "add",
                cfg["regulatory_liaison"],
                "Package for exam; coordinate communications",
            ),
            (
                "remove",
                cfg["validator_ai"],
                "Validation complete; monitoring plan handed off",
            ),
        ],
    }
