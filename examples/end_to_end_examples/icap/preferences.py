"""
ICAAP (Internal Capital Adequacy Assessment Process) Demo

Real-world use case: Mid-size EU retail bank annual ICAAP cycle.

Demonstrates:
- Hierarchical task decomposition for ICAAP phases
- Preference dynamics emphasizing compliance near submission
- Ad hoc team coordination with human sign-offs
- Governance-by-design validation rules (LLM-based rubrics)
"""

from examples.end_to_end_examples.standard_rules import (
    speed_rubric,
    cost_rubric,
    evidence_seeking_behavior,
)
from math import exp
from datetime import datetime
from manager_agent_gym.schemas.preferences.preference import (
    Preference,
    PreferenceSnapshot,
)
from manager_agent_gym.schemas.preferences.evaluator import (
    Rubric,
    AggregationStrategy,
)
from manager_agent_gym.schemas.domain import Workflow
from manager_agent_gym.schemas.preferences.rubric import RubricCriteria, RunCondition
from manager_agent_gym.schemas.preferences import PreferenceWeightUpdateRequest


def create_preferences() -> PreferenceSnapshot:
    # ---------------------------
    # Deterministic helper rules
    # ---------------------------
    def _safe_hours(delta_seconds: float) -> float:
        return max(0.0, float(delta_seconds)) / 3600.0

    # ---------------------------
    # Hardening Framework Functions
    # ---------------------------
    def _validate_cost_realism(workflow: Workflow, context) -> float:
        """Penalize unrealistic cost discrepancies for ICAP assessments."""
        expected_min_cost = 60000.0  # Minimum realistic cost
        total_estimated = sum(
            task.estimated_cost
            for task in workflow.tasks.values()
            if task.estimated_cost
        )
        total_actual = sum(
            task.actual_cost for task in workflow.tasks.values() if task.actual_cost
        )

        if total_estimated == 0:
            return 0.0
        if total_actual < expected_min_cost:
            return 0.0  # ICAP assessments should cost >$60k

        cost_variance = abs(total_actual - total_estimated) / total_estimated
        if cost_variance > 0.3:
            return 0.2
        elif cost_variance > 0.15:
            return 0.6
        else:
            return 1.0

    def _icap_adversarial_pressure_score(workflow: Workflow) -> float:
        """Score based on handling ICAP adversarial pressure."""
        pressure_indicators = [
            "regulator challenge",
            "model criticism",
            "capital model failure",
            "stress scenario failure",
            "pra concern",
            "board challenge",
            "methodology dispute",
            "assumption challenge",
            "validation failure",
            "governance gap",
            "data quality issue",
            "capital inadequacy",
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
                        ]
                    ):
                        pressure_handled += 1
                    break

        return min(1.0, pressure_handled / max(1, len(pressure_indicators) * 0.3))

    def quality_seed_rule(workflow: Workflow) -> float:
        """Reward presence of seeds/config hints to improve reproducibility (0..1)."""
        keywords = ("seed", "configuration", "reproduce", "deterministic")
        total = 0
        hits = 0
        for res in workflow.resources.values():
            total += 1
            try:
                content = (res.content or "").lower()
                if any(k in content for k in keywords):
                    hits += 1
            except Exception:
                continue
        if total == 0:
            return 0.0
        return min(1.0, hits / max(1, total))

    def quality_resource_density(workflow: Workflow) -> float:
        """Reward having output artifacts for completed tasks (0..1)."""
        completed = [
            t for t in workflow.tasks.values() if t.status.value == "completed"
        ]
        if not completed:
            return 0.0
        total_outputs = 0
        for t in completed:
            total_outputs += len(t.output_resource_ids)
        avg_outputs = total_outputs / max(1, len(completed))
        # Saturate at 3 outputs per task
        return max(0.0, min(1.0, avg_outputs / 3.0))

    def speed_deadline_adherence(workflow: Workflow) -> float:
        """Penalty for duration overrun vs estimate aggregated across tasks (0..1)."""
        total_est = 0.0
        total_act = 0.0
        for t in workflow.tasks.values():
            if t.estimated_duration_hours is not None:
                total_est += float(t.estimated_duration_hours)
            if t.actual_duration_hours is not None:
                total_act += float(t.actual_duration_hours)
        if total_est <= 0.0:
            return 0.5  # neutral when no estimates
        over = max(0.0, total_act - total_est) / total_est
        return exp(-0.8 * over)

    def speed_time_to_first_output(workflow: Workflow) -> float:
        """Reward early first completion relative to expected hours (0..1)."""
        if workflow.started_at is None:
            return 0.5
        completed_times: list[datetime] = [
            t.completed_at
            for t in workflow.tasks.values()
            if t.completed_at is not None
        ]
        if not completed_times:
            return 0.0
        first_done = min(completed_times)
        elapsed_h = _safe_hours((first_done - workflow.started_at).total_seconds())
        expected_h = (
            workflow.total_expected_hours if workflow.total_expected_hours > 0 else 8.0
        )
        ratio = max(0.0, elapsed_h / max(1e-6, expected_h))
        return exp(-1.5 * ratio)

    def speed_blocked_deadtime_ratio(workflow: Workflow) -> float:
        """Penalty for dependency deadtime across tasks (0..1)."""
        dead_secs = 0.0
        denom_secs = 0.0
        for t in workflow.tasks.values():
            dead_secs += t.calculate_coordination_deadtime_seconds()
            if t.actual_duration_hours is not None:
                denom_secs += float(t.actual_duration_hours) * 3600.0
        if denom_secs <= 0.0:
            return 0.5
        ratio = max(0.0, dead_secs / denom_secs)
        return exp(-1.2 * ratio)

    def speed_throughput_progress(workflow: Workflow) -> float:
        """Progress proxy: completed/total tasks (0..1)."""
        total = len(workflow.tasks)
        if total == 0:
            return 0.0
        completed = len(
            [t for t in workflow.tasks.values() if t.status.value == "completed"]
        )
        return max(0.0, min(1.0, completed / max(1, total)))

    def cost_overrun_efficiency(workflow: Workflow) -> float:
        """Penalty for cost overrun vs budget (0..1)."""
        budget = workflow.total_budget
        actual = workflow.total_cost
        if budget <= 0.0:
            return 0.5
        over = max(0.0, actual - budget) / budget
        return 1.0 / (1.0 + over)

    def cost_per_completed_task_stability(workflow: Workflow) -> float:
        """Reward stable, reasonable cost per completed task vs planned average (0..1)."""
        completed = [
            t for t in workflow.tasks.values() if t.status.value == "completed"
        ]
        if not completed:
            return 0.0
        planned_avg = (
            (workflow.total_budget / max(1, len(workflow.tasks)))
            if len(workflow.tasks) > 0
            else 0.0
        )
        if planned_avg <= 0.0:
            return 0.5
        actual_avg = workflow.total_cost / max(1, len(completed))
        ratio = actual_avg / planned_avg
        # Reward closeness to 1.0 with a symmetric decay
        return 1.0 / (1.0 + abs(ratio - 1.0))

    def governance_decision_log_presence(workflow: Workflow) -> float:
        """Proxy for decision discipline: fraction of recent messages that look like decisions (0..1)."""
        recent = workflow.messages[-50:]
        if not recent:
            return 0.0
        hits = 0
        for m in recent:
            try:
                text = m.content.lower()
                if any(
                    k in text
                    for k in ("decision", "approve", "approved", "decide", "signed off")
                ):
                    hits += 1
            except Exception:
                continue
        return max(0.0, min(1.0, hits / max(1, len(recent))))

    # ---------------------------
    # QUALITY
    # ---------------------------
    quality_rubrics = [
        RubricCriteria(
            name="seeking_sourcing",
            evaluator_function=evidence_seeking_behavior,
            max_score=3.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="capital_adequacy_soundness",
            llm_prompt=(
                """Evaluate capital adequacy computation soundness. Award partial credit for:
                (a) internal consistency of calculations across tasks,
                (b) buffer calibration vs OCR+CBR/P2R/P2G/MDA,
                (c) cross‑checks between perspectives,
                (d) documented assumptions and sensitivity impacts.
                Cite specific workflow resources/messages for evidence. Output a numeric score in [0, 10]."""
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="assumptions_completeness_justification",
            llm_prompt=(
                """Assess if financial modelling assumptions are justified with data/benchmarks, with impacts and risks explained.
                Penalize missing or unverifiable evidence. Output a numeric score in [0, 5]."""
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="sensitivity_analysis_depth",
            llm_prompt=(
                """Evaluate sensitivity analysis depth: (1) multi‑parameter sweeps, (2) rationale for assumptions,
                (3) decision‑impact discussion. Award equal partial credit. Cite evidence. Output numeric score [0, 6]."""
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="reproducibility_procedural_integrity",
            evaluator_function=quality_seed_rule,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="scenario_coverage",
            llm_prompt=(
                """
                Evaluate scenario coverage evidence: baseline, adverse, severe, and reverse stress tests.
                Provide partial credit per scenario with severity rationale. Output numeric score [0, 10].
            """
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="risk_type_coverage",
            llm_prompt=(
                "Score 0–10 for risk type coverage: credit, market/CVA/IRRBB, liquidity, operational/model/concentration;"
                " award partial credit with materiality and method summaries. Output numeric score [0, 10]."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="mgmt_actions_linkage",
            llm_prompt=(
                "Evaluate linkage of management actions to results: triggers, timelines, quantified effects, governance."
                " Award partial credit with citations. Output numeric score [0, 10]."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="stress_testing_completeness",
            llm_prompt=(
                "Assess stress‑testing completeness (including reverse). Partial credit across scenarios, severity, and action linkage."
                " Output numeric score [0, 10]."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="artifact_density_quality",
            evaluator_function=quality_resource_density,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # ---------------------------
    # COMPLIANCE (ICAAP-focused)
    # ---------------------------
    compliance_rubrics = [
        RubricCriteria(
            name="regulatory_mapping_completeness",
            llm_prompt=(
                "Evaluate mapping of ICAAP to PRA/ECB/CRD/CRR and Basel principles. Award partial credit for: coverage,"
                " evidence quality (citations), proportionality rationale, and explicit gaps/limitations. Output numeric score [0, 10]."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="formal_signoffs_present",
            llm_prompt=(
                "Assess formal sign‑offs: named approvers (e.g., Board/CRO/CFO) with dates and scope; reference specific ICAAP sections."
                " Award partial credit. Output numeric score [0, 10]."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="data_lineage_and_audit_trail",
            llm_prompt=(
                "Evaluate data lineage and auditability: source registries, reconciliations/controls, reproducibility steps, issue log with remediation."
                " Award partial credit with citations. Output numeric score [0, 10]."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="model_risk_controls",
            llm_prompt=(
                "Assess model risk controls: assumptions/limitations, independent validation evidence, performance monitoring/backtesting, inventory references."
                " Provide partial credit with citations. Output numeric score [0, 10]."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="sensitive_info_handling",
            llm_prompt=(
                "Evaluate sensitive information handling: PII/secret handling, redactions, and documented access controls/roles."
                " Output numeric score [0, 10]."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="capital_adequacy_thresholds",
            llm_prompt=(
                "Evaluate normative capital adequacy over 3 years. Partial credit for CET1≥OCR+CBR, P2R/P2G, MDA, and management buffer discussion."
                " Output numeric score [0, 10]."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="material_risk_coverage",
            llm_prompt=(
                "Assess material risk coverage: inventory, core risks, additional risks, proportionality; ensure each risk has quantification approach and controls."
                " Partial credit with citations. Output numeric score [0, 10]."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # ---------------------------
    # GOVERNANCE
    # ---------------------------
    governance_rubrics = [
        RubricCriteria(
            name="governance_completeness",
            llm_prompt=(
                "Evaluate governance completeness: roles, RAF/limits, committees, sign‑offs, and integration into planning/budgeting."
                " Award partial credit with citations. Output numeric score [0, 10]."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="dual_perspective_coherence",
            llm_prompt=(
                "Evaluate coherence between economic and normative perspectives: presence, assumption alignment, reconciliation, plan alignment."
                " Output numeric score [0, 10]."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="management_actions_credibility",
            llm_prompt=(
                "Assess credibility of management actions: feasibility, timeliness, quantification, triggers/governance."
                " Partial credit with citations. Output numeric score [0, 10]."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="decision_log_coverage",
            llm_prompt=(
                "Evaluate decision log coverage and traceability: major decisions documented with rationale and approver, and linked to artifacts."
                " Output numeric score [0, 8]."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="escalation_discipline",
            llm_prompt=(
                "Assess escalation discipline: timely escalation when blocked, rationale provided, and resolution documented."
                " Output numeric score [0, 6]."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="governance_decision_log_signal",
            evaluator_function=governance_decision_log_presence,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # ---------------------------
    # SPEED
    # ---------------------------
    speed_rubrics = [
        # Deterministic
        RubricCriteria(
            name="deadline_adherence",
            evaluator_function=speed_deadline_adherence,
            max_score=1.0,
            run_condition=RunCondition.EACH_TIMESTEP,
        ),
        RubricCriteria(
            name="time_to_first_output",
            evaluator_function=speed_time_to_first_output,
            max_score=1.0,
            run_condition=RunCondition.EACH_TIMESTEP,
        ),
        RubricCriteria(
            name="blocked_deadtime_penalty",
            evaluator_function=speed_blocked_deadtime_ratio,
            max_score=1.0,
            run_condition=RunCondition.EACH_TIMESTEP,
        ),
        RubricCriteria(
            name="throughput_progress",
            evaluator_function=speed_throughput_progress,
            max_score=1.0,
            run_condition=RunCondition.EACH_TIMESTEP,
        ),
        # Existing combined speed rule
        RubricCriteria(
            name="speed_efficiency",
            evaluator_function=speed_rubric,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # LLM plan/robustness checks
        RubricCriteria(
            name="milestone_plan_quality",
            llm_prompt=(
                "Evaluate milestone plan realism and risk identification, including critical path identification and buffers."
                " Cite evidence. Output numeric score [0, MAX]."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="critical_path_robustness",
            llm_prompt=(
                "Assess critical path robustness: dependency clarity, alternates, and buffer adequacy."
                " Output numeric score [0, MAX]."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="risk_register_quality",
            llm_prompt=(
                "Evaluate risk register specificity, ownership, triggers, and mitigation steps related to schedule risks."
                " Output numeric score [0, MAX]."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # ---------------------------
    # COST
    # ---------------------------
    cost_rubrics = [
        RubricCriteria(
            name="cost_efficiency",
            evaluator_function=cost_rubric,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="cost_overrun_efficiency",
            evaluator_function=cost_overrun_efficiency,
            max_score=1.0,
            run_condition=RunCondition.EACH_TIMESTEP,
        ),
        RubricCriteria(
            name="cost_per_task_stability",
            evaluator_function=cost_per_completed_task_stability,
            max_score=1.0,
            run_condition=RunCondition.EACH_TIMESTEP,
        ),
        RubricCriteria(
            name="cost_justification_quality",
            llm_prompt=(
                "Assess cost justification quality: clear rationale tied to scope/benefit and alternative options considered."
                " Cite evidence. Output numeric score [0, MAX]."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="cost_realism_vs_scope",
            llm_prompt=(
                "Evaluate cost realism vs scope based on benchmarks and complexity; flag under/over estimation with justification."
                " Output numeric score [0, MAX]."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="savings_opportunities_identified",
            llm_prompt=(
                "Evaluate whether credible savings opportunities and trade‑offs are identified, with quantified impacts."
                " Output numeric score [0, MAX]."
            ),
            max_score=4.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="icap_adversarial_scenarios",
            llm_prompt=(
                """Evaluate handling of ICAP adversarial scenarios and regulatory pressure:
                - shows preparation for regulator challenges and model criticism
                - demonstrates response to capital model failures and stress scenario failures
                - shows handling of PRA concerns and board challenges
                - demonstrates preparation for methodology disputes and assumption challenges
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

    return PreferenceSnapshot(
        preferences=[
            Preference(
                name="quality",
                weight=0.4,
                evaluator=Rubric(
                    type="rubric",
                    name="quality_eval",
                    description="quality evaluator",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    criteria=quality_rubrics,
                ),
            ),
            Preference(
                name="compliance",
                weight=0.25,
                evaluator=Rubric(
                    type="rubric",
                    name="compliance_eval",
                    description="compliance evaluator",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    criteria=compliance_rubrics,
                ),
            ),
            Preference(
                name="governance",
                weight=0.15,
                evaluator=Rubric(
                    type="rubric",
                    name="governance_eval",
                    description="governance evaluator",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    criteria=governance_rubrics,
                ),
            ),
            Preference(
                name="speed",
                weight=0.1,
                evaluator=Rubric(
                    type="rubric",
                    name="speed_eval",
                    description="speed evaluator",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    criteria=speed_rubrics,
                ),
            ),
            Preference(
                name="cost",
                weight=0.1,
                evaluator=Rubric(
                    type="rubric",
                    name="cost_eval",
                    description="cost evaluator",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    criteria=cost_rubrics,
                ),
            ),
        ]
    )


def create_preference_update_requests() -> list[PreferenceWeightUpdateRequest]:
    """Build stakeholder weight update requests for the ICAP scenario.

    Converts the timeline of absolute weights into requests consumable by
    StakeholderAgent.apply_weight_updates.
    """
    timeline: dict[int, PreferenceSnapshot] = {
        0: PreferenceSnapshot(
            preferences=[
                Preference(name="quality", weight=0.3),
                Preference(name="compliance", weight=0.2),
                Preference(name="governance", weight=0.1),
                Preference(name="speed", weight=0.05),
                Preference(name="cost", weight=0.05),
            ]
        ),
        10: PreferenceSnapshot(
            preferences=[
                Preference(name="quality", weight=0.2),
                Preference(name="compliance", weight=0.3),
                Preference(name="governance", weight=0.1),
                Preference(name="speed", weight=0.05),
                Preference(name="cost", weight=0.05),
            ]
        ),
        30: PreferenceSnapshot(
            preferences=[
                Preference(name="quality", weight=0.1),
                Preference(name="compliance", weight=0.4),
                Preference(name="governance", weight=0.1),
                Preference(name="speed", weight=0.05),
                Preference(name="cost", weight=0.05),
            ]
        ),
        60: PreferenceSnapshot(
            preferences=[
                Preference(name="quality", weight=0.1),
                Preference(name="compliance", weight=0.6),
                Preference(name="governance", weight=0.05),
                Preference(name="speed", weight=0.05),
                Preference(name="cost", weight=0.05),
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
    """Create goal achievement evaluator for Annual ICAAP EU retail bank capital adequacy assessment."""
    goal_achievement_rubrics = [
        # Critical regulatory and governance deliverables (must have for ICAAP submission)
        RubricCriteria(
            name="comprehensive_risk_inventory_complete",
            llm_prompt=(
                "Does complete comprehensive risk inventory exist with: credit risk materiality assessment with quantitative thresholds, "
                "market/CVA/IRRBB quantification with stress scenario validation, liquidity and operational risk evaluation with impact analysis, "
                "concentration and model risk analysis with remediation plans, documented risk owners with accountability matrix, "
                "and quantification methods with independent validation evidence? "
                "Return true if comprehensive risk inventory meets all enhanced requirements, false otherwise."
            ),
            max_score=18.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="economic_capital_computation_validated",
            llm_prompt=(
                "Does validated economic capital computation exist with: comprehensive sensitivity analysis across multiple parameters, "
                "cross-model consistency checks with reconciliation documentation, economic capital framework with detailed methodology, "
                "independent validation evidence with challenger model results, and regulatory benchmark comparisons with variance explanations? "
                "Return true if economic capital computation meets all enhanced validation standards, false otherwise."
            ),
            max_score=15.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="stress_testing_comprehensive",
            llm_prompt=(
                "Does comprehensive stress testing exist with: baseline/adverse/severe scenarios executed with detailed impact analysis, "
                "reverse stress testing completed with breaking point identification and severity rationale, institution-wide scope confirmed with inter-risk correlations, "
                "management actions and recovery measures documented, and results interpreted with strategic implications assessed? "
                "Return true if stress testing meets all enhanced comprehensiveness standards, false otherwise."
            ),
            max_score=15.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="normative_capital_plan_approved",
            llm_prompt=(
                "Does approved normative capital plan exist with: detailed 3-year CET1 vs OCR+CBR projections with stress scenario impacts, "
                "comprehensive P2R/P2G assessment with supervisory dialogue evidence, MDA thresholds established with breach scenario analysis, "
                "management buffer sizing documented with volatility considerations, and board approval with strategic alignment confirmation? "
                "Return true if normative capital plan meets all enhanced approval standards, false otherwise."
            ),
            max_score=12.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Major governance and compliance deliverables (8-10 points each)
        RubricCriteria(
            name="governance_package_complete",
            llm_prompt=(
                "Does complete governance package exist with: decision logs documented, "
                "committee materials prepared, board and executive sign-offs secured, and escalation evidence maintained? "
                "Return true if governance package is complete, false otherwise."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="regulatory_mapping_documented",
            llm_prompt=(
                "Does documented regulatory mapping exist with: PRA/ECB/CRD/CRR compliance confirmed, "
                "Basel requirements addressed, proportionality rationale provided, and explicit gaps identified? "
                "Return true if regulatory mapping is documented, false otherwise."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="management_actions_catalog_feasible",
            llm_prompt=(
                "Does feasible management actions catalog exist with: management actions identified, "
                "feasibility assessments completed, triggers and timelines defined, and quantified impacts documented? "
                "Return true if management actions catalog is feasible, false otherwise."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="economic_normative_consistency",
            llm_prompt=(
                "Does economic and normative consistency exist with: consistency between perspectives demonstrated, "
                "reconciliations provided where required, perspective alignment documented, and differences explained? "
                "Return true if economic and normative consistency is established, false otherwise."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="data_lineage_registry_complete",
            llm_prompt=(
                "Does complete data lineage registry exist with: data sources documented, "
                "lineage tracking established, reproducibility notes provided, and key figures validated? "
                "Return true if data lineage registry is complete, false otherwise."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Important supporting deliverables (5-7 points each)
        RubricCriteria(
            name="scenario_coverage_evidenced",
            llm_prompt=(
                "Does evidenced scenario coverage exist with: scenario coverage comprehensive, "
                "reverse stress scenarios included, decision-impact analysis documented, and scenario rationale provided? "
                "Return true if scenario coverage is evidenced, false otherwise."
            ),
            max_score=7.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="board_committee_sign_offs",
            llm_prompt=(
                "Do board and committee sign-offs exist with: validation sign-offs secured, "
                "compliance approvals obtained, internal audit confirmation received, and board pack approved? "
                "Return true if board and committee sign-offs are secured, false otherwise."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="confidential_information_controls",
            llm_prompt=(
                "Do confidential information controls exist with: confidential information redacted appropriately, "
                "access controls documented, data security measures implemented, and information handling protocols followed? "
                "Return true if confidential information controls are effective, false otherwise."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="model_validation_evidence",
            llm_prompt=(
                "Does model validation evidence exist with: model validation completed, "
                "model performance assessed, validation reports documented, and model risk controls operational? "
                "Return true if model validation evidence is comprehensive, false otherwise."
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="regulatory_submission_readiness",
            llm_prompt=(
                "Does regulatory submission readiness exist with: submission package complete, "
                "regulatory requirements met, submission timeline confirmed, and quality assurance performed? "
                "Return true if regulatory submission readiness is achieved, false otherwise."
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Supporting deliverables (3-4 points each)
        RubricCriteria(
            name="proportionality_assessment_documented",
            llm_prompt=(
                "Does documented proportionality assessment exist with: proportionality principles applied, "
                "assessment rationale provided, regulatory expectations addressed, and complexity considerations documented? "
                "Return true if proportionality assessment is documented, false otherwise."
            ),
            max_score=4.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="risk_appetite_framework_updated",
            llm_prompt=(
                "Does updated risk appetite framework exist with: risk appetite statement current, "
                "risk limits defined, monitoring mechanisms active, and governance oversight confirmed? "
                "Return true if risk appetite framework is updated, false otherwise."
            ),
            max_score=4.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="audit_trail_maintained",
            llm_prompt=(
                "Does maintained audit trail exist with: audit trail comprehensive, "
                "documentation standards followed, version control active, and review history preserved? "
                "Return true if audit trail is maintained, false otherwise."
            ),
            max_score=3.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="high_risk_issues_resolved",
            llm_prompt=(
                "Do resolved high-risk issues exist with: high-risk issues identified and addressed, "
                "resolution documentation complete, outstanding issues minimal, and risk mitigation effective? "
                "Return true if high-risk issues are resolved, false otherwise."
            ),
            max_score=3.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    return Rubric(
        name="icap_goal_achievement_eval",
        description="Annual ICAAP EU retail bank capital adequacy assessment deliverable achievement measurement",
        aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
        criteria=goal_achievement_rubrics,
    )
