# pyright: reportMissingImports=false, reportMissingTypeStubs=false
"""
Technology Company Acquisition & Integration Demo

Real-world use case: $150M SaaS platform company acquisition and integration.

Demonstrates:
- Complex multi-workstream project management across technical, financial, and regulatory domains
- Cross-functional team coordination with diverse expertise requirements and stakeholder management
- Timeline-critical integration planning with cascading dependencies and risk mitigation strategies
- Regulatory compliance management across multiple jurisdictions with approval workflow coordination
- Technology systems integration with service continuity requirements and minimal customer disruption
- Human capital retention and cultural integration during high-uncertainty transition periods
"""

from examples.end_to_end_examples.standard_rules import (
    speed_rubric,
    cost_rubric,
)
from manager_agent_gym.schemas.preferences.preference import (
    Preference,
    PreferenceWeights,
    Evaluator,
)
from manager_agent_gym.schemas.preferences.evaluator import AggregationStrategy
from manager_agent_gym.schemas.core import Workflow
from manager_agent_gym.schemas.preferences.rubric import WorkflowRubric, RunCondition


def create_tech_acquisition_integration_preferences() -> PreferenceWeights:
    # ---------------------------
    # Deterministic helper rules
    # ---------------------------
    def _safe_hours(delta_seconds: float) -> float:
        return max(0.0, float(delta_seconds)) / 3600.0

    # ---------------------------
    # Hardening Framework Functions
    # ---------------------------
    def _validate_cost_realism(workflow: Workflow, context) -> float:
        """Penalize unrealistic cost discrepancies for tech acquisitions."""
        expected_min_cost = 75000.0  # Minimum realistic cost
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
            return 0.0  # Tech acquisitions should cost >$75k

        cost_variance = abs(total_actual - total_estimated) / total_estimated
        if cost_variance > 0.4:
            return 0.2
        elif cost_variance > 0.2:
            return 0.6
        else:
            return 1.0

    def _tech_acquisition_adversarial_pressure_score(workflow: Workflow) -> float:
        """Score based on handling tech acquisition adversarial pressure."""
        pressure_indicators = [
            "regulatory challenge",
            "antitrust concern",
            "integration difficulty",
            "cultural clash",
            "talent retention issue",
            "technology incompatibility",
            "competitive response",
            "customer churn",
            "due diligence gap",
            "valuation dispute",
            "deal breakage risk",
            "stakeholder opposition",
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
                            "managed",
                        ]
                    ):
                        pressure_handled += 1
                    break

        return min(1.0, pressure_handled / max(1, len(pressure_indicators) * 0.3))

    def due_diligence_completeness(workflow: Workflow) -> float:
        """Reward comprehensive due diligence coverage across technology, business, and regulatory areas (0..1)."""
        due_diligence_keywords = {
            "technology": [
                "architecture",
                "code quality",
                "cybersecurity",
                "infrastructure",
                "technical debt",
            ],
            "business": [
                "saas metrics",
                "customer contracts",
                "revenue",
                "operational workflow",
                "competitive",
            ],
            "regulatory": [
                "antitrust",
                "hsr filing",
                "data privacy",
                "gdpr",
                "licensing",
                "compliance",
            ],
            "financial": [
                "arr",
                "churn",
                "cac",
                "ltv",
                "financial projection",
                "valuation",
            ],
        }

        covered_areas = set()
        for res in workflow.resources.values():
            try:
                content = (res.content or "").lower()
                for area, keywords in due_diligence_keywords.items():
                    if any(keyword in content for keyword in keywords):
                        covered_areas.add(area)
            except Exception:
                continue

        return min(1.0, len(covered_areas) / len(due_diligence_keywords))

    def integration_timeline_adherence(workflow: Workflow) -> float:
        """Track adherence to critical integration timelines (90-day systems, 180-day full integration) (0..1)."""
        if workflow.started_at is None:
            return 0.0

        # Find key integration milestones
        systems_integration_time = None
        full_integration_time = None

        for task in workflow.tasks.values():
            if task.completed_at is not None:
                if any(
                    keyword in task.name.lower()
                    for keyword in ["systems integration", "critical systems"]
                ):
                    if (
                        systems_integration_time is None
                        or task.completed_at < systems_integration_time
                    ):
                        systems_integration_time = task.completed_at

                if any(
                    keyword in task.name.lower()
                    for keyword in ["organizational integration", "validation"]
                ):
                    if (
                        full_integration_time is None
                        or task.completed_at < full_integration_time
                    ):
                        full_integration_time = task.completed_at

        score = 0.0

        # 90-day systems integration target
        if systems_integration_time is not None:
            sys_days = (
                _safe_hours(
                    (systems_integration_time - workflow.started_at).total_seconds()
                )
                / 24.0
            )
            if sys_days <= 90.0:
                score += 0.5
            elif sys_days <= 120.0:
                score += 0.3

        # 180-day full integration target
        if full_integration_time is not None:
            full_days = (
                _safe_hours(
                    (full_integration_time - workflow.started_at).total_seconds()
                )
                / 24.0
            )
            if full_days <= 180.0:
                score += 0.5
            elif full_days <= 210.0:
                score += 0.3

        return min(1.0, score)

    def stakeholder_retention_tracking(workflow: Workflow) -> float:
        """Track talent retention and customer retention indicators throughout integration (0..1)."""
        retention_indicators = [
            "talent retention",
            "employee retention",
            "customer retention",
            "churn reduction",
        ]
        negative_indicators = [
            "talent loss",
            "employee departure",
            "customer churn",
            "attrition increase",
        ]

        positive_count = 0
        negative_count = 0

        for res in workflow.resources.values():
            try:
                content = (res.content or "").lower()
                for indicator in retention_indicators:
                    if indicator in content:
                        positive_count += 1
                for indicator in negative_indicators:
                    if indicator in content:
                        negative_count += 1
            except Exception:
                continue

        total_retention_signals = positive_count + negative_count
        if total_retention_signals == 0:
            return 0.5

        return max(0.0, min(1.0, positive_count / total_retention_signals))

    def regulatory_approval_progress(workflow: Workflow) -> float:
        """Track regulatory approval progress across multiple jurisdictions (0..1)."""
        approval_keywords = [
            "hsr approval",
            "antitrust clearance",
            "regulatory approval",
            "compliance verified",
        ]
        jurisdiction_keywords = [
            "north america",
            "europe",
            "gdpr",
            "ccpa",
            "cross-border",
        ]

        approval_signals = 0
        jurisdiction_coverage = 0

        for res in workflow.resources.values():
            try:
                content = (res.content or "").lower()
                if any(keyword in content for keyword in approval_keywords):
                    approval_signals += 1
                if any(keyword in content for keyword in jurisdiction_keywords):
                    jurisdiction_coverage += 1
            except Exception:
                continue

        # Combine approval progress and jurisdiction coverage
        approval_score = min(
            1.0, approval_signals / 3.0
        )  # Expect at least 3 approval milestones
        jurisdiction_score = min(
            1.0, jurisdiction_coverage / 2.0
        )  # Expect coverage of major jurisdictions

        return (approval_score + jurisdiction_score) / 2.0

    def systems_integration_quality(workflow: Workflow) -> float:
        """Assess quality of systems integration through uptime and security indicators (0..1)."""
        quality_indicators = [
            "99.5% uptime",
            "service continuity",
            "zero data loss",
            "security maintained",
        ]
        issue_indicators = [
            "system downtime",
            "data loss",
            "security breach",
            "service disruption",
        ]

        quality_count = 0
        issue_count = 0

        for res in workflow.resources.values():
            try:
                content = (res.content or "").lower()
                for indicator in quality_indicators:
                    if indicator in content:
                        quality_count += 1
                for indicator in issue_indicators:
                    if indicator in content:
                        issue_count += 1
            except Exception:
                continue

        if quality_count + issue_count == 0:
            return 0.5

        # Penalize issues more heavily
        quality_ratio = quality_count / max(1, quality_count + (issue_count * 2))
        return max(0.0, min(1.0, quality_ratio))

    def synergy_realization_progress(workflow: Workflow) -> float:
        """Track progress on synergy identification and realization (0..1)."""
        synergy_keywords = [
            "synergy",
            "cross-selling",
            "revenue enhancement",
            "cost savings",
            "operational efficiency",
        ]

        synergy_mentions = 0
        for res in workflow.resources.values():
            try:
                content = (res.content or "").lower()
                for keyword in synergy_keywords:
                    if keyword in content:
                        synergy_mentions += 1
            except Exception:
                continue

        # Normalize by expected synergy documentation
        return min(1.0, synergy_mentions / 5.0)

    def integration_artifact_density(workflow: Workflow) -> float:
        """Reward having integration artifacts for completed tasks (0..1)."""
        completed = [
            t for t in workflow.tasks.values() if t.status.value == "completed"
        ]
        if not completed:
            return 0.0
        total_outputs = 0
        for t in completed:
            total_outputs += len(t.output_resource_ids)
        avg_outputs = total_outputs / max(1, len(completed))
        # Saturate at 2.5 outputs per task for complex acquisitions
        return max(0.0, min(1.0, avg_outputs / 2.5))

    # ---------------------------
    # QUALITY
    # ---------------------------
    quality_rubrics = [
        WorkflowRubric(
            name="technology_due_diligence_depth",
            llm_prompt=(
                """Evaluate technology due diligence depth. Award partial credit for:
                (a) comprehensive software architecture assessment with scalability analysis,
                (b) thorough code quality and technical debt evaluation,
                (c) cybersecurity audit with compliance verification,
                (d) infrastructure assessment and integration complexity mapping.
                Cite specific workflow resources/messages for evidence. Output a numeric score in [0, MAX]."""
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="business_due_diligence_thoroughness",
            llm_prompt=(
                """Assess business due diligence thoroughness: (1) SaaS metrics validation accuracy,
                (2) customer contract analysis completeness, (3) revenue sustainability assessment,
                (4) operational workflow evaluation depth. Award equal partial credit. Output numeric score [0, MAX]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="integration_strategy_quality",
            llm_prompt=(
                """Evaluate integration strategy quality across technology, human capital, and customer dimensions.
                Assess platform compatibility planning, talent retention strategies, and service continuity protocols.
                Output numeric score [0, MAX]."""
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="due_diligence_completeness_measure",
            evaluator_function=due_diligence_completeness,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="systems_integration_excellence",
            llm_prompt=(
                """Assess systems integration excellence: data migration planning, API integration design,
                security infrastructure harmonization, and service continuity assurance. Evaluate technical depth
                and risk mitigation strategies. Output numeric score [0, MAX]."""
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="systems_integration_quality_measure",
            evaluator_function=systems_integration_quality,
            max_score=1.0,
            run_condition=RunCondition.EACH_TIMESTEP,
        ),
        WorkflowRubric(
            name="integration_artifact_density_measure",
            evaluator_function=integration_artifact_density,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # ---------------------------
    # COMPLIANCE (Acquisition-focused)
    # ---------------------------
    compliance_rubrics = [
        WorkflowRubric(
            name="regulatory_compliance_completeness",
            llm_prompt=(
                """Evaluate regulatory compliance completeness: HSR filing preparation, antitrust clearance coordination,
                data privacy compliance verification (GDPR/CCPA), and cross-border regulatory requirements.
                Award partial credit with citations. Output numeric score [0, MAX]."""
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="ip_ownership_validation",
            llm_prompt=(
                """Assess IP ownership validation thoroughness: software licensing compliance, intellectual property
                verification, ownership transfer documentation, and legal risk mitigation strategies.
                Output numeric score [0, MAX]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="data_privacy_security_compliance",
            llm_prompt=(
                """Evaluate data privacy and security compliance: GDPR/CCPA adherence, data handling protocols,
                security infrastructure standards, and cross-border data transfer compliance.
                Output numeric score [0, MAX]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="legal_documentation_quality",
            llm_prompt=(
                """Assess legal documentation quality: contract analysis completeness, legal risk assessment depth,
                compliance verification procedures, and audit trail maintenance. Output numeric score [0, MAX]."""
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="regulatory_approval_progress_measure",
            evaluator_function=regulatory_approval_progress,
            max_score=1.0,
            run_condition=RunCondition.EACH_TIMESTEP,
        ),
        WorkflowRubric(
            name="multi_jurisdiction_coordination",
            llm_prompt=(
                """Evaluate multi-jurisdiction regulatory coordination: North America and Europe compliance management,
                timeline synchronization, and cross-border approval process efficiency. Output numeric score [0, MAX]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="acquisition_crisis_scenarios",
            llm_prompt=(
                """Evaluate handling of tech acquisition crisis scenarios:
                - shows preparation for regulatory challenges and antitrust concerns
                - demonstrates response to integration difficulties and cultural clashes
                - shows handling of talent retention issues and technology incompatibilities
                - demonstrates preparation for competitive responses and customer churn risks
                - shows due diligence gap management and deal breakage risk mitigation
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
    # GOVERNANCE
    # ---------------------------
    governance_rubrics = [
        WorkflowRubric(
            name="integration_management_effectiveness",
            llm_prompt=(
                """Evaluate integration management office effectiveness: governance structure clarity, cross-functional
                team formation, decision-making frameworks, and project management infrastructure quality.
                Award partial credit across components. Output numeric score [0, MAX]."""
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="stakeholder_coordination_quality",
            llm_prompt=(
                """Assess stakeholder coordination quality: executive steering committee engagement, cross-functional
                collaboration, communication protocol effectiveness, and escalation procedure clarity.
                Output numeric score [0, MAX]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="risk_management_framework",
            llm_prompt=(
                """Evaluate risk management framework: integration risk identification, mitigation strategies,
                contingency planning, and issue escalation procedures. Assess comprehensiveness and effectiveness.
                Output numeric score [0, MAX]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="decision_tracking_accountability",
            llm_prompt=(
                """Assess decision tracking and accountability: decision documentation quality, approval workflows,
                accountability assignment, and progress tracking mechanisms. Output numeric score [0, MAX]."""
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="stakeholder_communication_management",
            llm_prompt=(
                """Evaluate stakeholder communication management: communication strategy effectiveness, progress reporting
                quality, transparency maintenance, and stakeholder engagement throughout integration process.
                Output numeric score [0, MAX]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # ---------------------------
    # SPEED
    # ---------------------------
    speed_rubrics = [
        # Acquisition-specific timing measures
        WorkflowRubric(
            name="critical_timeline_adherence",
            llm_prompt=(
                """Evaluate adherence to critical acquisition timelines: 90-day systems integration, 180-day full
                integration, regulatory approval coordination. Award partial credit based on timeline compliance.
                Output numeric score [0, MAX]."""
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="integration_timeline_adherence_measure",
            evaluator_function=integration_timeline_adherence,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="due_diligence_efficiency",
            llm_prompt=(
                """Assess due diligence process efficiency: technology, business, and regulatory workstream coordination,
                parallel execution effectiveness, and milestone achievement speed. Output numeric score [0, MAX]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Standard speed measures
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
            name="integration_budget_management",
            llm_prompt=(
                """Evaluate integration budget management: cost containment within ±10% variance, resource allocation
                efficiency, and value optimization for acquisition investments. Output numeric score [0, MAX]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="synergy_cost_effectiveness",
            llm_prompt=(
                """Assess synergy realization cost-effectiveness: operational efficiency improvements, cost savings
                identification, and integration ROI optimization. Output numeric score [0, MAX]."""
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="due_diligence_cost_optimization",
            llm_prompt=(
                """Evaluate due diligence cost optimization: resource utilization efficiency, external advisor
                management, and cost-benefit analysis quality. Output numeric score [0, MAX]."""
            ),
            max_score=4.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # ---------------------------
    # INTEGRATION SUCCESS
    # ---------------------------
    integration_success_rubrics = [
        WorkflowRubric(
            name="talent_retention_achievement",
            llm_prompt=(
                """Evaluate talent retention achievement: >85% retention target for technical leadership,
                cultural integration success, compensation harmonization effectiveness, and employee satisfaction
                maintenance. Output numeric score [0, MAX]."""
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="customer_retention_preservation",
            llm_prompt=(
                """Assess customer retention preservation: <5% churn target achievement, service continuity maintenance,
                customer satisfaction scores >90%, and value proposition enhancement success.
                Output numeric score [0, MAX]."""
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="service_continuity_excellence",
            llm_prompt=(
                """Evaluate service continuity excellence: >99.5% uptime achievement, zero customer data loss,
                minimal disruption during integration, and enhanced security posture. Output numeric score [0, MAX]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="stakeholder_retention_tracking_measure",
            evaluator_function=stakeholder_retention_tracking,
            max_score=1.0,
            run_condition=RunCondition.EACH_TIMESTEP,
        ),
        WorkflowRubric(
            name="synergy_realization_progress_measure",
            evaluator_function=synergy_realization_progress,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="cultural_integration_success",
            llm_prompt=(
                """Assess cultural integration success: unified values establishment, collaborative workflow development,
                leadership transition effectiveness, and integrated management practices. Output numeric score [0, MAX]."""
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    return PreferenceWeights(
        preferences=[
            Preference(
                name="quality",
                weight=0.25,
                evaluator=Evaluator(
                    name="quality",
                    rubrics=quality_rubrics,
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                ),
            ),
            Preference(
                name="compliance",
                weight=0.20,
                evaluator=Evaluator(
                    name="compliance",
                    rubrics=compliance_rubrics,
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                ),
            ),
            Preference(
                name="governance",
                weight=0.20,
                evaluator=Evaluator(
                    name="governance",
                    rubrics=governance_rubrics,
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                ),
            ),
            Preference(
                name="speed",
                weight=0.15,
                evaluator=Evaluator(
                    name="speed",
                    rubrics=speed_rubrics,
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                ),
            ),
            Preference(
                name="cost",
                weight=0.10,
                evaluator=Evaluator(
                    name="cost",
                    rubrics=cost_rubrics,
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                ),
            ),
            Preference(
                name="integration_success",
                weight=0.10,
                evaluator=Evaluator(
                    name="integration_success",
                    rubrics=integration_success_rubrics,
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                ),
            ),
        ]
    )


def create_preference_timeline():
    """Acquisition preference dynamics emphasizing due diligence early, then integration success."""

    return {
        0: PreferenceWeights(
            preferences=[
                Preference(name="quality", weight=0.35),
                Preference(name="compliance", weight=0.25),
                Preference(name="governance", weight=0.15),
                Preference(name="speed", weight=0.15),
                Preference(name="cost", weight=0.05),
                Preference(name="integration_success", weight=0.05),
            ]
        ),
        8: PreferenceWeights(
            preferences=[
                Preference(name="quality", weight=0.30),
                Preference(name="compliance", weight=0.20),
                Preference(name="governance", weight=0.20),
                Preference(name="speed", weight=0.15),
                Preference(name="cost", weight=0.10),
                Preference(name="integration_success", weight=0.05),
            ]
        ),
        15: PreferenceWeights(
            preferences=[
                Preference(name="quality", weight=0.25),
                Preference(name="compliance", weight=0.15),
                Preference(name="governance", weight=0.20),
                Preference(name="speed", weight=0.15),
                Preference(name="cost", weight=0.10),
                Preference(name="integration_success", weight=0.15),
            ]
        ),
        25: PreferenceWeights(
            preferences=[
                Preference(name="quality", weight=0.20),
                Preference(name="compliance", weight=0.10),
                Preference(name="governance", weight=0.15),
                Preference(name="speed", weight=0.10),
                Preference(name="cost", weight=0.15),
                Preference(name="integration_success", weight=0.30),
            ]
        ),
    }


def create_evaluator_to_measure_goal_achievement() -> Evaluator:
    """Create goal achievement evaluator for $150M SaaS platform acquisition and integration."""
    goal_achievement_rubrics = [
        # Critical technology and business integration deliverables (must have for successful acquisition)
        WorkflowRubric(
            name="technology_systems_integration_complete",
            llm_prompt=(
                "Does complete technology systems integration exist"
                "platform compatibility achieved, API integration operational, security infrastructure harmonized, and zero customer data loss? "
                "Return true if technology systems integration is complete, false otherwise."
            ),
            max_score=20.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="key_talent_retention_achieved",
            llm_prompt=(
                "Does achieved key talent retention exist with: >85% technical leadership retention confirmed, "
                "cultural integration successful, compensation harmonization completed, and leadership transition smooth? "
                "Return true if key talent retention is achieved, false otherwise."
            ),
            max_score=15.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="customer_churn_minimized",
            llm_prompt=(
                "Does minimized customer churn exist with: <5% customer churn during integration, "
                "service continuity assured, account management transition smooth, and customer satisfaction maintained? "
                "Return true if customer churn is minimized, false otherwise."
            ),
            max_score=15.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="regulatory_approvals_secured",
            llm_prompt=(
                "Do secured regulatory approvals exist with: all regulatory approvals obtained without conditions, "
                "HSR clearance confirmed, data privacy compliance verified (GDPR/CCPA), and cross-border requirements met? "
                "Return true if regulatory approvals are secured, false otherwise."
            ),
            max_score=12.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Major due diligence and compliance deliverables (8-10 points each)
        WorkflowRubric(
            name="technology_due_diligence_complete",
            llm_prompt=(
                "Does complete technology due diligence exist with: software architecture assessed, "
                "code quality analyzed, cybersecurity audit completed, IP ownership verified, and technical debt quantified? "
                "Return true if technology due diligence is complete, false otherwise."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="business_financial_validation",
            llm_prompt=(
                "Does business and financial validation exist with: SaaS metrics validated (ARR, churn, CAC, LTV), "
                "customer contract analysis completed, recurring revenue sustainability confirmed, and competitive positioning evaluated? "
                "Return true if business and financial validation is complete, false otherwise."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="ip_ownership_transfer_validated",
            llm_prompt=(
                "Does validated IP ownership transfer exist with: IP ownership fully validated, "
                "software licensing confirmed, patent portfolio transferred, and intellectual property rights secured? "
                "Return true if IP ownership transfer is validated, false otherwise."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="integration_budget_variance_control",
            llm_prompt=(
                "Does integration budget variance control exist with: <10% budget variance achieved, "
                "cost management effective, resource allocation optimized, and financial targets met? "
                "Return true if integration budget variance is controlled, false otherwise."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="synergy_targets_achievement",
            llm_prompt=(
                "Does synergy targets achievement exist with: synergy targets achieved within 12 months, "
                "cost synergies realized, revenue synergies captured, and integration value demonstrated? "
                "Return true if synergy targets are achieved, false otherwise."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Important supporting deliverables (5-7 points each)
        WorkflowRubric(
            name="integration_management_office_operational",
            llm_prompt=(
                "Does operational integration management office exist with: executive steering committee active, "
                "cross-functional integration teams coordinated, governance structure established, and project management infrastructure operational? "
                "Return true if integration management office is operational, false otherwise."
            ),
            max_score=7.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="service_continuity_protocols_maintained",
            llm_prompt=(
                "Do maintained service continuity protocols exist with: customer-facing system stability prioritized, "
                "competitive market position maintained, service level agreements met, and operational excellence sustained? "
                "Return true if service continuity protocols are maintained, false otherwise."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="cultural_integration_success",
            llm_prompt=(
                "Does cultural integration success exist with: unified values established, "
                "collaborative workflows implemented, cultural assessment completed, and team cohesion achieved? "
                "Return true if cultural integration is successful, false otherwise."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="data_migration_security_validated",
            llm_prompt=(
                "Does validated data migration security exist with: data migration completed securely, "
                "security protocols maintained, data integrity verified, and privacy compliance ensured? "
                "Return true if data migration security is validated, false otherwise."
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="customer_relationship_preservation",
            llm_prompt=(
                "Does customer relationship preservation exist with: customer notification strategy executed, "
                "account management transition smooth, value proposition enhanced, and customer satisfaction monitored? "
                "Return true if customer relationships are preserved, false otherwise."
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Supporting deliverables (3-4 points each)
        WorkflowRubric(
            name="market_positioning_synergy_realized",
            llm_prompt=(
                "Does realized market positioning synergy exist with: competitive advantage articulated, "
                "product roadmap integration planned, cross-selling opportunities identified, and market strategy unified? "
                "Return true if market positioning synergy is realized, false otherwise."
            ),
            max_score=4.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="post_integration_revenue_growth",
            llm_prompt=(
                "Does post-integration revenue growth exist with: revenue growth trajectory maintained or improved, "
                "revenue enhancement strategies implemented, customer expansion achieved, and financial performance optimized? "
                "Return true if post-integration revenue growth is achieved, false otherwise."
            ),
            max_score=4.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="infrastructure_scalability_validated",
            llm_prompt=(
                "Does validated infrastructure scalability exist with: scalability assessment completed, "
                "infrastructure capacity confirmed, performance optimization achieved, and growth readiness ensured? "
                "Return true if infrastructure scalability is validated, false otherwise."
            ),
            max_score=3.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="operational_workflow_integration",
            llm_prompt=(
                "Does operational workflow integration exist with: workflows harmonized, "
                "process integration completed, operational efficiency maintained, and best practices consolidated? "
                "Return true if operational workflow integration is successful, false otherwise."
            ),
            max_score=3.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    return Evaluator(
        name="tech_acquisition_integration_goal_achievement_eval",
        description="Technology company acquisition and integration deliverable achievement measurement",
        aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
        rubrics=goal_achievement_rubrics,
    )
