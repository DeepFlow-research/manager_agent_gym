from manager_agent_gym.schemas.agents import AIAgentConfig, HumanAgentConfig


def create_brand_crisis_management_team_configs():
    """Create AI and human mock agent configurations for brand crisis management."""

    crisis_communications_lead = AIAgentConfig(
        agent_id="crisis_communications_lead",
        agent_type="ai",
        system_prompt=(
            "You are a Crisis Communications Lead specializing in messaging framework development, "
            "multi-channel communication strategy, and brand voice preservation during crisis situations."
        ),
        agent_description="Crisis Communications Lead",
        agent_capabilities=[
            "Develops messaging framework",
            "Develops multi-channel communication strategy",
            "Preserves brand voice during crisis",
        ],
    )
    social_media_manager = AIAgentConfig(
        agent_id="social_media_manager",
        agent_type="ai",
        system_prompt=(
            "You are a Social Media Manager handling real-time social media response, sentiment monitoring, "
            "and platform-specific crisis communications with consistency across channels."
        ),
        agent_description="Social Media Manager",
        agent_capabilities=[
            "Handles real-time social media response",
            "Monitors sentiment",
            "Maintains platform consistency",
        ],
    )
    stakeholder_relations_manager = AIAgentConfig(
        agent_id="stakeholder_relations_manager",
        agent_type="ai",
        system_prompt=(
            "You manage stakeholder relations including customer retention, employee communications, "
            "investor relations, and partner notifications during crisis events."
        ),
        agent_description="Stakeholder Relations Manager",
        agent_capabilities=[
            "Manages customer retention",
            "Manages employee communications",
            "Manages investor relations",
            "Manages partner notifications",
        ],
    )
    media_relations_specialist = AIAgentConfig(
        agent_id="media_relations_specialist",
        agent_type="ai",
        system_prompt=(
            "You handle traditional media relations including press releases, journalist relationships, "
            "spokesperson coordination, and narrative control efforts."
        ),
        agent_description="Media Relations Specialist",
        agent_capabilities=[
            "Handles traditional media relations",
            "Manages journalist relationships",
            "Coordinates spokesperson activities",
            "Controls narrative during crisis",
        ],
    )
    crisis_analyst = AIAgentConfig(
        agent_id="crisis_analyst",
        agent_type="ai",
        system_prompt=(
            "You are a Crisis Analyst conducting situation assessment, stakeholder impact analysis, "
            "financial impact quantification, and competitive landscape evaluation."
        ),
        agent_description="Crisis Analyst",
        agent_capabilities=[
            "Conducts situation assessment",
            "Analyzes stakeholder impact",
            "Quantifies financial impact",
            "Evaluates competitive landscape",
        ],
    )
    customer_service_coordinator = AIAgentConfig(
        agent_id="customer_service_coordinator",
        agent_type="ai",
        system_prompt=(
            "You coordinate customer service enhancement, develop crisis-specific scripts, "
            "and implement customer retention and compensation programs."
        ),
        agent_description="Customer Service Coordinator",
        agent_capabilities=[
            "Enhances customer service",
            "Develops crisis-specific scripts",
            "Implements customer retention and compensation programs",
        ],
    )
    digital_reputation_manager = AIAgentConfig(
        agent_id="digital_reputation_manager",
        agent_type="ai",
        system_prompt=(
            "You manage digital reputation recovery including SEO optimization, positive content creation, "
            "online review management, and influencer engagement strategies."
        ),
        agent_description="Digital Reputation Manager",
        agent_capabilities=[
            "Manages digital reputation recovery",
            "Optimizes SEO",
            "Creates positive content",
            "Manages online review management",
            "Engages influencers",
        ],
    )
    crisis_legal_counsel = AIAgentConfig(
        agent_id="crisis_legal_counsel",
        agent_type="ai",
        system_prompt=(
            "You provide legal guidance during crisis including risk assessment, regulatory compliance, "
            "documentation requirements, and litigation preparedness."
        ),
        agent_description="Crisis Legal Counsel",
        agent_capabilities=[
            "Provides legal guidance during crisis",
            "Assesses risk",
            "Ensures regulatory compliance",
            "Prepares litigation",
        ],
    )

    # Human sign-offs and leadership
    chief_executive_officer = HumanAgentConfig(
        agent_id="chief_executive_officer",
        agent_type="human_mock",
        system_prompt="CEO providing executive leadership, final decision authority, and external representation during crisis.",
        name="Chief Executive Officer",
        role="Executive Leadership",
        experience_years=20,
        background="Corporate leadership and crisis management",
        agent_description="Chief Executive Officer",
        agent_capabilities=[
            "Provides executive leadership",
            "Makes final decisions",
            "Represents the company externally",
        ],
    )
    chief_marketing_officer = HumanAgentConfig(
        agent_id="chief_marketing_officer",
        agent_type="human_mock",
        system_prompt="CMO overseeing brand protection, marketing strategy adjustments, and reputation recovery efforts.",
        name="Chief Marketing Officer",
        role="Brand Leadership",
        experience_years=15,
        background="Brand management and marketing communications",
        agent_description="Chief Marketing Officer",
        agent_capabilities=[
            "Oversees brand protection",
            "Adjusts marketing strategy",
            "Manages reputation recovery efforts",
        ],
    )
    chief_legal_officer = HumanAgentConfig(
        agent_id="chief_legal_officer",
        agent_type="human_mock",
        system_prompt="CLO ensuring legal compliance, risk mitigation, and regulatory requirements are met.",
        name="Chief Legal Officer",
        role="Legal Leadership",
        experience_years=18,
        background="Corporate law and regulatory compliance",
        agent_description="Chief Legal Officer",
        agent_capabilities=[
            "Ensures legal compliance",
            "Mitigates risk",
            "Meets regulatory requirements",
        ],
    )
    public_relations_director = HumanAgentConfig(
        agent_id="public_relations_director",
        agent_type="human_mock",
        system_prompt="PR Director leading external communications, media strategy, and spokesperson activities.",
        name="Public Relations Director",
        role="External Communications",
        experience_years=12,
        background="Public relations and crisis communications",
        agent_description="Public Relations Director",
        agent_capabilities=[
            "Leads external communications",
            "Manages media strategy",
            "Coordinates spokesperson activities",
        ],
    )
    human_resources_director = HumanAgentConfig(
        agent_id="human_resources_director",
        agent_type="human_mock",
        system_prompt="HR Director managing internal communications, employee morale, and workforce retention during crisis.",
        name="Human Resources Director",
        role="Internal Stakeholder Management",
        experience_years=14,
        background="Human resources and organizational development",
        agent_description="Human Resources Director",
        agent_capabilities=[
            "Manages internal communications",
            "Manages employee morale",
            "Manages workforce retention",
        ],
    )
    investor_relations_director = HumanAgentConfig(
        agent_id="investor_relations_director",
        agent_type="human_mock",
        system_prompt="IR Director maintaining investor confidence, providing transparent updates, and managing financial communications.",
        name="Investor Relations Director",
        role="Financial Communications",
        experience_years=10,
        background="Financial communications and investor relations",
        agent_description="Investor Relations Director",
        agent_capabilities=[
            "Maintains investor confidence",
            "Provides transparent updates",
            "Manages financial communications",
        ],
    )
    operations_director = HumanAgentConfig(
        agent_id="operations_director",
        agent_type="human_mock",
        system_prompt="Operations Director ensuring business continuity, supply chain stability, and operational crisis response.",
        name="Operations Director",
        role="Business Continuity",
        experience_years=16,
        background="Operations management and business continuity",
        agent_description="Operations Director",
        agent_capabilities=[
            "Ensures business continuity",
            "Manages supply chain stability",
            "Responds to operational crises",
        ],
    )
    brand_consultant = HumanAgentConfig(
        agent_id="external_brand_consultant",
        agent_type="human_mock",
        system_prompt="External brand consultant providing independent perspective, crisis strategy validation, and reputation recovery expertise.",
        name="External Brand Consultant",
        role="Strategic Advisory",
        experience_years=22,
        background="Brand consulting and crisis recovery",
        agent_description="External Brand Consultant",
        agent_capabilities=[
            "Provides independent perspective",
            "Validates crisis strategy",
            "Expertise in reputation recovery",
        ],
    )

    return {
        "crisis_communications_lead": crisis_communications_lead,
        "social_media_manager": social_media_manager,
        "stakeholder_relations_manager": stakeholder_relations_manager,
        "media_relations_specialist": media_relations_specialist,
        "crisis_analyst": crisis_analyst,
        "customer_service_coordinator": customer_service_coordinator,
        "digital_reputation_manager": digital_reputation_manager,
        "crisis_legal_counsel": crisis_legal_counsel,
        "chief_executive_officer": chief_executive_officer,
        "chief_marketing_officer": chief_marketing_officer,
        "chief_legal_officer": chief_legal_officer,
        "public_relations_director": public_relations_director,
        "human_resources_director": human_resources_director,
        "investor_relations_director": investor_relations_director,
        "operations_director": operations_director,
        "brand_consultant": brand_consultant,
    }


def create_brand_crisis_management_team_timeline():
    """Create crisis response coordination timeline for brand crisis management."""

    cfg = create_brand_crisis_management_team_configs()
    return {
        0: [
            (
                "add",
                cfg["crisis_communications_lead"],
                "Crisis communications strategy",
            ),
            ("add", cfg["crisis_analyst"], "Situation assessment and impact analysis"),
            ("add", cfg["chief_executive_officer"], "Executive crisis leadership"),
            ("add", cfg["chief_marketing_officer"], "Brand protection oversight"),
        ],
        2: [
            ("add", cfg["social_media_manager"], "Real-time social media response"),
            (
                "add",
                cfg["media_relations_specialist"],
                "Media relations and press response",
            ),
            (
                "add",
                cfg["public_relations_director"],
                "External communications leadership",
            ),
        ],
        4: [
            (
                "add",
                cfg["stakeholder_relations_manager"],
                "Multi-stakeholder coordination",
            ),
            (
                "add",
                cfg["customer_service_coordinator"],
                "Customer service enhancement",
            ),
            ("add", cfg["crisis_legal_counsel"], "Legal risk assessment"),
            ("add", cfg["chief_legal_officer"], "Legal compliance oversight"),
        ],
        6: [
            (
                "add",
                cfg["human_resources_director"],
                "Internal communications and employee relations",
            ),
            (
                "add",
                cfg["investor_relations_director"],
                "Investor confidence management",
            ),
            ("add", cfg["operations_director"], "Business continuity assurance"),
        ],
        10: [
            ("add", cfg["digital_reputation_manager"], "Digital reputation recovery"),
            ("add", cfg["brand_consultant"], "Strategic crisis advisory"),
        ],
    }
