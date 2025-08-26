"""
Legal M&A – Mid‑Market Tech Acquisition
Team personas (AI + human) and an ad‑hoc timeline with join/leave events.

Mirrors the schema style in the examples:
  - AIAgentConfig / HumanAgentConfig instances collected into a dict factory
  - A discrete‑timestep schedule mapping {int: List[Tuple[action, agent_cfg, rationale]]}

Exported helpers:
  - create_legal_mna_team_configs() -> Dict[str, AIAgentConfig|HumanAgentConfig|StakeholderConfig]
  - create_legal_mna_team_timeline() -> Dict[int, List[Tuple[str, BaseAgentConfig, str]]]
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
def create_legal_mna_team_configs():
    """Create AI and human mock agent configurations for Legal M&A."""

    # === AI Agents — drafting, diligence, and orchestration ===
    deal_counsel_ai = AIAgentConfig(
        agent_id="deal_counsel_ai",
        agent_type="ai",
        system_prompt=(
            "You are an AI Deal Counsel focused on drafting and negotiating the Share Purchase Agreement (SPA). "
            "You propose market‑standard positions, track redline deltas with rationales, harmonize defined terms, "
            "and maintain issue lists with fallbacks across indemnities, covenants, and termination mechanics."
        ),
        agent_description=(
            "AI counsel who drafts market‑standard SPA language, tracks gives/gets, and harmonizes terms."
        ),
        agent_capabilities=[
            "Drafts and negotiates SPA sections",
            "Tracks redline deltas with rationales",
            "Maintains issue lists with fallbacks",
            "Harmonizes definitions across documents",
        ],
    )

    diligence_reader = AIAgentConfig(
        agent_id="diligence_reader",
        agent_type="ai",
        system_prompt=(
            "You are an AI Diligence Reader that triages data‑room documents, extracts facts into a structured index, "
            "flags risk‑relevant findings (assignment/consent, MFN, exclusivity, change‑of‑control, IP chain‑of‑title), "
            "and links evidence to disclosure schedules."
        ),
        agent_description=(
            "Reader who turns the data room into a structured index and flags material risks with citations."
        ),
        agent_capabilities=[
            "Extracts facts into structured index",
            "Flags risk‑relevant findings",
            "Links evidence to schedules",
            "Maintains citations and versions",
        ],
    )

    schedules_builder = AIAgentConfig(
        agent_id="schedules_builder",
        agent_type="ai",
        system_prompt=(
            "You assemble disclosure schedules and consent lists from diligence outputs, ensure cross‑references to the SPA, "
            "and validate that exceptions are precise, current, and supported with evidence from the data room."
        ),
        agent_description=(
            "Assembler who produces precise, evidence‑linked schedules and consent lists."
        ),
        agent_capabilities=[
            "Builds disclosure schedules",
            "Cross‑references to SPA",
            "Validates precision and currency",
            "Tracks exceptions and evidence",
        ],
    )

    redline_explainer = AIAgentConfig(
        agent_id="redline_explainer",
        agent_type="ai",
        system_prompt=(
            "You are a Redline Explainer that summarizes diff chunks into executive‑readable rationales, "
            "identifies give‑gets, and proposes trade packages balancing value, certainty of close, and compliance."
        ),
        agent_description=(
            "Explainer who distills diffs into executive‑readable rationales and trade packages."
        ),
        agent_capabilities=[
            "Summarizes deltas and rationale",
            "Identifies give‑gets",
            "Proposes trade packages",
            "Balances value/certainty/compliance",
        ],
    )

    antitrust_analyst = AIAgentConfig(
        agent_id="antitrust_analyst",
        agent_type="ai",
        system_prompt=(
            "You analyze HSR thresholds and potential antitrust risk, assemble Item 4(c)/(d) materials, draft cover letters, "
            "and maintain a tracker for waiting periods, second requests, and remedies discussion points."
        ),
        agent_description=(
            "Analyst who manages HSR thresholds, waiting periods, and potential remedies."
        ),
        agent_capabilities=[
            "Analyzes HSR thresholds",
            "Assembles Item 4(c)/(d) materials",
            "Tracks waiting periods and requests",
            "Preps remedy discussion points",
        ],
    )

    cfius_analyst = AIAgentConfig(
        agent_id="cfius_analyst",
        agent_type="ai",
        system_prompt=(
            "You screen for CFIUS topical sensitivities (critical tech, supply chain, personal data), draft short‑form notices, "
            "and coordinate Q&A logs with outside counsel if a filing is elected."
        ),
        agent_description=(
            "Screening analyst who prepares CFIUS short‑form and coordinates Q&A logs."
        ),
        agent_capabilities=[
            "Screens for CFIUS sensitivities",
            "Drafts short‑form notices",
            "Maintains Q&A coordination",
            "Interfaces with outside counsel",
        ],
    )

    tax_structuring_ai = AIAgentConfig(
        agent_id="tax_structuring_ai",
        agent_type="ai",
        system_prompt=(
            "You are a Tax Structuring assistant that compares asset vs stock vs merger alternatives, models 338(h)(10)/336(e) "
            "elections, and produces step plans with annotated tax impacts and dependency checks."
        ),
        agent_description=(
            "Tax aide who compares structures, models elections, and drafts step plans."
        ),
        agent_capabilities=[
            "Models asset/stock/merger options",
            "Prepares 338(h)(10)/336(e) analyses",
            "Drafts annotated step plans",
            "Checks dependencies",
        ],
    )

    rwi_packager = AIAgentConfig(
        agent_id="rwi_packager",
        agent_type="ai",
        system_prompt=(
            "You coordinate Representations & Warranties Insurance (RWI) underwriting: assemble underwriting packets, "
            "track diligence responses, and reconcile exclusions with the SPA risk allocation."
        ),
        agent_description=(
            "Coordinator who aligns RWI underwriting with diligence outputs and SPA risk allocation."
        ),
        agent_capabilities=[
            "Assembles underwriting packets",
            "Tracks diligence responses",
            "Reconciles exclusions",
            "Aligns with SPA allocation",
        ],
    )

    funds_flow_coordinator = AIAgentConfig(
        agent_id="funds_flow_coordinator",
        agent_type="ai",
        system_prompt=(
            "You are a Funds Flow Coordinator who prepares sources‑and‑uses, drafts funds‑flow statements, and validates wire "
            "instructions and officer certificates for signing/closing mechanics."
        ),
        agent_description=(
            "Coordinator who drafts accurate funds‑flow and validates closing mechanics."
        ),
        agent_capabilities=[
            "Prepares sources‑and‑uses",
            "Drafts funds‑flow statements",
            "Validates wires and certificates",
            "Coordinates signing/closing",
        ],
    )

    closing_checklist_manager = AIAgentConfig(
        agent_id="closing_checklist_manager",
        agent_type="ai",
        system_prompt=(
            "You maintain the master closing checklist, verify third‑party consents and conditions precedent, and manage "
            "signature packets and bring‑down confirmations."
        ),
        agent_description=(
            "Checklist owner who manages CPs, consents, and signature packets to the finish line."
        ),
        agent_capabilities=[
            "Maintains master checklist",
            "Verifies consents and CPs",
            "Manages sign packets",
            "Runs bring‑down confirmations",
        ],
    )

    project_coordinator = AIAgentConfig(
        agent_id="project_coordinator",
        agent_type="ai",
        system_prompt=(
            "You run the deal room and status cadence: create trackers for issues, RFIs, and decisions; "
            "publish weekly summaries with risks, owners, and ETAs; and keep artifacts consistent across drafts."
        ),
        agent_description=(
            "Orchestrator who keeps trackers, decisions, and artifacts consistent across drafts."
        ),
        agent_capabilities=[
            "Runs issue/RFI/decision trackers",
            "Publishes weekly summaries",
            "Surfaces risks with owners/ETAs",
            "Maintains artifact consistency",
        ],
    )

    # === Human Mock Agents — leads, specialists, and approvers ===
    lead_mna_partner = HumanAgentConfig(
        agent_id="lead_mna_partner",
        agent_type="human_mock",
        system_prompt=(
            "Lead M&A Partner serving as principal negotiator and sign‑off authority for the acquirer. "
            "Sets negotiation strategy, approves trade‑offs, and ensures board and executive alignment."
        ),
        name="Lead M&A Partner",
        role="External Counsel – Lead",
        experience_years=18,
        background="Public/private M&A; Delaware/NY practice",
        agent_description=(
            "Principal negotiator who sets strategy, approves trade‑offs, and keeps board/executives aligned."
        ),
        agent_capabilities=[
            "Sets negotiation strategy",
            "Approves deal trade‑offs",
            "Ensures board/executive alignment",
            "Signs legal positions and escalations",
        ],
    )

    senior_mna_associate = HumanAgentConfig(
        agent_id="senior_mna_associate",
        agent_type="human_mock",
        system_prompt=(
            "Senior M&A Associate responsible for drafting SPA sections, coordinating disclosure schedules, "
            "running diligence calls, and synthesizing positions into decision memos."
        ),
        name="Senior M&A Associate",
        role="External Counsel – Associate",
        experience_years=7,
        background="Private M&A; tech transactions",
        agent_description=(
            "Senior associate who drafts SPA sections, coordinates schedules, and synthesizes positions."
        ),
        agent_capabilities=[
            "Drafts SPA and ancillary documents",
            "Coordinates disclosure schedules",
            "Runs diligence calls",
            "Prepares decision memos",
        ],
    )

    regulatory_counsel = HumanAgentConfig(
        agent_id="regulatory_counsel",
        agent_type="human_mock",
        system_prompt=(
            "Antitrust and regulatory counsel advising on HSR strategy, potential remedies, and multi‑jurisdiction sequencing; "
            "coordinates with antitrust_analyst on filings and timelines."
        ),
        name="Regulatory Counsel",
        role="Antitrust/HSR",
        experience_years=12,
        background="US antitrust; cross‑border filings",
        agent_description=(
            "Antitrust counsel who advises HSR strategy, remedies, and multi‑jurisdiction sequencing."
        ),
        agent_capabilities=[
            "Advises HSR thresholds and filings",
            "Coordinates with regulators",
            "Plans remedies discussions",
            "Aligns regulatory timelines",
        ],
    )

    ip_counsel = HumanAgentConfig(
        agent_id="ip_counsel",
        agent_type="human_mock",
        system_prompt=(
            "IP counsel validating chain‑of‑title, OSS usage, license compliance, and assignment mechanics; "
            "drafts IP/OSS and assignment schedules and approves IP‑related covenants."
        ),
        name="IP Counsel",
        role="Intellectual Property",
        experience_years=10,
        background="Software/IP transactions",
        agent_description=(
            "IP counsel who validates chain‑of‑title/OSS and drafts IP schedules and covenants."
        ),
        agent_capabilities=[
            "Validates IP ownership and OSS usage",
            "Drafts IP/OSS and assignment schedules",
            "Approves IP‑related covenants",
            "Manages IP risks and exceptions",
        ],
    )

    privacy_counsel = HumanAgentConfig(
        agent_id="privacy_counsel",
        agent_type="human_mock",
        system_prompt=(
            "Privacy counsel assessing DPAs, cross‑border transfers, and security frameworks; "
            "aligns privacy representations, exceptions, and remediation requirements."
        ),
        name="Privacy Counsel",
        role="Privacy & Security",
        experience_years=9,
        background="GDPR/CCPA; SaaS privacy",
        agent_description=(
            "Privacy counsel who aligns DPAs, transfers, and security representations with reality."
        ),
        agent_capabilities=[
            "Assesses DPAs and transfers",
            "Aligns privacy representations",
            "Tracks exceptions and remediation",
            "Coordinates with security/legal",
        ],
    )

    employment_counsel = HumanAgentConfig(
        agent_id="employment_counsel",
        agent_type="human_mock",
        system_prompt=(
            "Employment counsel covering offer/retention schemes, WARN/consultation obligations, and restrictive covenant scope; "
            "reviews works‑council/no‑poach issues and employee communications."
        ),
        name="Employment Counsel",
        role="Labor & Employment",
        experience_years=11,
        background="Employment & benefits in M&A",
        agent_description=(
            "Employment counsel who covers retention, WARN/consultation, and restrictive covenants."
        ),
        agent_capabilities=[
            "Designs retention/offer schemes",
            "Advises on WARN/consultation duties",
            "Reviews restrictive covenant scope",
            "Preps employee comms",
        ],
    )

    finance_counsel = HumanAgentConfig(
        agent_id="finance_counsel",
        agent_type="human_mock",
        system_prompt=(
            "Finance counsel aligning debt commitment papers, intercreditor terms, and conditions with SPA conditionality; "
            "coordinates closing deliverables and solvency certificates."
        ),
        name="Finance Counsel",
        role="Debt & Finance",
        experience_years=13,
        background="Acquisition finance",
        agent_description=(
            "Finance counsel who aligns commitment papers, intercreditor terms, and closing conditions."
        ),
        agent_capabilities=[
            "Aligns debt commitment papers",
            "Coordinates intercreditor terms",
            "Preps closing deliverables",
            "Drafts solvency certificates",
        ],
    )

    tax_partner = HumanAgentConfig(
        agent_id="tax_partner",
        agent_type="human_mock",
        system_prompt=(
            "Tax partner advising on structure selection, elections, and post‑closing steps; "
            "validates rollover/earnout metrics and drafts tax provisions."
        ),
        name="Tax Partner",
        role="Tax",
        experience_years=17,
        background="Corporate tax & M&A",
        agent_description=(
            "Tax partner who selects structures, elections, and post‑close steps with quantified impacts."
        ),
        agent_capabilities=[
            "Advises on structure selection",
            "Models elections and impacts",
            "Drafts tax provisions",
            "Validates rollover/earnout metrics",
        ],
    )

    rwi_broker = HumanAgentConfig(
        agent_id="rwi_broker",
        agent_type="human_mock",
        system_prompt=(
            "RWI broker coordinating underwriting calls, policy terms, exclusions, and binder mechanics; "
            "aligns RWI scope with diligence and SPA risk allocation."
        ),
        name="RWI Broker",
        role="Insurance Broker",
        experience_years=12,
        background="Transactional insurance",
        agent_description=(
            "RWI broker who coordinates underwriting, policy terms, exclusions, and binder mechanics."
        ),
        agent_capabilities=[
            "Coordinates underwriting calls",
            "Negotiates policy terms/exclusions",
            "Aligns RWI with SPA risk allocation",
            "Prepares binders",
        ],
    )

    general_counsel = HumanAgentConfig(
        agent_id="acquirer_gc",
        agent_type="human_mock",
        system_prompt=(
            "Acquirer General Counsel as stakeholder proxy for legal risk appetite; confirms governance, "
            "approvals, and final sign‑offs; escalates trade‑off decisions to executives and the board."
        ),
        name="General Counsel",
        role="Stakeholder – Legal",
        experience_years=15,
        background="In‑house GC, tech sector",
        agent_description=(
            "Acquirer GC who sets legal risk appetite, confirms governance, and approves sign‑offs."
        ),
        agent_capabilities=[
            "Sets legal risk appetite",
            "Confirms governance and approvals",
            "Escalates trade‑offs to executives/board",
            "Grants final sign‑offs",
        ],
    )

    cfo = HumanAgentConfig(
        agent_id="acquirer_cfo",
        agent_type="human_mock",
        system_prompt=(
            "Acquirer CFO overseeing funding, valuation adjustments, and post‑close financial reporting; "
            "signs off on funds‑flow and working capital mechanics."
        ),
        name="Chief Financial Officer",
        role="Stakeholder – Finance",
        experience_years=16,
        background="Corporate finance & M&A",
        agent_description=(
            "Acquirer CFO who oversees funding, valuation adjustments, and post‑close reporting."
        ),
        agent_capabilities=[
            "Approves funds‑flow and WC mechanics",
            "Reviews valuation adjustments",
            "Oversees post‑close reporting",
            "Aligns finance risks and controls",
        ],
    )

    target_ceo = HumanAgentConfig(
        agent_id="target_ceo",
        agent_type="human_mock",
        system_prompt=(
            "Target CEO ensuring cooperation, customer continuity, and employee communications; "
            "coordinates leadership transition and approves disclosure schedule accuracy."
        ),
        name="Target CEO",
        role="Target Leadership",
        experience_years=12,
        background="SaaS leadership",
        agent_description=(
            "Target CEO who ensures cooperation, customer continuity, and clear employee communications."
        ),
        agent_capabilities=[
            "Coordinates leadership transition",
            "Approves disclosure schedule accuracy",
            "Supports customer transition",
            "Leads employee communications",
        ],
    )

    # Optional explicit stakeholder agent (if your runner supports it)
    stakeholder = StakeholderConfig(
        agent_id="acquirer_gc_stakeholder",
        agent_type="stakeholder",
        system_prompt=(
            "You are the Acquirer General Counsel. You prioritize early momentum, then high‑quality drafts and "
            "governance, finishing with strict compliance at signing/closing. Approve key trade‑offs."
        ),
        model_name="o3",
        name="Acquirer GC (Stakeholder)",
        role="Executive Stakeholder",
        persona_description="Pragmatic, governance‑minded, risk‑aware; values crisp redline logs and evidence‑linked schedules.",
        agent_description=(
            "Acquirer GC stakeholder who prioritizes momentum early, then quality/governance, then strict compliance at close."
        ),
        agent_capabilities=[
            "Sets priorities across phases",
            "Approves key trade‑offs",
            "Demands evidence‑linked schedules",
            "Grants final legal approval",
        ],
        response_latency_steps_min=1,
        response_latency_steps_max=3,
        push_probability_per_timestep=0.1,
        suggestion_rate=0.5,
        clarification_reply_rate=0.9,
        strictness=0.65,
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
        "deal_counsel_ai": deal_counsel_ai,
        "diligence_reader": diligence_reader,
        "schedules_builder": schedules_builder,
        "redline_explainer": redline_explainer,
        "antitrust_analyst": antitrust_analyst,
        "cfius_analyst": cfius_analyst,
        "tax_structuring_ai": tax_structuring_ai,
        "rwi_packager": rwi_packager,
        "funds_flow_coordinator": funds_flow_coordinator,
        "closing_checklist_manager": closing_checklist_manager,
        "project_coordinator": project_coordinator,
        # Human
        "lead_mna_partner": lead_mna_partner,
        "senior_mna_associate": senior_mna_associate,
        "regulatory_counsel": regulatory_counsel,
        "ip_counsel": ip_counsel,
        "privacy_counsel": privacy_counsel,
        "employment_counsel": employment_counsel,
        "finance_counsel": finance_counsel,
        "tax_partner": tax_partner,
        "rwi_broker": rwi_broker,
        "general_counsel": general_counsel,
        "cfo": cfo,
        "target_ceo": target_ceo,
        # Optional stakeholder object (ok to ignore in runners that don't need it)
        "stakeholder": stakeholder,
    }


# ---------------------------
# TEAM TIMELINE (ad hoc join/leave)
# ---------------------------
def create_team_timeline():
    """
    Timestep → [(action, agent_cfg, rationale)]
    Actions: "add" or "remove".
    """
    cfg = create_legal_mna_team_configs()

    return {
        0: [
            # Kickoff & diligence scoping
            (
                "add",
                cfg["project_coordinator"],
                "Stand up IM/trackers and weekly cadence",
            ),
            (
                "add",
                cfg["lead_mna_partner"],
                "Establish negotiation strategy and governance",
            ),
            (
                "add",
                cfg["senior_mna_associate"],
                "Drafting support and diligence coordination",
            ),
            (
                "add",
                cfg["diligence_reader"],
                "Spin up dataroom triage and risk extraction",
            ),
            (
                "add",
                cfg["deal_counsel_ai"],
                "Draft SPA v0 scaffold aligned to structure",
            ),
            (
                "add",
                cfg["general_counsel"],
                "Stakeholder alignment and sign‑off authority",
            ),
        ],
        6: [
            # Specialized diligence
            ("add", cfg["ip_counsel"], "IP chain‑of‑title, OSS, assignment mechanics"),
            (
                "add",
                cfg["privacy_counsel"],
                "DPA, cross‑border transfers, security posture",
            ),
            (
                "add",
                cfg["employment_counsel"],
                "Employee/retention/WARN & restrictive covenants",
            ),
            ("add", cfg["antitrust_analyst"], "HSR analysis and filings prep"),
            (
                "add",
                cfg["tax_structuring_ai"],
                "Structure alternatives and step‑plan modeling",
            ),
        ],
        12: [
            # Drafting & schedules
            (
                "add",
                cfg["schedules_builder"],
                "Disclosure schedules v0 and consent mapping",
            ),
            ("add", cfg["redline_explainer"], "Summarize deltas and propose give‑gets"),
            ("add", cfg["finance_counsel"], "Debt commitment alignment and conditions"),
            ("add", cfg["cfo"], "Funding oversight and WC peg modeling"),
            (
                "remove",
                cfg["diligence_reader"],
                "Front‑loaded triage complete; keep exceptions owner‑led",
            ),
        ],
        18: [
            # Negotiation loops & regulatory
            (
                "add",
                cfg["regulatory_counsel"],
                "HSR strategy and second‑request posture",
            ),
            ("add", cfg["cfius_analyst"], "CFIUS screen/draft (if elected)"),
            (
                "add",
                cfg["rwi_packager"],
                "Underwriting packet & exclusions reconciliation",
            ),
            (
                "remove",
                cfg["tax_structuring_ai"],
                "Structure converged; tax partner to finalize language",
            ),
        ],
        25: [
            # Integration with financing and leadership engagement
            (
                "add",
                cfg["funds_flow_coordinator"],
                "Sources/uses and funds‑flow drafting",
            ),
            ("add", cfg["target_ceo"], "Customer/employee comms alignment"),
        ],
        35: [
            # Team churn milestone (associate joins mid‑run per paper pattern)
            (
                "add",
                cfg["senior_mna_associate"],
                "Additional bandwidth for redlines and schedules",
            ),
        ],
        45: [
            # Closing mechanics
            (
                "add",
                cfg["closing_checklist_manager"],
                "Master closing checklist and sign packets",
            ),
            (
                "remove",
                cfg["redline_explainer"],
                "Negotiations converged; finalize closing set",
            ),
        ],
        55: [
            # Final bring‑down and signing/closing
            ("add", cfg["tax_partner"], "Bring‑down tax confirmations and covenants"),
            (
                "remove",
                cfg["antitrust_analyst"],
                "Regulatory filings submitted; tracking only",
            ),
        ],
    }
