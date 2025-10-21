"""
Gen-AI Feature Launch Demo

Real-world use case: User-facing generative AI feature launch with safety gates and governance.

Demonstrates:
- Complex multi-stakeholder coordination across AI safety, privacy, security, and regulatory compliance domains
- Risk-driven project management with safety-first prioritization and gate-based approval workflows
- High-stakes decision making under regulatory scrutiny with audit-ready documentation requirements
- Crisis-ready deployment planning with real-time monitoring, kill switches, and incident response capabilities
- Cross-functional team leadership managing technical specialists, legal counsel, and executive stakeholders
- Regulatory compliance management across data protection, AI transparency, and safety disclosure requirements
- Timeline-critical delivery under 6-week constraint with safety-first scope management and controlled rollout strategies
"""

from examples.end_to_end_examples.standard_rules import (
    speed_rubric,
    cost_rubric,
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
        """Penalize unrealistic cost discrepancies for AI feature development."""
        expected_min_cost = 25000.0  # Minimum realistic cost
        total_estimated = sum(
            task.estimated_cost
            for task in workflow.tasks.values()
            if task.estimated_cost
        )
        total_actual = sum(
            task.actual_cost for task in workflow.tasks.values() if task.actual_cost
        )

        if total_estimated == 0:
            return 0.0  # No cost planning penalty

        if total_actual < expected_min_cost:
            return 0.0  # AI development should cost more than $25k

        cost_variance = abs(total_actual - total_estimated) / total_estimated
        if cost_variance > 0.4:  # >40% cost variance penalty for tech projects
            return 0.2
        elif cost_variance > 0.15:  # >15% cost variance partial penalty
            return 0.6
        else:
            return 1.0

    def _require_external_validation(
        workflow: Workflow, validation_keywords: list[str]
    ) -> float:
        """Require evidence of external validation for AI safety and compliance."""
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
                        "certified",
                        "audited",
                        "reviewed",
                    ]
                ):
                    validation_evidence += 1

        return min(
            1.0, validation_evidence / max(1, total_tasks * 0.25)
        )  # Require 25% external validation

    def _ai_adversarial_pressure_score(workflow: Workflow) -> float:
        """Score based on handling AI-specific adversarial pressure and crisis scenarios."""
        pressure_indicators = [
            "regulatory investigation",
            "ai safety incident",
            "bias complaint",
            "data breach",
            "model vulnerability",
            "public backlash",
            "media scrutiny",
            "competitor attack",
            "red team findings",
            "safety failure",
            "audit findings",
        ]

        pressure_handled = 0
        for indicator in pressure_indicators:
            for res in workflow.resources.values():
                if indicator.lower() in str(res.content or "").lower():
                    # Check for resolution evidence
                    if any(
                        resolution.lower() in str(res.content or "").lower()
                        for resolution in [
                            "mitigated",
                            "resolved",
                            "addressed",
                            "fixed",
                            "patched",
                        ]
                    ):
                        pressure_handled += 1
                    break

        return min(
            1.0, pressure_handled / max(1, len(pressure_indicators) * 0.3)
        )  # Expect 30% pressure scenarios

    def ai_safety_seed_rule(workflow: Workflow) -> float:
        """Reward presence of safety seeds/config hints to improve AI safety reproducibility (0..1)."""
        keywords = (
            "safety_seed",
            "red_team_config",
            "safety_threshold",
            "test_reproducible",
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

    def safety_artifact_density(workflow: Workflow) -> float:
        """Reward having safety artifacts for completed AI tasks (0..1)."""
        completed = [
            t for t in workflow.tasks.values() if t.status.value == "completed"
        ]
        if not completed:
            return 0.0
        total_outputs = 0
        for t in completed:
            total_outputs += len(t.output_resource_ids)
        avg_outputs = total_outputs / max(1, len(completed))
        # Saturate at 2.5 outputs per task for AI safety complexity
        return max(0.0, min(1.0, avg_outputs / 2.5))

    def safety_deadline_adherence(workflow: Workflow) -> float:
        """Penalty for safety testing overrun vs estimate (0..1)."""
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

    def safety_time_to_first_output(workflow: Workflow) -> float:
        """Reward early first safety completion relative to expected hours (0..1)."""
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

    def safety_blocked_deadtime_ratio(workflow: Workflow) -> float:
        """Penalty for safety dependency deadtime across tasks (0..1)."""
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

    def safety_throughput_progress(workflow: Workflow) -> float:
        """Safety progress proxy: completed/total tasks (0..1)."""
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

    def safety_cost_per_completed_task_stability(workflow: Workflow) -> float:
        """Reward stable, reasonable safety cost per completed task vs planned average (0..1)."""
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

    def governance_safety_decision_log_presence(workflow: Workflow) -> float:
        """Proxy for safety decision discipline: fraction of recent messages that look like safety decisions (0..1)."""
        recent = workflow.messages[-50:]
        if not recent:
            return 0.0
        hits = 0
        for m in recent:
            try:
                text = m.content.lower()
                if any(
                    k in text
                    for k in (
                        "safety decision",
                        "risk accepted",
                        "red team approved",
                        "safety signed off",
                        "launch approved",
                    )
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
            name="ai_safety_testing_soundness",
            llm_prompt=(
                """Rigorously evaluate AI safety testing soundness with specific requirements:
                - shows comprehensive red team testing across ALL major attack vectors (not just basic tests)
                - demonstrates prompt injection and jailbreak resistance with quantitative pass/fail metrics
                - shows hallucination detection with statistical validation and accuracy benchmarks
                - demonstrates bias and fairness evaluation with measurable remediation steps
                - shows external security audit or independent validation (not just internal testing)
                PENALTY: Deduct 2 points for each missing requirement. No credit for testing without measurable results. Output a numeric score in [0, 10]."""
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="threat_model_completeness_justification",
            llm_prompt=(
                """Assess if AI threat modeling assumptions are justified with evidence/benchmarks, with attack scenarios and risks explained.
                Penalize missing or unverifiable threat analysis. Output a numeric score in [0, 5]."""
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="safety_control_architecture_depth",
            llm_prompt=(
                """Evaluate safety control architecture depth: (1) input/output filtering design, (2) runtime monitoring systems,
                (3) kill switch and circuit breaker implementation. Award equal partial credit. Cite evidence. Output numeric score [0, 6]."""
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="safety_reproducibility_procedural_integrity",
            evaluator_function=ai_safety_seed_rule,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="red_team_scenario_coverage",
            llm_prompt=(
                """Evaluate red team scenario coverage with specific evidence requirements:
                - shows systematic prompt injection testing with documented failure rates
                - demonstrates jailbreak resistance across multiple attack methodologies
                - shows data exfiltration prevention with quantitative validation
                - demonstrates unsafe function calling protection with test scenarios
                - shows adversarial input handling under stress conditions
                PENALTY: Deduct 2 points for each attack vector without quantitative results. No credit for theoretical coverage. Output numeric score [0, 10]."""
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="ai_risk_type_coverage",
            llm_prompt=(
                "Score 0–10 for AI risk type coverage: safety violations, bias/fairness, hallucination, privacy leakage, adversarial attacks;"
                " award partial credit with testing methodology summaries. Output numeric score [0, 10]."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="monitoring_systems_linkage",
            llm_prompt=(
                "Evaluate linkage of monitoring systems to safety results: alert thresholds, automated responses, escalation procedures."
                " Award partial credit with citations. Output numeric score [0, 10]."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="safety_testing_completeness",
            llm_prompt=(
                "Assess safety testing completeness (including human adversarial testing). Partial credit across scenarios, automation, and remediation tracking."
                " Output numeric score [0, 10]."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="safety_artifact_density_quality",
            evaluator_function=safety_artifact_density,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="ai_crisis_scenario_handling",
            llm_prompt=(
                """Evaluate AI crisis scenario handling and preparedness:
                - shows preparation for AI safety incident response with specific protocols
                - demonstrates handling of public AI bias complaints with remediation plans
                - shows regulatory investigation response procedures and documentation
                - demonstrates competitor AI attack mitigation strategies
                - shows media crisis management for AI safety failures
                Score 0 if no crisis scenarios addressed. Partial credit only with evidence of scenarios AND response plans. Output numeric score [0, 10]."""
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # ---------------------------
    # COMPLIANCE (AI-focused)
    # ---------------------------
    compliance_rubrics = [
        RubricCriteria(
            name="ai_regulatory_mapping_completeness",
            llm_prompt=(
                "Evaluate mapping of AI feature to privacy regulations (GDPR/CCPA/AI Act). Award partial credit for: coverage,"
                " evidence quality (citations), AI-specific compliance rationale, and explicit gaps/limitations. Output numeric score [0, 10]."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="stakeholder_signoffs_present",
            llm_prompt=(
                "Assess formal sign‑offs: named approvers (Product/Security/Privacy/Legal/Executive) with dates and scope; reference specific AI safety sections."
                " Award partial credit. Output numeric score [0, 10]."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="dpia_data_lineage_audit_trail",
            llm_prompt=(
                "Evaluate DPIA and data lineage auditability: data flow registries, consent mechanisms, DSR handling, reproducibility steps."
                " Award partial credit with citations. Output numeric score [0, 10]."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="ai_model_risk_controls",
            llm_prompt=(
                "Assess AI model risk controls: bias monitoring, performance validation, safety threshold enforcement, model version control."
                " Provide partial credit with citations. Output numeric score [0, 10]."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="pii_sensitive_info_handling",
            llm_prompt=(
                "Evaluate PII and sensitive information handling: detection systems, data minimization, anonymization procedures, access controls."
                " Cite evidence and award partial credit. Output numeric score [0, 10]."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="ai_transparency_disclosure_requirements",
            llm_prompt=(
                "Assess AI transparency disclosure compliance: user notifications, capability limitations, model cards, content labeling implementation."
                " Award partial credit for regulatory alignment. Output numeric score [0, 10]."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="external_compliance_validation",
            llm_prompt=(
                """Evaluate external compliance validation and adversarial pressure handling:
                - shows external legal or regulatory review of AI compliance approach
                - demonstrates third-party security audit of AI safety controls
                - shows preparation for regulatory investigation or compliance challenge
                - demonstrates handling of public bias or safety complaints
                - shows independent validation of privacy and data protection measures
                PENALTY: Deduct 2 points for each missing external validation. No credit for internal-only reviews. Output numeric score [0, 10]."""
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
            name="ai_governance_framework_maturity",
            llm_prompt=(
                "Evaluate AI governance framework maturity: decision rights clarity, approval workflows, risk escalation procedures, accountability assignment."
                " Award partial credit for documented processes. Output numeric score [0, 10]."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="launch_gate_governance_effectiveness",
            llm_prompt=(
                "Assess launch gate governance: safety thresholds, approval criteria, gate progression logic, rollback triggers."
                " Award partial credit for clear criteria and evidence. Output numeric score [0, 10]."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="cross_functional_coordination_quality",
            llm_prompt=(
                "Evaluate cross-functional coordination: stakeholder engagement, dependency management, communication effectiveness, conflict resolution."
                " Cite coordination evidence. Output numeric score [0, 10]."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="incident_response_governance",
            llm_prompt=(
                "Assess incident response governance: escalation procedures, decision authority, communication protocols, kill switch governance."
                " Award partial credit for preparedness evidence. Output numeric score [0, 10]."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="ai_decision_log_presence",
            evaluator_function=governance_safety_decision_log_presence,
            max_score=1.0,
            run_condition=RunCondition.EACH_TIMESTEP,
        ),
        RubricCriteria(
            name="audit_readiness_documentation",
            llm_prompt=(
                "Evaluate audit readiness: evidence linkage, decision traceability, compliance documentation completeness, regulatory scrutiny preparation."
                " Award partial credit for audit trail quality. Output numeric score [0, 10]."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # ---------------------------
    # SPEED
    # ---------------------------
    speed_rubrics = [
        RubricCriteria(
            name="safety_first_timeline_efficiency",
            evaluator_function=safety_deadline_adherence,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="red_team_velocity",
            evaluator_function=safety_time_to_first_output,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="safety_testing_coordination_efficiency",
            evaluator_function=safety_blocked_deadtime_ratio,
            max_score=1.0,
            run_condition=RunCondition.EACH_TIMESTEP,
        ),
        RubricCriteria(
            name="launch_gate_progression_speed",
            evaluator_function=safety_throughput_progress,
            max_score=1.0,
            run_condition=RunCondition.EACH_TIMESTEP,
        ),
        RubricCriteria(
            name="speed_efficiency",
            evaluator_function=speed_rubric,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # ---------------------------
    # COST
    # ---------------------------
    cost_rubrics = [
        RubricCriteria(
            name="ai_safety_cost_overrun_control",
            evaluator_function=cost_overrun_efficiency,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="safety_investment_efficiency",
            evaluator_function=safety_cost_per_completed_task_stability,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="cost_efficiency",
            evaluator_function=cost_rubric,
            max_score=1.0,
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
                    name="ai_safety_quality_eval",
                    description="AI safety and testing quality evaluation",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    criteria=quality_rubrics,
                ),
            ),
            Preference(
                name="compliance",
                weight=0.25,
                evaluator=Rubric(
                    name="ai_compliance_eval",
                    description="AI regulatory compliance and privacy evaluation",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    criteria=compliance_rubrics,
                ),
            ),
            Preference(
                name="governance",
                weight=0.15,
                evaluator=Rubric(
                    name="ai_governance_eval",
                    description="AI governance and stakeholder coordination evaluation",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    criteria=governance_rubrics,
                ),
            ),
            Preference(
                name="speed",
                weight=0.1,
                evaluator=Rubric(
                    name="ai_safety_speed_eval",
                    description="AI safety-first timeline and efficiency evaluation",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    criteria=speed_rubrics,
                ),
            ),
            Preference(
                name="cost",
                weight=0.1,
                evaluator=Rubric(
                    name="ai_safety_cost_eval",
                    description="AI safety investment and cost efficiency evaluation",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    criteria=cost_rubrics,
                ),
            ),
        ]
    )


def create_evaluator_to_measure_goal_achievement() -> Rubric:
    """Create a separate goal achievement evaluator for GenAI Feature Launch."""
    goal_achievement_rubrics = [
        # Critical deliverables (10 points each)
        RubricCriteria(
            name="security_assessment_completed",
            llm_prompt=(
                "Does a complete security assessment exist with: threat analysis, vulnerability assessment, "
                "security controls, and formal approval sign-off? "
                "Return 10.0 if all components exist and approved, removing 2.0 for every missing component to a minimum of 0."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="legal_compliance_verified",
            llm_prompt=(
                "Does verified legal compliance documentation exist with: regulatory review, "
                "privacy impact assessment, terms of service updates "
                "Return 10.0 if all verified and approved, removing 4.0 for every missing component."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="production_deployment_ready",
            llm_prompt=(
                "Does production deployment readiness exist with: deployment procedures, "
                "rollback plans, infrastructure provisioning, and ops team sign-off? "
                "Return 10.0 if fully ready for production, 5 if there is a evidence of a clear plan with progress made but it is not complete, 0.0 otherwise."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Major deliverables (7 points each)
        RubricCriteria(
            name="product_specification_exists",
            llm_prompt=(
                "Does a product specification document exist with: feature requirements, "
                "user stories, acceptance criteria, and technical constraints? "
                "Return 7.0 if all components exist, removing 2.0 for every missing component to a minimum of 0.0."
            ),
            max_score=7.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="technical_architecture_documented",
            llm_prompt=(
                "Does technical architecture documentation exist with: system design, "
                "infrastructure requirements, API specifications, and integration points? "
                "Return 7.0 if comprehensive documentation exists, removing 2.0 for every missing component to a minimum of 0.0."
            ),
            max_score=7.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Important deliverables (5 points each)
        RubricCriteria(
            name="performance_benchmarks_established",
            llm_prompt=(
                "Do performance benchmarks exist with: baseline metrics, target thresholds, "
                "measurement methodology, and success criteria? "
                "Return 5.0 if complete benchmarks exist, removing 1.0 for every missing component to a minimum of 0.0."
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="user_acceptance_criteria_defined",
            llm_prompt=(
                "Do user acceptance criteria exist with: success metrics, user scenarios, "
                "testing procedures, and acceptance thresholds? "
                "Return true if complete criteria exist, false otherwise."
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="launch_timeline_with_milestones",
            llm_prompt=(
                "Does a launch timeline exist with: key milestones, dependencies, "
                "critical path, resource allocation, and delivery dates? "
                "Return true if detailed timeline exists, false otherwise."
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="success_metrics_established",
            llm_prompt=(
                "Do success metrics exist with: KPI definitions, measurement methods, "
                "target values, monitoring procedures, and reporting framework? "
                "Return true if complete metrics framework exists, false otherwise."
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Supporting deliverables (3 points each)
        RubricCriteria(
            name="development_environment_setup",
            llm_prompt=(
                "Does development environment setup exist with: development tools, "
                "testing frameworks, CI/CD pipelines, and developer documentation? "
                "Return 3.0 if environment if evidence of a clear plan with progress made, 0.0 otherwise."
            ),
            max_score=3.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="user_documentation_complete",
            llm_prompt=(
                "Does user documentation exist with: user guides, API documentation, "
                "troubleshooting guides, and support procedures? "
                "Return true if comprehensive documentation exists, false otherwise."
            ),
            max_score=3.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    return Rubric(
        name="genai_goal_achievement_eval",
        description="Concrete deliverable and milestone achievement measurement",
        aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
        criteria=goal_achievement_rubrics,
    )


def create_preference_update_requests() -> list[PreferenceWeightUpdateRequest]:
    """Build stakeholder weight update requests for the Gen-AI Feature Launch scenario.

    Converts the timeline of absolute weights into requests consumable by
    StakeholderAgent.apply_weight_updates.
    """
    timeline: dict[int, PreferenceSnapshot] = {
        0: PreferenceSnapshot(
            preferences=[
                Preference(
                    name="quality",
                    weight=0.5,
                    evaluator=Rubric(
                        name="ai_safety_quality_eval",
                        description="placeholder",
                        aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                        criteria=[],
                    ),
                ),
                Preference(
                    name="compliance",
                    weight=0.3,
                    evaluator=Rubric(
                        name="ai_compliance_eval",
                        description="placeholder",
                        aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                        criteria=[],
                    ),
                ),
                Preference(name="governance", weight=0.1),
                Preference(name="speed", weight=0.05),
                Preference(name="cost", weight=0.05),
            ]
        ),
        8: PreferenceSnapshot(
            preferences=[
                Preference(name="quality", weight=0.4),
                Preference(name="compliance", weight=0.3),
                Preference(name="governance", weight=0.15),
                Preference(name="speed", weight=0.1),
                Preference(name="cost", weight=0.05),
            ]
        ),
        15: PreferenceSnapshot(
            preferences=[
                Preference(name="quality", weight=0.35),
                Preference(name="compliance", weight=0.25),
                Preference(name="governance", weight=0.2),
                Preference(name="speed", weight=0.1),
                Preference(name="cost", weight=0.1),
            ]
        ),
        25: PreferenceSnapshot(
            preferences=[
                Preference(name="quality", weight=0.3),
                Preference(name="compliance", weight=0.2),
                Preference(name="governance", weight=0.25),
                Preference(name="speed", weight=0.15),
                Preference(name="cost", weight=0.1),
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
