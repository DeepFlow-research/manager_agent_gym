from manager_agent_gym.schemas.core.workflow import Workflow
from manager_agent_gym.schemas.core.tasks import Task
from manager_agent_gym.schemas.core.base import TaskStatus
from manager_agent_gym.schemas.preferences import Constraint
from uuid import uuid4

from examples.common_stakeholders import create_stakeholder_agent
from .preferences import create_preferences  # if present later


def create_workflow() -> Workflow:
    wf = Workflow(
        name="Global Data Breach Incident Response (Privacy/Security)",
        workflow_goal=(
            "Coordinate legal‑privileged, cross‑functional response to a suspected global data breach impacting "
            "EU/US customers and partners. Objectives: preserve evidence, scope and contain the incident, determine "
            "notification obligations and timing, execute regulator/customer/partner communications, and implement "
            "remediation. Produce a defensible post‑incident report and board briefing with corrective action plan."
        ),
        owner_id=uuid4(),
    )

    # ---------------------------
    # PHASE 1 — Detection, Triage & Preservation
    # ---------------------------
    detection_triage = Task(
        name="Detection & Legal Triage",
        description=(
            "Open incident under legal privilege; classify severity; appoint Incident Commander (Legal). "
            "Ensure initial facts are captured and clock start is noted for notification SLAs."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=6.0,
        estimated_cost=3500.0,
    )
    detection_triage.subtasks = [
        Task(
            name="Incident Ticket & Severity",
            description="Create ticket; assign severity; record awareness timestamp; link systems/owners.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=1.5,
            estimated_cost=600.0,
        ),
        Task(
            name="Privilege & Counsel Engagement",
            description="Engage internal/external counsel; mark communications privileged & confidential.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=1.0,
            estimated_cost=700.0,
        ),
        Task(
            name="Legal Hold Issuance",
            description="Issue legal hold to relevant custodians; include IT, Security, Product, Support, Vendors.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=1.0,
            estimated_cost=500.0,
        ),
        Task(
            name="Initial Fact Pattern",
            description="Capture who/what/when/how; suspected data types; potential geographies and volumes.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=2.5,
            estimated_cost=1700.0,
        ),
    ]

    evidence_preservation = Task(
        name="Evidence Preservation & Chain of Custody",
        description=(
            "Snapshot affected systems; collect logs/artifacts; enforce chain‑of‑custody and access controls."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=8.0,
        estimated_cost=5000.0,
        dependency_task_ids=[detection_triage.task_id],
    )
    evidence_preservation.subtasks = [
        Task(
            name="System Snapshots & Images",
            description="Capture forensic images; time‑sync; hash and store in evidence vault.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=1800.0,
        ),
        Task(
            name="Log & Artifact Collection",
            description="Collect auth, app, DB, network logs; ticket trails; endpoint telemetry.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=1600.0,
        ),
        Task(
            name="Chain of Custody Ledger",
            description="Establish evidence ledger; track handlers; restrict access; audit periodically.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=2.0,
            estimated_cost=1600.0,
        ),
    ]

    # ---------------------------
    # PHASE 2 — Scoping, Data Mapping & Obligations
    # ---------------------------
    forensics_scoping = Task(
        name="Forensics Scoping & Timeline",
        description=(
            "Establish attack vector hypotheses; identify impacted systems/accounts; reconstruct a timeline of events."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=14.0,
        estimated_cost=9000.0,
        dependency_task_ids=[evidence_preservation.task_id],
    )
    forensics_scoping.subtasks = [
        Task(
            name="Attack Vector Hypotheses",
            description="Phishing? Credential stuffing? Supply chain? Build testable hypotheses.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=2500.0,
        ),
        Task(
            name="Impacted Systems & Accounts",
            description="Inventory affected services, identities, and data stores; define blast radius.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=5.0,
            estimated_cost=3000.0,
        ),
        Task(
            name="Event Timeline",
            description="Reconstruct dwell time and lateral movement; identify first/last known bad.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=5.0,
            estimated_cost=3500.0,
        ),
    ]

    data_mapping = Task(
        name="Data Classification & Residency Mapping",
        description=(
            "Classify data (PII/PHI/PCI/sensitive categories), link to jurisdictions and storage/processing locations, "
            "and estimate affected data subjects/records."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=12.0,
        estimated_cost=7000.0,
        dependency_task_ids=[forensics_scoping.task_id],
    )
    data_mapping.subtasks = [
        Task(
            name="Data Subjects & Categories",
            description="Identify categories (customers, employees, partners) and sensitive flags (minors, health).",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=1800.0,
        ),
        Task(
            name="Residency & Cross‑Border Transfers",
            description="Map data storage/processing locations; identify restricted transfers.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=2000.0,
        ),
        Task(
            name="Volume Estimation",
            description="Estimate records affected by system/log inference; track uncertainty bands.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=2200.0,
        ),
    ]

    obligations_matrix = Task(
        name="Notification Obligations Matrix",
        description=(
            "Determine whether/when to notify regulators, individuals, and partners across jurisdictions; "
            "capture legal bases, timelines, and content requirements."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=10.0,
        estimated_cost=6500.0,
        dependency_task_ids=[data_mapping.task_id],
    )
    obligations_matrix.subtasks = [
        Task(
            name="Regulator Matrix",
            description="EU DPA 72‑hour assessment; US state breach laws; sectoral overlays (e.g., GLBA/HIPAA).",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=2600.0,
        ),
        Task(
            name="Contractual Notices",
            description="Customer/partner contract notice obligations and SLAs.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=1900.0,
        ),
        Task(
            name="Notification Content Checklist",
            description="Required elements (facts, scope, mitigations, rights, contacts) by jurisdiction.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=2000.0,
        ),
    ]

    # ---------------------------
    # PHASE 3 — Containment, Remediation & Communications
    # ---------------------------
    containment = Task(
        name="Containment & Eradication",
        description="Isolate affected assets; revoke credentials/keys; patch and harden; monitor for persistence.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=16.0,
        estimated_cost=9000.0,
        dependency_task_ids=[forensics_scoping.task_id],
    )
    containment.subtasks = [
        Task(
            name="Access Revocation & Key Rotation",
            description="Disable compromised accounts; rotate secrets/keys; tighten policies.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=2200.0,
        ),
        Task(
            name="Patching & Hardening",
            description="Apply fixes; add detections; block indicators; verify configuration baselines.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=3500.0,
        ),
        Task(
            name="Persistence Hunt",
            description="Search for backdoors and scheduled tasks; verify clean state.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=3300.0,
        ),
    ]

    comms_plan = Task(
        name="Communications & Stakeholder Plan",
        description=(
            "Draft regulator notifications, customer/partner notices, FAQs, employee comms, and press holding statements; "
            "define spokespersons and Q&A protocols."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=12.0,
        estimated_cost=6000.0,
        dependency_task_ids=[obligations_matrix.task_id],
    )
    comms_plan.subtasks = [
        Task(
            name="Regulator Notifications Drafts",
            description="Prepare DPA/AG draft notices and forms for counsel review.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=2200.0,
        ),
        Task(
            name="Customer/Partner Notice Drafts",
            description="Draft customer/partner notices and FAQs; align on tone and distribution list.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=1900.0,
        ),
        Task(
            name="Internal/Press Brief",
            description="Internal guidance and external holding statement; media strategy if needed.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=1900.0,
        ),
    ]

    vendor_coordination = Task(
        name="Vendor & Third‑Party Coordination",
        description="Coordinate with processors/sub‑processors or vendors potentially implicated; confirm their remediation.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=8.0,
        estimated_cost=4200.0,
        dependency_task_ids=[forensics_scoping.task_id, obligations_matrix.task_id],
    )

    notifications_dispatch = Task(
        name="Notifications Dispatch & Tracking",
        description="File regulator notices and send individual/partner notifications; track acknowledgements and responses.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=10.0,
        estimated_cost=5000.0,
        dependency_task_ids=[comms_plan.task_id, containment.task_id],
    )

    # ---------------------------
    # PHASE 4 — Documentation, Governance & Improvement
    # ---------------------------
    remediation = Task(
        name="Remediation & Security Enhancements",
        description="Implement corrective actions (controls, monitoring, training) and verify effectiveness.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=12.0,
        estimated_cost=7000.0,
        dependency_task_ids=[containment.task_id],
    )

    recordkeeping = Task(
        name="Recordkeeping & DPIA/ROPA Updates",
        description="Update ROPA entries, DPIAs where relevant, and maintain full incident record for audit/regulators.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=8.0,
        estimated_cost=4200.0,
        dependency_task_ids=[notifications_dispatch.task_id],
    )

    post_incident_report = Task(
        name="Post‑Incident Report (Privileged)",
        description="Draft final privileged report: timeline, facts, scope, notifications, remediation, and lessons learned.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=14.0,
        estimated_cost=9000.0,
        dependency_task_ids=[remediation.task_id, recordkeeping.task_id],
    )

    board_brief = Task(
        name="Board Briefing & Decisions",
        description="Deliver executive summary to Board; capture decisions and budget approvals for long‑term fixes.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=4.0,
        estimated_cost=2500.0,
        dependency_task_ids=[post_incident_report.task_id],
    )

    lessons_learned = Task(
        name="Lessons Learned & Playbook Updates",
        description="Run retrospective; update playbooks/runbooks; schedule training and test exercises.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=6.0,
        estimated_cost=2500.0,
        dependency_task_ids=[board_brief.task_id],
    )

    # Register tasks
    for t in [
        detection_triage,
        evidence_preservation,
        forensics_scoping,
        data_mapping,
        obligations_matrix,
        containment,
        comms_plan,
        vendor_coordination,
        notifications_dispatch,
        remediation,
        recordkeeping,
        post_incident_report,
        board_brief,
        lessons_learned,
    ]:
        wf.add_task(t)

    # ---------------------------
    # CONSTRAINTS (Regulatory, Privilege, Documentation)
    # ---------------------------
    wf.constraints.extend(
        [
            Constraint(
                name="Legal Hold Enforced",
                description="Legal hold must be issued to relevant custodians before any system changes that could alter evidence.",
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=[
                    "Detection & Legal Triage",
                    "Evidence Preservation & Chain of Custody",
                ],
                metadata={"evidence": ["hold_notices", "acknowledgements"]},
            ),
            Constraint(
                name="Chain of Custody Preserved",
                description="Evidence must have a complete chain‑of‑custody with restricted access and hashing.",
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=["Evidence Preservation & Chain of Custody"],
                metadata={"requirements": ["hashes", "access_logs", "ledger"]},
            ),
            Constraint(
                name="Regulatory Notification Timelines",
                description="Regulator notification obligations (e.g., 72‑hour to EU DPAs, applicable US state timelines) must be assessed and met when required.",
                constraint_type="regulatory",
                enforcement_level=0.95,
                applicable_task_types=[
                    "Notification Obligations Matrix",
                    "Communications & Stakeholder Plan",
                    "Notifications Dispatch & Tracking",
                ],
                metadata={"sla_hours": [72]},
            ),
            Constraint(
                name="Customer/Partner Notice Legal Review",
                description="All external notices must be reviewed and approved by counsel before dispatch.",
                constraint_type="organizational",
                enforcement_level=0.9,
                applicable_task_types=[
                    "Communications & Stakeholder Plan",
                    "Notifications Dispatch & Tracking",
                ],
                metadata={"approvers": ["privacy_counsel", "external_counsel"]},
            ),
            Constraint(
                name="Privileged Communications",
                description="All investigative communications are privileged & confidential and must be labeled and stored accordingly.",
                constraint_type="organizational",
                enforcement_level=0.9,
                applicable_task_types=[
                    "Detection & Legal Triage",
                    "Forensics Scoping & Timeline",
                    "Post‑Incident Report (Privileged)",
                ],
                metadata={"labels": ["attorney_client_privileged", "work_product"]},
            ),
            Constraint(
                name="PII and Secrets Redaction",
                description="Confidential information must be redacted or access‑controlled in artifacts and communications.",
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=[
                    "Communications & Stakeholder Plan",
                    "Notifications Dispatch & Tracking",
                    "Recordkeeping & DPIA/ROPA Updates",
                    "Post‑Incident Report (Privileged)",
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

    prefs = create_preferences()
    stakeholder = create_stakeholder_agent(persona="risk_averse", preferences=prefs)
    wf.add_agent(stakeholder)

    return wf
