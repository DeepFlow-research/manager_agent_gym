"""
Global Data Breach Incident Response — Preferences & Evaluators

Preferences (4):
  - speed                : speed-to-triage/containment vs regulatory clocks
  - regulatory_compliance: jurisdictional accuracy & timeliness of notifications
  - communications       : clarity/consistency of regulator + customer/partner comms
  - documentation        : chain-of-custody, privilege hygiene, audit-ready reporting

Mirrors schema style in prior examples:
  * PreferenceWeights / Preference
  * Evaluator(aggregation=AggregationStrategy.WEIGHTED_AVERAGE, rubrics=[WorkflowRubric...])
  * WorkflowRubric with llm_prompt or evaluator_function
  * create_*_preference_update_requests(): absolute, normalized timeline updates
"""

from typing import List
from manager_agent_gym.schemas.preferences.preference import (
    Preference,
    PreferenceWeights,
)
from manager_agent_gym.schemas.preferences.evaluator import (
    Evaluator,
    AggregationStrategy,
)
from manager_agent_gym.schemas.preferences.rubric import WorkflowRubric, RunCondition
from manager_agent_gym.schemas.preferences import PreferenceWeightUpdateRequest
from manager_agent_gym.schemas.core import Workflow
from manager_agent_gym.schemas.core.base import TaskStatus


# ---------------------------
# Deterministic rule helpers (Workflow -> score in [0, max])
# ---------------------------
def _pct_tasks_completed(workflow: Workflow, name_contains: str | None = None) -> float:
    tasks = list(workflow.tasks.values())
    if name_contains:
        tasks = [t for t in tasks if name_contains.lower() in (t.name or "").lower()]
    if not tasks:
        return 0.0
    done = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
    return done / len(tasks)


def _task_completed(workflow: Workflow, name_contains: str) -> float:
    return 1.0 if _pct_tasks_completed(workflow, name_contains) >= 1.0 else 0.0


# SPEED rules (triage/preservation/containment readiness)
def rule_triage_started(workflow: Workflow) -> float:
    return _task_completed(workflow, "Detection & Legal Triage")


def rule_evidence_custody_ok(workflow: Workflow) -> float:
    return _task_completed(workflow, "Evidence Preservation & Chain of Custody")


def rule_containment_complete(workflow: Workflow) -> float:
    return _task_completed(workflow, "Containment & Eradication")


# REGULATORY COMPLIANCE rules (obligations + notifications executed)
def rule_obligations_matrix_ready(workflow: Workflow) -> float:
    return _task_completed(workflow, "Notification Obligations Matrix")


def rule_notifications_sent(workflow: Workflow) -> float:
    return _task_completed(workflow, "Notifications Dispatch & Tracking")


# COMMUNICATIONS rules (drafts/plan ready)
def rule_comms_plan_ready(workflow: Workflow) -> float:
    return _task_completed(workflow, "Communications & Stakeholder Plan")


# DOCUMENTATION rules (recordkeeping & privileged report)
def rule_recordkeeping_updates_done(workflow: Workflow) -> float:
    return _task_completed(workflow, "Recordkeeping & DPIA/ROPA Updates")


def rule_privileged_report_complete(workflow: Workflow) -> float:
    return _task_completed(workflow, "Post‑Incident Report")


# ---------------------------
# LLM Rubrics
# ---------------------------
speed_rubrics: List[WorkflowRubric] = [
    WorkflowRubric(
        name="speed_to_containment_and_clock_handling",
        llm_prompt=(
            "Evaluate the team's speed and discipline: "
            "Was triage initiated under privilege immediately? "
            "Was evidence preserved without contamination (snapshots, logs, chain-of-custody)? "
            "Was containment/eradication executed quickly and safely? "
            "Assess whether regulatory clocks (e.g., GDPR 72-hour to DPAs; sectoral rules where applicable) "
            "were identified and tracked from the awareness timestamp. Return a numeric score [0, 10]."
        ),
        max_score=10.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    WorkflowRubric(
        name="rule_triage_started",
        evaluator_function=rule_triage_started,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    WorkflowRubric(
        name="rule_evidence_custody_ok",
        evaluator_function=rule_evidence_custody_ok,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    WorkflowRubric(
        name="rule_containment_complete",
        evaluator_function=rule_containment_complete,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
]

compliance_rubrics: List[WorkflowRubric] = [
    WorkflowRubric(
        name="regulatory_clock_adherence_and_jurisdictional_accuracy",
        llm_prompt=(
            "Assess regulatory compliance posture: "
            "Is the notification decisioning accurate by jurisdiction (e.g., GDPR Art. 33 72-hour to DPAs; "
            "US state breach laws; sectoral overlays such as HIPAA where applicable)? "
            "Were content requirements met and timelines documented (including 'without undue delay' to individuals "
            "where required)? Return a numeric score [0, 10]."
        ),
        max_score=10.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    WorkflowRubric(
        name="rule_obligations_matrix_ready",
        evaluator_function=rule_obligations_matrix_ready,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    WorkflowRubric(
        name="rule_notifications_sent",
        evaluator_function=rule_notifications_sent,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
]

communications_rubrics: List[WorkflowRubric] = [
    WorkflowRubric(
        name="communications_quality_and_consistency",
        llm_prompt=(
            "Evaluate regulator/customer/partner communications: "
            "clarity, accuracy, plain language, and avoidance of unsupported admissions; "
            "alignment of facts and uncertainty across all audiences; "
            "inclusion of required elements per guidance (what happened, data involved, mitigations, "
            "steps individuals can take, contacts). Return a numeric score [0, 10]."
        ),
        max_score=10.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    WorkflowRubric(
        name="rule_comms_plan_ready",
        evaluator_function=rule_comms_plan_ready,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
]

documentation_rubrics: List[WorkflowRubric] = [
    WorkflowRubric(
        name="evidence_chain_and_auditability",
        llm_prompt=(
            "Assess documentation hygiene and auditability: "
            "complete chain-of-custody (with hashes/handlers), privilege labeling, versioned artifacts, "
            "and an index that enables reproducibility for examiners/board. Return a numeric score [0, 10]."
        ),
        max_score=10.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    WorkflowRubric(
        name="rule_recordkeeping_updates_done",
        evaluator_function=rule_recordkeeping_updates_done,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    WorkflowRubric(
        name="rule_privileged_report_complete",
        evaluator_function=rule_privileged_report_complete,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
]


# ---------------------------
# Preferences + Evaluators
# ---------------------------
def create_preferences() -> PreferenceWeights:
    """Initial stakeholder weights for breach response (t=0 snapshot)."""
    return PreferenceWeights(
        preferences=[
            Preference(
                name="speed",
                weight=0.45,
                evaluator=Evaluator(
                    name="speed_eval",
                    description="Speed-to-triage/containment and disciplined handling of regulatory clocks.",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=speed_rubrics,
                ),
            ),
            Preference(
                name="regulatory_compliance",
                weight=0.3,
                evaluator=Evaluator(
                    name="compliance_eval",
                    description="Jurisdictional accuracy and timeliness of notifications (regulators/individuals/partners).",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=compliance_rubrics,
                ),
            ),
            Preference(
                name="communications",
                weight=0.15,
                evaluator=Evaluator(
                    name="comms_eval",
                    description="Quality and consistency of regulator/customer/partner communications.",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=communications_rubrics,
                ),
            ),
            Preference(
                name="documentation",
                weight=0.1,
                evaluator=Evaluator(
                    name="docs_eval",
                    description="Evidence chain, privilege hygiene, reproducibility, and audit-ready reporting.",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=documentation_rubrics,
                ),
            ),
        ]
    )


# ---------------------------
# Weight Update Requests (timeline)
# ---------------------------
def create_preference_update_requests() -> list[PreferenceWeightUpdateRequest]:
    """Stakeholder's weight changes over time (absolute, normalized)."""
    timeline: dict[int, PreferenceWeights] = {
        0: PreferenceWeights(
            preferences=[
                Preference(name="speed", weight=0.45),
                Preference(name="regulatory_compliance", weight=0.3),
                Preference(name="communications", weight=0.15),
                Preference(name="documentation", weight=0.1),
            ]
        ),
        12: PreferenceWeights(
            preferences=[
                Preference(name="speed", weight=0.25),
                Preference(name="regulatory_compliance", weight=0.4),
                Preference(name="communications", weight=0.25),
                Preference(name="documentation", weight=0.1),
            ]
        ),
        28: PreferenceWeights(
            preferences=[
                Preference(name="speed", weight=0.15),
                Preference(name="regulatory_compliance", weight=0.3),
                Preference(name="communications", weight=0.2),
                Preference(name="documentation", weight=0.35),
            ]
        ),
    }

    requests: list[PreferenceWeightUpdateRequest] = []
    for ts, weights in sorted(timeline.items(), key=lambda kv: kv[0]):
        changes = weights.get_preference_dict()
        if not changes:
            continue
        requests.append(
            PreferenceWeightUpdateRequest(
                timestep=ts,
                changes=changes,
                mode="absolute",
                normalize=True,
                clamp_zero=True,
                missing="create_zero",
                redistribution="proportional",
            )
        )
    return requests


def create_evaluator_to_measure_goal_achievement() -> Evaluator:
    """Create goal achievement evaluator for global data breach incident response."""
    goal_achievement_rubrics = [
        # Critical incident response deliverables (must have for breach containment and compliance)
        WorkflowRubric(
            name="incident_containment_achieved",
            llm_prompt=(
                "Does the workflow show evidence of incident containment with details including: incident scope contained, "
                "security breach stopped, further data loss prevented, and incident command structure operational? "
                "Return 20.0 if incident containment is achieved, 10.0 if there is evidence of incident containment but it is not complete, 0.0 otherwise."
            ),
            max_score=20.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="regulatory_notifications_compliant",
            llm_prompt=(
                "Do the output resources / generated tasks show evidence of regulatory notifications being sent with details including: GDPR 72-hour notification met, "
                "data protection authorities notified, breach notification timelines adhered to, and regulatory compliance maintained? "
                "Return 13.0 if regulatory notifications are compliant, 5.0 if there is evidence of regulatory notifications but it is not complete, 0.0 otherwise."
            ),
            max_score=13.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="legal_privilege_preserved",
            llm_prompt=(
                "Does preserved legal privilege exist with: attorney-client privilege maintained, "
                "communications properly marked privileged, work product doctrine protected, and confidential information secured? "
                "Return true if legal privilege is preserved, false otherwise."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="evidence_preservation_complete",
            llm_prompt=(
                "Is there a sign of evidence preservation being performed with intention of building a clear chain of custody for governance and reporting? "
                "Return 12.0 if there is evidence of evidence preservation, 6.0 if there is evidence of evidence preservation being planned or started but it is not complete, 0.0 otherwise."
            ),
            max_score=12.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Major communication and remediation deliverables (8-10 points each)
        WorkflowRubric(
            name="customer_notification_executed",
            llm_prompt=(
                "Does executed customer notification exist with: affected customers identified and notified, "
                "notification content legally compliant, communication channels activated, and customer support enhanced? "
                "Return 10.0 if there is evidence for all of the above, removing 2.0 for each missing element. To a minimum of 0.0."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="incident_investigation_completed",
            llm_prompt=(
                "Does completed incident investigation exist with: root cause analysis performed, "
                "attack vector identified, forensic investigation completed, and findings documented? "
                "Return true if incident investigation is completed, false otherwise."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="remediation_actions_implemented",
            llm_prompt=(
                "Do implemented remediation actions exist with: security vulnerabilities patched, "
                "system hardening completed, access controls strengthened, and preventive measures deployed? "
                "Return true if remediation actions are implemented, false otherwise."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="board_executive_reporting",
            llm_prompt=(
                "Does board and executive reporting exist with: board briefing completed, "
                "executive updates provided, governance reporting current, and leadership engagement documented? "
                "Return 8.0 if there is evidence of board and executive reporting, 4.0 if there is evidence of board and executive reporting but it is not complete, 0.0 otherwise."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Important supporting deliverables (5-7 points each)
        WorkflowRubric(
            name="media_crisis_communication",
            llm_prompt=(
                "Is there a sign of media crisis communication being performed with intention of managing the impact of the breach on the company's reputation? "
                "Return 7.0 if there is evidence of media crisis communication, 5.0 if there was any discussion of a need for crisis communication but it was not performed or deemed unnecessary, 3.0 if there was no discussion of a need for crisis communication, 0.0 otherwise."
            ),
            max_score=7.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="partner_vendor_coordination",
            llm_prompt=(
                "Does partner and vendor coordination exist with: third-party partners notified, "
                "vendor relationships managed, supply chain impact assessed, and business continuity maintained? "
                "Return true if partner and vendor coordination is effective, false otherwise."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="cyber_insurance_claims",
            llm_prompt=(
                "Do cyber insurance claims exist with: insurance coverage assessed, "
                "claims filed appropriately, coverage maximized, and insurance coordination active? "
                "Return true if cyber insurance claims are managed, false otherwise."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="litigation_preparedness",
            llm_prompt=(
                "Does litigation preparedness exist with: potential litigation assessed, "
                "litigation strategy developed, legal defenses prepared, and dispute resolution readiness confirmed? "
                "Return true if litigation preparedness is established, false otherwise."
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="post_incident_audit_complete",
            llm_prompt=(
                "Does complete post-incident audit exist with: incident response evaluated, "
                "lessons learned documented, process improvements identified, and audit recommendations implemented? "
                "Return true if post-incident audit is complete, false otherwise."
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Supporting deliverables (3-4 points each)
        WorkflowRubric(
            name="credit_monitoring_services",
            llm_prompt=(
                "Do credit monitoring services exist with: credit monitoring offered to affected individuals, "
                "identity protection services provided, monitoring services operational, and victim support active? "
                "Return true if credit monitoring services are provided, false otherwise."
            ),
            max_score=4.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="incident_response_team_coordination",
            llm_prompt=(
                "Does incident response team coordination exist with: response team activated, "
                "roles and responsibilities clear, cross-functional coordination effective, and team communication optimal? "
                "Return true if incident response team coordination is effective, false otherwise."
            ),
            max_score=4.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="security_improvements_documented",
            llm_prompt=(
                "Do documented security improvements exist with: security enhancements identified, "
                "improvement roadmap developed, security investments planned, and long-term protection strengthened? "
                "Return true if security improvements are documented, false otherwise."
            ),
            max_score=3.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="stakeholder_communication_maintained",
            llm_prompt=(
                "Does maintained stakeholder communication exist with: stakeholder updates regular, "
                "communication channels open, transparency maintained, and stakeholder confidence preserved? "
                "Return true if stakeholder communication is maintained, false otherwise."
            ),
            max_score=3.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    return Evaluator(
        name="legal_global_data_breach_goal_achievement_eval",
        description="Global data breach incident response and recovery deliverable achievement measurement",
        aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
        rubrics=goal_achievement_rubrics,
    )
