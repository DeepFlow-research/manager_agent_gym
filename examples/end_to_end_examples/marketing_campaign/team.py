"""
Renewable Energy – Integrated Marketing Campaign
Team personas (AI + human) and a timestep-based scheduling map.

Mirrors the schema style used in existing examples:
  - AIAgentConfig / HumanAgentConfig / optional StakeholderConfig
  - Timeline: Dict[int, List[Tuple[action, agent_cfg, rationale]]]

Exports:
  - create_renewables_marketing_team_configs()
  - create_renewables_marketing_team_timeline()
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
    """Create AI and human mock agent configurations for the renewables campaign."""

    # ===== AI Agents =====
    campaign_planner_ai = AIAgentConfig(
        agent_id="campaign_planner_ai",
        agent_type="ai",
        system_prompt=(
            "You are an AI Campaign Planner. Translate research and messaging into a channel plan and flighting calendar, "
            "maintain a living risk/dependency register, and propose weekly reallocations backed by performance signals."
        ),
        agent_description=(
            "Planner who keeps the campaign coherent, evidence‑driven, and adaptable week to week."
        ),
        agent_capabilities=[
            "Translates research to channel plan",
            "Maintains risk/dependency register",
            "Proposes weekly reallocations",
            "Tracks performance signals and trade‑offs",
        ],
    )

    creative_director_ai = AIAgentConfig(
        agent_id="creative_director_ai",
        agent_type="ai",
        system_prompt=(
            "You generate creative territories, briefs, and variant matrices aligned to the messaging house; "
            "enforce brand voice and inclusive tone across assets."
        ),
        agent_description=(
            "Creative partner who turns strategy into territories and briefs that scale across channels."
        ),
        agent_capabilities=[
            "Generates territories and briefs",
            "Enforces brand voice and inclusion",
            "Curates variant matrices",
            "Reviews creative for coherence",
        ],
    )

    copy_optimizer_ai = AIAgentConfig(
        agent_id="copy_optimizer_ai",
        agent_type="ai",
        system_prompt=(
            "You produce channel-specific copy variants (search, social, display, email) and run hypothesis-driven A/B tests; "
            "ensure claims align with the substantiation playbook."
        ),
        agent_description=(
            "Optimizer who ships clean variants and hardens copy through disciplined testing."
        ),
        agent_capabilities=[
            "Drafts channel‑specific variants",
            "Runs A/B tests with hypotheses",
            "Checks claims against substantiation",
            "Feeds learnings back to creative",
        ],
    )

    seo_analyst_ai = AIAgentConfig(
        agent_id="seo_analyst_ai",
        agent_type="ai",
        system_prompt=(
            "You create the SEO roadmap: keyword clusters, pillar/topic pages, internal links, and structured data; "
            "deliver a content backlog tied to ICP pain points."
        ),
        agent_description=(
            "SEO builder who aligns content to demand and makes the site discoverable and structured."
        ),
        agent_capabilities=[
            "Creates keyword clusters and pillars",
            "Plans internal links and schema",
            "Builds content backlog",
            "Aligns with ICP pain points",
        ],
    )

    media_buyer_ai = AIAgentConfig(
        agent_id="media_buyer_ai",
        agent_type="ai",
        system_prompt=(
            "You manage paid search/social/display setup, budgets, frequency caps, audience definitions, and brand safety lists; "
            "run canary rollouts and scale winners."
        ),
        agent_description=(
            "Buyer who paces budgets prudently, respects brand safety, and scales winners."
        ),
        agent_capabilities=[
            "Configures platforms and budgets",
            "Sets frequency caps and audiences",
            "Runs canary rollouts",
            "Scales winners and prunes waste",
        ],
    )

    analytics_ai = AIAgentConfig(
        agent_id="analytics_ai",
        agent_type="ai",
        system_prompt=(
            "You define KPI specs, UTM governance, event schemas; build an executive dashboard and alerting; "
            "produce weekly readouts and experiment design checks."
        ),
        agent_description=(
            "Analyst who puts measurement on rails and produces decision‑ready readouts."
        ),
        agent_capabilities=[
            "Defines KPIs and event schemas",
            "Implements dashboards and alerts",
            "Designs experiments",
            "Publishes weekly readouts",
        ],
    )

    consent_compliance_ai = AIAgentConfig(
        agent_id="consent_compliance_ai",
        agent_type="ai",
        system_prompt=(
            "You enforce privacy-by-design for marketing: CMP setup, granular opt-ins, data minimization, and audit trails; "
            "monitor for green claims compliance coordination with Legal Marketing."
        ),
        agent_description=(
            "Privacy guardian who keeps consent and minimization in place across all touchpoints."
        ),
        agent_capabilities=[
            "Configures CMP and opt‑ins",
            "Enforces minimization and audit trails",
            "Monitors compliance for green claims",
            "Coordinates with legal marketing",
        ],
    )

    accessibility_checker_ai = AIAgentConfig(
        agent_id="accessibility_checker_ai",
        agent_type="ai",
        system_prompt=(
            "You perform automated accessibility checks (contrast, alt text, captions) and flag copy for plain-language improvements; "
            "ensure WCAG 2.1 AA for web and key assets."
        ),
        agent_description=(
            "Accessibility sentinel who reduces friction for users and keeps assets compliant."
        ),
        agent_capabilities=[
            "Checks contrast/alt/captions",
            "Flags plain‑language fixes",
            "Tracks WCAG 2.1 AA compliance",
            "Coordinates remediation",
        ],
    )

    crm_ops_ai = AIAgentConfig(
        agent_id="crm_ops_ai",
        agent_type="ai",
        system_prompt=(
            "You configure lead scoring, routing, deduplication, and enrichment; track SLAs and feedback loops to Sales and Community Ops."
        ),
        agent_description=(
            "Revops enabler who keeps the data clean and routes leads quickly and fairly."
        ),
        agent_capabilities=[
            "Configures scoring and routing",
            "Deduplicates and enriches",
            "Tracks SLAs",
            "Closes feedback loops",
        ],
    )

    social_listener_ai = AIAgentConfig(
        agent_id="social_listener_ai",
        agent_type="ai",
        system_prompt=(
            "You monitor social/press signals, competitor moves, and sentiment; summarize insights for rapid creative and budget pivots."
        ),
        agent_description=(
            "Signal scout who finds shifts in sentiment and competition early."
        ),
        agent_capabilities=[
            "Monitors sentiment and competitor moves",
            "Summarizes insights",
            "Triggers budget/creative pivots",
            "Feeds learning back to planners",
        ],
    )

    # ===== Human Mock Agents =====
    cmo = HumanAgentConfig(
        agent_id="cmo",
        agent_type="human_mock",
        system_prompt=(
            "Chief Marketing Officer: sets campaign objectives, approves budgets, and arbitrates trade-offs "
            "between speed, brand quality, and compliance."
        ),
        name="Chief Marketing Officer",
        role="Executive Stakeholder",
        experience_years=18,
        background="Brand + growth leadership in energy/tech",
        agent_description=(
            "Executive who calibrates speed, brand quality, and compliance, and holds the team accountable."
        ),
        agent_capabilities=[
            "Sets objectives and KPIs",
            "Approves budgets and trade‑offs",
            "Chairs reviews and sign‑offs",
            "Balances speed/brand/compliance",
        ],
    )

    vp_marketing = HumanAgentConfig(
        agent_id="vp_marketing",
        agent_type="human_mock",
        system_prompt=(
            "Owns cross-channel plan, staffing, and weekly readouts; accountable for pipeline and brand KPIs."
        ),
        name="VP Marketing",
        role="LT Member",
        experience_years=14,
        background="Integrated marketing; B2B & B2C energy",
        agent_description=(
            "Operator who builds the team plan, cadence, and weekly readouts to drive pipeline and brand."
        ),
        agent_capabilities=[
            "Owns channel staffing and cadence",
            "Publishes weekly readouts",
            "Aligns pipeline and brand goals",
            "Escalates risks and decisions",
        ],
    )

    brand_creative_director = HumanAgentConfig(
        agent_id="brand_creative_director",
        agent_type="human_mock",
        system_prompt=(
            "Leads creative territories, narrative, and asset QA; co-owns brand approvals with Legal Marketing."
        ),
        name="Brand Creative Director",
        role="Creative Lead",
        experience_years=12,
        background="Brand systems; climate storytelling",
        agent_description=(
            "Creative leader who maintains brand integrity and approves high‑impact assets."
        ),
        agent_capabilities=[
            "Approves territories and assets",
            "Enforces brand and inclusive tone",
            "Partners with Legal on approvals",
            "Curates design quality",
        ],
    )

    performance_media_manager = HumanAgentConfig(
        agent_id="performance_media_manager",
        agent_type="human_mock",
        system_prompt=(
            "Owns paid budgets, platform ops, and pacing; enforces brand safety and flighting guardrails."
        ),
        name="Performance Media Manager",
        role="Paid Media",
        experience_years=8,
        background="Paid search/social/display; MMM-aware ops",
        agent_description=(
            "Buyer/ops lead who keeps spend efficient and brand‑safe across platforms."
        ),
        agent_capabilities=[
            "Owns platform setup and pacing",
            "Enforces brand safety",
            "Optimizes budgets",
            "Manages flighting",
        ],
    )

    web_lead = HumanAgentConfig(
        agent_id="web_lead",
        agent_type="human_mock",
        system_prompt=(
            "Owns LP builds, analytics implementation, CMP integration, and accessibility compliance."
        ),
        name="Web Experience Lead",
        role="Web/Conversion",
        experience_years=9,
        background="CRO + analytics; accessibility",
        agent_description=(
            "Web owner who ships accessible, measurable experiences that convert."
        ),
        agent_capabilities=[
            "Builds LPs and analytics",
            "Integrates CMP/accessibility",
            "Coordinates QA and releases",
            "Tracks conversion and fixes",
        ],
    )

    crm_lifecycle_manager = HumanAgentConfig(
        agent_id="crm_lifecycle_manager",
        agent_type="human_mock",
        system_prompt=(
            "Owns lifecycle design, deliverability, and preference center; collaborates with Sales/Community Ops."
        ),
        name="CRM & Lifecycle Manager",
        role="Lifecycle/Email",
        experience_years=7,
        background="CRM, deliverability, consent ops",
        agent_description=(
            "Lifecycle owner who ensures deliverability and respectful, effective nurture."
        ),
        agent_capabilities=[
            "Designs lifecycle journeys",
            "Maintains deliverability",
            "Runs preference center",
            "Aligns with Sales/Community",
        ],
    )

    pr_lead = HumanAgentConfig(
        agent_id="pr_lead",
        agent_type="human_mock",
        system_prompt=(
            "Owns PR/analyst relations; develops press kit, handles briefings, and coverage tracking."
        ),
        name="PR Lead",
        role="PR/AR",
        experience_years=10,
        background="Energy/tech PR and analyst relations",
        agent_description=(
            "PR lead who secures accurate coverage and prepares spokespeople."
        ),
        agent_capabilities=[
            "Builds press kit and briefings",
            "Runs interviews/analyst relations",
            "Monitors coverage",
            "Coordinates with legal marketing",
        ],
    )

    events_manager = HumanAgentConfig(
        agent_id="events_manager",
        agent_type="human_mock",
        system_prompt=(
            "Owns event kits, webinar production, staffing, and logistics with lead-capture compliance."
        ),
        name="Events & Field Manager",
        role="Events",
        experience_years=8,
        background="Industry events, webinars, field ops",
        agent_description=(
            "Producer who ships smooth events with compliant lead capture."
        ),
        agent_capabilities=[
            "Runs event/webinar production",
            "Staffs and equips teams",
            "Ensures compliant capture",
            "Closes loop with sales",
        ],
    )

    partnerships_manager = HumanAgentConfig(
        agent_id="partnerships_manager",
        agent_type="human_mock",
        system_prompt=(
            "Leads co-marketing with installers/finance/local programs; coordinates MDF and partner approvals."
        ),
        name="Partnerships Manager",
        role="Alliances/Partners",
        experience_years=9,
        background="Channel/alliances; co-marketing",
        agent_description=(
            "Alliances lead who amplifies reach via partners without compromising brand or compliance."
        ),
        agent_capabilities=[
            "Leads co‑marketing and MDF",
            "Coordinates partner approvals",
            "Aligns claims and assets",
            "Reports partner impact",
        ],
    )

    data_analyst = HumanAgentConfig(
        agent_id="data_analyst",
        agent_type="human_mock",
        system_prompt=(
            "Builds dashboards, QA analytics, designs experiments, and assists MMM/MTA alignment."
        ),
        name="Marketing Data Analyst",
        role="Analytics",
        experience_years=6,
        background="Attribution & experimentation",
        agent_description=(
            "Analyst who gets the right numbers to the right forums to drive decisions."
        ),
        agent_capabilities=[
            "Builds dashboards",
            "Runs attribution/experiments",
            "QA’s analytics",
            "Provides insights and guardrails",
        ],
    )

    legal_marketing_counsel = HumanAgentConfig(
        agent_id="legal_marketing_counsel",
        agent_type="human_mock",
        system_prompt=(
            "Advises on environmental claims substantiation and privacy; reviews partner co-branding and PR."
        ),
        name="Legal Marketing Counsel",
        role="Legal (Marketing)",
        experience_years=11,
        background="Advertising/consumer protection; privacy",
        agent_description=(
            "Counsel who keeps claims truthful and privacy‑safe across assets and partners."
        ),
        agent_capabilities=[
            "Reviews claims and disclosures",
            "Approves co‑branding and PR",
            "Advises on privacy/consent",
            "Tracks approvals and exceptions",
        ],
    )

    accessibility_specialist = HumanAgentConfig(
        agent_id="accessibility_specialist",
        agent_type="human_mock",
        system_prompt=(
            "Conducts manual WCAG 2.1 AA reviews and remediation guidance for key assets and flows."
        ),
        name="Accessibility Specialist",
        role="Accessibility",
        experience_years=8,
        background="WCAG audits, inclusive design",
        agent_description=(
            "Expert who ensures AA compliance and reduces friction for users with disabilities."
        ),
        agent_capabilities=[
            "Conducts manual WCAG audits",
            "Guides remediation",
            "Validates alt/captions/contrast",
            "Documents conformance",
        ],
    )

    sustainability_officer = HumanAgentConfig(
        agent_id="sustainability_officer",
        agent_type="human_mock",
        system_prompt=(
            "Validates environmental metrics (RECs, LCA references) for claims substantiation."
        ),
        name="Sustainability Officer",
        role="Sustainability",
        experience_years=13,
        background="ESG reporting; renewables",
        agent_description=(
            "Officer who validates environmental claims with credible metrics and sources."
        ),
        agent_capabilities=[
            "Validates REC/LCA references",
            "Approves green claims",
            "Maintains evidence register",
            "Advises messaging house",
        ],
    )

    sales_director = HumanAgentConfig(
        agent_id="sales_director",
        agent_type="human_mock",
        system_prompt=(
            "Aligns MQL definitions, routing SLAs, and feedback loops; ensures B2B pipeline velocity."
        ),
        name="Sales Director (B2B)",
        role="Sales",
        experience_years=15,
        background="C&I and utility sales",
        agent_description=(
            "Sales leader who aligns pipeline definitions and keeps velocity high."
        ),
        agent_capabilities=[
            "Aligns MQL/SQL definitions",
            "Sets routing SLAs",
            "Closes sales feedback loop",
            "Tracks velocity",
        ],
    )

    community_ops_manager = HumanAgentConfig(
        agent_id="community_ops_manager",
        agent_type="human_mock",
        system_prompt=(
            "Supports B2C community energy enrollments; manages support flows and compliance notices."
        ),
        name="Community Ops Manager",
        role="Community/B2C Ops",
        experience_years=7,
        background="Consumer ops; regulated programs",
        agent_description=(
            "Ops manager who scales support and compliance for community enrollments."
        ),
        agent_capabilities=[
            "Designs support flows",
            "Ensures compliance notices",
            "Coordinates with partners",
            "Reports enrollment KPIs",
        ],
    )

    # Optional explicit stakeholder (CMO) with initial preference snapshot
    stakeholder = StakeholderConfig(
        agent_id="cmo_stakeholder",
        agent_type="stakeholder",
        system_prompt=(
            "You are the CMO. Early phase: prioritize speed to launch. Mid: emphasize creative/brand quality and "
            "measurement integrity. Late: emphasize compliance and accessibility as reach scales."
        ),
        model_name="o3",
        name="CMO Stakeholder",
        role="Executive",
        persona_description="Outcome-driven, brand-minded, privacy-conscious; expects crisp weekly readouts.",
        agent_description=(
            "CMO who balances launch velocity with brand integrity and privacy."
        ),
        agent_capabilities=[
            "Sets pace and quality bars",
            "Approves budgets and exceptions",
            "Chairs weekly decision forums",
            "Holds teams to measurement discipline",
        ],
        response_latency_steps_min=1,
        response_latency_steps_max=3,
        push_probability_per_timestep=0.12,
        suggestion_rate=0.55,
        clarification_reply_rate=0.9,
        strictness=0.6,
        verbosity=2,
        initial_preferences=PreferenceWeights(
            preferences=[
                Preference(name="speed", weight=0.5),
                Preference(name="quality", weight=0.3),
                Preference(name="compliance", weight=0.2),
            ]
        ),
    )

    return {
        # AI
        "campaign_planner_ai": campaign_planner_ai,
        "creative_director_ai": creative_director_ai,
        "copy_optimizer_ai": copy_optimizer_ai,
        "seo_analyst_ai": seo_analyst_ai,
        "media_buyer_ai": media_buyer_ai,
        "analytics_ai": analytics_ai,
        "consent_compliance_ai": consent_compliance_ai,
        "accessibility_checker_ai": accessibility_checker_ai,
        "crm_ops_ai": crm_ops_ai,
        "social_listener_ai": social_listener_ai,
        # Human
        "cmo": cmo,
        "vp_marketing": vp_marketing,
        "brand_creative_director": brand_creative_director,
        "performance_media_manager": performance_media_manager,
        "web_lead": web_lead,
        "crm_lifecycle_manager": crm_lifecycle_manager,
        "pr_lead": pr_lead,
        "events_manager": events_manager,
        "partnerships_manager": partnerships_manager,
        "data_analyst": data_analyst,
        "legal_marketing_counsel": legal_marketing_counsel,
        "accessibility_specialist": accessibility_specialist,
        "sustainability_officer": sustainability_officer,
        "sales_director": sales_director,
        "community_ops_manager": community_ops_manager,
        # Stakeholder
        "stakeholder": stakeholder,
    }


# ---------------------------
# TEAM TIMELINE
# ---------------------------
def create_team_timeline():
    """
    Timestep → [(action, agent_cfg, rationale)]
    Actions: "add" or "remove".
    """
    cfg = create_team_configs()

    return {
        0: [
            ("add", cfg["cmo"], "Set objectives, budget guardrails, and KPIs"),
            ("add", cfg["vp_marketing"], "Stand up cadence and org plan"),
            (
                "add",
                cfg["campaign_planner_ai"],
                "Translate research to initial channel plan",
            ),
            ("add", cfg["analytics_ai"], "Define KPIs, UTM, dashboards"),
            ("add", cfg["consent_compliance_ai"], "Embed privacy-by-design up front"),
            (
                "add",
                cfg["social_listener_ai"],
                "Baseline sentiment and competitor activity",
            ),
        ],
        5: [
            ("add", cfg["seo_analyst_ai"], "SEO roadmap; inform content pillars"),
            ("add", cfg["brand_creative_director"], "Approve messaging territories"),
            (
                "add",
                cfg["legal_marketing_counsel"],
                "Review green claims substantiation approach",
            ),
        ],
        10: [
            ("add", cfg["creative_director_ai"], "Creative territories + briefs"),
            ("add", cfg["copy_optimizer_ai"], "Variant copy and A/B hypotheses"),
            ("add", cfg["web_lead"], "LP build plan and analytics mapping"),
        ],
        14: [
            ("add", cfg["accessibility_checker_ai"], "WCAG checks for assets and LPs"),
            ("add", cfg["crm_ops_ai"], "Scoring/routing/dedup config"),
            ("add", cfg["sustainability_officer"], "Validate metrics for claims"),
        ],
        18: [
            ("add", cfg["pr_lead"], "Press/analyst briefing program"),
            ("add", cfg["events_manager"], "Event/webinar plan and kits"),
            ("add", cfg["partnerships_manager"], "Partner co-marketing planning"),
        ],
        20: [
            ("add", cfg["performance_media_manager"], "Platform setup and pacing"),
            ("add", cfg["media_buyer_ai"], "Automate budgets, caps, and QA"),
            ("add", cfg["brand_creative_director"], "Final creative approvals"),
        ],
        22: [
            (
                "add",
                cfg["crm_lifecycle_manager"],
                "Nurture sequences and deliverability",
            ),
            ("add", cfg["sales_director"], "B2B pipeline SLA alignment"),
            ("add", cfg["community_ops_manager"], "B2C enrollment support alignment"),
        ],
        28: [
            ("add", cfg["data_analyst"], "Executive dashboard & analysis cadence"),
            (
                "remove",
                cfg["seo_analyst_ai"],
                "Initial roadmap delivered; ongoing items via planner",
            ),
        ],
        35: [
            (
                "add",
                cfg["analytics_ai"],
                "Experiment design reviews and MMM/MTA alignment",
            ),
            (
                "add",
                cfg["campaign_planner_ai"],
                "Weekly reallocation proposals based on results",
            ),
        ],
        45: [
            ("add", cfg["accessibility_specialist"], "Manual AA audit during scale-up"),
            (
                "remove",
                cfg["copy_optimizer_ai"],
                "Creative variants stabilized; focus on scaling",
            ),
        ],
        55: [
            (
                "remove",
                cfg["media_buyer_ai"],
                "Automation steady-state; human pacing sufficient",
            ),
            ("add", cfg["vp_marketing"], "Transition to wrap-up and learnings"),
        ],
    }
