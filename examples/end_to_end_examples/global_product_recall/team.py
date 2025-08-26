"""
Global Product Recall & Market Re-entry Strategy Demo
Real-world use case: Automotive safety component recall affecting 2M vehicles
across 15 countries with comprehensive remediation and market re-entry.
Demonstrates:
- Crisis decision-making under extreme time pressure with safety-first prioritization
- Multi-stakeholder coordination across regulatory authorities, consumers, and supply chains
- Dynamic preference evolution from crisis response to recovery optimization
- Complex parallel task management with interdependent global operations
- Executive escalation protocols with documented decision authority under uncertainty
- Adaptive resource allocation balancing immediate response with long-term recovery
"""

from manager_agent_gym.schemas.workflow_agents import AIAgentConfig, HumanAgentConfig


def create_team_configs():
    """Create AI and human mock agent configurations for Global Product Recall."""

    # Crisis Response and Safety Specialists
    crisis_coordinator = AIAgentConfig(
        agent_id="crisis_coordinator",
        agent_type="ai",
        system_prompt=(
            "You are a Crisis Management Coordinator responsible for 24/7 crisis operations, "
            "emergency response coordination, and executive escalation protocols under extreme time pressure."
        ),
        agent_description=(
            "Coordinator who stands up 24/7 crisis ops, enforces escalation, and keeps decision logs crisp."
        ),
        agent_capabilities=[
            "Runs crisis operations cadence",
            "Coordinates emergency response",
            "Manages executive escalations",
            "Maintains decision/owner/ETA logs",
        ],
    )

    safety_engineer = AIAgentConfig(
        agent_id="safety_engineer",
        agent_type="ai",
        system_prompt=(
            "You are a Product Safety Engineer conducting immediate safety assessments, defect characterization, "
            "risk analysis, and technical failure investigation for automotive components."
        ),
        agent_description=(
            "Engineer who quickly characterizes defects and quantifies safety risk to drive decisions."
        ),
        agent_capabilities=[
            "Performs safety assessments",
            "Investigates failure modes",
            "Analyzes risk and mitigations",
            "Reports safety findings",
        ],
    )

    quality_assurance_specialist = AIAgentConfig(
        agent_id="quality_assurance_specialist",
        agent_type="ai",
        system_prompt=(
            "You are a Quality Assurance Specialist implementing root cause analysis, design modifications, "
            "enhanced testing protocols, and supplier quality improvements."
        ),
        agent_description=(
            "QA specialist who leads root cause and hardens quality with better tests and supplier oversight."
        ),
        agent_capabilities=[
            "Runs root cause analysis",
            "Implements design modifications",
            "Enhances testing protocols",
            "Improves supplier quality",
        ],
    )

    # Regulatory and Compliance Specialists
    regulatory_affairs_manager = AIAgentConfig(
        agent_id="regulatory_affairs_manager",
        agent_type="ai",
        system_prompt=(
            "You are a Regulatory Affairs Manager coordinating multi-jurisdiction regulatory filings "
            "across NHTSA, Transport Canada, EU GPSR, and 15 national authorities with synchronized timelines."
        ),
        agent_description=(
            "Regulatory lead who synchronizes filings across authorities and keeps timings aligned."
        ),
        agent_capabilities=[
            "Coordinates multi‑jurisdiction filings",
            "Tracks timelines and dependencies",
            "Aligns with authorities",
            "Prepares regulator communications",
        ],
    )

    compliance_coordinator = AIAgentConfig(
        agent_id="compliance_coordinator",
        agent_type="ai",
        system_prompt=(
            "You are a Compliance Coordinator managing recall effectiveness monitoring, consumer response tracking, "
            "and regulatory status reporting across all markets targeting >95% completion rates."
        ),
        agent_description=(
            "Coordinator who drives completion rates and keeps regulators and consumers informed."
        ),
        agent_capabilities=[
            "Monitors recall effectiveness",
            "Tracks consumer responses",
            "Produces status reports",
            "Targets >95% completion",
        ],
    )

    # Consumer Communication and Public Relations
    communications_director = AIAgentConfig(
        agent_id="communications_director",
        agent_type="ai",
        system_prompt=(
            "You are a Communications Director managing crisis communication strategy, consumer safety notifications, "
            "media relations, and multi-channel stakeholder communication across global markets."
        ),
        agent_description=(
            "Communications lead who manages multi‑channel messages that are accurate and reassuring."
        ),
        agent_capabilities=[
            "Runs crisis comms strategy",
            "Drafts consumer safety notifications",
            "Handles media relations",
            "Coordinates stakeholder communication",
        ],
    )

    customer_service_manager = AIAgentConfig(
        agent_id="customer_service_manager",
        agent_type="ai",
        system_prompt=(
            "You are a Customer Service Manager deploying 24/7 customer hotlines, online portals, "
            "and customer return processing systems for global recall operations."
        ),
        agent_description=(
            "Service leader who scales inbound channels and smoothes returns at peak load."
        ),
        agent_capabilities=[
            "Deploys hotlines and portals",
            "Runs return processing systems",
            "Tracks SLAs and satisfaction",
            "Feeds learnings to ops",
        ],
    )

    # Operations and Logistics Specialists
    logistics_coordinator = AIAgentConfig(
        agent_id="logistics_coordinator",
        agent_type="ai",
        system_prompt=(
            "You are a Logistics Coordinator managing global reverse supply chain operations, "
            "dealer network coordination, and product retrieval across 15 countries."
        ),
        agent_description=(
            "Logistics planner who orchestrates global reverse supply chains under pressure."
        ),
        agent_capabilities=[
            "Manages reverse logistics",
            "Coordinates dealer networks",
            "Plans retrieval across countries",
            "Resolves operational bottlenecks",
        ],
    )

    supply_chain_manager = AIAgentConfig(
        agent_id="supply_chain_manager",
        agent_type="ai",
        system_prompt=(
            "You are a Supply Chain Manager implementing inventory quarantine, disposal protocols, "
            "and supplier coordination while maintaining partner relationships."
        ),
        agent_description=(
            "Supply chain lead who quarantines inventory and keeps partners aligned and safe."
        ),
        agent_capabilities=[
            "Implements quarantine/disposal",
            "Coordinates suppliers",
            "Maintains partner relationships",
            "Audits process compliance",
        ],
    )

    # Legal and Financial Specialists
    legal_counsel = AIAgentConfig(
        agent_id="legal_counsel",
        agent_type="ai",
        system_prompt=(
            "You are Legal Counsel managing multi-jurisdiction liability, litigation strategy development, "
            "and legal risk mitigation across 15 countries for product recall operations."
        ),
        agent_description=(
            "Counsel who manages liability and litigation risk while enabling decisive action."
        ),
        agent_capabilities=[
            "Assesses multi‑jurisdiction liability",
            "Guides litigation strategy",
            "Drafts legal communications",
            "Balances risk vs action",
        ],
    )

    financial_analyst = AIAgentConfig(
        agent_id="financial_analyst",
        agent_type="ai",
        system_prompt=(
            "You are a Financial Analyst managing crisis budget parameters, insurance claims processing, "
            "and financial impact containment for global recall operations."
        ),
        agent_description=(
            "Analyst who contains financial impact and optimizes insurance recovery."
        ),
        agent_capabilities=[
            "Manages crisis budget",
            "Processes insurance claims",
            "Tracks financial KPIs",
            "Models impact scenarios",
        ],
    )

    # Brand Recovery and Market Re-entry
    brand_manager = AIAgentConfig(
        agent_id="brand_manager",
        agent_type="ai",
        system_prompt=(
            "You are a Brand Manager developing customer confidence rebuilding campaigns, "
            "competitive repositioning strategy, and brand reputation recovery targeting >80% confidence restoration."
        ),
        agent_description=(
            "Brand leader who rebuilds trust with credible actions and clear messaging."
        ),
        agent_capabilities=[
            "Designs confidence rebuilding campaigns",
            "Plans competitive repositioning",
            "Coordinates recovery communications",
            "Measures trust restoration",
        ],
    )

    market_reentry_strategist = AIAgentConfig(
        agent_id="market_reentry_strategist",
        agent_type="ai",
        system_prompt=(
            "You are a Market Re-entry Strategist coordinating product redesign validation, "
            "regulatory approvals for sales resumption, and enhanced quality assurance protocols."
        ),
        agent_description=(
            "Strategist who choreographs the path back to market with validated fixes."
        ),
        agent_capabilities=[
            "Coordinates redesign validation",
            "Secures approvals for resumption",
            "Enhances QA protocols",
            "Stages re‑entry by market",
        ],
    )

    # Human Mock Agents - Regulatory Authorities
    nhtsa_examiner = HumanAgentConfig(
        agent_id="nhtsa_examiner",
        agent_type="human_mock",
        system_prompt="NHTSA examiner reviewing automotive safety defect reports and recall effectiveness for US market.",
        name="NHTSA Safety Examiner",
        role="US Safety Regulator",
        experience_years=15,
        background="Automotive safety regulation",
        agent_description=(
            "US regulator who reviews defect reports and validates recall effectiveness."
        ),
        agent_capabilities=[
            "Reviews defect reports",
            "Assesses recall effectiveness",
            "Issues findings/requirements",
            "Coordinates with manufacturer",
        ],
    )

    transport_canada_official = HumanAgentConfig(
        agent_id="transport_canada_official",
        agent_type="human_mock",
        system_prompt="Transport Canada official coordinating Canadian market recall approval and monitoring.",
        name="Transport Canada Official",
        role="Canadian Safety Regulator",
        experience_years=12,
        background="Transportation safety regulation",
        agent_description=(
            "Canadian regulator who coordinates approval and monitoring."
        ),
        agent_capabilities=[
            "Coordinates Canadian approvals",
            "Monitors compliance",
            "Communicates updates",
            "Engages with stakeholders",
        ],
    )

    eu_gpsr_coordinator = HumanAgentConfig(
        agent_id="eu_gpsr_coordinator",
        agent_type="human_mock",
        system_prompt="EU GPSR coordinator managing European market recall coordination and compliance validation.",
        name="EU GPSR Coordinator",
        role="European Safety Regulator",
        experience_years=14,
        background="European product safety regulation",
        agent_description=(
            "EU coordinator who ensures GPSR compliance and oversight across member states."
        ),
        agent_capabilities=[
            "Oversees EU coordination",
            "Validates compliance",
            "Tracks status across markets",
            "Aligns messaging and actions",
        ],
    )

    # Human Mock Agents - Executive Leadership and Governance
    ceo = HumanAgentConfig(
        agent_id="ceo",
        agent_type="human_mock",
        system_prompt="Chief Executive Officer providing ultimate crisis decision authority and stakeholder communication.",
        name="Chief Executive Officer",
        role="Executive Leadership",
        experience_years=25,
        background="Executive leadership and crisis management",
        agent_description=(
            "Chief executive who sets priorities, communicates externally, and owns final decisions."
        ),
        agent_capabilities=[
            "Sets crisis priorities",
            "Communicates to stakeholders",
            "Approves major decisions",
            "Allocates resources",
        ],
    )

    chief_safety_officer = HumanAgentConfig(
        agent_id="chief_safety_officer",
        agent_type="human_mock",
        system_prompt="Chief Safety Officer ensuring consumer safety prioritization and safety protocol compliance.",
        name="Chief Safety Officer",
        role="Safety Leadership",
        experience_years=20,
        background="Product safety and risk management",
        agent_description=(
            "Safety leader who keeps consumer protection paramount and protocols enforced."
        ),
        agent_capabilities=[
            "Oversees safety protocols",
            "Validates corrective actions",
            "Tracks incidents",
            "Approves safety sign‑offs",
        ],
    )

    general_counsel = HumanAgentConfig(
        agent_id="general_counsel",
        agent_type="human_mock",
        system_prompt="General Counsel approving legal strategy and managing liability exposure across jurisdictions.",
        name="General Counsel",
        role="Legal Leadership",
        experience_years=18,
        background="Corporate law and litigation",
        agent_description=(
            "General Counsel who approves legal strategy and manages liability exposure."
        ),
        agent_capabilities=[
            "Approves legal strategy",
            "Manages liability exposure",
            "Coordinates multi‑jurisdiction issues",
            "Oversees documentation",
        ],
    )

    chief_financial_officer = HumanAgentConfig(
        agent_id="chief_financial_officer",
        agent_type="human_mock",
        system_prompt="Chief Financial Officer approving crisis budget and managing financial impact containment.",
        name="Chief Financial Officer",
        role="Financial Leadership",
        experience_years=22,
        background="Corporate finance and crisis management",
        agent_description=(
            "CFO who approves crisis budget and steers financial impact containment."
        ),
        agent_capabilities=[
            "Approves crisis budget",
            "Tracks financial impact",
            "Optimizes insurance/claims",
            "Reports to board and regulators",
        ],
    )

    # Human Mock Agents - Independent Validation and External Stakeholders
    independent_safety_auditor = HumanAgentConfig(
        agent_id="independent_safety_auditor",
        agent_type="human_mock",
        system_prompt="Independent safety auditor validating recall effectiveness and safety remediation measures.",
        name="Independent Safety Auditor",
        role="Independent Validation",
        experience_years=16,
        background="Automotive safety auditing",
        agent_description=(
            "Independent validator who pressure‑tests recall effectiveness."
        ),
        agent_capabilities=[
            "Validates remediation effectiveness",
            "Runs independent checks",
            "Issues findings",
            "Recommends improvements",
        ],
    )

    insurance_adjuster = HumanAgentConfig(
        agent_id="insurance_adjuster",
        agent_type="human_mock",
        system_prompt="Insurance adjuster processing recall-related claims and coverage optimization.",
        name="Insurance Adjuster",
        role="Insurance Representative",
        experience_years=10,
        background="Product liability insurance",
        agent_description=(
            "Adjuster who expedites valid claims and optimizes coverage use."
        ),
        agent_capabilities=[
            "Processes claims",
            "Coordinates with insurers",
            "Documents coverage decisions",
            "Advises finance on recovery",
        ],
    )

    consumer_advocacy_representative = HumanAgentConfig(
        agent_id="consumer_advocacy_representative",
        agent_type="human_mock",
        system_prompt="Consumer advocacy representative ensuring consumer protection and recall effectiveness.",
        name="Consumer Advocacy Representative",
        role="Consumer Protection",
        experience_years=12,
        background="Consumer protection and advocacy",
        agent_description=(
            "Advocate who ensures consumer protections are real and visible."
        ),
        agent_capabilities=[
            "Represents consumer interests",
            "Validates effectiveness measures",
            "Provides feedback to improve",
            "Monitors outreach quality",
        ],
    )

    board_chair = HumanAgentConfig(
        agent_id="board_chair",
        agent_type="human_mock",
        system_prompt="Board Chair providing governance oversight and final approval for major crisis decisions.",
        name="Board Chair",
        role="Board Governance",
        experience_years=30,
        background="Corporate governance and crisis oversight",
        agent_description=(
            "Board leader who provides governance oversight and final approvals."
        ),
        agent_capabilities=[
            "Chairs crisis board sessions",
            "Approves major crisis actions",
            "Ensures governance documentation",
            "Holds executives accountable",
        ],
    )

    return {
        # AI Agents - Crisis Response and Operations
        "crisis_coordinator": crisis_coordinator,
        "safety_engineer": safety_engineer,
        "quality_assurance_specialist": quality_assurance_specialist,
        "regulatory_affairs_manager": regulatory_affairs_manager,
        "compliance_coordinator": compliance_coordinator,
        "communications_director": communications_director,
        "customer_service_manager": customer_service_manager,
        "logistics_coordinator": logistics_coordinator,
        "supply_chain_manager": supply_chain_manager,
        "legal_counsel": legal_counsel,
        "financial_analyst": financial_analyst,
        "brand_manager": brand_manager,
        "market_reentry_strategist": market_reentry_strategist,
        # Human Mock Agents - Regulatory Authorities
        "nhtsa_examiner": nhtsa_examiner,
        "transport_canada_official": transport_canada_official,
        "eu_gpsr_coordinator": eu_gpsr_coordinator,
        # Human Mock Agents - Executive Leadership
        "ceo": ceo,
        "chief_safety_officer": chief_safety_officer,
        "general_counsel": general_counsel,
        "chief_financial_officer": chief_financial_officer,
        # Human Mock Agents - Independent Validation and External
        "independent_safety_auditor": independent_safety_auditor,
        "insurance_adjuster": insurance_adjuster,
        "consumer_advocacy_representative": consumer_advocacy_representative,
        "board_chair": board_chair,
    }


def create_team_timeline():
    """Create crisis-phased coordination timeline for Global Product Recall."""

    cfg = create_team_configs()
    return {
        # Phase 1: Immediate Crisis Response (0-72 hours)
        0: [
            ("add", cfg["crisis_coordinator"], "Crisis management coordination"),
            ("add", cfg["safety_engineer"], "Immediate safety assessment"),
            (
                "add",
                cfg["regulatory_affairs_manager"],
                "Emergency regulatory notifications",
            ),
            ("add", cfg["ceo"], "Executive crisis authority"),
        ],
        # Phase 2: Crisis Team Expansion (Hours 24-72)
        1: [
            ("add", cfg["communications_director"], "Crisis communication strategy"),
            ("add", cfg["legal_counsel"], "Legal risk assessment"),
            ("add", cfg["chief_safety_officer"], "Safety oversight authority"),
        ],
        # Phase 3: Consumer Communication Launch (Days 3-7)
        3: [
            ("add", cfg["customer_service_manager"], "Customer service infrastructure"),
            ("add", cfg["compliance_coordinator"], "Regulatory compliance monitoring"),
            ("add", cfg["general_counsel"], "Legal strategy approval"),
        ],
        # Phase 4: Regulatory Authority Engagement (Days 5-14)
        5: [
            ("add", cfg["nhtsa_examiner"], "US regulatory review"),
            (
                "add",
                cfg["transport_canada_official"],
                "Canadian regulatory coordination",
            ),
            ("add", cfg["eu_gpsr_coordinator"], "European regulatory oversight"),
        ],
        # Phase 5: Operations and Logistics Deployment (Weeks 2-4)
        8: [
            ("add", cfg["logistics_coordinator"], "Global logistics coordination"),
            ("add", cfg["supply_chain_manager"], "Supply chain operations"),
            ("add", cfg["financial_analyst"], "Financial impact management"),
        ],
        # Phase 6: Root Cause and Quality (Weeks 3-8)
        12: [
            ("add", cfg["quality_assurance_specialist"], "Root cause analysis"),
            ("add", cfg["chief_financial_officer"], "Financial oversight"),
        ],
        # Phase 7: Independent Validation and External Stakeholders (Weeks 8-16)
        20: [
            ("add", cfg["independent_safety_auditor"], "Independent safety validation"),
            ("add", cfg["insurance_adjuster"], "Insurance claims processing"),
            (
                "add",
                cfg["consumer_advocacy_representative"],
                "Consumer protection oversight",
            ),
        ],
        # Phase 8: Brand Recovery and Market Re-entry (Weeks 16-24)
        30: [
            ("add", cfg["brand_manager"], "Brand recovery strategy"),
            ("add", cfg["market_reentry_strategist"], "Market re-entry planning"),
        ],
        # Phase 9: Final Governance and Approval (Weeks 20-26)
        40: [
            ("add", cfg["board_chair"], "Board governance and final approvals"),
        ],
    }
