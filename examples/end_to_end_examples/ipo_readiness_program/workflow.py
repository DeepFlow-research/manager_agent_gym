"""
IPO Readiness Program Demo

Real-world use case: Mid-size growth company preparing for U.S. public listing.

Demonstrates:
- Complex regulatory compliance coordination under strict SEC deadlines
- Multi-stakeholder team management across legal, audit, governance, and finance
- Risk-based decision making with materiality assessments and disclosure judgments
- Document workflow orchestration with approval dependencies and version control
- Crisis management when material weaknesses or compliance gaps are discovered
- Strategic timing decisions balancing transparency requirements with competitive positioning
"""

from uuid import uuid4, UUID

from manager_agent_gym.schemas.core.workflow import Workflow
from manager_agent_gym.schemas.core.tasks import Task
from manager_agent_gym.schemas.core.base import TaskStatus
from manager_agent_gym.schemas.preferences import Constraint


def create_workflow() -> Workflow:
    """Create IPO Readiness workflow with SEC compliance phases and dependencies."""

    workflow = Workflow(
        name="IPO Readiness Program - US Public Listing",
        workflow_goal=(
            """
            Objective: Execute a structured IPO readiness program to prepare a mid-size growth company for listing on a
            U.S. exchange, ensuring financial, governance, disclosure, and operational requirements are met and evidenced
            for SEC review, underwriter diligence, and investor confidence.

            Primary deliverables:
            - S-1 registration statement with complete narrative (Business, Risk Factors, MD&A, Executive Compensation,
              Legal Proceedings) and financials compliant with Regulation S-X (audited, age-appropriate periods).
            - PCAOB-audited financial statements with reconciliations, non-GAAP disclosure controls, and comfort letter
              readiness for underwriters.
            - Corporate governance package: independent directors, audit/comp committees, charters, board minutes,
              and Rule 10A-3 compliance mapped to NYSE/Nasdaq standards.
            - Internal controls documentation: disclosure controls & procedures (SOX 302) and ICFR roadmap; 404(b)
              readiness if applicable; management certification process rehearsed.
            - Risk management and disclosure register: comprehensive inventory of operational, financial, legal,
              and cyber risks with consistent mapping to S-1 risk factors.
            - Legal and compliance artifacts: Staff Legal Bulletin No. 19-compliant legal/tax opinions, comfort letter
              request lists, and EDGAR submission workflows tested.
            - Marketing and communications plan: counsel-approved quiet-period strategy, test-the-waters (if EGC),
              IR playbook with Reg FD safeguards, and post-pricing disclosure controls.
            - Listing requirements checklist with market value/shareholder distribution tests, exchange approval
              correspondence, and evidence of auditor PCAOB registration.

            Acceptance criteria (high-level):
            - S-1 accepted for review by SEC with ≤2 major comment letter cycles; all Reg S-K and Reg S-X disclosures
              evidenced and traceable to supporting workpapers.
            - Independent board committees in place and certified as meeting NYSE/Nasdaq standards; committee minutes
              and charters filed.
            - Audit sign-offs completed; comfort letters available; management SOX 302 certifications rehearsed.
            - Legal and tax opinions filed; EDGAR test submissions validated without error codes.
            - Comms plan operational with documented legal pre-clearance; no material "gun-jumping" incidents.

            Constraints (soft):
            - Target horizon: complete readiness within ≤ 8 weeks of simulated effort; no >5-day stalls on critical path
              (financial statements, governance formation, S-1 drafting).
            - Budget guardrail: stay within ±20% of planned legal/audit/consulting costs absent justified scope changes.
            - Transparency: prefer candid disclosure of known material weaknesses or risks, paired with remediation
              plans, over concealment to maximize SEC and investor confidence.

            """
        ),
        owner_id=uuid4(),
    )

    # Phase 1: Financial Audit & Controls Foundation
    financial_foundation = Task(
        id=UUID(int=0),
        name="Financial Audit & Controls Foundation",
        description=(
            "Establish PCAOB audit relationship, implement baseline financial controls, "
            "and prepare audited financial statements for S-1 registration."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=80.0,
        estimated_cost=12000.0,
    )
    financial_foundation.subtasks = [
        Task(
            id=UUID(int=100),
            name="PCAOB Auditor Engagement",
            description="Engage PCAOB-registered auditor and establish audit timeline and scope.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=15.0,
            estimated_cost=2250.0,
        ),
        Task(
            id=UUID(int=101),
            name="Financial Statement Preparation",
            description="Prepare audited financial statements with required periods per Regulation S-X.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=35.0,
            estimated_cost=5250.0,
        ),
        Task(
            id=UUID(int=102),
            name="Non-GAAP Reconciliations",
            description="Prepare and validate non-GAAP financial measure reconciliations and disclosures.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=20.0,
            estimated_cost=3000.0,
        ),
        Task(
            id=UUID(int=103),
            name="Comfort Letter Framework",
            description="Establish comfort letter procedures and coordinate with underwriter requirements.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=10.0,
            estimated_cost=1500.0,
        ),
    ]

    # Phase 2: Corporate Governance Structure
    governance_setup = Task(
        id=UUID(int=1),
        name="Corporate Governance Structure",
        description=(
            "Establish independent board structure, audit and compensation committees, "
            "and governance policies meeting NYSE/Nasdaq listing standards."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=60.0,
        estimated_cost=9000.0,
        dependency_task_ids=[financial_foundation.id],
    )
    governance_setup.subtasks = [
        Task(
            id=UUID(int=200),
            name="Independent Director Recruitment",
            description="Recruit and onboard independent directors meeting exchange qualification standards.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=25.0,
            estimated_cost=3750.0,
        ),
        Task(
            id=UUID(int=201),
            name="Board Committee Formation",
            description="Form audit, compensation, and nominating committees with compliant charters.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=20.0,
            estimated_cost=3000.0,
        ),
        Task(
            id=UUID(int=202),
            name="Governance Documentation",
            description="Document governance policies, committee charters, and board procedures.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=15.0,
            estimated_cost=2250.0,
        ),
    ]

    # Phase 3: S-1 Registration Statement
    s1_preparation = Task(
        id=UUID(int=2),
        name="S-1 Registration Statement",
        description=(
            "Draft comprehensive S-1 registration statement with business narrative, "
            "risk factors, MD&A, and regulatory disclosures."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=70.0,
        estimated_cost=10500.0,
        dependency_task_ids=[financial_foundation.id],
    )
    s1_preparation.subtasks = [
        Task(
            id=UUID(int=300),
            name="Business Description",
            description="Draft comprehensive business and operations description for S-1.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=25.0,
            estimated_cost=3750.0,
        ),
        Task(
            id=UUID(int=301),
            name="Risk Factors Documentation",
            description="Compile and document material risk factors with legal review.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=25.0,
            estimated_cost=3750.0,
        ),
        Task(
            id=UUID(int=302),
            name="MD&A Preparation",
            description="Prepare Management Discussion & Analysis with trend analysis and outlook.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=20.0,
            estimated_cost=3000.0,
        ),
    ]

    # Phase 4: SOX Compliance Implementation
    sox_implementation = Task(
        id=UUID(int=3),
        name="SOX Compliance Implementation",
        description=(
            "Implement SOX 302 disclosure controls, establish ICFR framework, "
            "and prepare management certification processes."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=50.0,
        estimated_cost=7500.0,
        dependency_task_ids=[governance_setup.id],
    )
    sox_implementation.subtasks = [
        Task(
            id=UUID(int=400),
            name="SOX 302 Controls",
            description="Implement disclosure controls and procedures per SOX Section 302.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=25.0,
            estimated_cost=3750.0,
        ),
        Task(
            id=UUID(int=401),
            name="ICFR Documentation",
            description="Document internal controls over financial reporting framework.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=25.0,
            estimated_cost=3750.0,
        ),
    ]

    # Phase 5: Legal & Regulatory Compliance
    legal_compliance = Task(
        id=UUID(int=4),
        name="Legal & Regulatory Compliance",
        description=(
            "Obtain required legal opinions, prepare EDGAR submissions, "
            "and ensure securities law compliance."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=45.0,
        estimated_cost=6750.0,
        dependency_task_ids=[s1_preparation.id],
    )
    legal_compliance.subtasks = [
        Task(
            id=UUID(int=500),
            name="Legal Opinion Preparation",
            description="Obtain legal and tax opinions per Staff Legal Bulletin No. 19.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=20.0,
            estimated_cost=3000.0,
        ),
        Task(
            id=UUID(int=501),
            name="EDGAR Filing Preparation",
            description="Prepare and test EDGAR submission workflows and procedures.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=15.0,
            estimated_cost=2250.0,
        ),
        Task(
            id=UUID(int=502),
            name="Securities Law Compliance Review",
            description="Conduct comprehensive securities law compliance review and documentation.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=10.0,
            estimated_cost=1500.0,
        ),
    ]

    # Phase 6: Exchange Listing Preparation
    exchange_preparation = Task(
        id=UUID(int=5),
        name="Exchange Listing Preparation",
        description=(
            "Verify listing standard compliance, conduct market value analysis, "
            "and prepare exchange application."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=35.0,
        estimated_cost=5250.0,
        dependency_task_ids=[governance_setup.id, sox_implementation.id],
    )

    # Phase 7: Marketing & Communications
    marketing_strategy = Task(
        id=UUID(int=6),
        name="Marketing & Communications Strategy",
        description=(
            "Develop quiet period compliance strategy and investor relations framework."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=30.0,
        estimated_cost=4500.0,
        dependency_task_ids=[legal_compliance.id],
    )

    # Phase 8: Due Diligence & Final Preparation
    due_diligence = Task(
        id=UUID(int=7),
        name="Due Diligence & Final Preparation",
        description=(
            "Complete underwriter due diligence preparation and final SEC submission readiness."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=40.0,
        estimated_cost=6000.0,
        dependency_task_ids=[sox_implementation.id, exchange_preparation.id],
    )
    due_diligence.subtasks = [
        Task(
            id=UUID(int=700),
            name="Management Presentations",
            description="Prepare management presentation materials for underwriter meetings.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=15.0,
            estimated_cost=2250.0,
        ),
        Task(
            id=UUID(int=701),
            name="Data Room Preparation",
            description="Organize due diligence data room with supporting documentation.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=25.0,
            estimated_cost=3750.0,
        ),
    ]

    # Phase 9: Submission & Review Coordination
    submission_coordination = Task(
        id=UUID(int=8),
        name="SEC Submission & Review Coordination",
        description=(
            "Coordinate SEC submission, manage comment letter process, "
            "and prepare for effective date."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=25.0,
        estimated_cost=3750.0,
        dependency_task_ids=[due_diligence.id, marketing_strategy.id],
    )

    for task in [
        financial_foundation,
        governance_setup,
        s1_preparation,
        sox_implementation,
        legal_compliance,
        exchange_preparation,
        marketing_strategy,
        due_diligence,
        submission_coordination,
    ]:
        workflow.add_task(task)

    # SEC and exchange compliance constraints for IPO readiness
    workflow.constraints.extend(
        [
            Constraint(
                name="PCAOB Auditor Registration Required",
                description=(
                    "All financial statement audits must be performed by PCAOB-registered auditors."
                ),
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=["PCAOB Auditor Engagement"],
                metadata={},
            ),
            Constraint(
                name="Independent Director Requirements",
                description=(
                    "Board must have majority independent directors meeting NYSE/Nasdaq standards."
                ),
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=["Independent Director Recruitment"],
                metadata={},
            ),
            Constraint(
                name="SOX 302 Certification Required",
                description=(
                    "SOX 302 disclosure controls and management certifications must be implemented."
                ),
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=["SOX 302 Controls"],
                metadata={},
            ),
            Constraint(
                name="Material Information Disclosure",
                description=(
                    "All material information must be disclosed in S-1 with supporting documentation."
                ),
                constraint_type="regulatory",
                enforcement_level=0.95,
                applicable_task_types=[
                    "Risk Factors Documentation",
                    "S-1 Registration Statement",
                ],
                metadata={},
            ),
            Constraint(
                name="Quiet Period Compliance",
                description=(
                    "All communications must comply with quiet period restrictions and gun-jumping rules."
                ),
                constraint_type="regulatory",
                enforcement_level=0.9,
                applicable_task_types=["Marketing & Communications Strategy"],
                metadata={},
            ),
            Constraint(
                name="EDGAR Filing Validation",
                description=(
                    "All EDGAR submissions must pass validation tests without error codes."
                ),
                constraint_type="regulatory",
                enforcement_level=0.9,
                applicable_task_types=["EDGAR Filing Preparation"],
                metadata={},
            ),
            Constraint(
                name="Comfort Letter Requirements",
                description=(
                    "Comfort letters must be available for underwriter due diligence requirements."
                ),
                constraint_type="organizational",
                enforcement_level=0.85,
                applicable_task_types=["Comfort Letter Framework"],
                metadata={},
            ),
            Constraint(
                name="Exchange Listing Standards",
                description=(
                    "Company must meet all quantitative and qualitative listing requirements."
                ),
                constraint_type="regulatory",
                enforcement_level=0.9,
                applicable_task_types=["Exchange Listing Preparation"],
                metadata={},
            ),
            Constraint(
                name="Internal Controls Documentation",
                description=(
                    "ICFR documentation must be comprehensive and support management assessments."
                ),
                constraint_type="organizational",
                enforcement_level=0.8,
                applicable_task_types=["ICFR Documentation"],
                metadata={},
            ),
        ]
    )

    return workflow
