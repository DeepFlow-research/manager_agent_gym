from math import exp

from manager_agent_gym.schemas.preferences.preference import (
    Preference,
    PreferenceWeights,
)
from manager_agent_gym.schemas.preferences.evaluator import (
    Evaluator,
    AggregationStrategy,
)
from manager_agent_gym.schemas.preferences.rubric import WorkflowRubric, RunCondition
from manager_agent_gym.schemas.core.workflow import Workflow
from manager_agent_gym.schemas.preferences import PreferenceWeightUpdateRequest


def create_preferences() -> PreferenceWeights:
    # ---------------------------
    # Deterministic helper rules (smooth, 0..1)
    # ---------------------------
    def _ratio(a: float, b: float) -> float:
        return 0.0 if b <= 0 else max(0.0, min(1.0, a / b))

    def _exp_penalty(r: float, alpha: float = 1.0) -> float:
        return exp(-alpha * max(0.0, r))

    # ---------------------------
    # Hardening Framework Functions
    # ---------------------------
    def _validate_cost_realism(workflow: Workflow, context) -> float:
        """Penalize unrealistic cost discrepancies for legal negotiations."""
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
            return 0.0
        if total_actual < expected_min_cost:
            return 0.0  # Legal negotiations should cost >$25k

        cost_variance = abs(total_actual - total_estimated) / total_estimated
        if cost_variance > 0.3:
            return 0.2
        elif cost_variance > 0.15:
            return 0.6
        else:
            return 1.0

    def _require_external_validation(
        workflow: Workflow, validation_keywords: list[str]
    ) -> float:
        """Require evidence of external validation for legal matters."""
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

        return min(1.0, validation_evidence / max(1, total_tasks * 0.25))

    def _legal_adversarial_pressure_score(workflow: Workflow) -> float:
        """Score based on handling legal adversarial pressure and challenges."""
        pressure_indicators = [
            "counterparty objection",
            "legal challenge",
            "compliance dispute",
            "regulatory inquiry",
            "contract dispute",
            "liability concern",
            "indemnity pushback",
            "term negotiation",
            "deadline pressure",
            "deal breakage risk",
            "escalation",
            "litigation threat",
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
                            "agreed",
                        ]
                    ):
                        pressure_handled += 1
                    break

        return min(1.0, pressure_handled / max(1, len(pressure_indicators) * 0.3))

    def resp_time_to_first_redline(workflow: Workflow) -> float:
        """Proxy for time-to-first-meaningful output: first completed subtask vs expected hours."""
        if workflow.started_at is None:
            return 0.5
        completed_times = [
            t.completed_at for t in workflow.tasks.values() if t.completed_at
        ]
        if not completed_times:
            return 0.0
        first_done = min(completed_times)
        elapsed_h = (
            max(0.0, (first_done - workflow.started_at).total_seconds()) / 3600.0
        )
        expected_h = (
            workflow.total_expected_hours if workflow.total_expected_hours > 0 else 12.0
        )
        return _exp_penalty(elapsed_h / max(1e-6, expected_h), alpha=1.2)

    def throughput_progress(workflow: Workflow) -> float:
        total = len(workflow.tasks)
        completed = len(
            [t for t in workflow.tasks.values() if t.status.value == "completed"]
        )
        return _ratio(completed, max(1, total))

    def blocked_deadtime_penalty(workflow: Workflow) -> float:
        dead = 0.0
        actual = 0.0
        for t in workflow.tasks.values():
            dead += t.calculate_coordination_deadtime_seconds()
            if t.actual_duration_hours:
                actual += float(t.actual_duration_hours) * 3600.0
        if actual <= 0.0:
            return 0.5
        return _exp_penalty(dead / actual, alpha=1.1)

    def cost_overrun_efficiency(workflow: Workflow) -> float:
        budget = workflow.total_budget
        actual = workflow.total_cost
        if budget <= 0.0:
            return 0.5
        over = max(0.0, actual - budget) / budget
        return 1.0 / (1.0 + over)

    def artifact_presence_score(workflow: Workflow) -> float:
        """Reward presence of key artifacts (DPA, SCC/IDTA, Security Schedule, SLA pack, Exit Plan)."""
        keywords = [
            "data processing agreement",
            "dpa",
            "standard contractual clauses",
            "scc",
            "idta",
            "security schedule",
            "soc 2",
            "iso 27001",
            "sla",
            "slo",
            "exit plan",
            "termination assistance",
            "sub-processor",
        ]
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
        # Saturate when >= 5 artifacts are present
        return max(0.0, min(1.0, hits / 5.0))

    def approvals_coverage(workflow: Workflow) -> float:
        """Proxy for final approvals: look for messages mentioning GC/CISO/DPO/CFO approvals."""
        if not workflow.messages:
            return 0.0
        labels = ("gc", "general counsel", "ciso", "dpo", "cfo", "approval", "approved")
        hits = 0
        for m in workflow.messages[-200:]:
            try:
                txt = m.content.lower()
                if any(label in txt for label in labels):
                    hits += 1
            except Exception:
                continue
        return max(0.0, min(1.0, hits / 8.0))

    # ---------------------------
    # LLM rubric prompts (numeric [0, MAX])
    # ---------------------------
    # Privacy & Compliance
    privacy_llm = [
        WorkflowRubric(
            name="dpa_article_28_completeness",
            llm_prompt=(
                "Rigorously assess DPA compliance with GDPR Art. 28(3) requirements:\n"
                "- shows documented processing instructions with specific, measurable requirements\n"
                "- demonstrates confidentiality obligations with enforceable penalties\n"
                "- shows security measures with technical and organizational controls\n"
                "- demonstrates sub-processor authorization with legal review and flow-down requirements\n"
                "- shows data subject rights assistance with response time commitments\n"
                "- demonstrates breach notification with specific timeframes and procedures\n"
                "PENALTY: Deduct 1 point for each missing or vague requirement. No credit for boilerplate language. Output numeric score [0, 8]."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="intl_transfers_mechanisms",
            llm_prompt=(
                "Evaluate international transfer provisions: EU SCCs modules and UK IDTA/Addendum as applicable; "
                "Transfer Impact Assessment (if needed); any DPF/UK Data Bridge coverage. Partial credit per element; "
                "cite evidence. Output numeric score [0, 6]."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="ccpa_cpra_service_provider_clauses",
            llm_prompt=(
                "Evaluate CPRA service provider/contractor terms: restricted use/retention/sharing; monitoring/audit rights; "
                "flow-down to sub-contractors. Cite contract locations. Output numeric score [0, 5]."
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="records_and_data_mapping",
            llm_prompt=(
                "Assess presence and quality of data map and sub-processor register aligned with Art. 30 duties, "
                "and linkage to the DPA. Cite artifacts. Output numeric score [0, 5]."
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    privacy_rules = [
        WorkflowRubric(
            name="artifact_presence_privacy_core",
            evaluator_function=artifact_presence_score,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="legal_adversarial_scenarios",
            llm_prompt=(
                """Evaluate handling of legal adversarial scenarios and negotiations:
                - shows preparation for counterparty objections and aggressive negotiation tactics
                - demonstrates response to liability pushback and indemnity limitations
                - shows handling of compliance disputes and regulatory challenges
                - demonstrates preparation for contract disputes and litigation threats
                - shows escalation management and deal breakage risk mitigation
                Score 0 if no adversarial scenarios addressed. Partial credit only with evidence of challenges AND resolution strategies. Return score [0, 10]."""
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

    # Security
    security_llm = [
        WorkflowRubric(
            name="assurance_evidence_quality",
            llm_prompt=(
                "Evaluate assurance evidence: SOC 2 Type II and/or ISO/IEC 27001:2022 (with SoA). Assess scope and recency; "
                "award partial credit when at least one strong anchor is present. Output numeric score [0, 6]."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="security_controls_mapping",
            llm_prompt=(
                "Assess Security Schedule control coverage vs ISO/IEC 27002:2022 or NCSC Cloud Principles; ensure encryption, access control, "
                "vuln management, logging/monitoring, incident management, supplier mgmt, secure development are addressed. "
                "Cite control references. Output numeric score [0, 7]."
            ),
            max_score=7.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="pen_test_and_bcp_quality",
            llm_prompt=(
                "Evaluate pen-test executive summary and BCP/DR content with measurable RTO/RPO. Partial credit for scope/method, high-level findings, "
                "remediation status, and BCP measurables. Output numeric score [0, 5]."
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    security_rules = [
        WorkflowRubric(
            name="artifact_presence_security_core",
            evaluator_function=artifact_presence_score,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # Contract Quality (coherence, SLAs, LoL/IP, exit)
    quality_llm = [
        WorkflowRubric(
            name="internal_consistency_msa_dpa_security",
            llm_prompt=(
                "Evaluate internal consistency across MSA, DPA, and Security Schedule (e.g., definitions, scope of services, data handling, "
                "audit/records, and termination/return). Cite inconsistencies or confirm alignment. Output numeric score [0, 8]."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="sla_slo_alignment",
            llm_prompt=(
                "Assess SLIs/SLOs and alignment with SLAs and service credits, including error budget policy and credit cap. "
                "Award partial credit for clarity, user-centric SLOs, and realistic remedies. Output numeric score [0, 6]."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="liability_indemnities_balance",
            llm_prompt=(
                "Evaluate limitations of liability and indemnities (scope, carve-outs such as IP infringement, DP/security breach, confidentiality). "
                "Judge balance and alignment to risk appetite. Output numeric score [0, 6]."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="exit_plan_quality",
            llm_prompt=(
                "Assess Exit/Termination Assistance schedule: minimum content, timelines, roles, data migration, knowledge transfer, and fees. "
                "Cite evidence. Output numeric score [0, 5]."
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    quality_rules = [
        WorkflowRubric(
            name="artifact_presence_quality_core",
            evaluator_function=artifact_presence_score,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # Governance & Record-keeping
    governance_llm = [
        WorkflowRubric(
            name="audit_rights_practicality",
            llm_prompt=(
                "Assess audit rights practicality: certifications/independent reports allowed, remote audit options, reasonable limits, "
                "and preservation of Article 28(3)(h) audit right. Output numeric score [0, 5]."
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="negotiation_record_completeness",
            llm_prompt=(
                "Evaluate negotiation record completeness: issue tables, decisions, approvals, rationales, and versioning. "
                "Cite artifacts. Output numeric score [0, 6]."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="approvals_and_signoffs",
            llm_prompt=(
                "Assess coverage of senior approvals (GC, CISO, DPO, Finance) and risk acceptances, with scope and dates. "
                "Output numeric score [0, 5]."
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    governance_rules = [
        WorkflowRubric(
            name="approvals_signal",
            evaluator_function=approvals_coverage,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # Speed
    speed_llm = [
        WorkflowRubric(
            name="plan_realism_and_risks",
            llm_prompt=(
                "Evaluate milestone plan realism and critical path identification; buffers and risk mitigations present. "
                "Cite evidence. Output numeric score [0, 5]."
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    speed_rules = [
        WorkflowRubric(
            name="time_to_first_redline",
            evaluator_function=resp_time_to_first_redline,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="progress_throughput",
            evaluator_function=throughput_progress,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="blocked_deadtime",
            evaluator_function=blocked_deadtime_penalty,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # Cost
    cost_llm = [
        WorkflowRubric(
            name="cost_justification",
            llm_prompt=(
                "Assess cost justification quality: review effort aligns to scope/complexity; concessions linked to risk mitigations; "
                "identify savings opportunities. Output numeric score [0, 4]."
            ),
            max_score=4.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    cost_rules = [
        WorkflowRubric(
            name="overrun_efficiency",
            evaluator_function=cost_overrun_efficiency,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    return PreferenceWeights(
        preferences=[
            Preference(
                name="privacy_compliance",
                weight=0.25,
                evaluator=Evaluator(
                    name="privacy_eval",
                    description="placeholder",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=privacy_llm + privacy_rules,
                ),
            ),
            Preference(
                name="security",
                weight=0.2,
                evaluator=Evaluator(
                    name="security_eval",
                    description="placeholder",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=security_llm + security_rules,
                ),
            ),
            Preference(
                name="quality",
                weight=0.2,
                evaluator=Evaluator(
                    name="quality_eval",
                    description="placeholder",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=quality_llm + quality_rules,
                ),
            ),
            Preference(
                name="governance",
                weight=0.15,
                evaluator=Evaluator(
                    name="governance_eval",
                    description="placeholder",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=governance_llm + governance_rules,
                ),
            ),
            Preference(
                name="speed",
                weight=0.1,
                evaluator=Evaluator(
                    name="speed_eval",
                    description="placeholder",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=speed_llm + speed_rules,
                ),
            ),
            Preference(
                name="cost",
                weight=0.1,
                evaluator=Evaluator(
                    name="cost_eval",
                    description="placeholder",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=cost_llm + cost_rules,
                ),
            ),
        ]
    )


def create_evaluator_to_measure_goal_achievement() -> Evaluator:
    """Create a separate goal achievement evaluator for Legal Contract Negotiation."""
    goal_achievement_rubrics = [
        # Critical deliverables (10 points each)
        WorkflowRubric(
            name="final_contract_executed",
            llm_prompt=(
                "Does a final executed contract exist with: all parties' signatures, "
                "complete terms, effective date, and proper legal format? "
                "Return true if fully executed and legally binding, false otherwise."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="stakeholder_approvals_obtained",
            llm_prompt=(
                "Do all stakeholder approvals exist with: legal sign-off, business approval, "
                "procurement clearance, and executive authorization? "
                "Return 10.0 if all approvals obtained, 7 if there was an attempt to optimal approvals with some effort but a failure of execution, 5.0 if the need for approvals was mentioned in a resource, message or task, 0.0 otherwise."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="legal_opinion_provided",
            llm_prompt=(
                "Do the output resources / generated tasks show evidence of legal opinion being provided with details including: contract enforceability assessment, "
                "key risk analysis, regulatory compliance review, and recommendation summary? "
                "Return 10.0 if there is evidence of a formal legal position being drafted, 5.0 if there is evidence of legal opinion being provided but it is not complete, 0.0 otherwise."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Major deliverables (7 points each)
        WorkflowRubric(
            name="initial_contract_draft_exists",
            llm_prompt=(
                "Do the output resources / generated tasks show evidence of an initial contract draft being provided with details including: core commercial terms, "
                "standard legal provisions, specific scope of work, and payment terms? "
                "Return 7.0 if there is evidence of an initial contract draft being provided, 5.0 if there is evidence of an initial contract draft being provided but it is not complete, 0.0 otherwise."
            ),
            max_score=7.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="risk_assessment_completed",
            llm_prompt=(
                "Do the output resources / generated tasks show evidence of a legal risk assessment being provided with details including: identified contract risks, "
                "impact analysis, mitigation strategies, and approval recommendations? "
                "Return 7.0 if there is evidence of a legal risk assessment being provided, 5.0 if there is evidence of a legal risk assessment being provided but it is not complete, 0.0 otherwise."
            ),
            max_score=7.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="due_diligence_completed",
            llm_prompt=(
                "Do the output resources / generated tasks show evidence of due diligence being performed with details including: counterparty verification, "
                "financial checks, legal entity validation, and background research? "
                "Return 7.0 if there is evidence of due diligence being performed, 5.0 if there is evidence of due diligence being performed but it is not complete, 0.0 otherwise."
            ),
            max_score=7.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="commercial_terms_validated",
            llm_prompt=(
                "Do validated commercial terms exist with: pricing verification, "
                "payment schedule confirmation, deliverable specifications, and SLA definitions? "
                "Return true if all terms validated, false otherwise."
            ),
            max_score=7.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Important deliverables (5 points each)
        WorkflowRubric(
            name="negotiation_strategy_documented",
            llm_prompt=(
                "Does a negotiation strategy exist in the tasks / resources with: position priorities, "
                "fallback positions, deal breakers, and tactical approach? "
                "Return true if strategy documented, false otherwise."
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="compliance_framework_established",
            llm_prompt=(
                "Do the output resources / generated tasks show evidence of a compliance framework being established with details including: monitoring procedures, "
                "reporting requirements, escalation processes, and performance metrics? "
                "Return 5.0 if there is evidence of a compliance framework being established, 3.0 if there is evidence of a compliance framework being established but it is not complete, 0.0 otherwise."
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="performance_metrics_defined",
            llm_prompt=(
                "Do performance metrics exist with: KPI definitions, measurement criteria, "
                "reporting schedules, and penalty/incentive structures? "
                "Return true if metrics fully defined, false otherwise."
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Supporting deliverables (3 points each)
        WorkflowRubric(
            name="termination_procedures_documented",
            llm_prompt=(
                "Do the output resources / generated tasks show evidence of termination procedures being documented with details including: termination triggers, notice requirements, "
                "transition procedures, and asset return protocols? "
                "Return 3.0 if there is evidence of termination procedures being documented, 1.0 if there is evidence of termination procedures being documented but it is not complete, 0.0 otherwise."
            ),
            max_score=3.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="dispute_resolution_procedures",
            llm_prompt=(
                "Do the output resources / generated tasks show evidence of dispute resolution procedures being established with details including: escalation hierarchy, "
                "mediation processes, arbitration clauses, and governing law specifications? "
                "Return 3.0 if there is evidence of dispute resolution procedures being established, 1.0 if there is evidence of dispute resolution procedures being established but it is not complete, 0.0 otherwise."
            ),
            max_score=3.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    return Evaluator(
        name="legal_contract_goal_achievement_eval",
        description="Concrete deliverable and milestone achievement measurement for contract negotiation",
        aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
        rubrics=goal_achievement_rubrics,
    )


def create_preference_update_requests() -> list[PreferenceWeightUpdateRequest]:
    # Define a simple timeline of preference shifts across the negotiation.
    # Early: slightly higher on speed to get first drafts; mid: increase privacy/security and quality;
    # late: emphasize governance/sign-offs and overall contract quality.
    timeline: dict[int, PreferenceWeights] = {
        10: PreferenceWeights(
            preferences=[
                Preference(name="privacy_compliance", weight=0.23),
                Preference(name="security", weight=0.18),
                Preference(name="quality", weight=0.17),
                Preference(name="governance", weight=0.12),
                Preference(name="speed", weight=0.18),
                Preference(name="cost", weight=0.12),
            ]
        ),
        20: PreferenceWeights(
            preferences=[
                Preference(name="privacy_compliance", weight=0.28),
                Preference(name="security", weight=0.22),
                Preference(name="quality", weight=0.21),
                Preference(name="governance", weight=0.14),
                Preference(name="speed", weight=0.08),
                Preference(name="cost", weight=0.07),
            ]
        ),
        30: PreferenceWeights(
            preferences=[
                Preference(name="privacy_compliance", weight=0.27),
                Preference(name="security", weight=0.22),
                Preference(name="quality", weight=0.25),
                Preference(name="governance", weight=0.16),
                Preference(name="speed", weight=0.05),
                Preference(name="cost", weight=0.05),
            ]
        ),
        40: PreferenceWeights(
            preferences=[
                Preference(name="privacy_compliance", weight=0.26),
                Preference(name="security", weight=0.21),
                Preference(name="quality", weight=0.25),
                Preference(name="governance", weight=0.18),
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
