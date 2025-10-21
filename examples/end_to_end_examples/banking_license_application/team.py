"""
Banking License Application Demo
Real-world use case: European mid-size commercial bank seeking to establish
federal branch operations in the US market.
Demonstrates:
- Complex regulatory approval workflow with multiple jurisdictions
- Multi-phase application process with interdependent deliverables
- Stakeholder coordination across regulatory bodies and internal teams
- Risk management and compliance framework implementation
- Operational readiness assessment and capital structure planning
"""

from manager_agent_gym.schemas.agents import AIAgentConfig, HumanAgentConfig


def create_banking_license_team_configs():
    """Create AI and human mock agent configurations for Banking License Application."""

    # Regulatory and Legal Specialists
    regulatory_strategist = AIAgentConfig(
        agent_id="regulatory_strategist",
        agent_type="ai",
        system_prompt=(
            "You are a Regulatory Strategy Expert specializing in US banking regulations, OCC requirements, "
            "Federal Reserve coordination, and multi-jurisdiction regulatory navigation for foreign bank market entry."
        ),
        agent_description="Regulatory Strategy Expert",
        agent_capabilities=[
            "Specializes in US banking regulations",
            "Specializes in OCC requirements",
            "Specializes in Federal Reserve coordination",
            "Specializes in multi-jurisdiction regulatory navigation",
        ],
    )

    legal_counsel = AIAgentConfig(
        agent_id="legal_counsel",
        agent_type="ai",
        system_prompt=(
            "You are Legal Counsel focusing on banking law, regulatory compliance, corporate structure, "
            "and legal documentation for federal branch establishment and licensing."
        ),
        agent_description="Legal Counsel",
        agent_capabilities=[
            "Focuses on banking law",
            "Focuses on regulatory compliance",
            "Focuses on corporate structure",
            "Focuses on legal documentation",
        ],
    )

    compliance_specialist = AIAgentConfig(
        agent_id="compliance_specialist",
        agent_type="ai",
        system_prompt=(
            "You are a Compliance Specialist expert in AML/BSA programs, customer identification procedures, "
            "enhanced due diligence, and US banking compliance framework implementation."
        ),
        agent_description="Compliance Specialist",
        agent_capabilities=[
            "Specializes in AML/BSA programs",
            "Specializes in customer identification procedures",
            "Specializes in enhanced due diligence",
            "Specializes in US banking compliance framework implementation",
        ],
    )

    # Risk Management and Financial Specialists
    risk_manager = AIAgentConfig(
        agent_id="risk_manager",
        agent_type="ai",
        system_prompt=(
            "You are a Risk Management Specialist developing comprehensive risk frameworks including "
            "credit risk policies, market risk controls, operational risk assessment, and liquidity management."
        ),
        agent_description="Risk Management Specialist",
        agent_capabilities=[
            "Specializes in credit risk policies",
            "Specializes in market risk controls",
            "Specializes in operational risk assessment",
            "Specializes in liquidity management",
        ],
    )

    capital_structuring_analyst = AIAgentConfig(
        agent_id="capital_structuring_analyst",
        agent_type="ai",
        system_prompt=(
            "You are a Capital Structuring Analyst managing $50M minimum capital requirements, "
            "CED arrangements, funding strategy, and regulatory capital adequacy documentation."
        ),
        agent_description="Capital Structuring Analyst",
        agent_capabilities=[
            "Manages $50M minimum capital requirements",
            "Manages CED arrangements",
            "Manages funding strategy",
            "Manages regulatory capital adequacy documentation",
        ],
    )

    financial_analyst = AIAgentConfig(
        agent_id="financial_analyst",
        agent_type="ai",
        system_prompt=(
            "You are a Financial Analyst preparing business plans, financial projections, "
            "market analysis, and revenue forecasting for US market entry strategy."
        ),
        agent_description="Financial Analyst",
        agent_capabilities=[
            "Prepares business plans",
            "Prepares financial projections",
            "Prepares market analysis",
            "Prepares revenue forecasting",
        ],
    )

    # Operations and Technology Specialists
    operations_manager = AIAgentConfig(
        agent_id="operations_manager",
        agent_type="ai",
        system_prompt=(
            "You are an Operations Manager responsible for operational readiness including IT infrastructure, "
            "correspondent banking relationships, physical office setup, and service delivery capabilities."
        ),
        agent_description="Operations Manager",
        agent_capabilities=[
            "Responsible for operational readiness",
            "Responsible for IT infrastructure",
            "Responsible for correspondent banking relationships",
            "Responsible for physical office setup",
            "Responsible for service delivery capabilities",
        ],
    )

    technology_architect = AIAgentConfig(
        agent_id="technology_architect",
        agent_type="ai",
        system_prompt=(
            "You are a Technology Architect designing core banking systems, security infrastructure, "
            "regulatory reporting capabilities, and IT compliance framework implementation."
        ),
        agent_description="Technology Architect",
        agent_capabilities=[
            "Designs core banking systems",
            "Designs security infrastructure",
            "Designs regulatory reporting capabilities",
            "Designs IT compliance framework implementation",
        ],
    )

    hr_specialist = AIAgentConfig(
        agent_id="hr_specialist",
        agent_type="ai",
        system_prompt=(
            "You are an HR Specialist managing staffing plans, senior management recruitment, "
            "background checks, training programs, and human resources policy development."
        ),
        agent_description="HR Specialist",
        agent_capabilities=[
            "Manages staffing plans",
            "Manages senior management recruitment",
            "Manages background checks",
            "Manages training programs",
            "Manages human resources policy development",
        ],
    )

    # Business Development and Strategy
    business_development_lead = AIAgentConfig(
        agent_id="business_development_lead",
        agent_type="ai",
        system_prompt=(
            "You are a Business Development Lead developing US market entry strategy, competitive analysis, "
            "target customer segments, product offerings, and growth strategy implementation."
        ),
        agent_description="Business Development Lead",
        agent_capabilities=[
            "Develops US market entry strategy",
            "Develops competitive analysis",
            "Develops target customer segments",
            "Develops product offerings",
            "Develops growth strategy implementation",
        ],
    )

    project_coordinator = AIAgentConfig(
        agent_id="project_coordinator",
        agent_type="ai",
        system_prompt=(
            "You are a Project Coordinator managing overall project timeline, stakeholder coordination, "
            "milestone tracking, and ensuring regulatory approval process stays on 18-24 month timeline."
        ),
        agent_description="Project Coordinator",
        agent_capabilities=[
            "Manages overall project timeline",
            "Manages stakeholder coordination",
            "Manages milestone tracking",
            "Ensures regulatory approval process stays on 18-24 month timeline",
        ],
    )

    # Human Mock Agents - Regulatory and Approval Authorities
    occ_examiner = HumanAgentConfig(
        agent_id="occ_examiner",
        agent_type="human_mock",
        system_prompt="OCC examiner reviewing federal branch license application for completeness and regulatory compliance.",
        name="OCC Bank Examiner",
        role="Federal Regulator",
        experience_years=12,
        background="Banking supervision and regulation",
        agent_description="OCC Bank Examiner",
        agent_capabilities=[
            "Reviews federal branch license application for completeness and regulatory compliance"
        ],
    )

    federal_reserve_supervisor = HumanAgentConfig(
        agent_id="federal_reserve_supervisor",
        agent_type="human_mock",
        system_prompt="Federal Reserve supervisor coordinating international banking supervision and Regulation K compliance.",
        name="Federal Reserve Supervisor",
        role="Central Bank Supervisor",
        experience_years=15,
        background="International banking supervision",
        agent_description="Federal Reserve Supervisor",
        agent_capabilities=[
            "Coordinates international banking supervision and Regulation K compliance"
        ],
    )

    home_country_regulator = HumanAgentConfig(
        agent_id="home_country_regulator",
        agent_type="human_mock",
        system_prompt="ECB/national authority supervisor approving US market expansion and coordinating supervision.",
        name="ECB Supervisor",
        role="Home Country Regulator",
        experience_years=14,
        background="Cross-border banking supervision",
        agent_description="ECB Supervisor",
        agent_capabilities=[
            "Approves US market expansion and coordinates cross-border banking supervision"
        ],
    )

    # Human Mock Agents - Internal Governance and Approval
    board_chair = HumanAgentConfig(
        agent_id="board_chair",
        agent_type="human_mock",
        system_prompt="Board Chair providing strategic oversight and final board approval for US market entry initiative.",
        name="Board Chair",
        role="Board Leadership",
        experience_years=20,
        background="Banking executive leadership",
        agent_description="Board Chair",
        agent_capabilities=[
            "Provides strategic oversight and final board approval for US market entry initiative"
        ],
    )

    chief_risk_officer = HumanAgentConfig(
        agent_id="chief_risk_officer",
        agent_type="human_mock",
        system_prompt="Chief Risk Officer approving risk management framework and ensuring risk appetite alignment.",
        name="Chief Risk Officer",
        role="Senior Risk Executive",
        experience_years=18,
        background="Banking risk management",
        agent_description="Chief Risk Officer",
        agent_capabilities=[
            "Validates risk management framework and ensures risk appetite alignment"
        ],
    )

    chief_compliance_officer = HumanAgentConfig(
        agent_id="chief_compliance_officer",
        agent_type="human_mock",
        system_prompt="Chief Compliance Officer validating compliance framework and regulatory readiness.",
        name="Chief Compliance Officer",
        role="Senior Compliance Executive",
        experience_years=16,
        background="Banking compliance and regulation",
        agent_description="Chief Compliance Officer",
        agent_capabilities=["Validates compliance framework and regulatory readiness"],
    )

    internal_audit_director = HumanAgentConfig(
        agent_id="internal_audit_director",
        agent_type="human_mock",
        system_prompt="Internal Audit Director reviewing controls, governance, and process adequacy.",
        name="Internal Audit Director",
        role="Internal Audit",
        experience_years=14,
        background="Banking audit and controls",
        agent_description="Internal Audit Director",
        agent_capabilities=["Reviews controls, governance, and process adequacy"],
    )

    # Human Mock Agents - External Specialists and Validators
    external_legal_advisor = HumanAgentConfig(
        agent_id="external_legal_advisor",
        agent_type="human_mock",
        system_prompt="External legal advisor specializing in US banking law and regulatory applications.",
        name="External Legal Advisor",
        role="Banking Law Specialist",
        experience_years=22,
        background="US banking regulation and law",
        agent_description="External Legal Advisor",
        agent_capabilities=[
            "Specializes in US banking law and regulatory applications"
        ],
    )

    independent_consultant = HumanAgentConfig(
        agent_id="independent_consultant",
        agent_type="human_mock",
        system_prompt="Independent banking consultant providing objective review and regulatory expertise.",
        name="Independent Banking Consultant",
        role="Regulatory Consultant",
        experience_years=25,
        background="Banking regulation and consulting",
        agent_description="Independent Banking Consultant",
        agent_capabilities=["Provides objective review and regulatory expertise"],
    )

    third_party_validator = HumanAgentConfig(
        agent_id="third_party_validator",
        agent_type="human_mock",
        system_prompt="Third-party validator conducting independent assessment of operational readiness and compliance.",
        name="Third-Party Validator",
        role="Independent Validator",
        experience_years=12,
        background="Banking operations and compliance validation",
        agent_description="Third-Party Validator",
        agent_capabilities=[
            "Conducts independent assessment of operational readiness and compliance"
        ],
    )

    return {
        # AI Agents - Core Team
        "regulatory_strategist": regulatory_strategist,
        "legal_counsel": legal_counsel,
        "compliance_specialist": compliance_specialist,
        "risk_manager": risk_manager,
        "capital_structuring_analyst": capital_structuring_analyst,
        "financial_analyst": financial_analyst,
        "operations_manager": operations_manager,
        "technology_architect": technology_architect,
        "hr_specialist": hr_specialist,
        "business_development_lead": business_development_lead,
        "project_coordinator": project_coordinator,
        # Human Mock Agents - Regulatory Authorities
        "occ_examiner": occ_examiner,
        "federal_reserve_supervisor": federal_reserve_supervisor,
        "home_country_regulator": home_country_regulator,
        # Human Mock Agents - Internal Governance
        "board_chair": board_chair,
        "chief_risk_officer": chief_risk_officer,
        "chief_compliance_officer": chief_compliance_officer,
        "internal_audit_director": internal_audit_director,
        # Human Mock Agents - External Specialists
        "external_legal_advisor": external_legal_advisor,
        "independent_consultant": independent_consultant,
        "third_party_validator": third_party_validator,
    }


def create_banking_license_team_timeline():
    """Create phased team coordination timeline for Banking License Application."""

    cfg = create_banking_license_team_configs()
    return {
        # Phase 1: Initial Strategy and Foundation (Timesteps 0-10)
        0: [
            (
                "add",
                cfg["regulatory_strategist"],
                "Regulatory strategy and feasibility assessment",
            ),
            (
                "add",
                cfg["legal_counsel"],
                "Legal structure and documentation framework",
            ),
            ("add", cfg["project_coordinator"], "Project management and coordination"),
            (
                "add",
                cfg["external_legal_advisor"],
                "Legal advisory and regulatory guidance",
            ),
        ],
        # Phase 2: Application Preparation (Timesteps 5-15)
        5: [
            (
                "add",
                cfg["financial_analyst"],
                "Business plan and financial documentation",
            ),
            (
                "add",
                cfg["compliance_specialist"],
                "Due diligence and background verification",
            ),
            ("add", cfg["capital_structuring_analyst"], "Capital structure planning"),
        ],
        # Phase 3: Regulatory Engagement (Timesteps 10-20)
        10: [
            ("add", cfg["home_country_regulator"], "ECB/home supervisor coordination"),
            ("add", cfg["independent_consultant"], "Independent regulatory expertise"),
        ],
        # Phase 4: Framework Development (Timesteps 15-25)
        15: [
            ("add", cfg["risk_manager"], "Risk management framework development"),
            ("add", cfg["operations_manager"], "Operational infrastructure planning"),
            ("add", cfg["technology_architect"], "IT systems and infrastructure"),
        ],
        # Phase 5: Operational Readiness (Timesteps 20-30)
        20: [
            ("add", cfg["hr_specialist"], "Staffing and human resources"),
            ("add", cfg["business_development_lead"], "Market entry strategy"),
            ("add", cfg["chief_risk_officer"], "Risk framework validation"),
        ],
        # Phase 6: Regulatory Review Phase (Timesteps 25-35)
        25: [
            ("add", cfg["occ_examiner"], "OCC application review"),
            ("add", cfg["federal_reserve_supervisor"], "Federal Reserve coordination"),
            ("add", cfg["chief_compliance_officer"], "Compliance framework validation"),
        ],
        # Phase 7: Internal Governance and Validation (Timesteps 30-40)
        30: [
            (
                "add",
                cfg["internal_audit_director"],
                "Internal audit and controls review",
            ),
            (
                "add",
                cfg["third_party_validator"],
                "Independent operational readiness validation",
            ),
        ],
        # Phase 8: Final Approval Phase (Timesteps 35-45)
        35: [
            ("add", cfg["board_chair"], "Board oversight and final approval"),
        ],
    }
