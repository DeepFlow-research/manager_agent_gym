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
        name="Enterprise SaaS MSA/SOW Negotiation Factory",
        workflow_goal=(
            "Stand up a repeatable, metrics‑driven commercial contracting factory for Enterprise SaaS deals. "
            "Objectives: qualify and tier deals, select playbooks, run redlines with controlled deviations, "
            "complete DPA/security reviews, secure approvals, and execute signatures with CLM ingest and "
            "obligation handoff. Optimize cycle time without increasing risk exposure."
        ),
        owner_id=uuid4(),
    )

    # ---------------------------
    # PHASE 1 — Intake, Tiering, and Deal Package
    # ---------------------------
    intake_qualification = Task(
        name="Intake & Risk Tiering",
        description=(
            "Deal intake form; risk tiering based on ARR, data sensitivity, residency, industry/regime (e.g., finance/health), "
            "and requested deviations. Output: tier, target cycle time, and required artifacts checklist."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=6.0,
        estimated_cost=1200.0,
    )
    intake_qualification.subtasks = [
        Task(
            name="Deal Intake Form",
            description="Collect customer, product, data flows, geographies, and term sheets.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=2.0,
            estimated_cost=300.0,
        ),
        Task(
            name="Risk Tier Decision",
            description="Assign tier (L/M/H) using rubric; set SLA and approver map.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=2.0,
            estimated_cost=400.0,
        ),
        Task(
            name="Artifacts Checklist",
            description="Define required docs (MSA/SOW, DPA, InfoSec, Insurance, Export, Finance).",
            status=TaskStatus.PENDING,
            estimated_duration_hours=2.0,
            estimated_cost=500.0,
        ),
    ]

    customer_profile = Task(
        name="Customer Profile & Data Flows",
        description=(
            "Map data categories (PII/PHI/PCI), residency, transfers, processors/sub‑processors, and product usage to inform DPA and security scopes."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=8.0,
        estimated_cost=1600.0,
        dependency_task_ids=[intake_qualification.task_id],
    )
    customer_profile.subtasks = [
        Task(
            name="Data Categories & Residency",
            description="Identify data types and storage/processing locations; cross‑border transfers.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=600.0,
        ),
        Task(
            name="Sub‑Processor Mapping",
            description="Confirm sub‑processors used and notices/consents needed.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=600.0,
        ),
        Task(
            name="Product Scope Confirmation",
            description="SKU/modules, environments (prod/sandbox), and support duties.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=2.0,
            estimated_cost=400.0,
        ),
    ]

    package_assembly = Task(
        name="Contract Package Assembly",
        description=(
            "Assemble initial contracting package: company paper MSA + SOW template, DPA, InfoSec/controls exhibits, SLAs, support/maintenance, pricing order form."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=6.0,
        estimated_cost=1200.0,
        dependency_task_ids=[customer_profile.task_id],
    )
    package_assembly.subtasks = [
        Task(
            name="MSA/SOW Templates",
            description="Load latest templates; clause library and alt language versions.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=2.0,
            estimated_cost=400.0,
        ),
        Task(
            name="DPA & Transfers Annex",
            description="Attach DPA with SCCs/IDTA/approved mechanisms; list sub‑processors.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=2.0,
            estimated_cost=400.0,
        ),
        Task(
            name="Security & SLA Exhibits",
            description="Controls matrix (SIG/CAIQ mapping), uptime/response SLAs, credits schedule.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=2.0,
            estimated_cost=400.0,
        ),
    ]

    # ---------------------------
    # PHASE 2 — Playbook, Redlines, and Reviews
    # ---------------------------
    playbook_selection = Task(
        name="Playbook Selection & Deviation Plan",
        description=(
            "Select applicable playbook based on tier; pre‑approve fallback positions and define boundaries for negotiator discretion. "
            "Log anticipated deviations and approval path."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=5.0,
        estimated_cost=1000.0,
        dependency_task_ids=[package_assembly.task_id],
    )
    playbook_selection.subtasks = [
        Task(
            name="Fallback Map",
            description="Map fallback language and guardrails for key clauses (limitation, indemnity, data, IP, audit).",
            status=TaskStatus.PENDING,
            estimated_duration_hours=2.0,
            estimated_cost=350.0,
        ),
        Task(
            name="Deviation Register",
            description="Pre‑log requested/likely deviations with approver list and rationales.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=1.5,
            estimated_cost=300.0,
        ),
        Task(
            name="Negotiation Plan",
            description="Define sequencing (paper first/cross‑redlines), deadlines, and risk posture.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=1.5,
            estimated_cost=350.0,
        ),
    ]

    redline_round1 = Task(
        name="Redlines Round 1 (Legal)",
        description="Apply redlines per playbook; annotate clause rationales; generate issues list.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=10.0,
        estimated_cost=2500.0,
        dependency_task_ids=[playbook_selection.task_id],
    )
    redline_round1.subtasks = [
        Task(
            name="Clause Coverage Audit",
            description="Ensure all key clauses present and aligned to baseline: liability caps, indemnities, IP/licence, audit/controls, termination/SOW changes.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=900.0,
        ),
        Task(
            name="DPA Alignment",
            description="Align definitions/priority of docs, breach notice timelines, transfer mechanisms, subprocessors & audits.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=800.0,
        ),
        Task(
            name="Issues List",
            description="Summarize negotiable vs hard‑no items; assign owners and due dates.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=800.0,
        ),
    ]

    infosec_questionnaire = Task(
        name="Security Questionnaire & Controls Mapping",
        description="Complete/respond to SIG/CAIQ or customer questionnaire; map to controls exhibit; capture gaps and mitigations.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=8.0,
        estimated_cost=1800.0,
        dependency_task_ids=[package_assembly.task_id],
    )
    export_sanctions = Task(
        name="Export Controls & Sanctions Screening",
        description="Screen parties, end use, and geographies; add export clauses if applicable.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=4.0,
        estimated_cost=900.0,
        dependency_task_ids=[package_assembly.task_id],
    )
    insurance_review = Task(
        name="Insurance Certificates & Risk Transfer",
        description="Verify insurance requirements (cyber, E&O, GL) and obtain certificates; align indemnity and caps with coverage.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=4.0,
        estimated_cost=800.0,
        dependency_task_ids=[package_assembly.task_id],
    )

    counterparty_paper = Task(
        name="Counterparty Paper (If Required)",
        description="If negotiating on customer paper, normalize to clause library, identify deltas, and expand approvals accordingly.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=10.0,
        estimated_cost=2500.0,
        dependency_task_ids=[redline_round1.task_id],
    )

    # ---------------------------
    # PHASE 3 — Approvals & Governance
    # ---------------------------
    internal_approvals = Task(
        name="Internal Approvals & Escalations",
        description="Collect approvals for deviations: Legal exec, Security, Finance, Sales leadership, and Product as needed.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=6.0,
        estimated_cost=1200.0,
        dependency_task_ids=[
            redline_round1.task_id,
            infosec_questionnaire.task_id,
            insurance_review.task_id,
            export_sanctions.task_id,
        ],
    )
    internal_approvals.subtasks = [
        Task(
            name="Deviation Approvals",
            description="Route deviation register to approvers; capture decisions and conditions.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=600.0,
        ),
        Task(
            name="Risk Register & Exceptions Table",
            description="Finalize exceptions table with owner, mitigation, and review dates.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=600.0,
        ),
    ]

    redline_round2 = Task(
        name="Redlines Round 2 (Negotiation)",
        description="Respond to counterparty; converge on final text; lock schedules and exhibits.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=8.0,
        estimated_cost=2000.0,
        dependency_task_ids=[internal_approvals.task_id],
    )

    # ---------------------------
    # PHASE 4 — Signature & Handoff
    # ---------------------------
    signature_package = Task(
        name="Signature Package Assembly",
        description="Assemble execution‑ready docs with signature blocks, exhibits, and order forms; verify legal names and authorities.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=4.0,
        estimated_cost=700.0,
        dependency_task_ids=[redline_round2.task_id],
    )
    esignature = Task(
        name="eSignature & Counterparts",
        description="Execute via e‑signature platform; track completion and counterparts; handle notarization if required.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=3.0,
        estimated_cost=500.0,
        dependency_task_ids=[signature_package.task_id],
    )
    clm_ingest = Task(
        name="CLM Ingest & Metadata",
        description="Ingest fully executed docs into CLM; extract clause metadata; set renewal/notice dates.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=5.0,
        estimated_cost=900.0,
        dependency_task_ids=[esignature.task_id],
    )
    obligations_handoff = Task(
        name="Obligations & SLA Handoff",
        description="Publish obligations matrix to Sales/CS/Support/Sec; set alerts for SLAs, audits, and renewals.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=5.0,
        estimated_cost=800.0,
        dependency_task_ids=[clm_ingest.task_id],
    )
    kickoff = Task(
        name="Customer Kickoff & Playbook Feedback",
        description="Run internal/external kickoff; capture playbook learnings and update clause library.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=3.0,
        estimated_cost=600.0,
        dependency_task_ids=[obligations_handoff.task_id],
    )

    # Register tasks
    for t in [
        intake_qualification,
        customer_profile,
        package_assembly,
        playbook_selection,
        redline_round1,
        infosec_questionnaire,
        export_sanctions,
        insurance_review,
        counterparty_paper,
        internal_approvals,
        redline_round2,
        signature_package,
        esignature,
        clm_ingest,
        obligations_handoff,
        kickoff,
    ]:
        WorkflowMutations.add_task(wf, t)

    # ---------------------------
    # CONSTRAINTS (Playbook, Compliance, Execution Hygiene)
    # ---------------------------
    wf.constraints.extend(
        [
            Constraint(
                name="Playbook Deviation Approval",
                description="Any deviation beyond pre‑approved fallbacks must have documented approval before counter‑offer.",
                constraint_type="organizational",
                enforcement_level=0.95,
                applicable_task_types=[
                    "Playbook Selection & Deviation Plan",
                    "Redlines Round 1 (Legal)",
                    "Redlines Round 2 (Negotiation)",
                ],
                metadata={
                    "approvers": ["legal_exec", "security", "finance", "product"]
                },
            ),
            Constraint(
                name="DPA & Transfers Mechanism",
                description="DPA must be executed with valid cross‑border transfer mechanism and subprocessors listed.",
                constraint_type="regulatory",
                enforcement_level=0.95,
                applicable_task_types=[
                    "Contract Package Assembly",
                    "Redlines Round 1 (Legal)",
                ],
                metadata={
                    "mechanisms": ["SCCs", "UK IDTA", "Addenda/Appropriate Safeguards"]
                },
            ),
            Constraint(
                name="Security Questionnaire Completion",
                description="Security questionnaire/controls mapping must be completed or waived by Security before approvals.",
                constraint_type="organizational",
                enforcement_level=0.9,
                applicable_task_types=[
                    "Security Questionnaire & Controls Mapping",
                    "Internal Approvals & Escalations",
                ],
                metadata={"standards": ["SIG", "CAIQ", "SOC2", "ISO27001"]},
            ),
            Constraint(
                name="Export/Sanctions Clearance",
                description="Export control and sanctions screening must be completed before signature.",
                constraint_type="regulatory",
                enforcement_level=0.9,
                applicable_task_types=[
                    "Export Controls & Sanctions Screening",
                    "Signature Package Assembly",
                ],
                metadata={},
            ),
            Constraint(
                name="Insurance Evidence",
                description="Certificates of insurance meeting contract thresholds must be on file before signature.",
                constraint_type="organizational",
                enforcement_level=0.85,
                applicable_task_types=[
                    "Insurance Certificates & Risk Transfer",
                    "Signature Package Assembly",
                ],
                metadata={"coverage": ["cyber", "E&O", "GL"]},
            ),
            Constraint(
                name="CLM Ingest Required",
                description="Fully executed documents must be ingested into CLM with metadata extracted before handoff.",
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=[
                    "CLM Ingest & Metadata",
                    "Obligations & SLA Handoff",
                ],
                metadata={
                    "required_metadata": [
                        "renewal_date",
                        "notice_period",
                        "liability_cap",
                        "indemnity_scope",
                    ]
                },
            ),
            Constraint(
                name="PII and Secrets Redaction",
                description="Confidential information must be redacted or access‑controlled in artifacts and communications.",
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=[
                    "Intake & Risk Tiering",
                    "Contract Package Assembly",
                    "Redlines Round 1 (Legal)",
                    "Redlines Round 2 (Negotiation)",
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
    stakeholder = create_stakeholder_agent(persona="deal_desk", preferences=prefs)
    WorkflowMutations.add_agent(wf, stakeholder)

    return wf
