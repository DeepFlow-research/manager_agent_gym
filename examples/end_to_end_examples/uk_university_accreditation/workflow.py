"""
UK University Accreditation Renewal Demo

Real-world use case: Mid-size UK university OfS registration renewal.

Demonstrates:
- Multi-stakeholder regulatory compliance coordination across diverse functional areas
- Sequential dependency management with parallel track execution for efficiency
- Risk-based governance oversight with escalation management under regulatory deadlines
- Evidence-based compliance documentation with quality assurance validation
- Cross-functional team coordination between academic, administrative, and external stakeholders
"""

from uuid import uuid4, UUID

from manager_agent_gym.schemas.core.workflow import Workflow
from manager_agent_gym.schemas.core.tasks import Task
from manager_agent_gym.schemas.core.base import TaskStatus
from manager_agent_gym.schemas.preferences import Constraint


def create_workflow() -> Workflow:
    """Create UK University Accreditation Renewal workflow with phased compliance evidence gathering."""

    workflow = Workflow(
        name="UK University Accreditation Renewal - Mid-size Institution",
        workflow_goal=(
            """
            Objective: Execute a structured accreditation (registration) renewal for a mid-size UK university to
            demonstrate compliance with Office for Students (OfS) ongoing conditions of registration, ensure high-quality
            academic standards, protect student interests, and maintain international student sponsorship rights.

            Primary deliverables:
            - Comprehensive evidence pack against OfS conditions A–E, including mapped compliance to quality, standards,
              governance, financial sustainability, access & participation, and student protection requirements.
            - Quality and standards matrix: course clusters mapped to B-conditions (B1–B6) with external examiner
              summaries, continuation/completion/progression KPIs, and remediation actions.
            - Consumer law compliance audit: CMA-compliant prospectus and contracts with evidence of clear, fair, and
              transparent information on courses, costs, and contact hours.
            - Updated Access and Participation Plan (APP) with monitoring data, gap analysis, and proposed adjustments
              in line with OfS regulatory advice and sector benchmarks.
            - Governance package: Council, Senate, and Quality Committee minutes evidencing oversight, decisions, and
              sign-offs; risk registers and escalation logs.
            - UKVI student sponsor compliance pack: attendance monitoring records, CAS issuance logs, and reporting
              evidence to confirm fitness as a licensed sponsor.
            - Prevent duty documentation: risk assessment, training coverage, incident logs, and governing-body oversight
              consistent with OfS Prevent monitoring requirements.
            - Data quality assurance pack: validated HESA Data Futures submissions, internal audit checks, and signed
              statements of data integrity.
            - Student outcomes narrative aligned to Teaching Excellence Framework (TEF) indicators and evidence of
              continuous improvement initiatives.

            Acceptance criteria (high-level):
            - OfS evidence pack submitted on time with no material deficiencies; ≤2 rounds of clarifications from the
              regulator.
            - Demonstrated compliance with all quality & standards baselines (B-conditions), supported by KPIs and
              external examiner validation.
            - APP accepted as valid and credible by OfS; demonstrable governance oversight of equality of opportunity.
            - CMA compliance confirmed by legal review; no unresolved findings on unfair terms or information clarity.
            - UKVI sponsorship compliance maintained with no major findings or risk of licence downgrade.
            - Prevent duty compliance evidenced with governing-body sign-off; training coverage ≥95% across staff.
            - HESA Data Futures submissions validated with no critical data quality flags raised.
            - Council, Senate, and Board sign-offs documented for all key evidence packs.

            Constraints (soft):
            - Target horizon: complete renewal readiness within ≤ 8 weeks of simulated effort; avoid >5-day stalls on
              critical-path activities (e.g., quality evidence mapping, APP submission, HESA data checks).
            - Budget guardrail: stay within ±20% of planned compliance, audit, and consultancy costs absent justified
              scope changes.
            - Transparency: prefer proactive disclosure of known risks or weaknesses (e.g., low continuation in a
              subject area) with mitigation plans over concealment, to maximize regulator trust and institutional
              credibility.
            """
        ),
        owner_id=uuid4(),
    )

    # Phase 1: Governance Setup & Stakeholder Coordination
    governance_setup = Task(
        id=UUID(int=0),
        name="Governance Structure & Stakeholder Coordination",
        description=(
            "Establish accreditation steering committee; define roles, responsibilities, and reporting lines; "
            "map OfS conditions to institutional accountability framework; set timeline and milestones."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=6.0,
        estimated_cost=900.0,
    )
    governance_setup.subtasks = [
        Task(
            id=UUID(int=100),
            name="Steering Committee Formation",
            description="Form accreditation steering committee with cross-functional representation and clear terms of reference.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=2.0,
            estimated_cost=300.0,
        ),
        Task(
            id=UUID(int=101),
            name="OfS Conditions Mapping",
            description="Map OfS conditions A-E to institutional responsibilities and evidence requirements.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=2.0,
            estimated_cost=300.0,
        ),
        Task(
            id=UUID(int=102),
            name="Timeline & Milestone Planning",
            description="Establish detailed project timeline with key milestones and interdependency management.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=2.0,
            estimated_cost=300.0,
        ),
    ]

    # Phase 2: Quality & Standards Evidence Compilation
    quality_standards = Task(
        id=UUID(int=1),
        name="Quality & Standards Evidence Package",
        description=(
            "Compile evidence against OfS B-conditions (B1-B6); gather external examiner reports, "
            "student outcome KPIs, continuation/completion data, and remediation action plans."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=14.0,
        estimated_cost=2100.0,
        dependency_task_ids=[governance_setup.id],
    )
    quality_standards.subtasks = [
        Task(
            id=UUID(int=110),
            name="Course Cluster Mapping & KPI Analysis",
            description="Map course clusters to B-conditions; analyze continuation, completion, and progression rates by subject.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=5.0,
            estimated_cost=750.0,
        ),
        Task(
            id=UUID(int=111),
            name="External Examiner Report Synthesis",
            description="Compile and synthesize external examiner reports; identify trends and remediation requirements.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
        Task(
            id=UUID(int=112),
            name="Student Outcome Enhancement Plans",
            description="Document enhancement plans for underperforming areas with timelines and success measures.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=450.0,
        ),
        Task(
            id=UUID(int=113),
            name="Academic Standards Validation",
            description="Validate academic standards compliance with sector benchmarks and regulatory expectations.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=2.0,
            estimated_cost=300.0,
        ),
    ]

    consumer_law_audit = Task(
        id=UUID(int=2),
        name="Consumer Law Compliance Audit",
        description=(
            "Conduct comprehensive CMA compliance review of prospectus, contracts, and course information; "
            "ensure transparency of costs, contact hours, and student rights."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=10.0,
        estimated_cost=1500.0,
        dependency_task_ids=[governance_setup.id],
    )
    consumer_law_audit.subtasks = [
        Task(
            id=UUID(int=120),
            name="Prospectus & Marketing Review",
            description="Review all prospectus and marketing materials for CMA compliance and accuracy of course information.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
        Task(
            id=UUID(int=121),
            name="Student Contract Analysis",
            description="Analyze student contracts and terms for unfair clauses and compliance with consumer protection law.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=450.0,
        ),
        Task(
            id=UUID(int=122),
            name="Cost Transparency Assessment",
            description="Assess transparency of all costs including tuition, accommodation, and additional fees.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=450.0,
        ),
    ]

    # Phase 3: Access & Participation Plan Update
    access_participation = Task(
        id=UUID(int=3),
        name="Access & Participation Plan Update",
        description=(
            "Update APP with latest monitoring data, gap analysis, and proposed interventions; "
            "align with OfS guidance and sector benchmarks for widening access."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=12.0,
        estimated_cost=1800.0,
        dependency_task_ids=[quality_standards.id],
    )
    access_participation.subtasks = [
        Task(
            id=UUID(int=130),
            name="APP Monitoring Data Analysis",
            description="Analyze current APP performance against targets; identify gaps and successes.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
        Task(
            id=UUID(int=131),
            name="Sector Benchmarking & Gap Analysis",
            description="Benchmark performance against sector averages; conduct detailed gap analysis.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
        Task(
            id=UUID(int=132),
            name="Intervention Strategy Development",
            description="Develop evidence-based intervention strategies with measurable outcomes and timelines.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
    ]

    # Phase 4: UKVI Sponsorship Compliance
    ukvi_compliance = Task(
        id=UUID(int=4),
        name="UKVI Student Sponsor Compliance Pack",
        description=(
            "Compile UKVI compliance evidence including attendance monitoring, CAS management, "
            "and reporting protocols to maintain sponsor licence status."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=8.0,
        estimated_cost=1200.0,
        dependency_task_ids=[governance_setup.id],
    )
    ukvi_compliance.subtasks = [
        Task(
            id=UUID(int=140),
            name="Attendance Monitoring Audit",
            description="Audit attendance monitoring systems and records for compliance with UKVI requirements.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=450.0,
        ),
        Task(
            id=UUID(int=141),
            name="CAS Management Review",
            description="Review CAS issuance processes, records, and compliance with Home Office guidance.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=450.0,
        ),
        Task(
            id=UUID(int=142),
            name="UKVI Reporting Protocol Validation",
            description="Validate all UKVI reporting protocols and evidence of timely compliance submissions.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=2.0,
            estimated_cost=300.0,
        ),
    ]

    # Phase 5: Prevent Duty & Safeguarding
    prevent_duty = Task(
        id=UUID(int=5),
        name="Prevent Duty Compliance Documentation",
        description=(
            "Compile Prevent duty evidence including risk assessment, training records, "
            "incident logs, and governing body oversight documentation."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=6.0,
        estimated_cost=900.0,
        dependency_task_ids=[governance_setup.id],
    )
    prevent_duty.subtasks = [
        Task(
            id=UUID(int=150),
            name="Prevent Risk Assessment Update",
            description="Update institutional Prevent risk assessment with current threat analysis and mitigation measures.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=2.0,
            estimated_cost=300.0,
        ),
        Task(
            id=UUID(int=151),
            name="Training Coverage Analysis",
            description="Analyze staff training coverage and compliance with Prevent duty training requirements.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=2.0,
            estimated_cost=300.0,
        ),
        Task(
            id=UUID(int=152),
            name="Governance Oversight Documentation",
            description="Document governing body oversight of Prevent duty compliance and decision-making.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=2.0,
            estimated_cost=300.0,
        ),
    ]

    # Phase 6: Data Quality & HESA Compliance
    data_quality = Task(
        id=UUID(int=6),
        name="Data Quality Assurance & HESA Compliance",
        description=(
            "Validate HESA Data Futures submissions; conduct internal audit of data integrity; "
            "compile signed statements and data validation evidence."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=10.0,
        estimated_cost=1500.0,
        dependency_task_ids=[quality_standards.id, access_participation.id],
    )
    data_quality.subtasks = [
        Task(
            id=UUID(int=160),
            name="HESA Data Futures Validation",
            description="Validate all HESA Data Futures submissions for accuracy and completeness.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
        Task(
            id=UUID(int=161),
            name="Internal Data Audit",
            description="Conduct comprehensive internal audit of data collection, processing, and integrity controls.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
        Task(
            id=UUID(int=162),
            name="Data Integrity Statements",
            description="Compile signed statements of data integrity from relevant senior officers.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=2.0,
            estimated_cost=300.0,
        ),
    ]

    # Phase 7: Financial Sustainability & Student Protection
    financial_sustainability = Task(
        id=UUID(int=7),
        name="Financial Sustainability & Student Protection",
        description=(
            "Compile financial sustainability evidence and student protection plan documentation "
            "to demonstrate ongoing viability and student interest protection."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=8.0,
        estimated_cost=1200.0,
        dependency_task_ids=[consumer_law_audit.id],
    )
    financial_sustainability.subtasks = [
        Task(
            id=UUID(int=170),
            name="Financial Sustainability Assessment",
            description="Assess and document institutional financial sustainability including scenario planning.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
        Task(
            id=UUID(int=171),
            name="Student Protection Plan Update",
            description="Update student protection plan with current arrangements and risk mitigation strategies.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
    ]

    # Phase 8: Evidence Consolidation & Submission
    evidence_consolidation = Task(
        id=UUID(int=8),
        name="Evidence Consolidation & OfS Submission",
        description=(
            "Consolidate all evidence packages; prepare comprehensive OfS submission documentation; "
            "obtain final governance approvals and submit to OfS."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=10.0,
        estimated_cost=1500.0,
        dependency_task_ids=[
            ukvi_compliance.id,
            prevent_duty.id,
            data_quality.id,
            financial_sustainability.id,
        ],
    )
    evidence_consolidation.subtasks = [
        Task(
            id=UUID(int=180),
            name="Evidence Package Assembly",
            description="Assemble comprehensive evidence package with cross-references and supporting documentation.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
        Task(
            id=UUID(int=181),
            name="Final Governance Approvals",
            description="Obtain final approvals from Council, Senate, and relevant committees with documented sign-offs.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=450.0,
        ),
        Task(
            id=UUID(int=182),
            name="OfS Submission & Quality Check",
            description="Conduct final quality checks and submit complete evidence package to OfS.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=450.0,
        ),
    ]

    for task in [
        governance_setup,
        quality_standards,
        consumer_law_audit,
        access_participation,
        ukvi_compliance,
        prevent_duty,
        data_quality,
        financial_sustainability,
        evidence_consolidation,
    ]:
        workflow.add_task(task)

    # Regulatory and governance constraints for UK university accreditation
    workflow.constraints.extend(
        [
            Constraint(
                name="OfS Conditions Compliance",
                description=(
                    "All OfS ongoing conditions of registration (A-E) must be evidenced with comprehensive compliance documentation."
                ),
                constraint_type="regulatory",
                enforcement_level=1.0,
                applicable_task_types=[
                    "Quality & Standards Evidence Package",
                    "Evidence Consolidation",
                ],
                metadata={},
            ),
            Constraint(
                name="UKVI Sponsor Licence Maintenance",
                description=(
                    "UKVI sponsor licence compliance must be maintained with no major findings that could lead to licence suspension."
                ),
                constraint_type="regulatory",
                enforcement_level=1.0,
                applicable_task_types=["UKVI Student Sponsor Compliance Pack"],
                metadata={},
            ),
            Constraint(
                name="Data Protection and Quality",
                description=(
                    "All student data must be handled in compliance with GDPR and data quality standards validated through internal audit."
                ),
                constraint_type="regulatory",
                enforcement_level=0.95,
                applicable_task_types=["Data Quality Assurance & HESA Compliance"],
                metadata={},
            ),
            Constraint(
                name="Consumer Protection Compliance",
                description=(
                    "All student-facing materials and contracts must comply with CMA consumer protection requirements."
                ),
                constraint_type="regulatory",
                enforcement_level=0.9,
                applicable_task_types=["Consumer Law Compliance Audit"],
                metadata={},
            ),
            Constraint(
                name="Prevent Duty Statutory Compliance",
                description=(
                    "Prevent duty compliance must be evidenced with governing body oversight and training coverage ≥95%."
                ),
                constraint_type="regulatory",
                enforcement_level=0.95,
                applicable_task_types=["Prevent Duty Compliance Documentation"],
                metadata={},
            ),
            Constraint(
                name="Academic Quality Standards",
                description=(
                    "Academic quality must meet sector benchmarks with external examiner validation and enhancement plans for underperformance."
                ),
                constraint_type="regulatory",
                enforcement_level=0.85,
                applicable_task_types=["Quality & Standards Evidence Package"],
                metadata={},
            ),
            Constraint(
                name="Access and Participation Credibility",
                description=(
                    "APP must be credible and evidence-based with demonstrable governance oversight and realistic targets."
                ),
                constraint_type="regulatory",
                enforcement_level=0.8,
                applicable_task_types=["Access & Participation Plan Update"],
                metadata={},
            ),
            Constraint(
                name="Financial Sustainability Evidence",
                description=(
                    "Financial sustainability must be evidenced with scenario planning and student protection arrangements."
                ),
                constraint_type="organizational",
                enforcement_level=0.85,
                applicable_task_types=["Financial Sustainability & Student Protection"],
                metadata={},
            ),
            Constraint(
                name="Governance Documentation",
                description=(
                    "All key decisions must be documented with appropriate governance approval and sign-offs."
                ),
                constraint_type="organizational",
                enforcement_level=0.9,
                applicable_task_types=["Evidence Consolidation & OfS Submission"],
                metadata={},
            ),
        ]
    )

    return workflow
