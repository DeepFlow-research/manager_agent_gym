"""
Global Product Recall & Market Re-entry Strategy Demo
Real-world use case: Automotive safety component recall affecting 2M vehicles
across 15 countries with comprehensive remediation and market re-entry.
Demonstrates:
- Crisis decision-making under extreme time pressure with safety-first prioritization
- Multi-stakeholder coordination across regulatory authorities, consumers, and supply chains
- Dynamic preference evolution from crisis response to recovery optimization
- Complex parallel task management with interdependent global operations
- Executive escalation protocols with documented decision authority under uncertainty
- Adaptive resource allocation balancing immediate response with long-term recovery
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
        """Penalize unrealistic cost discrepancies for product recalls."""
        expected_min_cost = 200000.0  # Minimum realistic cost
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
            return 0.0  # Product recalls should cost >$200k

        cost_variance = abs(total_actual - total_estimated) / total_estimated
        if cost_variance > 0.5:  # Recalls have high cost uncertainty
            return 0.2
        elif cost_variance > 0.3:
            return 0.6
        else:
            return 1.0

    def _recall_adversarial_pressure_score(workflow: Workflow) -> float:
        """Score based on handling recall adversarial pressure."""
        pressure_indicators = [
            "media scrutiny",
            "regulatory investigation",
            "customer backlash",
            "legal liability",
            "supply chain disruption",
            "competitor advantage",
            "brand damage",
            "safety criticism",
            "class action suit",
            "recall expansion",
            "regulator enforcement",
            "public outcry",
        ]

        pressure_handled = 0
        for indicator in pressure_indicators:
            for res in workflow.resources.values():
                if indicator.lower() in str(res.content or "").lower():
                    if any(
                        resolution.lower() in str(res.content or "").lower()
                        for resolution in [
                            "managed",
                            "addressed",
                            "mitigated",
                            "contained",
                        ]
                    ):
                        pressure_handled += 1
                    break

        return min(1.0, pressure_handled / max(1, len(pressure_indicators) * 0.3))

    def crisis_response_speed(workflow: Workflow) -> float:
        """Reward fast initial crisis response within 72 hours (0..1)."""
        crisis_keywords = (
            "crisis",
            "assessment",
            "safety",
            "notification",
            "emergency",
        )
        fast_completed = []

        for task in workflow.tasks.values():
            task_desc = (task.description or "").lower()
            task_name = (task.name or "").lower()
            if any(k in task_desc or k in task_name for k in crisis_keywords):
                if (
                    task.status.value == "completed"
                    and task.completed_at
                    and workflow.started_at
                ):
                    hours_to_complete = _safe_hours(
                        (task.completed_at - workflow.started_at).total_seconds()
                    )
                    if hours_to_complete <= 72.0:  # Within 72 hour crisis window
                        fast_completed.append(hours_to_complete)

        if not fast_completed:
            return 0.0

        # Reward based on average speed of crisis tasks (faster = better)
        avg_hours = sum(fast_completed) / len(fast_completed)
        # Exponential reward for speed (72 hours = 0.5, 24 hours = ~0.8, 12 hours = ~0.9)
        return exp(-avg_hours / 36.0)

    def consumer_safety_prioritization(workflow: Workflow) -> float:
        """Reward evidence of consumer safety prioritization over cost concerns (0..1)."""
        safety_keywords = (
            "safety",
            "consumer",
            "injury",
            "hazard",
            "incident",
            "protection",
        )
        cost_keywords = ("cost", "budget", "expense", "financial", "savings")

        safety_mentions = 0
        cost_mentions = 0

        for res in workflow.resources.values():
            try:
                content = (res.content or "").lower()
                safety_mentions += sum(1 for k in safety_keywords if k in content)
                cost_mentions += sum(1 for k in cost_keywords if k in content)
            except Exception:
                continue

        total_mentions = safety_mentions + cost_mentions
        if total_mentions == 0:
            return 0.5  # neutral

        # Reward higher ratio of safety vs cost discussions
        safety_ratio = safety_mentions / total_mentions
        return min(1.0, safety_ratio * 1.5)  # Cap at 1.0, boost safety focus

    def regulatory_coordination_effectiveness(workflow: Workflow) -> float:
        """Reward coordination across multiple regulatory jurisdictions (0..1)."""
        regulatory_keywords = (
            "nhtsa",
            "transport canada",
            "eu gpsr",
            "regulatory",
            "authority",
            "jurisdiction",
        )
        coordination_keywords = (
            "coordinate",
            "synchronize",
            "timeline",
            "filing",
            "submission",
        )

        reg_hits = 0
        coord_hits = 0
        total_resources = 0

        for res in workflow.resources.values():
            total_resources += 1
            try:
                content = (res.content or "").lower()
                if any(k in content for k in regulatory_keywords):
                    reg_hits += 1
                if any(k in content for k in coordination_keywords):
                    coord_hits += 1
            except Exception:
                continue

        if total_resources == 0:
            return 0.0

        # Both regulatory coverage and coordination evidence needed
        reg_coverage = min(
            1.0, reg_hits / max(1, total_resources * 0.3)
        )  # Expect 30% to mention regulators
        coord_evidence = min(
            1.0, coord_hits / max(1, total_resources * 0.2)
        )  # Expect 20% to mention coordination

        return (reg_coverage * coord_evidence) ** 0.5  # Geometric mean

    def stakeholder_communication_coverage(workflow: Workflow) -> float:
        """Reward comprehensive stakeholder communication (0..1)."""
        stakeholder_types = (
            "consumer",
            "dealer",
            "supplier",
            "media",
            "investor",
            "regulator",
            "employee",
        )
        communication_channels = (
            "notification",
            "hotline",
            "portal",
            "campaign",
            "briefing",
            "update",
        )

        stakeholder_coverage = set()
        channel_coverage = set()

        for res in workflow.resources.values():
            try:
                content = (res.content or "").lower()
                for stakeholder in stakeholder_types:
                    if stakeholder in content:
                        stakeholder_coverage.add(stakeholder)
                for channel in communication_channels:
                    if channel in content:
                        channel_coverage.add(channel)
            except Exception:
                continue

        # Score based on breadth of stakeholder and channel coverage
        stakeholder_score = len(stakeholder_coverage) / len(stakeholder_types)
        channel_score = len(channel_coverage) / len(communication_channels)

        return (stakeholder_score + channel_score) / 2.0

    def recall_completion_tracking(workflow: Workflow) -> float:
        """Reward evidence of recall completion tracking and monitoring (0..1)."""
        tracking_keywords = (
            "completion",
            "response rate",
            "tracking",
            "monitoring",
            "effectiveness",
            "95%",
            "target",
        )

        tracking_evidence = 0
        total_resources = 0

        for res in workflow.resources.values():
            total_resources += 1
            try:
                content = (res.content or "").lower()
                if any(k in content for k in tracking_keywords):
                    tracking_evidence += 1
            except Exception:
                continue

        if total_resources == 0:
            return 0.0

        # Expect tracking evidence in at least 15% of resources
        return min(1.0, tracking_evidence / max(1, total_resources * 0.15))

    def crisis_timeline_adherence(workflow: Workflow) -> float:
        """Penalty for delays in crisis-critical tasks (0..1)."""
        crisis_keywords = (
            "crisis",
            "emergency",
            "immediate",
            "urgent",
            "notification",
            "safety",
        )
        total_est = 0.0
        total_act = 0.0

        for task in workflow.tasks.values():
            task_desc = (task.description or "").lower() + (task.name or "").lower()
            if any(k in task_desc for k in crisis_keywords):
                if task.estimated_duration_hours is not None:
                    total_est += float(task.estimated_duration_hours)
                if task.actual_duration_hours is not None:
                    total_act += float(task.actual_duration_hours)

        if total_est <= 0.0:
            return 0.5  # neutral when no estimates

        # Stricter penalty for crisis tasks
        over = max(0.0, total_act - total_est) / total_est
        return exp(-1.5 * over)  # Harsher penalty than regular tasks

    # ---------------------------
    # CONSUMER SAFETY
    # ---------------------------
    consumer_safety_rubrics = [
        WorkflowRubric(
            name="immediate_safety_response",
            llm_prompt=(
                """Evaluate immediate safety response effectiveness. Award credit for evidence of:
                (a) rapid safety assessment and risk characterization within 72 hours,
                (b) prompt regulatory notifications to all relevant authorities,
                (c) immediate consumer safety warnings and communication deployment,
                (d) product quarantine and sales halt implementation.
                Cite specific workflow resources/messages for evidence. Output a numeric score in [0, MAX]."""
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="zero_tolerance_safety_incidents",
            llm_prompt=(
                """Assess prevention of additional safety incidents post-recall announcement:
                evidence of hazard containment, monitoring systems, and incident prevention measures.
                Penalize any evidence of additional injuries or safety failures. Output numeric score [0, MAX]."""
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="consumer_protection_prioritization",
            llm_prompt=(
                """Evaluate consumer protection prioritization over financial considerations:
                evidence of safety-first decision making, resource allocation, and communication messaging.
                Award credit for explicit safety prioritization statements. Output numeric score [0, MAX]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="safety_prioritization_signal",
            evaluator_function=consumer_safety_prioritization,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="crisis_response_speed_signal",
            evaluator_function=crisis_response_speed,
            max_score=1.0,
            run_condition=RunCondition.EACH_TIMESTEP,
        ),
        # Evidence gate: safety deliverables must exist
        WorkflowRubric(
            name="safety_deliverables_evidence",
            llm_prompt=(
                "Award credit ONLY if concrete safety deliverables exist: completed Safety Impact Assessment,\n"
                "regulator notification letters/receipts, consumer warning artifacts (templates/dispatch logs), and quarantine proofs. [0,10]"
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # ---------------------------
    # REGULATORY COMPLIANCE
    # ---------------------------
    regulatory_compliance_rubrics = [
        WorkflowRubric(
            name="multi_jurisdiction_coordination",
            llm_prompt=(
                """Evaluate multi-jurisdiction regulatory coordination across 15 countries. Award credit for evidence of:
                (a) synchronized regulatory filings with NHTSA, Transport Canada, EU GPSR,
                (b) coordinated timeline management across jurisdictions,
                (c) consistent defect characterization and risk assessment,
                (d) proactive regulatory relationship management.
                Output numeric score [0, MAX]."""
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="regulatory_approval_achievement",
            llm_prompt=(
                """Assess regulatory approval achievement for market re-entry:
                evidence of regulatory sign-offs, compliance validation, and approval documentation
                across all 15 markets. Output numeric score [0, MAX]."""
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="compliance_documentation_completeness",
            llm_prompt=(
                """Evaluate regulatory compliance documentation completeness:
                recall effectiveness monitoring, audit trails, status reporting,
                and regulatory relationship maintenance. Output numeric score [0, MAX]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="regulatory_excellence_standard",
            llm_prompt=(
                """Assess adherence to regulatory excellence standard:
                evidence of exceeding minimum compliance requirements, proactive communication,
                and maintaining excellent regulatory standing. Output numeric score [0, MAX]."""
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="regulatory_coordination_signal",
            evaluator_function=regulatory_coordination_effectiveness,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # ---------------------------
    # CRISIS MANAGEMENT
    # ---------------------------
    crisis_management_rubrics = [
        WorkflowRubric(
            name="crisis_team_activation_effectiveness",
            llm_prompt=(
                """Evaluate crisis management team activation and coordination:
                24/7 operations setup, executive authority establishment, decision-making protocols,
                and cross-functional team coordination under pressure. Output numeric score [0, MAX]."""
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="stakeholder_communication_strategy",
            llm_prompt=(
                """Assess stakeholder communication strategy effectiveness:
                multi-channel consumer notifications, media relations, dealer coordination,
                and regulatory authority liaison management. Output numeric score [0, MAX]."""
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="decision_authority_documentation",
            llm_prompt=(
                """Evaluate decision authority documentation and governance:
                documented decision-making authority, executive escalation protocols,
                audit trail maintenance, and governance under uncertainty. Output numeric score [0, MAX]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="crisis_timeline_management",
            llm_prompt=(
                """Assess crisis timeline management and milestone achievement:
                72-hour initial response, 6-month recall completion target,
                and 18-month market re-entry timeline adherence. Output numeric score [0, MAX]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="stakeholder_communication_coverage_signal",
            evaluator_function=stakeholder_communication_coverage,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="crisis_timeline_adherence_signal",
            evaluator_function=crisis_timeline_adherence,
            max_score=1.0,
            run_condition=RunCondition.EACH_TIMESTEP,
        ),
        # Evidence gate: comms and governance artifacts
        WorkflowRubric(
            name="comms_governance_artifacts_evidence",
            llm_prompt=(
                "Require uploaded artifacts for: consumer comms (templates, schedules, dispatch proof), media decision tree, dealer kit,\n"
                "and decision authority/escalation docs with sign-offs. Return 0 if missing. [0,8]"
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # ---------------------------
    # OPERATIONAL EXECUTION
    # ---------------------------
    operational_execution_rubrics = [
        WorkflowRubric(
            name="global_logistics_coordination",
            llm_prompt=(
                """Evaluate global product retrieval logistics coordination:
                reverse supply chain activation, dealer network coordination,
                customer return processing, and disposal/recycling protocols across 15 countries.
                Output numeric score [0, MAX]."""
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="recall_completion_effectiveness",
            llm_prompt=(
                """Assess recall completion effectiveness targeting >95% completion rate:
                consumer response tracking, targeted outreach programs,
                effectiveness monitoring, and completion rate achievement. Output numeric score [0, MAX]."""
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="root_cause_remediation_quality",
            llm_prompt=(
                """Evaluate root cause analysis and remediation quality:
                technical failure investigation depth, design modification validation,
                enhanced testing protocols, and supplier quality improvements. Output numeric score [0, MAX]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="supply_chain_partner_retention",
            llm_prompt=(
                """Assess supply chain partner and dealer network retention:
                enhanced quality agreements, relationship maintenance,
                and confidence preservation throughout crisis. Output numeric score [0, MAX]."""
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="recall_completion_tracking_signal",
            evaluator_function=recall_completion_tracking,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Evidence gate: logistics artifacts per country
        WorkflowRubric(
            name="logistics_artifacts_evidence",
            llm_prompt=(
                "Award credit only if country-level reverse-logistics plans, dealer coordination agreements, customer return SOPs,\n"
                "and disposal vendor protocols are present. Cite IDs. [0,10]"
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # ---------------------------
    # BRAND RECOVERY
    # ---------------------------
    brand_recovery_rubrics = [
        WorkflowRubric(
            name="customer_confidence_restoration",
            llm_prompt=(
                """Evaluate customer confidence restoration strategy targeting >80% pre-recall levels:
                confidence rebuilding campaigns, safety messaging effectiveness,
                brand reputation monitoring, and customer trust recovery metrics. Output numeric score [0, MAX]."""
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="market_reentry_strategy_quality",
            llm_prompt=(
                """Assess market re-entry strategy quality and execution:
                product redesign validation, enhanced quality protocols,
                competitive repositioning, and sales resumption readiness. Output numeric score [0, MAX]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="brand_reputation_recovery_evidence",
            llm_prompt=(
                """Evaluate brand reputation recovery evidence and measurement:
                independent survey results, brand perception monitoring,
                media sentiment analysis, and reputation recovery demonstration. Output numeric score [0, MAX]."""
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="competitive_repositioning_effectiveness",
            llm_prompt=(
                """Assess competitive repositioning effectiveness:
                safety leadership positioning, enhanced quality messaging,
                market differentiation strategy, and competitive advantage rebuilding. Output numeric score [0, MAX]."""
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Evidence gate: reputation and confidence metrics
        WorkflowRubric(
            name="reputation_metrics_evidence",
            llm_prompt=(
                "Require independent survey results, brand-sentiment dashboards, and recovery KPI reports before awarding credit. [0,10]"
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # ---------------------------
    # FINANCIAL RISK MANAGEMENT
    # ---------------------------
    financial_risk_rubrics = [
        WorkflowRubric(
            name="financial_impact_containment",
            llm_prompt=(
                """Evaluate financial impact containment within crisis budget parameters:
                cost management effectiveness, insurance coverage optimization,
                and financial impact mitigation measures. Output numeric score [0, MAX]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="legal_liability_management",
            llm_prompt=(
                """Assess legal liability management across 15 jurisdictions:
                litigation strategy development, liability exposure minimization,
                and legal risk mitigation effectiveness. Output numeric score [0, MAX]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="insurance_claims_optimization",
            llm_prompt=(
                """Evaluate insurance claims processing and coverage optimization:
                claims submission completeness, coverage maximization,
                and recovery strategy effectiveness. Output numeric score [0, MAX]."""
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="cost_efficiency",
            evaluator_function=cost_rubric,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Evidence gate: insurance and liability artifacts
        WorkflowRubric(
            name="insurance_liability_artifacts_evidence",
            llm_prompt=(
                "Require filed insurance claims package, coverage analysis, litigation strategy docs, and exposure matrices before credit. [0,10]"
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # ---------------------------
    # SPEED (Crisis Response)
    # ---------------------------
    speed_rubrics = [
        # Deterministic
        WorkflowRubric(
            name="crisis_response_speed",
            evaluator_function=crisis_response_speed,
            max_score=1.0,
            run_condition=RunCondition.EACH_TIMESTEP,
        ),
        WorkflowRubric(
            name="crisis_timeline_adherence",
            evaluator_function=crisis_timeline_adherence,
            max_score=1.0,
            run_condition=RunCondition.EACH_TIMESTEP,
        ),
        # Standard speed rule
        WorkflowRubric(
            name="speed_efficiency",
            evaluator_function=speed_rubric,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # LLM speed assessments
        WorkflowRubric(
            name="emergency_response_timing",
            llm_prompt=(
                """Evaluate emergency response timing and urgency management:
                72-hour crisis response window, regulatory notification speed,
                and consumer safety warning deployment timing. Output numeric score [0, MAX]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="milestone_achievement_pace",
            llm_prompt=(
                """Assess milestone achievement pace for 6-month recall completion:
                progress tracking, timeline adherence, and acceleration strategies
                for meeting critical deadlines. Output numeric score [0, MAX]."""
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    return PreferenceWeights(
        preferences=[
            Preference(
                name="consumer_safety",
                weight=0.40,
                evaluator=Evaluator(
                    name="consumer_safety",
                    description="Measures the consumer safety of the crisis response",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=consumer_safety_rubrics,
                ),
            ),
            Preference(
                name="regulatory_compliance",
                weight=0.25,
                evaluator=Evaluator(
                    name="regulatory_compliance",
                    description="Measures the regulatory compliance of the crisis response",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=regulatory_compliance_rubrics,
                ),
            ),
            Preference(
                name="crisis_management",
                weight=0.15,
                evaluator=Evaluator(
                    name="crisis_management",
                    description="Measures the crisis management of the crisis response",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=crisis_management_rubrics,
                ),
            ),
            Preference(
                name="operational_execution",
                weight=0.10,
                evaluator=Evaluator(
                    name="operational_execution",
                    description="Measures the operational execution of the crisis response",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=operational_execution_rubrics,
                ),
            ),
            Preference(
                name="brand_recovery",
                weight=0.05,
                evaluator=Evaluator(
                    name="brand_recovery",
                    description="Measures the brand recovery of the crisis response",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=brand_recovery_rubrics,
                ),
            ),
            Preference(
                name="financial_risk_management",
                weight=0.03,
                evaluator=Evaluator(
                    name="financial_risk_management",
                    description="Measures the financial risk management of the crisis response",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=financial_risk_rubrics,
                ),
            ),
            Preference(
                name="speed",
                weight=0.02,
                evaluator=Evaluator(
                    name="speed",
                    description="Measures the speed of the crisis response",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=speed_rubrics,
                ),
            ),
        ]
    )


def create_preference_update_requests() -> list[PreferenceWeightUpdateRequest]:
    """Return weight update requests for crisis → recovery dynamics."""
    timeline: dict[int, PreferenceWeights] = {
        0: PreferenceWeights(
            preferences=[
                Preference(name="consumer_safety", weight=0.5),
                Preference(name="regulatory_compliance", weight=0.2),
                Preference(name="crisis_management", weight=0.2),
                Preference(name="operational_execution", weight=0.05),
                Preference(name="brand_recovery", weight=0.02),
                Preference(name="financial_risk_management", weight=0.02),
                Preference(name="speed", weight=0.01),
            ]
        ),
        10: PreferenceWeights(
            preferences=[
                Preference(name="consumer_safety", weight=0.4),
                Preference(name="regulatory_compliance", weight=0.25),
                Preference(name="crisis_management", weight=0.2),
                Preference(name="operational_execution", weight=0.1),
                Preference(name="brand_recovery", weight=0.02),
                Preference(name="financial_risk_management", weight=0.02),
                Preference(name="speed", weight=0.01),
            ]
        ),
        25: PreferenceWeights(
            preferences=[
                Preference(name="consumer_safety", weight=0.35),
                Preference(name="regulatory_compliance", weight=0.25),
                Preference(name="crisis_management", weight=0.15),
                Preference(name="operational_execution", weight=0.15),
                Preference(name="brand_recovery", weight=0.05),
                Preference(name="financial_risk_management", weight=0.03),
                Preference(name="speed", weight=0.02),
            ]
        ),
        40: PreferenceWeights(
            preferences=[
                Preference(name="consumer_safety", weight=0.3),
                Preference(name="regulatory_compliance", weight=0.25),
                Preference(name="crisis_management", weight=0.1),
                Preference(name="operational_execution", weight=0.15),
                Preference(name="brand_recovery", weight=0.1),
                Preference(name="financial_risk_management", weight=0.05),
                Preference(name="speed", weight=0.05),
            ]
        ),
        60: PreferenceWeights(
            preferences=[
                Preference(name="consumer_safety", weight=0.25),
                Preference(name="regulatory_compliance", weight=0.2),
                Preference(name="crisis_management", weight=0.05),
                Preference(name="operational_execution", weight=0.15),
                Preference(name="brand_recovery", weight=0.2),
                Preference(name="financial_risk_management", weight=0.1),
                Preference(name="speed", weight=0.05),
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
    """Create goal achievement evaluator for global product recall and market re-entry strategy."""
    goal_achievement_rubrics = [
        # Critical safety and regulatory deliverables (absolutely must have for recall success)
        WorkflowRubric(
            name="recall_execution_framework_ready",
            llm_prompt=(
                "Does ready recall execution framework exist with: comprehensive tracking methodology for all 15 markets, "
                "consumer response monitoring system designed, completion rate measurement framework established, and reporting templates prepared? "
                "Return true if recall execution framework is ready for deployment, false otherwise."
            ),
            max_score=20.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="safety_incident_prevention_protocols_established",
            llm_prompt=(
                "Do established safety incident prevention protocols exist with: comprehensive hazard containment procedures documented, "
                "safety monitoring framework implemented, incident response protocols operational, and prevention measures validated? "
                "Return true if safety incident prevention protocols are fully established, false otherwise."
            ),
            max_score=18.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="regulatory_notification_packages_prepared",
            llm_prompt=(
                "Do prepared regulatory notification packages exist with: NHTSA/Transport Canada/EU GPSR filing templates completed, "
                "national authority notification packages for 15 countries prepared, defect characterization fully documented, and coordinated submission timeline established? "
                "Return true if regulatory notification packages are prepared and ready for submission, false otherwise."
            ),
            max_score=15.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="market_reentry_strategy_documented",
            llm_prompt=(
                "Does documented market re-entry strategy exist with: comprehensive re-entry plan for all jurisdictions, "
                "enhanced quality protocols framework established, product redesign specifications completed, and approval pathway strategy defined? "
                "Return true if market re-entry strategy is fully documented and ready for execution, false otherwise."
            ),
            max_score=12.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Major operational and customer recovery deliverables (8-10 points each)
        WorkflowRubric(
            name="customer_confidence_metrics_restored",
            llm_prompt=(
                "Do restored customer confidence metrics exist with: >80% of pre-recall confidence levels achieved within 12 months, "
                "brand reputation recovery demonstrated through independent surveys, consumer trust indicators positive, and market positioning maintained? "
                "Return true if customer confidence metrics are restored, false otherwise."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="product_retrieval_logistics_operational",
            llm_prompt=(
                "Does operational product retrieval logistics exist with: reverse supply chain activated, "
                "dealer network coordination complete, customer return processing active, and affected inventory quarantined and disposed? "
                "Return true if product retrieval logistics are operational, false otherwise."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="root_cause_analysis_remediation",
            llm_prompt=(
                "Does root cause analysis and remediation exist with: technical failure investigation completed, "
                "design modifications developed, enhanced testing protocols implemented, and manufacturing process corrections validated? "
                "Return true if root cause analysis and remediation are complete, false otherwise."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="crisis_management_coordination",
            llm_prompt=(
                "Does crisis management coordination exist with: cross-functional recall team activated, "
                "executive communication protocols operational, 24/7 incident response capability active, and decision-making authority documented? "
                "Return true if crisis management coordination is effective, false otherwise."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="consumer_communication_campaign",
            llm_prompt=(
                "Does consumer communication campaign exist with: multi-channel safety notifications deployed (mail/electronic/dealer), "
                "customer service hotline operational, media relations strategy active, and regulatory-compliant messaging maintained? "
                "Return true if consumer communication campaign is effective, false otherwise."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Important supporting deliverables (5-7 points each)
        WorkflowRubric(
            name="regulatory_compliance_documentation",
            llm_prompt=(
                "Does regulatory compliance documentation exist with: recall effectiveness monitoring active, "
                "consumer response tracking operational, regulatory status reporting current, and audit trail maintained across all markets? "
                "Return true if regulatory compliance documentation is complete, false otherwise."
            ),
            max_score=7.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="financial_impact_contained",
            llm_prompt=(
                "Does contained financial impact exist with: crisis management budget parameters maintained, "
                "insurance coverage maximized, litigation exposure minimized, and financial stakeholder communication active? "
                "Return true if financial impact is contained, false otherwise."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="supply_chain_partners_retained",
            llm_prompt=(
                "Do retained supply chain partners exist with: enhanced quality agreements executed, "
                "supplier relationship preservation active, dealer network confidence maintained, and partnership value protected? "
                "Return true if supply chain partners are retained, false otherwise."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="legal_liability_management",
            llm_prompt=(
                "Does legal liability management exist with: liability management across jurisdictions, "
                "insurance claims processing active, litigation strategy developed, and legal risk mitigation operational? "
                "Return true if legal liability management is effective, false otherwise."
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="enhanced_quality_assurance",
            llm_prompt=(
                "Does enhanced quality assurance exist with: quality protocols upgraded, "
                "testing procedures enhanced, supplier quality improvements implemented, and validation evidence documented? "
                "Return true if enhanced quality assurance is operational, false otherwise."
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Supporting deliverables (3-4 points each)
        WorkflowRubric(
            name="social_media_crisis_management",
            llm_prompt=(
                "Does social media crisis management exist with: social media monitoring active, "
                "crisis response protocols implemented, reputation management strategies deployed, and online sentiment tracking operational? "
                "Return true if social media crisis management is effective, false otherwise."
            ),
            max_score=4.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="competitive_repositioning_plan",
            llm_prompt=(
                "Does competitive repositioning plan exist with: market positioning strategy updated, "
                "competitive advantages redefined, value proposition enhanced, and market share protection strategies active? "
                "Return true if competitive repositioning plan is established, false otherwise."
            ),
            max_score=4.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="disposal_recycling_protocols",
            llm_prompt=(
                "Do disposal and recycling protocols exist with: environmental compliance maintained, "
                "product disposal procedures documented, recycling partnerships established, and waste management optimized? "
                "Return true if disposal and recycling protocols are operational, false otherwise."
            ),
            max_score=3.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="recall_effectiveness_monitoring",
            llm_prompt=(
                "Does recall effectiveness monitoring exist with: monitoring systems operational, "
                "completion rate tracking active, consumer response analysis current, and effectiveness metrics reported? "
                "Return true if recall effectiveness monitoring is operational, false otherwise."
            ),
            max_score=3.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    return Evaluator(
        name="global_product_recall_goal_achievement_eval",
        description="Global product recall and market re-entry strategy deliverable achievement measurement",
        aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
        rubrics=goal_achievement_rubrics,
    )
