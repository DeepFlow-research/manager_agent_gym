"""
UK University Accreditation Renewal Demo

Real-world use case: Mid-size UK university OfS registration renewal.

Demonstrates:
- Multi-stakeholder regulatory compliance coordination across diverse functional areas
- Sequential dependency management with parallel track execution for efficiency
- Risk-based governance oversight with escalation management under regulatory deadlines
- Evidence-based compliance documentation with quality assurance validation
- Cross-functional team coordination between academic, administrative, and external stakeholders
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
    """Create AI and human mock agent configurations for UK University Accreditation."""

    # AI Agents for specialist tasks
    academic_quality_analyst = AIAgentConfig(
        agent_id="academic_quality_analyst",
        agent_type="ai",
        system_prompt=(
            "You are an Academic Quality Analyst specializing in OfS B-conditions compliance, "
            "external examiner report analysis, student outcome KPIs, and academic standards validation."
        ),
        agent_description=(
            "Analyst who turns evidence into clear judgments about academic standards against OfS expectations."
        ),
        agent_capabilities=[
            "Maps B‑conditions to evidence",
            "Analyzes external examiner reports",
            "Tracks outcome KPIs and trends",
            "Prepares governance‑ready summaries",
        ],
    )
    regulatory_compliance_specialist = AIAgentConfig(
        agent_id="regulatory_compliance_specialist",
        agent_type="ai",
        system_prompt=(
            "You are a Regulatory Compliance Specialist focusing on OfS conditions mapping, "
            "consumer law compliance, UKVI sponsorship requirements, and Prevent duty documentation."
        ),
        agent_description=(
            "Compliance mapper who aligns OfS/consumer/UKVI/Prevent requirements with auditable controls."
        ),
        agent_capabilities=[
            "Builds condition‑to‑control matrices",
            "Drafts compliant procedures and notices",
            "Coordinates UKVI and Prevent documentation",
            "Flags gaps and remediation owners",
        ],
    )
    data_quality_manager = AIAgentConfig(
        agent_id="data_quality_manager",
        agent_type="ai",
        system_prompt=(
            "You are a Data Quality Manager responsible for HESA Data Futures validation, "
            "internal audit processes, data integrity controls, and GDPR compliance."
        ),
        agent_description=(
            "Data steward who ensures HESA submissions are correct and the data trail stands up to audit."
        ),
        agent_capabilities=[
            "Runs Data Futures validation",
            "Implements data integrity controls",
            "Coordinates internal audits",
            "Documents GDPR‑aligned governance",
        ],
    )
    access_participation_coordinator = AIAgentConfig(
        agent_id="access_participation_coordinator",
        agent_type="ai",
        system_prompt=(
            "You coordinate Access & Participation Plan updates, analyzing monitoring data, "
            "conducting gap analysis, and developing evidence-based intervention strategies."
        ),
        agent_description=(
            "Coordinator who drives evidence‑based interventions and keeps APP reporting coherent."
        ),
        agent_capabilities=[
            "Analyzes APP monitoring data",
            "Designs interventions and KPIs",
            "Drafts updates and governance packs",
            "Tracks actions to completion",
        ],
    )
    student_protection_officer = AIAgentConfig(
        agent_id="student_protection_officer",
        agent_type="ai",
        system_prompt=(
            "You are a Student Protection Officer ensuring CMA consumer law compliance, "
            "contract fairness, cost transparency, and student interest protection."
        ),
        agent_description=(
            "Officer who safeguards student interests with fair contracts, clear costs, and credible protections."
        ),
        agent_capabilities=[
            "Audits CMA contract fairness",
            "Ensures cost transparency",
            "Maintains protection plans",
            "Coordinates student‑facing comms",
        ],
    )
    financial_sustainability_analyst = AIAgentConfig(
        agent_id="financial_sustainability_analyst",
        agent_type="ai",
        system_prompt=(
            "You analyze institutional financial sustainability, conduct scenario planning, "
            "and maintain student protection plan documentation."
        ),
        agent_description=(
            "Analyst who stress‑tests institutional finances and links risks to mitigation plans."
        ),
        agent_capabilities=[
            "Runs scenario and sensitivity analysis",
            "Builds sustainability indicators",
            "Links risks to protection plans",
            "Prepares governing‑body summaries",
        ],
    )
    governance_documentation_lead = AIAgentConfig(
        agent_id="governance_documentation_lead",
        agent_type="ai",
        system_prompt=(
            "You assemble governance documentation, coordinate evidence packages, "
            "manage approval workflows, and ensure submission readiness."
        ),
        agent_description=(
            "Documentation owner who assembles a coherent submission with traceable evidence."
        ),
        agent_capabilities=[
            "Builds governance document sets",
            "Maintains evidence index and traceability",
            "Coordinates approvals and sign‑offs",
            "Ensures submission readiness",
        ],
    )

    # Human Mock Agents for approvals and oversight
    external_quality_reviewer = HumanAgentConfig(
        agent_id="external_quality_reviewer",
        agent_type="human_mock",
        system_prompt="Independent external quality reviewer validating academic standards compliance and quality assurance processes.",
        name="External Quality Reviewer",
        role="Independent Quality Validation",
        experience_years=15,
        background="Higher education quality assurance",
        agent_description=(
            "Independent reviewer who validates standards and provides constructive external challenge."
        ),
        agent_capabilities=[
            "Conducts quality reviews",
            "Benchmarks against sector norms",
            "Issues findings and recommendations",
            "Verifies action closure",
        ],
    )
    legal_compliance_counsel = HumanAgentConfig(
        agent_id="legal_compliance_counsel",
        agent_type="human_mock",
        system_prompt="Legal compliance counsel ensuring consumer law compliance and regulatory requirement adherence.",
        name="Legal Compliance Counsel",
        role="Legal Compliance",
        experience_years=12,
        background="Education law and consumer protection",
        agent_description=(
            "Counsel who ensures student‑facing obligations and consumer protections are truly met."
        ),
        agent_capabilities=[
            "Reviews consumer law compliance",
            "Advises on notices/terms",
            "Checks enforcement readiness",
            "Approves remedial actions",
        ],
    )
    data_protection_officer = HumanAgentConfig(
        agent_id="data_protection_officer",
        agent_type="human_mock",
        system_prompt="Data Protection Officer ensuring GDPR compliance, data quality validation, and information governance.",
        name="Data Protection Officer",
        role="Data Protection",
        experience_years=8,
        background="Data protection and information governance",
        agent_description=(
            "DPO who balances research/teaching needs with lawful processing and data minimization."
        ),
        agent_capabilities=[
            "Reviews GDPR compliance",
            "Approves data sharing/retention",
            "Oversees DPIA/IG processes",
            "Tracks remediation to closure",
        ],
    )
    internal_audit_director = HumanAgentConfig(
        agent_id="internal_audit_director",
        agent_type="human_mock",
        system_prompt="Internal Audit Director reviewing compliance processes, control effectiveness, and audit trail documentation.",
        name="Internal Audit Director",
        role="Internal Audit",
        experience_years=14,
        background="Higher education audit and controls",
        agent_description=(
            "Assurance lead who validates process effectiveness and audit trail completeness."
        ),
        agent_capabilities=[
            "Plans and executes audits",
            "Assesses control effectiveness",
            "Reports findings and follow‑ups",
            "Confirms remediation effectiveness",
        ],
    )
    ukvi_compliance_manager = HumanAgentConfig(
        agent_id="ukvi_compliance_manager",
        agent_type="human_mock",
        system_prompt="UKVI Compliance Manager overseeing student sponsor licence compliance and immigration law adherence.",
        name="UKVI Compliance Manager",
        role="Immigration Compliance",
        experience_years=10,
        background="Immigration law and student visa compliance",
        agent_description=(
            "UKVI lead who ensures sponsor licence compliance and robust status tracking."
        ),
        agent_capabilities=[
            "Audits sponsor licence duties",
            "Validates status tracking/reporting",
            "Coordinates with case teams",
            "Prepares inspection evidence",
        ],
    )
    prevent_duty_coordinator = HumanAgentConfig(
        agent_id="prevent_duty_coordinator",
        agent_type="human_mock",
        system_prompt="Prevent Duty Coordinator managing statutory compliance, risk assessment, and safeguarding protocols.",
        name="Prevent Duty Coordinator",
        role="Safeguarding & Prevent",
        experience_years=7,
        background="Safeguarding and counter-terrorism compliance",
        agent_description=(
            "Coordinator who ensures Prevent duties are met proportionately with clear safeguards."
        ),
        agent_capabilities=[
            "Maintains risk assessments",
            "Runs training and awareness",
            "Documents referrals/process",
            "Reviews proportionality and rights",
        ],
    )
    senate_chair = HumanAgentConfig(
        agent_id="senate_chair",
        agent_type="human_mock",
        system_prompt="Senate Chair responsible for academic governance oversight and final academic quality approvals.",
        name="Senate Chair",
        role="Academic Governance",
        experience_years=20,
        background="Academic leadership and governance",
        agent_description=(
            "Academic governance lead who challenges evidence and approves standards."
        ),
        agent_capabilities=[
            "Chairs academic approvals",
            "Ensures standards are met",
            "Tracks actions to close",
            "Balances quality and timelines",
        ],
    )
    university_council_chair = HumanAgentConfig(
        agent_id="university_council_chair",
        agent_type="human_mock",
        system_prompt="University Council Chair providing institutional governance oversight and final submission approval.",
        name="University Council Chair",
        role="Institutional Governance",
        experience_years=18,
        background="Higher education governance and strategy",
        agent_description=(
            "Council chair who provides institutional oversight and final sign‑off."
        ),
        agent_capabilities=[
            "Oversees institutional compliance",
            "Approves submission readiness",
            "Balances risk and reputation",
            "Holds executives accountable",
        ],
    )

    # Stakeholder (Vice-Chancellor) for strategic oversight and priority decisions
    stakeholder = StakeholderConfig(
        agent_id="vice_chancellor",
        agent_type="stakeholder",
        system_prompt=(
            "You are the Vice-Chancellor balancing regulatory compliance, institutional reputation, "
            "and operational efficiency in the accreditation renewal process."
        ),
        model_name="o3",
        name="Vice-Chancellor",
        role="Executive Leadership",
        persona_description="Strategic, compliance-focused, values institutional reputation and student interest protection.",
        agent_description=(
            "Vice‑Chancellor who sets direction, arbitrates trade‑offs, and signs off on a defensible submission."
        ),
        agent_capabilities=[
            "Sets priorities and guardrails",
            "Chairs cross‑functional reviews",
            "Approves remediation plans",
            "Owns final submission decision",
        ],
        response_latency_steps_min=1,
        response_latency_steps_max=4,
        push_probability_per_timestep=0.08,
        suggestion_rate=0.4,
        clarification_reply_rate=0.85,
        strictness=0.7,
        verbosity=3,
        initial_preferences=PreferenceWeights(
            preferences=[
                Preference(name="regulatory_compliance", weight=0.4),
                Preference(name="academic_quality", weight=0.3),
                Preference(name="governance", weight=0.2),
                Preference(name="speed", weight=0.06),
                Preference(name="cost", weight=0.04),
            ]
        ),
    )

    return {
        "academic_quality_analyst": academic_quality_analyst,
        "regulatory_compliance_specialist": regulatory_compliance_specialist,
        "data_quality_manager": data_quality_manager,
        "access_participation_coordinator": access_participation_coordinator,
        "student_protection_officer": student_protection_officer,
        "financial_sustainability_analyst": financial_sustainability_analyst,
        "governance_documentation_lead": governance_documentation_lead,
        "external_quality_reviewer": external_quality_reviewer,
        "legal_compliance_counsel": legal_compliance_counsel,
        "data_protection_officer": data_protection_officer,
        "internal_audit_director": internal_audit_director,
        "ukvi_compliance_manager": ukvi_compliance_manager,
        "prevent_duty_coordinator": prevent_duty_coordinator,
        "senate_chair": senate_chair,
        "university_council_chair": university_council_chair,
        "stakeholder": stakeholder,
    }


def create_team_timeline():
    """Create phased coordination timeline for UK University Accreditation renewal."""

    cfg = create_team_configs()
    return {
        0: [
            (
                "add",
                cfg["academic_quality_analyst"],
                "Quality & standards evidence compilation",
            ),
            (
                "add",
                cfg["regulatory_compliance_specialist"],
                "OfS conditions mapping and compliance",
            ),
            (
                "add",
                cfg["data_quality_manager"],
                "HESA data validation and quality controls",
            ),
            (
                "add",
                cfg["governance_documentation_lead"],
                "Governance structure and documentation",
            ),
        ],
        8: [
            (
                "add",
                cfg["access_participation_coordinator"],
                "Access & Participation Plan update",
            ),
            (
                "add",
                cfg["student_protection_officer"],
                "Consumer law compliance and student protection",
            ),
        ],
        12: [
            (
                "add",
                cfg["ukvi_compliance_manager"],
                "UKVI sponsor licence compliance validation",
            ),
            (
                "add",
                cfg["prevent_duty_coordinator"],
                "Prevent duty compliance documentation",
            ),
        ],
        16: [
            (
                "add",
                cfg["financial_sustainability_analyst"],
                "Financial sustainability assessment",
            ),
        ],
        20: [
            ("add", cfg["external_quality_reviewer"], "Independent quality validation"),
            ("add", cfg["legal_compliance_counsel"], "Legal compliance review"),
        ],
        24: [
            (
                "add",
                cfg["data_protection_officer"],
                "Data protection and GDPR compliance review",
            ),
            (
                "add",
                cfg["internal_audit_director"],
                "Internal audit and controls validation",
            ),
        ],
        28: [
            ("add", cfg["senate_chair"], "Academic governance approval"),
        ],
        30: [
            (
                "add",
                cfg["university_council_chair"],
                "Final institutional approval and submission",
            ),
        ],
    }
