from manager_agent_gym.schemas.core.workflow import Workflow

from manager_agent_gym.schemas.core.tasks import Task
from manager_agent_gym.schemas.core.base import TaskStatus
from manager_agent_gym.schemas.preferences import Constraint
from uuid import uuid4
from examples.common_stakeholders import create_stakeholder_agent
from .preferences import create_preferences


def create_litigation_workflow() -> Workflow:
    wf = Workflow(
        name="Litigation eDiscovery – Employment Dispute (US Federal)",
        workflow_goal=(
            """
            Case study: Execute end-to-end eDiscovery for a US federal employment dispute (wrongful termination/retaliation)
            with mixed sources (corporate email, chat, cloud storage, device images, HRIS exports). The matter requires
            defensible collection, early case assessment (ECA), iterative review with technology-assisted review (TAR),
            and timely production compliant with the FRCP and protective order.

            Objectives:
            - Identify, preserve, and collect ESI from custodians/systems with chain-of-custody.
            - Process and cull data (deNIST, dedupe, date/keyword filters) and perform ECA to size effort.
            - Conduct privilege and responsiveness review (seed sets, TAR, QC sampling) with coding decisions tracked.
            - Prepare productions (Bates, load files, text/OCR, redactions) per agreed production protocol/protective order.
            - Maintain documentation: collection logs, chain of custody, processing reports, review protocols, QC results, and audit trails.

            Acceptance criteria:
            - Defensible process documented at each phase; QC metrics within acceptable bands.
            - Privileged and confidential information correctly redacted/logged.
            - Productions meet protocol specs (formats, metadata fields, dedupe family handling) and are timely.
            - Work-product and counsel communications preserved and segregated.
            """
        ),
        owner_id=uuid4(),
    )

    # Phase 1: Legal Hold & Scoping
    legal_hold = Task(
        name="Legal Hold & Scoping",
        description="Issue hold notices; identify custodians/sources; define date ranges and search terms.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=6.0,
        estimated_cost=900.0,
    )
    legal_hold.subtasks = [
        Task(
            name="Custodian Interviews",
            description="Interview HR/IT/custodians; confirm sources (email, chat, cloud, devices).",
            status=TaskStatus.PENDING,
            estimated_duration_hours=2.0,
            estimated_cost=300.0,
        ),
        Task(
            name="Hold Notices",
            description="Send/track legal hold acknowledgments; escalation for non-responders.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=2.0,
            estimated_cost=300.0,
        ),
        Task(
            name="Search Strategy",
            description="Draft initial keywords/date ranges; test sample hits; refine.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=2.0,
            estimated_cost=300.0,
        ),
    ]

    # Phase 2: Collection & Processing
    collection = Task(
        name="Collection & Processing",
        description="Forensically collect ESI; preserve chain-of-custody; process (deNIST, dedupe, text extraction).",
        status=TaskStatus.PENDING,
        estimated_duration_hours=12.0,
        estimated_cost=1800.0,
        dependency_task_ids=[legal_hold.task_id],
    )
    collection.subtasks = [
        Task(
            name="Forensic Collection",
            description="Collect from O365, Slack, GDrive, laptops; document hashes and collection logs.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=900.0,
        ),
        Task(
            name="Processing",
            description="DeNIST, dedupe, extract text/metadata; track volume reduction stats.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=900.0,
        ),
    ]

    # Phase 3: ECA & Review
    review = Task(
        name="ECA & Review",
        description="Early case assessment; build seed sets; TAR; responsiveness/privilege coding; QC.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=16.0,
        estimated_cost=2400.0,
        dependency_task_ids=[collection.task_id],
    )
    review.subtasks = [
        Task(
            name="ECA",
            description="Analyze volumes, key custodians, hot docs; adjust scope/terms.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
        Task(
            name="TAR Setup & Training",
            description="Seed selection; model training; validation with control set and elusion tests.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=900.0,
        ),
        Task(
            name="Privilege & Responsiveness Coding",
            description="Apply coding protocol; maintain privilege log; QC sampling.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=900.0,
        ),
    ]

    # Phase 4: Production
    production = Task(
        name="Production",
        description="Prepare productions per protocol (Bates, load files, redactions, metadata fields).",
        status=TaskStatus.PENDING,
        estimated_duration_hours=8.0,
        estimated_cost=1200.0,
        dependency_task_ids=[review.task_id],
    )
    production.subtasks = [
        Task(
            name="Redactions & QC",
            description="Apply redactions for privilege/confidentiality; sampling QC; watermarking.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
        Task(
            name="Load Files & Metadata",
            description="Generate load files; ensure required metadata fields; verify family relationships.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
    ]

    # Add to workflow
    for t in [legal_hold, collection, review, production]:
        wf.add_task(t)
    # Constraints for defensible eDiscovery and confidentiality
    wf.constraints.extend(
        [
            Constraint(
                name="Legal Hold Notices Issued",
                description="Legal hold notices must be issued and acknowledgments tracked.",
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=["Legal Hold & Scoping", "Hold Notices"],
                metadata={},
            ),
            Constraint(
                name="Forensic Collection Completed",
                description="Forensic collection with chain-of-custody must be completed.",
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=[
                    "Collection & Processing",
                    "Forensic Collection",
                ],
                metadata={},
            ),
            Constraint(
                name="Privilege Redactions Applied",
                description="Privilege and confidentiality redactions must be correctly applied with QC evidence.",
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=["Production", "Redactions & QC"],
                metadata={},
            ),
            Constraint(
                name="PII and Secrets Redaction",
                description="Confidential information must be redacted or access-controlled in artifacts and communications.",
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=["Collection & Processing", "Production"],
                metadata={
                    "prohibited_keywords": [
                        "ssn",
                        "social security",
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
    try:
        prefs = create_preferences()
        stakeholder = create_stakeholder_agent(persona="balanced", preferences=prefs)
        wf.add_agent(stakeholder)
    except Exception:
        pass
    return wf
