from __future__ import annotations

from math import exp
from datetime import datetime

from manager_agent_gym.schemas.domain.workflow import Workflow
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
from examples.end_to_end_examples.standard_rules import speed_rubric, cost_rubric


def create_preferences() -> PreferenceSnapshot:
    # ---------------------------
    # Deterministic helper rules
    # ---------------------------
    def _safe_hours(delta_seconds: float) -> float:
        return max(0.0, float(delta_seconds)) / 3600.0

    # ---------------------------
    # Hardening Framework Functions
    # ---------------------------

    def _require_external_validation(
        workflow: Workflow, validation_keywords: list[str]
    ) -> float:
        """Require evidence of external validation for data science methodologies."""
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
                        "peer-reviewed",
                        "validated",
                        "audited",
                        "reviewed",
                        "approved",
                    ]
                ):
                    validation_evidence += 1

        return min(
            1.0, validation_evidence / max(1, total_tasks * 0.3)
        )  # Require 30% external validation

    def _data_science_adversarial_pressure_score(workflow: Workflow) -> float:
        """Score based on handling data science adversarial pressure and challenges."""
        pressure_indicators = [
            "data quality issue",
            "model bias",
            "statistical significance",
            "reproducibility challenge",
            "peer review",
            "methodology critique",
            "data privacy concern",
            "ethical review",
            "regulatory inquiry",
            "audit findings",
            "performance degradation",
            "model drift",
        ]

        pressure_handled = 0
        for indicator in pressure_indicators:
            for res in workflow.resources.values():
                if indicator.lower() in str(res.content or "").lower():
                    # Check for resolution evidence
                    if any(
                        resolution.lower() in str(res.content or "").lower()
                        for resolution in [
                            "addressed",
                            "mitigated",
                            "resolved",
                            "corrected",
                            "validated",
                        ]
                    ):
                        pressure_handled += 1
                    break

        return min(
            1.0, pressure_handled / max(1, len(pressure_indicators) * 0.3)
        )  # Expect 30% pressure scenarios

    def artifact_density_quality(workflow: Workflow) -> float:
        completed = [
            t for t in workflow.tasks.values() if t.status.value == "completed"
        ]
        if not completed:
            return 0.0
        total_outputs = 0
        for t in completed:
            total_outputs += len(t.output_resource_ids)
        avg_outputs = total_outputs / max(1, len(completed))
        return max(0.0, min(1.0, avg_outputs / 3.0))

    def reproducibility_signal(workflow: Workflow) -> float:
        """Signal [0,1] for presence of seeds/env pinning/experiment config hints in resources."""
        keywords = (
            "seed",
            "deterministic",
            "requirements.txt",
            "environment.yml",
            "pip freeze",
            "docker",
            "mlflow run",
        )
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

    def experiment_tracking_signal(workflow: Workflow) -> float:
        """Signal [0,1] for presence of tracking artifacts (mlflow/wandb/comet) in resources."""
        keywords = (
            "mlflow",
            "wandb",
            "weights & biases",
            "comet",
            "experiment id",
            "run id",
        )
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

    def dq_test_density(workflow: Workflow) -> float:
        """Signal [0,1] for presence of data-quality tests/expectations in artifacts."""
        keywords = (
            "test",
            "assert",
            "expectation",
            "validation",
            "great expectations",
            "dq check",
        )
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

    def pii_leak_scan(workflow: Workflow) -> float:
        """Return 1.0 if no obvious sensitive tokens; otherwise decay with number of hits."""
        prohibited = (
            "ssn",
            "passport",
            "password",
            "api key",
            "secret key",
            "private key",
            "account_number",
        )
        hits = 0
        for res in workflow.resources.values():
            try:
                content = (res.content or "").lower()
                for k in prohibited:
                    if k in content:
                        hits += 1
            except Exception:
                continue
        return 1.0 / (1.0 + float(hits))

    # Speed-related deterministic rules (each timestep)
    def speed_deadline_adherence(workflow: Workflow) -> float:
        total_est = 0.0
        total_act = 0.0
        for t in workflow.tasks.values():
            if t.estimated_duration_hours is not None:
                total_est += float(t.estimated_duration_hours)
            if t.actual_duration_hours is not None:
                total_act += float(t.actual_duration_hours)
        if total_est <= 0.0:
            return 0.5
        over = max(0.0, total_act - total_est) / total_est
        return exp(-0.8 * over)

    def speed_time_to_first_output(workflow: Workflow) -> float:
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
        total = len(workflow.tasks)
        if total == 0:
            return 0.0
        completed = len(
            [t for t in workflow.tasks.values() if t.status.value == "completed"]
        )
        return max(0.0, min(1.0, completed / max(1, total)))

    # ---------------------------
    # QUALITY
    # ---------------------------
    quality_rubrics = [
        RubricCriteria(
            name="evaluation_rigor",
            llm_prompt=(
                """Rigorously evaluate evaluation methodology with specific requirements:
                - shows proper train/validation/test splits with temporal considerations and documented rationale
                - demonstrates comprehensive calibration analysis with quantitative metrics (not just plots)
                - shows systematic data leakage detection with specific checks and validation
                - demonstrates statistically justified threshold selection with confidence intervals
                - shows uncertainty quantification with multiple methods and validation
                - shows external peer review or independent validation of methodology
                PENALTY: Deduct 2 points for each missing quantitative requirement. No credit for subjective assessments. Return score [0, 10]."""
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="error_analysis_depth",
            llm_prompt=(
                """
                Classify error analysis depth as "low" | "medium" | "high" (return this in score). Cite evidence.
                - LOW: Little to no cohort breakdowns; failure modes not described; no ablations.
                - MEDIUM: Some cohort breakdowns and failure descriptions; at least one ablation/what-if.
                - HIGH: Systematic cohort analysis with worst-group identification; clear confusion modes; multiple ablations.
                """
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="feature_quality_review",
            llm_prompt=(
                """
                Classify feature quality as "low" | "medium" | "high" (return this in score). Cite evidence.
                - LOW: Poor/absent docs; no stability/drift checks; leakage risks not addressed.
                - MEDIUM: Basic docs; some stability/drift or leakage checks; limitations noted.
                - HIGH: Thorough docs with lineage; stability/drift quantified; leakage and collinearity risks addressed.
                """
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="artifact_density_quality",
            evaluator_function=artifact_density_quality,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="data_science_adversarial_scenarios",
            llm_prompt=(
                """Evaluate handling of data science adversarial scenarios and challenges:
                - shows preparation for and handling of data quality issues and dataset challenges
                - demonstrates response to model bias accusations and fairness challenges
                - shows handling of reproducibility challenges and peer review criticism
                - demonstrates response to regulatory inquiries about methodology and ethics
                - shows preparation for model performance degradation and drift scenarios
                Score 0 if no adversarial scenarios addressed. Partial credit only with evidence of challenges AND resolution strategies. Return score [0, 10]."""
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # ---------------------------
    # RESPONSIBLE AI
    # ---------------------------
    rai_rubrics = [
        RubricCriteria(
            name="fairness_assessment_completeness",
            llm_prompt=(
                """
                Classify fairness assessment completeness as "low" | "medium" | "high" (return this in score). Cite evidence.
                - LOW: No group definitions or metrics; no policy comparison; no mitigation plan.
                - MEDIUM: Groups defined and some metrics computed OR policy comparison present; limited mitigation.
                - HIGH: Groups and metrics comprehensive; policy thresholds applied; mitigation/governance documented.
                """
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="explainability_quality",
            llm_prompt=(
                """
                Classify explainability quality as "low" | "medium" | "high" (return this in score). Cite evidence.
                - LOW: Minimal importances; no local explanations; no stakeholder-friendly narrative.
                - MEDIUM: Either decent global or local explanations and a basic narrative.
                - HIGH: Both robust global and local explanations with clear stakeholder narrative and limits.
                """
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="pii_leak_scan",
            evaluator_function=pii_leak_scan,
            max_score=1.0,
            run_condition=RunCondition.EACH_TIMESTEP,
        ),
    ]

    # ---------------------------
    # MLOPS
    # ---------------------------
    mlops_rubrics = [
        RubricCriteria(
            name="reproducibility_signal",
            evaluator_function=reproducibility_signal,
            max_score=1.0,
            run_condition=RunCondition.EACH_TIMESTEP,
        ),
        RubricCriteria(
            name="experiment_tracking_signal",
            evaluator_function=experiment_tracking_signal,
            max_score=1.0,
            run_condition=RunCondition.EACH_TIMESTEP,
        ),
        RubricCriteria(
            name="cicd_readiness",
            llm_prompt=(
                """
                Classify CI/CD readiness as "low" | "medium" | "high" (return this in score). Cite evidence.
                - LOW: No automated tests; no scans; artifacts not versioned.
                - MEDIUM: Some tests and scans OR versioned artifacts; gaps remain.
                - HIGH: Tests passing in CI; scans run and addressed; versioned artifacts and pinned env.
                """
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="monitoring_readiness",
            llm_prompt=(
                """
                Classify monitoring readiness as "low" | "medium" | "high" (return this in score). Cite evidence.
                - LOW: No metrics/SLOs; no alerting; no rollback/runbook.
                - MEDIUM: Some metrics or alerting; partial ownership; basic rollback notes.
                - HIGH: Metrics/SLOs defined; alerting/ownership clear; tested rollback with runbook.
                """
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # ---------------------------
    # DATA GOVERNANCE
    # ---------------------------
    data_gov_rubrics = [
        RubricCriteria(
            name="data_lineage_completeness",
            llm_prompt=(
                """
                Classify data lineage completeness as "low" | "medium" | "high" (return this in score). Cite evidence.
                - LOW: Sources/transforms missing; no owners/controls; no reconciliations.
                - MEDIUM: Sources and transforms present; some ownership/controls; partial reconciliations.
                - HIGH: Full sources/transforms; clear ownership/controls; reconciliations with variances explained.
                """
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="data_quality_checks_coverage",
            llm_prompt=(
                """
                Classify data-quality coverage as "low" | "medium" | "high" (return this in score). Cite evidence.
                - LOW: Few or no expectations; no integrity/freshness checks; no remediation.
                - MEDIUM: Some expectations and basic integrity/freshness; partial remediation.
                - HIGH: Comprehensive expectations; integrity/freshness with alerts; remediation process.
                """
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="dq_test_density",
            evaluator_function=dq_test_density,
            max_score=1.0,
            run_condition=RunCondition.EACH_TIMESTEP,
        ),
    ]

    # ---------------------------
    # BUSINESS VALUE
    # ---------------------------
    biz_value_rubrics = [
        RubricCriteria(
            name="kpi_linkage_clarity",
            llm_prompt=(
                """
                Classify KPI linkage clarity as "low" | "medium" | "high" (return this in score). Cite evidence.
                - LOW: KPI vague; no baseline/window; unclear decision linkage.
                - MEDIUM: KPI defined with baseline/window OR decision linkage described.
                - HIGH: KPI fully specified, impact model sensible, and decision linkage explicit.
                """
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="roi_estimate_credibility",
            llm_prompt=(
                """
                Classify ROI credibility as "low" | "medium" | "high" (return this in score). Cite evidence.
                - LOW: Costs/benefits unclear; no benchmarks; no uncertainty.
                - MEDIUM: Some transparency and either benchmarks or uncertainty ranges.
                - HIGH: Transparent components; benchmarked; scenario ranges with payback/sensitivity.
                """
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # ---------------------------
    # SPEED
    # ---------------------------
    speed_rubrics = [
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
        RubricCriteria(
            name="speed_efficiency",
            evaluator_function=speed_rubric,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="milestone_plan_quality",
            llm_prompt=(
                """
                Classify milestone plan quality as "low" | "medium" | "high" (return this in score). Cite evidence.
                - LOW: No critical path; no buffers; unrealistic estimates.
                - MEDIUM: Some path or buffers; partially realistic estimates.
                - HIGH: Clear critical path; appropriate buffers; realistic estimates with exit criteria.
                """
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="risk_register_quality",
            llm_prompt=(
                """
                Classify schedule risk register quality as "low" | "medium" | "high" (return this in score). Cite evidence.
                - LOW: Vague risks; no owners; no mitigations.
                - MEDIUM: Specific risks with some owners or mitigations.
                - HIGH: Specific risks with owners, triggers, and mitigation/residual plan.
                """
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
            evaluator_function=lambda w: (
                lambda budget, actual: (
                    0.5
                    if budget <= 0
                    else 1.0 / (1.0 + max(0.0, (actual - budget) / max(1e-6, budget)))
                )
            )(w.total_budget, w.total_cost),
            max_score=1.0,
            run_condition=RunCondition.EACH_TIMESTEP,
        ),
        RubricCriteria(
            name="cost_per_task_stability",
            evaluator_function=lambda w: (
                lambda planned_avg, actual_avg: (
                    0.5
                    if planned_avg <= 0
                    else 1.0 / (1.0 + abs((actual_avg / max(1e-6, planned_avg)) - 1.0))
                )
            )(
                (w.total_budget / max(1, len(w.tasks))) if len(w.tasks) > 0 else 0.0,
                (
                    w.total_cost
                    / max(
                        1,
                        len(
                            [
                                t
                                for t in w.tasks.values()
                                if t.status.value == "completed"
                            ]
                        ),
                    )
                )
                if len([t for t in w.tasks.values() if t.status.value == "completed"])
                > 0
                else 0.0,
            ),
            max_score=1.0,
            run_condition=RunCondition.EACH_TIMESTEP,
        ),
        RubricCriteria(
            name="cost_realism_vs_scope",
            llm_prompt=(
                """
                Classify cost realism as "low" | "medium" | "high" (return this in score). Cite evidence.
                - LOW: No benchmarks; costs misaligned with scope; no uncertainty.
                - MEDIUM: Some benchmarking or uncertainty; partial alignment.
                - HIGH: Benchmarked, aligned with scope, and uncertainty ranges disclosed.
                """
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="cost_justification_quality",
            llm_prompt=(
                """
                Classify cost justification quality as "low" | "medium" | "high" (return this in score). Cite evidence.
                - LOW: Costs not linked to outcomes; no alternatives; no sensitivity.
                - MEDIUM: Partial linkage; alternatives mentioned; basic sensitivity.
                - HIGH: Strong linkage; alternatives with trade-offs; thorough sensitivity.
                """
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    return PreferenceSnapshot(
        preferences=[
            Preference(
                name="quality",
                weight=0.25,
                evaluator=Rubric(
                    name="quality_eval",
                    description="quality evaluator",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    criteria=quality_rubrics,
                ),
            ),
            Preference(
                name="responsible_ai",
                weight=0.20,
                evaluator=Rubric(
                    name="responsible_ai_eval",
                    description="responsible ai evaluator",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    criteria=rai_rubrics,
                ),
            ),
            Preference(
                name="mlops",
                weight=0.15,
                evaluator=Rubric(
                    name="mlops_eval",
                    description="mlops evaluator",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    criteria=mlops_rubrics,
                ),
            ),
            Preference(
                name="data_governance",
                weight=0.10,
                evaluator=Rubric(
                    name="data_governance_eval",
                    description="data governance evaluator",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    criteria=data_gov_rubrics,
                ),
            ),
            Preference(
                name="business_value",
                weight=0.10,
                evaluator=Rubric(
                    name="business_value_eval",
                    description="business value evaluator",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    criteria=biz_value_rubrics,
                ),
            ),
            Preference(
                name="speed",
                weight=0.10,
                evaluator=Rubric(
                    name="speed_eval",
                    description="speed evaluator",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    criteria=speed_rubrics,
                ),
            ),
            Preference(
                name="cost",
                weight=0.10,
                evaluator=Rubric(
                    name="cost_eval",
                    description="cost evaluator",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    criteria=cost_rubrics,
                ),
            ),
        ],
        timestep=0,
    )


def create_preference_update_requests() -> list[PreferenceWeightUpdateRequest]:
    """Stakeholder weight update requests for DS analytics scenario."""
    timeline: dict[int, PreferenceSnapshot] = {
        0: PreferenceSnapshot(
            preferences=[
                Preference(name="quality", weight=0.20),
                Preference(name="responsible_ai", weight=0.15),
                Preference(name="mlops", weight=0.10),
                Preference(name="data_governance", weight=0.15),
                Preference(name="business_value", weight=0.10),
                Preference(name="speed", weight=0.15),
                Preference(name="cost", weight=0.15),
            ]
        ),
        10: PreferenceSnapshot(
            preferences=[
                Preference(name="quality", weight=0.25),
                Preference(name="responsible_ai", weight=0.15),
                Preference(name="mlops", weight=0.15),
                Preference(name="data_governance", weight=0.10),
                Preference(name="business_value", weight=0.10),
                Preference(name="speed", weight=0.10),
                Preference(name="cost", weight=0.15),
            ]
        ),
        60: PreferenceSnapshot(
            preferences=[
                Preference(name="quality", weight=0.20),
                Preference(name="responsible_ai", weight=0.25),
                Preference(name="mlops", weight=0.20),
                Preference(name="data_governance", weight=0.05),
                Preference(name="business_value", weight=0.15),
                Preference(name="speed", weight=0.05),
                Preference(name="cost", weight=0.10),
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
    """Create goal achievement evaluator for data science analytics project delivery."""
    goal_achievement_rubrics = [
        # Critical technical deliverables (must have for production deployment)
        RubricCriteria(
            name="production_ready_model_deployed",
            llm_prompt=(
                "Does deployed production-ready model exist with: CI/CD pipeline operational, "
                "model artifacts versioned and tracked, deployment package complete, and monitoring systems active? "
                "Return 18.0 if all conditions are met, removing 4 for every condition not met to a minimum of 0.0. Return 5.0 if there is evidence of any of these being planned but not yet completed."
            ),
            max_score=18.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="data_privacy_compliance_verified",
            llm_prompt=(
                "Does verified data privacy compliance exist with: PII policy compliance confirmed, "
                "secrets removed from artifacts, data access controls implemented, and privacy review passed? "
                "Return true is there is signs of an effort to verify data privacy compliance, false otherwise."
            ),
            max_score=15.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="reproducible_training_pipeline",
            llm_prompt=(
                "Does reproducible training pipeline exist with: fixed seeds implemented, "
                "environment captured and documented, experiment tracking active, and runs reproducible across environments? "
                "Return 15.0 if there is evidence of: 1. seeding, 2. environment pinning, 3. experiment tracking, removing 4.0 for each missing element. To a minimum of 0.0."
            ),
            max_score=15.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="bias_fairness_analysis_completed",
            llm_prompt=(
                "Does completed bias/fairness analysis exist with: bias metrics within policy thresholds, "
                "fairness analysis documented, mitigation strategies implemented, and responsible AI controls active? "
                "Return 12.0 if there is evidence of: 1. bias metrics within policy thresholds, 2. fairness analysis documented, 3. mitigation strategies implemented, 4. responsible AI controls active, removing 3.0 for each missing element. To a minimum of 0.0."
            ),
            max_score=12.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Major technical and business deliverables (8-10 points each)
        RubricCriteria(
            name="model_performance_thresholds_met",
            llm_prompt=(
                "Do met model performance thresholds exist with: evaluation metrics (AUC/accuracy) above minimum thresholds, "
                "calibration validated, performance benchmarks achieved, and quality gates passed? "
                "Return 10.0 if there is evidence of: 1. evaluation metrics (AUC/accuracy) above minimum thresholds, 2. calibration validated, 3. performance benchmarks achieved, 4. quality gates passed, removing 2.0 for each missing element. To a minimum of 0.0."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="curated_dataset_with_lineage",
            llm_prompt=(
                "Does curated dataset with lineage exist with: data quality checks implemented, "
                "data lineage documented, governance controls applied, and dataset versioning operational? "
                "Return 10.0 if there is evidence of: 1. data quality checks implemented, 2. data lineage documented, 3. governance controls applied, 4. dataset versioning operational, removing 2.0 for each missing element. To a minimum of 0.0."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="model_card_and_explainability",
            llm_prompt=(
                "Do model card and explainability exist with: model card completed with performance metrics, "
                "explainability report generated, interpretability features documented, and transparency requirements met? "
                "Return true if model card and explainability are complete, false otherwise."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Important supporting deliverables (5-7 points each)
        RubricCriteria(
            name="deployment_readiness_gate_passed",
            llm_prompt=(
                "Does passed deployment readiness gate exist with: security review completed, "
                "rollback plan documented, monitoring strategy validated, and operational readiness confirmed? "
                "Return 7.0 if there is evidence of: 1. security review completed, 2. rollback plan documented, 3. monitoring strategy validated, 4. operational readiness confirmed, removing 1.0 for each missing element. To a minimum of 0.0."
            ),
            max_score=7.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="experiment_tracking_system",
            llm_prompt=(
                "Does experiment tracking system exist with: all experiments logged, "
                "hyperparameters tracked, model versions managed, and reproducibility ensured? "
                "Return true if experiment tracking system has been created, false otherwise."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="model_monitoring_alerts",
            llm_prompt=(
                "Do model monitoring alerts exist with: drift detection implemented, "
                "performance monitoring active, alert thresholds configured, and incident response procedures defined? "
                "Return 5.0 if model monitoring alerts are implemented, 3.0 if it is planned or partially complete but not finalized, 0.0 otherwise."
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Supporting deliverables (3-4 points each)
        RubricCriteria(
            name="business_requirements_documented",
            llm_prompt=(
                "Do documented business requirements exist with: success metrics defined, "
                "business objectives captured, stakeholder requirements documented, and acceptance criteria established? "
                "Return true if business requirements are documented, false otherwise."
            ),
            max_score=4.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="model_validation_framework",
            llm_prompt=(
                "Does model validation framework exist with: validation strategies implemented, "
                "cross-validation performed, holdout testing completed, and validation results documented? "
                "Return true if model validation framework is established, false otherwise."
            ),
            max_score=4.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="data_access_governance",
            llm_prompt=(
                "Does data access governance exist with: access controls implemented, "
                "approval workflows established, audit trails maintained, and compliance monitoring active? "
                "Return true if data access governance is operational, false otherwise."
            ),
            max_score=3.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="project_documentation_complete",
            llm_prompt=(
                "Does complete project documentation exist with: methodology documented, "
                "assumptions captured, limitations identified, and knowledge transfer materials prepared? "
                "Return true if project documentation is complete, false otherwise."
            ),
            max_score=3.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    return Rubric(
        name="data_science_analytics_goal_achievement_eval",
        description="Data science analytics project delivery and governance achievement measurement",
        aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
        criteria=goal_achievement_rubrics,
    )
