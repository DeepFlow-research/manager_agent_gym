"""
Banking License Application Demo
Real-world use case: European mid-size commercial bank seeking to establish
federal branch operations in the US market.
Demonstrates:
- Complex regulatory approval workflow with multiple jurisdictions
- Multi-phase application process with interdependent deliverables
- Stakeholder coordination across regulatory bodies and internal teams
- Risk management and compliance framework implementation
- Operational readiness assessment and capital structure planning
"""

from examples.end_to_end_examples.standard_rules import (
    speed_rubric,
    cost_rubric,
)
from math import exp
from manager_agent_gym.schemas.preferences.evaluator import (
    Rubric,
    AggregationStrategy,
)
from manager_agent_gym.schemas.preferences.preference import (
    Preference,
    PreferenceSnapshot,
)
from manager_agent_gym.schemas.domain import Workflow
from manager_agent_gym.schemas.preferences.rubric import RubricCriteria, RunCondition
from manager_agent_gym.schemas.preferences import PreferenceWeightUpdateRequest


def create_banking_license_preferences() -> PreferenceSnapshot:
    # ---------------------------
    # Deterministic helper rules
    # ---------------------------
    def _safe_hours(delta_seconds: float) -> float:
        return max(0.0, float(delta_seconds)) / 3600.0

    # ---------------------------
    # Hardening Framework Functions
    # ---------------------------
    def _validate_cost_realism(workflow: Workflow, context) -> float:
        """Penalize unrealistic cost discrepancies for banking license applications."""
        expected_min_cost = 120000.0  # Minimum realistic cost
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
            return 0.0  # Banking license applications should cost >$120k

        cost_variance = abs(total_actual - total_estimated) / total_estimated
        if cost_variance > 0.4:
            return 0.2
        elif cost_variance > 0.2:
            return 0.6
        else:
            return 1.0

    def _banking_adversarial_pressure_score(workflow: Workflow) -> float:
        """Score based on handling banking license adversarial pressure."""
        pressure_indicators = [
            "regulator challenge",
            "application deficiency",
            "capital adequacy concern",
            "governance criticism",
            "compliance gap",
            "prudential concern",
            "fit and proper challenge",
            "business model question",
            "risk management criticism",
            "operational resilience concern",
            "supervisory feedback",
            "license denial risk",
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
                            "remediated",
                            "improved",
                            "strengthened",
                        ]
                    ):
                        pressure_handled += 1
                    break

        return min(1.0, pressure_handled / max(1, len(pressure_indicators) * 0.3))

    def regulatory_documentation_completeness(workflow: Workflow) -> float:
        """Reward presence of regulatory documentation keywords in resources (0..1)."""
        keywords = (
            "application",
            "compliance",
            "regulatory",
            "policy",
            "procedure",
            "framework",
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

    def operational_readiness_density(workflow: Workflow) -> float:
        """Reward having operational artifacts for infrastructure tasks (0..1)."""
        infra_keywords = (
            "infrastructure",
            "system",
            "operational",
            "setup",
            "implementation",
        )
        completed = [
            t for t in workflow.tasks.values() if t.status.value == "completed"
        ]
        if not completed:
            return 0.0

        infra_tasks = []
        for t in completed:
            task_desc = (t.description or "").lower()
            if any(k in task_desc for k in infra_keywords):
                infra_tasks.append(t)

        if not infra_tasks:
            return 0.5  # neutral if no infrastructure tasks completed

        total_outputs = 0
        for t in infra_tasks:
            total_outputs += len(t.output_resource_ids)
        avg_outputs = total_outputs / max(1, len(infra_tasks))
        # Saturate at 2 outputs per infrastructure task
        return max(0.0, min(1.0, avg_outputs / 2.0))

    def regulatory_milestone_adherence(workflow: Workflow) -> float:
        """Penalty for duration overrun on regulatory critical path tasks (0..1)."""
        regulatory_keywords = (
            "application",
            "approval",
            "regulatory",
            "submission",
            "review",
        )
        reg_tasks = []

        for t in workflow.tasks.values():
            task_desc = (t.description or "").lower()
            task_name = (t.name or "").lower()
            if any(k in task_desc or k in task_name for k in regulatory_keywords):
                reg_tasks.append(t)

        if not reg_tasks:
            return 1

        total_est = 0.0
        total_act = 0.0
        for t in reg_tasks:
            if t.estimated_duration_hours is not None:
                total_est += float(t.estimated_duration_hours)
            if t.actual_duration_hours is not None:
                total_act += float(t.actual_duration_hours)

        if total_est <= 0.0:
            return 0.5
        over = max(0.0, total_act - total_est) / total_est
        return exp(-1.0 * over)

    def stakeholder_coordination_effectiveness(workflow: Workflow) -> float:
        """Proxy for stakeholder coordination: fraction of messages mentioning key stakeholders (0..1)."""
        stakeholders = (
            "occ",
            "federal reserve",
            "fed",
            "fdic",
            "ecb",
            "regulator",
            "supervisor",
            "board",
        )
        recent = workflow.messages[
            -100:
        ]  # More messages for complex stakeholder coordination
        if not recent:
            return 0.0
        hits = 0
        for m in recent:
            try:
                text = m.content.lower()
                if any(s in text for s in stakeholders):
                    hits += 1
            except Exception:
                continue
        return max(0.0, min(1.0, hits / max(1, len(recent))))

    def capital_adequacy_tracking(workflow: Workflow) -> float:
        """Reward tracking of capital requirements and CED arrangements (0..1)."""
        capital_keywords = ("capital", "ced", "funding", "$50m", "deposit", "liquidity")
        total = 0
        hits = 0
        for res in workflow.resources.values():
            total += 1
            try:
                content = (res.content or "").lower()
                if any(k in content for k in capital_keywords):
                    hits += 1
            except Exception:
                continue
        if total == 0:
            return 0.0
        return min(1.0, hits / max(1, total))

    def compliance_framework_coverage(workflow: Workflow) -> float:
        """Reward comprehensive compliance framework coverage (0..1)."""
        compliance_areas = (
            "aml",
            "bsa",
            "kyc",
            "cip",
            "sanctions",
            "monitoring",
            "reporting",
        )
        coverage_count = 0

        for res in workflow.resources.values():
            try:
                content = (res.content or "").lower()
                for area in compliance_areas:
                    if area in content:
                        coverage_count += 1
                        break  # Count each resource once
            except Exception:
                continue

        # Normalize by number of compliance areas
        return min(1.0, coverage_count / len(compliance_areas))

    # ---------------------------
    # REGULATORY COMPLIANCE
    # ---------------------------
    regulatory_compliance_rubrics = [
        RubricCriteria(
            name="occ_application_completeness",
            llm_prompt=(
                "Does the workflow show evidence of an OCC application package being prepared with details including: "
                """Evaluate OCC application package completeness. Award partial credit for:
                (a) complete business plan with financial projections,
                (b) management team documentation and background checks,
                (c) capital adequacy documentation,
                (d) operational readiness assessment.
                Cite specific workflow resources/messages for evidence. 
                Return 10.0 if there is evidence of an OCC application package being prepared, 5.0 if there is evidence of an OCC application package being prepared but it is not complete, 0.0 otherwise.
                
                """
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="multi_jurisdiction_coordination",
            llm_prompt=(
                """
                Assess the quality of coordination between US and European regulators if it takes place: We can assume that the application is for a US branch of a European bank.
                Signs of successful coordination include:
                (a) ECB/home supervisor engagement and approval,
                (b) Federal Reserve coordination and non-objection,
                (c) FDIC requirements compliance (if applicable),
                (d) documented supervision arrangements.
                Return 10.0 for an attempt at drafting each of these items, removing 2.5 for each missing element. To a minimum of 0.0.
                """
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="aml_bsa_program_robustness",
            llm_prompt=(
                """
                Evaluate the robustness of the AML/BSA compliance checks by searching for evidence of:
                (1) comprehensive policies and procedures,
                (2) customer identification and enhanced due diligence,
                (3) transaction monitoring and reporting systems,
                (4) training and governance framework.
                In the resources the workflow has created, search for evidence of the above items.
                Return 10.0 for an attempt at drafting each of these items, removing 2.5 for each missing element. To a minimum of 0.0.
                """
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="federal_reserve_regulation_k_compliance",
            llm_prompt=(
                """
                Assess Federal Reserve Regulation K compliance framework:
                policies, procedures, reporting requirements, and supervision coordination.
                In the resources the workflow has created, search for evidence of the above items.
                Return 10.0 for an attempt at drafting each of these items, removing 2.5 for each missing element. To a minimum of 0.0.
                """
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="due_diligence_thoroughness",
            llm_prompt=(
                """
                Evaluate due diligence thoroughness: beneficial ownership verification,
                management background checks, corporate affiliations review, and regulatory fitness assessment.
                In the resources the workflow has created, search for evidence of the above items.
                Return 10.0 for an attempt at drafting each of these items, removing 2.5 for each missing element. To a minimum of 0.0.
                """
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="regulatory_documentation_signal",
            evaluator_function=regulatory_documentation_completeness,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="compliance_framework_coverage_signal",
            evaluator_function=compliance_framework_coverage,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # ---------------------------
    # OPERATIONAL READINESS
    # ---------------------------
    operational_readiness_rubrics = [
        RubricCriteria(
            name="it_infrastructure_completeness",
            llm_prompt=(
                """
                Evaluate IT infrastructure completeness: core banking systems,
                security infrastructure, regulatory reporting capabilities, and integration testing.
                In the resources the workflow has created, search for evidence of the above items.
                Return 10.0 for a draft of the core banking systems, 5.0 for a draft of the security infrastructure, 5.0 for a draft of the regulatory reporting capabilities, and 5.0 for a draft of the integration testing. To a minimum of 0.0.
                """
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="correspondent_banking_relationships",
            llm_prompt=(
                """Assess correspondent banking relationship establishment:
                clearing and settlement arrangements, payment system access,
                and operational banking partnerships with documented agreements.
                In the resources the workflow has created, search for evidence of the above items.
                Return 10.0 for a draft of the clearing and settlement arrangements, 5.0 for a draft of the payment system access, and 5.0 for a draft of the operational banking partnerships with documented agreements. To a minimum of 0.0.
                """
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="physical_office_and_facilities",
            llm_prompt=(
                """Evaluate physical office setup and operational facilities:
                office locations, security systems, operational procedures,
                and service delivery capabilities.
                In the resources the workflow has created, search for evidence of the above items.
                Return 10.0 for a draft of the office locations, 5.0 for a draft of the security systems, 5.0 for a draft of the operational procedures, and 5.0 for a draft of the service delivery capabilities. To a minimum of 0.0.
                """
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="staffing_and_human_resources",
            llm_prompt=(
                """Assess staffing plan execution: senior management recruitment,
                operational staff hiring, HR policies establishment,
                and comprehensive training programs.
                In the resources the workflow has created, search for evidence of the above items.
                Return 10.0 for a draft of the senior management recruitment, 5.0 for a draft of the operational staff hiring, 5.0 for a draft of the HR policies establishment, and 5.0 for a draft of the comprehensive training programs. To a minimum of 0.0.
                """
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="operational_procedures_quality",
            llm_prompt=(
                """Evaluate operational procedures and workflows quality:
                completeness, clarity, compliance integration,
                and service delivery optimization. Output numeric score [0, MAX]."""
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="operational_readiness_density_signal",
            evaluator_function=operational_readiness_density,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Evidence gate: require concrete operational artifacts before awarding strong credit
        RubricCriteria(
            name="operational_artifacts_evidence",
            llm_prompt=(
                "Check for concrete operational readiness deliverables and artifacts.\n"
                "Award credit ONLY if evidence exists for items such as: deployed IT systems (configs, test results),\n"
                "security controls documentation, regulatory reporting system setup, physical office setup proofs,\n"
                "and finalized operating procedures. Cite specific task/resource IDs. Output numeric score [0,10]."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # ---------------------------
    # RISK MANAGEMENT
    # ---------------------------
    risk_management_rubrics = [
        RubricCriteria(
            name="comprehensive_risk_framework",
            llm_prompt=(
                """Evaluate comprehensive risk management framework covering:
                credit risk policies, market risk controls, operational risk assessment,
                and liquidity management procedures. Award partial credit per risk type. Output numeric score [0, MAX]."""
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="regulatory_reporting_systems",
            llm_prompt=(
                """Assess regulatory reporting systems establishment:
                Call Report capabilities, Federal Reserve reporting,
                and automated regulatory compliance reporting. Output numeric score [0, MAX]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="credit_underwriting_standards",
            llm_prompt=(
                """Evaluate credit risk policies and underwriting standards:
                risk assessment criteria, approval processes, portfolio management,
                and monitoring procedures. Output numeric score [0, MAX]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="liquidity_and_funding_management",
            llm_prompt=(
                """Assess liquidity management and funding strategy:
                liquidity risk controls, stress testing framework,
                funding diversification, and contingency planning. Output numeric score [0, MAX]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="operational_risk_controls",
            llm_prompt=(
                """Evaluate operational risk management framework:
                risk identification and assessment, control implementation,
                incident management, and business continuity planning. Output numeric score [0, MAX]."""
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Evidence gate: require finalized risk framework artifacts
        RubricCriteria(
            name="risk_framework_artifacts_evidence",
            llm_prompt=(
                "Verify presence of finalized risk framework artifacts: approved Credit Risk Policy, Market & Liquidity controls,\n"
                "Operational Risk Assessment report, BCP/DR plan, and liquidity stress testing methodology.\n"
                "Score 0 if only planning text exists without deliverables; cite resources and task IDs. [0,10]"
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # ---------------------------
    # CAPITAL STRUCTURE
    # ---------------------------
    capital_structure_rubrics = [
        RubricCriteria(
            name="minimum_capital_compliance",
            llm_prompt=(
                """Evaluate $50M minimum capital requirement compliance:
                capital adequacy documentation, funding source verification,
                and regulatory capital structure approval. Output numeric score [0, MAX]."""
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="ced_arrangements_quality",
            llm_prompt=(
                """Assess Capital Equivalent Deposit (CED) arrangements:
                structure adequacy, liquidity facility establishment,
                and ongoing funding commitments. Output numeric score [0, MAX]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="funding_strategy_sustainability",
            llm_prompt=(
                """Evaluate ongoing funding strategy sustainability:
                diversified funding sources, committed facilities,
                and long-term capital planning. Output numeric score [0, MAX]."""
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="capital_adequacy_tracking_signal",
            evaluator_function=capital_adequacy_tracking,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # ---------------------------
    # STAKEHOLDER COORDINATION
    # ---------------------------
    stakeholder_coordination_rubrics = [
        RubricCriteria(
            name="regulator_relationship_management",
            llm_prompt=(
                """Evaluate regulator relationship management quality:
                proactive communication, transparency in submissions,
                responsiveness to regulatory requests, and relationship building.
                Award partial credit with evidence. Output numeric score [0, MAX]."""
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="project_governance_effectiveness",
            llm_prompt=(
                """Assess project governance effectiveness: clear roles and responsibilities,
                decision-making processes, escalation procedures, and board reporting.
                Partial credit with documentation citations. Output numeric score [0, MAX]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="legal_counsel_coordination",
            llm_prompt=(
                """Evaluate legal counsel coordination and management:
                expertise utilization, cost management, work coordination,
                and deliverable quality oversight. Output numeric score [0, MAX]."""
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="internal_stakeholder_alignment",
            llm_prompt=(
                """Assess internal stakeholder alignment: executive team coordination,
                board engagement, business unit alignment, and change management.
                Output numeric score [0, MAX]."""
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="stakeholder_coordination_signal",
            evaluator_function=stakeholder_coordination_effectiveness,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Evidence gate: governance/liaison documentation and sign-offs
        RubricCriteria(
            name="governance_and_liaison_artifacts_evidence",
            llm_prompt=(
                "Require evidence of regulator liaison protocols, project governance artifacts (RACI, escalation),\n"
                "and legal counsel coordination records. Award credit only with uploaded documents/approvals. [0,8]"
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # ---------------------------
    # MARKET ENTRY STRATEGY
    # ---------------------------
    market_entry_rubrics = [
        RubricCriteria(
            name="market_analysis_depth",
            llm_prompt=(
                """Evaluate US market analysis depth and quality:
                competitive landscape assessment, target segment identification,
                regulatory environment analysis, and market opportunity quantification.
                Output numeric score [0, MAX]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="business_plan_realism",
            llm_prompt=(
                """Assess business plan realism and feasibility:
                revenue projections credibility, growth strategy viability,
                resource requirements accuracy, and timeline achievability.
                Award partial credit with evidence. Output numeric score [0, MAX]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="product_strategy_alignment",
            llm_prompt=(
                """Evaluate product strategy alignment with market needs:
                product offering design, pricing strategy competitiveness,
                service delivery capability, and customer value proposition.
                Output numeric score [0, MAX]."""
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="competitive_positioning",
            llm_prompt=(
                """Assess competitive positioning strategy:
                differentiation factors, competitive advantages,
                market entry barriers consideration, and positioning sustainability.
                Output numeric score [0, MAX]."""
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # ---------------------------
    # SPEED (Timeline Management)
    # ---------------------------
    speed_rubrics = [
        # Deterministic
        RubricCriteria(
            name="regulatory_milestone_adherence",
            evaluator_function=regulatory_milestone_adherence,
            max_score=1.0,
            run_condition=RunCondition.EACH_TIMESTEP,
        ),
        RubricCriteria(
            name="deadline_adherence",
            evaluator_function=lambda w: speed_deadline_adherence(w),
            max_score=5.0,
            run_condition=RunCondition.EACH_TIMESTEP,
        ),
        RubricCriteria(
            name="throughput_progress",
            evaluator_function=lambda w: speed_throughput_progress(w),
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
        # LLM timeline management checks
        RubricCriteria(
            name="critical_path_management",
            llm_prompt=(
                """Evaluate critical path management for 18-24 month timeline:
                regulatory approval sequencing, dependency management,
                and timeline risk mitigation. Output numeric score [0, MAX]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="regulatory_timeline_optimization",
            llm_prompt=(
                """Assess regulatory timeline optimization:
                parallel track utilization, early regulatory engagement,
                and approval process acceleration strategies. Output numeric score [0, MAX]."""
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="milestone_tracking_quality",
            llm_prompt=(
                """Evaluate milestone tracking and reporting quality:
                progress monitoring, variance identification,
                and corrective action implementation. Output numeric score [0, MAX]."""
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Evidence gate: baseline schedule and timestamps
        RubricCriteria(
            name="schedule_and_timestamp_evidence",
            llm_prompt=(
                "Award credit only if a baseline schedule (milestones/Gantt) and timestamped task histories exist to support speed claims.\n"
                "Return 0 without such artifacts; cite evidence if present. [0,6]"
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # Helper functions used in speed rubrics
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

    def speed_throughput_progress(workflow: Workflow) -> float:
        """Progress proxy: completed/total tasks (0..1)."""
        total = len(workflow.tasks)
        if total == 0:
            return 0.0
        completed = len(
            [t for t in workflow.tasks.values() if t.status.value == "completed"]
        )
        return max(0.0, min(1.0, completed / max(1, total)))

    # ---------------------------
    # COST (Budget Management)
    # ---------------------------
    cost_rubrics = [
        RubricCriteria(
            name="cost_efficiency",
            evaluator_function=cost_rubric,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="budget_adherence_5m_limit",
            llm_prompt=(
                """Evaluate adherence to $5M total project budget:
                cost tracking accuracy, budget variance analysis,
                and cost control effectiveness. Output numeric score [0, MAX]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="cost_category_optimization",
            llm_prompt=(
                """Assess cost optimization across categories:
                regulatory fees, legal costs, consultant fees, and setup expenses.
                Award partial credit for each category with justification. Output numeric score [0, MAX]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="value_for_money_assessment",
            llm_prompt=(
                """Evaluate value for money in vendor selection and resource allocation:
                cost-benefit analysis, competitive procurement, and ROI consideration.
                Output numeric score [0, MAX]."""
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="cost_transparency_reporting",
            llm_prompt=(
                """Assess cost transparency and reporting quality:
                detailed cost breakdowns, variance explanations,
                and stakeholder cost communication. Output numeric score [0, MAX]."""
            ),
            max_score=4.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Evidence gate: budget control and variance reporting artifacts
        RubricCriteria(
            name="budget_control_artifacts_evidence",
            llm_prompt=(
                "Verify presence of cost tracking plan, variance reports, procurement/contract artifacts, and approval logs.\n"
                "If only estimates exist and actuals are 0 with no reports, return 0. Provide citations. [0,6]"
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="banking_adversarial_scenarios",
            llm_prompt=(
                """Evaluate handling of banking license adversarial scenarios:
                - shows preparation for regulator challenges and application deficiencies
                - demonstrates response to capital adequacy concerns and governance criticism
                - shows handling of compliance gaps and prudential concerns
                - demonstrates preparation for fit and proper challenges and business model questions
                - shows license denial risk management and supervisory feedback response
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
                name="regulatory_compliance",
                weight=0.35,
                evaluator=Rubric(
                    name="regulatory_compliance",
                    description="placeholder",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    criteria=regulatory_compliance_rubrics,
                ),
            ),
            Preference(
                name="operational_readiness",
                weight=0.25,
                evaluator=Rubric(
                    name="operational_readiness",
                    description="placeholder",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    criteria=operational_readiness_rubrics,
                ),
            ),
            Preference(
                name="risk_management",
                weight=0.15,
                evaluator=Rubric(
                    name="risk_management",
                    description="placeholder",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    criteria=risk_management_rubrics,
                ),
            ),
            Preference(
                name="capital_structure",
                weight=0.10,
                evaluator=Rubric(
                    name="capital_structure",
                    description="placeholder",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    criteria=capital_structure_rubrics,
                ),
            ),
            Preference(
                name="stakeholder_coordination",
                weight=0.08,
                evaluator=Rubric(
                    name="stakeholder_coordination",
                    description="placeholder",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    criteria=stakeholder_coordination_rubrics,
                ),
            ),
            Preference(
                name="market_entry_strategy",
                weight=0.04,
                evaluator=Rubric(
                    name="market_entry_strategy",
                    description="placeholder",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    criteria=market_entry_rubrics,
                ),
            ),
            Preference(
                name="speed",
                weight=0.02,
                evaluator=Rubric(
                    name="speed",
                    description="placeholder",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    criteria=speed_rubrics,
                ),
            ),
            Preference(
                name="cost",
                weight=0.01,
                evaluator=Rubric(
                    name="cost",
                    description="placeholder",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    criteria=cost_rubrics,
                ),
            ),
        ]
    )


def create_preference_update_requests() -> list[PreferenceWeightUpdateRequest]:
    """Return weight update requests for compliance → operational readiness dynamics."""
    timeline: dict[int, PreferenceSnapshot] = {
        0: PreferenceSnapshot(
            preferences=[
                Preference(name="regulatory_compliance", weight=0.4),
                Preference(name="operational_readiness", weight=0.2),
                Preference(name="risk_management", weight=0.15),
                Preference(name="capital_structure", weight=0.1),
                Preference(name="stakeholder_coordination", weight=0.08),
                Preference(name="market_entry_strategy", weight=0.04),
                Preference(name="speed", weight=0.02),
                Preference(name="cost", weight=0.01),
            ]
        ),
        15: PreferenceSnapshot(
            preferences=[
                Preference(name="regulatory_compliance", weight=0.35),
                Preference(name="operational_readiness", weight=0.25),
                Preference(name="risk_management", weight=0.15),
                Preference(name="capital_structure", weight=0.1),
                Preference(name="stakeholder_coordination", weight=0.08),
                Preference(name="market_entry_strategy", weight=0.04),
                Preference(name="speed", weight=0.02),
                Preference(name="cost", weight=0.01),
            ]
        ),
        30: PreferenceSnapshot(
            preferences=[
                Preference(name="regulatory_compliance", weight=0.3),
                Preference(name="operational_readiness", weight=0.3),
                Preference(name="risk_management", weight=0.15),
                Preference(name="capital_structure", weight=0.1),
                Preference(name="stakeholder_coordination", weight=0.08),
                Preference(name="market_entry_strategy", weight=0.04),
                Preference(name="speed", weight=0.02),
                Preference(name="cost", weight=0.01),
            ]
        ),
        45: PreferenceSnapshot(
            preferences=[
                Preference(name="regulatory_compliance", weight=0.25),
                Preference(name="operational_readiness", weight=0.35),
                Preference(name="risk_management", weight=0.15),
                Preference(name="capital_structure", weight=0.1),
                Preference(name="stakeholder_coordination", weight=0.08),
                Preference(name="market_entry_strategy", weight=0.04),
                Preference(name="speed", weight=0.02),
                Preference(name="cost", weight=0.01),
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
    """Create goal achievement evaluator for US banking license application process."""
    goal_achievement_rubrics = [
        # Critical regulatory approvals (absolutely must have for legal banking operations)
        RubricCriteria(
            name="occ_license_approval_granted",
            llm_prompt=(
                "Does OCC (Office of the Comptroller of the Currency) license approval exist with: "
                "final approval letter, all regulatory conditions satisfied, federal branch authorization, "
                "and operational commencement approval? "
                "Return true if OCC license is officially granted and operational, false otherwise."
            ),
            max_score=20.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="federal_reserve_non_objection",
            llm_prompt=(
                "Does Federal Reserve non-objection exist with: formal non-objection letter, "
                "supervision arrangements confirmed, consolidated supervision agreement, and compliance attestation? "
                "Return true if Federal Reserve non-objection is secured, false otherwise."
            ),
            max_score=15.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="home_country_regulator_approval",
            llm_prompt=(
                "Does home country regulator (ECB/national authority) approval exist with: "
                "US market entry authorization, consolidated supervision attestation, capital adequacy confirmation, "
                "and cross-border oversight agreement? "
                "Return true if home country approval is secured, false otherwise."
            ),
            max_score=15.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Major compliance and operational deliverables (10-12 points each)
        RubricCriteria(
            name="aml_bsa_program_implemented",
            llm_prompt=(
                "Does implemented AML/BSA compliance program exist with: written compliance policies, "
                "customer identification procedures, enhanced due diligence protocols, independent testing, "
                "and BSA officer appointment? "
                "Return true if AML/BSA program is fully implemented and validated, false otherwise."
            ),
            max_score=12.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="capital_structure_established",
            llm_prompt=(
                "Does established capital structure exist with: $50M minimum capital deposited, "
                "CED (Capital Equivalent Deposit) arrangements confirmed, liquidity facilities secured, "
                "and ongoing funding sources documented? "
                "Return true if capital requirements are fully satisfied, false otherwise."
            ),
            max_score=12.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="risk_management_framework_operational",
            llm_prompt=(
                "Does operational risk management framework exist with: credit risk policies, "
                "market risk controls, liquidity management procedures, operational risk assessment, "
                "and regulatory reporting systems? "
                "Return true if risk management framework is operational, false otherwise."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="operational_infrastructure_deployed",
            llm_prompt=(
                "Does deployed operational infrastructure exist with: IT systems operational, "
                "physical office setup complete, correspondent banking relationships established, "
                "and service delivery capabilities tested? "
                "Return true if operational infrastructure is fully deployed, false otherwise."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="senior_management_appointed",
            llm_prompt=(
                "Does appointed senior management team exist with: all key positions filled, "
                "background checks completed, regulatory fitness confirmed, and board governance established? "
                "Return true if senior management is appointed and qualified, false otherwise."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Important supporting deliverables (6-8 points each)
        RubricCriteria(
            name="business_plan_approved",
            llm_prompt=(
                "Does approved business plan exist with: comprehensive market analysis, "
                "target customer segments defined, product offerings documented, 3-year financial projections, "
                "and regulatory acceptance confirmed? "
                "Return 8.0 if there is evidence of a business plan being approved and comprehensive, 4.0 if there is evidence of a business plan being drafted or planned but it is not complete, 0.0 otherwise."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="corporate_governance_established",
            llm_prompt=(
                "Does established corporate governance exist with: board structure implemented, "
                "committee charters approved, governance policies documented, and decision-making authorities defined? "
                "Return 8.0 if there is evidence of corporate governance being established, 4.0 if there is evidence of corporate governance being established but it is not complete, 0.0 otherwise."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="regulatory_reporting_systems",
            llm_prompt=(
                "Do regulatory reporting systems exist with: automated reporting capabilities, "
                "data quality controls, regulatory submission procedures, and compliance monitoring tools? "
                "Return 6.0 if there is evidence of specifications for regulatory reporting systems are drafted, 3.0 if there is evidence of regulatory reporting systems being established but it is not complete, 0.0 otherwise."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="due_diligence_completed",
            llm_prompt=(
                "Does completed due diligence exist with: beneficial ownership verification, "
                "management background checks completed, corporate affiliations reviewed, and regulatory validation secured? "
                "Return true if comprehensive due diligence is completed, false otherwise."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="legal_structure_finalized",
            llm_prompt=(
                "Does finalized legal structure exist with: US entity incorporation complete, "
                "legal documentation package executed, regulatory structure confirmed, and operational agreements signed? "
                "Return true if legal structure is finalized, false otherwise."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Supporting deliverables (3-5 points each)
        RubricCriteria(
            name="market_entry_strategy_documented",
            llm_prompt=(
                "Does documented market entry strategy exist with: competitive analysis completed, "
                "customer acquisition strategy defined, revenue projections validated, and go-to-market timeline established? "
                "Return true if market entry strategy is documented, false otherwise."
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="regulatory_conditions_satisfied",
            llm_prompt=(
                "Is there evidence that any regulatory conditions relevent to banking operations have been broken? "
                "Return 4.0 if there is no evidence of a regulatory condition being broken, 0.0 otherwise."
            ),
            max_score=4.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="fdic_insurance_secured",
            llm_prompt=(
                "Does FDIC insurance exist with: application submitted, coverage approved, "
                "premium payments arranged, and deposit insurance operational (if applicable)? "
                "Return true if FDIC insurance is secured or N/A, false otherwise."
            ),
            max_score=3.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    return Rubric(
        name="banking_license_goal_achievement_eval",
        description="US banking license application deliverable achievement measurement",
        aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
        criteria=goal_achievement_rubrics,
    )
