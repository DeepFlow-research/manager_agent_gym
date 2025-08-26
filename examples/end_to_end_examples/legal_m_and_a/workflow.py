"""
Legal M&A acquisition scenario (Pydantic-based) aligned with ICAAP example flow.

Mid-Market Tech Acquisition – end-to-end workflow from intake to signing/closing.
"""

from uuid import uuid4, UUID

from manager_agent_gym.schemas.core.workflow import Workflow
from manager_agent_gym.schemas.core.tasks import Task
from manager_agent_gym.schemas.core.base import TaskStatus
from manager_agent_gym.schemas.preferences import Constraint


def create_workflow() -> Workflow:
    """Create a Legal M&A workflow using the shared Pydantic schemas.

    Mirrors the ICAAP example structure: constructs a `Workflow`, registers
    `Task`s with dependencies and subtasks, and attaches governance `Constraint`s.
    """

    workflow = Workflow(
        name="Mid-Market Tech Acquisition – Legal M&A",
        workflow_goal=(
            """
            Objective: Coordinate end-to-end legal workstreams for a mid-market tech acquisition and
            reach signing/closing within ~90 days while preserving key customer relationships and
            minimizing regulatory risk.

            Primary deliverables:
            - SPA drafts and a redline history with change rationales and crisp decision memos
            - Evidence-linked disclosure schedules and consent lists mapped to diligence artifacts
            - HSR submission (and CFIUS notice if elected) with waiting-period tracking and mitigations
            - Funds-flow, sources/uses, signature packets, and a complete closing set with bring-down plan
            - Risk register, RAID log, weekly status cadence, and board/committee approvals

            Acceptance criteria (aligned with evaluators):
            - Drafting completeness/consistency across SPA core sections with coherent fallback ladders
            - Disclosure schedules are precise, current, and cite supporting evidence from the data room
            - Funds-flow and closing set are execution-ready; bring-down confirmations planned
            - HSR/CFIUS filings prepared and submitted as required; third-party consents actively managed
            - Governance artifacts captured; no hard gating items outstanding at close

            Team alignment (see team configuration and timeline):
            - AI agents: deal_counsel_ai, diligence_reader, schedules_builder, redline_explainer,
              antitrust_analyst, cfius_analyst, tax_structuring_ai, funds_flow_coordinator,
              closing_checklist_manager, project_coordinator
            - Human roles: lead_mna_partner, senior_mna_associate, regulatory/ip/privacy/employment/finance counsel,
              tax_partner, rwi_broker, acquirer GC/CFO, target CEO
            - Preference dynamics emphasize early momentum (speed), then raise quality and compliance as signing approaches.
            """
        ),
        owner_id=uuid4(),
    )

    # T1: Intake & objectives
    t1 = Task(
        id=UUID(int=2000),
        name="Deal Intake & Objectives",
        description=(
            "Kickoff; define EV, consideration mix, must-have protections (RWI, escrow),"
            " risks, and cadence. Produce deal memo and seed risk register."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=6.0,
        estimated_cost=1200.0,
    )
    t1.subtasks = [
        Task(
            id=UUID(int=2100),
            name="Stakeholder Kickoff & Deal Memo v0",
            description="Initial stakeholder session; produce v0 deal memo and RAID seed.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=600.0,
        ),
        Task(
            id=UUID(int=2101),
            name="Dataroom Structure & Permissions",
            description="Create secure dataroom, access controls, and audit trail.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=2.0,
            estimated_cost=400.0,
        ),
    ]

    # T2: Governance readiness
    t2 = Task(
        id=UUID(int=2001),
        name="Authority & Governance Readiness",
        description=(
            "Map approvals/decision rights; draft resolutions; confirm conflicts and engagements."
        ),
        status=TaskStatus.PENDING,
        dependency_task_ids=[t1.id],
        estimated_duration_hours=5.0,
        estimated_cost=1000.0,
    )

    # T3: Diligence scope and RFIs
    t3 = Task(
        id=UUID(int=2002),
        name="Diligence Scope & RFI Program",
        description=(
            "Define diligence scope (legal/financial/tax/commercial/IP/privacy/HR/security),"
            " issue RFIs, and establish evidence standards with provenance."
        ),
        status=TaskStatus.PENDING,
        dependency_task_ids=[t1.id],
        estimated_duration_hours=8.0,
        estimated_cost=1600.0,
    )

    # T4: Financial diligence (QoE/WC)
    t4 = Task(
        id=UUID(int=2003),
        name="Financial Diligence – QoE & Working Capital",
        description=(
            "Coordinate QoE and WC analysis; inform price, earnout metrics, and SPA drafting."
        ),
        status=TaskStatus.PENDING,
        dependency_task_ids=[t3.id],
        estimated_duration_hours=10.0,
        estimated_cost=2000.0,
    )

    # T5: Corporate/equity/litigation diligence
    t5 = Task(
        id=UUID(int=2004),
        name="Legal Diligence – Corporate, Equity, & Litigation",
        description=(
            "Verify corporate standing, cap table, equity plans, disputes; summarize exposures."
        ),
        status=TaskStatus.PENDING,
        dependency_task_ids=[t3.id],
        estimated_duration_hours=9.0,
        estimated_cost=1800.0,
    )

    # T6: Contracts/IP/privacy diligence
    t6 = Task(
        id=UUID(int=2005),
        name="Legal Diligence – Material Contracts, IP, & Privacy",
        description=(
            "Review key contracts (consents/MFN/termination), IP chain-of-title/OSS, and privacy posture."
        ),
        status=TaskStatus.PENDING,
        dependency_task_ids=[t3.id],
        estimated_duration_hours=12.0,
        estimated_cost=2400.0,
    )

    # T7: Regulatory & antitrust assessment
    t7 = Task(
        id=UUID(int=2006),
        name="Regulatory & Antitrust Assessment (HSR/CFIUS)",
        description=(
            "Assess HSR reportability and CFIUS triggers; outline filing timeline and risk-sharing."
        ),
        status=TaskStatus.PENDING,
        dependency_task_ids=[t1.id, t3.id],
        estimated_duration_hours=6.0,
        estimated_cost=1200.0,
    )

    # T8: Structure & tax planning
    t8 = Task(
        id=UUID(int=2007),
        name="Deal Structure & Tax Planning",
        description=(
            "Select structure (asset/stock/merger), elections, and rollover/earnout mechanics; draft step-plan."
        ),
        status=TaskStatus.PENDING,
        dependency_task_ids=[t4.id, t5.id, t6.id, t7.id],
        estimated_duration_hours=8.0,
        estimated_cost=1600.0,
    )

    # T9: Financing and RWI
    t9 = Task(
        id=UUID(int=2008),
        name="Financing Workstream (Debt/RWI)",
        description=(
            "Secure debt commitments; coordinate RWI underwriting; align with SPA conditionality."
        ),
        status=TaskStatus.PENDING,
        dependency_task_ids=[t4.id, t8.id],
        estimated_duration_hours=7.0,
        estimated_cost=1400.0,
    )

    # T10: Drafting – SPA v1 and schedules
    t10 = Task(
        id=UUID(int=2009),
        name="Drafting – SPA and Schedules (v1)",
        description=(
            "Produce SPA v1 reflecting structure and diligence; seed disclosure schedules and consent lists."
        ),
        status=TaskStatus.PENDING,
        dependency_task_ids=[t5.id, t6.id, t8.id],
        estimated_duration_hours=10.0,
        estimated_cost=2200.0,
    )

    # T11: Negotiation and redlines
    t11 = Task(
        id=UUID(int=2010),
        name="Negotiation & Redlines",
        description=(
            "Iterative redlines with clear rationales and issue resolution; exec decision memos."
        ),
        status=TaskStatus.PENDING,
        dependency_task_ids=[t10.id],
        estimated_duration_hours=8.0,
        estimated_cost=1600.0,
    )

    # T12: Regulatory filings
    t12 = Task(
        id=UUID(int=2011),
        name="Regulatory Filings (HSR/CFIUS)",
        description=(
            "Prepare/file HSR and any CFIUS notices; track requests and waiting periods."
        ),
        status=TaskStatus.PENDING,
        dependency_task_ids=[t7.id, t10.id, t11.id],
        estimated_duration_hours=6.0,
        estimated_cost=1200.0,
    )

    # T13: Closing mechanics & bring‑down
    t13 = Task(
        id=UUID(int=2012),
        name="Closing Mechanics & Bring-Down Diligence",
        description=(
            "Build closing checklist; finalize consents and funds flow; bring-down reps/covenants."
        ),
        status=TaskStatus.PENDING,
        dependency_task_ids=[t9.id, t11.id, t12.id],
        estimated_duration_hours=7.0,
        estimated_cost=1400.0,
    )

    # T14: Signing & closing
    t14 = Task(
        id=UUID(int=2013),
        name="Signing & Closing",
        description=(
            "Execute signatures; confirm conditions precedent; release funds; circulate closing set."
        ),
        status=TaskStatus.PENDING,
        dependency_task_ids=[t13.id],
        estimated_duration_hours=4.0,
        estimated_cost=800.0,
    )

    # T15: Post‑closing & Day‑1
    t15 = Task(
        id=UUID(int=2014),
        name="Post-Closing & Day-1 Integration Readiness",
        description=(
            "Track covenants (escrow/earnout/indemnities); ensure Day‑1 legal/commercial readiness."
        ),
        status=TaskStatus.PENDING,
        dependency_task_ids=[t14.id],
        estimated_duration_hours=5.0,
        estimated_cost=1000.0,
    )

    for task in [
        t1,
        t2,
        t3,
        t4,
        t5,
        t6,
        t7,
        t8,
        t9,
        t10,
        t11,
        t12,
        t13,
        t14,
        t15,
    ]:
        workflow.add_task(task)

    # Governance and compliance constraints
    workflow.constraints.extend(
        [
            Constraint(
                name="Board Approvals Before Signing",
                description="Acquirer and target board approvals must be executed before signing.",
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=[
                    "Authority & Governance Readiness",
                    "Signing & Closing",
                ],
                metadata={},
            ),
            Constraint(
                name="HSR Acceptance Before Close",
                description=(
                    "HSR filing accepted and waiting period expired or early termination granted before closing."
                ),
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=[
                    "Regulatory Filings (HSR/CFIUS)",
                    "Signing & Closing",
                ],
                metadata={},
            ),
            Constraint(
                name="No Close Without Required Consents",
                description=(
                    "All required third‑party consents listed on disclosure schedules must be obtained or waived."
                ),
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=[
                    "Closing Mechanics & Bring-Down Diligence",
                    "Signing & Closing",
                ],
                metadata={},
            ),
            Constraint(
                name="Financing Sources Available",
                description=(
                    "Debt/RWI and funds flow finalized; no unsatisfied financing‑out that jeopardizes closing."
                ),
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=[
                    "Financing Workstream (Debt/RWI)",
                    "Signing & Closing",
                ],
                metadata={},
            ),
            Constraint(
                name="CFIUS Clearance If Applicable",
                description="CFIUS clearance received if mandatory or elected by the stakeholder.",
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=[
                    "Regulatory Filings (HSR/CFIUS)",
                    "Signing & Closing",
                ],
                metadata={},
            ),
        ]
    )

    return workflow
