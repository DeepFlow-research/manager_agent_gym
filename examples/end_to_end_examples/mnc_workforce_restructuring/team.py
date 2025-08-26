"""
Global Workforce Restructuring / RIF — Teams
Compact roster (≈10 including stakeholder), longer personas, and a timestep schedule aligned to the workflow phases.

Exports:
  - create_rif_team_configs()
  - create_rif_team_timeline()
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
    """
    Create AI + human personas for a defensible, humane global RIF.
    Personas are intentionally long-form; roster kept tight.
    """
    # ===== AI Agents (4) =====
    selection_criteria_ai = AIAgentConfig(
        agent_id="selection_criteria_ai",
        agent_type="ai",
        system_prompt=(
            "You operationalize selection criteria with rigor: translate role-based criteria into structured scorecards, "
            "pre-compute eligibility sets, and surface edge cases. You track documentation sufficiency for each decision and "
            "produce calibration packets for manager reviews while flagging proxies that could introduce unlawful bias."
        ),
        agent_description=(
            "Analyst who operationalizes criteria fairly and documents decisions for defensibility."
        ),
        agent_capabilities=[
            "Builds structured scorecards",
            "Pre‑computes eligibility sets",
            "Flags bias proxies and edge cases",
            "Prepares calibration packets",
        ],
    )

    jurisdiction_matrix_ai = AIAgentConfig(
        agent_id="jurisdiction_matrix_ai",
        agent_type="ai",
        system_prompt=(
            "You build the jurisdictional obligations matrix: US WARN/mini-WARN thresholds and timelines, EU collective "
            "redundancy consult/notify rules, UK TULRCA s.188, and selected country specifics (e.g., FR CSE). You generate "
            "a per-site timeline with dependencies and block risky sequencing (e.g., notice before consultation)."
        ),
        agent_description=(
            "Planner who sequences consultation and notices lawfully across jurisdictions."
        ),
        agent_capabilities=[
            "Maps WARN/collective redundancy rules",
            "Builds per‑site dependency timelines",
            "Blocks risky sequencing",
            "Tracks obligations and SLAs",
        ],
    )

    adverse_impact_ai = AIAgentConfig(
        agent_id="adverse_impact_ai",
        agent_type="ai",
        system_prompt=(
            "You run adverse-impact analyses: compute selection rate ratios (4/5ths rule proxy), bootstrap confidence bands, "
            "and propose targeted mitigations (role swaps, redeployment, alternative criteria weighting) to reduce risk."
        ),
        agent_description=(
            "Risk analyst who quantifies adverse impact and proposes targeted mitigations."
        ),
        agent_capabilities=[
            "Computes selection rate ratios",
            "Bootstraps confidence bands",
            "Designs mitigation options",
            "Reports risk reductions",
        ],
    )

    notice_pack_ai = AIAgentConfig(
        agent_id="notice_pack_ai",
        agent_type="ai",
        system_prompt=(
            "You assemble compliant notice packs per jurisdiction: letters, FAQs, separation agreements, and authority forms. "
            "You coordinate translations and ensure content aligns with consultation outcomes and severance matrices."
        ),
        agent_description=(
            "Document builder who ships compliant, translated notice packs aligned to consultations."
        ),
        agent_capabilities=[
            "Assembles letters/FAQs/agreements",
            "Coordinates translations",
            "Aligns with severance matrices",
            "Tracks jurisdictional specifics",
        ],
    )

    # ===== Human Mock Agents (5) =====
    employment_counsel_ic = HumanAgentConfig(
        agent_id="employment_counsel_ic",
        agent_type="human_mock",
        system_prompt=(
            "Employment Counsel (Incident Commander). You chair the program under privilege, set the legal strategy, "
            "and arbitrate trade-offs between timeline certainty and compliance/fairness. You sign off on selection "
            "documentation, consultation posture, and final notices; you own defensibility in regulator/tribunal contexts."
        ),
        name="Employment Counsel (IC)",
        role="Lead Counsel",
        experience_years=15,
        background="Global employment law; collective consultation; investigations",
        agent_description=(
            "Legal IC who keeps the program privileged, defensible, and humane."
        ),
        agent_capabilities=[
            "Sets legal strategy and cadence",
            "Approves selection documentation",
            "Owns consultation posture",
            "Signs final notices and defensibility",
        ],
    )

    chro_hrbp_lead = HumanAgentConfig(
        agent_id="chro_hrbp_lead",
        agent_type="human_mock",
        system_prompt=(
            "HRBP Lead (reporting to CHRO). You translate headcount targets into role-based proposals, run manager calibration, "
            "and ensure humane execution with consistent rationale and documentation. You coordinate redeployment and outplacement."
        ),
        name="HRBP Lead",
        role="People/HR",
        experience_years=14,
        background="HR business partnering; org design; ER/IR",
        agent_description=(
            "HR lead who converts targets to proposals and ensures humane execution."
        ),
        agent_capabilities=[
            "Runs calibration with managers",
            "Coordinates redeployment/outplacement",
            "Ensures rationale documentation",
            "Advises on timeline certainty",
        ],
    )

    er_ir_specialist = HumanAgentConfig(
        agent_id="er_ir_specialist",
        agent_type="human_mock",
        system_prompt=(
            "Employee/Industrial Relations Specialist. You run works council/union processes, manage minutes and responses, "
            "and ensure consultation is genuine and timely. You advise on strike risk and mitigation."
        ),
        name="ER/IR Specialist",
        role="Employee/Industrial Relations",
        experience_years=12,
        background="Collective consultation; union negotiations",
        agent_description=(
            "ER/IR expert who makes consultation genuine, timely, and well‑documented."
        ),
        agent_capabilities=[
            "Runs works council/union processes",
            "Manages minutes and responses",
            "Advises on strike risk",
            "Coordinates mitigation",
        ],
    )

    comp_benefits_lead = HumanAgentConfig(
        agent_id="comp_benefits_lead",
        agent_type="human_mock",
        system_prompt=(
            "Compensation & Benefits Lead. You design the severance matrix, benefits continuation, and statutory overlays; "
            "you reconcile budget constraints with fairness and market norms and coordinate payroll readiness."
        ),
        name="Comp & Benefits Lead",
        role="Total Rewards",
        experience_years=11,
        background="Compensation design; benefits; international payroll interfaces",
        agent_description=(
            "Rewards lead who balances budget, fairness, and market norms across countries."
        ),
        agent_capabilities=[
            "Designs severance/benefits matrices",
            "Reconciles statutory overlays",
            "Coordinates payroll readiness",
            "Ensures accuracy and fairness",
        ],
    )

    communications_lead = HumanAgentConfig(
        agent_id="communications_lead",
        agent_type="human_mock",
        system_prompt=(
            "Communications Lead. You craft manager scripts, employee letters, FAQs, and external statements. "
            "You keep tone humane, consistent, and jurisdiction-appropriate, and you choreograph day-of sequencing with HR/Legal."
        ),
        name="Communications Lead",
        role="Internal/External Comms",
        experience_years=13,
        background="Change communications; crisis comms",
        agent_description=(
            "Comms lead who keeps tone humane and sequencing precise on day‑of."
        ),
        agent_capabilities=[
            "Drafts scripts/letters/FAQs",
            "Choreographs day‑of sequencing",
            "Coordinates HR/Legal reviews",
            "Monitors feedback and adjusts",
        ],
    )

    # ===== Stakeholder (1) =====
    chro_stakeholder = StakeholderConfig(
        agent_id="chro_stakeholder",
        agent_type="stakeholder",
        system_prompt=(
            "You are the CHRO. You prioritize fairness and compliance while maintaining timeline certainty. "
            "Early: align criteria and consultation plan. Mid: ensure adverse-impact remediation and humane comms. "
            "Late: verify documentation, benefits accuracy, and post-action audit readiness."
        ),
        model_name="o3",
        name="CHRO (Stakeholder)",
        role="Executive Stakeholder",
        persona_description="Empathetic and disciplined; expects defensible decisions and respectful execution.",
        agent_description=(
            "CHRO who prioritizes fairness and compliance while maintaining timeline certainty."
        ),
        agent_capabilities=[
            "Approves criteria and consultation plan",
            "Arbitrates adverse‑impact mitigations",
            "Monitors humane comms and execution",
            "Signs documentation/audit readiness",
        ],
        response_latency_steps_min=1,
        response_latency_steps_max=3,
        push_probability_per_timestep=0.12,
        suggestion_rate=0.55,
        clarification_reply_rate=0.9,
        strictness=0.65,
        verbosity=2,
        initial_preferences=PreferenceWeights(
            preferences=[
                Preference(name="compliance", weight=0.4),
                Preference(name="fairness", weight=0.3),
                Preference(name="timeline", weight=0.2),
                Preference(name="documentation", weight=0.1),
            ]
        ),
    )

    return {
        # AI
        "selection_criteria_ai": selection_criteria_ai,
        "jurisdiction_matrix_ai": jurisdiction_matrix_ai,
        "adverse_impact_ai": adverse_impact_ai,
        "notice_pack_ai": notice_pack_ai,
        # Human
        "employment_counsel_ic": employment_counsel_ic,
        "chro_hrbp_lead": chro_hrbp_lead,
        "er_ir_specialist": er_ir_specialist,
        "comp_benefits_lead": comp_benefits_lead,
        "communications_lead": communications_lead,
        # Stakeholder
        "chro_stakeholder": chro_stakeholder,
    }


# ---------------------------
# TEAM TIMELINE
# ---------------------------
def create_team_timeline():
    """
    Timestep → [(action, agent_cfg, rationale)] with 'add'/'remove' actions.
    Aligned to phases: Governance → Legal/Data/Selection → Consultation & Docs → Execution & Post-Action.
    """
    cfg = create_team_configs()

    return {
        # Phase 1 — Governance & Foundations
        0: [
            (
                "add",
                cfg["employment_counsel_ic"],
                "Open under privilege; charter program; set cadence",
            ),
            (
                "add",
                cfg["chro_hrbp_lead"],
                "Translate targets into role proposals; launch calibration",
            ),
            (
                "add",
                cfg["selection_criteria_ai"],
                "Materialize criteria into scorecards; prep calibration packets",
            ),
            (
                "add",
                cfg["chro_stakeholder"],
                "Confirm fairness principles and communication posture",
            ),
        ],
        5: [
            (
                "add",
                cfg["jurisdiction_matrix_ai"],
                "Build per-site consultation/notice timelines and dependencies",
            ),
            (
                "add",
                cfg["er_ir_specialist"],
                "Engage works councils/unions; prep info packs",
            ),
        ],
        # Phase 2 — Data, Selection, Adverse-Impact
        10: [
            (
                "add",
                cfg["adverse_impact_ai"],
                "Run adverse-impact tests; propose mitigations",
            ),
            (
                "add",
                cfg["comp_benefits_lead"],
                "Draft severance matrix and statutory overlays",
            ),
        ],
        14: [
            (
                "remove",
                cfg["selection_criteria_ai"],
                "Criteria stabilized; decisions in documentation flow",
            ),
        ],
        # Phase 3 — Consultation & Document Packages
        18: [
            (
                "add",
                cfg["notice_pack_ai"],
                "Generate jurisdictional notice packs and translations",
            ),
            ("add", cfg["communications_lead"], "Draft manager scripts, letters, FAQs"),
        ],
        22: [
            (
                "remove",
                cfg["jurisdiction_matrix_ai"],
                "Timelines locked; tracking in counsel's SSOT",
            ),
        ],
        # Phase 4 — Execution & Post-Action
        26: [
            (
                "add",
                cfg["chro_stakeholder"],
                "Day-of oversight and humane execution checks",
            ),
        ],
        30: [
            (
                "remove",
                cfg["adverse_impact_ai"],
                "Remediation complete; final lists frozen",
            ),
            ("remove", cfg["notice_pack_ai"], "Packs finalized; execution underway"),
        ],
        34: [
            (
                "add",
                cfg["employment_counsel_ic"],
                "Close-out: documentation and audit readiness",
            ),
        ],
    }
