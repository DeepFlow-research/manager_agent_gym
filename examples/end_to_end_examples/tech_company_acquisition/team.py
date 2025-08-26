"""
Technology Company Acquisition & Integration Demo

Real-world use case: $150M SaaS platform company acquisition and integration.

Demonstrates:
- Multi-workstream coordination across technology, financial, regulatory, and operational domains
- Cross-functional expertise integration for complex acquisition due diligence and execution
- Timeline-driven team deployment with phase-specific expertise activation
- Stakeholder management across acquiring and target company teams during integration
- Risk mitigation through specialized roles for compliance, technology, and human capital integration
"""

from manager_agent_gym.schemas.workflow_agents import AIAgentConfig, HumanAgentConfig


def create_tech_acquisition_team_configs():
    """Create AI and human mock agent configurations for technology acquisition integration."""

    # ---------------------------
    # AI AGENTS - Technical & Operational
    # ---------------------------
    tech_due_diligence_lead = AIAgentConfig(
        agent_id="tech_due_diligence_lead",
        agent_type="ai",
        system_prompt=(
            "You are a Technology Due Diligence Lead specializing in software architecture assessment, "
            "code quality analysis, cybersecurity audits, infrastructure scalability evaluation, and "
            "technical debt quantification with integration complexity mapping."
        ),
        agent_description=(
            "Technical diligence lead who turns sprawling systems into a clear risk map and integration plan."
        ),
        agent_capabilities=[
            "Assesses architecture and code quality",
            "Evaluates cybersecurity posture",
            "Quantifies technical debt and risks",
            "Drafts integration complexity map",
        ],
    )

    business_analyst = AIAgentConfig(
        agent_id="business_analyst",
        agent_type="ai",
        system_prompt=(
            "You are a Business Analyst focusing on SaaS metrics validation (ARR, churn, CAC, LTV), "
            "customer contract analysis, recurring revenue sustainability, and operational workflow assessment."
        ),
        agent_description=(
            "Business analyst who validates SaaS fundamentals and pressure‑tests growth assumptions."
        ),
        agent_capabilities=[
            "Validates ARR/churn/CAC/LTV metrics",
            "Analyzes contracts and cohorts",
            "Assesses revenue durability",
            "Summarizes operational workflows",
        ],
    )

    financial_analyst = AIAgentConfig(
        agent_id="financial_analyst",
        agent_type="ai",
        system_prompt=(
            "You are a Financial Analyst conducting financial projection verification, competitive positioning "
            "evaluation, market opportunity sizing, and acquisition valuation analysis."
        ),
        agent_description=(
            "Financial analyst who connects market reality to projections and valuation."
        ),
        agent_capabilities=[
            "Builds projection cross‑checks",
            "Sizes market and competition",
            "Analyzes valuation sensitivities",
            "Flags key model risks",
        ],
    )

    systems_integration_architect = AIAgentConfig(
        agent_id="systems_integration_architect",
        agent_type="ai",
        system_prompt=(
            "You are a Systems Integration Architect designing platform compatibility roadmaps, "
            "data migration planning, API integration design, and security infrastructure harmonization."
        ),
        agent_description=(
            "Architect who designs pragmatic integration roadmaps and reduces migration risk."
        ),
        agent_capabilities=[
            "Designs platform compatibility plans",
            "Plans data migration and cutovers",
            "Defines API/integration patterns",
            "Aligns security infrastructure",
        ],
    )

    cybersecurity_specialist = AIAgentConfig(
        agent_id="cybersecurity_specialist",
        agent_type="ai",
        system_prompt=(
            "You are a Cybersecurity Specialist conducting security audits, data privacy compliance verification, "
            "infrastructure security assessment, and integration security protocol design."
        ),
        agent_description=(
            "Security specialist who finds material risks early and proposes workable mitigations."
        ),
        agent_capabilities=[
            "Runs security audits and gap analysis",
            "Verifies privacy/compliance posture",
            "Designs integration security controls",
            "Tracks remediation owners and SLAs",
        ],
    )

    hr_integration_manager = AIAgentConfig(
        agent_id="hr_integration_manager",
        agent_type="ai",
        system_prompt=(
            "You are an HR Integration Manager developing talent retention strategies, cultural assessment, "
            "organizational design, compensation harmonization, and employee communication initiatives."
        ),
        agent_description=(
            "People leader who balances retention, culture, and org design through transition."
        ),
        agent_capabilities=[
            "Designs retention and comms plans",
            "Runs cultural/organizational assessments",
            "Coordinates comp/benefit harmonization",
            "Guides change management and onboarding",
        ],
    )

    customer_success_manager = AIAgentConfig(
        agent_id="customer_success_manager",
        agent_type="ai",
        system_prompt=(
            "You are a Customer Success Manager ensuring customer relationship preservation, "
            "service continuity assurance, account management transition, and satisfaction monitoring."
        ),
        agent_description=(
            "Customer steward who protects relationships and minimizes churn during the deal."
        ),
        agent_capabilities=[
            "Plans account transitions",
            "Ensures service continuity",
            "Coordinates comms and SLAs",
            "Monitors satisfaction and risks",
        ],
    )

    project_coordination_lead = AIAgentConfig(
        agent_id="project_coordination_lead",
        agent_type="ai",
        system_prompt=(
            "You are a Project Coordination Lead establishing integration management office, "
            "cross-functional team coordination, governance structures, and project tracking infrastructure."
        ),
        agent_description=(
            "IMO lead who sets governance, coordinates teams, and drives decisions to closure."
        ),
        agent_capabilities=[
            "Establishes governance and cadence",
            "Maintains trackers and status",
            "Surfaces risks/decisions with owners",
            "Keeps artifacts consistent",
        ],
    )

    # ---------------------------
    # HUMAN MOCK AGENTS - Approvals & Oversight
    # ---------------------------
    regulatory_counsel = HumanAgentConfig(
        agent_id="regulatory_counsel",
        agent_type="human_mock",
        system_prompt="Legal counsel specializing in antitrust clearance, HSR filing coordination, and regulatory compliance across multiple jurisdictions.",
        name="Regulatory Counsel",
        role="Legal & Regulatory",
        experience_years=12,
        background="M&A regulatory law",
        agent_description=(
            "Antitrust strategist who sequences filings and navigates remedies with minimal deal friction."
        ),
        agent_capabilities=[
            "Advises on HSR and remedies",
            "Coordinates filings and timelines",
            "Interfaces with regulators",
            "Mitigates antitrust risks",
        ],
    )

    data_privacy_officer = HumanAgentConfig(
        agent_id="data_privacy_officer",
        agent_type="human_mock",
        system_prompt="Data Privacy Officer ensuring GDPR/CCPA compliance, cross-border data transfer protocols, and privacy framework integration.",
        name="Data Privacy Officer",
        role="Privacy & Compliance",
        experience_years=8,
        background="Data privacy and security",
        agent_description=(
            "Privacy lead who ensures lawful data handling across both orgs throughout diligence and integration."
        ),
        agent_capabilities=[
            "Reviews DPAs and data flows",
            "Sets transfer and minimization rules",
            "Approves integration controls",
            "Tracks remediation and notices",
        ],
    )

    ip_legal_specialist = HumanAgentConfig(
        agent_id="ip_legal_specialist",
        agent_type="human_mock",
        system_prompt="Intellectual Property Legal Specialist conducting IP ownership validation, software licensing verification, and patent portfolio assessment.",
        name="IP Legal Specialist",
        role="Intellectual Property",
        experience_years=10,
        background="Technology law and IP",
        agent_description=(
            "IP specialist who secures chain‑of‑title and practical licensing for the combined company."
        ),
        agent_capabilities=[
            "Validates IP ownership and OSS",
            "Drafts IP/OSS schedules",
            "Advises on assignment/consents",
            "Mitigates IP litigation risks",
        ],
    )

    financial_controller = HumanAgentConfig(
        agent_id="financial_controller",
        agent_type="human_mock",
        system_prompt="Financial Controller overseeing acquisition accounting, financial integration, budget management, and synergy tracking.",
        name="Financial Controller",
        role="Financial Integration",
        experience_years=14,
        background="M&A accounting and finance",
        agent_description=(
            "Controller who keeps the numbers reliable across purchase accounting and integration."
        ),
        agent_capabilities=[
            "Oversees acquisition accounting",
            "Runs budget and synergy tracking",
            "Aligns reporting and controls",
            "Approves financial integration steps",
        ],
    )

    chief_technology_officer = HumanAgentConfig(
        agent_id="chief_technology_officer",
        agent_type="human_mock",
        system_prompt="Chief Technology Officer providing strategic technology vision, integration architecture approval, and technical leadership transition oversight.",
        name="Chief Technology Officer",
        role="Technology Leadership",
        experience_years=16,
        background="Enterprise technology and M&A",
        agent_description=(
            "Technology leader who sets the integration vision and de‑risks technical transitions."
        ),
        agent_capabilities=[
            "Approves architecture decisions",
            "Allocates technical resources",
            "Chairs integration design reviews",
            "Resolves high‑impact technical risks",
        ],
    )

    executive_sponsor = HumanAgentConfig(
        agent_id="executive_sponsor",
        agent_type="human_mock",
        system_prompt="Executive Sponsor overseeing acquisition strategy execution, stakeholder communication, and integration success accountability.",
        name="Executive Sponsor",
        role="Executive Leadership",
        experience_years=18,
        background="Corporate development and M&A",
        agent_description=(
            "Executive owner who aligns stakeholders and clears organizational roadblocks."
        ),
        agent_capabilities=[
            "Sets success criteria and guardrails",
            "Resolves cross‑functional conflicts",
            "Approves scope and timelines",
            "Communicates status to leadership",
        ],
    )

    target_company_ceo = HumanAgentConfig(
        agent_id="target_company_ceo",
        agent_type="human_mock",
        system_prompt="Target Company CEO facilitating integration cooperation, employee communication, customer transition support, and cultural integration leadership.",
        name="Target Company CEO",
        role="Target Leadership",
        experience_years=12,
        background="SaaS company leadership",
        agent_description=(
            "Target leader who keeps talent engaged and customers supported during the transition."
        ),
        agent_capabilities=[
            "Coordinates employee communications",
            "Supports customer continuity",
            "Aligns leadership transition",
            "Approves disclosure schedule accuracy",
        ],
    )

    integration_steering_committee = HumanAgentConfig(
        agent_id="integration_steering_committee",
        agent_type="human_mock",
        system_prompt="Integration Steering Committee providing governance oversight, strategic decision-making, issue escalation resolution, and integration milestone approval.",
        name="Integration Steering Committee",
        role="Governance & Oversight",
        experience_years=20,
        background="Corporate governance and integration",
        agent_description=(
            "Governance body that enforces decision discipline and milestone accountability."
        ),
        agent_capabilities=[
            "Sets governance and decision rights",
            "Approves milestones and exceptions",
            "Allocates resources to unblock work",
            "Monitors integration KPIs",
        ],
    )

    return {
        "tech_due_diligence_lead": tech_due_diligence_lead,
        "business_analyst": business_analyst,
        "financial_analyst": financial_analyst,
        "systems_integration_architect": systems_integration_architect,
        "cybersecurity_specialist": cybersecurity_specialist,
        "hr_integration_manager": hr_integration_manager,
        "customer_success_manager": customer_success_manager,
        "project_coordination_lead": project_coordination_lead,
        "regulatory_counsel": regulatory_counsel,
        "data_privacy_officer": data_privacy_officer,
        "ip_legal_specialist": ip_legal_specialist,
        "financial_controller": financial_controller,
        "chief_technology_officer": chief_technology_officer,
        "executive_sponsor": executive_sponsor,
        "target_company_ceo": target_company_ceo,
        "integration_steering_committee": integration_steering_committee,
    }


def create_tech_acquisition_team_timeline():
    """Create phase-based coordination timeline for technology acquisition integration."""

    cfg = create_tech_acquisition_team_configs()
    return {
        0: [
            # Phase 1: Initial Due Diligence Team Deployment
            (
                "add",
                cfg["tech_due_diligence_lead"],
                "Technology architecture and security assessment",
            ),
            (
                "add",
                cfg["business_analyst"],
                "SaaS metrics and customer contract validation",
            ),
            (
                "add",
                cfg["financial_analyst"],
                "Financial projection and valuation verification",
            ),
            (
                "add",
                cfg["project_coordination_lead"],
                "Integration management office establishment",
            ),
            (
                "add",
                cfg["regulatory_counsel"],
                "Regulatory framework and compliance planning",
            ),
        ],
        6: [
            # Phase 2: Specialized Due Diligence Expansion
            (
                "add",
                cfg["cybersecurity_specialist"],
                "Deep security audit and compliance verification",
            ),
            (
                "add",
                cfg["data_privacy_officer"],
                "GDPR/CCPA compliance and privacy framework assessment",
            ),
            (
                "add",
                cfg["ip_legal_specialist"],
                "Intellectual property validation and licensing review",
            ),
        ],
        12: [
            # Phase 3: Integration Planning and Systems Architecture
            (
                "add",
                cfg["systems_integration_architect"],
                "Platform integration and migration planning",
            ),
            (
                "add",
                cfg["hr_integration_manager"],
                "Talent retention and cultural integration strategy",
            ),
            (
                "add",
                cfg["financial_controller"],
                "Financial integration and budget management",
            ),
        ],
        18: [
            # Phase 4: Stakeholder Engagement and Customer Transition
            (
                "add",
                cfg["customer_success_manager"],
                "Customer relationship preservation and transition",
            ),
            (
                "add",
                cfg["target_company_ceo"],
                "Employee communication and cultural integration leadership",
            ),
            (
                "add",
                cfg["chief_technology_officer"],
                "Technology leadership transition and architecture approval",
            ),
        ],
        25: [
            # Phase 5: Executive Oversight and Governance
            (
                "add",
                cfg["executive_sponsor"],
                "Strategic oversight and stakeholder communication",
            ),
            (
                "add",
                cfg["integration_steering_committee"],
                "Governance, decision-making, and milestone approval",
            ),
        ],
    }
