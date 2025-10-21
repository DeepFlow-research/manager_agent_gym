"""
Enterprise SaaS MSA/SOW Negotiation Factory — Preferences & Evaluators

Preferences (4):
  - speed               : cycle-time discipline from intake to signature readiness
  - risk_compliance     : DPA/transfers, security questionnaire, export/sanctions, insurance approvals
  - playbook_adherence  : deviation discipline and approval hygiene
  - handoff_quality     : CLM ingest, metadata completeness, obligations matrix & alerts

Mirrors schema style in prior examples:
  * PreferenceWeights / Preference
  * Rubric(aggregation=AggregationStrategy.WEIGHTED_AVERAGE, criteria=[RubricCriteria...])
  * RubricCriteria with llm_prompt or evaluator_function
  * create_*_preference_update_requests(): absolute, normalized timeline updates
"""

from typing import List
from manager_agent_gym.schemas.preferences.preference import (
    Preference,
    PreferenceSnapshot,
)
from manager_agent_gym.schemas.preferences.evaluator import (
    Rubric,
    AggregationStrategy,
)
from manager_agent_gym.schemas.preferences.rubric import RubricCriteria, RunCondition
from manager_agent_gym.schemas.preferences import PreferenceWeightUpdateRequest
from manager_agent_gym.schemas.domain import Workflow
from manager_agent_gym.schemas.domain.base import TaskStatus


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


# ---------------------------
# Hardening Framework Functions
# ---------------------------
def _validate_cost_realism(workflow: Workflow, context) -> float:
    """Penalize unrealistic cost discrepancies for enterprise negotiations."""
    expected_min_cost = 15000.0  # Minimum realistic cost
    total_estimated = sum(
        task.estimated_cost for task in workflow.tasks.values() if task.estimated_cost
    )
    total_actual = sum(
        task.actual_cost for task in workflow.tasks.values() if task.actual_cost
    )

    if total_estimated == 0:
        return 0.0  # No cost planning penalty

    if total_actual < expected_min_cost:
        return 0.0  # Enterprise negotiations should cost more than $15k

    cost_variance = abs(total_actual - total_estimated) / total_estimated
    if cost_variance > 0.3:  # >30% cost variance penalty for negotiations
        return 0.2
    elif cost_variance > 0.15:  # >15% cost variance partial penalty
        return 0.6
    else:
        return 1.0


def _require_external_validation(
    workflow: Workflow, validation_keywords: List[str]
) -> float:
    """Require evidence of external validation for legal and compliance matters."""
    validation_evidence = 0
    total_tasks = len(workflow.tasks)

    for task in workflow.tasks.values():
        if any(
            keyword.lower() in (task.description or "").lower()
            for keyword in validation_keywords
        ):
            if any(
                keyword.lower() in str(res.content or "").lower()
                for res in workflow.resources.values()
                for keyword in [
                    "approved",
                    "validated",
                    "reviewed",
                    "signed-off",
                    "certified",
                ]
            ):
                validation_evidence += 1

    return min(
        1.0, validation_evidence / max(1, total_tasks * 0.25)
    )  # Require 25% external validation


def _negotiation_adversarial_pressure_score(workflow: Workflow) -> float:
    """Score based on handling negotiation adversarial pressure and challenges."""
    pressure_indicators = [
        "customer pushback",
        "legal objection",
        "security concern",
        "compliance challenge",
        "pricing pressure",
        "contract dispute",
        "deadline pressure",
        "competitive threat",
        "redline rejection",
        "deal risk",
        "escalation",
        "executive intervention",
    ]

    pressure_handled = 0
    for indicator in pressure_indicators:
        for res in workflow.resources.values():
            if indicator.lower() in str(res.content or "").lower():
                # Check for resolution evidence
                if any(
                    resolution.lower() in str(res.content or "").lower()
                    for resolution in [
                        "resolved",
                        "mitigated",
                        "addressed",
                        "negotiated",
                        "agreed",
                    ]
                ):
                    pressure_handled += 1
                break

    return min(
        1.0, pressure_handled / max(1, len(pressure_indicators) * 0.3)
    )  # Expect 30% pressure scenarios


# SPEED rules (intake -> redlines -> signature readiness)
def rule_intake_tiering_done(workflow: Workflow) -> float:
    return _task_completed(workflow, "Intake & Risk Tiering")


def rule_playbook_selected(workflow: Workflow) -> float:
    return _task_completed(workflow, "Playbook Selection & Deviation Plan")


def rule_redlines_round1_done(workflow: Workflow) -> float:
    return _task_completed(workflow, "Redlines Round 1")


def rule_signature_package_ready(workflow: Workflow) -> float:
    return _task_completed(workflow, "Signature Package Assembly")


# RISK/COMPLIANCE rules (privacy, security, export, insurance; plus approvals)
def rule_dpa_transfers_attached(workflow: Workflow) -> float:
    # Proxy via Contract Package Assembly completion
    return _task_completed(workflow, "Contract Package Assembly")


def rule_security_questionnaire_done(workflow: Workflow) -> float:
    return _task_completed(workflow, "Security Questionnaire & Controls Mapping")


def rule_export_sanctions_cleared(workflow: Workflow) -> float:
    return _task_completed(workflow, "Export Controls & Sanctions Screening")


def rule_insurance_verified(workflow: Workflow) -> float:
    return _task_completed(workflow, "Insurance Certificates & Risk Transfer")


def rule_internal_approvals_done(workflow: Workflow) -> float:
    return _task_completed(workflow, "Internal Approvals & Escalations")


# PLAYBOOK ADHERENCE rules (deviation register + approvals + round2 close)
def rule_deviation_register_active(workflow: Workflow) -> float:
    return _task_completed(workflow, "Playbook Selection & Deviation Plan")


def rule_negotiation_round2_complete(workflow: Workflow) -> float:
    return _task_completed(workflow, "Redlines Round 2")


# HANDOFF quality rules (CLM, metadata, obligations matrix)
def rule_clm_ingest_complete(workflow: Workflow) -> float:
    return _task_completed(workflow, "CLM Ingest & Metadata")


def rule_obligations_handoff_complete(workflow: Workflow) -> float:
    return _task_completed(workflow, "Obligations & SLA Handoff")


# ---------------------------
# LLM Rubrics
# ---------------------------
speed_rubrics: List[RubricCriteria] = [
    RubricCriteria(
        name="cycle_time_efficiency",
        llm_prompt=(
            "Evaluate cycle-time discipline with specific efficiency requirements:\n"
            "- shows intake and tiering completed within defined SLA timeframes (not just 'quickly')\n"
            "- demonstrates Round 1 redlines covered 80%+ of critical issues with quantifiable coverage\n"
            "- shows signature package assembled with documented approval chain and authority verification\n"
            "- demonstrates proactive deadline management with buffer time for complications\n"
            "PENALTY: Deduct 2 points for each missing quantifiable metric. No credit for subjective 'efficiency'. Return a numeric score [0, 10]."
        ),
        max_score=10.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    RubricCriteria(
        name="rule_intake_tiering_done",
        evaluator_function=rule_intake_tiering_done,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    RubricCriteria(
        name="rule_playbook_selected",
        evaluator_function=rule_playbook_selected,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    RubricCriteria(
        name="rule_redlines_round1_done",
        evaluator_function=rule_redlines_round1_done,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    RubricCriteria(
        name="rule_signature_package_ready",
        evaluator_function=rule_signature_package_ready,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
]

risk_rubrics: List[RubricCriteria] = [
    RubricCriteria(
        name="risk_posture_and_compliance",
        llm_prompt=(
            "Rigorously assess risk/compliance posture with validation requirements:\n"
            "- shows properly executed DPA with valid, current transfer mechanism documentation\n"
            "- demonstrates accurate sub-processor list with independent verification (not just customer-provided)\n"
            "- shows security questionnaire completed with external security team validation\n"
            "- demonstrates export/sanctions checks with legal team sign-off and documentation\n"
            "- shows insurance evidence independently verified and aligned to contract caps\n"
            "PENALTY: Deduct 2 points for each compliance item without external validation. No credit for internal-only reviews. Return a numeric score [0, 10]."
        ),
        max_score=10.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    RubricCriteria(
        name="rule_dpa_transfers_attached",
        evaluator_function=rule_dpa_transfers_attached,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    RubricCriteria(
        name="rule_security_questionnaire_done",
        evaluator_function=rule_security_questionnaire_done,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    RubricCriteria(
        name="rule_export_sanctions_cleared",
        evaluator_function=rule_export_sanctions_cleared,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    RubricCriteria(
        name="rule_insurance_verified",
        evaluator_function=rule_insurance_verified,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    RubricCriteria(
        name="rule_internal_approvals_done",
        evaluator_function=rule_internal_approvals_done,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    RubricCriteria(
        name="negotiation_adversarial_scenarios",
        llm_prompt=(
            "Evaluate handling of adversarial negotiation scenarios:\n"
            "- shows preparation for and handling of aggressive customer pushback on key terms\n"
            "- demonstrates response to competitive pressure and deadline manipulation tactics\n"
            "- shows handling of legal objections and compliance challenges from customer counsel\n"
            "- demonstrates escalation management for executive-level intervention or deal threats\n"
            "- shows contingency planning for redline rejection and negotiation breakdown scenarios\n"
            "Score 0 if no adversarial scenarios addressed. Partial credit only with evidence of pressure AND resolution strategies. Return a numeric score [0, 10]."
        ),
        max_score=10.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    RubricCriteria(
        name="cost_realism_validation",
        evaluator_function=_validate_cost_realism,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
]

playbook_rubrics: List[RubricCriteria] = [
    RubricCriteria(
        name="playbook_deviation_discipline",
        llm_prompt=(
            "Evaluate playbook adherence and deviation discipline: "
            "Are deviations logged with rationale and routed to the right approvers? "
            "Did negotiators stay within discretion boundaries and use fallbacks appropriately? "
            "Is Round 2 focused on true deltas rather than re-litigating baselines? "
            "Return a numeric score [0, 10]."
        ),
        max_score=10.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    RubricCriteria(
        name="rule_deviation_register_active",
        evaluator_function=rule_deviation_register_active,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    RubricCriteria(
        name="rule_negotiation_round2_complete",
        evaluator_function=rule_negotiation_round2_complete,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
]

handoff_rubrics: List[RubricCriteria] = [
    RubricCriteria(
        name="handoff_and_metadata_quality",
        llm_prompt=(
            "Evaluate handoff quality: "
            "Were fully executed documents ingested into CLM with key metadata (renewal dates, notice periods, "
            "liability caps, indemnities)? "
            "Was an obligations/SLA matrix published to GTM/Success with alerts configured? "
            "Return a numeric score [0, 10]."
        ),
        max_score=10.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    RubricCriteria(
        name="rule_clm_ingest_complete",
        evaluator_function=rule_clm_ingest_complete,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    RubricCriteria(
        name="rule_obligations_handoff_complete",
        evaluator_function=rule_obligations_handoff_complete,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
]


# ---------------------------
# Preferences + Evaluators
# ---------------------------
def create_preferences() -> PreferenceSnapshot:
    """Initial stakeholder weights for MSA/SOW factory (t=0 snapshot)."""
    return PreferenceSnapshot(
        preferences=[
            Preference(
                name="speed",
                weight=0.4,
                evaluator=Rubric(
                    name="speed_eval",
                    description="Cycle-time discipline from intake to signature readiness.",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    criteria=speed_rubrics,
                ),
            ),
            Preference(
                name="risk_compliance",
                weight=0.3,
                evaluator=Rubric(
                    name="risk_eval",
                    description="DPA/transfers, security questionnaire, export/sanctions, insurance approvals, and internal approvals.",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    criteria=risk_rubrics,
                ),
            ),
            Preference(
                name="playbook_adherence",
                weight=0.2,
                evaluator=Rubric(
                    name="playbook_eval",
                    description="Deviation discipline and approval hygiene; focus Round 2 on true deltas.",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    criteria=playbook_rubrics,
                ),
            ),
            Preference(
                name="handoff_quality",
                weight=0.1,
                evaluator=Rubric(
                    name="handoff_eval",
                    description="CLM ingest with metadata; obligations matrix & alerts to GTM/Success.",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    criteria=handoff_rubrics,
                ),
            ),
        ]
    )


# ---------------------------
# Weight Update Requests (timeline)
# ---------------------------
def create_preference_update_requests() -> list[PreferenceWeightUpdateRequest]:
    """Stakeholder's weight changes over time (absolute, normalized)."""
    timeline: dict[int, PreferenceSnapshot] = {
        # Early: speed to first redlines + package readiness
        0: PreferenceSnapshot(
            preferences=[
                Preference(name="speed", weight=0.4),
                Preference(name="risk_compliance", weight=0.3),
                Preference(name="playbook_adherence", weight=0.2),
                Preference(name="handoff_quality", weight=0.1),
            ]
        ),
        # Mid: tighten risk/compliance and playbook discipline during negotiation/approvals
        18: PreferenceSnapshot(
            preferences=[
                Preference(name="speed", weight=0.25),
                Preference(name="risk_compliance", weight=0.4),
                Preference(name="playbook_adherence", weight=0.25),
                Preference(name="handoff_quality", weight=0.1),
            ]
        ),
        # Late: ensure clean handoff and metadata; protect renewal/SLAs
        26: PreferenceSnapshot(
            preferences=[
                Preference(name="speed", weight=0.15),
                Preference(name="risk_compliance", weight=0.25),
                Preference(name="playbook_adherence", weight=0.2),
                Preference(name="handoff_quality", weight=0.4),
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


def create_evaluator_to_measure_goal_achievement() -> Rubric:
    """Create goal achievement evaluator for enterprise SaaS MSA/SOW negotiation factory."""
    goal_achievement_rubrics = [
        # Critical contracting process deliverables (must have for commercial deals)
        RubricCriteria(
            name="deal_tiering_risk_assessment_complete",
            llm_prompt=(
                "Does complete deal tiering and risk assessment exist with: risk tier assigned (L/M/H), "
                "target cycle time defined, required artifacts checklist established, and SLA mappings confirmed? "
                "Return true if deal tiering and risk assessment are complete, false otherwise."
            ),
            max_score=12.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="msa_sow_execution_ready",
            llm_prompt=(
                "Does execution-ready MSA/SOW exist with: negotiated terms finalized, "
                "redline deviations controlled and approved, legal review completed, and signature-ready documents prepared? "
                "Return true if MSA/SOW are execution-ready, false otherwise."
            ),
            max_score=15.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="dpa_security_review_approved",
            llm_prompt=(
                "Does approved DPA and security review exist with: data processing addendum finalized, "
                "security requirements validated, privacy compliance confirmed, and InfoSec approval secured? "
                "Return true if DPA and security review are approved, false otherwise."
            ),
            max_score=12.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="signature_execution_complete",
            llm_prompt=(
                "Does complete signature execution exist with: electronic signatures secured, "
                "authorization confirmations received, execution logistics completed, and contract binding confirmed? "
                "Return true if signature execution is complete, false otherwise."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Major operational efficiency deliverables (8-10 points each)
        RubricCriteria(
            name="clm_ingest_obligation_handoff",
            llm_prompt=(
                "Does CLM ingest and obligation handoff exist with: contract management system integration complete, "
                "obligations tracked and assigned, handoff procedures executed, and contract lifecycle management active? "
                "Return true if CLM ingest and obligation handoff are operational, false otherwise."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="customer_data_profile_mapped",
            llm_prompt=(
                "Does mapped customer data profile exist with: data categories identified (PII/PHI/PCI), "
                "residency requirements documented, transfer protocols established, and sub-processor mapping complete? "
                "Return true if customer data profile is mapped, false otherwise."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="playbook_selection_optimization",
            llm_prompt=(
                "Does playbook selection optimization exist with: appropriate playbooks selected for deal type, "
                "deviation control mechanisms active, negotiation efficiency maximized, and process standardization maintained? "
                "Return true if playbook selection is optimized, false otherwise."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="approval_workflow_streamlined",
            llm_prompt=(
                "Does streamlined approval workflow exist with: approver hierarchy established, "
                "escalation paths defined, approval cycle time optimized, and bottleneck resolution active? "
                "Return true if approval workflow is streamlined, false otherwise."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="metrics_driven_cycle_time",
            llm_prompt=(
                "Does metrics-driven cycle time optimization exist with: cycle time tracking active, "
                "performance metrics monitored, optimization targets achieved, and efficiency improvements documented? "
                "Return true if metrics-driven cycle time optimization is active, false otherwise."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Important supporting deliverables (5-7 points each)
        RubricCriteria(
            name="export_control_compliance",
            llm_prompt=(
                "Does export control compliance exist with: export restrictions assessed, "
                "compliance requirements validated, documentation prepared, and regulatory adherence confirmed? "
                "Return true if export control compliance is established, false otherwise."
            ),
            max_score=7.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="insurance_verification_complete",
            llm_prompt=(
                "Does complete insurance verification exist with: insurance requirements validated, "
                "coverage adequacy confirmed, policy documentation secured, and risk protection established? "
                "Return true if insurance verification is complete, false otherwise."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="financial_terms_validation",
            llm_prompt=(
                "Does financial terms validation exist with: pricing terms confirmed, "
                "payment structures validated, revenue recognition approved, and financial compliance ensured? "
                "Return true if financial terms validation is complete, false otherwise."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="cross_border_data_transfers",
            llm_prompt=(
                "Do cross-border data transfers exist with: transfer mechanisms documented, "
                "adequacy decisions confirmed, standard contractual clauses implemented, and data flow mapping complete? "
                "Return true if cross-border data transfers are properly managed, false otherwise."
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="template_deviation_control",
            llm_prompt=(
                "Does template deviation control exist with: deviation tracking active, "
                "approval requirements enforced, risk assessment for deviations completed, and template integrity maintained? "
                "Return true if template deviation control is effective, false otherwise."
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Supporting deliverables (3-4 points each)
        RubricCriteria(
            name="repeatable_factory_process",
            llm_prompt=(
                "Does repeatable factory process exist with: standardized workflows documented, "
                "process repeatability ensured, quality consistency maintained, and scalability demonstrated? "
                "Return true if repeatable factory process is established, false otherwise."
            ),
            max_score=4.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="stakeholder_coordination_active",
            llm_prompt=(
                "Does active stakeholder coordination exist with: internal alignment maintained, "
                "customer communication effective, legal coordination seamless, and cross-functional collaboration optimized? "
                "Return true if stakeholder coordination is active, false otherwise."
            ),
            max_score=4.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="risk_exposure_minimized",
            llm_prompt=(
                "Does minimized risk exposure exist with: legal risks assessed and mitigated, "
                "commercial risks controlled, operational risks managed, and overall risk profile optimized? "
                "Return true if risk exposure is minimized, false otherwise."
            ),
            max_score=3.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="contract_portfolio_optimization",
            llm_prompt=(
                "Does contract portfolio optimization exist with: contract terms standardized, "
                "portfolio risk balanced, commercial value maximized, and strategic alignment maintained? "
                "Return true if contract portfolio optimization is achieved, false otherwise."
            ),
            max_score=3.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    return Rubric(
        name="enterprise_saas_negotiation_goal_achievement_eval",
        description="Enterprise SaaS MSA/SOW negotiation factory deliverable achievement measurement",
        aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
        criteria=goal_achievement_rubrics,
    )
