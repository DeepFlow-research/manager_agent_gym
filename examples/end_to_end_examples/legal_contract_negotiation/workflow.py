from manager_agent_gym.schemas.domain.workflow import Workflow
from manager_agent_gym.schemas.domain.task import Task
from manager_agent_gym.schemas.domain.base import TaskStatus
from uuid import uuid4
from examples.common_stakeholders import create_stakeholder_agent
from .preferences import create_preferences
from manager_agent_gym.core.workflow.services import WorkflowMutations


def create_workflow() -> Workflow:
    wf = Workflow(
        name="Legal Contract Negotiation – Enterprise MSA & DPA",
        workflow_goal=(
            """
            Case study: Negotiate and execute a complex enterprise Master Services Agreement (MSA) with supporting
            Data Processing Agreement (DPA) and Security Schedule for a global SaaS platform provider. The negotiation
            spans data protection (GDPR/CCPA), information security (SOC2/ISO 27001 controls), SLAs and service credits,
            limitations of liability, IP and licensing, data residency/transfer mechanisms, audit rights, subcontractors,
            business continuity (RTO/RPO), and termination/exit assistance. Multiple stakeholders are involved: Legal,
            Privacy, Security/IT Risk, Procurement, Finance, and the Business owner, with an external vendor counsel.

            Objectives:
            - Deliver a signed MSA, DPA, and Security Schedule aligned with internal risk appetite and regulatory
              requirements while enabling time‑bound onboarding.
            - Ensure clear allocation of risks (LoL caps/carve‑outs; SLA remedies; indemnities; IP ownership/licensing).
            - Validate privacy and security controls (data mapping, sub‑processors, breach response, encryption, access
              controls, audit rights) with appropriate evidence (SOC2, pen test summaries, policy excerpts).
            - Achieve commercial targets (pricing tiers, indexation, payment terms, credits) agreed with Finance.
            - Maintain a documented negotiation record: redlines, decisions, approvals, and rationales.

            Acceptance criteria:
            - All critical issues closed or explicitly risk‑accepted with senior approvals; no open high‑severity gaps.
            - Final documents internally consistent and traceable to requirements and decisions.
            - Execution artifacts complete (sign‑offs, signature pages, countersigned PDFs) and obligations tracker seeded.

            Constraints:
            - Target timeline ≤ 3 weeks; avoid critical‑path stalls > 3 business days without escalation.
            - Budget guardrail within ±20% of planned review effort barring scope change.
            - Transparency: self‑identify unresolved risks with remediation plans and time‑boxed follow‑ups.
            """
        ),
        owner_id=uuid4(),
    )

    # Phase 1: Intake & Requirements
    intake = Task(
        name="Intake & Requirements",
        description=(
            "Collect use case, data flows, jurisdictions, contract templates, and stakeholder roster; define critical issues."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=6.0,
        estimated_cost=900.0,
    )
    intake.subtasks = [
        Task(
            name="Use Case & Data Mapping",
            description="Document categories of data, flows, residency, sub‑processors; capture diagrams.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=450.0,
        ),
        Task(
            name="Stakeholder Register",
            description="Identify Legal/Privacy/Security/Procurement/Finance/Business contacts and SLAs.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=2.0,
            estimated_cost=300.0,
        ),
        Task(
            name="Critical Issues List",
            description="Draft material issues (LoL, SLAs, DPA clauses, audit, exit) and target positions.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=1.0,
            estimated_cost=150.0,
        ),
    ]

    # Phase 2: Drafting & Redlines
    drafting = Task(
        name="Drafting – MSA/DPA/Security Schedule",
        description="Prepare initial redlines to vendor paper; align with playbook and risk appetite.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=10.0,
        estimated_cost=1500.0,
        dependency_task_ids=[intake.task_id],
    )
    drafting.subtasks = [
        Task(
            name="MSA Redlines",
            description="LoL, indemnities, IP, audit rights, choice of law/venue, termination/exit assistance.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
        Task(
            name="DPA Redlines",
            description="GDPR/CCPA, sub‑processors, SCCs/IDTA, breaches, data subject rights, deletion/return.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=450.0,
        ),
        Task(
            name="Security Schedule",
            description="Controls mapping (SOC2/ISO), encryption, access, vulnerability mgmt, BCP/DR, pen test.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=450.0,
        ),
    ]

    # Phase 3: Reviews (Legal/Privacy/Security/Finance)
    reviews = Task(
        name="Internal Reviews & Approvals",
        description="Obtain SME reviews and risk approvals; reconcile conflicts; document decisions.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=12.0,
        estimated_cost=1800.0,
        dependency_task_ids=[drafting.task_id],
    )
    reviews.subtasks = [
        Task(
            name="Privacy Review",
            description="Assess DPA, SCCs, sub‑processors, retention, DSAR support; track findings/resolutions.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.5,
            estimated_cost=525.0,
        ),
        Task(
            name="Security Review",
            description="Evaluate controls evidence (SOC2/ISO), questionnaires, pen test summary, BCP/DR; gaps/mitigations.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.5,
            estimated_cost=525.0,
        ),
        Task(
            name="Finance & Commercial",
            description="Pricing models, indexation, service credits, payment terms; ROI sanity check.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=2.5,
            estimated_cost=375.0,
        ),
        Task(
            name="Legal Final Review",
            description="Resolve conflicts across functions; confirm risk acceptances and carve‑outs.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=2.5,
            estimated_cost=375.0,
        ),
    ]

    # Phase 4: Negotiation Rounds
    negotiation = Task(
        name="Negotiation Rounds",
        description="Exchange redlines; discuss issues; converge on acceptable positions with documented trade‑offs.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=14.0,
        estimated_cost=2100.0,
        dependency_task_ids=[reviews.task_id],
    )
    negotiation.subtasks = [
        Task(
            name="Round 1 – Issue Table",
            description="Publish issue list with positions, rationales, and proposed compromises.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
        Task(
            name="Round 2 – Concessions",
            description="Targeted concessions tied to risk mitigations (e.g., enhanced credits for higher LoL).",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
        Task(
            name="Round 3 – Final Clean‑up",
            description="Resolve residual drafting issues; ensure internal consistency across documents.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=900.0,
        ),
    ]

    # Phase 5: Execution & Handover
    execution = Task(
        name="Execution & Handover",
        description="Assemble signature packets; obtain countersignatures; seed obligations tracker; archive records.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=8.0,
        estimated_cost=1200.0,
        dependency_task_ids=[negotiation.task_id],
    )
    execution.subtasks = [
        Task(
            name="Signature Package",
            description="Signature pages, sign‑off matrix, countersigned PDFs; confirm metadata integrity.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=450.0,
        ),
        Task(
            name="Obligations Tracker",
            description="Create tracker for audits, SLAs, credits, security attestations, renewal/termination windows.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=450.0,
        ),
        Task(
            name="Records & Archive",
            description="Versioned repository of drafts, redlines, decisions, evidence; access controls set.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=2.0,
            estimated_cost=300.0,
        ),
    ]

    # Cross‑cutting tasks
    playbook = Task(
        name="Negotiation Playbook & Policy Alignment",
        description="Map internal policies to contract positions; maintain fallback options for high‑friction clauses.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=5.0,
        estimated_cost=750.0,
        dependency_task_ids=[intake.task_id],
    )
    dataroom = Task(
        name="Data Room Setup",
        description="Organize vendor evidence (SOC2, ISMS, pen test, insurance, financials) and internal approvals.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=3.0,
        estimated_cost=450.0,
        dependency_task_ids=[intake.task_id],
    )

    for t in [
        intake,
        drafting,
        reviews,
        negotiation,
        execution,
        playbook,
        dataroom,
    ]:
        WorkflowMutations.add_task(wf, t)
    # Attach default stakeholder
    try:
        prefs = create_preferences()
        stakeholder = create_stakeholder_agent(persona="balanced", preferences=prefs)
        WorkflowMutations.add_agent(wf, stakeholder)
    except Exception:
        pass
    return wf
