from __future__ import annotations

from math import exp
from datetime import datetime

from manager_agent_gym.schemas.core.workflow import Workflow
from manager_agent_gym.schemas.preferences.preference import (
    Preference,
    PreferenceWeights,
)
from manager_agent_gym.schemas.preferences.evaluator import (
    Evaluator,
    AggregationStrategy,
)
from manager_agent_gym.schemas.preferences.rubric import WorkflowRubric, RunCondition
from examples.end_to_end_examples.standard_rules import speed_rubric, cost_rubric
from manager_agent_gym.schemas.preferences import PreferenceWeightUpdateRequest


def create_preferences() -> PreferenceWeights:
    # Deterministic helpers
    def artifact_density(workflow: Workflow) -> float:
        completed = [
            t for t in workflow.tasks.values() if t.status.value == "completed"
        ]
        if not completed:
            return 0.0
        outputs = sum(len(t.output_resource_ids) for t in completed)
        avg = outputs / max(1, len(completed))
        return max(0.0, min(1.0, avg / 3.0))

    # ---------------------------
    # Hardening Framework Functions
    # ---------------------------
    def _validate_cost_realism(workflow: Workflow, context) -> float:
        """Penalize unrealistic cost discrepancies for litigation ediscovery."""
        expected_min_cost = 40000.0  # Minimum realistic cost
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
            return 0.0  # Litigation ediscovery should cost >$40k

        cost_variance = abs(total_actual - total_estimated) / total_estimated
        if cost_variance > 0.4:
            return 0.2
        elif cost_variance > 0.2:
            return 0.6
        else:
            return 1.0

    def _litigation_adversarial_pressure_score(workflow: Workflow) -> float:
        """Score based on handling litigation adversarial pressure."""
        pressure_indicators = [
            "opposing counsel challenge",
            "discovery dispute",
            "privilege claim",
            "confidentiality breach",
            "data loss",
            "spoliation claim",
            "court sanction",
            "motion to compel",
            "protective order violation",
            "deadline pressure",
            "cost challenge",
            "production deficiency",
        ]

        pressure_handled = 0
        for indicator in pressure_indicators:
            for res in workflow.resources.values():
                if indicator.lower() in str(res.content or "").lower():
                    if any(
                        resolution.lower() in str(res.content or "").lower()
                        for resolution in [
                            "resolved",
                            "defended",
                            "addressed",
                            "remediated",
                        ]
                    ):
                        pressure_handled += 1
                    break

        return min(1.0, pressure_handled / max(1, len(pressure_indicators) * 0.3))

    def pii_leak_scan(workflow: Workflow) -> float:
        prohibited = (
            "ssn",
            "social security",
            "password",
            "api key",
            "secret key",
            "private key",
            "account_number",
        )
        hits = 0
        for res in workflow.resources.values():
            try:
                text = (res.content or "").lower()
                for k in prohibited:
                    if k in text:
                        hits += 1
            except Exception:
                continue
        return 1.0 / (1.0 + float(hits))

    def chain_of_custody_signal(workflow: Workflow) -> float:
        keywords = (
            "chain of custody",
            "hash",
            "sha256",
            "md5",
            "forensic image",
            "bitstream",
        )
        hits = 0
        total = 0
        for res in workflow.resources.values():
            total += 1
            try:
                text = (res.content or "").lower()
                if any(k in text for k in keywords):
                    hits += 1
            except Exception:
                continue
        if total == 0:
            return 0.0
        return min(1.0, hits / max(1, total))

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
        times: list[datetime] = [
            t.completed_at
            for t in workflow.tasks.values()
            if t.completed_at is not None
        ]
        if not times:
            return 0.0
        first_done = min(times)
        elapsed_h = (
            max(0.0, (first_done - workflow.started_at).total_seconds()) / 3600.0
        )
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

    # QUALITY: defensibility and review rigor
    quality_rubrics = [
        WorkflowRubric(
            name="eca_rigor",
            llm_prompt=(
                """
                Classify Early Case Assessment (ECA) rigor as "low" | "medium" | "high" (return this in score). Cite specific resource/message IDs.
                - LOW: No volume sizing; key custodians/hot docs not identified; scope not refined.
                - MEDIUM: Basic sizing and some hot docs; limited refinement of scope/terms.
                - HIGH: Thorough sizing; hot docs/custodians identified; scope/terms iteratively refined.
                """
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="tar_validation_completeness",
            llm_prompt=(
                """
                Classify TAR validation completeness as "low" | "medium" | "high" (return this in score). Cite evidence.
                - LOW: No control set; no elusion/precision-recall reporting.
                - MEDIUM: Control set present OR some precision/recall analysis.
                - HIGH: Control set, elusion tests, and precision/recall with thresholds documented.
                """
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="review_qc_coverage",
            llm_prompt=(
                """
                Classify review QC coverage as "low" | "medium" | "high" (return this in score). Cite evidence.
                - LOW: No sampling or QC; no double-blind checks.
                - MEDIUM: Some sampling QC or spot checks; limited documentation.
                - HIGH: Systematic sampling, double checks, and documented issue remediation.
                """
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="artifact_density",
            evaluator_function=artifact_density,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # COMPLIANCE: FRCP/protective order and production protocol
    compliance_rubrics = [
        WorkflowRubric(
            name="frcp_protective_order_adherence",
            llm_prompt=(
                """
                Classify adherence to FRCP/protective order as "low" | "medium" | "high" (return this in score). Cite evidence.
                - LOW: No mention of protective order terms; procedures not aligned; missing logs.
                - MEDIUM: Some alignment with partial documentation; gaps remain.
                - HIGH: Clear mapping to FRCP/protective order; complete documentation and approvals.
                """
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="production_protocol_compliance",
            llm_prompt=(
                """
                Classify production protocol compliance as "low" | "medium" | "high" (return this in score). Cite evidence.
                - LOW: Bates/load files/metadata requirements not met; family handling missing.
                - MEDIUM: Most requirements met; minor gaps.
                - HIGH: All protocol specs satisfied; verified with QC checks and logs.
                """
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="legal_hold_completeness",
            llm_prompt=(
                """
                Classify legal hold completeness as "low" | "medium" | "high" (return this in score). Cite evidence.
                - LOW: Hold notices not issued/tracked; custodian list incomplete.
                - MEDIUM: Notices issued and partly tracked; some custodians pending.
                - HIGH: Notices issued/acknowledged; escalations handled; custodians and sources complete.
                """
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # CONFIDENTIALITY & PRIVILEGE
    confidentiality_rubrics = [
        WorkflowRubric(
            name="pii_leak_scan",
            evaluator_function=pii_leak_scan,
            max_score=1.0,
            run_condition=RunCondition.EACH_TIMESTEP,
        ),
        WorkflowRubric(
            name="privilege_log_completeness",
            llm_prompt=(
                """
                Classify privilege log completeness as "low" | "medium" | "high" (return this in score). Cite evidence.
                - LOW: No privilege log; no redaction rationale.
                - MEDIUM: Basic log with gaps; some rationales provided.
                - HIGH: Comprehensive log with entries, rationales, and references to documents.
                """
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="chain_of_custody_signal",
            evaluator_function=chain_of_custody_signal,
            max_score=1.0,
            run_condition=RunCondition.EACH_TIMESTEP,
        ),
    ]

    # SPEED
    speed_rubrics = [
        WorkflowRubric(
            name="deadline_adherence",
            evaluator_function=speed_deadline_adherence,
            max_score=1.0,
            run_condition=RunCondition.EACH_TIMESTEP,
        ),
        WorkflowRubric(
            name="time_to_first_output",
            evaluator_function=speed_time_to_first_output,
            max_score=1.0,
            run_condition=RunCondition.EACH_TIMESTEP,
        ),
        WorkflowRubric(
            name="blocked_deadtime_penalty",
            evaluator_function=speed_blocked_deadtime_ratio,
            max_score=1.0,
            run_condition=RunCondition.EACH_TIMESTEP,
        ),
        WorkflowRubric(
            name="throughput_progress",
            evaluator_function=speed_throughput_progress,
            max_score=1.0,
            run_condition=RunCondition.EACH_TIMESTEP,
        ),
        WorkflowRubric(
            name="speed_efficiency",
            evaluator_function=speed_rubric,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # COST
    cost_rubrics = [
        WorkflowRubric(
            name="cost_efficiency",
            evaluator_function=cost_rubric,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="litigation_adversarial_scenarios",
            llm_prompt=(
                """Evaluate handling of litigation adversarial scenarios and discovery disputes:
                - shows preparation for opposing counsel challenges and discovery disputes
                - demonstrates response to privilege claims and confidentiality breaches
                - shows handling of data loss incidents and spoliation claims
                - demonstrates preparation for court sanctions and motions to compel
                - shows protective order compliance and production deficiency resolution
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

    return PreferenceWeights(
        preferences=[
            Preference(
                name="quality",
                weight=0.3,
                evaluator=Evaluator(
                    name="quality_eval",
                    description="defensibility and review rigor",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=quality_rubrics,
                ),
            ),
            Preference(
                name="compliance",
                weight=0.25,
                evaluator=Evaluator(
                    name="compliance_eval",
                    description="FRCP/protective order and production protocol",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=compliance_rubrics,
                ),
            ),
            Preference(
                name="confidentiality",
                weight=0.15,
                evaluator=Evaluator(
                    name="confidentiality_eval",
                    description="PII, privilege, and chain-of-custody",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=confidentiality_rubrics,
                ),
            ),
            Preference(
                name="speed",
                weight=0.15,
                evaluator=Evaluator(
                    name="speed_eval",
                    description="timeliness",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=speed_rubrics,
                ),
            ),
            Preference(
                name="cost",
                weight=0.15,
                evaluator=Evaluator(
                    name="cost_eval",
                    description="cost efficiency",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=cost_rubrics,
                ),
            ),
        ],
        timestep=0,
    )


def create_preference_update_requests() -> list[PreferenceWeightUpdateRequest]:
    """Preference shifts across ECA → review → production lifecycle."""
    timeline: dict[int, PreferenceWeights] = {
        0: PreferenceWeights(
            preferences=[
                Preference(name="quality", weight=0.30),
                Preference(name="compliance", weight=0.25),
                Preference(name="confidentiality", weight=0.15),
                Preference(name="speed", weight=0.15),
                Preference(name="cost", weight=0.15),
            ]
        ),
        15: PreferenceWeights(
            preferences=[
                Preference(name="quality", weight=0.35),
                Preference(name="compliance", weight=0.25),
                Preference(name="confidentiality", weight=0.15),
                Preference(name="speed", weight=0.15),
                Preference(name="cost", weight=0.10),
            ]
        ),
        30: PreferenceWeights(
            preferences=[
                Preference(name="quality", weight=0.25),
                Preference(name="compliance", weight=0.30),
                Preference(name="confidentiality", weight=0.20),
                Preference(name="speed", weight=0.10),
                Preference(name="cost", weight=0.15),
            ]
        ),
        45: PreferenceWeights(
            preferences=[
                Preference(name="quality", weight=0.20),
                Preference(name="compliance", weight=0.25),
                Preference(name="confidentiality", weight=0.25),
                Preference(name="speed", weight=0.10),
                Preference(name="cost", weight=0.20),
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
    """Create goal achievement evaluator for litigation eDiscovery employment dispute process."""
    goal_achievement_rubrics = [
        # Critical eDiscovery process deliverables (must have for FRCP compliance and defensible process)
        WorkflowRubric(
            name="defensible_collection_chain_custody",
            llm_prompt=(
                "Does defensible collection with chain of custody exist with: ESI collection documented, "
                "chain-of-custody maintained, forensic integrity preserved, and collection logs complete? "
                "Return true if defensible collection with chain of custody is established, false otherwise."
            ),
            max_score=18.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="privilege_review_qc_validated",
            llm_prompt=(
                "Does validated privilege review with QC exist with: privilege review completed, "
                "privileged documents identified and protected, QC sampling performed, and privilege log maintained? "
                "Return true if privilege review with QC is validated, false otherwise."
            ),
            max_score=15.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="frcp_compliant_productions",
            llm_prompt=(
                "Do FRCP-compliant productions exist with: production protocol specifications met, "
                "Bates numbering applied, load files generated, metadata fields included, and timely delivery achieved? "
                "Return true if productions are FRCP-compliant, false otherwise."
            ),
            max_score=15.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="tar_responsiveness_review_complete",
            llm_prompt=(
                "Does complete TAR responsiveness review exist with: technology-assisted review implemented, "
                "seed sets established, coding decisions tracked, responsiveness review completed, and quality metrics achieved? "
                "Return true if TAR responsiveness review is complete, false otherwise."
            ),
            max_score=12.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="eca_data_sizing_completed",
            llm_prompt=(
                "Does completed ECA data sizing exist with: early case assessment performed, "
                "data volume estimated, effort sizing completed, and case strategy informed? "
                "Return 10.0 if ECA data sizing is completed, 5.0 if it is mentioned but not completed,0.0 otherwise."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="processing_culling_denist_performed",
            llm_prompt=(
                "Does performed processing and culling exist with: data processing completed, "
                "deNIST filtering applied, deduplication performed, and date/keyword culling executed? "
                "Return true if processing and culling are performed, false otherwise."
            ),
            max_score=4.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="protective_order_compliance",
            llm_prompt=(
                "Does protective order compliance exist with: No PII identifiable in any outputs which are going to be shared publicly, no signs of any violation of protective order requirements, confidentiality maintained, and court order adherence confirmed? "
                "Return true if protective order compliance is achieved, false otherwise."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="custodian_interviews_source_identification",
            llm_prompt=(
                "Do custodian interviews and source identification exist with: key custodians interviewed, "
                "data sources identified and mapped, custodian data holdings documented, and source completeness confirmed? "
                "Return 8.0 if custodian interviews and source identification are complete, 4.0 if it is mentioned but not completed, 0.0 otherwise."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Important supporting deliverables (5-7 points each)
        WorkflowRubric(
            name="search_terms_validation",
            llm_prompt=(
                "Does search terms validation exist with: search terms defined and tested, "
                "search strategy documented, hit rates analyzed, and search effectiveness confirmed? "
                "Return 7.0 if search terms validation is complete, 3.0 if it is mentioned but not completed, 0.0 otherwise."
            ),
            max_score=7.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="work_product_segregation",
            llm_prompt=(
                "Does work product segregation exist with: attorney work product identified and protected, "
                "counsel communications preserved and segregated, work product privilege maintained, and document classification secure? "
                "Return true if work product segregation is established, false otherwise."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="family_deduplication_handling",
            llm_prompt=(
                "Does family deduplication handling exist with: document families identified, "
                "family grouping maintained, deduplication family-aware, and family integrity preserved? "
                "Return true if family deduplication handling is proper, false otherwise."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="ocr_text_extraction_quality",
            llm_prompt=(
                "Is there any sign that documents recieved from other parties that had to be OCR'd show signs of detected duplicates, low quality, or other issues? "
                "Return 5.0 if there are no such issues, 0.0 otherwise."
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="redaction_privilege_logging",
            llm_prompt=(
                "Are the documents recieved from other parties that had to be redaacted not identifiable as original documents (but no other issues)? "
                "Return 5.0 if there are no such issues, 0.0 otherwise."
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Supporting deliverables (3-4 points each)
        WorkflowRubric(
            name="production_load_files_metadata",
            llm_prompt=(
                "Are the production load files and metadata properly generated and processed? "
                "Return 4.0 if there are no such issues, 0.0 otherwise."
            ),
            max_score=4.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="audit_trails_documentation",
            llm_prompt=(
                "Do audit trails and documentation exist with: process documentation maintained, "
                "audit trails preserved, workflow tracking active, and documentation standards met? "
                "Return true if audit trails and documentation are comprehensive, false otherwise."
            ),
            max_score=4.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="court_deadlines_met",
            llm_prompt=(
                "Are there signs of court deadlines being met, or of efforts being made to meet them? "
                "Return 3.0 if there are no signs of missed court dates, 0.0 otherwise."
            ),
            max_score=3.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    return Evaluator(
        name="legal_litigation_ediscovery_goal_achievement_eval",
        description="Litigation eDiscovery employment dispute process deliverable achievement measurement",
        aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
        rubrics=goal_achievement_rubrics,
    )
