"""
Brand Crisis Management & Reputation Recovery Demo
Real-world use case: Mid-market consumer goods company social media-driven reputation crisis.
Demonstrates:
- Crisis response coordination under extreme time pressure with incomplete information
- Multi-stakeholder communication orchestration across diverse groups (customers, media, employees, investors)
- Real-time adaptive strategy adjustment based on evolving situation dynamics
- Resource allocation prioritization during time-critical scenarios with competing demands
- Cross-functional team coordination with varying expertise levels and decision authority
- Timeline management with hard deadlines and cascading dependencies
- Reputation management through strategic messaging and narrative control
- Stakeholder relationship preservation during high-stress crisis periods
"""

from uuid import uuid4

from manager_agent_gym.schemas.domain.workflow import Workflow
from manager_agent_gym.schemas.domain.task import Task
from manager_agent_gym.schemas.domain.base import TaskStatus
from manager_agent_gym.schemas.preferences import Constraint
from manager_agent_gym.core.workflow.services import WorkflowMutations


def create_brand_crisis_management_workflow() -> Workflow:
    """Create brand crisis management workflow with hierarchical phases and dependencies."""

    workflow = Workflow(
        name="Brand Crisis Management & Reputation Recovery",
        workflow_goal=(
            """
            Objective: Execute comprehensive brand crisis management response to social media-driven reputation incident affecting mid-market consumer goods company, coordinate multi-stakeholder communications, implement reputation recovery strategy, and restore customer trust to pre-crisis levels within 4-month timeline.
            Primary deliverables:
            - Crisis assessment and stakeholder impact analysis with comprehensive situation evaluation, stakeholder mapping, sentiment analysis across digital platforms, and financial impact quantification with real-time monitoring dashboard.
            - Multi-channel crisis communication strategy with coordinated messaging framework across social media, traditional media, internal communications, and customer service channels with platform-specific content and media relations protocols.
            - Executive crisis team activation with cross-functional team deployment including executive leadership, PR specialists, legal counsel, HR representatives, and customer service leads with defined roles and 24/7 response capability.
            - Customer communication and engagement program with direct customer outreach campaigns, social media response protocols, customer service enhancement, compensation program development, and community management strategy.
            - Internal stakeholder management with employee communication plan, leadership messaging alignment, partner notifications, investor relations updates, and board reporting with morale monitoring.
            - Media relations and narrative control with press release development, interview preparation, journalist relationship management, and proactive media engagement with message consistency.
            - Digital reputation recovery campaign with SEO optimization, positive content creation, influencer engagement, customer testimonial programs, and online review management.
            - Legal and regulatory coordination with legal risk assessment, regulatory notification requirements, litigation preparedness, compliance verification, and documentation preservation.
            Acceptance criteria (high‑level):
            - Customer sentiment recovery to >75% of pre-crisis levels within 4 months; social media sentiment shifted from negative to neutral/positive across all platforms.
            - Media coverage balance achieved with 60% neutral-to-positive articles within 6 weeks; no unresolved factual inaccuracies in major media coverage.
            - Internal stakeholder confidence maintained with <5% employee turnover during crisis period; investor confidence preserved with transparent communication.
            - Legal and compliance requirements met with zero regulatory violations; all documentation properly maintained for potential legal proceedings.
            - Customer retention rate >90% among existing customer base; customer service resolution time <24 hours for crisis-related inquiries.
            - Brand trust metrics restored to within 80% of pre-crisis baseline through independent third-party measurement.
            """
        ),
        owner_id=uuid4(),
    )

    # Phase 1: Immediate Crisis Response (Hours 0-6)
    crisis_assessment = Task(
        name="Crisis Assessment & Impact Analysis",
        description=(
            "Conduct comprehensive crisis situation assessment and stakeholder impact analysis; "
            "quantify scope, scale, and immediate threats to brand reputation."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=4.0,
        estimated_cost=800.0,
    )
    crisis_assessment.subtasks = [
        Task(
            name="Situation Evaluation",
            description="Evaluate crisis scope, scale, and immediate threats across all digital platforms and traditional media.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=2.0,
            estimated_cost=400.0,
        ),
        Task(
            name="Stakeholder Impact Mapping",
            description="Map affected stakeholders and assess potential impact on customers, employees, investors, and partners.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=1.5,
            estimated_cost=300.0,
        ),
        Task(
            name="Financial Impact Assessment",
            description="Assess immediate and projected financial impact including revenue, market cap, and operational costs.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=0.5,
            estimated_cost=100.0,
        ),
    ]

    executive_team_activation = Task(
        name="Executive Crisis Team Activation",
        description=(
            "Activate crisis management team and establish decision-making protocols with 24/7 response capability."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=2.0,
        estimated_cost=600.0,
        dependency_task_ids=[crisis_assessment.task_id],
    )
    executive_team_activation.subtasks = [
        Task(
            name="Crisis Team Assembly",
            description="Assemble cross-functional crisis response team with defined roles and decision-making authority.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=1.0,
            estimated_cost=300.0,
        ),
        Task(
            name="Communication Protocols Setup",
            description="Set up crisis communication protocols and emergency contact systems for 24/7 coordination.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=1.0,
            estimated_cost=300.0,
        ),
    ]

    immediate_response_strategy = Task(
        name="Immediate Response Strategy",
        description=(
            "Develop initial crisis response strategy and key messaging framework aligned with brand values."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=6.0,
        estimated_cost=1200.0,
        dependency_task_ids=[executive_team_activation.task_id],
    )
    immediate_response_strategy.subtasks = [
        Task(
            name="Core Messaging Development",
            description="Develop core crisis messaging aligned with brand values and legal requirements.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=600.0,
        ),
        Task(
            name="Channel Strategy Planning",
            description="Plan multi-channel communication strategy across social media, traditional media, and direct channels.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=2.0,
            estimated_cost=400.0,
        ),
        Task(
            name="Target Audience Prioritization",
            description="Prioritize target audiences and customize messaging for each stakeholder segment.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=1.0,
            estimated_cost=200.0,
        ),
    ]

    # Phase 2: Public Communication Launch (Hours 2-24)
    public_communication_launch = Task(
        name="Public Communication Launch",
        description=(
            "Execute initial public communications across all channels with coordinated messaging."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=8.0,
        estimated_cost=1600.0,
        dependency_task_ids=[immediate_response_strategy.task_id],
    )
    public_communication_launch.subtasks = [
        Task(
            name="Social Media Response",
            description="Deploy coordinated social media response across all platforms with real-time monitoring.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=800.0,
        ),
        Task(
            name="Press Release Distribution",
            description="Distribute official press release to media outlets and key stakeholders.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=2.0,
            estimated_cost=400.0,
        ),
        Task(
            name="Customer Service Enhancement",
            description="Enhance customer service protocols and scripts for crisis-related inquiries.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=2.0,
            estimated_cost=400.0,
        ),
    ]

    internal_stakeholder_communication = Task(
        name="Internal Stakeholder Communication",
        description=(
            "Execute comprehensive internal stakeholder communication plan for employees, partners, and investors."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=6.0,
        estimated_cost=1200.0,
        dependency_task_ids=[immediate_response_strategy.task_id],
    )
    internal_stakeholder_communication.subtasks = [
        Task(
            name="Employee Communication",
            description="Communicate crisis situation and response plan to all employees with leadership talking points.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=600.0,
        ),
        Task(
            name="Partner & Investor Notifications",
            description="Notify key partners, vendors, and investors about crisis and response strategy.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=600.0,
        ),
    ]

    # Phase 3: Active Crisis Management (Days 1-7)
    media_relations_management = Task(
        name="Media Relations & Narrative Control",
        description=(
            "Manage ongoing media relations and control narrative with spokesperson coordination and monitoring."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=16.0,
        estimated_cost=3200.0,
        dependency_task_ids=[public_communication_launch.task_id],
    )
    media_relations_management.subtasks = [
        Task(
            name="Spokesperson Coordination",
            description="Coordinate spokesperson activities and prepare for media interviews with consistent messaging.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=8.0,
            estimated_cost=1600.0,
        ),
        Task(
            name="Media Monitoring & Response",
            description="Monitor media coverage and adjust messaging strategy based on narrative evolution.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=8.0,
            estimated_cost=1600.0,
        ),
    ]

    customer_engagement_program = Task(
        name="Customer Engagement & Retention Program",
        description=(
            "Implement direct customer engagement and retention programs with compensation and service enhancement."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=20.0,
        estimated_cost=4000.0,
        dependency_task_ids=[public_communication_launch.task_id],
    )
    customer_engagement_program.subtasks = [
        Task(
            name="Customer Outreach Campaign",
            description="Execute direct customer outreach and communication campaign with personalized messaging.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=12.0,
            estimated_cost=2400.0,
        ),
        Task(
            name="Compensation Program Implementation",
            description="Implement customer compensation and retention program with clear eligibility criteria.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=8.0,
            estimated_cost=1600.0,
        ),
    ]

    legal_regulatory_coordination = Task(
        name="Legal & Regulatory Coordination",
        description=(
            "Coordinate legal and regulatory compliance requirements with risk assessment and documentation."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=12.0,
        estimated_cost=2400.0,
        dependency_task_ids=[crisis_assessment.task_id],
    )
    legal_regulatory_coordination.subtasks = [
        Task(
            name="Legal Risk Assessment",
            description="Conduct comprehensive legal risk assessment and litigation preparedness planning.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=1200.0,
        ),
        Task(
            name="Documentation & Compliance",
            description="Ensure proper documentation preservation and regulatory compliance requirements.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=1200.0,
        ),
    ]

    # Phase 4: Digital Reputation Recovery (Weeks 2-8)
    digital_reputation_recovery = Task(
        name="Digital Reputation Recovery Campaign",
        description=(
            "Implement comprehensive digital reputation recovery with SEO, content creation, and online review management."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=24.0,
        estimated_cost=4800.0,
        dependency_task_ids=[media_relations_management.task_id],
    )
    digital_reputation_recovery.subtasks = [
        Task(
            name="Positive Content Creation",
            description="Create and distribute positive brand content across digital channels and platforms.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=12.0,
            estimated_cost=2400.0,
        ),
        Task(
            name="SEO & Online Review Management",
            description="Implement SEO optimization and online review management strategy.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=8.0,
            estimated_cost=1600.0,
        ),
        Task(
            name="Influencer & Testimonial Programs",
            description="Launch influencer engagement and customer testimonial programs.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=800.0,
        ),
    ]

    # Phase 5: Long-term Recovery & Monitoring (Weeks 6-16)
    brand_trust_rebuilding = Task(
        name="Brand Trust Rebuilding & Monitoring",
        description=(
            "Execute long-term brand trust rebuilding with community engagement and trust metrics monitoring."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=18.0,
        estimated_cost=3600.0,
        dependency_task_ids=[
            customer_engagement_program.task_id,
            digital_reputation_recovery.task_id,
        ],
    )
    brand_trust_rebuilding.subtasks = [
        Task(
            name="Community Engagement Initiatives",
            description="Launch community engagement and corporate responsibility initiatives to rebuild trust.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=12.0,
            estimated_cost=2400.0,
        ),
        Task(
            name="Trust Metrics Monitoring",
            description="Implement ongoing trust metrics monitoring and reporting system with third-party validation.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=1200.0,
        ),
    ]

    crisis_lessons_documentation = Task(
        name="Crisis Response Analysis & Protocol Updates",
        description=(
            "Document crisis response lessons learned and update protocols for future crisis preparedness."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=8.0,
        estimated_cost=1600.0,
        dependency_task_ids=[brand_trust_rebuilding.task_id],
    )
    crisis_lessons_documentation.subtasks = [
        Task(
            name="Response Effectiveness Analysis",
            description="Analyze crisis response effectiveness and identify improvement areas with stakeholder feedback.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=800.0,
        ),
        Task(
            name="Protocol Updates & Training",
            description="Update crisis management protocols and implement training programs based on lessons learned.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=800.0,
        ),
    ]

    # Additional cross-cutting tasks
    sentiment_monitoring_dashboard = Task(
        name="Real-time Sentiment Monitoring Dashboard",
        description=(
            "Create real-time sentiment monitoring dashboard across all platforms with automated alerts."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=6.0,
        estimated_cost=1200.0,
        dependency_task_ids=[crisis_assessment.task_id],
    )

    crisis_communication_hub = Task(
        name="Crisis Communication Hub Setup",
        description=(
            "Set up centralized crisis communication hub for coordinated messaging and stakeholder updates."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=4.0,
        estimated_cost=800.0,
        dependency_task_ids=[executive_team_activation.task_id],
    )

    stakeholder_feedback_integration = Task(
        name="Stakeholder Feedback Integration System",
        description=(
            "Implement system for collecting and integrating stakeholder feedback into response strategy adjustments."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=6.0,
        estimated_cost=1200.0,
        dependency_task_ids=[internal_stakeholder_communication.task_id],
    )

    for task in [
        crisis_assessment,
        executive_team_activation,
        immediate_response_strategy,
        public_communication_launch,
        internal_stakeholder_communication,
        media_relations_management,
        customer_engagement_program,
        legal_regulatory_coordination,
        digital_reputation_recovery,
        brand_trust_rebuilding,
        crisis_lessons_documentation,
        sentiment_monitoring_dashboard,
        crisis_communication_hub,
        stakeholder_feedback_integration,
    ]:
        WorkflowMutations.add_task(workflow, task)

    # Constraints for crisis response discipline and confidentiality
    workflow.constraints.extend(
        [
            Constraint(
                name="Executive Team Activated",
                description="Crisis team must be activated with defined decision-making protocols.",
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=["Executive Crisis Team Activation"],
                metadata={},
            ),
            Constraint(
                name="Public Communication Launched",
                description="Coordinated public communication must be launched across channels.",
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=["Public Communication Launch"],
                metadata={},
            ),
            Constraint(
                name="Internal Stakeholder Communication",
                description="Comprehensive internal communication to employees, partners, and investors must occur.",
                constraint_type="organizational",
                enforcement_level=0.85,
                applicable_task_types=["Internal Stakeholder Communication"],
                metadata={},
            ),
            Constraint(
                name="Media Monitoring Active",
                description="Active media relations and monitoring must be maintained with narrative control.",
                constraint_type="organizational",
                enforcement_level=0.8,
                applicable_task_types=["Media Relations & Narrative Control"],
                metadata={},
            ),
            Constraint(
                name="Digital Reputation Campaign Executed",
                description="Digital reputation recovery campaign must be executed and evidenced.",
                constraint_type="organizational",
                enforcement_level=0.8,
                applicable_task_types=["Digital Reputation Recovery Campaign"],
                metadata={},
            ),
            Constraint(
                name="PII and Secrets Redaction",
                description="Confidential information must be redacted or access-controlled in artifacts and communications.",
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=[
                    "Public Communication Launch",
                    "Internal Stakeholder Communication",
                    "Media Relations & Narrative Control",
                ],
                metadata={
                    "prohibited_keywords": [
                        "ssn",
                        "password",
                        "api key",
                        "secret key",
                        "private key",
                        "account_number",
                    ]
                },
            ),
        ]
    )

    return workflow
