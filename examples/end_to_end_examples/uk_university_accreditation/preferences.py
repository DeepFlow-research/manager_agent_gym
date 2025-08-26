"""
UK University Accreditation Renewal Demo

Real-world use case: Mid-size UK university OfS registration renewal.

Demonstrates:
- Multi-stakeholder regulatory compliance coordination across diverse functional areas
- Sequential dependency management with parallel track execution for efficiency
- Risk-based governance oversight with escalation management under regulatory deadlines
- Evidence-based compliance documentation with quality assurance validation
- Cross-functional team coordination between academic, administrative, and external stakeholders
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
        """Penalize unrealistic cost discrepancies for university accreditation."""
        expected_min_cost = 35000.0  # Minimum realistic cost
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
            return 0.0  # University accreditation should cost >$35k

        cost_variance = abs(total_actual - total_estimated) / total_estimated
        if cost_variance > 0.3:
            return 0.2
        elif cost_variance > 0.15:
            return 0.6
        else:
            return 1.0

    def _university_adversarial_pressure_score(workflow: Workflow) -> float:
        """Score based on handling university accreditation adversarial pressure."""
        pressure_indicators = [
            "ofs challenge",
            "regulatory concern",
            "academic standard dispute",
            "compliance gap",
            "student complaint",
            "faculty resistance",
            "resource shortfall",
            "timeline pressure",
            "assessment failure",
            "accreditation risk",
            "quality concern",
            "funding threat",
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
                            "improved",
                            "corrected",
                        ]
                    ):
                        pressure_handled += 1
                    break

        return min(1.0, pressure_handled / max(1, len(pressure_indicators) * 0.3))

    def regulatory_evidence_density(workflow: Workflow) -> float:
        """Reward presence of regulatory evidence and compliance documentation (0..1)."""
        keywords = (
            "evidence",
            "compliance",
            "ofs",
            "regulatory",
            "documentation",
            "audit",
            "validation",
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

    def academic_quality_artifacts(workflow: Workflow) -> float:
        """Reward having quality-related artifacts for completed tasks (0..1)."""
        completed = [
            t for t in workflow.tasks.values() if t.status.value == "completed"
        ]
        if not completed:
            return 0.0
        quality_keywords = (
            "external examiner",
            "kpi",
            "standards",
            "assessment",
            "quality",
        )
        quality_outputs = 0
        total_outputs = 0
        for t in completed:
            for res_id in t.output_resource_ids:
                if res_id in workflow.resources:
                    total_outputs += 1
                    try:
                        content = (workflow.resources[res_id].content or "").lower()
                        if any(k in content for k in quality_keywords):
                            quality_outputs += 1
                    except Exception:
                        continue
        if total_outputs == 0:
            return 0.0
        return max(0.0, min(1.0, quality_outputs / max(1, total_outputs)))

    def accreditation_deadline_adherence(workflow: Workflow) -> float:
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
        return exp(-1.0 * over)  # Slightly more forgiving than ICAP

    def governance_approval_tracking(workflow: Workflow) -> float:
        """Track presence of governance approvals and sign-offs (0..1)."""
        recent = workflow.messages[-100:]  # Look at more messages for approvals
        if not recent:
            return 0.0
        hits = 0
        approval_terms = (
            "approved",
            "signed off",
            "council",
            "senate",
            "committee",
            "governance",
            "authorization",
        )
        for m in recent:
            try:
                text = m.content.lower()
                if any(k in text for k in approval_terms):
                    hits += 1
            except Exception:
                continue
        return max(0.0, min(1.0, hits / max(1, len(recent))))

    def student_protection_coverage(workflow: Workflow) -> float:
        """Assess coverage of student protection requirements (0..1)."""
        protection_keywords = (
            "student protection",
            "consumer law",
            "cma",
            "transparency",
            "unfair terms",
        )
        total = 0
        hits = 0
        for res in workflow.resources.values():
            total += 1
            try:
                content = (res.content or "").lower()
                if any(k in content for k in protection_keywords):
                    hits += 1
            except Exception:
                continue
        if total == 0:
            return 0.0
        return min(1.0, hits / max(1, total))

    def data_quality_validation_presence(workflow: Workflow) -> float:
        """Check for presence of data quality validation evidence (0..1)."""
        validation_keywords = (
            "hesa",
            "data quality",
            "validation",
            "audit",
            "integrity",
            "accuracy",
        )
        total = 0
        hits = 0
        for res in workflow.resources.values():
            total += 1
            try:
                content = (res.content or "").lower()
                if any(k in content for k in validation_keywords):
                    hits += 1
            except Exception:
                continue
        if total == 0:
            return 0.0
        return min(1.0, hits / max(1, total))

    def stakeholder_coordination_efficiency(workflow: Workflow) -> float:
        """Measure efficiency of cross-functional coordination (0..1)."""
        coordination_keywords = (
            "coordination",
            "stakeholder",
            "cross-functional",
            "committee",
            "steering",
        )
        recent = workflow.messages[-50:]
        if not recent:
            return 0.0
        hits = 0
        for m in recent:
            try:
                text = m.content.lower()
                if any(k in text for k in coordination_keywords):
                    hits += 1
            except Exception:
                continue
        return max(0.0, min(1.0, hits / max(1, len(recent))))

    # ---------------------------
    # ACADEMIC QUALITY & STANDARDS
    # ---------------------------
    academic_quality_rubrics = [
        WorkflowRubric(
            name="b_conditions_compliance_evidence",
            llm_prompt=(
                """Evaluate compliance evidence against OfS B-conditions (B1-B6). Award partial credit for:
                (a) course cluster mapping to standards requirements,
                (b) external examiner report integration and analysis,
                (c) student outcome KPIs (continuation, completion, progression),
                (d) enhancement plans for underperforming areas.
                Cite specific workflow resources/messages for evidence. Output a numeric score in [0, 10]."""
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="external_examiner_synthesis_quality",
            llm_prompt=(
                """Assess quality of external examiner report synthesis and trend analysis.
                Look for systematic analysis, identification of patterns, and action planning.
                Penalize superficial or incomplete analysis. Output a numeric score in [0, 6]."""
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="student_outcome_analysis_depth",
            llm_prompt=(
                """Evaluate depth of student outcome analysis: (1) KPI benchmarking against sector,
                (2) identification of improvement areas, (3) evidence-based enhancement planning.
                Award equal partial credit. Cite evidence. Output numeric score [0, 8]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="academic_standards_validation",
            llm_prompt=(
                """Assess academic standards validation against sector benchmarks and regulatory expectations.
                Look for systematic comparison, gap identification, and remediation strategies.
                Output numeric score [0, 7]."""
            ),
            max_score=7.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="quality_artifact_density",
            evaluator_function=academic_quality_artifacts,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # ---------------------------
    # REGULATORY COMPLIANCE
    # ---------------------------
    regulatory_compliance_rubrics = [
        WorkflowRubric(
            name="ofs_conditions_mapping_completeness",
            llm_prompt=(
                """Evaluate mapping of institutional activities to OfS conditions A-E. Award partial credit for: coverage,
                evidence quality (citations), accountability framework alignment, and explicit compliance gaps/mitigations.
                Output numeric score [0, 10]."""
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="consumer_law_compliance_thoroughness",
            llm_prompt=(
                """Assess CMA consumer law compliance review: prospectus accuracy, contract fairness, cost transparency,
                and student rights protection. Award partial credit with citations. Output numeric score [0, 10]."""
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="ukvi_sponsorship_compliance_validation",
            llm_prompt=(
                """Evaluate UKVI sponsor licence compliance validation: attendance monitoring systems,
                CAS management processes, reporting protocol adherence, and compliance audit evidence.
                Award partial credit with citations. Output numeric score [0, 8]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="prevent_duty_compliance_evidence",
            llm_prompt=(
                """Assess Prevent duty compliance documentation: risk assessment currency, training coverage analysis,
                incident management protocols, and governing body oversight evidence.
                Provide partial credit with citations. Output numeric score [0, 8]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="data_protection_and_quality_controls",
            llm_prompt=(
                """Evaluate data protection and quality controls: GDPR compliance evidence, HESA data validation,
                internal audit processes, and data integrity assurance measures.
                Output numeric score [0, 9]."""
            ),
            max_score=9.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="regulatory_evidence_density",
            evaluator_function=regulatory_evidence_density,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="student_protection_coverage",
            evaluator_function=student_protection_coverage,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # ---------------------------
    # GOVERNANCE & OVERSIGHT
    # ---------------------------
    governance_rubrics = [
        WorkflowRubric(
            name="governance_structure_effectiveness",
            llm_prompt=(
                """Evaluate governance structure effectiveness: steering committee formation, role clarity,
                accountability framework, and decision-making processes. Award partial credit with citations.
                Output numeric score [0, 9]."""
            ),
            max_score=9.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="access_participation_governance_oversight",
            llm_prompt=(
                """Assess governance oversight of Access & Participation Plan: monitoring data analysis,
                gap identification, intervention strategy development, and governing body engagement.
                Output numeric score [0, 8]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="financial_sustainability_governance",
            llm_prompt=(
                """Evaluate governance of financial sustainability assessment: scenario planning oversight,
                risk management integration, and student protection plan governance.
                Partial credit with citations. Output numeric score [0, 7]."""
            ),
            max_score=7.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="evidence_consolidation_oversight",
            llm_prompt=(
                """Assess oversight of evidence consolidation and submission process: quality assurance,
                approval workflows, and submission readiness validation.
                Output numeric score [0, 6]."""
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="governance_approval_tracking",
            evaluator_function=governance_approval_tracking,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="stakeholder_coordination_efficiency",
            evaluator_function=stakeholder_coordination_efficiency,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # ---------------------------
    # DATA QUALITY & INTEGRITY
    # ---------------------------
    data_quality_rubrics = [
        WorkflowRubric(
            name="hesa_data_validation_thoroughness",
            llm_prompt=(
                """Evaluate HESA Data Futures validation thoroughness: accuracy checks, completeness validation,
                consistency analysis, and error correction processes. Award partial credit.
                Output numeric score [0, 8]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="internal_audit_quality_controls",
            llm_prompt=(
                """Assess internal audit quality controls: data collection validation, processing integrity checks,
                control effectiveness assessment, and audit trail documentation.
                Cite evidence. Output numeric score [0, 7]."""
            ),
            max_score=7.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="data_integrity_assurance_strength",
            llm_prompt=(
                """Evaluate data integrity assurance measures: senior officer attestations, validation procedures,
                error detection mechanisms, and correction protocols. Output numeric score [0, 6]."""
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="data_quality_validation_presence",
            evaluator_function=data_quality_validation_presence,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # ---------------------------
    # SPEED
    # ---------------------------
    speed_rubrics = [
        # Deterministic
        WorkflowRubric(
            name="accreditation_deadline_adherence",
            evaluator_function=accreditation_deadline_adherence,
            max_score=1.0,
            run_condition=RunCondition.EACH_TIMESTEP,
        ),
        WorkflowRubric(
            name="evidence_compilation_efficiency",
            llm_prompt=(
                """Evaluate efficiency of evidence compilation process: parallel track execution,
                dependency management, and milestone achievement. Cite evidence.
                Output numeric score [0, 6]."""
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="regulatory_submission_timeliness",
            llm_prompt=(
                """Assess timeliness of regulatory submission preparation and quality assurance processes.
                Look for proactive timeline management and early issue identification.
                Output numeric score [0, 5]."""
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
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
        WorkflowRubric(
            name="cost_efficiency",
            evaluator_function=cost_rubric,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="compliance_cost_optimization",
            llm_prompt=(
                """Assess compliance cost optimization: efficient use of internal resources vs external consultants,
                technology leveraging for efficiency, and cost-benefit analysis of compliance activities.
                Cite evidence. Output numeric score [0, 6]."""
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="resource_allocation_effectiveness",
            llm_prompt=(
                """Evaluate resource allocation effectiveness across compliance workstreams:
                staff utilization, external support justification, and timeline-cost trade-offs.
                Output numeric score [0, 5]."""
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="university_crisis_scenarios",
            llm_prompt=(
                """Evaluate handling of university accreditation crisis scenarios:
                - shows preparation for OFS challenges and regulatory concerns
                - demonstrates response to academic standard disputes and compliance gaps
                - shows handling of student complaints and faculty resistance
                - demonstrates preparation for resource shortfalls and timeline pressure
                - shows contingency planning for assessment failures and accreditation risks
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

    return PreferenceWeights(
        preferences=[
            Preference(
                name="academic_quality",
                weight=0.25,
                evaluator=Evaluator(
                    name="academic_quality_eval",
                    description="academic quality and standards evaluator",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=academic_quality_rubrics,
                ),
            ),
            Preference(
                name="regulatory_compliance",
                weight=0.3,
                evaluator=Evaluator(
                    name="regulatory_compliance_eval",
                    description="regulatory compliance evaluator",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=regulatory_compliance_rubrics,
                ),
            ),
            Preference(
                name="governance",
                weight=0.2,
                evaluator=Evaluator(
                    name="governance_eval",
                    description="governance and oversight evaluator",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=governance_rubrics,
                ),
            ),
            Preference(
                name="data_quality",
                weight=0.15,
                evaluator=Evaluator(
                    name="data_quality_eval",
                    description="data quality and integrity evaluator",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=data_quality_rubrics,
                ),
            ),
            Preference(
                name="speed",
                weight=0.06,
                evaluator=Evaluator(
                    name="speed_eval",
                    description="speed and timeliness evaluator",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=speed_rubrics,
                ),
            ),
            Preference(
                name="cost",
                weight=0.04,
                evaluator=Evaluator(
                    name="cost_eval",
                    description="cost efficiency evaluator",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=cost_rubrics,
                ),
            ),
        ]
    )


def create_preference_update_requests() -> list[PreferenceWeightUpdateRequest]:
    """Build stakeholder weight update requests for the UK University Accreditation scenario.

    Timeline shifts from initial setup and evidence gathering to regulatory compliance
    focus as submission deadline approaches.
    """
    timeline: dict[int, PreferenceWeights] = {
        0: PreferenceWeights(
            preferences=[
                Preference(
                    name="academic_quality",
                    weight=0.3,
                    evaluator=Evaluator(
                        name="academic_quality_eval",
                        description="placeholder",
                        aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                        rubrics=[],
                    ),
                ),
                Preference(
                    name="regulatory_compliance",
                    weight=0.2,
                    evaluator=Evaluator(
                        name="regulatory_compliance_eval",
                        description="placeholder",
                        aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                        rubrics=[],
                    ),
                ),
                Preference(name="governance", weight=0.2),
                Preference(name="data_quality", weight=0.2),
                Preference(name="speed", weight=0.05),
                Preference(name="cost", weight=0.05),
            ]
        ),
        10: PreferenceWeights(
            preferences=[
                Preference(name="academic_quality", weight=0.25),
                Preference(name="regulatory_compliance", weight=0.3),
                Preference(name="governance", weight=0.2),
                Preference(name="data_quality", weight=0.15),
                Preference(name="speed", weight=0.06),
                Preference(name="cost", weight=0.04),
            ]
        ),
        20: PreferenceWeights(
            preferences=[
                Preference(name="academic_quality", weight=0.2),
                Preference(name="regulatory_compliance", weight=0.4),
                Preference(name="governance", weight=0.15),
                Preference(name="data_quality", weight=0.15),
                Preference(name="speed", weight=0.06),
                Preference(name="cost", weight=0.04),
            ]
        ),
        30: PreferenceWeights(
            preferences=[
                Preference(name="academic_quality", weight=0.15),
                Preference(name="regulatory_compliance", weight=0.5),
                Preference(name="governance", weight=0.15),
                Preference(name="data_quality", weight=0.1),
                Preference(name="speed", weight=0.07),
                Preference(name="cost", weight=0.03),
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
    """Create goal achievement evaluator for UK University OfS accreditation renewal process."""
    goal_achievement_rubrics = [
        # Critical OfS compliance deliverables (must have for registration renewal)
        WorkflowRubric(
            name="ofs_evidence_pack_submitted_compliant",
            llm_prompt=(
                "Does submitted compliant OfS evidence pack exist with: evidence pack submitted on time, "
                "no material deficiencies identified, ≤2 rounds of regulator clarifications, and OfS conditions A-E addressed comprehensively? "
                "Return: 20.0 if all conditions are met, removing 2 for every condition not met to a minimum of 0.0."
            ),
            max_score=20.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="quality_standards_compliance_b_conditions",
            llm_prompt=(
                "Does quality standards compliance with B-conditions exist with: course clusters mapped to B1-B6 conditions, "
                "external examiner summaries provided, continuation/completion/progression KPIs met, and remediation actions documented? "
                "Return 18.0 if all conditions are met, removing 2 for every condition not met to a minimum of 0.0. Return 5.0 if there is evidence of any of these being planned but not yet completed."
            ),
            max_score=18.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="cma_consumer_law_compliance_audit",
            llm_prompt=(
                "Does CMA consumer law compliance audit exist with: CMA-compliant prospectus and contracts confirmed, "
                "clear/fair/transparent information verified, legal review completed, and no unresolved unfair terms findings? "
                "Return 15.0 if all conditions are met, removing 2 for every condition not met to a minimum of 0.0. Return 5.0 if there is evidence of any of these being planned but not yet completed."
            ),
            max_score=15.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="app_accepted_ofs_valid_credible",
            llm_prompt=(
                "Does OfS-accepted APP exist with: Access and Participation Plan updated, "
                "monitoring data provided, gap analysis completed, OfS acceptance as valid and credible confirmed? "
                "Return true if APP is OfS-accepted as valid and credible, false otherwise."
            ),
            max_score=12.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Major regulatory and governance deliverables (8-10 points each)
        WorkflowRubric(
            name="ukvi_sponsorship_compliance_maintained",
            llm_prompt=(
                "Does maintained UKVI sponsorship compliance exist with: attendance monitoring records current, "
                "CAS issuance logs documented, reporting evidence provided, and sponsor license maintained without major findings? "
                "Return true if UKVI sponsorship compliance is maintained, false otherwise."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="prevent_duty_documentation_compliant",
            llm_prompt=(
                "Does compliant Prevent duty documentation exist with: risk assessment completed, "
                "training coverage documented, incident logs maintained, and governing-body oversight consistent with OfS monitoring? "
                "Return true if Prevent duty documentation is compliant, false otherwise."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="governance_package_decisions_documented",
            llm_prompt=(
                "Does documented governance package with decisions exist with: Council/Senate/Quality Committee minutes complete, "
                "oversight decisions documented, sign-offs secured, and risk registers/escalation logs maintained? "
                "Return true if governance package with decisions is documented, false otherwise."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="data_quality_assurance_hesa_validated",
            llm_prompt=(
                "Does HESA-validated data quality assurance exist with: HESA Data Futures submissions validated, "
                "internal audit checks completed, data integrity statements signed, and data quality confirmed? "
                "Return true if data quality assurance is HESA-validated, false otherwise."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="student_outcomes_tef_aligned",
            llm_prompt=(
                "Does TEF-aligned student outcomes narrative exist with: Teaching Excellence Framework indicators addressed, "
                "continuous improvement evidence provided, student outcomes narrative compelling, and TEF alignment demonstrated? "
                "Return true if student outcomes are TEF-aligned, false otherwise."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Important supporting deliverables (5-7 points each)
        WorkflowRubric(
            name="financial_sustainability_evidence",
            llm_prompt=(
                "Does financial sustainability evidence exist with: financial sustainability demonstrated, "
                "financial projections validated, sustainability metrics met, and financial governance robust? "
                "Return true if financial sustainability evidence is compelling, false otherwise."
            ),
            max_score=7.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="student_protection_measures_documented",
            llm_prompt=(
                "Do documented student protection measures exist with: student protection plan current, "
                "protection measures operational, student interests safeguarded, and protection compliance demonstrated? "
                "Return true if student protection measures are documented, false otherwise."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="external_examiner_summaries_validated",
            llm_prompt=(
                "Do validated external examiner summaries exist with: external examiner reports comprehensive, "
                "quality assurance validation completed, academic standards confirmed, and examiner feedback addressed? "
                "Return true if external examiner summaries are validated, false otherwise."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="equality_opportunity_governance_oversight",
            llm_prompt=(
                "Does equality opportunity governance oversight exist with: equality of opportunity monitored, "
                "governance oversight demonstrated, gap analysis completed, and diversity metrics tracked? "
                "Return true if equality opportunity governance oversight is effective, false otherwise."
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="academic_standards_baseline_compliance",
            llm_prompt=(
                "Does academic standards baseline compliance exist with: academic standards maintained, "
                "baseline requirements met, quality thresholds achieved, and standards governance operational? "
                "Return true if academic standards baseline compliance is demonstrated, false otherwise."
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Supporting deliverables (3-4 points each)
        WorkflowRubric(
            name="course_information_transparency",
            llm_prompt=(
                "Does course information transparency exist with: course information clear and accurate, "
                "costs and contact hours transparent, student information accessible, and transparency standards met? "
                "Return true if course information transparency is achieved, false otherwise."
            ),
            max_score=4.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="regulatory_correspondence_tracking",
            llm_prompt=(
                "Does regulatory correspondence tracking exist with: OfS communications logged, "
                "regulator interactions documented, compliance correspondence maintained, and response tracking active? "
                "Return true if regulatory correspondence tracking is comprehensive, false otherwise."
            ),
            max_score=4.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="continuous_improvement_initiatives",
            llm_prompt=(
                "Do continuous improvement initiatives exist with: improvement initiatives identified and implemented, "
                "enhancement activities documented, quality development ongoing, and improvement culture demonstrated? "
                "Return true if continuous improvement initiatives are active, false otherwise."
            ),
            max_score=3.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="sector_benchmarking_alignment",
            llm_prompt=(
                "Does sector benchmarking alignment exist with: sector benchmarks analyzed, "
                "performance compared to peers, best practices identified, and sector alignment demonstrated? "
                "Return true if sector benchmarking alignment is established, false otherwise."
            ),
            max_score=3.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    return Evaluator(
        name="uk_university_accreditation_goal_achievement_eval",
        description="UK University OfS accreditation renewal process deliverable achievement measurement",
        aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
        rubrics=goal_achievement_rubrics,
    )
