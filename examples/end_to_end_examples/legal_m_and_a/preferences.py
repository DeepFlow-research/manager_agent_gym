"""
Legal M&A – Preferences, Evaluators, and Weight Update Requests

- Uses the same schema patterns as existing examples:
  * PreferenceWeights / Preference
  * Evaluator(aggregation=AggregationStrategy.WEIGHTED_AVERAGE, rubrics=[WorkflowRubric...])
  * WorkflowRubric with either llm_prompt or evaluator_function (rule-based)
  * PreferenceWeightUpdateRequest timeline with absolute weights

Exports:
  - create_preferences() -> PreferenceWeights
  - create_mna_preference_update_requests() -> list[PreferenceWeightUpdateRequest]
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
# Rule-based helper functions (Workflow -> score in [0, max])
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
    """Penalize unrealistic cost discrepancies for M&A legal work."""
    expected_min_cost = 75000.0  # Minimum realistic cost
    total_estimated = sum(
        task.estimated_cost for task in workflow.tasks.values() if task.estimated_cost
    )
    total_actual = sum(
        task.actual_cost for task in workflow.tasks.values() if task.actual_cost
    )

    if total_estimated == 0:
        return 0.0
    if total_actual < expected_min_cost:
        return 0.0  # M&A legal work should cost >$75k

    cost_variance = abs(total_actual - total_estimated) / total_estimated
    if cost_variance > 0.4:
        return 0.2
    elif cost_variance > 0.2:
        return 0.6
    else:
        return 1.0


def _ma_adversarial_pressure_score(workflow: Workflow) -> float:
    """Score based on handling M&A adversarial pressure and deal challenges."""
    pressure_indicators = [
        "regulatory challenge",
        "antitrust concern",
        "due diligence issue",
        "valuation dispute",
        "disclosure problem",
        "material adverse change",
        "indemnity dispute",
        "closing condition",
        "third party consent",
        "financing contingency",
        "tax structure challenge",
        "deal breakage",
    ]

    pressure_handled = 0
    for indicator in pressure_indicators:
        for res in workflow.resources.values():
            if indicator.lower() in str(res.content or "").lower():
                if any(
                    resolution.lower() in str(res.content or "").lower()
                    for resolution in [
                        "resolved",
                        "mitigated",
                        "addressed",
                        "negotiated",
                        "waived",
                    ]
                ):
                    pressure_handled += 1
                break

    return min(1.0, pressure_handled / max(1, len(pressure_indicators) * 0.3))


# --- Quality-oriented rules (deterministic) ---
def rule_spa_core_sections_present(workflow: Workflow) -> float:
    """
    Score 0..1 if core drafting/negotiation tasks are complete:
      - 'Drafting – SPA and Schedules' and 'Negotiation & Redlines'
    """
    return 0.5 * _task_completed(workflow, "Drafting – SPA") + 0.5 * _task_completed(
        workflow, "Negotiation & Redlines"
    )


def rule_disclosure_schedules_evidence_linked(workflow: Workflow) -> float:
    """
    Proxy: both 'Legal Diligence – Material Contracts, IP, & Privacy' and 'Diligence Scope & RFI Program' completed.
    """
    return 0.5 * _task_completed(
        workflow, "Material Contracts"
    ) + 0.5 * _task_completed(workflow, "RFI Program")


def rule_funds_flow_and_checklist_ready(workflow: Workflow) -> float:
    """
    Proxy: completion of 'Closing Mechanics & Bring-Down Diligence' indicates funds-flow + closing checklist readiness.
    """
    return _task_completed(workflow, "Closing Mechanics")


# --- Compliance-oriented rules (deterministic) ---
def rule_hsr_submitted(workflow: Workflow) -> float:
    """HSR/CFIUS filing package prepared and filed -> completion of 'Regulatory Filings (HSR/CFIUS)'."""
    return _task_completed(workflow, "Regulatory Filings")


def rule_approvals_and_consents(workflow: Workflow) -> float:
    """
    Board/committee approvals and third-party consents readiness:
      - 'Authority & Governance Readiness' and 'Closing Mechanics' complete.
    """
    return 0.5 * _task_completed(
        workflow, "Authority & Governance"
    ) + 0.5 * _task_completed(workflow, "Closing Mechanics")


# ---------------------------
# LLM Rubrics
# ---------------------------
quality_rubrics: List[WorkflowRubric] = [
    WorkflowRubric(
        name="spa_drafting_completeness_and_consistency",
        llm_prompt=(
            "Assess the Share Purchase Agreement (SPA) draft and redline history for: "
            "(a) comprehensive coverage of core sections (reps/warranties, covenants, conditions, indemnities, termination), "
            "(b) internal consistency of defined terms and cross-references, and "
            "(c) clarity of fallback positions and issue logs. "
            "Cite specific messages/files in the workflow as evidence. Return a numeric score [0, 10]."
        ),
        max_score=10.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    WorkflowRubric(
        name="disclosure_schedules_precision_and_provenance",
        llm_prompt=(
            "Evaluate the precision of disclosure schedules and consent lists: "
            "exceptions are narrow, accurate as-of-date, and each exception references supporting evidence "
            "(e.g., dataroom docs, emails). Check that customer/partner consents are mapped with status and owner. "
            "Return a numeric score [0, 10]."
        ),
        max_score=10.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    WorkflowRubric(
        name="funds_flow_and_closing_set_readiness",
        llm_prompt=(
            "Assess funds-flow statements and closing set readiness: sources/uses tie out, wire instructions validated, "
            "signature packets complete, and bring-down confirmations planned. Return a numeric score [0, 8]."
        ),
        max_score=8.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    # Rule-based seeds for reproducibility and objective checks
    WorkflowRubric(
        name="rule_spa_core_sections_present",
        evaluator_function=rule_spa_core_sections_present,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    WorkflowRubric(
        name="rule_disclosure_schedules_evidence_linked",
        evaluator_function=rule_disclosure_schedules_evidence_linked,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    WorkflowRubric(
        name="rule_funds_flow_and_checklist_ready",
        evaluator_function=rule_funds_flow_and_checklist_ready,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
]

compliance_rubrics: List[WorkflowRubric] = [
    WorkflowRubric(
        name="hsr_submission_quality",
        llm_prompt=(
            "Evaluate HSR submission quality and readiness: inclusion of Item 4(c)/(d) documents, "
            "accuracy of narrative responses, and proper affidavits/certifications. "
            "Assess timing relative to signing/closing plan and any second-request mitigation planning. "
            "Return a numeric score [0, 10]."
        ),
        max_score=10.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    WorkflowRubric(
        name="cfius_screening_and_strategy",
        llm_prompt=(
            "Evaluate CFIUS screening and strategy: identification of foreign ownership/control, "
            "assessment of critical technology/infrastructure/sensitive personal data, and decision memo for filing. "
            "If applicable, assess draft notice quality and Q&A readiness. Return a numeric score [0, 8]."
        ),
        max_score=8.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    WorkflowRubric(
        name="consents_and_change_of_control_management",
        llm_prompt=(
            "Assess management of third‑party consents and change‑of‑control/anti‑assignment provisions: "
            "correct identification, risk ranking, and realistic SLA/owner plans for outreach. "
            "Return a numeric score [0, 8]."
        ),
        max_score=8.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    # Rule-based checks
    WorkflowRubric(
        name="rule_hsr_submitted",
        evaluator_function=rule_hsr_submitted,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    WorkflowRubric(
        name="rule_approvals_and_consents",
        evaluator_function=rule_approvals_and_consents,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    WorkflowRubric(
        name="ma_adversarial_scenarios",
        llm_prompt=(
            """Evaluate handling of M&A adversarial scenarios and deal challenges:
            - shows preparation for regulatory challenges and antitrust concerns
            - demonstrates response to due diligence issues and valuation disputes
            - shows handling of disclosure problems and material adverse changes
            - demonstrates preparation for indemnity disputes and closing condition challenges
            - shows deal breakage risk management and financing contingency resolution
            Score 0 if no adversarial scenarios addressed. Return score [0, 10]."""
        ),
        max_score=10.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    WorkflowRubric(
        name="cost_realism_validation",
        evaluator_function=_validate_cost_realism,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
]


# ---------------------------
# Preferences + Evaluators
# ---------------------------
def create_preferences() -> PreferenceWeights:
    """Initial stakeholder weights for Legal M&A (t=0 snapshot)."""
    return PreferenceWeights(
        preferences=[
            Preference(
                name="quality",
                weight=0.3,
                evaluator=Evaluator(
                    name="quality_eval",
                    description="Evaluates drafting completeness, schedules precision, and closing readiness.",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=quality_rubrics,
                ),
            ),
            Preference(
                name="compliance",
                weight=0.2,
                evaluator=Evaluator(
                    name="compliance_eval",
                    description="Evaluates HSR/CFIUS posture and third‑party consents management.",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=compliance_rubrics,
                ),
            ),
        ]
    )


# ---------------------------
# Weight Update Requests (timeline)
# ---------------------------
def create_mna_preference_update_requests() -> list[PreferenceWeightUpdateRequest]:
    """Stakeholder's explicit weight changes over time (absolute, normalized)."""
    timeline: dict[int, PreferenceWeights] = {
        0: PreferenceWeights(
            preferences=[
                Preference(name="quality", weight=0.3),
                Preference(name="compliance", weight=0.2),
                Preference(name="speed", weight=0.5),
            ]
        ),
        35: PreferenceWeights(
            preferences=[
                Preference(name="quality", weight=0.6),
                Preference(name="compliance", weight=0.2),
                Preference(name="speed", weight=0.2),
            ]
        ),
        70: PreferenceWeights(
            preferences=[
                Preference(name="quality", weight=0.3),
                Preference(name="compliance", weight=0.6),
                Preference(name="speed", weight=0.1),
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
    """Create goal achievement evaluator for mid-market tech acquisition legal M&A process."""
    goal_achievement_rubrics = [
        # Critical transaction deliverables (absolutely must have for signing/closing)
        WorkflowRubric(
            name="spa_execution_ready_draft",
            llm_prompt=(
                "Does execution-ready SPA draft exist with: complete core sections (purchase price, representations, covenants), "
                "coherent fallback ladders documented, redline history with change rationales, and legal review completed? "
                "Return true if SPA is execution-ready and comprehensive, false otherwise."
            ),
            max_score=18.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="disclosure_schedules_evidence_linked",
            llm_prompt=(
                "Do evidence-linked disclosure schedules exist with: precise and current disclosure information, "
                "supporting evidence cited from data room, disclosure accuracy validated, and legal completeness confirmed? "
                "Return true if disclosure schedules are evidence-linked and complete, false otherwise."
            ),
            max_score=15.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="hsr_cfius_filings_submitted",
            llm_prompt=(
                "Do submitted HSR/CFIUS filings exist with: HSR submission prepared and filed, "
                "CFIUS notice submitted if required, waiting-period tracking active, and regulatory compliance confirmed? "
                "Return true if HSR/CFIUS filings are submitted and compliant, false otherwise."
            ),
            max_score=15.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="funds_flow_closing_set_ready",
            llm_prompt=(
                "Does ready funds flow and closing set exist with: sources/uses documented, "
                "signature packets prepared, complete closing set assembled, and bring-down plan established? "
                "Return true if funds flow and closing set are execution-ready, false otherwise."
            ),
            max_score=12.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Major transaction coordination deliverables (8-10 points each)
        WorkflowRubric(
            name="third_party_consents_managed",
            llm_prompt=(
                "Do managed third-party consents exist with: consent requirements identified, "
                "consent requests submitted, customer relationship preservation strategies active, and consent tracking operational? "
                "Return true if third-party consents are actively managed, false otherwise."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="due_diligence_artifacts_organized",
            llm_prompt=(
                "Do organized due diligence artifacts exist with: data room structure maintained, "
                "diligence findings documented, legal/regulatory/IP/privacy review completed, and artifact traceability established? "
                "Return true if due diligence artifacts are organized and accessible, false otherwise."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="governance_approvals_secured",
            llm_prompt=(
                "Do secured governance approvals exist with: board/committee approvals obtained, "
                "governance artifacts captured, shareholder approvals secured if required, and authorization documentation complete? "
                "Return true if governance approvals are secured, false otherwise."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="risk_register_raid_log_maintained",
            llm_prompt=(
                "Do maintained risk register and RAID log exist with: transaction risks identified, "
                "mitigation strategies documented, weekly status cadence operational, and risk monitoring active? "
                "Return true if risk register and RAID log are maintained, false otherwise."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="redline_negotiation_history",
            llm_prompt=(
                "Does redline negotiation history exist with: negotiation progression documented, "
                "decision rationales captured, fallback positions established, and negotiation strategy coherent? "
                "Return true if redline negotiation history is comprehensive, false otherwise."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Important supporting deliverables (5-7 points each)
        WorkflowRubric(
            name="deal_memo_objectives_documented",
            llm_prompt=(
                "Do documented deal memo and objectives exist with: enterprise value defined, "
                "consideration mix established, transaction structure clear, and deal rationale documented? "
                "Return true if deal memo and objectives are documented, false otherwise."
            ),
            max_score=7.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="tax_structuring_analysis",
            llm_prompt=(
                "Does tax structuring analysis exist with: tax-efficient structure designed, "
                "tax opinions secured, structuring alternatives evaluated, and tax implications documented? "
                "Return true if tax structuring analysis is complete, false otherwise."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="reps_warranties_insurance",
            llm_prompt=(
                "Does reps and warranties insurance exist with: RWI policy negotiated, "
                "coverage terms established, premium arrangements confirmed, and insurance protection operational? "
                "Return true if RWI insurance is secured, false otherwise."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="employment_matters_review",
            llm_prompt=(
                "Does employment matters review exist with: key employee retention addressed, "
                "employment agreements reviewed, compensation arrangements documented, and HR integration planned? "
                "Return true if employment matters review is complete, false otherwise."
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="ip_portfolio_analysis",
            llm_prompt=(
                "Do the resources published in the workflow suggest no signs of application deficiencies or regulatory concerns raised? "
                "Return true if there are no such issues, False otherwise."
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Supporting deliverables (3-4 points each)
        WorkflowRubric(
            name="antitrust_clearance_strategy",
            llm_prompt=(
                "Does antitrust clearance strategy exist with: antitrust risk assessment completed, "
                "clearance timeline established, regulatory strategy documented, and competition law compliance confirmed? "
                "Return true if antitrust clearance strategy is established, false otherwise."
            ),
            max_score=4.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="escrow_holdback_arrangements",
            llm_prompt=(
                "Do escrow and holdback arrangements exist with: escrow terms negotiated, "
                "holdback mechanisms established, indemnification procedures documented, and post-closing adjustments planned? "
                "Return true if escrow and holdback arrangements are established, false otherwise."
            ),
            max_score=4.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="data_room_security_compliance",
            llm_prompt=(
                "Does data room security compliance exist with: secure data room operational, "
                "access controls implemented, audit trail maintained, and confidentiality protections active? "
                "Return true if data room security compliance is maintained, false otherwise."
            ),
            max_score=3.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="closing_conditions_checklist",
            llm_prompt=(
                "Does closing conditions checklist exist with: all closing conditions identified, "
                "condition satisfaction tracked, closing readiness confirmed, and no gating items outstanding? "
                "Return true if closing conditions checklist is complete, false otherwise."
            ),
            max_score=3.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    return Evaluator(
        name="legal_mna_goal_achievement_eval",
        description="Legal M&A mid-market tech acquisition transaction deliverable achievement measurement",
        aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
        rubrics=goal_achievement_rubrics,
    )
