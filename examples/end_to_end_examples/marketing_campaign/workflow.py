"""
Renewable Energy Company – Integrated Marketing Campaign
Real-world style demo: National brand + product launch for utility-scale solar and community wind offerings.

Demonstrates:
- Cross-channel campaign planning (B2B & B2C) with compliance for environmental claims
- Funnel design with content, paid, PR, events, and partner co-marketing
- Measurement plan with experimentation, MMM/MTA alignment, and brand lift
- Accessibility and privacy-safe lead capture across web and field events
- Executive/stakeholder checkpoints with risk & dependency management
"""

from uuid import UUID
from manager_agent_gym.schemas.core.workflow import Workflow
from manager_agent_gym.schemas.core.tasks import Task
from manager_agent_gym.schemas.core.base import TaskStatus
from manager_agent_gym.schemas.preferences import Constraint


def create_workflow() -> Workflow:
    """Create an integrated marketing workflow with hierarchical phases and dependencies."""
    workflow = Workflow(
        name="Renewable Energy – Integrated Marketing Campaign",
        owner_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
        workflow_goal=(
            """
            Objective: Launch a national integrated campaign for Acme Renewables to drive brand awareness,
            qualified pipeline for B2B (utilities, municipalities, C&I), and sign-ups for B2C community energy.
            Primary deliverables:
            - Messaging house & claims playbook (substantiated, privacy-safe), brand & creative toolkit
            - Channel plan & budget (paid/owned/earned), flighting calendar, and experimentation plan
            - Web conversion flows (accessibility & consent), CRM and lead-routing with scoring
            - PR & analyst program, events/field marketing kit, partner co-marketing assets
            - Measurement framework (brand lift, funnel KPIs, CAC/LTV), MMM/MTA-compatible UTM governance
            Acceptance criteria (high‑level):
            - Brand lift ≥ +6% aided awareness within target segments; ≥ 15% MoM web organic uplift during flight
            - ≥ 1,000 MQLs (B2B+B2C) with <= target CAC thresholds; ≥ 25 qualified opportunities for B2B
            - Claims substantiation log maintained; no greenwashing guideline violations
            - WCAG 2.1 AA compliance for key web assets; consent opt‑in rates ≥ 85%
            - Experimentation cadence established; weekly executive dashboard live
            """
        ),
    )

    # ---------------------------
    # PHASE 1 — Strategy & Foundations
    # ---------------------------

    discovery_research = Task(
        name="Market Discovery & Audience Research",
        description=(
            "Synthesize TAM/SAM/SOM, audience personas (utilities, municipalities, C&I, residential), "
            "buyer jobs-to-be-done, competitive scan, and channel benchmarks. Output: insights deck & JTBD map."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=24.0,
        estimated_cost=6000.0,
    )
    discovery_research.subtasks = [
        Task(
            name="TAM/SAM/SOM & Segment Prioritization",
            description="Quantify market size; prioritize segments with ICP fit and reachable media.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=1500.0,
        ),
        Task(
            name="Persona & JTBD Interviews",
            description="Interview 12–16 targets across utility, municipal, C&I, residential segments.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=8.0,
            estimated_cost=2000.0,
        ),
        Task(
            name="Competitive & Claims Landscape",
            description="Analyze competitor messaging, claims, certifications, and pricing signals.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=1500.0,
        ),
        Task(
            name="Channel Benchmarking",
            description="Benchmark CPC/CPM/CPL and conversion across paid social/search/display and events.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=1000.0,
        ),
    ]

    messaging_house = Task(
        name="Messaging House & Green Claims Playbook",
        description=(
            "Craft value prop ladders, proof points, and environmental claims with evidence requirements "
            "(emissions avoided, RECs, lifecycle impacts). Output: messaging house + substantiation log template."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=20.0,
        estimated_cost=5000.0,
        dependency_task_ids=[discovery_research.task_id],
    )
    messaging_house.subtasks = [
        Task(
            name="Value Proposition Ladder",
            description="Segment-specific value props mapped to pains/gains and JTBD.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=5.0,
            estimated_cost=1250.0,
        ),
        Task(
            name="Claims Substantiation Matrix",
            description="Define each claim, evidence type, and acceptance criteria; owners & review cadence.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=8.0,
            estimated_cost=2000.0,
        ),
        Task(
            name="Brand & Tone Guidelines",
            description="Guidelines for inclusive, accessible, and non-greenwashing language.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=7.0,
            estimated_cost=1750.0,
        ),
    ]

    channel_plan = Task(
        name="Channel Strategy, Budget & Flighting",
        description=(
            "Translate strategy to channel mix (paid/owned/earned), budget allocations, geo & segment targets, "
            "and a flighting calendar with guardrails for experiments and caps."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=18.0,
        estimated_cost=4500.0,
        dependency_task_ids=[messaging_house.task_id],
    )
    channel_plan.subtasks = [
        Task(
            name="Paid Media Mix & Caps",
            description="Define spend allocation, frequency caps, and brand safety lists.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=1500.0,
        ),
        Task(
            name="Owned/Earned Plan",
            description="SEO/Pillar content roadmap, PR/AR outreach plan, community & events calendar.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=1500.0,
        ),
        Task(
            name="Experimentation Plan",
            description="A/B and multivariate plan across landing pages/ads; power & MDE assumptions.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=1500.0,
        ),
    ]

    # ---------------------------
    # PHASE 2 — Creative, Web, and Data Foundations
    # ---------------------------

    creative_toolkit = Task(
        name="Creative Toolkit & Asset Production",
        description=(
            "Produce hero/variant creatives for priority segments and channels; templates for partner co‑marketing; "
            "ensure alt text/captions and inclusive imagery. Output: asset library & spec sheets."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=30.0,
        estimated_cost=12000.0,
        dependency_task_ids=[channel_plan.task_id],
    )
    creative_toolkit.subtasks = [
        Task(
            name="Concepts & Storyboards",
            description="Three creative territories with storyboard proof points and social cut-downs.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=10.0,
            estimated_cost=4000.0,
        ),
        Task(
            name="Production & Adaptations",
            description="Produce master assets; adapt for paid social/search/display/OOH/email.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=14.0,
            estimated_cost=5600.0,
        ),
        Task(
            name="Accessibility Pass",
            description="Alt text, captions, contrast checks; inclusive language review.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=2400.0,
        ),
    ]

    web_conversion = Task(
        name="Web & Conversion Experience",
        description=(
            "Build/optimize campaign landing pages, calculators, and lead capture with WCAG 2.1 AA and "
            "consent management. Output: pages live with UTM taxonomy and event schema."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=28.0,
        estimated_cost=9000.0,
        dependency_task_ids=[channel_plan.task_id],
    )
    web_conversion.subtasks = [
        Task(
            name="Landing Page & Calculator",
            description="CTA-focused LPs with sector-specific calculators (savings, emissions avoided).",
            status=TaskStatus.PENDING,
            estimated_duration_hours=10.0,
            estimated_cost=3500.0,
        ),
        Task(
            name="Consent & Preference Center",
            description="CMP integration, granular opt-ins, unsubscribe flows, and cookie banner logic.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=8.0,
            estimated_cost=2500.0,
        ),
        Task(
            name="Analytics & Event Schema",
            description="UTM conventions, events, and schema for MMM/MTA; QA plan.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=10.0,
            estimated_cost=3000.0,
        ),
    ]

    crm_enablement = Task(
        name="CRM Enablement & Lead Routing",
        description=(
            "Configure scoring, deduplication, enrichment, and routing to Sales/Community Ops; "
            "set SLAs and feedback loop. Output: playbooks + dashboards."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=16.0,
        estimated_cost=5000.0,
        dependency_task_ids=[web_conversion.task_id],
    )
    crm_enablement.subtasks = [
        Task(
            name="Scoring & Enrichment",
            description="Firmographic/intent enrichment; scores tuned for A/B testing impact.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=2000.0,
        ),
        Task(
            name="Routing & SLAs",
            description="Queues, assignments, and reply SLAs for B2B and B2C flows.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=2000.0,
        ),
        Task(
            name="Dashboards",
            description="Ops dashboards for handoffs and funnel health.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=1000.0,
        ),
    ]

    # ---------------------------
    # PHASE 3 — Launch & Go-to-Market
    # ---------------------------

    pr_analyst = Task(
        name="PR & Analyst Program",
        description=(
            "Brief key media/analysts on product roadmap, case studies, and sustainability impact; embargoed press kit."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=12.0,
        estimated_cost=6000.0,
        dependency_task_ids=[messaging_house.task_id],
    )
    pr_analyst.subtasks = [
        Task(
            name="Press Kit & Embargo Plan",
            description="Release, FAQs, spokespeople prep, assets, and embargo schedule.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=3000.0,
        ),
        Task(
            name="Briefings & Coverage Tracker",
            description="Analyst/media outreach, interviews, and coverage measurement.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=3000.0,
        ),
    ]

    events_field = Task(
        name="Events & Field Marketing",
        description=(
            "Plan and execute industry events, webinars, and community pop-ups with lead capture kits."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=16.0,
        estimated_cost=8000.0,
        dependency_task_ids=[creative_toolkit.task_id, web_conversion.task_id],
    )
    events_field.subtasks = [
        Task(
            name="Event Kit & Staffing",
            description="Booth assets, demo flow, consent capture, and staffing plan.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=8.0,
            estimated_cost=4000.0,
        ),
        Task(
            name="Webinar Production",
            description="Topic selection, speaker prep, and post-event nurture setup.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=8.0,
            estimated_cost=4000.0,
        ),
    ]

    partner_comarketing = Task(
        name="Partner Co‑Marketing",
        description=(
            "Co-develop content and campaigns with installers, finance partners, and local programs."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=14.0,
        estimated_cost=5000.0,
        dependency_task_ids=[creative_toolkit.task_id, messaging_house.task_id],
    )
    partner_comarketing.subtasks = [
        Task(
            name="Partner Asset Pack",
            description="Co-branding rules, templates, and MDF playbook.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=2000.0,
        ),
        Task(
            name="Joint Campaigns",
            description="Pilot co-branded pilots in two priority regions.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=8.0,
            estimated_cost=3000.0,
        ),
    ]

    paid_media_activation = Task(
        name="Paid Media Activation",
        description=(
            "Launch paid search/social/display/OOH per flighting; ensure brand safety, frequency caps, and creative rotation."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=20.0,
        estimated_cost=50000.0,
        dependency_task_ids=[creative_toolkit.task_id, channel_plan.task_id],
    )
    paid_media_activation.subtasks = [
        Task(
            name="Platform Setup & QA",
            description="Budgets, audiences, pixels, events, and creative QA per platform spec.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=8.0,
            estimated_cost=2000.0,
        ),
        Task(
            name="Go‑Live",
            description="Phased roll-out with canary budgets before full flight.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=12.0,
            estimated_cost=3000.0,
        ),
    ]

    email_nurture = Task(
        name="Email & Nurture Programs",
        description=(
            "Design drip sequences by segment; respect consent preferences and enable one‑click unsubscribe."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=12.0,
        estimated_cost=3000.0,
        dependency_task_ids=[crm_enablement.task_id, messaging_house.task_id],
    )
    email_nurture.subtasks = [
        Task(
            name="Drip & Trigger Design",
            description="Welcome, education, and re‑engagement sequences; B2B vs B2C forks.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=1500.0,
        ),
        Task(
            name="Deliverability & Compliance",
            description="SPF/DKIM/DMARC, list hygiene, and rate limiting.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=1500.0,
        ),
    ]

    # ---------------------------
    # PHASE 4 — Measurement & Optimization
    # ---------------------------

    measurement_framework = Task(
        name="Measurement Framework & Dashboards",
        description=(
            "Define KPIs, brand lift study, MMM/MTA alignment, and executive dashboard; institute weekly reviews."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=16.0,
        estimated_cost=6000.0,
        dependency_task_ids=[channel_plan.task_id, web_conversion.task_id],
    )
    measurement_framework.subtasks = [
        Task(
            name="KPI Spec & UTM Governance",
            description="CAC/LTV, funnel KPIs; establish UTM conventions and governance docs.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=8.0,
            estimated_cost=2500.0,
        ),
        Task(
            name="Executive Dashboard",
            description="Auto-refresh dashboard with weekly readout and alert thresholds.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=8.0,
            estimated_cost=3500.0,
        ),
    ]

    experimentation_optimization = Task(
        name="Experimentation & Optimization",
        description=(
            "Run A/B tests across LPs, ads, and nurture; implement learnings and scale winners."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=20.0,
        estimated_cost=7000.0,
        dependency_task_ids=[
            measurement_framework.task_id,
            paid_media_activation.task_id,
        ],
    )
    experimentation_optimization.subtasks = [
        Task(
            name="Test Execution",
            description="Prioritized backlog; canonical analysis template and guardrails.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=10.0,
            estimated_cost=3500.0,
        ),
        Task(
            name="Scale & Rollout",
            description="Rollout winning variants across channels with holdouts where applicable.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=10.0,
            estimated_cost=3500.0,
        ),
    ]

    brand_lift_study = Task(
        name="Brand Lift Study",
        description=(
            "Run brand lift with target segments; analyze aided/unaided awareness, consideration, and favorability."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=10.0,
        estimated_cost=12000.0,
        dependency_task_ids=[paid_media_activation.task_id],
    )
    brand_lift_study.subtasks = [
        Task(
            name="Survey Fielding",
            description="Define sample, screener, and quotas; field during mid-flight.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=8000.0,
        ),
        Task(
            name="Analysis & Readout",
            description="Report results; recommend next-flight adjustments.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=4000.0,
        ),
    ]

    executive_readouts = Task(
        name="Executive Readouts & Decision Memos",
        description="Weekly readouts, risk register, and decision memos for trade-offs and reallocations.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=8.0,
        estimated_cost=2000.0,
        dependency_task_ids=[measurement_framework.task_id],
    )

    wrap_up = Task(
        name="Post‑Campaign Review & Learnings",
        description=(
            "Synthesize performance, creative insights, channel economics, and operational learnings; "
            "publish playbook and backlog for next cycle."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=12.0,
        estimated_cost=2500.0,
        dependency_task_ids=[
            experimentation_optimization.task_id,
            executive_readouts.task_id,
        ],
    )

    # ---------------------------
    # REGISTER TASKS IN WORKFLOW
    # ---------------------------
    for task in [
        discovery_research,
        messaging_house,
        channel_plan,
        creative_toolkit,
        web_conversion,
        crm_enablement,
        pr_analyst,
        events_field,
        partner_comarketing,
        paid_media_activation,
        email_nurture,
        measurement_framework,
        experimentation_optimization,
        brand_lift_study,
        executive_readouts,
        wrap_up,
    ]:
        workflow.add_task(task)

    # ---------------------------
    # CONSTRAINTS (Green claims, privacy, brand, accessibility, governance)
    # ---------------------------
    workflow.constraints.extend(
        [
            Constraint(
                name="Environmental Claims Substantiation",
                description="All environmental claims must be substantiated and documented; no greenwashing.",
                constraint_type="regulatory",
                enforcement_level=0.95,
                applicable_task_types=[
                    "Messaging House & Green Claims Playbook",
                    "Creative Toolkit & Asset Production",
                    "PR & Analyst Program",
                    "Partner Co‑Marketing",
                    "Paid Media Activation",
                    "Web & Conversion Experience",
                ],
                metadata={
                    "evidence_required": [
                        "certifications",
                        "LCA refs",
                        "REC documentation",
                    ]
                },
            ),
            Constraint(
                name="Marketing Privacy & Consent",
                description="Consent, preference management, and data minimization must be enforced for all lead capture.",
                constraint_type="regulatory",
                enforcement_level=0.9,
                applicable_task_types=[
                    "Web & Conversion Experience",
                    "CRM Enablement & Lead Routing",
                    "Email & Nurture Programs",
                    "Events & Field Marketing",
                ],
                metadata={
                    "required_controls": ["CMP", "double_opt_in", "unsub_one_click"],
                    "prohibited_keywords": [
                        "ssn",
                        "password",
                        "api key",
                        "secret key",
                        "private key",
                        "account_number",
                    ],
                },
            ),
            Constraint(
                name="Brand & Trademark Usage",
                description="Creative and partner co‑branding must follow brand guidelines and approvals.",
                constraint_type="organizational",
                enforcement_level=0.85,
                applicable_task_types=[
                    "Creative Toolkit & Asset Production",
                    "Partner Co‑Marketing",
                    "Paid Media Activation",
                    "PR & Analyst Program",
                ],
                metadata={"approval_required": ["brand_team", "legal_marketing"]},
            ),
            Constraint(
                name="Accessibility (WCAG 2.1 AA)",
                description="Campaign web and key assets must meet WCAG 2.1 AA standards.",
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=[
                    "Web & Conversion Experience",
                    "Creative Toolkit & Asset Production",
                    "Email & Nurture Programs",
                ],
                metadata={"standards": ["wcag_2_1_aa"]},
            ),
            Constraint(
                name="Executive Budget Guardrails",
                description="Spend and reallocations must remain within approved guardrails unless escalated.",
                constraint_type="organizational",
                enforcement_level=0.8,
                applicable_task_types=[
                    "Paid Media Activation",
                    "Experimentation & Optimization",
                ],
                metadata={"budget_variance_threshold_pct": 10},
            ),
        ]
    )

    return workflow
