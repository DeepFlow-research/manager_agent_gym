"""
ICAAP (Internal Capital Adequacy Assessment Process) Demo

Real-world use case: Mid-size EU retail bank annual ICAAP cycle.

Demonstrates:
- Hierarchical task decomposition for ICAAP phases
- Preference dynamics emphasizing compliance near submission
- Ad hoc team coordination with human sign-offs
- Governance-by-design validation rules (LLM-based rubrics)
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


def create_team_configs():
    """Create AI and human mock agent configurations for ICAAP."""

    credit_modeler = AIAgentConfig(
        agent_id="credit_risk_modeler",
        agent_type="ai",
        system_prompt=(
            "You are a Credit Risk Modeler focusing on PD/LGD/EAD estimation, concentration risk, "
            "and economic capital computation with sensitivity analysis."
        ),
        agent_description=(
            "Quant who produces defensible credit capital estimates with clear assumptions and sensitivity."
        ),
        agent_capabilities=[
            "Builds PD/LGD/EAD estimates",
            "Analyzes concentration risk",
            "Computes economic capital",
            "Documents sensitivity and overlays",
        ],
    )
    irrbb_analyst = AIAgentConfig(
        agent_id="irrbb_analyst",
        agent_type="ai",
        system_prompt=(
            "You are an IRRBB Analyst specializing in EVE/NII measurement, behavioral assumptions, "
            "and policy limit checks under standard shocks."
        ),
        agent_description=(
            "ALM analyst who quantifies EVE/NII risk under sound behavioral assumptions."
        ),
        agent_capabilities=[
            "Measures EVE/NII sensitivities",
            "Calibrates behavioral assumptions",
            "Checks policy limit compliance",
            "Prepares IRRBB reports",
        ],
    )
    op_risk_analyst = AIAgentConfig(
        agent_id="op_risk_analyst",
        agent_type="ai",
        system_prompt=(
            "You are an Operational Risk Analyst conducting scenario assessments with loss data and "
            "model risk overlays."
        ),
        agent_description=(
            "Operational risk analyst who combines data and scenarios into credible loss estimates."
        ),
        agent_capabilities=[
            "Analyzes loss data",
            "Runs scenario assessments",
            "Applies model risk overlays",
            "Drafts ORSA/ICAAP write‑ups",
        ],
    )
    stress_designer = AIAgentConfig(
        agent_id="stress_testing_designer",
        agent_type="ai",
        system_prompt=(
            "You design institution-wide stress scenarios (baseline/adverse/severe) and reverse stress tests, "
            "ensuring severity and plausibility with clear attribution."
        ),
        agent_description=(
            "Designer who drafts plausible yet severe scenarios with clear attribution logic."
        ),
        agent_capabilities=[
            "Builds baseline/adverse/severe paths",
            "Designs reverse stress tests",
            "Documents variable books",
            "Preps governance review decks",
        ],
    )
    capital_planner = AIAgentConfig(
        agent_id="capital_planner",
        agent_type="ai",
        system_prompt=(
            "You are a Capital Planning Analyst projecting earnings, RWAs, and CET1 vs OCR+CBR with P2R/P2G and MDA checks."
        ),
        agent_description=(
            "Planner who projects capital trajectory vs OCR+buffers and turns results into actions."
        ),
        agent_capabilities=[
            "Projects earnings/RWAs/CET1",
            "Assesses OCR+CBR and P2R/P2G",
            "Runs MDA checks",
            "Drafts management actions",
        ],
    )
    documentation_lead = AIAgentConfig(
        agent_id="documentation_lead",
        agent_type="ai",
        system_prompt=(
            "You assemble ICAAP documentation including CAS, risk coverage, stress results, and management actions with traceability."
        ),
        agent_description=(
            "Editor who assembles a clear, traceable ICAAP pack with evidence links."
        ),
        agent_capabilities=[
            "Compiles CAS/risk coverage",
            "Links evidence and version control",
            "Tracks approvals",
            "Ensures submission readiness",
        ],
    )

    # Human sign-offs
    model_validation = HumanAgentConfig(
        agent_id="model_validation_lead",
        agent_type="human_mock",
        system_prompt="Independent model validation lead providing methodology/data validation sign-off.",
        name="Model Validation Lead",
        role="Independent Validation",
        experience_years=10,
        background="Quantitative risk validation",
        agent_description=(
            "Independent challenger who tests methods, data, and outcomes with rigor."
        ),
        agent_capabilities=[
            "Reviews methodology/data",
            "Runs outcomes analysis",
            "Designs monitoring",
            "Documents effective challenge",
        ],
    )
    compliance_officer = HumanAgentConfig(
        agent_id="regulatory_compliance_officer",
        agent_type="human_mock",
        system_prompt="Regulatory compliance officer ensuring CRD/CRR and SREP alignment.",
        name="Compliance Officer",
        role="Regulatory Compliance",
        experience_years=8,
        background="Bank regulation",
        agent_description=(
            "Compliance lead who checks CRD/CRR alignment and SREP expectations."
        ),
        agent_capabilities=[
            "Maps rules to controls",
            "Reviews alignment and gaps",
            "Advises on remediation",
            "Tracks regulator interactions",
        ],
    )
    internal_audit = HumanAgentConfig(
        agent_id="internal_audit_reviewer",
        agent_type="human_mock",
        system_prompt="Internal audit reviewer checking process controls and documentation completeness.",
        name="Internal Audit Reviewer",
        role="Internal Audit",
        experience_years=12,
        background="Audit and controls",
        agent_description=(
            "Assurance function validating process control and documentation trail."
        ),
        agent_capabilities=[
            "Performs process/control audits",
            "Tests documentation completeness",
            "Issues findings/follow‑ups",
            "Confirms remediation effectiveness",
        ],
    )
    board_committee = HumanAgentConfig(
        agent_id="board_committee",
        agent_type="human_mock",
        system_prompt="Board/committee responsible for risk appetite, limits, and ICAAP approval.",
        name="Board Committee",
        role="Board Approval",
        experience_years=15,
        background="Board governance",
        agent_description=(
            "Committee that provides challenge and approves the package prior to submission."
        ),
        agent_capabilities=[
            "Challenges assumptions and results",
            "Balances risk appetite and buffers",
            "Approves final decisions",
            "Holds management accountable",
        ],
    )

    # Stakeholder (bank CFO) for priority tradeoffs and approvals
    stakeholder = StakeholderConfig(
        agent_id="bank_cfo",
        agent_type="stakeholder",
        system_prompt=(
            "You are the bank CFO balancing regulatory compliance, delivery speed, and resource cost."
        ),
        model_name="o3",
        name="Bank CFO",
        role="Executive Stakeholder",
        persona_description="Pragmatic, compliance-focused, values timely delivery with adequate quality.",
        agent_description=(
            "CFO who sets priorities, arbitrates trade‑offs, and signs off on ICAAP quality and timing."
        ),
        agent_capabilities=[
            "Sets compliance/time/cost priorities",
            "Approves buffer policy and actions",
            "Chairs decision forums",
            "Owns final submission call",
        ],
        response_latency_steps_min=1,
        response_latency_steps_max=3,
        push_probability_per_timestep=0.1,
        suggestion_rate=0.5,
        clarification_reply_rate=0.9,
        strictness=0.6,
        verbosity=2,
        initial_preferences=PreferenceWeights(
            preferences=[
                Preference(name="quality", weight=0.4),
                Preference(name="time", weight=0.35),
                Preference(name="cost", weight=0.25),
            ]
        ),
    )

    return {
        "credit_modeler": credit_modeler,
        "irrbb_analyst": irrbb_analyst,
        "op_risk_analyst": op_risk_analyst,
        "stress_designer": stress_designer,
        "capital_planner": capital_planner,
        "documentation_lead": documentation_lead,
        "model_validation": model_validation,
        "compliance_officer": compliance_officer,
        "internal_audit": internal_audit,
        "board_committee": board_committee,
        "stakeholder": stakeholder,
    }


def create_team_timeline():
    """Create ad hoc coordination timeline for ICAAP."""

    cfg = create_team_configs()
    return {
        0: [
            ("add", cfg["credit_modeler"], "Credit risk economic capital"),
            ("add", cfg["irrbb_analyst"], "IRRBB EVE/NII"),
            ("add", cfg["op_risk_analyst"], "Operational risk scenarios"),
            ("add", cfg["documentation_lead"], "Documentation assembly"),
        ],
        15: [
            ("add", cfg["stress_designer"], "Scenario design"),
        ],
        40: [
            ("add", cfg["capital_planner"], "Normative projections and buffers"),
        ],
        70: [
            ("add", cfg["model_validation"], "Independent validation"),
            ("add", cfg["compliance_officer"], "Regulatory review"),
        ],
        85: [
            ("add", cfg["internal_audit"], "Internal audit review"),
            ("add", cfg["board_committee"], "Final approval"),
        ],
    }
