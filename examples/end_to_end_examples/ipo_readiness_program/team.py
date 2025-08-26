"""
IPO Readiness Program Demo

Real-world use case: Mid-size growth company preparing for U.S. public listing.

Demonstrates:
- Complex regulatory compliance coordination under strict SEC deadlines
- Multi-stakeholder team management across legal, audit, governance, and finance
- Risk-based decision making with materiality assessments and disclosure judgments
- Document workflow orchestration with approval dependencies and version control
- Crisis management when material weaknesses or compliance gaps are discovered
- Strategic timing decisions balancing transparency requirements with competitive positioning
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
    """Create AI and human mock agent configurations for IPO readiness."""

    financial_controller = AIAgentConfig(
        agent_id="financial_controller",
        agent_type="ai",
        system_prompt=(
            "You are a Financial Controller focusing on PCAOB audit coordination, financial statement preparation, "
            "and non-GAAP reconciliation compliance for SEC registration."
        ),
        agent_description=(
            "Controller who orchestrates audit‑ready financials and keeps the S‑1 numbers clean and defensible."
        ),
        agent_capabilities=[
            "Coordinates PCAOB audit requests",
            "Owns financial statements and tie‑outs",
            "Manages non‑GAAP reconciliation",
            "Tracks disclosure consistency",
        ],
    )
    securities_lawyer = AIAgentConfig(
        agent_id="securities_lawyer",
        agent_type="ai",
        system_prompt=(
            "You are a Securities Lawyer specializing in S-1 registration statement drafting, "
            "SEC disclosure requirements, and quiet period compliance."
        ),
        agent_description=(
            "Securities specialist who steers S‑1 drafting and keeps the team aligned with SEC rules and timelines."
        ),
        agent_capabilities=[
            "Drafts/edits S‑1 and exhibits",
            "Guides disclosure and quiet period",
            "Coordinates SEC comments/responses",
            "Maintains rule compliance mapping",
        ],
    )
    governance_specialist = AIAgentConfig(
        agent_id="governance_specialist",
        agent_type="ai",
        system_prompt=(
            "You are a Corporate Governance Specialist establishing board independence, "
            "committee structures, and NYSE/Nasdaq listing compliance."
        ),
        agent_description=(
            "Governance architect who sets board independence, committees, and listing compliance mechanics."
        ),
        agent_capabilities=[
            "Designs board/committee structures",
            "Implements independence standards",
            "Aligns with NYSE/Nasdaq rules",
            "Prepares governance disclosures",
        ],
    )
    sox_compliance_manager = AIAgentConfig(
        agent_id="sox_compliance_manager",
        agent_type="ai",
        system_prompt=(
            "You design and implement SOX 302/404 internal controls, disclosure controls & procedures, "
            "and management certification processes for public company readiness."
        ),
        agent_description=(
            "Controls leader who operationalizes SOX 302/404 and ensures certifiable management assertions."
        ),
        agent_capabilities=[
            "Implements SOX controls and testing",
            "Builds disclosure controls & procedures",
            "Tracks deficiencies and remediation",
            "Prepares certification packages",
        ],
    )
    audit_coordinator = AIAgentConfig(
        agent_id="audit_coordinator",
        agent_type="ai",
        system_prompt=(
            "You coordinate PCAOB audits, manage comfort letter processes, "
            "and ensure audit opinion quality for IPO registration."
        ),
        agent_description=(
            "Coordination hub for auditors, comfort letters, and opinion deliverables on IPO timeline."
        ),
        agent_capabilities=[
            "Manages audit PBCs and schedules",
            "Coordinates comfort letter process",
            "Ensures opinion quality and readiness",
            "Resolves auditor information gaps",
        ],
    )
    edgar_specialist = AIAgentConfig(
        agent_id="edgar_specialist",
        agent_type="ai",
        system_prompt=(
            "You prepare EDGAR submissions, manage SEC filing workflows, "
            "and coordinate regulatory submission timing and validation."
        ),
        agent_description=(
            "EDGAR operator who gets filings right the first time and keeps submissions on schedule."
        ),
        agent_capabilities=[
            "Prepares/validates EDGAR submissions",
            "Coordinates filing timing and checks",
            "Maintains submission audit trail",
            "Resolves XBRL/formatting issues",
        ],
    )
    disclosure_analyst = AIAgentConfig(
        agent_id="disclosure_analyst",
        agent_type="ai",
        system_prompt=(
            "You analyze materiality thresholds, draft risk factor disclosures, "
            "and ensure comprehensive MD&A narrative preparation."
        ),
        agent_description=(
            "Analyst who drives materiality analysis and clear MD&A and risk narratives."
        ),
        agent_capabilities=[
            "Drafts MD&A and risk factors",
            "Runs materiality assessments",
            "Aligns KPIs across disclosures",
            "Maintains issue/decision logs",
        ],
    )
    ir_communications = AIAgentConfig(
        agent_id="investor_relations_lead",
        agent_type="ai",
        system_prompt=(
            "You develop investor relations strategy, manage quiet period protocols, "
            "and coordinate marketing communications compliance with Regulation FD."
        ),
        agent_description=(
            "IR lead who choreographs quiet‑period comms and prepares the market narrative with compliance."
        ),
        agent_capabilities=[
            "Designs IR strategy and quiet‑period ops",
            "Preps roadshow and messaging controls",
            "Tracks Reg FD compliance",
            "Coordinates comms sign‑offs",
        ],
    )

    # Human sign-offs and specialized roles
    external_auditor = HumanAgentConfig(
        agent_id="external_auditor_lead",
        agent_type="human_mock",
        system_prompt="PCAOB-registered external auditor providing financial statement audit opinions and comfort letters.",
        name="External Auditor Lead",
        role="PCAOB Audit Partner",
        experience_years=15,
        background="Public company auditing",
        agent_description=(
            "External audit partner who signs opinions and ensures audit evidence supports investor‑grade disclosures."
        ),
        agent_capabilities=[
            "Plans and executes PCAOB audits",
            "Issues comfort letters and opinions",
            "Reviews controls and adjustments",
            "Coordinates with audit committee",
        ],
    )
    sec_counsel = HumanAgentConfig(
        agent_id="sec_legal_counsel",
        agent_type="human_mock",
        system_prompt="SEC legal counsel ensuring registration statement compliance and regulatory coordination.",
        name="SEC Legal Counsel",
        role="Securities Law Expert",
        experience_years=12,
        background="SEC practice and public offerings",
        agent_description=(
            "SEC counsel who guides interactions with the Staff and keeps the S‑1 process smooth and compliant."
        ),
        agent_capabilities=[
            "Advises on SEC rules and process",
            "Coordinates comment letter responses",
            "Reviews disclosures and exhibits",
            "Manages regulator communications",
        ],
    )
    independent_director = HumanAgentConfig(
        agent_id="lead_independent_director",
        agent_type="human_mock",
        system_prompt="Lead independent director ensuring board governance compliance and audit committee oversight.",
        name="Lead Independent Director",
        role="Board Governance",
        experience_years=20,
        background="Public company board service",
        agent_description=(
            "Board leader who ensures governance readiness and credible oversight structures for life as a public company."
        ),
        agent_capabilities=[
            "Oversees governance structure build‑out",
            "Chairs independence/committee checks",
            "Coordinates board policy approvals",
            "Interfaces with audit committee",
        ],
    )
    audit_committee_chair = HumanAgentConfig(
        agent_id="audit_committee_chair",
        agent_type="human_mock",
        system_prompt="Audit committee chair with financial expertise overseeing internal controls and auditor independence.",
        name="Audit Committee Chair",
        role="Financial Expert",
        experience_years=18,
        background="CFO and audit committee experience",
        agent_description=(
            "Financial expert who validates internal controls and auditor independence before sign‑off."
        ),
        agent_capabilities=[
            "Oversees SOX readiness",
            "Reviews auditor independence",
            "Approves remediation plans",
            "Grants audit sign‑off",
        ],
    )
    underwriter_counsel = HumanAgentConfig(
        agent_id="underwriter_legal_counsel",
        agent_type="human_mock",
        system_prompt="Underwriter legal counsel conducting due diligence review and comfort letter coordination.",
        name="Underwriter Counsel",
        role="Underwriter Legal",
        experience_years=14,
        background="IPO transactions and due diligence",
        agent_description=(
            "Underwriters’ counsel who runs due‑diligence rigor and coordinates comfort mechanics with banks."
        ),
        agent_capabilities=[
            "Leads due‑diligence and Q&A",
            "Coordinates with auditors on comforts",
            "Reviews offering documents",
            "Advises on marketing restrictions",
        ],
    )
    listing_specialist = HumanAgentConfig(
        agent_id="exchange_listing_specialist",
        agent_type="human_mock",
        system_prompt="Exchange listing specialist ensuring compliance with NYSE/Nasdaq quantitative and qualitative standards.",
        name="Exchange Listing Specialist",
        role="Exchange Relations",
        experience_years=10,
        background="Exchange listing requirements",
        agent_description=(
            "Exchange liaison who ensures quantitative/qualitative listing boxes are genuinely ticked."
        ),
        agent_capabilities=[
            "Runs listing standards checklist",
            "Coordinates with exchange reviewers",
            "Tracks documentation and timelines",
            "Flags gaps for remediation",
        ],
    )
    internal_audit_director = HumanAgentConfig(
        agent_id="internal_audit_director",
        agent_type="human_mock",
        system_prompt="Internal audit director reviewing SOX controls implementation and process effectiveness.",
        name="Internal Audit Director",
        role="Internal Audit",
        experience_years=16,
        background="SOX compliance and internal controls",
        agent_description=(
            "Internal audit lead who validates process control maturity and audit trail completeness."
        ),
        agent_capabilities=[
            "Performs control testing and QA",
            "Reviews documentation sufficiency",
            "Issues findings and follow‑ups",
            "Advises on process improvements",
        ],
    )
    cfo_approval = HumanAgentConfig(
        agent_id="chief_financial_officer",
        agent_type="human_mock",
        system_prompt="Chief Financial Officer providing executive oversight and final financial certification approval.",
        name="Chief Financial Officer",
        role="Executive Leadership",
        experience_years=22,
        background="Public company finance",
        agent_description=(
            "CFO who certifies the numbers and ensures investor‑grade readiness across finance and controls."
        ),
        agent_capabilities=[
            "Owns certification readiness",
            "Aligns finance, audit, and governance",
            "Approves offering economics",
            "Chairs financial sign‑off gates",
        ],
    )

    # Stakeholder (CEO) for strategic decisions and IPO timing
    stakeholder = StakeholderConfig(
        agent_id="company_ceo",
        agent_type="stakeholder",
        system_prompt=(
            "You are the company CEO balancing IPO timing, market conditions, regulatory compliance, and disclosure transparency."
        ),
        model_name="o3",
        name="Company CEO",
        role="Executive Stakeholder",
        persona_description="Strategic, market-focused, values timing and transparency balance for successful public offering.",
        agent_description=(
            "CEO decision‑maker who integrates market timing with compliance and disclosure quality for IPO success."
        ),
        agent_capabilities=[
            "Sets timing and readiness standards",
            "Arbitrates scope vs schedule vs risk",
            "Approves external messaging posture",
            "Holds teams accountable to gates",
        ],
        response_latency_steps_min=1,
        response_latency_steps_max=4,
        push_probability_per_timestep=0.15,
        suggestion_rate=0.6,
        clarification_reply_rate=0.85,
        strictness=0.7,
        verbosity=3,
        initial_preferences=PreferenceWeights(
            preferences=[
                Preference(name="sec_compliance", weight=0.4),
                Preference(name="speed", weight=0.3),
                Preference(name="governance", weight=0.3),
            ]
        ),
    )

    return {
        "financial_controller": financial_controller,
        "securities_lawyer": securities_lawyer,
        "governance_specialist": governance_specialist,
        "sox_compliance_manager": sox_compliance_manager,
        "audit_coordinator": audit_coordinator,
        "edgar_specialist": edgar_specialist,
        "disclosure_analyst": disclosure_analyst,
        "investor_relations_lead": ir_communications,
        "external_auditor_lead": external_auditor,
        "sec_legal_counsel": sec_counsel,
        "lead_independent_director": independent_director,
        "audit_committee_chair": audit_committee_chair,
        "underwriter_legal_counsel": underwriter_counsel,
        "exchange_listing_specialist": listing_specialist,
        "internal_audit_director": internal_audit_director,
        "chief_financial_officer": cfo_approval,
        "stakeholder": stakeholder,
    }


def create_team_timeline():
    """Create phased coordination timeline for IPO readiness."""

    cfg = create_team_configs()
    return {
        0: [
            ("add", cfg["financial_controller"], "Financial audit foundation"),
            ("add", cfg["securities_lawyer"], "S-1 registration preparation"),
            ("add", cfg["governance_specialist"], "Board structure establishment"),
            ("add", cfg["audit_coordinator"], "PCAOB audit coordination"),
        ],
        8: [
            ("add", cfg["sox_compliance_manager"], "SOX compliance implementation"),
            ("add", cfg["disclosure_analyst"], "Risk factor and MD&A preparation"),
        ],
        15: [
            ("add", cfg["edgar_specialist"], "EDGAR filing preparation"),
            ("add", cfg["external_auditor_lead"], "External audit execution"),
        ],
        20: [
            ("add", cfg["sec_legal_counsel"], "SEC legal review"),
            ("add", cfg["lead_independent_director"], "Board governance oversight"),
        ],
        25: [
            ("add", cfg["audit_committee_chair"], "Audit committee approval"),
            ("add", cfg["investor_relations_lead"], "Communications strategy"),
        ],
        28: [
            ("add", cfg["underwriter_legal_counsel"], "Due diligence coordination"),
            (
                "add",
                cfg["exchange_listing_specialist"],
                "Listing standards verification",
            ),
        ],
        30: [
            ("add", cfg["internal_audit_director"], "Internal controls validation"),
            ("add", cfg["chief_financial_officer"], "Executive certification"),
        ],
    }
