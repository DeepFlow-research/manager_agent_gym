"""
Pharmaceutical Product Launch Demo

Real-world use case: Global pharmaceutical company launching new drug product.

Demonstrates:
- Sequential dependency management across 9 interconnected regulatory and manufacturing phases
- Safety-critical decision prioritization when regulatory compliance conflicts with commercial timelines
- Multi-stakeholder coordination across highly specialized domains (regulatory, quality, manufacturing, commercial)
- Long-horizon strategic planning with 10+ week critical path and complex approval gates
- Risk escalation and mitigation when patient safety signals or manufacturing deficiencies emerge
- Resource reallocation under strict regulatory constraints and budget pressures
"""

from examples.end_to_end_examples.standard_rules import (
    speed_rubric,
    cost_rubric,
)
from math import exp
from manager_agent_gym.schemas.preferences.preference import (
    Preference,
    PreferenceWeights,
)
from manager_agent_gym.schemas.preferences.evaluator import (
    Evaluator,
    AggregationStrategy,
)
from manager_agent_gym.schemas.core import Workflow
from manager_agent_gym.schemas.preferences.rubric import WorkflowRubric, RunCondition
from manager_agent_gym.schemas.preferences import PreferenceWeightUpdateRequest


def create_preferences() -> PreferenceWeights:
    # ---------------------------
    # Deterministic helper rules
    # ---------------------------
    def _safe_hours(delta_seconds: float) -> float:
        return max(0.0, float(delta_seconds)) / 3600.0

    # ---------------------------
    # Hardening Framework Functions
    # ---------------------------
    def _validate_cost_realism(workflow: Workflow, context) -> float:
        """Penalize unrealistic cost discrepancies for pharmaceutical launches."""
        expected_min_cost = 100000.0  # Minimum realistic cost
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
            return 0.0  # Pharma launches should cost >$100k

        cost_variance = abs(total_actual - total_estimated) / total_estimated
        if cost_variance > 0.4:
            return 0.2
        elif cost_variance > 0.2:
            return 0.6
        else:
            return 1.0

    def _pharma_adversarial_pressure_score(workflow: Workflow) -> float:
        """Score based on handling pharmaceutical adversarial pressure."""
        pressure_indicators = [
            "regulatory challenge",
            "fda objection",
            "safety concern",
            "efficacy question",
            "manufacturing issue",
            "supply chain disruption",
            "competitive threat",
            "patent challenge",
            "adverse event",
            "recall risk",
            "compliance violation",
            "inspection finding",
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
                            "corrected",
                        ]
                    ):
                        pressure_handled += 1
                    break

        return min(1.0, pressure_handled / max(1, len(pressure_indicators) * 0.3))

    def regulatory_compliance_indicators(workflow: Workflow) -> float:
        """Reward presence of regulatory compliance indicators and documentation (0..1)."""
        keywords = (
            "ectd",
            "ich",
            "fda",
            "ema",
            "cgmp",
            "validation",
            "dossier",
            "regulatory",
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

    def manufacturing_validation_density(workflow: Workflow) -> float:
        """Reward having manufacturing validation artifacts for completed tasks (0..1)."""
        completed = [
            t for t in workflow.tasks.values() if t.status.value == "completed"
        ]
        if not completed:
            return 0.0
        total_outputs = 0
        for t in completed:
            total_outputs += len(t.output_resource_ids)
        avg_outputs = total_outputs / max(1, len(completed))
        # Saturate at 3 outputs per task for manufacturing
        return max(0.0, min(1.0, avg_outputs / 3.0))

    def safety_monitoring_adherence(workflow: Workflow) -> float:
        """Penalty for duration overrun vs regulatory safety timeline estimates (0..1)."""
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
        return exp(-1.2 * over)  # Stricter than normal for safety-critical

    def patient_safety_progress(workflow: Workflow) -> float:
        """Progress proxy: completed safety-critical tasks vs total (0..1)."""
        safety_tasks = [
            t
            for t in workflow.tasks.values()
            if any(
                keyword in t.name.lower()
                for keyword in ["safety", "pharmacovigilance", "risk"]
            )
        ]
        if not safety_tasks:
            return 0.5
        completed_safety = len(
            [t for t in safety_tasks if t.status.value == "completed"]
        )
        return max(0.0, min(1.0, completed_safety / max(1, len(safety_tasks))))

    def manufacturing_cost_efficiency(workflow: Workflow) -> float:
        """Penalty for manufacturing cost overrun vs budget (0..1)."""
        budget = workflow.total_budget
        actual = workflow.total_cost
        if budget <= 0.0:
            return 0.5
        over = max(0.0, actual - budget) / budget
        return 1.0 / (1.0 + 2.0 * over)  # Stricter penalty for pharma cost overruns

    def quality_system_maturity(workflow: Workflow) -> float:
        """Reward QbD and quality system implementation indicators (0..1)."""
        qbd_keywords = (
            "qbd",
            "cqa",
            "cpp",
            "design space",
            "control strategy",
            "lifecycle",
        )
        recent = workflow.messages[-40:]
        if not recent:
            return 0.0
        hits = 0
        for m in recent:
            try:
                text = m.content.lower()
                if any(k in text for k in qbd_keywords):
                    hits += 1
            except Exception:
                continue
        return max(0.0, min(1.0, hits / max(1, len(recent))))

    def regulatory_governance_discipline(workflow: Workflow) -> float:
        """Proxy for regulatory governance: fraction of messages indicating regulatory approvals (0..1)."""
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
                        "approved",
                        "cleared",
                        "validated",
                        "qualified",
                        "signed off",
                        "certified",
                    )
                ):
                    hits += 1
            except Exception:
                continue
        return max(0.0, min(1.0, hits / max(1, len(recent))))

    def commercial_readiness_tracking(workflow: Workflow) -> float:
        """Track commercial readiness milestone completion (0..1)."""
        commercial_tasks = [
            t
            for t in workflow.tasks.values()
            if any(
                keyword in t.name.lower()
                for keyword in ["commercial", "market", "launch", "training"]
            )
        ]
        if not commercial_tasks:
            return 0.0
        completed_commercial = len(
            [t for t in commercial_tasks if t.status.value == "completed"]
        )
        return max(0.0, min(1.0, completed_commercial / max(1, len(commercial_tasks))))

    # ---------------------------
    # REGULATORY COMPLIANCE
    # ---------------------------
    regulatory_rubrics = [
        WorkflowRubric(
            name="ectd_dossier_completeness",
            llm_prompt=(
                """Evaluate eCTD dossier completeness and ICH compliance. Award partial credit for:
                (a) Module 3 (Quality) completeness with manufacturing and analytical data,
                (b) Module 4 (Nonclinical) safety data alignment with ICH guidelines,
                (c) Module 5 (Clinical) study reports and integrated summaries,
                (d) cross-module consistency and regulatory formatting.
                Cite specific workflow resources/messages for evidence. Output a numeric score in [0, 10]."""
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="regulatory_submission_quality",
            llm_prompt=(
                """Assess regulatory submission quality and agency readiness:
                FDA/EMA submission completeness, response to regulatory questions,
                inspection readiness, and regulatory correspondence management.
                Award partial credit with documentation citations. Output numeric score [0, 8]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="ich_guideline_adherence",
            llm_prompt=(
                """Evaluate adherence to ICH guidelines (Q8-Q11, M4):
                Quality by Design implementation, pharmaceutical development approach,
                lifecycle management principles, and regulatory harmonization.
                Output numeric score [0, 8]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="regulatory_compliance_tracking",
            evaluator_function=regulatory_compliance_indicators,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="regulatory_timeline_management",
            llm_prompt=(
                """
                Evaluate regulatory timeline management: submission milestones,
                agency interaction scheduling, inspection preparedness, approval pathway optimization.
                Provide partial credit per milestone achieved. Output numeric score [0, 6].
            """
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="multi_jurisdiction_coordination",
            llm_prompt=(
                "Score 0–6 for multi-jurisdictional coordination: FDA/EMA alignment, local authority submissions,"
                " regulatory strategy harmonization across regions. Award partial credit with coordination evidence."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # ---------------------------
    # MANUFACTURING QUALITY
    # ---------------------------
    manufacturing_rubrics = [
        WorkflowRubric(
            name="cgmp_compliance_validation",
            llm_prompt=(
                """Evaluate cGMP compliance and manufacturing validation. Award partial credit for:
                (a) Equipment qualification (IQ/OQ/PQ) completeness and documentation,
                (b) Process validation with three consecutive batches,
                (c) Analytical method validation per ICH Q2(R1),
                (d) Manufacturing readiness and inspection preparedness.
                Cite specific validation evidence. Output numeric score [0, 10]."""
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="qbd_implementation_depth",
            llm_prompt=(
                """Assess Quality by Design implementation depth:
                Critical Quality Attributes definition, Design Space establishment,
                Control Strategy development, and lifecycle management planning.
                Provide partial credit with QbD framework citations. Output numeric score [0, 8]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="manufacturing_process_control",
            llm_prompt=(
                """Evaluate manufacturing process control and consistency:
                Critical Process Parameters monitoring, batch-to-batch consistency,
                process capability demonstration, and control strategy implementation.
                Output numeric score [0, 8]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="manufacturing_validation_artifacts",
            evaluator_function=manufacturing_validation_density,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="quality_system_implementation",
            evaluator_function=quality_system_maturity,
            max_score=1.0,
            run_condition=RunCondition.EACH_TIMESTEP,
        ),
        WorkflowRubric(
            name="supply_chain_qualification",
            llm_prompt=(
                "Assess supply chain and distribution qualification: logistics partner validation,"
                " cold-chain integrity, serialization implementation, and distribution readiness."
                " Award partial credit with qualification evidence. Output numeric score [0, 6]."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # ---------------------------
    # PATIENT SAFETY
    # ---------------------------
    safety_rubrics = [
        WorkflowRubric(
            name="pharmacovigilance_system_robustness",
            llm_prompt=(
                """Evaluate pharmacovigilance system completeness and robustness:
                Risk Management Plan comprehensiveness, adverse event reporting infrastructure,
                signal detection protocols, and safety database functionality.
                Award partial credit across safety system components. Output numeric score [0, 10]."""
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="risk_management_effectiveness",
            llm_prompt=(
                """Assess risk management plan effectiveness and implementation:
                Safety concern identification, risk minimization measures,
                benefit-risk assessment, and post-market surveillance planning.
                Cite risk management documentation. Output numeric score [0, 8]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="safety_signal_preparedness",
            llm_prompt=(
                """Evaluate safety signal detection and management preparedness:
                Signal detection methodology, safety data review processes,
                regulatory communication protocols, and risk mitigation responsiveness.
                Output numeric score [0, 6]."""
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="patient_safety_prioritization",
            evaluator_function=patient_safety_progress,
            max_score=1.0,
            run_condition=RunCondition.EACH_TIMESTEP,
        ),
        WorkflowRubric(
            name="safety_timeline_adherence",
            evaluator_function=safety_monitoring_adherence,
            max_score=1.0,
            run_condition=RunCondition.EACH_TIMESTEP,
        ),
        WorkflowRubric(
            name="pharma_crisis_scenarios",
            llm_prompt=(
                """Evaluate handling of pharmaceutical crisis scenarios:
                - shows preparation for FDA regulatory challenges and objections
                - demonstrates response to safety concerns and adverse events
                - shows handling of manufacturing issues and supply chain disruptions
                - demonstrates preparation for competitive threats and patent challenges
                - shows recall risk management and compliance violation response
                Score 0 if no crisis scenarios addressed. Return score [0, 10]."""
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
    # COMMERCIAL READINESS
    # ---------------------------
    commercial_rubrics = [
        WorkflowRubric(
            name="market_access_strategy_quality",
            llm_prompt=(
                """Evaluate market access strategy development and execution:
                Health Technology Assessment submissions, payer value dossiers,
                pricing strategy development, and early access program implementation.
                Award partial credit across market access components. Output numeric score [0, 8]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="launch_readiness_preparation",
            llm_prompt=(
                """Assess commercial launch readiness and preparation quality:
                Commercial team training and certification, inventory staging,
                distribution network activation, and launch governance approval.
                Cite launch readiness evidence. Output numeric score [0, 6]."""
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="stakeholder_engagement_effectiveness",
            llm_prompt=(
                """Evaluate stakeholder engagement across the launch process:
                Regulatory agency communication, healthcare provider education,
                payer engagement, and patient advocacy coordination.
                Output numeric score [0, 6]."""
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="commercial_milestone_tracking",
            evaluator_function=commercial_readiness_tracking,
            max_score=1.0,
            run_condition=RunCondition.EACH_TIMESTEP,
        ),
    ]

    # ---------------------------
    # GOVERNANCE
    # ---------------------------
    governance_rubrics = [
        WorkflowRubric(
            name="cross_functional_governance",
            llm_prompt=(
                """Evaluate cross-functional governance effectiveness:
                Decision-making processes across regulatory, quality, safety, and commercial,
                escalation procedures, accountability frameworks, and board oversight.
                Award partial credit with governance evidence. Output numeric score [0, 8]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="regulatory_governance_discipline",
            evaluator_function=regulatory_governance_discipline,
            max_score=1.0,
            run_condition=RunCondition.EACH_TIMESTEP,
        ),
        WorkflowRubric(
            name="launch_gate_management",
            llm_prompt=(
                """Assess launch gate and milestone management:
                Gate criteria definition, approval processes, risk assessment at gates,
                and go/no-go decision documentation and rationale.
                Output numeric score [0, 6]."""
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # ---------------------------
    # SPEED
    # ---------------------------
    speed_rubrics = [
        WorkflowRubric(
            name="speed_efficiency",
            evaluator_function=speed_rubric,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="regulatory_timeline_optimization",
            llm_prompt=(
                "Assess regulatory timeline optimization and efficiency:"
                " critical path management, parallel processing utilization, regulatory milestone achievement."
                " Output numeric score [0, 6]."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="manufacturing_timeline_efficiency",
            llm_prompt=(
                "Evaluate manufacturing validation timeline efficiency:"
                " equipment qualification speed, validation batch execution, analytical method validation pace."
                " Output numeric score [0, 4]."
            ),
            max_score=4.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # ---------------------------
    # COST
    # ---------------------------
    cost_rubrics = [
        WorkflowRubric(
            name="cost_efficiency",
            evaluator_function=cost_rubric,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="manufacturing_cost_management",
            evaluator_function=manufacturing_cost_efficiency,
            max_score=1.0,
            run_condition=RunCondition.EACH_TIMESTEP,
        ),
        WorkflowRubric(
            name="regulatory_cost_optimization",
            llm_prompt=(
                "Assess regulatory and development cost optimization:"
                " consultant utilization efficiency, regulatory fee management, development cost control."
                " Output numeric score [0, 4]."
            ),
            max_score=4.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    return PreferenceWeights(
        preferences=[
            Preference(
                name="regulatory_compliance",
                weight=0.3,
                evaluator=Evaluator(
                    name="regulatory_compliance_eval",
                    description="regulatory compliance evaluator",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=regulatory_rubrics,
                ),
            ),
            Preference(
                name="manufacturing_quality",
                weight=0.25,
                evaluator=Evaluator(
                    name="manufacturing_quality_eval",
                    description="manufacturing quality evaluator",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=manufacturing_rubrics,
                ),
            ),
            Preference(
                name="patient_safety",
                weight=0.2,
                evaluator=Evaluator(
                    name="patient_safety_eval",
                    description="patient safety evaluator",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=safety_rubrics,
                ),
            ),
            Preference(
                name="commercial_readiness",
                weight=0.15,
                evaluator=Evaluator(
                    name="commercial_readiness_eval",
                    description="commercial readiness evaluator",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=commercial_rubrics,
                ),
            ),
            Preference(
                name="governance",
                weight=0.05,
                evaluator=Evaluator(
                    name="governance_eval",
                    description="governance evaluator",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=governance_rubrics,
                ),
            ),
            Preference(
                name="speed",
                weight=0.03,
                evaluator=Evaluator(
                    name="speed_eval",
                    description="speed evaluator",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=speed_rubrics,
                ),
            ),
            Preference(
                name="cost",
                weight=0.02,
                evaluator=Evaluator(
                    name="cost_eval",
                    description="cost evaluator",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=cost_rubrics,
                ),
            ),
        ]
    )


def create_preference_update_requests() -> list[PreferenceWeightUpdateRequest]:
    """
    Create dynamic preference timeline emphasizing different aspects during pharmaceutical launch:
    - Early: Manufacturing quality and regulatory preparation (foundation building)
    - Mid: Regulatory compliance and patient safety (submission phase)
    - Late: Commercial readiness and speed (launch execution)
    """
    timeline = {
        10: PreferenceWeights(
            preferences=[
                Preference(name="regulatory_compliance", weight=0.25),
                Preference(name="manufacturing_quality", weight=0.35),
                Preference(name="patient_safety", weight=0.25),
                Preference(name="commercial_readiness", weight=0.1),
                Preference(name="governance", weight=0.03),
                Preference(name="speed", weight=0.01),
                Preference(name="cost", weight=0.01),
            ]
        ),
        25: PreferenceWeights(
            preferences=[
                Preference(name="regulatory_compliance", weight=0.4),
                Preference(name="manufacturing_quality", weight=0.2),
                Preference(name="patient_safety", weight=0.25),
                Preference(name="commercial_readiness", weight=0.1),
                Preference(name="governance", weight=0.03),
                Preference(name="speed", weight=0.01),
                Preference(name="cost", weight=0.01),
            ]
        ),
        40: PreferenceWeights(
            preferences=[
                Preference(name="regulatory_compliance", weight=0.3),
                Preference(name="manufacturing_quality", weight=0.15),
                Preference(name="patient_safety", weight=0.2),
                Preference(name="commercial_readiness", weight=0.25),
                Preference(name="governance", weight=0.05),
                Preference(name="speed", weight=0.03),
                Preference(name="cost", weight=0.02),
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
    """Create goal achievement evaluator for pharmaceutical product launch with regulatory focus."""
    goal_achievement_rubrics = [
        # Critical regulatory deliverables (absolutely must have for drug approval)
        WorkflowRubric(
            name="ectd_regulatory_dossier_submitted",
            llm_prompt=(
                "Does submitted eCTD regulatory dossier exist with: complete modules (quality, safety, nonclinical, clinical), "
                "FDA/EMA submission confirmed, ICH guidelines (Q8-Q11, M4) compliance, and formal agency acceptance received? "
                "Return 20.0 if there is evidence of an eCTD dossier being submitted and accepted, "
                "10.0 if there is evidence of any of the following: eCTD dossier being submitted but it is not complete, "
                "FDA/EMA submission is planned and completed but not confirmed, "
                "ICH guidelines (Q8-Q11, M4) are shown to be compliant, "
                "formal agency acceptance not received, "
                "0.0 otherwise."
            ),
            max_score=20.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="cgmp_manufacturing_validated",
            llm_prompt=(
                "Does validated cGMP manufacturing exist with: external audit reports completed, "
                "IQ/OQ/PQ equipment qualification documented, lot release procedures validated, and no unresolved major observations? "
                "Return 18.0 if there is evidence of cGMP manufacturing being validated and audit-ready, "
                "10.0 if there is evidence of any of the following: external audit reports completed but not yet received, "
                "IQ/OQ/PQ equipment qualification documented but not yet received, "
                "lot release procedures validated but not yet received, "
                "unresolved major observations, "
                "0.0 otherwise."
            ),
            max_score=18.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="qbd_framework_documented",
            llm_prompt=(
                "Does documented QbD (Quality by Design) framework exist with: critical quality attributes (CQAs) defined, "
                "critical process parameters (CPPs) established, control strategy implemented, and reproducibility demonstrated across validation batches? "
                "Return 15.0 if there is evidence of a QbD framework being documented and validated, "
                "10.0 if there is evidence of any of the following: critical quality attributes (CQAs) defined but not yet received, "
                "critical process parameters (CPPs) established, "
                "control strategy implemented, "
                "reproducibility demonstrated across validation batches, "
                "0.0 otherwise."
            ),
            max_score=15.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="pharmacovigilance_system_operational",
            llm_prompt=(
                "Does operational pharmacovigilance system exist with: safety management plan active, "
                "adverse event reporting pathways established, signal detection protocols implemented, and risk minimization measures documented? "
                "Return 15.0 if there is evidence of a pharmacovigilance system being operational with all conditions met, "
                "10.0 if there is evidence of any of the following: safety management plan active, "
                "adverse event reporting pathways established, "
                "signal detection protocols implemented, "
                "risk minimization measures documented, "
                "0.0 otherwise."
            ),
            max_score=15.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Major compliance and commercial deliverables (10-12 points each)
        WorkflowRubric(
            name="plair_commercial_authorization",
            llm_prompt=(
                "Does PLAIR (Pre-Launch Activities Importation Request) authorization exist with: "
                "FDA/EMA commercial staging approval, product import clearance, and commercial release readiness confirmed? "
                "Return 12.0 if there is evidence of a PLAIR authorization being secured, "
                "10.0 if there is evidence of any of the following: FDA/EMA commercial staging approval, "
                "product import clearance, "
                "commercial release readiness confirmed, "
                "0.0 otherwise."
            ),
            max_score=12.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="market_access_strategy_approved",
            llm_prompt=(
                "Does approved market access strategy exist with: payer dossiers completed, "
                "HTA submissions filed, pricing models validated, and early access programs operational? "
                "Return 12.0 if there is evidence of a market access strategy being approved, "
                "5.0 if there is evidence of any of the following: payer dossiers completed, "
                "HTA submissions filed, "
                "pricing models validated, "
                "early access programs operational, "
                "0.0 otherwise."
            ),
            max_score=12.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="supply_chain_readiness_validated",
            llm_prompt=(
                "Does validated supply chain readiness exist with: logistics partners qualified, "
                "cold-chain testing completed, serialization/track-and-trace compliance operational, and inventory ramp-up executed? "
                "Return 10.0 if there is evidence of supply chain being validated and ready, "
                "5.0 if there is evidence of any of the following: logistics partners qualified, "
                "cold-chain testing completed, "
                "serialization/track-and-trace compliance operational, "
                "inventory ramp-up executed, " 
                "0.0 otherwise."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="governance_sign_offs_secured",
            llm_prompt=(
                "Do secured governance sign-offs exist with: Regulatory Affairs approval, Quality approval, "
                "Pharmacovigilance approval, Commercial approval, and Executive Board authorization documented? "
                "Return true if all governance sign-offs are secured, false otherwise."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="regulatory_correspondence_documented",
            llm_prompt=(
                "Does documented regulatory correspondence exist with: FDA/EMA communication logs, "
                "agency feedback responses, deficiency resolution tracking, and first cycle review progress confirmed? "
                "Return true if regulatory correspondence is documented, false otherwise."
            ),
            max_score=7.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Important supporting deliverables (6-8 points each)
        WorkflowRubric(
            name="clinical_data_package_complete",
            llm_prompt=(
                "Does complete clinical data package exist with: efficacy endpoints met, "
                "safety profile characterized, statistical analysis plan executed, and clinical study report finalized? "
                "Return 8.0 if clinical data package is complete, 3.0 if it is planned or partially complete but not finalized, 0.0 otherwise."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="analytical_method_validation",
            llm_prompt=(
                "Does analytical method validation exist with: assay validation completed, "
                "method transfer documented, stability studies finalized, and release testing protocols established? "
                "Return 8.0 if analytical methods are validated, 3.0 if it is planned or partially complete but not finalized, 0.0 otherwise."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="lifecycle_monitoring_plan",
            llm_prompt=(
                "Does lifecycle monitoring plan exist with: post-market surveillance strategy, "
                "continued process verification protocols, change control procedures, and lifecycle stage gates defined? "
                "Return 6.0 if lifecycle monitoring plan is operational, 3.0 if it is planned or partially complete but not finalized, 0.0 otherwise."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Supporting deliverables (3-5 points each)
        WorkflowRubric(
            name="decision_logs_maintained",
            llm_prompt=(
                "Do maintained decision logs exist with: launch readiness reviews documented, "
                "critical decision rationales captured, risk-benefit assessments recorded, and accountability trails established? "
                "Return 5.0 if decision logs are maintained, 3.0 if it is planned or partially complete but not finalized, 0.0 otherwise."
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="batch_release_procedures",
            llm_prompt=(
                "Do batch release procedures exist with: release testing protocols validated, "
                "certificate of analysis templates approved, batch disposition criteria established, and quality person authorization documented? "
                "Return 4.0 if batch release procedures are established, 2.0 if it is planned or partially complete but not finalized, 0.0 otherwise."
            ),
            max_score=4.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="launch_readiness_assessment",
            llm_prompt=(
                "Does launch readiness assessment exist with: cross-functional readiness confirmed, "
                "go/no-go criteria evaluated, launch timeline validated, and stakeholder alignment documented? "
                "Return 4.0 if launch readiness assessment is complete, 2.0 if it is planned or partially complete but not finalized, 0.0 otherwise."
            ),
            max_score=4.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="regulatory_agency_feedback_incorporation",
            llm_prompt=(
                "Does regulatory agency feedback incorporation exist with: FDA/EMA guidance integrated, "
                "comment responses submitted, deficiency remediation completed, and approval pathway confirmed? "
                "Return 3.0 if agency feedback is incorporated, 1.0 if it is planned or partially complete but not finalized, 0.0 otherwise."
            ),
            max_score=3.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    return Evaluator(
        name="pharma_product_launch_goal_achievement_eval",
        description="Pharmaceutical product launch regulatory and commercial deliverable achievement measurement",
        aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
        rubrics=goal_achievement_rubrics,
    )
