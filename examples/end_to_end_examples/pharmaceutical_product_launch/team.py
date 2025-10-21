"""
Pharmaceutical Product Launch Demo

Real-world use case: Global pharmaceutical company launching new drug product.

Demonstrates:
- Sequential dependency management across 9 interconnected regulatory and manufacturing phases
- Safety-critical decision prioritization when regulatory compliance conflicts with commercial timelines
- Multi-stakeholder coordination across highly specialized domains (regulatory, quality, manufacturing, commercial)
- Long-horizon strategic planning with 10+ week critical path and complex approval gates
- Risk escalation and mitigation when patient safety signals or manufacturing deficiencies emerge
- Resource reallocation under strict regulatory constraints and budget pressures
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


def create_team_configs():
    """Create AI and human mock agent configurations for pharmaceutical product launch."""

    regulatory_affairs_lead = AIAgentConfig(
        agent_id="regulatory_affairs_lead",
        agent_type="ai",
        system_prompt=(
            "You are a Regulatory Affairs Lead focusing on eCTD dossier preparation, FDA/EMA submissions, "
            "and ICH guideline compliance for pharmaceutical product registration."
        ),
        agent_description=(
            "Regulatory lead who charts a submission path and turns complex ICH/FDA/EMA rules into clear, auditable work."
        ),
        agent_capabilities=[
            "Builds eCTD dossier structure and plans",
            "Coordinates FDA/EMA interactions",
            "Maps ICH requirements to evidence",
            "Tracks questions, findings, and responses",
        ],
    )
    manufacturing_scientist = AIAgentConfig(
        agent_id="manufacturing_scientist",
        agent_type="ai",
        system_prompt=(
            "You are a Manufacturing Scientist specializing in cGMP compliance, process validation, "
            "equipment qualification (IQ/OQ/PQ), and manufacturing scale-up for commercial production."
        ),
        agent_description=(
            "Process scientist who scales reliably from lab to plant and proves cGMP compliance."
        ),
        agent_capabilities=[
            "Designs process validation (IQ/OQ/PQ)",
            "Implements cGMP manufacturing controls",
            "Plans scale‑up and tech transfer",
            "Documents deviations and CAPA",
        ],
    )
    quality_assurance_manager = AIAgentConfig(
        agent_id="quality_assurance_manager",
        agent_type="ai",
        system_prompt=(
            "You are a Quality Assurance Manager implementing Quality by Design (QbD), critical quality attributes (CQAs), "
            "control strategies, and analytical method validation per ICH guidelines."
        ),
        agent_description=(
            "QA leader who locks in QbD, CQAs, and control strategies that stand up to inspection."
        ),
        agent_capabilities=[
            "Defines CQAs and control strategies",
            "Validates analytical methods",
            "Runs change control and batch review",
            "Prepares inspection‑ready records",
        ],
    )
    pharmacovigilance_specialist = AIAgentConfig(
        agent_id="pharmacovigilance_specialist",
        agent_type="ai",
        system_prompt=(
            "You design pharmacovigilance systems with risk management plans, adverse event reporting, "
            "signal detection protocols, and post-market safety surveillance for patient protection."
        ),
        agent_description=(
            "PV specialist who designs systems that spot safety signals early and respond responsibly."
        ),
        agent_capabilities=[
            "Builds RMP and case processing flows",
            "Implements signal detection protocols",
            "Coordinates adverse‑event reporting",
            "Publishes safety summaries",
        ],
    )
    market_access_strategist = AIAgentConfig(
        agent_id="market_access_strategist",
        agent_type="ai",
        system_prompt=(
            "You are a Market Access Strategist developing HTA submissions, payer value dossiers, "
            "pricing strategies, and early access programs for successful commercial launch."
        ),
        agent_description=(
            "Value storyteller who turns evidence into payer acceptance and ethical access pathways."
        ),
        agent_capabilities=[
            "Develops HTA submissions and value dossiers",
            "Designs pricing/reimbursement strategy",
            "Coordinates early access programs",
            "Aligns with medical and commercial",
        ],
    )
    supply_chain_coordinator = AIAgentConfig(
        agent_id="supply_chain_coordinator",
        agent_type="ai",
        system_prompt=(
            "You coordinate pharmaceutical supply chain operations including serialization, cold-chain validation, "
            "distribution partner qualification, and global logistics for product launch."
        ),
        agent_description=(
            "Coordinator who keeps serialization, cold‑chain, and partners synchronized for launch."
        ),
        agent_capabilities=[
            "Implements serialization and traceability",
            "Validates cold‑chain and logistics",
            "Qualifies distribution partners",
            "Runs global launch logistics",
        ],
    )
    clinical_data_manager = AIAgentConfig(
        agent_id="clinical_data_manager",
        agent_type="ai",
        system_prompt=(
            "You manage clinical data compilation for regulatory submissions including integrated safety/efficacy summaries, "
            "clinical study reports, and benefit-risk assessments for Module 5 of eCTD dossiers."
        ),
        agent_description=(
            "Data manager who assembles clean, consistent clinical evidence suitable for Module 5."
        ),
        agent_capabilities=[
            "Compiles CSRs and ISS/ISE",
            "Ensures traceability and standards",
            "Resolves data queries and discrepancies",
            "Produces benefit‑risk summaries",
        ],
    )
    commercial_launch_manager = AIAgentConfig(
        agent_id="commercial_launch_manager",
        agent_type="ai",
        system_prompt=(
            "You coordinate commercial launch activities including sales team training, inventory staging, "
            "launch readiness reviews, and stakeholder engagement for successful market entry."
        ),
        agent_description=(
            "Launch orchestrator who aligns training, inventory, and engagement to hit day‑1 readiness."
        ),
        agent_capabilities=[
            "Runs launch readiness reviews",
            "Coordinates sales/medical training",
            "Plans inventory and distribution",
            "Manages stakeholder engagement",
        ],
    )

    # Human sign-offs and specialized regulatory roles
    fda_regulatory_consultant = HumanAgentConfig(
        agent_id="fda_regulatory_consultant",
        agent_type="human_mock",
        system_prompt="FDA regulatory consultant providing specialized guidance on US regulatory requirements and submission strategy.",
        name="FDA Regulatory Consultant",
        role="FDA Regulatory Expert",
        experience_years=18,
        background="FDA guidance and pharmaceutical regulation",
        agent_description=(
            "US regulatory advisor who anticipates questions and sharpens submission quality."
        ),
        agent_capabilities=[
            "Advises on FDA pathways and guidance",
            "Preps meetings and briefing books",
            "Reviews responses and commitments",
            "Coaches for inspection readiness",
        ],
    )
    ema_regulatory_consultant = HumanAgentConfig(
        agent_id="ema_regulatory_consultant",
        agent_type="human_mock",
        system_prompt="EMA regulatory consultant ensuring European regulatory compliance and CHMP submission readiness.",
        name="EMA Regulatory Consultant",
        role="EMA Regulatory Expert",
        experience_years=16,
        background="European regulatory affairs and EMA procedures",
        agent_description=(
            "EU regulatory advisor who aligns CHMP expectations and shepherds submissions."
        ),
        agent_capabilities=[
            "Guides EU procedures and timelines",
            "Reviews Module 1/overview materials",
            "Coordinates Q&A and day‑80/120 responses",
            "Aligns with national authorities",
        ],
    )
    quality_control_director = HumanAgentConfig(
        agent_id="quality_control_director",
        agent_type="human_mock",
        system_prompt="Quality Control Director overseeing analytical testing, release testing, and quality system compliance.",
        name="Quality Control Director",
        role="Quality Control",
        experience_years=20,
        background="Pharmaceutical quality control and cGMP",
        agent_description=(
            "QC leader who ensures methods, release, and quality systems are inspection‑ready."
        ),
        agent_capabilities=[
            "Oversees analytical/release testing",
            "Maintains QC systems and data integrity",
            "Leads investigations and CAPA",
            "Prepares for regulatory inspections",
        ],
    )
    manufacturing_operations_head = HumanAgentConfig(
        agent_id="manufacturing_operations_head",
        agent_type="human_mock",
        system_prompt="Manufacturing Operations Head responsible for production readiness, facility qualification, and manufacturing compliance.",
        name="Manufacturing Operations Head",
        role="Manufacturing Leadership",
        experience_years=22,
        background="Pharmaceutical manufacturing and operations",
        agent_description=(
            "Manufacturing head who certifies plant readiness and compliant throughput."
        ),
        agent_capabilities=[
            "Validates facilities and equipment",
            "Approves manufacturing readiness",
            "Oversees batch execution and release",
            "Manages deviations and improvements",
        ],
    )
    pharmacovigilance_director = HumanAgentConfig(
        agent_id="pharmacovigilance_director",
        agent_type="human_mock",
        system_prompt="Pharmacovigilance Director ensuring patient safety, regulatory safety reporting, and risk management compliance.",
        name="Pharmacovigilance Director",
        role="Safety Leadership",
        experience_years=15,
        background="Drug safety and pharmacovigilance",
        agent_description=(
            "PV lead who assures patient protection and regulator confidence post‑launch."
        ),
        agent_capabilities=[
            "Approves PV systems and RMP",
            "Oversees signal detection and reporting",
            "Chairs safety governance",
            "Coordinates inspections and findings",
        ],
    )
    medical_affairs_director = HumanAgentConfig(
        agent_id="medical_affairs_director",
        agent_type="human_mock",
        system_prompt="Medical Affairs Director providing clinical oversight, medical review, and healthcare provider engagement.",
        name="Medical Affairs Director",
        role="Medical Leadership",
        experience_years=19,
        background="Clinical medicine and medical affairs",
        agent_description=(
            "Medical leader who ensures scientific accuracy and ethical HCP engagement."
        ),
        agent_capabilities=[
            "Reviews clinical claims and materials",
            "Guides scientific communications",
            "Coordinates MSL training and FAQs",
            "Oversees publication and evidence plans",
        ],
    )
    regulatory_compliance_auditor = HumanAgentConfig(
        agent_id="regulatory_compliance_auditor",
        agent_type="human_mock",
        system_prompt="Regulatory compliance auditor conducting internal audits and ensuring readiness for regulatory inspections.",
        name="Regulatory Compliance Auditor",
        role="Compliance Audit",
        experience_years=14,
        background="Regulatory compliance and audit",
        agent_description=(
            "Independent auditor who tests compliance and closes gaps before authorities do."
        ),
        agent_capabilities=[
            "Plans and executes compliance audits",
            "Evaluates CAPA effectiveness",
            "Verifies documentation completeness",
            "Prepares inspection mock‑audits",
        ],
    )
    commercial_executive = HumanAgentConfig(
        agent_id="commercial_executive",
        agent_type="human_mock",
        system_prompt="Commercial Executive providing strategic oversight for market access, pricing, and launch execution.",
        name="Commercial Executive",
        role="Commercial Leadership",
        experience_years=17,
        background="Pharmaceutical commercial strategy",
        agent_description=(
            "Executive who aligns market strategy with safety/regulatory constraints to drive responsible success."
        ),
        agent_capabilities=[
            "Sets launch commercial objectives",
            "Balances access, price, and ethics",
            "Approves go‑to‑market plans",
            "Resolves cross‑functional trade‑offs",
        ],
    )
    launch_steering_committee = HumanAgentConfig(
        agent_id="launch_steering_committee",
        agent_type="human_mock",
        system_prompt="Launch Steering Committee responsible for cross-functional governance, launch gates, and final authorization.",
        name="Launch Steering Committee",
        role="Executive Governance",
        experience_years=25,
        background="Pharmaceutical executive leadership",
        agent_description=(
            "Governance body that enforces gates and authorizes launch when evidence supports it."
        ),
        agent_capabilities=[
            "Chairs gate reviews and sign‑offs",
            "Challenges risk and readiness assumptions",
            "Allocates resources for blockers",
            "Approves final authorization",
        ],
    )

    # Stakeholder (Chief Medical Officer) for patient safety and regulatory priorities
    stakeholder = StakeholderConfig(
        agent_id="chief_medical_officer",
        agent_type="stakeholder",
        system_prompt=(
            "You are the Chief Medical Officer balancing patient safety, regulatory compliance, commercial objectives, and launch timing."
        ),
        model_name="o3",
        name="Chief Medical Officer",
        role="Executive Stakeholder",
        persona_description="Patient-focused, safety-first, values regulatory excellence with responsible commercial success.",
        agent_description=(
            "CMO who prioritizes patient safety and compliance, and makes the final call on launch readiness."
        ),
        agent_capabilities=[
            "Balances patient safety vs speed",
            "Sets non‑negotiable guardrails",
            "Approves risk mitigations/waivers",
            "Owns final launch decision",
        ],
        response_latency_steps_min=1,
        response_latency_steps_max=4,
        push_probability_per_timestep=0.12,
        suggestion_rate=0.6,
        clarification_reply_rate=0.9,
        strictness=0.8,
        verbosity=3,
        preference_data=PreferenceSnapshot(
            preferences=[
                Preference(name="patient_safety", weight=0.4),
                Preference(name="regulatory_compliance", weight=0.3),
                Preference(name="manufacturing_quality", weight=0.2),
                Preference(name="commercial_readiness", weight=0.1),
            ]
        ),
    )

    return {
        "regulatory_affairs_lead": regulatory_affairs_lead,
        "manufacturing_scientist": manufacturing_scientist,
        "quality_assurance_manager": quality_assurance_manager,
        "pharmacovigilance_specialist": pharmacovigilance_specialist,
        "market_access_strategist": market_access_strategist,
        "supply_chain_coordinator": supply_chain_coordinator,
        "clinical_data_manager": clinical_data_manager,
        "commercial_launch_manager": commercial_launch_manager,
        "fda_regulatory_consultant": fda_regulatory_consultant,
        "ema_regulatory_consultant": ema_regulatory_consultant,
        "quality_control_director": quality_control_director,
        "manufacturing_operations_head": manufacturing_operations_head,
        "pharmacovigilance_director": pharmacovigilance_director,
        "medical_affairs_director": medical_affairs_director,
        "regulatory_compliance_auditor": regulatory_compliance_auditor,
        "commercial_executive": commercial_executive,
        "launch_steering_committee": launch_steering_committee,
        "stakeholder": stakeholder,
    }


def create_team_timeline():
    """Create phased coordination timeline for pharmaceutical product launch."""

    cfg = create_team_configs()
    return {
        0: [
            ("add", cfg["regulatory_affairs_lead"], "eCTD dossier preparation"),
            ("add", cfg["manufacturing_scientist"], "Manufacturing validation"),
            ("add", cfg["quality_assurance_manager"], "Quality by Design framework"),
            ("add", cfg["clinical_data_manager"], "Clinical data compilation"),
        ],
        12: [
            (
                "add",
                cfg["pharmacovigilance_specialist"],
                "Pharmacovigilance system setup",
            ),
            ("add", cfg["supply_chain_coordinator"], "Supply chain readiness"),
        ],
        20: [
            ("add", cfg["fda_regulatory_consultant"], "FDA submission guidance"),
            ("add", cfg["ema_regulatory_consultant"], "EMA regulatory review"),
        ],
        28: [
            ("add", cfg["quality_control_director"], "Quality control oversight"),
            ("add", cfg["manufacturing_operations_head"], "Manufacturing operations"),
        ],
        35: [
            ("add", cfg["market_access_strategist"], "Market access strategy"),
            ("add", cfg["pharmacovigilance_director"], "Safety system validation"),
        ],
        42: [
            ("add", cfg["medical_affairs_director"], "Medical affairs review"),
            ("add", cfg["commercial_launch_manager"], "Commercial preparation"),
        ],
        48: [
            ("add", cfg["regulatory_compliance_auditor"], "Compliance audit"),
            ("add", cfg["commercial_executive"], "Commercial strategy"),
        ],
        55: [
            (
                "add",
                cfg["launch_steering_committee"],
                "Launch governance and authorization",
            ),
        ],
    }
