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

from uuid import uuid4

from manager_agent_gym.schemas.domain.workflow import Workflow
from manager_agent_gym.schemas.domain.task import Task
from manager_agent_gym.schemas.domain.base import TaskStatus
from manager_agent_gym.schemas.preferences import Constraint
from manager_agent_gym.core.workflow.services import WorkflowMutations


def create_workflow() -> Workflow:
    """Create global product recall workflow with crisis management phases and dependencies."""

    workflow = Workflow(
        name="Global Product Recall & Market Re-entry Strategy - Automotive Safety Component",
        workflow_goal=(
            """
            Objective: Execute comprehensive global product recall for automotive safety component affecting 2M vehicles 
            across 15 countries, implement effective remediation measures, and achieve successful market re-entry with 
            restored consumer confidence and regulatory compliance.
            Primary deliverables:
            - Global regulatory notification package: NHTSA, Transport Canada, EU GPSR, and national authority filings 
              with defect characterization, risk assessment, and coordinated timeline across all jurisdictions.
            - Crisis management coordination: cross-functional recall team activation, executive communication protocols, 
              regulatory liaison management, and 24/7 incident response capability with documented decision-making authority.
            - Consumer communication campaign: multi-channel safety notifications (mail, electronic, dealer networks), 
              customer service hotline deployment, media relations strategy, and social media crisis management with 
              regulatory-compliant messaging.
            - Product retrieval logistics: reverse supply chain activation, dealer network coordination, customer return 
              processing, affected inventory identification and quarantine, and disposal/recycling protocols across 
              global markets.
            - Root cause analysis and remediation: technical failure investigation, design modification development, 
              enhanced testing protocols, supplier quality improvements, and manufacturing process corrections with 
              validation evidence.
            - Regulatory compliance documentation: recall effectiveness monitoring, consumer response tracking 
              (targeting >95% completion), regulatory status reporting, and audit trail maintenance across all markets.
            - Market re-entry strategy: product redesign validation, regulatory approval for resumed sales, enhanced 
              quality assurance protocols, customer confidence rebuilding campaign, and competitive repositioning plan.
            - Legal and financial coordination: liability management across jurisdictions, insurance claims processing, 
              litigation strategy development, and financial impact mitigation with stakeholder communication.
            
            Acceptance criteria (high-level):
            - Recall completion rate >95% across all 15 markets with regulatory sign-offs obtained; no outstanding 
              critical safety findings.
            - Consumer safety incidents eliminated with zero additional injuries/fatalities post-recall announcement; 
              product hazard fully contained.
            - Regulatory approvals secured for market re-entry in all jurisdictions; enhanced quality protocols 
              validated and operational.
            - Customer confidence metrics restored to >80% of pre-recall levels within 12 months; brand reputation 
              recovery demonstrated through independent surveys.
            - Financial impact contained within crisis management budget parameters; insurance coverage maximized 
              and litigation exposure minimized.
            - Supply chain partners retained with enhanced quality agreements; dealer network confidence maintained 
              throughout process.
            """
        ),
        owner_id=uuid4(),
    )

    # Phase 1: Crisis Assessment & Initial Response (Immediate - First 72 Hours)
    crisis_assessment = Task(
        name="Crisis Assessment & Safety Evaluation",
        description=(
            "Conduct immediate safety assessment, determine recall scope, activate crisis management team, "
            "and establish incident command structure with regulatory consultation."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=24.0,
        estimated_cost=50000.0,
    )
    crisis_assessment.subtasks = [
        Task(
            name="Safety Impact Assessment",
            description="Evaluate immediate safety risks, incident analysis, and potential for additional failures.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=8.0,
            estimated_cost=15000.0,
        ),
        Task(
            name="Recall Scope Determination",
            description="Define affected vehicle population, production date ranges, and geographic distribution.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=8.0,
            estimated_cost=20000.0,
        ),
        Task(
            name="Crisis Team Activation",
            description="Activate cross-functional crisis management team with executive authority and 24/7 operations.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=8.0,
            estimated_cost=15000.0,
        ),
    ]

    regulatory_notifications = Task(
        name="Global Regulatory Notification Package",
        description=(
            "Prepare and submit comprehensive regulatory notifications to NHTSA, Transport Canada, "
            "EU GPSR, and all 15 national authorities with coordinated timeline."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=32.0,
        estimated_cost=75000.0,
        dependency_task_ids=[crisis_assessment.task_id],
    )
    regulatory_notifications.subtasks = [
        Task(
            name="Defect Characterization Report",
            description="Technical analysis of safety defect with failure modes, risk assessment, and incident data.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=12.0,
            estimated_cost=30000.0,
        ),
        Task(
            name="Multi-Jurisdiction Filing Coordination",
            description="Coordinate regulatory submissions across 15 countries with timeline synchronization.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=12.0,
            estimated_cost=25000.0,
        ),
        Task(
            name="Regulatory Authority Liaison",
            description="Establish communication protocols with all regulatory bodies and ongoing compliance coordination.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=8.0,
            estimated_cost=20000.0,
        ),
    ]

    # Phase 2: Consumer Communication & Public Response (Days 3-14)
    consumer_communication = Task(
        name="Consumer Communication Campaign Launch",
        description=(
            "Deploy multi-channel consumer safety notifications, activate customer service infrastructure, "
            "and implement crisis communication strategy across all markets."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=40.0,
        estimated_cost=200000.0,
        dependency_task_ids=[regulatory_notifications.task_id],
    )
    consumer_communication.subtasks = [
        Task(
            name="Safety Notification Development",
            description="Create regulatory-compliant safety notifications for mail, electronic, and dealer channels.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=12.0,
            estimated_cost=50000.0,
        ),
        Task(
            name="Customer Service Infrastructure",
            description="Deploy 24/7 customer service hotlines, online portals, and dealer network support systems.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=16.0,
            estimated_cost=100000.0,
        ),
        Task(
            name="Media Relations & Crisis Communication",
            description="Execute media strategy, social media crisis management, and stakeholder communication.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=12.0,
            estimated_cost=50000.0,
        ),
    ]

    crisis_management_coordination = Task(
        name="Crisis Management Coordination & Governance",
        description=(
            "Establish crisis management governance, executive communication protocols, "
            "and decision-making authority with audit trail documentation."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=28.0,
        estimated_cost=60000.0,
        dependency_task_ids=[consumer_communication.task_id],
    )
    crisis_management_coordination.subtasks = [
        Task(
            name="Executive Communication Protocols",
            description="Implement executive briefing schedules, decision escalation procedures, and board reporting.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=10.0,
            estimated_cost=20000.0,
        ),
        Task(
            name="Cross-Functional Team Coordination",
            description="Coordinate engineering, manufacturing, legal, regulatory, and communications teams.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=12.0,
            estimated_cost=25000.0,
        ),
        Task(
            name="Decision Authority Documentation",
            description="Document all crisis decisions with rationale, approvers, and audit trail maintenance.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=15000.0,
        ),
    ]

    # Phase 3: Product Retrieval & Logistics (Weeks 2-12)
    product_retrieval_logistics = Task(
        name="Global Product Retrieval Logistics",
        description=(
            "Activate reverse supply chain operations, coordinate dealer networks, "
            "and manage customer return processing across all 15 markets."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=60.0,
        estimated_cost=500000.0,
        dependency_task_ids=[crisis_management_coordination.task_id],
    )
    product_retrieval_logistics.subtasks = [
        Task(
            name="Reverse Supply Chain Activation",
            description="Implement logistics for collecting recalled components from dealers and customers globally.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=20.0,
            estimated_cost=200000.0,
        ),
        Task(
            name="Dealer Network Coordination",
            description="Coordinate with global dealer network for customer notifications and component replacement.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=20.0,
            estimated_cost=150000.0,
        ),
        Task(
            name="Customer Return Processing",
            description="Process customer returns, component inspection, and disposal/recycling protocols.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=20.0,
            estimated_cost=150000.0,
        ),
    ]

    inventory_management = Task(
        name="Affected Inventory Management & Quarantine",
        description=(
            "Identify and quarantine all affected inventory, implement disposal protocols, "
            "and manage supply chain partner coordination."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=32.0,
        estimated_cost=100000.0,
        dependency_task_ids=[product_retrieval_logistics.task_id],
    )
    inventory_management.subtasks = [
        Task(
            name="Inventory Identification & Quarantine",
            description="Identify all affected inventory in supply chain and implement quarantine procedures.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=16.0,
            estimated_cost=50000.0,
        ),
        Task(
            name="Disposal & Recycling Protocols",
            description="Implement environmentally compliant disposal and recycling for recalled components.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=16.0,
            estimated_cost=50000.0,
        ),
    ]

    # Phase 4: Root Cause Analysis & Remediation (Weeks 2-16)
    root_cause_analysis = Task(
        name="Root Cause Analysis & Technical Investigation",
        description=(
            "Conduct comprehensive technical failure investigation, develop design modifications, "
            "and implement enhanced testing protocols with validation evidence."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=80.0,
        estimated_cost=300000.0,
        dependency_task_ids=[inventory_management.task_id],
    )
    root_cause_analysis.subtasks = [
        Task(
            name="Technical Failure Investigation",
            description="Deep-dive technical analysis of component failure modes, contributing factors, and design flaws.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=32.0,
            estimated_cost=120000.0,
        ),
        Task(
            name="Design Modification Development",
            description="Develop and validate design modifications to eliminate safety defects permanently.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=32.0,
            estimated_cost=120000.0,
        ),
        Task(
            name="Enhanced Testing Protocol Implementation",
            description="Implement enhanced testing protocols and quality validation procedures.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=16.0,
            estimated_cost=60000.0,
        ),
    ]

    supplier_quality_improvements = Task(
        name="Supplier Quality Improvements & Process Corrections",
        description=(
            "Implement supplier quality improvements, manufacturing process corrections, "
            "and enhanced quality assurance with supplier agreement updates."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=48.0,
        estimated_cost=150000.0,
        dependency_task_ids=[root_cause_analysis.task_id],
    )
    supplier_quality_improvements.subtasks = [
        Task(
            name="Supplier Quality Enhancement",
            description="Implement enhanced supplier quality requirements and monitoring protocols.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=24.0,
            estimated_cost=75000.0,
        ),
        Task(
            name="Manufacturing Process Corrections",
            description="Implement manufacturing process improvements and quality control enhancements.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=24.0,
            estimated_cost=75000.0,
        ),
    ]

    # Phase 5: Regulatory Compliance & Monitoring (Ongoing)
    compliance_monitoring = Task(
        name="Regulatory Compliance Documentation & Monitoring",
        description=(
            "Implement recall effectiveness monitoring, consumer response tracking, "
            "and regulatory status reporting across all markets."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=40.0,
        estimated_cost=80000.0,
        dependency_task_ids=[supplier_quality_improvements.task_id],
    )
    compliance_monitoring.subtasks = [
        Task(
            name="Recall Effectiveness Monitoring",
            description="Monitor recall completion rates targeting >95% across all 15 markets.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=20.0,
            estimated_cost=40000.0,
        ),
        Task(
            name="Consumer Response Tracking",
            description="Track consumer response rates and implement targeted outreach for non-respondents.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=12.0,
            estimated_cost=25000.0,
        ),
        Task(
            name="Regulatory Status Reporting",
            description="Maintain ongoing regulatory reporting and audit trail documentation.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=8.0,
            estimated_cost=15000.0,
        ),
    ]

    # Phase 6: Legal & Financial Coordination (Parallel to all phases)
    legal_financial_coordination = Task(
        name="Legal & Financial Risk Management",
        description=(
            "Manage liability across jurisdictions, process insurance claims, "
            "develop litigation strategy, and coordinate financial impact mitigation."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=56.0,
        estimated_cost=250000.0,
        dependency_task_ids=[compliance_monitoring.task_id],
    )
    legal_financial_coordination.subtasks = [
        Task(
            name="Multi-Jurisdiction Liability Management",
            description="Manage legal liability and regulatory compliance across 15 countries.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=20.0,
            estimated_cost=100000.0,
        ),
        Task(
            name="Insurance Claims & Coverage Optimization",
            description="Process insurance claims and maximize coverage for recall-related costs.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=16.0,
            estimated_cost=75000.0,
        ),
        Task(
            name="Litigation Strategy & Financial Impact",
            description="Develop litigation defense strategy and implement financial impact mitigation measures.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=20.0,
            estimated_cost=75000.0,
        ),
    ]

    # Phase 7: Market Re-entry Strategy (Months 12-18)
    market_reentry_preparation = Task(
        name="Market Re-entry Strategy & Product Validation",
        description=(
            "Prepare comprehensive market re-entry strategy including product redesign validation, "
            "regulatory approvals, and enhanced quality protocols."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=64.0,
        estimated_cost=200000.0,
        dependency_task_ids=[legal_financial_coordination.task_id],
    )
    market_reentry_preparation.subtasks = [
        Task(
            name="Product Redesign Validation",
            description="Complete validation of redesigned product with enhanced safety features.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=24.0,
            estimated_cost=80000.0,
        ),
        Task(
            name="Regulatory Approval for Sales Resumption",
            description="Secure regulatory approvals for resumed sales across all 15 markets.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=20.0,
            estimated_cost=60000.0,
        ),
        Task(
            name="Enhanced Quality Assurance Implementation",
            description="Implement and validate enhanced quality assurance protocols for ongoing production.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=20.0,
            estimated_cost=60000.0,
        ),
    ]

    customer_confidence_recovery = Task(
        name="Customer Confidence & Brand Reputation Recovery",
        description=(
            "Implement comprehensive customer confidence rebuilding campaign and competitive "
            "repositioning strategy to restore brand reputation."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=48.0,
        estimated_cost=300000.0,
        dependency_task_ids=[market_reentry_preparation.task_id],
    )
    customer_confidence_recovery.subtasks = [
        Task(
            name="Customer Confidence Rebuilding Campaign",
            description="Launch targeted campaign to rebuild customer confidence with safety messaging and guarantees.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=24.0,
            estimated_cost=150000.0,
        ),
        Task(
            name="Competitive Repositioning Strategy",
            description="Develop competitive repositioning strategy emphasizing enhanced safety and quality.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=16.0,
            estimated_cost=100000.0,
        ),
        Task(
            name="Brand Reputation Monitoring",
            description="Implement brand reputation monitoring and measurement targeting >80% confidence restoration.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=8.0,
            estimated_cost=50000.0,
        ),
    ]

    # Cross-cutting coordination and oversight tasks
    program_management = Task(
        name="Crisis Program Management & Coordination",
        description=(
            "Provide overall crisis program management, timeline coordination, "
            "and cross-functional integration throughout the recall process."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=120.0,
        estimated_cost=300000.0,
        dependency_task_ids=[crisis_assessment.task_id],
    )

    stakeholder_communication = Task(
        name="Stakeholder Communication & Relationship Management",
        description=(
            "Manage ongoing stakeholder communication including investors, suppliers, dealers, "
            "media, and regulatory authorities throughout the crisis."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=80.0,
        estimated_cost=200000.0,
        dependency_task_ids=[crisis_assessment.task_id],
    )

    quality_assurance_oversight = Task(
        name="Quality Assurance & Process Oversight",
        description=(
            "Provide independent quality assurance oversight and process validation "
            "throughout the recall and remediation process."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=60.0,
        estimated_cost=150000.0,
        dependency_task_ids=[regulatory_notifications.task_id],
    )

    # Add all tasks to workflow
    for task in [
        crisis_assessment,
        regulatory_notifications,
        consumer_communication,
        crisis_management_coordination,
        product_retrieval_logistics,
        inventory_management,
        root_cause_analysis,
        supplier_quality_improvements,
        compliance_monitoring,
        legal_financial_coordination,
        market_reentry_preparation,
        customer_confidence_recovery,
        program_management,
        stakeholder_communication,
        quality_assurance_oversight,
    ]:
        WorkflowMutations.add_task(workflow, task)

    # Constraints for recall governance, compliance, and confidentiality
    workflow.constraints.extend(
        [
            Constraint(
                name="Regulatory Notifications Submitted",
                description="Comprehensive regulatory notifications must be prepared and submitted across all markets.",
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=["Global Regulatory Notification Package"],
                metadata={},
            ),
            Constraint(
                name="Consumer Safety Messaging Compliance",
                description="Consumer communication campaign must be launched with regulatory-compliant safety messaging.",
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=["Consumer Communication Campaign Launch"],
                metadata={},
            ),
            Constraint(
                name="Recall Effectiveness Monitoring",
                description="Recall effectiveness monitoring and regulatory reporting must be implemented.",
                constraint_type="organizational",
                enforcement_level=0.9,
                applicable_task_types=[
                    "Regulatory Compliance Documentation & Monitoring"
                ],
                metadata={},
            ),
            Constraint(
                name="Market Re-entry Approvals",
                description="Regulatory approval must be secured prior to market re-entry and sales resumption.",
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=["Regulatory Approval for Sales Resumption"],
                metadata={},
            ),
            Constraint(
                name="Decision Authority Documented",
                description="Crisis governance must document decision authority and audit trails.",
                constraint_type="organizational",
                enforcement_level=0.85,
                applicable_task_types=[
                    "Crisis Management Coordination & Governance",
                    "Decision Authority Documentation",
                ],
                metadata={},
            ),
            Constraint(
                name="PII and Secrets Redaction",
                description="Confidential information must be redacted or access-controlled in artifacts and communications.",
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=[
                    "Regulatory Compliance Documentation & Monitoring",
                    "Global Regulatory Notification Package",
                    "Consumer Communication Campaign Launch",
                ],
                metadata={
                    "prohibited_keywords": [
                        "ssn",
                        "social security",
                        "passport",
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
