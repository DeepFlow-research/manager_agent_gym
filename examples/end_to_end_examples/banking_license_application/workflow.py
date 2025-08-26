"""
Banking License Application Demo
Real-world use case: European mid-size commercial bank seeking to establish
federal branch operations in the US market.
Demonstrates:
- Long-term strategic project management with 18-24 month regulatory timelines
- Multi-jurisdiction stakeholder coordination balancing conflicting regulatory requirements
- Sequential dependency management with critical path optimization across complex approvals
- Resource allocation strategy balancing regulatory compliance with operational readiness
- Executive decision-making under regulatory uncertainty with documented governance protocols
- Cross-functional team orchestration spanning legal, regulatory, operational, and business domains
"""

from uuid import uuid4

from manager_agent_gym.schemas.core.workflow import Workflow
from manager_agent_gym.schemas.core.tasks import Task
from manager_agent_gym.schemas.core.base import TaskStatus
from manager_agent_gym.schemas.preferences import Constraint


def create_banking_license_application_workflow() -> Workflow:
    """Create banking license application workflow with regulatory phases and dependencies."""

    workflow = Workflow(
        name="US Banking License Application - European Commercial Bank",
        workflow_goal=(
            """
            Objective: Execute comprehensive banking license application and US market entry strategy for European 
            mid-size commercial bank seeking to establish federal branch operations, including regulatory approvals, 
            operational readiness, and compliance framework implementation.
            Primary deliverables:
            - Complete federal branch license application package (OCC Form, business plan, management profiles, 
              capital documentation) with supporting legal and financial documentation.
            - Comprehensive due diligence portfolio: beneficial ownership verification, AML/BSA compliance program, 
              customer identification procedures, and enhanced due diligence protocols.
            - Regulatory compliance framework: policies, procedures, and controls addressing Federal Reserve 
              Regulation K, OCC guidelines, and FDIC requirements with documented governance structure.
            - Operational readiness assessment: IT infrastructure, staffing plan, physical office setup, 
              correspondent banking relationships, and service delivery capabilities.
            - Risk management framework: credit risk policies, market risk controls, liquidity management 
              procedures, operational risk assessment, and regulatory reporting systems.
            - Stakeholder engagement strategy: regulator communication plan, legal counsel coordination, 
              consultant management, and internal executive alignment.
            - US market entry business plan: competitive analysis, target customer segments, product offerings, 
              revenue projections, and 3-year growth strategy.
            - Capital and funding structure: $50M minimum capital requirement, CED (Capital Equivalent Deposit) 
              arrangements, liquidity facilities, and ongoing funding sources.
            
            Acceptance criteria (high-level):
            - OCC preliminary and final approval obtained with all regulatory conditions satisfied; Federal Reserve 
              non-objection secured.
            - Home country regulator (ECB/national authority) approval for US market entry with comprehensive 
              supervision attestation.
            - Complete AML/BSA compliance program implemented with independent validation; no outstanding 
              regulatory concerns.
            - Operational infrastructure fully deployed and tested; correspondent banking relationships established 
              and operational.
            - Senior management team hired and background-checked; board governance framework established and 
              documented.
            - Capital requirements satisfied with funds deposited; FDIC insurance application approved (if applicable).
            """
        ),
        owner_id=uuid4(),
    )

    # Phase 1: Pre-Application Preparation & Strategy
    regulatory_strategy = Task(
        name="Regulatory Strategy & Feasibility Assessment",
        description=(
            "Conduct comprehensive feasibility analysis, engage preliminary regulatory consultations, "
            "and develop detailed regulatory strategy and timeline."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=20.0,
        estimated_cost=5000.0,
    )
    regulatory_strategy.subtasks = [
        Task(
            name="Regulatory Landscape Analysis",
            description="Analyze OCC, Federal Reserve, and FDIC requirements; assess regulatory environment and recent precedents.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=8.0,
            estimated_cost=2000.0,
        ),
        Task(
            name="Home Country Coordination",
            description="Engage ECB/national supervisor for US expansion approval; establish supervision coordination framework.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=1500.0,
        ),
        Task(
            name="Pre-Application Consultations",
            description="Conduct preliminary meetings with OCC and Federal Reserve; document feedback and requirements.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=1500.0,
        ),
    ]

    legal_structure = Task(
        name="Legal Structure & Documentation Framework",
        description=(
            "Establish US legal entity structure, corporate governance framework, "
            "and foundational legal documentation."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=16.0,
        estimated_cost=4000.0,
        dependency_task_ids=[regulatory_strategy.task_id],
    )
    legal_structure.subtasks = [
        Task(
            name="Entity Structure Design",
            description="Design optimal legal structure for federal branch operations; incorporate US entities as required.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=1500.0,
        ),
        Task(
            name="Corporate Governance Framework",
            description="Establish board structure, committee charters, and governance policies for US operations.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=5.0,
            estimated_cost=1250.0,
        ),
        Task(
            name="Legal Documentation Package",
            description="Prepare articles of incorporation, operating agreements, and foundational legal documents.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=5.0,
            estimated_cost=1250.0,
        ),
    ]

    # Phase 2: Application Preparation
    application_package = Task(
        name="OCC Application Package Preparation",
        description=(
            "Compile comprehensive OCC application including business plan, financial projections, "
            "management profiles, and supporting documentation."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=24.0,
        estimated_cost=6000.0,
        dependency_task_ids=[legal_structure.task_id],
    )
    application_package.subtasks = [
        Task(
            name="Business Plan Development",
            description="Develop comprehensive business plan with market analysis, strategy, and 3-year financial projections.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=10.0,
            estimated_cost=2500.0,
        ),
        Task(
            name="Management Team Documentation",
            description="Compile management profiles, background checks, regulatory history, and organizational structure.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=8.0,
            estimated_cost=2000.0,
        ),
        Task(
            name="Financial Documentation",
            description="Prepare capital adequacy documentation, funding commitments, and financial statements.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=1500.0,
        ),
    ]

    due_diligence = Task(
        name="Due Diligence & Background Verification",
        description=(
            "Complete comprehensive due diligence on beneficial ownership, management team, "
            "and corporate affiliations with regulatory validation."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=18.0,
        estimated_cost=4500.0,
        dependency_task_ids=[application_package.task_id],
    )
    due_diligence.subtasks = [
        Task(
            name="Beneficial Ownership Analysis",
            description="Conduct thorough beneficial ownership verification and regulatory fitness assessment.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=8.0,
            estimated_cost=2000.0,
        ),
        Task(
            name="Management Background Checks",
            description="Complete comprehensive background investigations for all key management personnel.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=1500.0,
        ),
        Task(
            name="Corporate Affiliations Review",
            description="Analyze corporate structure, affiliations, and potential conflicts of interest.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=1000.0,
        ),
    ]

    # Phase 3: Compliance Framework Development
    aml_bsa_program = Task(
        name="AML/BSA Compliance Program",
        description=(
            "Develop comprehensive AML/BSA compliance program including policies, procedures, "
            "monitoring systems, and training protocols."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=20.0,
        estimated_cost=5000.0,
        dependency_task_ids=[due_diligence.task_id],
    )
    aml_bsa_program.subtasks = [
        Task(
            name="Policy Framework Development",
            description="Develop AML/BSA policies, procedures, and compliance manual tailored to US operations.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=8.0,
            estimated_cost=2000.0,
        ),
        Task(
            name="CIP & Enhanced Due Diligence",
            description="Implement Customer Identification Program and enhanced due diligence procedures.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=1500.0,
        ),
        Task(
            name="Monitoring & Reporting Systems",
            description="Establish transaction monitoring, suspicious activity reporting, and regulatory reporting systems.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=1500.0,
        ),
    ]

    regulatory_compliance = Task(
        name="Regulatory Compliance Framework",
        description=(
            "Implement comprehensive compliance framework addressing Federal Reserve Regulation K, "
            "OCC guidelines, and FDIC requirements."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=16.0,
        estimated_cost=4000.0,
        dependency_task_ids=[aml_bsa_program.task_id],
    )
    regulatory_compliance.subtasks = [
        Task(
            name="Fed Regulation K Compliance",
            description="Implement Federal Reserve Regulation K requirements for international banking operations.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=1500.0,
        ),
        Task(
            name="OCC Guidelines Implementation",
            description="Establish compliance framework for OCC supervisory guidance and examination requirements.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=5.0,
            estimated_cost=1250.0,
        ),
        Task(
            name="FDIC Requirements (if applicable)",
            description="Assess and implement FDIC insurance requirements and compliance obligations.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=5.0,
            estimated_cost=1250.0,
        ),
    ]

    # Phase 4: Risk Management Framework
    risk_management = Task(
        name="Risk Management Framework Development",
        description=(
            "Establish comprehensive risk management framework covering credit, market, operational, "
            "and liquidity risks with appropriate controls and reporting."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=22.0,
        estimated_cost=5500.0,
        dependency_task_ids=[regulatory_compliance.task_id],
    )
    risk_management.subtasks = [
        Task(
            name="Credit Risk Policies",
            description="Develop credit risk policies, underwriting standards, and portfolio management procedures.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=8.0,
            estimated_cost=2000.0,
        ),
        Task(
            name="Market & Liquidity Risk Controls",
            description="Implement market risk controls, liquidity management procedures, and stress testing framework.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=7.0,
            estimated_cost=1750.0,
        ),
        Task(
            name="Operational Risk Assessment",
            description="Conduct operational risk assessment and implement operational risk management framework.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=7.0,
            estimated_cost=1750.0,
        ),
    ]

    regulatory_reporting = Task(
        name="Regulatory Reporting Systems",
        description=(
            "Establish regulatory reporting systems and procedures for Call Reports, "
            "Federal Reserve reporting, and other regulatory requirements."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=14.0,
        estimated_cost=3500.0,
        dependency_task_ids=[risk_management.task_id],
    )

    # Phase 5: Operational Readiness
    operational_infrastructure = Task(
        name="Operational Infrastructure Setup",
        description=(
            "Establish complete operational infrastructure including IT systems, physical offices, "
            "and operational procedures."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=28.0,
        estimated_cost=7000.0,
        dependency_task_ids=[regulatory_reporting.task_id],
    )
    operational_infrastructure.subtasks = [
        Task(
            name="IT Infrastructure & Systems",
            description="Deploy core banking systems, security infrastructure, and regulatory reporting capabilities.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=12.0,
            estimated_cost=3000.0,
        ),
        Task(
            name="Physical Office Setup",
            description="Establish physical offices, security systems, and operational facilities in target markets.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=8.0,
            estimated_cost=2000.0,
        ),
        Task(
            name="Operational Procedures",
            description="Develop operational procedures, workflows, and service delivery capabilities.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=8.0,
            estimated_cost=2000.0,
        ),
    ]

    banking_relationships = Task(
        name="Correspondent Banking & Relationships",
        description=(
            "Establish correspondent banking relationships, payment system access, "
            "and operational banking partnerships."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=16.0,
        estimated_cost=4000.0,
        dependency_task_ids=[operational_infrastructure.task_id],
    )
    banking_relationships.subtasks = [
        Task(
            name="Correspondent Bank Selection",
            description="Identify and negotiate correspondent banking relationships for clearing and settlement.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=8.0,
            estimated_cost=2000.0,
        ),
        Task(
            name="Payment System Access",
            description="Establish access to Federal Reserve payment systems and other critical infrastructure.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=8.0,
            estimated_cost=2000.0,
        ),
    ]

    # Phase 6: Capital Structure & Funding
    capital_structure = Task(
        name="Capital Structure & CED Arrangements",
        description=(
            "Establish capital structure meeting $50M minimum requirement, "
            "arrange CED facilities, and secure ongoing funding sources."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=18.0,
        estimated_cost=4500.0,
        dependency_task_ids=[banking_relationships.task_id],
    )
    capital_structure.subtasks = [
        Task(
            name="Capital Funding & Documentation",
            description="Secure and document $50M minimum capital requirement with regulatory-compliant structure.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=8.0,
            estimated_cost=2000.0,
        ),
        Task(
            name="CED Arrangements",
            description="Establish Capital Equivalent Deposit arrangements and ongoing liquidity facilities.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=1500.0,
        ),
        Task(
            name="Ongoing Funding Strategy",
            description="Develop ongoing funding strategy and establish committed funding sources.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=1000.0,
        ),
    ]

    # Phase 7: Staffing & Human Resources
    staffing_plan = Task(
        name="Staffing Plan & Human Resources",
        description=(
            "Implement comprehensive staffing plan, hire senior management team, "
            "and establish HR policies and procedures."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=20.0,
        estimated_cost=5000.0,
        dependency_task_ids=[capital_structure.task_id],
    )
    staffing_plan.subtasks = [
        Task(
            name="Senior Management Recruitment",
            description="Recruit and hire senior management team with regulatory approval and background checks.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=10.0,
            estimated_cost=2500.0,
        ),
        Task(
            name="Operational Staff Planning",
            description="Develop staffing plan and recruit operational staff for branch operations.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=1500.0,
        ),
        Task(
            name="HR Policies & Training",
            description="Establish HR policies, compensation framework, and comprehensive training programs.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=1000.0,
        ),
    ]

    # Phase 8: Market Entry Strategy
    market_entry_strategy = Task(
        name="US Market Entry Business Strategy",
        description=(
            "Develop comprehensive market entry strategy including competitive analysis, "
            "target segments, and product development."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=24.0,
        estimated_cost=6000.0,
        dependency_task_ids=[staffing_plan.task_id],
    )
    market_entry_strategy.subtasks = [
        Task(
            name="Market Analysis & Competitive Intelligence",
            description="Conduct comprehensive US market analysis and competitive landscape assessment.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=8.0,
            estimated_cost=2000.0,
        ),
        Task(
            name="Target Segment Strategy",
            description="Define target customer segments, value propositions, and go-to-market strategy.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=8.0,
            estimated_cost=2000.0,
        ),
        Task(
            name="Product Development & Pricing",
            description="Develop product offerings, pricing strategy, and revenue projections for 3-year period.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=8.0,
            estimated_cost=2000.0,
        ),
    ]

    # Phase 9: Final Application & Approval
    application_submission = Task(
        name="Application Submission & Regulatory Process",
        description=(
            "Submit completed application packages and manage regulatory review process "
            "through to final approval."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=16.0,
        estimated_cost=4000.0,
        dependency_task_ids=[market_entry_strategy.task_id],
    )
    application_submission.subtasks = [
        Task(
            name="OCC Application Submission",
            description="Submit complete OCC application package and manage preliminary review process.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=1500.0,
        ),
        Task(
            name="Federal Reserve Coordination",
            description="Coordinate with Federal Reserve for non-objection and supervision arrangements.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=5.0,
            estimated_cost=1250.0,
        ),
        Task(
            name="Regulatory Response Management",
            description="Manage regulatory questions, provide supplemental information, and address conditions.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=5.0,
            estimated_cost=1250.0,
        ),
    ]

    final_approvals = Task(
        name="Final Approvals & Launch Preparation",
        description=(
            "Obtain final regulatory approvals, satisfy all conditions, "
            "and prepare for operational launch."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=12.0,
        estimated_cost=3000.0,
        dependency_task_ids=[application_submission.task_id],
    )
    final_approvals.subtasks = [
        Task(
            name="Condition Satisfaction",
            description="Satisfy all regulatory conditions and obtain final OCC approval.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=1500.0,
        ),
        Task(
            name="Launch Readiness Assessment",
            description="Conduct final operational readiness assessment and launch preparation.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=1500.0,
        ),
    ]

    # Cross-cutting coordination and oversight tasks
    project_management = Task(
        name="Project Management & Coordination",
        description=(
            "Provide overall project management, stakeholder coordination, "
            "and progress tracking throughout the application process."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=30.0,
        estimated_cost=7500.0,
        dependency_task_ids=[regulatory_strategy.task_id],
    )

    stakeholder_engagement = Task(
        name="Stakeholder Engagement & Communication",
        description=(
            "Manage stakeholder engagement including board reporting, regulatory communication, "
            "and internal coordination throughout the process."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=20.0,
        estimated_cost=5000.0,
        dependency_task_ids=[regulatory_strategy.task_id],
    )

    quality_assurance = Task(
        name="Quality Assurance & Documentation Control",
        description=(
            "Provide quality assurance oversight, documentation control, "
            "and compliance validation throughout the application process."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=16.0,
        estimated_cost=4000.0,
        dependency_task_ids=[legal_structure.task_id],
    )

    # Add all tasks to workflow
    for task in [
        regulatory_strategy,
        legal_structure,
        application_package,
        due_diligence,
        aml_bsa_program,
        regulatory_compliance,
        risk_management,
        regulatory_reporting,
        operational_infrastructure,
        banking_relationships,
        capital_structure,
        staffing_plan,
        market_entry_strategy,
        application_submission,
        final_approvals,
        project_management,
        stakeholder_engagement,
        quality_assurance,
    ]:
        workflow.add_task(task)

    # Constraints for regulatory approvals and compliance framework
    workflow.constraints.extend(
        [
            Constraint(
                name="OCC Application Submitted",
                description="Completed OCC application must be submitted and tracked.",
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=["OCC Application Submission"],
                metadata={},
            ),
            Constraint(
                name="AML/BSA Program Implemented",
                description="Comprehensive AML/BSA compliance program must be implemented and documented.",
                constraint_type="regulatory",
                enforcement_level=0.95,
                applicable_task_types=["AML/BSA Compliance Program"],
                metadata={},
            ),
            Constraint(
                name="Regulatory Compliance Framework Implemented",
                description="Compliance framework addressing Fed Reg K, OCC, and FDIC must be in place.",
                constraint_type="regulatory",
                enforcement_level=0.9,
                applicable_task_types=["Regulatory Compliance Framework"],
                metadata={},
            ),
            Constraint(
                name="Capital Funding Documented",
                description="$50M minimum capital must be documented with compliant structure.",
                constraint_type="regulatory",
                enforcement_level=0.9,
                applicable_task_types=["Capital Funding & Documentation"],
                metadata={},
            ),
            Constraint(
                name="Final Approvals & Launch Readiness",
                description="Final approvals and launch readiness assessment must be completed.",
                constraint_type="organizational",
                enforcement_level=0.85,
                applicable_task_types=["Final Approvals & Launch Preparation"],
                metadata={},
            ),
            Constraint(
                name="PII and Secrets Redaction",
                description="Confidential information must be redacted or access-controlled in artifacts and communications.",
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=[
                    "OCC Application Package Preparation",
                    "Due Diligence & Background Verification",
                    "AML/BSA Compliance Program",
                ],
                metadata={
                    "prohibited_keywords": [
                        "ssn",
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
