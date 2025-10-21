"""
US Co‑op Bank — Internal Risk & Solvency Assessment (ORSA‑style) Preferences

Preferences selected (4):
  - capital_adequacy  : sufficiency vs NCUA RBC/CCULR with management buffers and scenario coverage
  - liquidity_resilience: liquidity survival horizon and contingency funding plan quality
  - model_risk_hygiene : SR 11‑7 inventory/validation/monitoring and effective challenge
  - governance_quality : board oversight, documentation, and auditability

Schema parity:
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
    """Penalize unrealistic cost discrepancies for ORSA assessments."""
    expected_min_cost = 80000.0  # Minimum realistic cost
    total_estimated = sum(
        task.estimated_cost for task in workflow.tasks.values() if task.estimated_cost
    )
    total_actual = sum(
        task.actual_cost for task in workflow.tasks.values() if task.actual_cost
    )

    if total_estimated == 0:
        return 0.0
    if total_actual < expected_min_cost:
        return 0.0  # ORSA assessments should cost >$80k

    cost_variance = abs(total_actual - total_estimated) / total_estimated
    if cost_variance > 0.3:
        return 0.2
    elif cost_variance > 0.15:
        return 0.6
    else:
        return 1.0


def _orsa_adversarial_pressure_score(workflow: Workflow) -> float:
    """Score based on handling ORSA adversarial pressure and regulatory challenges."""
    pressure_indicators = [
        "regulator challenge",
        "model criticism",
        "stress test failure",
        "capital adequacy concern",
        "audit finding",
        "board challenge",
        "methodology dispute",
        "data quality issue",
        "assumption challenge",
        "scenario inadequacy",
        "governance gap",
        "validation failure",
    ]

    pressure_handled = 0
    for indicator in pressure_indicators:
        for res in workflow.resources.values():
            if indicator.lower() in str(res.content or "").lower():
                if any(
                    resolution.lower() in str(res.content or "").lower()
                    for resolution in [
                        "addressed",
                        "resolved",
                        "validated",
                        "improved",
                        "corrected",
                    ]
                ):
                    pressure_handled += 1
                break

    return min(1.0, pressure_handled / max(1, len(pressure_indicators) * 0.3))


# CAPITAL ADEQUACY rules
def rule_capital_policy_ready(workflow: Workflow) -> float:
    """Capital Adequacy & Buffer Policy task completed."""
    return _task_completed(workflow, "Capital Adequacy & Buffer Policy")


def rule_scenario_suite_built(workflow: Workflow) -> float:
    """Scenario Suite Design task completed."""
    return _task_completed(workflow, "Scenario Suite Design")


# LIQUIDITY rules
def rule_liquidity_cfp_ready(workflow: Workflow) -> float:
    """Liquidity Profile & Contingency Funding Plan task completed."""
    return _task_completed(workflow, "Liquidity Profile & Contingency Funding Plan")


# MODEL RISK rules
def rule_model_inventory_done(workflow: Workflow) -> float:
    return _task_completed(workflow, "Data & Model Inventory")


def rule_validation_executed(workflow: Workflow) -> float:
    return _task_completed(workflow, "Model Validation & Use‑Test")


# GOVERNANCE rules
def rule_board_approved(workflow: Workflow) -> float:
    return _task_completed(workflow, "Board Review & Approval")


def rule_audit_trail_verified(workflow: Workflow) -> float:
    return _task_completed(workflow, "Control Testing & Audit Trail")


# ---------------------------
# LLM Rubrics
# ---------------------------
capital_rubrics: List[RubricCriteria] = [
    RubricCriteria(
        name="capital_buffers_vs_requirements",
        llm_prompt=(
            "Evaluate capital adequacy: Does the capital plan meet applicable requirements for a US credit union "
            "(NCUA RBC or CCULR) and articulate a justified management buffer? "
            "Check that scenario results (credit losses, IRRBB/NII/EVE impacts, operational add‑ons) are reconciled "
            "to capital decisions and dividend/member distribution constraints. Return a score [0, 10]."
        ),
        max_score=10.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    RubricCriteria(
        name="loss_estimation_coherence",
        llm_prompt=(
            "Assess coherence of loss and earnings projections feeding capital: consistency of PD/LGD/EAD (or proxies), "
            "ALM/IRRBB impacts, overlays/qualitative adjustments, and documentation of assumptions/limitations. "
            "Return a score [0, 8]."
        ),
        max_score=8.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    RubricCriteria(
        name="rule_capital_policy_ready",
        evaluator_function=rule_capital_policy_ready,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    RubricCriteria(
        name="rule_scenario_suite_built",
        evaluator_function=rule_scenario_suite_built,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
]

liquidity_rubrics: List[RubricCriteria] = [
    RubricCriteria(
        name="contingency_funding_plan_quality",
        llm_prompt=(
            "Evaluate the contingency funding plan (CFP): stress scenarios, trigger framework, playbooks, "
            "and access to contingent liquidity sources (e.g., Discount Window/CLF) as appropriate. "
            "Return a score [0, 10]."
        ),
        max_score=10.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    RubricCriteria(
        name="liquidity_survival_horizon",
        llm_prompt=(
            "Assess survival horizon analysis quality and assumptions (deposit outflows, secured/unsecured market access), "
            "and linkage to management actions. Return a score [0, 8]."
        ),
        max_score=8.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    RubricCriteria(
        name="rule_liquidity_cfp_ready",
        evaluator_function=rule_liquidity_cfp_ready,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
]

model_risk_rubrics: List[RubricCriteria] = [
    RubricCriteria(
        name="sr11_7_controls_completeness",
        llm_prompt=(
            "Evaluate SR 11‑7 compliance: inventory coverage, materiality ratings, validation scope/results, "
            "conceptual soundness and outcomes analysis, ongoing monitoring, and effective challenge documentation. "
            "Return a score [0, 10]."
        ),
        max_score=10.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    RubricCriteria(
        name="rule_model_inventory_done",
        evaluator_function=rule_model_inventory_done,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    RubricCriteria(
        name="rule_validation_executed",
        evaluator_function=rule_validation_executed,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
]

governance_rubrics: List[RubricCriteria] = [
    RubricCriteria(
        name="board_oversight_and_decisions",
        llm_prompt=(
            "Evaluate Board/Risk Committee oversight quality: evidence of challenge, decisions on risk appetite and "
            "capital buffers, and documented approvals. Return a score [0, 8]."
        ),
        max_score=8.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    RubricCriteria(
        name="documentation_reproducibility_audit_trail",
        llm_prompt=(
            "Assess documentation quality and reproducibility: versioned artifacts, evidence index, "
            "and audit trail sufficient for examination. Return a score [0, 8]."
        ),
        max_score=8.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    RubricCriteria(
        name="rule_board_approved",
        evaluator_function=rule_board_approved,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    RubricCriteria(
        name="rule_audit_trail_verified",
        evaluator_function=rule_audit_trail_verified,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    RubricCriteria(
        name="orsa_adversarial_scenarios",
        llm_prompt=(
            """Evaluate handling of ORSA adversarial scenarios and regulatory challenges:
            - shows preparation for regulator challenges and model criticism
            - demonstrates response to stress test failures and capital adequacy concerns
            - shows handling of audit findings and board challenges
            - demonstrates preparation for methodology disputes and data quality issues
            - shows validation failure recovery and governance gap resolution
            Score 0 if no adversarial scenarios addressed. Return score [0, 10]."""
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


# ---------------------------
# Preferences + Evaluators
# ---------------------------
def create_preferences() -> PreferenceSnapshot:
    """Initial stakeholder evaluation preferences for the ORSA‑style assessment (t=0 snapshot)."""
    return PreferenceSnapshot(
        preferences=[
            Preference(
                name="capital_adequacy",
                weight=0.35,
                evaluator=Rubric(
                    name="capital_eval",
                    description="Capital adequacy vs RBC/CCULR, buffers, scenario coherence.",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    criteria=capital_rubrics,
                ),
            ),
            Preference(
                name="liquidity_resilience",
                weight=0.25,
                evaluator=Rubric(
                    name="liquidity_eval",
                    description="Liquidity survival horizon and CFP quality.",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    criteria=liquidity_rubrics,
                ),
            ),
            Preference(
                name="model_risk_hygiene",
                weight=0.2,
                evaluator=Rubric(
                    name="model_risk_eval",
                    description="SR 11‑7 inventory, validation, monitoring, and challenge documentation.",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    criteria=model_risk_rubrics,
                ),
            ),
            Preference(
                name="governance_quality",
                weight=0.2,
                evaluator=Rubric(
                    name="governance_eval",
                    description="Board oversight, approvals, documentation, and audit trail.",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    criteria=governance_rubrics,
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
        0: PreferenceSnapshot(
            preferences=[
                Preference(
                    name="capital_adequacy",
                    weight=0.35,
                    evaluator=Rubric(
                        name="capital_eval",
                        description="c",
                        aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                        criteria=capital_rubrics,
                    ),
                ),
                Preference(
                    name="liquidity_resilience",
                    weight=0.25,
                    evaluator=Rubric(
                        name="liquidity_eval",
                        description="l",
                        aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                        criteria=liquidity_rubrics,
                    ),
                ),
                Preference(
                    name="model_risk_hygiene",
                    weight=0.2,
                    evaluator=Rubric(
                        name="model_risk_eval",
                        description="m",
                        aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                        criteria=model_risk_rubrics,
                    ),
                ),
                Preference(
                    name="governance_quality",
                    weight=0.2,
                    evaluator=Rubric(
                        name="governance_eval",
                        description="g",
                        aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                        criteria=governance_rubrics,
                    ),
                ),
            ]
        ),
        20: PreferenceSnapshot(
            preferences=[
                Preference(
                    name="capital_adequacy",
                    weight=0.4,
                    evaluator=Rubric(
                        name="capital_eval",
                        description="c",
                        aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                        criteria=capital_rubrics,
                    ),
                ),
                Preference(
                    name="liquidity_resilience",
                    weight=0.3,
                    evaluator=Rubric(
                        name="liquidity_eval",
                        description="l",
                        aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                        criteria=liquidity_rubrics,
                    ),
                ),
                Preference(
                    name="model_risk_hygiene",
                    weight=0.2,
                    evaluator=Rubric(
                        name="model_risk_eval",
                        description="m",
                        aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                        criteria=model_risk_rubrics,
                    ),
                ),
                Preference(
                    name="governance_quality",
                    weight=0.1,
                    evaluator=Rubric(
                        name="governance_eval",
                        description="g",
                        aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                        criteria=governance_rubrics,
                    ),
                ),
            ]
        ),
        40: PreferenceSnapshot(
            preferences=[
                Preference(
                    name="capital_adequacy",
                    weight=0.25,
                    evaluator=Rubric(
                        name="capital_eval",
                        description="c",
                        aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                        criteria=capital_rubrics,
                    ),
                ),
                Preference(
                    name="liquidity_resilience",
                    weight=0.2,
                    evaluator=Rubric(
                        name="liquidity_eval",
                        description="l",
                        aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                        criteria=liquidity_rubrics,
                    ),
                ),
                Preference(
                    name="model_risk_hygiene",
                    weight=0.2,
                    evaluator=Rubric(
                        name="model_risk_eval",
                        description="m",
                        aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                        criteria=model_risk_rubrics,
                    ),
                ),
                Preference(
                    name="governance_quality",
                    weight=0.35,
                    evaluator=Rubric(
                        name="governance_eval",
                        description="g",
                        aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                        criteria=governance_rubrics,
                    ),
                ),
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
    """Create goal achievement evaluator for US Co-op Bank internal risk and solvency assessment."""
    goal_achievement_rubrics = [
        # Critical risk assessment and regulatory deliverables (must have for supervisory approval)
        RubricCriteria(
            name="board_approved_assessment_complete",
            llm_prompt=(
                "Does complete board-approved assessment exist with: Board approval secured, "
                "supervisory-ready documentation prepared, internal risk assessment comprehensive, and solvency evaluation validated? "
                "Return true if board-approved assessment is complete, false otherwise."
            ),
            max_score=18.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="risk_appetite_statement_quantified",
            llm_prompt=(
                "Does quantified risk appetite statement exist with: quantitative limits established, "
                "early-warning indicators defined, risk appetite clearly articulated, and monitoring mechanisms active? "
                "Return true if risk appetite statement is quantified, false otherwise."
            ),
            max_score=15.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="capital_plan_ncua_compliant",
            llm_prompt=(
                "Does NCUA-compliant capital plan exist with: NCUA RBC or CCULR leverage requirements met, "
                "management buffer policy established, capital adequacy demonstrated, and regulatory compliance confirmed? "
                "Return true if capital plan is NCUA-compliant, false otherwise."
            ),
            max_score=15.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="scenario_stress_testing_comprehensive",
            llm_prompt=(
                "Does comprehensive scenario stress testing exist with: credit/IRRBB/liquidity/operational scenarios executed, "
                "climate overlay included, stress testing results documented, and scenario coverage adequate? "
                "Return true if scenario stress testing is comprehensive, false otherwise."
            ),
            max_score=12.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Major risk management and governance deliverables (8-10 points each)
        RubricCriteria(
            name="material_risk_inventory_assessed",
            llm_prompt=(
                "Does assessed material risk inventory exist with: inherent risks identified, "
                "controls effectiveness evaluated, residual risks documented, and risk owners assigned? "
                "Return true if material risk inventory is assessed, false otherwise."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="model_risk_framework_sr11_7",
            llm_prompt=(
                "Does SR 11-7 compliant model risk framework exist with: model inventory maintained, "
                "validation evidence documented, challenger outcomes reviewed, and model risk controls operational per SR 11-7? "
                "Return true if model risk framework is SR 11-7 compliant, false otherwise."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="liquidity_adequacy_contingency_plan",
            llm_prompt=(
                "Does liquidity adequacy and contingency plan exist with: liquidity adequacy analysis completed, "
                "contingency funding plan established, liquidity stress testing performed, and funding sources diversified? "
                "Return true if liquidity adequacy and contingency plan are established, false otherwise."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="board_package_supervisory_ready",
            llm_prompt=(
                "Does supervisory-ready board package exist with: executive summary prepared, "
                "key findings documented, capital decisions supported, and remediation actions planned? "
                "Return true if board package is supervisory-ready, false otherwise."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="governance_proportionality_documented",
            llm_prompt=(
                "Does documented governance proportionality exist with: credit union scale considerations addressed, "
                "proportionality rationale provided, governance appropriate to complexity, and regulatory expectations met? "
                "Return true if governance proportionality is documented, false otherwise."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Important supporting deliverables (5-7 points each)
        RubricCriteria(
            name="strategic_plan_budget_linkage",
            llm_prompt=(
                "Does strategic plan and budget linkage exist with: linkages to strategic plan confirmed, "
                "budget cycle integration documented, planning alignment verified, and strategic consistency maintained? "
                "Return true if strategic plan and budget linkage is established, false otherwise."
            ),
            max_score=7.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="climate_risk_overlay_included",
            llm_prompt=(
                "Does included climate risk overlay exist with: climate risk scenarios incorporated, "
                "climate risk assessment completed, environmental risk factors considered, and climate overlay documented? "
                "Return true if climate risk overlay is included, false otherwise."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="raci_roles_responsibilities",
            llm_prompt=(
                "Do RACI roles and responsibilities exist with: Board/Risk Committee roles defined, "
                "Management responsibilities clear, Risk and Finance functions assigned, and Internal Audit oversight established? "
                "Return true if RACI roles and responsibilities are established, false otherwise."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="recovery_options_documented",
            llm_prompt=(
                "Do documented recovery options exist with: recovery strategies identified, "
                "recovery actions planned, capital restoration options evaluated, and recovery planning comprehensive? "
                "Return true if recovery options are documented, false otherwise."
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="operational_risk_assessment",
            llm_prompt=(
                "Does operational risk assessment exist with: operational risks identified and quantified, "
                "operational risk controls evaluated, operational risk scenarios tested, and operational risk management effective? "
                "Return true if operational risk assessment is comprehensive, false otherwise."
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Supporting deliverables (3-4 points each)
        RubricCriteria(
            name="documentation_standards_audit_trail",
            llm_prompt=(
                "Do documentation standards and audit trail exist with: documentation standards defined, "
                "audit trail requirements met, version control maintained, and documentation quality assured? "
                "Return true if documentation standards and audit trail are established, false otherwise."
            ),
            max_score=4.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="data_foundations_validated",
            llm_prompt=(
                "Do validated data foundations exist with: data quality confirmed, "
                "data sources documented, data governance established, and data integrity maintained? "
                "Return true if data foundations are validated, false otherwise."
            ),
            max_score=4.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="regulatory_examination_readiness",
            llm_prompt=(
                "Does regulatory examination readiness exist with: examination preparation complete, "
                "regulatory responses ready, documentation organized, and compliance posture strong? "
                "Return true if regulatory examination readiness is achieved, false otherwise."
            ),
            max_score=3.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="risk_culture_assessment",
            llm_prompt=(
                "Does risk culture assessment exist with: risk culture evaluated, "
                "risk awareness measured, risk management behaviors assessed, and culture enhancement planned? "
                "Return true if risk culture assessment is complete, false otherwise."
            ),
            max_score=3.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    return Rubric(
        name="orsa_goal_achievement_eval",
        description="US Co-op Bank internal risk and solvency assessment deliverable achievement measurement",
        aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
        criteria=goal_achievement_rubrics,
    )
