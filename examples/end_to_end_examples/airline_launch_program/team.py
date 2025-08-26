"""
Airline Launch Program Demo

Real-world use case: UK airline startup securing AOC and Operating Licence.

Demonstrates:
- Multi-track regulatory certification coordination with critical path dependencies
- Complex aviation safety and security compliance management under CAA oversight
- Resource-constrained project execution with parallel workstream management
- Stakeholder coordination across aviation authorities, lessors, airports, and service providers
- Risk-based decision making in heavily regulated industry with safety-critical requirements
- Escalation management for regulatory findings and compliance gaps
"""

from manager_agent_gym.schemas.workflow_agents import (
    AIAgentConfig,
    HumanAgentConfig,
)


def create_team_configs():
    """Create AI and human mock agent configurations for Airline Launch Program."""

    # AI Agents for specialist aviation tasks
    flight_operations_specialist = AIAgentConfig(
        agent_id="flight_operations_specialist",
        agent_type="ai",
        system_prompt=(
            "You are a Flight Operations Specialist developing Operations Manual sections (OM-A/B/C/D), "
            "flight procedures, crew training programs, and operational control systems."
        ),
        agent_description="Flight Operations Specialist",
        agent_capabilities=[
            "Develops Operations Manual sections",
            "Develops flight procedures",
            "Develops crew training programs",
            "Develops operational control systems",
        ],
    )
    safety_management_specialist = AIAgentConfig(
        agent_id="safety_management_specialist",
        agent_type="ai",
        system_prompt=(
            "You are a Safety Management Specialist implementing SMS compliant with ICAO Annex 19, "
            "developing safety policy, risk management processes, and safety assurance systems."
        ),
        agent_description="Safety Management Specialist",
        agent_capabilities=[
            "Develops safety policy",
            "Develops risk management processes",
            "Develops safety assurance systems",
        ],
    )
    airworthiness_manager = AIAgentConfig(
        agent_id="airworthiness_manager",
        agent_type="ai",
        system_prompt=(
            "You are an Airworthiness Manager establishing CAMO arrangements, Part-145 contracts, "
            "maintenance programs, and continuing airworthiness management compliance."
        ),
        agent_description="Airworthiness Manager",
        agent_capabilities=[
            "Develops CAMO arrangements",
            "Develops Part-145 contracts",
            "Develops maintenance programs",
            "Develops continuing airworthiness management compliance",
        ],
    )
    aviation_security_specialist = AIAgentConfig(
        agent_id="aviation_security_specialist",
        agent_type="ai",
        system_prompt=(
            "You are an Aviation Security Specialist developing airline security programmes under NASP, "
            "managing staff vetting, security training, and screening equipment arrangements."
        ),
        agent_description="Aviation Security Specialist",
        agent_capabilities=[
            "Develops aviation security programmes",
            "Develops staff vetting",
            "Develops security training",
            "Develops screening equipment arrangements",
        ],
    )
    regulatory_affairs_manager = AIAgentConfig(
        agent_id="regulatory_affairs_manager",
        agent_type="ai",
        system_prompt=(
            "You are a Regulatory Affairs Manager coordinating AOC and Operating Licence applications, "
            "managing CAA liaison, inspection support, and regulatory compliance activities."
        ),
        agent_description="Regulatory Affairs Manager",
        agent_capabilities=[
            "Coordinates AOC and Operating Licence applications",
            "Manages CAA liaison",
            "Manages inspection support",
            "Manages regulatory compliance activities",
        ],
    )
    financial_compliance_analyst = AIAgentConfig(
        agent_id="financial_compliance_analyst",
        agent_type="ai",
        system_prompt=(
            "You are a Financial Compliance Analyst preparing financial fitness documentation, "
            "securing insurance coverage, and managing financial monitoring systems."
        ),
        agent_description="Financial Compliance Analyst",
        agent_capabilities=[
            "Prepares financial fitness documentation",
            "Secures insurance coverage",
            "Manages financial monitoring systems",
        ],
    )
    airport_operations_coordinator = AIAgentConfig(
        agent_id="airport_operations_coordinator",
        agent_type="ai",
        system_prompt=(
            "You coordinate airport operations including slot management, ground handling contracts, "
            "disruption management plans, and passenger rights compliance."
        ),
        agent_description="Airport Operations Coordinator",
        agent_capabilities=[
            "Coordinates airport operations including slot management",
            "Coordinates ground handling contracts",
            "Coordinates disruption management plans",
            "Coordinates passenger rights compliance",
        ],
    )
    training_standards_manager = AIAgentConfig(
        agent_id="training_standards_manager",
        agent_type="ai",
        system_prompt=(
            "You are a Training Standards Manager developing OM-D training programs, competency standards, "
            "crew checking requirements, and training delivery systems."
        ),
        agent_description="Training Standards Manager",
        agent_capabilities=[
            "Develops OM-D training programs",
            "Develops competency standards",
            "Develops crew checking requirements",
            "Develops training delivery systems",
        ],
    )

    # Human Mock Agents for approvals and oversight
    caa_principal_inspector = HumanAgentConfig(
        agent_id="caa_principal_inspector",
        agent_type="human_mock",
        system_prompt="CAA Principal Inspector responsible for AOC certification oversight, inspection coordination, and regulatory approval decisions.",
        name="CAA Principal Inspector",
        role="Regulatory Authority",
        experience_years=20,
        background="Aviation regulatory oversight and certification",
        agent_description="CAA Principal Inspector",
        agent_capabilities=[
            "Oversees AOC certification oversight",
            "Oversees inspection coordination",
            "Oversees regulatory approval decisions",
        ],
    )
    chief_pilot = HumanAgentConfig(
        agent_id="chief_pilot",
        agent_type="human_mock",
        system_prompt="Chief Pilot (nominated postholder) responsible for flight operations oversight, pilot training approval, and operational safety.",
        name="Chief Pilot",
        role="Flight Operations Postholder",
        experience_years=15,
        background="Commercial aviation and flight operations management",
        agent_description="Chief Pilot",
        agent_capabilities=[
            "Oversees flight operations oversight",
            "Oversees pilot training approval",
            "Oversees operational safety",
        ],
    )
    head_of_safety = HumanAgentConfig(
        agent_id="head_of_safety",
        agent_type="human_mock",
        system_prompt="Head of Safety (nominated postholder) responsible for SMS oversight, safety risk management, and safety culture development.",
        name="Head of Safety",
        role="Safety Management Postholder",
        experience_years=12,
        background="Aviation safety management and risk assessment",
        agent_description="Head of Safety",
        agent_capabilities=[
            "Oversees SMS oversight",
            "Oversees safety risk management",
            "Oversees safety culture development",
        ],
    )
    continuing_airworthiness_manager = HumanAgentConfig(
        agent_id="continuing_airworthiness_manager",
        agent_type="human_mock",
        system_prompt="Continuing Airworthiness Manager (nominated postholder) responsible for CAMO oversight and airworthiness compliance.",
        name="Continuing Airworthiness Manager",
        role="Airworthiness Postholder",
        experience_years=18,
        background="Aircraft maintenance and airworthiness management",
        agent_description="Continuing Airworthiness Manager",
        agent_capabilities=[
            "Oversees CAMO oversight",
            "Oversees airworthiness compliance",
        ],
    )
    head_of_training = HumanAgentConfig(
        agent_id="head_of_training",
        agent_type="human_mock",
        system_prompt="Head of Training (nominated postholder) responsible for crew training program oversight and competency validation.",
        name="Head of Training",
        role="Training Postholder",
        experience_years=14,
        background="Aviation training and crew development",
        agent_description="Head of Training",
        agent_capabilities=[
            "Oversees crew training program oversight",
            "Oversees competency validation",
        ],
    )
    security_manager = HumanAgentConfig(
        agent_id="security_manager",
        agent_type="human_mock",
        system_prompt="Security Manager (nominated postholder) responsible for aviation security programme and NASP compliance oversight.",
        name="Security Manager",
        role="Security Postholder",
        experience_years=10,
        background="Aviation security and threat assessment",
        agent_description="Security Manager",
        agent_capabilities=["Oversees aviation security programme and NASP compliance"],
    )
    ground_operations_manager = HumanAgentConfig(
        agent_id="ground_operations_manager",
        agent_type="human_mock",
        system_prompt="Ground Operations Manager (nominated postholder) responsible for ground operations oversight and airport coordination.",
        name="Ground Operations Manager",
        role="Ground Operations Postholder",
        experience_years=12,
        background="Airport operations and ground handling management",
        agent_description="Ground Operations Manager",
        agent_capabilities=[
            "Oversees ground operations oversight",
            "Oversees airport coordination",
        ],
    )
    aviation_legal_counsel = HumanAgentConfig(
        agent_id="aviation_legal_counsel",
        agent_type="human_mock",
        system_prompt="Aviation Legal Counsel providing regulatory compliance advice, contract review, and legal risk management.",
        name="Aviation Legal Counsel",
        role="Legal Advisory",
        experience_years=16,
        background="Aviation law and regulatory compliance",
        agent_description="Aviation Legal Counsel",
        agent_capabilities=[
            "Provides regulatory compliance advice",
            "Reviews contracts",
            "Manages legal risk",
        ],
    )
    cfo_finance_director = HumanAgentConfig(
        agent_id="cfo_finance_director",
        agent_type="human_mock",
        system_prompt="CFO/Finance Director responsible for financial fitness demonstration, insurance arrangements, and financial controls.",
        name="CFO/Finance Director",
        role="Financial Leadership",
        experience_years=18,
        background="Aviation finance and insurance management",
        agent_description="CFO/Finance Director",
        agent_capabilities=[
            "Demonstrates financial fitness",
            "Arranges insurance",
            "Manages financial controls",
        ],
    )
    accountable_manager = HumanAgentConfig(
        agent_id="accountable_manager",
        agent_type="human_mock",
        system_prompt="Accountable Manager providing ultimate responsibility for airline operations, safety, and regulatory compliance.",
        name="Accountable Manager",
        role="Executive Leadership",
        experience_years=25,
        background="Airline management and aviation operations",
        agent_description="Accountable Manager",
        agent_capabilities=[
            "Provides ultimate responsibility for airline operations",
            "Ensures safety and regulatory compliance",
        ],
    )

    return {
        "flight_operations_specialist": flight_operations_specialist,
        "safety_management_specialist": safety_management_specialist,
        "airworthiness_manager": airworthiness_manager,
        "aviation_security_specialist": aviation_security_specialist,
        "regulatory_affairs_manager": regulatory_affairs_manager,
        "financial_compliance_analyst": financial_compliance_analyst,
        "airport_operations_coordinator": airport_operations_coordinator,
        "training_standards_manager": training_standards_manager,
        "caa_principal_inspector": caa_principal_inspector,
        "chief_pilot": chief_pilot,
        "head_of_safety": head_of_safety,
        "continuing_airworthiness_manager": continuing_airworthiness_manager,
        "head_of_training": head_of_training,
        "security_manager": security_manager,
        "ground_operations_manager": ground_operations_manager,
        "aviation_legal_counsel": aviation_legal_counsel,
        "cfo_finance_director": cfo_finance_director,
        "accountable_manager": accountable_manager,
    }


def create_team_timeline():
    """Create phased coordination timeline for Airline Launch Program certification."""

    cfg = create_team_configs()
    return {
        0: [
            (
                "add",
                cfg["flight_operations_specialist"],
                "Operations Manual development",
            ),
            ("add", cfg["safety_management_specialist"], "SMS implementation"),
            (
                "add",
                cfg["regulatory_affairs_manager"],
                "Regulatory coordination and foundation",
            ),
        ],
        5: [
            (
                "add",
                cfg["airworthiness_manager"],
                "CAMO and airworthiness arrangements",
            ),
            ("add", cfg["aviation_security_specialist"], "Aviation security programme"),
            (
                "add",
                cfg["financial_compliance_analyst"],
                "Financial fitness and insurance",
            ),
        ],
        10: [
            ("add", cfg["training_standards_manager"], "Training program development"),
            (
                "add",
                cfg["airport_operations_coordinator"],
                "Airport operations and slot coordination",
            ),
        ],
        15: [
            ("add", cfg["chief_pilot"], "Flight operations oversight"),
            ("add", cfg["head_of_safety"], "Safety management oversight"),
            ("add", cfg["continuing_airworthiness_manager"], "Airworthiness oversight"),
        ],
        20: [
            ("add", cfg["head_of_training"], "Training program validation"),
            ("add", cfg["security_manager"], "Security programme oversight"),
            ("add", cfg["ground_operations_manager"], "Ground operations validation"),
        ],
        25: [
            ("add", cfg["caa_principal_inspector"], "CAA inspection and certification"),
            ("add", cfg["aviation_legal_counsel"], "Legal compliance review"),
        ],
        30: [
            ("add", cfg["cfo_finance_director"], "Financial fitness validation"),
        ],
        35: [
            (
                "add",
                cfg["accountable_manager"],
                "Final accountability and launch approval",
            ),
        ],
    }
