"""
Global Workforce Restructuring / RIF — Preferences & Evaluators

Preferences (5):
  - compliance            : jurisdictional obligations (WARN/mini‑WARN, EU collective consultation/authority notices, UK s.188),
                            sequencing (consultation before notice), and statutory overlays
  - fairness_defensibility: selection criteria integrity, calibration, adverse‑impact analysis & remediation, documentation
  - employee_experience   : humane communications, support (outplacement/EAP), accuracy of pay/benefits
  - timeline_certainty    : milestone discipline (consultation windows, filing deadlines, day‑of execution readiness)
  - documentation_quality : decision logs, minutes, approvals, and audit‑ready recordkeeping
"""

from typing import List, Optional
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
from manager_agent_gym.schemas.domain import Workflow, TaskStatus


# -------------
# Helpers
# -------------
def _task_by_name(workflow: Workflow, name_contains: str) -> Optional[object]:
    for t in workflow.tasks.values():
        if name_contains.lower() in (t.name or "").lower():
            return t
    return None


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


# -------------
# Cost Validation Helpers
# -------------
def _validate_cost_realism(workflow: Workflow, context) -> float:
    """Penalize unrealistic cost discrepancies between estimates and actuals."""
    expected_min_cost = 50000.0  # Minimum realistic cost
    total_estimated = sum(
        task.estimated_cost for task in workflow.tasks.values() if task.estimated_cost
    )
    total_actual = sum(
        task.actual_cost for task in workflow.tasks.values() if task.actual_cost
    )

    if total_estimated == 0:
        return 0.0  # No cost planning penalty

    if total_actual < expected_min_cost:
        return 0.0  # Unrealistic low actual costs penalty

    cost_variance = abs(total_actual - total_estimated) / total_estimated
    if cost_variance > 0.5:  # >50% cost variance penalty
        return 0.2
    elif cost_variance > 0.2:  # >20% cost variance partial penalty
        return 0.6
    else:
        return 1.0


def _require_external_validation(
    workflow: Workflow, validation_keywords: List[str]
) -> float:
    """Require evidence of external validation, not just internal completion."""
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
                for keyword in ["approved", "validated", "certified", "confirmed"]
            ):
                validation_evidence += 1

    return min(
        1.0, validation_evidence / max(1, total_tasks * 0.3)
    )  # Require 30% external validation


def _adversarial_pressure_score(workflow: Workflow) -> float:
    """Score based on handling adversarial stakeholder pressure and challenges."""
    pressure_indicators = [
        "union opposition",
        "employee resistance",
        "regulatory pushback",
        "legal challenge",
        "media scrutiny",
        "works council disagreement",
        "regulatory investigation",
        "whistleblower",
        "adverse publicity",
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
                    ]
                ):
                    pressure_handled += 1
                break

    return min(
        1.0, pressure_handled / max(1, len(pressure_indicators) * 0.4)
    )  # Expect 40% pressure scenarios


# -------------
# Deterministic Rules
# -------------
# Compliance
def rule_consultation_before_notice(workflow: Workflow) -> float:
    """Require Works Council/Union Consultation to be completed before 'Notice & Document Packages' are treated as complete."""
    wc = _task_by_name(workflow, "Works Council/Union Consultation")
    notices = _task_by_name(workflow, "Notice & Document Packages")
    if not wc or not notices:
        return 0.0
    wc_done = _task_completed(workflow, "Works Council/Union Consultation")
    notices_done = _task_completed(workflow, "Notice & Document Packages")

    # NEW: Require external validation and adversarial pressure handling
    external_validation = _require_external_validation(
        workflow, ["consultation", "works council", "union"]
    )
    adversarial_score = _adversarial_pressure_score(workflow)

    base_score = 1.0 if (wc_done >= 1.0 and notices_done >= 1.0) else 0.0
    return base_score * 0.4 + external_validation * 0.3 + adversarial_score * 0.3


def rule_warn_matrix_and_filings(workflow: Workflow) -> float:
    """US WARN/mini‑WARN matrix prepared and regulator filings submitted."""
    matrix_ready = _task_completed(workflow, "US WARN")
    filings_done = _task_completed(workflow, "Regulator Filings & Confirmations")
    # allow partial credit if filings done but matrix not explicitly found
    return 0.5 * matrix_ready + 0.5 * filings_done


def rule_uk_eu_consult_notifications(workflow: Workflow) -> float:
    """EU/UK collective consultation and authority notices tracked."""
    eu = _task_completed(workflow, "EU Collective Redundancies")
    uk = _task_completed(workflow, "UK Collective Consultation")
    filings = _task_completed(workflow, "Regulator Filings & Confirmations")
    return 0.4 * eu + 0.4 * uk + 0.2 * filings


# Fairness/Defensibility
def rule_selection_docs_complete(workflow: Workflow) -> float:
    return _task_completed(workflow, "Selection Decisions & Documentation")


def rule_adverse_impact_tested(workflow: Workflow) -> float:
    return 1.0 if _pct_tasks_completed(workflow, "Adverse‑Impact") >= 1.0 else 0.0


# Employee Experience
def rule_comms_playbooks_ready(workflow: Workflow) -> float:
    return _task_completed(workflow, "Communications & Day‑Of Playbooks")


def rule_payroll_benefits_ready(workflow: Workflow) -> float:
    return _task_completed(workflow, "Payroll, Benefits & HRIS Updates")


# Timeline Certainty
def rule_timeline_milestones_locked(workflow: Workflow) -> float:
    wc = _task_completed(workflow, "Works Council/Union Consultation")
    notices = _task_completed(workflow, "Notice & Document Packages")
    execution_ctrl = _task_completed(workflow, "Execution Control Room")
    return 0.34 * wc + 0.33 * notices + 0.33 * execution_ctrl


# Documentation Quality
def rule_audit_and_records(workflow: Workflow) -> float:
    # credit for Documentation constraint outcomes: use Post‑Action Audit & Lessons Learned as proxy
    base_completion = _task_completed(workflow, "Post‑Action Audit & Lessons Learned")

    external_validation = _require_external_validation(
        workflow, ["audit", "legal review", "compliance"]
    )

    return base_completion * 0.4 + external_validation * 0.6


# -------------
# LLM Rubrics
# -------------
compliance_rubrics: List[RubricCriteria] = [
    RubricCriteria(
        name="jurisdictional_obligations_and_sequencing",
        llm_prompt=(
            "Evaluate compliance posture of the RIF: Does the plan respect EU collective redundancy rules and UK s.188 "
            "(consultation and authority notifications), and US WARN/mini‑WARN deadlines? "
            "Check that consultation occurs before issuing notices where required, and that statutory severance/benefits "
            "overlays are applied. Return [0, 10]."
        ),
        max_score=10.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    RubricCriteria(
        name="rule_consultation_before_notice",
        evaluator_function=rule_consultation_before_notice,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    RubricCriteria(
        name="rule_warn_matrix_and_filings",
        evaluator_function=rule_warn_matrix_and_filings,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    RubricCriteria(
        name="rule_uk_eu_consult_notifications",
        evaluator_function=rule_uk_eu_consult_notifications,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
]

fairness_rubrics: List[RubricCriteria] = [
    RubricCriteria(
        name="selection_defensibility",
        llm_prompt=(
            "RIGOROUSLY assess selection fairness and defensibility:\n"
            "- has objective, measurable selection criteria (not subjective)\n"
            "- shows statistical validation of calibration process across managers\n"
            "- demonstrates adverse-impact analysis with <4/5ths rule compliance OR remediation\n"
            "- shows external legal review/validation (not just internal documentation)\n"
            "- demonstrates union/works council agreement or formal dispute resolution\n"
            "PENALTY: Subtract 3 points for each missing requirement. Score harshly if only documentation without evidence. Return [0, 10]."
        ),
        max_score=10.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    RubricCriteria(
        name="rule_selection_docs_complete",
        evaluator_function=rule_selection_docs_complete,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    RubricCriteria(
        name="rule_adverse_impact_tested",
        evaluator_function=rule_adverse_impact_tested,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    RubricCriteria(
        name="adversarial_resistance_handling",
        llm_prompt=(
            "Evaluate adversarial stakeholder resistance handling:\n"
            "- shows evidence of union opposition/disagreement and resolution strategy\n"
            "- demonstrates handling of employee resistance or negative reactions\n"
            "- shows preparation for potential legal challenges or whistleblower scenarios\n"
            "- demonstrates media/PR strategy for negative publicity\n"
            "- shows regulatory challenge preparation and response\n"
            "Score 0 if no adversarial scenarios addressed. Partial credit only with evidence of resistance AND resolution. Return [0, 10]."
        ),
        max_score=10.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
]

employee_exp_rubrics: List[RubricCriteria] = [
    RubricCriteria(
        name="humane_communications_and_support",
        llm_prompt=(
            "Evaluate the employee experience: clarity and empathy of manager scripts and letters, availability of "
            "outplacement/EAP support, and respect in day‑of sequencing. Return [0, 10]."
        ),
        max_score=10.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    RubricCriteria(
        name="rule_comms_playbooks_ready",
        evaluator_function=rule_comms_playbooks_ready,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    RubricCriteria(
        name="rule_payroll_benefits_ready",
        evaluator_function=rule_payroll_benefits_ready,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
]

timeline_rubrics: List[RubricCriteria] = [
    RubricCriteria(
        name="milestone_discipline",
        llm_prompt=(
            "Evaluate timeline discipline:\n"
            "- shows realistic consultation windows (minimum 30 days EU, 45 days UK)\n"
            "- demonstrates buffer time for regulatory delays/pushback\n"
            "- shows contingency plans for union resistance or legal challenges\n"
            "- demonstrates cross-jurisdictional coordination with time zone considerations\n"
            "- MUST show evidence of stress-testing timeline under adverse scenarios\n"
            "PENALTY: Deduct 2 points for each missing element. No credit for generic timelines. Return [0, 10]."
        ),
        max_score=10.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    RubricCriteria(
        name="rule_timeline_milestones_locked",
        evaluator_function=rule_timeline_milestones_locked,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
]

docs_rubrics: List[RubricCriteria] = [
    RubricCriteria(
        name="audit_trail_and_recordkeeping",
        llm_prompt=(
            "Assess documentation/audit trail: decision logs, consultation minutes and responses, notice copies, "
            "authority filings, and post‑action audit completeness. Return [0, 10]."
        ),
        max_score=10.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    RubricCriteria(
        name="rule_audit_and_records",
        evaluator_function=rule_audit_and_records,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
]


# -------------
# Preferences + Evaluators
# -------------
def create_preferences() -> PreferenceSnapshot:
    """Initial stakeholder weights for a global RIF (t=0 snapshot)."""
    return PreferenceSnapshot(
        preferences=[
            Preference(
                name="compliance",
                weight=0.35,
                evaluator=Rubric(
                    name="compliance_eval",
                    description="Jurisdictional obligations & sequencing across EU/UK/US; statutory overlays.",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    criteria=compliance_rubrics,
                ),
            ),
            Preference(
                name="fairness_defensibility",
                weight=0.25,
                evaluator=Rubric(
                    name="fairness_eval",
                    description="Selection criteria integrity, calibration, adverse‑impact testing and remediation.",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    criteria=fairness_rubrics,
                ),
            ),
            Preference(
                name="employee_experience",
                weight=0.2,
                evaluator=Rubric(
                    name="employee_exp_eval",
                    description="Humane communications and accurate pay/benefits execution.",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    criteria=employee_exp_rubrics,
                ),
            ),
            Preference(
                name="timeline_certainty",
                weight=0.1,
                evaluator=Rubric(
                    name="timeline_eval",
                    description="Milestone discipline and cross‑jurisdictional sequencing certainty.",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    criteria=timeline_rubrics,
                ),
            ),
            Preference(
                name="documentation_quality",
                weight=0.1,
                evaluator=Rubric(
                    name="docs_eval",
                    description="Audit‑ready recordkeeping and post‑action audit completeness.",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    criteria=docs_rubrics,
                ),
            ),
        ]
    )


# -------------
# Weight Update Requests (timeline)
# -------------
def create_preference_update_requests() -> list[PreferenceWeightUpdateRequest]:
    """Stakeholder's weight changes over time (absolute, normalized)."""
    timeline: dict[int, PreferenceSnapshot] = {
        # Early: align criteria and jurisdictional plan; protect compliance & fairness
        0: PreferenceSnapshot(
            preferences=[
                Preference(name="compliance", weight=0.35),
                Preference(name="fairness_defensibility", weight=0.3),
                Preference(name="employee_experience", weight=0.15),
                Preference(name="timeline_certainty", weight=0.1),
                Preference(name="documentation_quality", weight=0.1),
            ]
        ),
        # Mid: consultation underway, selections frozen; emphasize employee experience and documentation hygiene
        18: PreferenceSnapshot(
            preferences=[
                Preference(name="compliance", weight=0.3),
                Preference(name="fairness_defensibility", weight=0.25),
                Preference(name="employee_experience", weight=0.2),
                Preference(name="timeline_certainty", weight=0.15),
                Preference(name="documentation_quality", weight=0.1),
            ]
        ),
        # Late: protect execution day, filings, and post‑action audit
        26: PreferenceSnapshot(
            preferences=[
                Preference(name="compliance", weight=0.25),
                Preference(name="fairness_defensibility", weight=0.2),
                Preference(name="employee_experience", weight=0.25),
                Preference(name="timeline_certainty", weight=0.15),
                Preference(name="documentation_quality", weight=0.15),
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
    """Create goal achievement evaluator for global workforce restructuring/RIF program."""
    goal_achievement_rubrics = [
        # Critical legal compliance and governance deliverables (must have for defensible restructuring)
        RubricCriteria(
            name="legal_compliance_multijiurisdictional",
            llm_prompt=(
                "Does multi-jurisdictional legal compliance exist with: US WARN/mini-WARN compliance confirmed, "
                "EU collective consultation completed, UK TULRCA s.188 requirements met, FR CSE obligations satisfied, "
                "and all jurisdictional requirements addressed? "
                "Return true if legal compliance is multi-jurisdictional and complete, false otherwise."
            ),
            max_score=20.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="selection_criteria_defensible_documented",
            llm_prompt=(
                "Do documented defensible selection criteria exist with: objective selection criteria established, "
                "adverse-impact analysis performed, bias assessment completed, and legal defensibility confirmed? "
                "Return true if selection criteria are defensible and documented, false otherwise."
            ),
            max_score=18.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="privilege_strategy_confidentiality_maintained",
            llm_prompt=(
                "Does maintained privilege strategy and confidentiality exist with: attorney-client privilege preserved, "
                "work product protection maintained, confidential communications secured, and legal strategy protected? "
                "Return true if privilege strategy and confidentiality are maintained, false otherwise."
            ),
            max_score=15.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="governance_approval_accountability",
            llm_prompt=(
                "Does governance approval and accountability exist with: executive decision-making documented, "
                "board approval secured where required, accountability trails established, and governance compliance confirmed? "
                "Return true if governance approval and accountability are established, false otherwise."
            ),
            max_score=12.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Major operational and human impact deliverables (8-10 points each)
        RubricCriteria(
            name="redeployment_mitigation_efforts_documented",
            llm_prompt=(
                "Do documented redeployment and mitigation efforts exist with: redeployment opportunities explored, "
                "alternative placement attempts documented, mitigation strategies implemented, and effort comprehensiveness demonstrated? "
                "Return true if redeployment and mitigation efforts are documented, false otherwise."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="employee_communications_executed",
            llm_prompt=(
                "Does executed employee communications exist with: employee notification strategy implemented, "
                "communication timing appropriate, messaging consistent and compassionate, and employee support provided? "
                "Return true if employee communications are executed effectively, false otherwise."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="benefits_payroll_transitions_complete",
            llm_prompt=(
                "Do complete benefits and payroll transitions exist with: severance packages processed, "
                "benefits transitions managed, COBRA/healthcare continuity arranged, and payroll changes executed? "
                "Return true if benefits and payroll transitions are complete, false otherwise."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="regulator_filings_notifications_timely",
            llm_prompt=(
                "Do timely regulator filings and notifications exist with: WARN notices filed, "
                "government notifications submitted, regulatory compliance maintained, and filing deadlines met? "
                "Return true if regulator filings and notifications are timely, false otherwise."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="post_action_audit_lessons_learned",
            llm_prompt=(
                "Do post-action audit and lessons learned exist with: implementation review completed, "
                "lessons learned documented, process improvements identified, and audit recommendations captured? "
                "Return true if post-action audit and lessons learned are complete, false otherwise."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Important supporting deliverables (5-7 points each)
        RubricCriteria(
            name="workforce_planning_analytics",
            llm_prompt=(
                "Does workforce planning analytics exist with: headcount analysis completed, "
                "skills gap assessment performed, organizational design optimized, and workforce planning strategic? "
                "Return true if workforce planning analytics are comprehensive, false otherwise."
            ),
            max_score=7.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="employee_support_services",
            llm_prompt=(
                "Do employee support services exist with: outplacement services provided, "
                "career transition support available, counseling resources offered, and employee assistance comprehensive? "
                "Return true if employee support services are adequate, false otherwise."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="stakeholder_communication_management",
            llm_prompt=(
                "Does stakeholder communication management exist with: internal stakeholder communication coordinated, "
                "external stakeholder management active, investor relations maintained, and communication consistency achieved? "
                "Return true if stakeholder communication management is effective, false otherwise."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="legal_risk_mitigation",
            llm_prompt=(
                "Does legal risk mitigation exist with: legal risks identified and assessed, "
                "risk mitigation strategies implemented, legal exposure minimized, and defensive posture strengthened? "
                "Return true if legal risk mitigation is effective, false otherwise."
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="union_works_council_engagement",
            llm_prompt=(
                "Does union and works council engagement exist with: union consultation conducted, "
                "works council engagement completed, collective bargaining obligations met, and labor relations managed? "
                "Return true if union and works council engagement is proper, false otherwise."
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Supporting deliverables (3-4 points each)
        RubricCriteria(
            name="documentation_version_control",
            llm_prompt=(
                "Does documentation version control exist with: document management systematic, "
                "version control maintained, approval workflows established, and documentation integrity preserved? "
                "Return true if documentation version control is established, false otherwise."
            ),
            max_score=4.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="change_management_support",
            llm_prompt=(
                "Does change management support exist with: change management strategy implemented, "
                "transition support provided, organizational change facilitated, and change adaptation supported? "
                "Return true if change management support is effective, false otherwise."
            ),
            max_score=4.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="business_continuity_maintained",
            llm_prompt=(
                "Does maintained business continuity exist with: operational continuity preserved, "
                "business disruption minimized, critical functions maintained, and service delivery sustained? "
                "Return true if business continuity is maintained, false otherwise."
            ),
            max_score=3.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="cost_benefit_analysis_validated",
            llm_prompt=(
                "Does validated cost-benefit analysis exist with: financial analysis completed, "
                "cost savings quantified, business case validated, and ROI demonstration provided? "
                "Return true if cost-benefit analysis is validated, false otherwise."
            ),
            max_score=3.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    return Rubric(
        name="mnc_workforce_restructuring_goal_achievement_eval",
        description="Global workforce restructuring/RIF program deliverable achievement measurement",
        aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
        criteria=goal_achievement_rubrics,
    )
