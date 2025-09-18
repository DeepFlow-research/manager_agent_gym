"""
IPO Readiness Program Demo

Real-world use case: Mid-size growth company preparing for U.S. public listing.

Demonstrates:
- Complex regulatory compliance coordination under strict SEC deadlines
- Multi-stakeholder team management across legal, audit, governance, and finance
- Risk-based decision making with materiality assessments and disclosure judgments
- Document workflow orchestration with approval dependencies and version control
- Crisis management when material weaknesses or compliance gaps are discovered
- Strategic timing decisions balancing transparency requirements with competitive positioning
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
        """Penalize unrealistic cost discrepancies for IPO readiness."""
        try:
            expected_min_cost = 150000.0  # IPO readiness should cost >$150k
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
                return 0.0  # IPO readiness should cost >$150k

            cost_variance = abs(total_actual - total_estimated) / total_estimated
            if cost_variance > 0.4:
                return 0.2
            elif cost_variance > 0.2:
                return 0.6
            else:
                return 1.0
        except Exception as e:
            print(f"Error in _validate_cost_realism: {e}")
            return 1.0

    def _ipo_adversarial_pressure_score(workflow: Workflow) -> float:
        """Score based on handling IPO adversarial pressure."""
        pressure_indicators = [
            "sec comment letter",
            "market volatility",
            "roadshow challenge",
            "investor skepticism",
            "regulatory delay",
            "audit finding",
            "due diligence issue",
            "valuation dispute",
            "competitor response",
            "market timing",
            "filing deficiency",
            "compliance gap",
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
                            "mitigated",
                            "corrected",
                        ]
                    ):
                        pressure_handled += 1
                    break

        return min(1.0, pressure_handled / max(1, len(pressure_indicators) * 0.3))

    def sec_filing_readiness(workflow: Workflow) -> float:
        """Reward presence of SEC filing indicators and readiness markers (0..1)."""
        keywords = ("s-1", "edgar", "sec", "filing", "registration", "prospectus")
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

    def governance_artifact_density(workflow: Workflow) -> float:
        """Reward having governance output artifacts for completed tasks (0..1)."""
        completed = [
            t for t in workflow.tasks.values() if t.status.value == "completed"
        ]
        if not completed:
            return 0.0
        total_outputs = 0
        for t in completed:
            total_outputs += len(t.output_resource_ids)
        avg_outputs = total_outputs / max(1, len(completed))
        # Saturate at 2 outputs per task for governance
        return max(0.0, min(1.0, avg_outputs / 2.0))

    def regulatory_deadline_adherence(workflow: Workflow) -> float:
        """Penalty for duration overrun vs regulatory timeline estimates (0..1)."""
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
        return exp(-1.0 * over)

    def compliance_progress_tracking(workflow: Workflow) -> float:
        """Progress proxy: completed/total tasks weighted by compliance criticality (0..1)."""
        total = len(workflow.tasks)
        if total == 0:
            return 0.0
        completed = len(
            [t for t in workflow.tasks.values() if t.status.value == "completed"]
        )
        return max(0.0, min(1.0, completed / max(1, total)))

    def audit_cost_efficiency(workflow: Workflow) -> float:
        """Penalty for cost overrun vs audit/legal budget (0..1)."""
        budget = workflow.total_budget
        actual = workflow.total_cost
        if budget <= 0.0:
            return 0.5
        over = max(0.0, actual - budget) / budget
        return 1.0 / (1.0 + 1.5 * over)  # Stricter penalty for IPO cost overruns

    def sox_control_maturity(workflow: Workflow) -> float:
        """Reward SOX control implementation indicators (0..1)."""
        sox_keywords = (
            "sox",
            "internal controls",
            "icfr",
            "302",
            "404",
            "certification",
        )
        recent = workflow.messages[-30:]
        if not recent:
            return 0.0
        hits = 0
        for m in recent:
            try:
                text = m.content.lower()
                if any(k in text for k in sox_keywords):
                    hits += 1
            except Exception:
                continue
        return max(0.0, min(1.0, hits / max(1, len(recent))))

    def board_governance_compliance(workflow: Workflow) -> float:
        """Proxy for governance discipline: fraction of messages indicating board activities (0..1)."""
        recent = workflow.messages[-40:]
        if not recent:
            return 0.0
        hits = 0
        for m in recent:
            try:
                text = m.content.lower()
                if any(
                    k in text
                    for k in (
                        "board",
                        "committee",
                        "independent",
                        "director",
                        "governance",
                        "charter",
                    )
                ):
                    hits += 1
            except Exception:
                continue
        return max(0.0, min(1.0, hits / max(1, len(recent))))

    # ---------------------------
    # SEC COMPLIANCE
    # ---------------------------
    sec_compliance_rubrics = [
        WorkflowRubric(
            name="s1_completeness_quality",
            llm_prompt=(
                """Evaluate S-1 registration statement completeness and quality. Award partial credit for:
                (a) comprehensive business description with competitive landscape,
                (b) material risk factors with specific company relevance,
                (c) MD&A with trend analysis and forward-looking statements,
                (d) executive compensation disclosure completeness.
                Cite specific workflow resources/messages for evidence. Output a numeric score in [0, 10]."""
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="financial_statement_audit_quality",
            llm_prompt=(
                """Assess PCAOB-audited financial statement quality and compliance:
                (1) appropriate accounting periods per Regulation S-X,
                (2) non-GAAP reconciliation completeness and clarity,
                (3) auditor opinion quality and material weakness disclosures,
                (4) comfort letter readiness for underwriters.
                Award equal partial credit. Cite evidence. Output numeric score [0, 8]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="regulatory_disclosure_accuracy",
            llm_prompt=(
                """Evaluate regulatory disclosure accuracy and completeness:
                All material information disclosed with supporting documentation,
                risk factor mapping to actual business risks, legal proceedings disclosure,
                and related party transaction documentation. Output numeric score [0, 8]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="sec_filing_readiness_indicators",
            evaluator_function=sec_filing_readiness,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="edgar_submission_validation",
            llm_prompt=(
                """
                Evaluate EDGAR submission readiness: test filing validation,
                error-free submission capability, proper document formatting,
                and submission timeline coordination. Output numeric score [0, 6].
            """
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="material_weakness_handling",
            llm_prompt=(
                "Score 0–8 for material weakness identification and remediation planning:"
                " disclosure adequacy, remediation timeline, management assessment quality."
                " Award partial credit with materiality rationale. Output numeric score [0, 8]."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="quiet_period_compliance",
            llm_prompt=(
                "Evaluate quiet period compliance strategy: gun-jumping avoidance,"
                " test-the-waters eligibility and execution, communication controls, legal pre-clearance."
                " Award partial credit with citations. Output numeric score [0, 6]."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # ---------------------------
    # GOVERNANCE & CONTROLS
    # ---------------------------
    governance_rubrics = [
        WorkflowRubric(
            name="board_independence_compliance",
            llm_prompt=(
                """Evaluate board independence and governance structure compliance. Award partial credit for:
                (a) majority independent directors meeting NYSE/Nasdaq standards,
                (b) audit committee financial expertise and independence,
                (c) compensation committee independence and charter compliance,
                (d) governance policy documentation and board procedures.
                Cite specific workflow resources for evidence. Output numeric score [0, 10]."""
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="sox_control_implementation",
            llm_prompt=(
                """Assess SOX compliance implementation quality:
                SOX 302 disclosure controls adequacy, ICFR framework completeness,
                management certification process readiness, control testing documentation.
                Provide partial credit with citations. Output numeric score [0, 8]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="committee_structure_effectiveness",
            llm_prompt=(
                """Evaluate board committee structure and effectiveness:
                audit/compensation/nominating committee formation, charter compliance,
                meeting documentation, and decision-making authority clarity.
                Output numeric score [0, 8]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="governance_artifact_completeness",
            evaluator_function=governance_artifact_density,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="internal_control_maturity",
            evaluator_function=sox_control_maturity,
            max_score=1.0,
            run_condition=RunCondition.EACH_TIMESTEP,
        ),
        WorkflowRubric(
            name="board_governance_discipline",
            evaluator_function=board_governance_compliance,
            max_score=1.0,
            run_condition=RunCondition.EACH_TIMESTEP,
        ),
    ]

    # ---------------------------
    # FINANCIAL READINESS
    # ---------------------------
    financial_rubrics = [
        WorkflowRubric(
            name="audit_opinion_quality",
            llm_prompt=(
                """Evaluate audit opinion quality and financial statement readiness:
                clean audit opinions, material weakness remediation,
                accounting policy appropriateness, revenue recognition compliance.
                Award partial credit with documentation citations. Output numeric score [0, 10]."""
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="financial_controls_testing",
            llm_prompt=(
                """Assess financial controls testing and documentation:
                control design effectiveness, operating effectiveness testing,
                deficiency identification and remediation, management assessment quality.
                Partial credit with evidence citations. Output numeric score [0, 8]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="comfort_letter_readiness",
            llm_prompt=(
                """Evaluate comfort letter readiness for underwriters:
                procedures documentation, negative assurance capability,
                subsequent event review processes, underwriter coordination.
                Output numeric score [0, 6]."""
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="non_gaap_reconciliation_quality",
            llm_prompt=(
                "Assess non-GAAP measure reconciliation quality: calculation accuracy,"
                " disclosure completeness, SEC compliance, comparability facilitation."
                " Output numeric score [0, 6]."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # ---------------------------
    # LEGAL & REGULATORY
    # ---------------------------
    legal_rubrics = [
        WorkflowRubric(
            name="legal_opinion_completeness",
            llm_prompt=(
                """Evaluate legal opinion completeness and regulatory compliance:
                corporate authority opinions, securities law compliance opinions,
                tax opinion adequacy, Staff Legal Bulletin No. 19 compliance.
                Award partial credit with specific citations. Output numeric score [0, 8]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="securities_law_compliance",
            llm_prompt=(
                """Assess securities law compliance across all activities:
                registration statement compliance, disclosure obligations,
                insider trading policy implementation, Regulation FD compliance.
                Provide partial credit with citations. Output numeric score [0, 8]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="exchange_listing_readiness",
            llm_prompt=(
                """Evaluate exchange listing standard compliance and readiness:
                quantitative listing requirements, corporate governance standards,
                market value thresholds, shareholder distribution requirements.
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
            name="regulatory_deadline_compliance",
            evaluator_function=regulatory_deadline_adherence,
            max_score=1.0,
            run_condition=RunCondition.EACH_TIMESTEP,
        ),
        WorkflowRubric(
            name="compliance_progress_efficiency",
            evaluator_function=compliance_progress_tracking,
            max_score=1.0,
            run_condition=RunCondition.EACH_TIMESTEP,
        ),
        WorkflowRubric(
            name="ipo_timeline_adherence",
            llm_prompt=(
                "Assess IPO timeline adherence and milestone achievement:"
                " critical path management, regulatory milestone timing, market window optimization."
                " Output numeric score [0, 6]."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="sec_response_efficiency",
            llm_prompt=(
                "Evaluate SEC comment letter response efficiency and quality:"
                " response timeliness, completeness, legal adequacy, revision quality."
                " Output numeric score [0, 6]."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="ipo_crisis_scenarios",
            llm_prompt=(
                """Evaluate handling of IPO crisis and market pressure scenarios:
                - shows preparation for SEC comment letters and regulatory delays
                - demonstrates response to market volatility and timing challenges
                - shows handling of roadshow challenges and investor skepticism
                - demonstrates preparation for audit findings and due diligence issues
                - shows contingency planning for filing deficiencies and compliance gaps
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
            name="audit_cost_management",
            evaluator_function=audit_cost_efficiency,
            max_score=1.0,
            run_condition=RunCondition.EACH_TIMESTEP,
        ),
        WorkflowRubric(
            name="legal_cost_justification",
            llm_prompt=(
                "Assess legal and professional service cost justification:"
                " scope appropriateness, fee reasonableness, value delivery, cost control measures."
                " Output numeric score [0, 6]."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="underwriter_cost_optimization",
            llm_prompt=(
                "Evaluate underwriter and advisory cost optimization:"
                " fee negotiation effectiveness, service scope alignment, comparative market analysis."
                " Output numeric score [0, 4]."
            ),
            max_score=4.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    return PreferenceWeights(
        preferences=[
            Preference(
                name="sec_compliance",
                weight=0.3,
                evaluator=Evaluator(
                    name="sec_compliance_eval",
                    description="SEC compliance evaluator",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=sec_compliance_rubrics,
                ),
            ),
            Preference(
                name="governance",
                weight=0.25,
                evaluator=Evaluator(
                    name="governance_eval",
                    description="governance evaluator",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=governance_rubrics,
                ),
            ),
            Preference(
                name="financial_readiness",
                weight=0.2,
                evaluator=Evaluator(
                    name="financial_readiness_eval",
                    description="financial readiness evaluator",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=financial_rubrics,
                ),
            ),
            Preference(
                name="legal_regulatory",
                weight=0.15,
                evaluator=Evaluator(
                    name="legal_regulatory_eval",
                    description="legal and regulatory evaluator",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=legal_rubrics,
                ),
            ),
            Preference(
                name="speed",
                weight=0.05,
                evaluator=Evaluator(
                    name="speed_eval",
                    description="speed evaluator",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=speed_rubrics,
                ),
            ),
            Preference(
                name="cost",
                weight=0.05,
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
    Create dynamic preference timeline emphasizing different aspects during IPO process:
    - Early: Financial readiness and governance setup (foundational)
    - Mid: SEC compliance and legal preparation (regulatory focus)
    - Late: Speed and final compliance (execution pressure)
    """
    timeline = {
        5: PreferenceWeights(
            preferences=[
                Preference(name="sec_compliance", weight=0.2),
                Preference(name="governance", weight=0.3),
                Preference(name="financial_readiness", weight=0.3),
                Preference(name="legal_regulatory", weight=0.1),
                Preference(name="speed", weight=0.05),
                Preference(name="cost", weight=0.05),
            ]
        ),
        15: PreferenceWeights(
            preferences=[
                Preference(name="sec_compliance", weight=0.35),
                Preference(name="governance", weight=0.2),
                Preference(name="financial_readiness", weight=0.2),
                Preference(name="legal_regulatory", weight=0.15),
                Preference(name="speed", weight=0.05),
                Preference(name="cost", weight=0.05),
            ]
        ),
        25: PreferenceWeights(
            preferences=[
                Preference(name="sec_compliance", weight=0.4),
                Preference(name="governance", weight=0.15),
                Preference(name="financial_readiness", weight=0.15),
                Preference(name="legal_regulatory", weight=0.2),
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


def create_evaluator_to_measure_goal_achievement() -> Evaluator:
    """Create goal achievement evaluator for IPO readiness program with SEC compliance focus."""
    goal_achievement_rubrics = [
        # Critical SEC compliance deliverables (absolutely must have for public listing)
        WorkflowRubric(
            name="s1_registration_statement_accepted",
            llm_prompt=(
                "Does accepted S-1 registration statement exist with: complete narrative sections (Business, Risk Factors, MD&A), "
                "Regulation S-X compliant financials, SEC acceptance for review confirmed, and ≤2 major comment letter cycles achieved? "
                "Return true if S-1 is accepted and progressing smoothly, false otherwise."
            ),
            max_score=20.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="pcaob_audited_financials_completed",
            llm_prompt=(
                "Do completed PCAOB-audited financial statements exist with: audit sign-offs secured, "
                "comfort letters available for underwriters, age-appropriate periods covered, and reconciliations documented? "
                "Return true if PCAOB audit is complete and ready, false otherwise."
            ),
            max_score=18.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="independent_board_committees_certified",
            llm_prompt=(
                "Do certified independent board committees exist with: independent directors appointed, "
                "audit/compensation committees formed, NYSE/Nasdaq standards met, and committee charters filed? "
                "Return true if board committees are certified and compliant, false otherwise."
            ),
            max_score=15.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="sox_controls_documentation_ready",
            llm_prompt=(
                "Does ready SOX controls documentation exist with: disclosure controls & procedures (SOX 302) documented, "
                "ICFR roadmap established, management certification rehearsed, and 404(b) readiness achieved if applicable? "
                "Return true if SOX controls documentation is ready, false otherwise."
            ),
            max_score=12.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Major compliance and operational deliverables (8-10 points each)
        WorkflowRubric(
            name="edgar_submission_workflows_tested",
            llm_prompt=(
                "Do tested EDGAR submission workflows exist with: EDGAR test submissions validated, "
                "submission procedures documented, error-free filing capability confirmed, and technical readiness verified? "
                "Return true if EDGAR workflows are tested and ready, false otherwise."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="legal_tax_opinions_filed",
            llm_prompt=(
                "Do filed legal and tax opinions exist with: Staff Legal Bulletin No. 19 compliance confirmed, "
                "legal opinions executed, tax opinions secured, and regulatory filing requirements met? "
                "Return true if legal and tax opinions are filed, false otherwise."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="listing_requirements_checklist_complete",
            llm_prompt=(
                "Does complete listing requirements checklist exist with: market value tests met, "
                "shareholder distribution validated, exchange approval correspondence secured, and auditor PCAOB registration confirmed? "
                "Return true if listing requirements checklist is complete, false otherwise."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="risk_disclosure_register_comprehensive",
            llm_prompt=(
                "Does comprehensive risk disclosure register exist with: operational/financial/legal/cyber risks inventoried, "
                "consistent mapping to S-1 risk factors, risk assessment completed, and disclosure accuracy validated? "
                "Return true if risk disclosure register is comprehensive, false otherwise."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="quiet_period_communications_plan",
            llm_prompt=(
                "Does quiet period communications plan exist with: counsel-approved strategy documented, "
                "test-the-waters capability (if EGC), Reg FD safeguards implemented, and post-pricing disclosure controls established? "
                "Return true if communications plan is operational and compliant, false otherwise."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Important supporting deliverables (5-7 points each)
        WorkflowRubric(
            name="corporate_governance_package_complete",
            llm_prompt=(
                "Does complete corporate governance package exist with: governance policies documented, "
                "board structure established, committee charters approved, and Rule 10A-3 compliance mapped? "
                "Return true if corporate governance package is complete, false otherwise."
            ),
            max_score=7.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="internal_controls_framework_validated",
            llm_prompt=(
                "Does validated internal controls framework exist with: control procedures documented, "
                "testing completed, deficiencies remediated, and effectiveness demonstrated? "
                "Return true if internal controls framework is validated, false otherwise."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="investor_relations_playbook_ready",
            llm_prompt=(
                "Does ready investor relations playbook exist with: IR strategy documented, "
                "stakeholder communication plans prepared, analyst targeting completed, and post-IPO IR framework established? "
                "Return true if IR playbook is ready for deployment, false otherwise."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="executive_compensation_disclosure",
            llm_prompt=(
                "Does executive compensation disclosure exist with: compensation analysis completed, "
                "peer benchmarking documented, proxy disclosure prepared, and compensation committee approval secured? "
                "Return true if executive compensation disclosure is complete, false otherwise."
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="comfort_letter_request_lists",
            llm_prompt=(
                "Do comfort letter request lists exist with: underwriter requirements documented, "
                "auditor coordination completed, comfort letter procedures established, and closing logistics planned? "
                "Return true if comfort letter processes are ready, false otherwise."
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Supporting deliverables (3-4 points each)
        WorkflowRubric(
            name="non_gaap_disclosure_controls",
            llm_prompt=(
                "Do non-GAAP disclosure controls exist with: non-GAAP measures defined, "
                "reconciliation procedures documented, SEC compliance validated, and disclosure consistency maintained? "
                "Return true if non-GAAP disclosure controls are established, false otherwise."
            ),
            max_score=4.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="legal_proceedings_documentation",
            llm_prompt=(
                "Does legal proceedings documentation exist with: material litigation identified, "
                "disclosure requirements assessed, legal risk evaluation completed, and S-1 disclosure prepared? "
                "Return true if legal proceedings documentation is complete, false otherwise."
            ),
            max_score=4.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="board_meeting_minutes_documented",
            llm_prompt=(
                "Do documented board meeting minutes exist with: IPO authorization resolutions passed, "
                "key decisions documented, governance compliance recorded, and audit trail maintained? "
                "Return true if board meeting documentation is complete, false otherwise."
            ),
            max_score=3.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="regulatory_correspondence_archive",
            llm_prompt=(
                "Does regulatory correspondence archive exist with: SEC communications logged, "
                "comment letter responses tracked, regulator feedback documented, and compliance history maintained? "
                "Return true if regulatory correspondence is properly archived, false otherwise."
            ),
            max_score=3.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    return Evaluator(
        name="ipo_readiness_goal_achievement_eval",
        description="IPO readiness program SEC compliance and public listing deliverable achievement measurement",
        aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
        rubrics=goal_achievement_rubrics,
    )
