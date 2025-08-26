"""
Technology Company Acquisition & Integration Demo
Real-world use case: $150M SaaS platform company acquisition and integration.
Demonstrates:
- Complex multi-workstream project management across technical, financial, and regulatory domains
- Cross-functional team coordination with diverse expertise requirements and stakeholder management
- Timeline-critical integration planning with cascading dependencies and risk mitigation strategies
- Regulatory compliance management across multiple jurisdictions with approval workflow coordination
- Technology systems integration with service continuity requirements and minimal customer disruption
- Human capital retention and cultural integration during high-uncertainty transition periods
- Customer relationship preservation through transparent communication and service excellence maintenance
- Strategic value realization through synergy identification and performance optimization
"""

from uuid import uuid4

from manager_agent_gym.schemas.core.workflow import Workflow
from manager_agent_gym.schemas.core.tasks import Task
from manager_agent_gym.schemas.core.base import TaskStatus
from manager_agent_gym.schemas.preferences import Constraint


def create_tech_acquisition_integration_workflow() -> Workflow:
    """Create technology acquisition and integration workflow with hierarchical phases and dependencies."""

    workflow = Workflow(
        name="Technology Company Acquisition & Integration",
        workflow_goal=(
            """
            Objective: Execute comprehensive acquisition of $150M SaaS platform company serving 50K+ enterprise customers across North America and Europe, conduct thorough technology and business due diligence, manage regulatory compliance, and achieve successful integration with retained talent and customer base within 6-month timeline.
            Primary deliverables:
            - Technology due diligence package: software architecture assessment, code quality analysis, cybersecurity audit, IP ownership verification, infrastructure scalability evaluation, and technical debt quantification with integration complexity mapping.
            - Business and financial due diligence: SaaS metrics validation (ARR, churn, CAC, LTV), customer contract analysis, recurring revenue sustainability, operational workflow assessment, and competitive positioning evaluation.
            - Regulatory compliance framework: antitrust clearance coordination, HSR filing preparation, data privacy compliance verification (GDPR/CCPA), software licensing validation, and cross-border regulatory requirements.
            - Integration management office establishment: executive steering committee formation, cross-functional integration teams, governance structure definition, and project management infrastructure.
            - Technology systems integration strategy: platform compatibility roadmap, data migration planning, API integration design, security infrastructure harmonization, and service continuity protocols.
            - Human capital integration program: talent retention strategies, cultural assessment, organizational design, compensation harmonization, and leadership transition planning.
            - Customer relationship preservation: customer notification strategy, service continuity assurance, account management transition, and value proposition enhancement.
            - Market positioning and synergy realization: competitive advantage articulation, product roadmap integration, cross-selling opportunities, and revenue enhancement strategies.
            Acceptance criteria (high‑level):
            - Technology integration completed with >99.5% service uptime maintained; zero customer data loss or security incidents.
            - Key talent retention >85% for technical leadership; customer churn <5% during integration period.
            - All regulatory approvals secured without conditions; IP ownership fully validated and transferred.
            - Integration budget variance <10% of approved allocation; synergy targets achieved within 12 months.
            - Cultural integration success with unified values and collaborative workflows.
            - Post-integration revenue growth trajectory maintained or improved.
            Constraints (soft):
            - Integration timeline: critical systems integration within 90 days, complete operational integration within 6 months.
            - Regulatory dependencies: adapt to HSR review timeline variability; maintain compliance readiness.
            - Business continuity: prioritize customer-facing system stability; maintain competitive market position.
            """
        ),
        owner_id=uuid4(),
    )

    # Phase 1: Pre-Acquisition Due Diligence
    technology_due_diligence = Task(
        name="Technology Due Diligence Assessment",
        description=(
            "Conduct comprehensive technology assessment including software architecture, code quality, "
            "cybersecurity posture, IP ownership, infrastructure scalability, and technical debt analysis."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=20.0,
        estimated_cost=3000.0,
    )
    technology_due_diligence.subtasks = [
        Task(
            name="Software Architecture Analysis",
            description="Assess software architecture patterns, scalability design, and technical implementation quality.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=8.0,
            estimated_cost=1200.0,
        ),
        Task(
            name="Code Quality & Technical Debt Assessment",
            description="Evaluate codebase quality, technical debt levels, and development practices.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=900.0,
        ),
        Task(
            name="Cybersecurity & Infrastructure Audit",
            description="Conduct security audit and infrastructure scalability evaluation with compliance assessment.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=900.0,
        ),
    ]

    business_due_diligence = Task(
        name="Business & Financial Due Diligence",
        description=(
            "Validate SaaS metrics, analyze customer contracts, assess revenue sustainability, "
            "and evaluate operational workflows and competitive positioning."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=16.0,
        estimated_cost=2400.0,
    )
    business_due_diligence.subtasks = [
        Task(
            name="SaaS Metrics Validation",
            description="Validate ARR, churn rates, CAC, LTV, and other key SaaS performance indicators.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=900.0,
        ),
        Task(
            name="Customer Contract Analysis",
            description="Analyze customer contracts, revenue recognition patterns, and contract renewal dynamics.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=5.0,
            estimated_cost=750.0,
        ),
        Task(
            name="Operational Workflow Assessment",
            description="Evaluate operational processes, workflow efficiency, and organizational capabilities.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=5.0,
            estimated_cost=750.0,
        ),
    ]

    regulatory_compliance_framework = Task(
        name="Regulatory Compliance & Legal Framework",
        description=(
            "Coordinate antitrust clearance, prepare HSR filings, verify data privacy compliance, "
            "validate software licensing, and manage cross-border regulatory requirements."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=14.0,
        estimated_cost=2100.0,
        dependency_task_ids=[
            technology_due_diligence.task_id,
            business_due_diligence.task_id,
        ],
    )
    regulatory_compliance_framework.subtasks = [
        Task(
            name="Antitrust & HSR Filing Preparation",
            description="Prepare HSR filings and coordinate antitrust clearance processes with regulatory authorities.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=8.0,
            estimated_cost=1200.0,
        ),
        Task(
            name="Data Privacy & Licensing Compliance",
            description="Verify GDPR/CCPA compliance and validate software licensing arrangements.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=900.0,
        ),
    ]

    # Phase 2: Integration Planning & Setup
    integration_management_office = Task(
        name="Integration Management Office Setup",
        description=(
            "Establish executive steering committee, form cross-functional teams, define governance structure, "
            "and create project management infrastructure with clear accountability."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=10.0,
        estimated_cost=1500.0,
        dependency_task_ids=[regulatory_compliance_framework.task_id],
    )
    integration_management_office.subtasks = [
        Task(
            name="Governance Structure Definition",
            description="Define integration governance structure, decision-making frameworks, and escalation procedures.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
        Task(
            name="Cross-Functional Team Formation",
            description="Form integration teams across technology, business, and operational workstreams.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=450.0,
        ),
        Task(
            name="Project Management Infrastructure",
            description="Establish project management tools, communication protocols, and progress tracking systems.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=450.0,
        ),
    ]

    technology_integration_strategy = Task(
        name="Technology Systems Integration Strategy",
        description=(
            "Develop platform compatibility roadmap, plan data migration, design API integration, "
            "harmonize security infrastructure, and establish service continuity protocols."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=18.0,
        estimated_cost=2700.0,
        dependency_task_ids=[
            technology_due_diligence.task_id,
            integration_management_office.task_id,
        ],
    )
    technology_integration_strategy.subtasks = [
        Task(
            name="Platform Compatibility Assessment",
            description="Assess platform compatibility and develop integration architecture roadmap.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=900.0,
        ),
        Task(
            name="Data Migration Planning",
            description="Plan comprehensive data migration strategy with validation and rollback procedures.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=900.0,
        ),
        Task(
            name="API Integration Design",
            description="Design API integration architecture and security infrastructure harmonization.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=900.0,
        ),
    ]

    human_capital_integration = Task(
        name="Human Capital Integration Program",
        description=(
            "Develop talent retention strategies, conduct cultural assessment, design organizational structure, "
            "harmonize compensation, and plan leadership transition."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=16.0,
        estimated_cost=2400.0,
        dependency_task_ids=[integration_management_office.task_id],
    )
    human_capital_integration.subtasks = [
        Task(
            name="Talent Retention Strategy",
            description="Develop comprehensive talent retention strategy for key personnel and technical leadership.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=900.0,
        ),
        Task(
            name="Cultural Assessment & Alignment",
            description="Conduct cultural assessment and develop alignment strategy for organizational integration.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=5.0,
            estimated_cost=750.0,
        ),
        Task(
            name="Organizational Design & Compensation",
            description="Design integrated organizational structure and harmonize compensation frameworks.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=5.0,
            estimated_cost=750.0,
        ),
    ]

    # Phase 3: Customer & Market Integration
    customer_relationship_preservation = Task(
        name="Customer Relationship Preservation",
        description=(
            "Develop customer notification strategy, ensure service continuity, manage account transitions, "
            "and enhance value propositions with relationship management."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=12.0,
        estimated_cost=1800.0,
        dependency_task_ids=[technology_integration_strategy.task_id],
    )
    customer_relationship_preservation.subtasks = [
        Task(
            name="Customer Communication Strategy",
            description="Develop customer notification strategy and communication plan for integration process.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
        Task(
            name="Service Continuity Assurance",
            description="Implement service continuity protocols and account management transition procedures.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
        Task(
            name="Value Proposition Enhancement",
            description="Develop enhanced value propositions and relationship management assignments.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
    ]

    market_positioning_synergies = Task(
        name="Market Positioning & Synergy Realization",
        description=(
            "Articulate competitive advantages, integrate product roadmaps, identify cross-selling opportunities, "
            "and develop revenue enhancement strategies with performance tracking."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=14.0,
        estimated_cost=2100.0,
        dependency_task_ids=[
            customer_relationship_preservation.task_id,
            human_capital_integration.task_id,
        ],
    )
    market_positioning_synergies.subtasks = [
        Task(
            name="Competitive Advantage Integration",
            description="Articulate integrated competitive advantages and market positioning strategy.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=5.0,
            estimated_cost=750.0,
        ),
        Task(
            name="Product Roadmap Integration",
            description="Integrate product roadmaps and identify innovation synergies and cross-selling opportunities.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=5.0,
            estimated_cost=750.0,
        ),
        Task(
            name="Revenue Enhancement Strategy",
            description="Develop revenue enhancement strategies and performance tracking mechanisms.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
    ]

    # Phase 4: Implementation & Validation
    systems_integration_execution = Task(
        name="Systems Integration Execution",
        description=(
            "Execute technology integration, data migration, security harmonization, "
            "and service continuity with minimal customer disruption."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=24.0,
        estimated_cost=3600.0,
        dependency_task_ids=[technology_integration_strategy.task_id],
    )
    systems_integration_execution.subtasks = [
        Task(
            name="Critical Systems Integration",
            description="Execute critical systems integration with service uptime maintenance and monitoring.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=12.0,
            estimated_cost=1800.0,
        ),
        Task(
            name="Data Migration & Validation",
            description="Execute data migration with comprehensive validation and integrity verification.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=8.0,
            estimated_cost=1200.0,
        ),
        Task(
            name="Security Infrastructure Harmonization",
            description="Harmonize security infrastructure and implement unified security protocols.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
    ]

    organizational_integration_execution = Task(
        name="Organizational Integration Execution",
        description=(
            "Execute organizational integration, leadership transitions, cultural alignment, "
            "and employee engagement with retention monitoring."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=16.0,
        estimated_cost=2400.0,
        dependency_task_ids=[human_capital_integration.task_id],
    )
    organizational_integration_execution.subtasks = [
        Task(
            name="Leadership Transition Implementation",
            description="Implement leadership transition plan and unified management structure.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=900.0,
        ),
        Task(
            name="Employee Integration & Engagement",
            description="Execute employee integration programs and monitor retention metrics.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=10.0,
            estimated_cost=1500.0,
        ),
    ]

    # Phase 5: Performance Validation & Optimization
    integration_validation = Task(
        name="Integration Performance Validation",
        description=(
            "Validate integration success metrics, assess synergy realization, "
            "and optimize performance with stakeholder satisfaction measurement."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=12.0,
        estimated_cost=1800.0,
        dependency_task_ids=[
            systems_integration_execution.task_id,
            organizational_integration_execution.task_id,
        ],
    )
    integration_validation.subtasks = [
        Task(
            name="Success Metrics Validation",
            description="Validate integration success metrics including uptime, retention, and satisfaction scores.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=900.0,
        ),
        Task(
            name="Synergy Realization Assessment",
            description="Assess synergy realization and revenue enhancement achievement with optimization recommendations.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=900.0,
        ),
    ]

    # Additional cross-cutting tasks
    regulatory_approval_coordination = Task(
        name="Regulatory Approval Coordination",
        description=(
            "Coordinate ongoing regulatory approvals, maintain compliance status, "
            "and manage jurisdiction-specific requirements throughout integration."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=8.0,
        estimated_cost=1200.0,
        dependency_task_ids=[regulatory_compliance_framework.task_id],
    )

    stakeholder_communication_management = Task(
        name="Stakeholder Communication Management",
        description=(
            "Manage ongoing stakeholder communications, progress reporting, "
            "and issue escalation throughout the integration process."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=10.0,
        estimated_cost=1500.0,
        dependency_task_ids=[integration_management_office.task_id],
    )

    for task in [
        technology_due_diligence,
        business_due_diligence,
        regulatory_compliance_framework,
        integration_management_office,
        technology_integration_strategy,
        human_capital_integration,
        customer_relationship_preservation,
        market_positioning_synergies,
        systems_integration_execution,
        organizational_integration_execution,
        integration_validation,
        regulatory_approval_coordination,
        stakeholder_communication_management,
    ]:
        workflow.add_task(task)

    # Constraints for acquisition regulatory, governance, and confidentiality controls
    workflow.constraints.extend(
        [
            Constraint(
                name="Antitrust & HSR Filings",
                description="Antitrust clearance and HSR filing preparation must be completed.",
                constraint_type="regulatory",
                enforcement_level=0.95,
                applicable_task_types=["Antitrust & HSR Filing Preparation"],
                metadata={},
            ),
            Constraint(
                name="Data Privacy & Licensing Compliance",
                description="GDPR/CCPA compliance and licensing validations must be verified.",
                constraint_type="regulatory",
                enforcement_level=0.9,
                applicable_task_types=["Data Privacy & Licensing Compliance"],
                metadata={},
            ),
            Constraint(
                name="Integration Governance Established",
                description="Integration governance, teams, and PMO must be established.",
                constraint_type="organizational",
                enforcement_level=0.85,
                applicable_task_types=[
                    "Integration Management Office Setup",
                    "Governance Structure Definition",
                ],
                metadata={},
            ),
            Constraint(
                name="Critical Systems Integration Executed",
                description="Critical systems integration must be executed with service continuity protocols.",
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=["Critical Systems Integration"],
                metadata={},
            ),
            Constraint(
                name="Regulatory Approval Coordination Active",
                description="Ongoing regulatory approval coordination must be in place throughout integration.",
                constraint_type="regulatory",
                enforcement_level=0.8,
                applicable_task_types=["Regulatory Approval Coordination"],
                metadata={},
            ),
            Constraint(
                name="PII and Secrets Redaction",
                description="Confidential information must be redacted or access-controlled in artifacts and communications.",
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=[
                    "Technology Due Diligence Assessment",
                    "Business & Financial Due Diligence",
                    "Integration Management Office Setup",
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
