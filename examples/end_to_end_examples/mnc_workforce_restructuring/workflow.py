from manager_agent_gym.schemas.domain.workflow import Workflow
from manager_agent_gym.schemas.domain.task import Task
from manager_agent_gym.schemas.domain.base import TaskStatus
from manager_agent_gym.schemas.preferences import Constraint
from uuid import uuid4

# Optional stakeholder + preferences (tolerant import pattern)
from examples.common_stakeholders import create_stakeholder_agent
from .preferences import create_preferences  # to be provided later
from manager_agent_gym.core.workflow.services import WorkflowMutations


def create_workflow() -> Workflow:
    wf = Workflow(
        name="Global Workforce Restructuring / RIF (Employment)",
        workflow_goal=(
            "Plan and execute a defensible, humane global workforce restructuring. Objectives: establish governance, "
            "define selection criteria, run legal/jurisdictional scoping (US WARN/mini‑WARN, EU collective consultation, "
            "UK TULRCA s.188, FR CSE), perform adverse‑impact analysis, redeployment/mitigation, prepare documentation and "
            "notices, execute communications and payroll/benefits changes, and complete post‑action audit and regulator filings."
        ),
        owner_id=uuid4(),
    )

    # ---------------------------
    # PHASE 1 — Program Foundation & Governance
    # ---------------------------
    program_charter = Task(
        name="Program Charter & Governance",
        description=(
            "Define objectives, scope, roles, and cadence; confirm privilege strategy with Legal; "
            "stand up risk/issue controls and a single source of truth (SSOT) for artifacts."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=8.0,
        estimated_cost=3500.0,
    )
    program_charter.subtasks = [
        Task(
            name="Executive Alignment",
            description="Confirm business case, headcount targets, timeline, and risk appetite.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=2.0,
            estimated_cost=800.0,
        ),
        Task(
            name="Privilege & Records Protocol",
            description="Mark privileged communications; define document retention and access controls.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=2.0,
            estimated_cost=700.0,
        ),
        Task(
            name="SSOT & Version Control",
            description="Create artifact index, versioning standards, and approval workflow.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=2.0,
            estimated_cost=600.0,
        ),
        Task(
            name="Risk/Issue Log",
            description="Initialize RAID log; define escalation thresholds and owners.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=2.0,
            estimated_cost=600.0,
        ),
    ]

    # ---------------------------
    # PHASE 2 — Legal Scoping, Data & Selection
    # ---------------------------
    data_pull = Task(
        name="Data Pull & Workforce Baseline",
        description=(
            "Compile HRIS roster, roles/locations, tenure, performance data, compensations/benefits, visas, "
            "and union/Works Council coverage; ensure data quality and minimization."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=10.0,
        estimated_cost=3000.0,
        dependency_task_ids=[program_charter.task_id],
    )
    data_pull.subtasks = [
        Task(
            name="Data Quality & Minimization",
            description="De‑duplicate, correct errors, and remove fields not needed for decisions.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=800.0,
        ),
        Task(
            name="Union/Works Council Coverage Map",
            description="Mark countries/sites with collective representation (works councils/unions).",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=900.0,
        ),
        Task(
            name="Visa/Immigration Flags",
            description="Identify visa‑dependent roles and consult immigration counsel if needed.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=1300.0,
        ),
    ]

    selection_criteria = Task(
        name="Selection Criteria & Adverse‑Impact Plan",
        description=(
            "Define role‑based selection criteria (skills, redundancy of role, performance bands) and guard against "
            "discriminatory impact; set documentation templates and sign‑off path."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=12.0,
        estimated_cost=4200.0,
        dependency_task_ids=[data_pull.task_id],
    )
    selection_criteria.subtasks = [
        Task(
            name="Criteria Definition & Sources",
            description="List objective criteria, weightings, and data sources; map to roles/groups.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=1200.0,
        ),
        Task(
            name="Calibration & Manager Training",
            description="Run calibration sessions to reduce bias; train managers on documentation.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=1500.0,
        ),
        Task(
            name="Adverse‑Impact Test Plan",
            description="Define adverse‑impact testing approach (e.g., 4/5ths rule proxy) and remediation steps.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=1500.0,
        ),
    ]

    jurisdiction_scoping = Task(
        name="Jurisdictional Scoping & Timelines",
        description=(
            "Identify per‑country obligations: US WARN/mini‑WARN thresholds and 60‑day timelines; EU collective redundancies "
            "Directive 98/59/EC consultation/notification; UK TULRCA s.188; FR CSE consultation/notification; tailor plan."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=10.0,
        estimated_cost=4500.0,
        dependency_task_ids=[selection_criteria.task_id],
    )
    jurisdiction_scoping.subtasks = [
        Task(
            name="US WARN & mini‑WARN Matrix",
            description="Map establishments, thresholds, and timing; draft notice recipients & content.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=1600.0,
        ),
        Task(
            name="EU Collective Redundancies",
            description="Consultation and competent authority notification requirements by Member State.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=1400.0,
        ),
        Task(
            name="UK Collective Consultation",
            description="20+ redundancies in 90 days triggers collective consultation; plan timelines.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=1500.0,
        ),
    ]

    redeployment = Task(
        name="Redeployment & Vacancy Freeze Plan",
        description="Identify redeployment options, freeze backfills where appropriate, and define priority placement rules.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=8.0,
        estimated_cost=2200.0,
        dependency_task_ids=[selection_criteria.task_id],
    )

    severance_benefits = Task(
        name="Severance, Benefits & Support Program",
        description=(
            "Design severance matrix (tenure/grade), benefits continuation, outplacement/career services, "
            "and local statutory overlays."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=10.0,
        estimated_cost=3500.0,
        dependency_task_ids=[jurisdiction_scoping.task_id],
    )
    severance_benefits.subtasks = [
        Task(
            name="Statutory Overlays",
            description="Country‑specific statutory minimums and formulas.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=1200.0,
        ),
        Task(
            name="Enhanced Package & Eligibility",
            description="Define enhanced terms and eligibility criteria; align to budget.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=1100.0,
        ),
        Task(
            name="Outplacement & EAP",
            description="Set up outplacement services and employee assistance resources.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=1200.0,
        ),
    ]

    # ---------------------------
    # PHASE 3 — Consultation, Documentation & Approvals
    # ---------------------------
    works_council = Task(
        name="Works Council/Union Consultation",
        description="Prepare information packs and conduct consultations with works councils/unions as required.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=12.0,
        estimated_cost=4200.0,
        dependency_task_ids=[jurisdiction_scoping.task_id, severance_benefits.task_id],
    )
    works_council.subtasks = [
        Task(
            name="Information Pack",
            description="Provide reasons, numbers, selection criteria, timeframe, and mitigation steps.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=1300.0,
        ),
        Task(
            name="Minutes & Responses",
            description="Record meetings, address proposals to avoid/reduce redundancies.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=1400.0,
        ),
        Task(
            name="Authority Notifications",
            description="Notify competent authorities where required and track acknowledgements.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=1500.0,
        ),
    ]

    selection_decisions = Task(
        name="Selection Decisions & Documentation",
        description="Apply criteria, record decision rationales, and compile manager letters for review by Legal/HR.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=14.0,
        estimated_cost=4800.0,
        dependency_task_ids=[selection_criteria.task_id, works_council.task_id],
    )
    selection_decisions.subtasks = [
        Task(
            name="Decision Logs",
            description="Role‑by‑role decision logs with evidence and approver signatures.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=5.0,
            estimated_cost=1500.0,
        ),
        Task(
            name="Adverse‑Impact Test & Remediation",
            description="Run adverse‑impact analysis; adjust selections or mitigations as needed.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=5.0,
            estimated_cost=1700.0,
        ),
        Task(
            name="Legal/HR QA",
            description="Final QA for defensibility and consistency; freeze list for comms.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=1600.0,
        ),
    ]

    notice_packs = Task(
        name="Notice & Document Packages",
        description="Assemble compliant notice letters, FAQs, separation agreements, and authority filings templates.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=10.0,
        estimated_cost=3200.0,
        dependency_task_ids=[selection_decisions.task_id],
    )
    notice_packs.subtasks = [
        Task(
            name="Jurisdictional Templates",
            description="Country‑specific letters (redundancy/termination), translations, and FAQs.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=1200.0,
        ),
        Task(
            name="Separation Agreements",
            description="Prepare agreements with releases and consideration where applicable.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=1100.0,
        ),
        Task(
            name="Authority Notice Forms",
            description="Populate and QA forms for authorities/ministries as required.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=900.0,
        ),
    ]

    # ---------------------------
    # PHASE 4 — Execution, Payroll/Systems & Post‑Action
    # ---------------------------
    communications = Task(
        name="Communications & Day‑Of Playbooks",
        description="Prepare manager scripts, employee meeting schedules, and external/internal announcements.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=8.0,
        estimated_cost=2800.0,
        dependency_task_ids=[notice_packs.task_id],
    )
    payroll_benefits = Task(
        name="Payroll, Benefits & HRIS Updates",
        description="Load severance terms, benefits continuation, and termination codes; schedule payments.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=8.0,
        estimated_cost=2600.0,
        dependency_task_ids=[notice_packs.task_id, severance_benefits.task_id],
    )
    access_management = Task(
        name="Access & Asset Management",
        description="Coordinate timely, respectful systems/access changes and asset return logistics.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=6.0,
        estimated_cost=2000.0,
        dependency_task_ids=[communications.task_id],
    )
    execution_room = Task(
        name="Execution Control Room",
        description="Run day‑of operations; track delivery of notices, exceptions, and employee support routing.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=12.0,
        estimated_cost=3600.0,
        dependency_task_ids=[
            communications.task_id,
            payroll_benefits.task_id,
            access_management.task_id,
        ],
    )
    grievances = Task(
        name="Grievances & Appeals Handling",
        description="Manage appeals and grievances; log outcomes and escalate legal risks.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=6.0,
        estimated_cost=1800.0,
        dependency_task_ids=[execution_room.task_id],
    )
    regulator_filings = Task(
        name="Regulator Filings & Confirmations",
        description="Submit required authority notifications and track confirmations and deadlines.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=6.0,
        estimated_cost=2200.0,
        dependency_task_ids=[works_council.task_id, notice_packs.task_id],
    )
    post_action_audit = Task(
        name="Post‑Action Audit & Lessons Learned",
        description="Audit compliance, calculate realized adverse impact, and capture improvements for playbooks.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=8.0,
        estimated_cost=2600.0,
        dependency_task_ids=[grievances.task_id, regulator_filings.task_id],
    )

    # Register tasks
    for t in [
        program_charter,
        data_pull,
        selection_criteria,
        jurisdiction_scoping,
        redeployment,
        severance_benefits,
        works_council,
        selection_decisions,
        notice_packs,
        communications,
        payroll_benefits,
        access_management,
        execution_room,
        grievances,
        regulator_filings,
        post_action_audit,
    ]:
        WorkflowMutations.add_task(wf, t)

    # ---------------------------
    # CONSTRAINTS (Legal, Fairness, Documentation, Confidentiality)
    # ---------------------------
    wf.constraints.extend(
        [
            Constraint(
                name="Collective Consultation & Authority Notice (EU/UK)",
                description="Where thresholds are met (e.g., EU Directive 98/59/EC; UK 20+ in 90 days), consult representatives and notify authorities before dismissals.",
                constraint_type="regulatory",
                enforcement_level=0.95,
                applicable_task_types=[
                    "Works Council/Union Consultation",
                    "Regulator Filings & Confirmations",
                ],
                metadata={"references": ["EU 98/59/EC", "UK TULRCA s.188"]},
            ),
            Constraint(
                name="US WARN/mini‑WARN Compliance",
                description="If WARN thresholds are met, provide specific written notice to affected employees and designated government units within required timelines (typically 60 days).",
                constraint_type="regulatory",
                enforcement_level=0.95,
                applicable_task_types=[
                    "Notice & Document Packages",
                    "Regulator Filings & Confirmations",
                    "Communications & Day‑Of Playbooks",
                ],
                metadata={
                    "notice_elements": ["nature", "timing", "contacts"],
                    "timeline_days": 60,
                },
            ),
            Constraint(
                name="Selection Fairness & Adverse‑Impact Testing",
                description="Selection procedures must avoid unlawful discrimination; run adverse‑impact analyses and remediate if required.",
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=[
                    "Selection Criteria & Adverse‑Impact Plan",
                    "Selection Decisions & Documentation",
                    "Post‑Action Audit & Lessons Learned",
                ],
                metadata={"guidance": ["EEOC Uniform Guidelines (29 CFR Part 1607)"]},
            ),
            Constraint(
                name="Consultation Before Decision",
                description="Where required, consultation must be genuine and completed before final decisions and notices.",
                constraint_type="regulatory",
                enforcement_level=0.9,
                applicable_task_types=[
                    "Works Council/Union Consultation",
                    "Selection Decisions & Documentation",
                ],
                metadata={},
            ),
            Constraint(
                name="Severance & Statutory Minimums",
                description="Severance and benefits must meet or exceed applicable statutory minimums in each jurisdiction.",
                constraint_type="regulatory",
                enforcement_level=0.9,
                applicable_task_types=[
                    "Severance, Benefits & Support Program",
                    "Payroll, Benefits & HRIS Updates",
                ],
                metadata={},
            ),
            Constraint(
                name="Documentation & Audit Trail",
                description="All decisions, notices, and approvals must be documented and traceable for audit and tribunal/regulator review.",
                constraint_type="organizational",
                enforcement_level=0.9,
                applicable_task_types=[
                    "Selection Decisions & Documentation",
                    "Notice & Document Packages",
                    "Execution Control Room",
                    "Post‑Action Audit & Lessons Learned",
                ],
                metadata={"evidence": ["decision_logs", "minutes", "notice_copies"]},
            ),
            Constraint(
                name="PII and Secrets Redaction",
                description="Confidential and personal data must be access‑controlled and redacted in shared artifacts and communications.",
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=[
                    "Data Pull & Workforce Baseline",
                    "Notice & Document Packages",
                    "Communications & Day‑Of Playbooks",
                ],
                metadata={
                    "prohibited_keywords": [
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

    # Stakeholder agent
    prefs = create_preferences()
    stakeholder = create_stakeholder_agent(persona="balanced", preferences=prefs)
    WorkflowMutations.add_agent(wf, stakeholder)

    return wf
