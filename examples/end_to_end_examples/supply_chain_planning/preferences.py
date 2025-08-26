"""
Suez Logistics – Supply Chain Planning Preferences

Preferences selected (4):
  - service_reliability : OTIF, dwell time, schedule integrity, exception handling
  - compliance         : customs/advance filings and Dangerous Goods controls
  - cost_efficiency    : utilization, empty repositioning, and cost variance
  - risk_resilience    : contingency playbooks, reroute/hold/advance triggers, control‑tower discipline

Mirrors schema patterns from examples:
  * PreferenceWeights / Preference
  * Evaluator(aggregation=AggregationStrategy.WEIGHTED_AVERAGE, rubrics=[WorkflowRubric...])
  * WorkflowRubric with llm_prompt or evaluator_function
  * create_*_preference_update_requests(): absolute, normalized timeline updates
"""

from typing import List
from manager_agent_gym.schemas.preferences.preference import (
    Preference,
    PreferenceWeights,
)
from manager_agent_gym.schemas.preferences.evaluator import (
    Evaluator,
    AggregationStrategy,
)
from manager_agent_gym.schemas.preferences.rubric import WorkflowRubric, RunCondition
from manager_agent_gym.schemas.preferences import PreferenceWeightUpdateRequest
from manager_agent_gym.schemas.core import Workflow
from manager_agent_gym.schemas.core.base import TaskStatus


# ---------------------------
# Deterministic rule helpers (Workflow -> score in [0, max])
# ---------------------------
def _pct_tasks_completed(workflow: Workflow, name_contains: str | None = None) -> float:
    tasks = list(workflow.tasks.values())
    if name_contains:
        tasks = [t for t in tasks if name_contains.lower() in (t.name or "").lower()]
    if not tasks:
        return 0.0
    done = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
    return done / len(tasks)


def _task_completed(workflow: Workflow, name_contains: str) -> float:
    return 1.0 if _pct_tasks_completed(workflow, name_contains) >= 1.0 else 0.0


# ---------------------------
# Hardening Framework Functions
# ---------------------------
def _validate_cost_realism(workflow: Workflow, context) -> float:
    """Penalize unrealistic cost discrepancies for supply chain planning."""
    expected_min_cost = 40000.0  # Minimum realistic cost
    total_estimated = sum(
        task.estimated_cost for task in workflow.tasks.values() if task.estimated_cost
    )
    total_actual = sum(
        task.actual_cost for task in workflow.tasks.values() if task.actual_cost
    )

    if total_estimated == 0:
        return 0.0
    if total_actual < expected_min_cost:
        return 0.0  # Supply chain planning should cost >$40k

    cost_variance = abs(total_actual - total_estimated) / total_estimated
    if cost_variance > 0.3:
        return 0.2
    elif cost_variance > 0.15:
        return 0.6
    else:
        return 1.0


def _require_external_validation(
    workflow: Workflow, validation_keywords: List[str]
) -> float:
    """Require evidence of external validation for supply chain operations."""
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
                    "confirmed",
                    "verified",
                    "certified",
                ]
            ):
                validation_evidence += 1

    return min(1.0, validation_evidence / max(1, total_tasks * 0.25))


def _supply_chain_adversarial_pressure_score(workflow: Workflow) -> float:
    """Score based on handling supply chain adversarial pressure and disruptions."""
    pressure_indicators = [
        "supply disruption",
        "carrier delay",
        "port congestion",
        "customs hold",
        "strike action",
        "weather delay",
        "capacity shortage",
        "equipment shortage",
        "route disruption",
        "fuel price surge",
        "trade dispute",
        "force majeure",
    ]

    pressure_handled = 0
    for indicator in pressure_indicators:
        for res in workflow.resources.values():
            if indicator.lower() in str(res.content or "").lower():
                if any(
                    resolution.lower() in str(res.content or "").lower()
                    for resolution in [
                        "mitigated",
                        "resolved",
                        "alternative",
                        "contingency",
                        "backup",
                    ]
                ):
                    pressure_handled += 1
                break

    return min(1.0, pressure_handled / max(1, len(pressure_indicators) * 0.3))


# SERVICE RELIABILITY rules (schedule integrity + ops readiness)
def rule_slots_and_rotation_confirmed(workflow: Workflow) -> float:
    return 0.5 * _task_completed(
        workflow, "Suez Transit Slot & Convoy Planning"
    ) + 0.5 * _task_completed(workflow, "Vessel ETA & Rotation Alignment")


def rule_control_tower_live(workflow: Workflow) -> float:
    return _task_completed(workflow, "Execution Control Tower Setup")


def rule_gate_cutoffs_live(workflow: Workflow) -> float:
    return _task_completed(workflow, "Gate-In & Cutoff Management")


# COMPLIANCE rules (customs/DG)
def rule_customs_ready(workflow: Workflow) -> float:
    return _task_completed(workflow, "Customs & Documentation")


def rule_dg_cleared(workflow: Workflow) -> float:
    return _task_completed(workflow, "Dangerous Goods (DG) Screening")


# COST EFFICIENCY rules (utilization + empty repositioning)
def rule_capacity_plan_ready(workflow: Workflow) -> float:
    return _task_completed(workflow, "Network & Capacity Plan")


def rule_repositioning_planned(workflow: Workflow) -> float:
    return _task_completed(workflow, "Equipment & Container Repositioning")


# RISK RESILIENCE rules (contingencies + exception handling)
def rule_contingency_defined(workflow: Workflow) -> float:
    return _task_completed(workflow, "Risk & Contingency Planning")


def rule_ops_exception_loop_running(workflow: Workflow) -> float:
    return _task_completed(workflow, "Daily Operations & Exception Handling")


# ---------------------------
# LLM Rubrics
# ---------------------------
service_rubrics: List[WorkflowRubric] = [
    WorkflowRubric(
        name="otif_and_dwell_performance",
        llm_prompt=(
            "Evaluate service reliability using available artifacts and metrics: "
            "On‑Time‑In‑Full (OTIF) targets vs actuals, dwell time at yards/ports, and schedule adherence. "
            "Assess whether the control tower triages exceptions by SLA/impact and documents resolutions. "
            "Return a numeric score [0, 10]."
        ),
        max_score=10.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    WorkflowRubric(
        name="schedule_integrity",
        llm_prompt=(
            "Assess schedule integrity: confirmed Suez transit slots/convoys, synchronized rotations/ETAs, "
            "and timely publication of cutoffs (docs, gate‑in, VGM). "
            "Return a numeric score [0, 8]."
        ),
        max_score=8.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    WorkflowRubric(
        name="rule_slots_and_rotation_confirmed",
        evaluator_function=rule_slots_and_rotation_confirmed,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    WorkflowRubric(
        name="rule_control_tower_live",
        evaluator_function=rule_control_tower_live,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    WorkflowRubric(
        name="rule_gate_cutoffs_live",
        evaluator_function=rule_gate_cutoffs_live,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
]

compliance_rubrics: List[WorkflowRubric] = [
    WorkflowRubric(
        name="customs_and_advance_filing_completeness",
        llm_prompt=(
            "Evaluate customs posture: HS code accuracy, manifest integrity, pre‑arrival/advance filings on time, "
            "and certificates/permits completeness, with audit trail. Return a numeric score [0, 10]."
        ),
        max_score=10.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    WorkflowRubric(
        name="dangerous_goods_screening_quality",
        llm_prompt=(
            "Assess Dangerous Goods (DG) screening quality: correct classification, required declarations, "
            "stowage restrictions, and load holds where applicable. Return a numeric score [0, 8]."
        ),
        max_score=8.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    WorkflowRubric(
        name="rule_customs_ready",
        evaluator_function=rule_customs_ready,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    WorkflowRubric(
        name="rule_dg_cleared",
        evaluator_function=rule_dg_cleared,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
]

cost_rubrics: List[WorkflowRubric] = [
    WorkflowRubric(
        name="utilization_and_cost_variance",
        llm_prompt=(
            "Evaluate cost efficiency: equipment/yard/warehouse utilization vs plan, cost variance to budget, "
            "and evidence of optimization actions (e.g., load consolidation, shift optimization). Return [0, 10]."
        ),
        max_score=10.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    WorkflowRubric(
        name="empty_repositioning_efficiency",
        llm_prompt=(
            "Assess empty repositioning efficiency: balance of empties across depots, avoided deadhead moves, "
            "and alignment to demand bands. Return a numeric score [0, 8]."
        ),
        max_score=8.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    WorkflowRubric(
        name="rule_capacity_plan_ready",
        evaluator_function=rule_capacity_plan_ready,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    WorkflowRubric(
        name="rule_repositioning_planned",
        evaluator_function=rule_repositioning_planned,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
]

risk_rubrics: List[WorkflowRubric] = [
    WorkflowRubric(
        name="contingency_playbooks_quality",
        llm_prompt=(
            "Rigorously evaluate risk resilience and contingency planning:\n"
            "- shows specific trigger logic for reroute/hold/advance playbooks with measurable thresholds\n"
            "- demonstrates evidence of stress-testing playbooks under multiple disruption scenarios\n"
            "- shows rehearsals with documented lessons learned and process improvements\n"
            "- demonstrates multi-tier escalation procedures with decision authority levels\n"
            "- shows integration with external partners and alternative routing capabilities\n"
            "PENALTY: Deduct 2 points for each missing quantifiable requirement. No credit for theoretical playbooks. Return [0, 10]."
        ),
        max_score=10.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    WorkflowRubric(
        name="disruption_response_effectiveness",
        llm_prompt=(
            "Assess how exceptions were handled during execution: detection latency, escalation discipline, "
            "customer comms quality, and time‑to‑resolution. Return a numeric score [0, 8]."
        ),
        max_score=8.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    WorkflowRubric(
        name="rule_contingency_defined",
        evaluator_function=rule_contingency_defined,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    WorkflowRubric(
        name="rule_ops_exception_loop_running",
        evaluator_function=rule_ops_exception_loop_running,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    WorkflowRubric(
        name="supply_chain_crisis_scenarios",
        llm_prompt=(
            """Evaluate handling of supply chain crisis and disruption scenarios:
            - shows preparation for major supply disruptions and carrier failures
            - demonstrates response to port congestion and customs holds
            - shows handling of strike actions and weather-related delays
            - demonstrates preparation for capacity shortages and equipment shortages
            - shows contingency planning for trade disputes and force majeure events
            Score 0 if no crisis scenarios addressed. Partial credit only with evidence of disruptions AND mitigation strategies. Return score [0, 10]."""
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
# Preferences + Evaluators
# ---------------------------
def create_preferences() -> PreferenceWeights:
    """Initial stakeholder weights for Suez supply chain planning (t=0 snapshot)."""
    return PreferenceWeights(
        preferences=[
            Preference(
                name="service_reliability",
                weight=0.4,
                evaluator=Evaluator(
                    name="service_eval",
                    description="OTIF, dwell time, schedule integrity, and exception handling.",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=service_rubrics,
                ),
            ),
            Preference(
                name="compliance",
                weight=0.25,
                evaluator=Evaluator(
                    name="compliance_eval",
                    description="Customs/advance filings and DG controls readiness and quality.",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=compliance_rubrics,
                ),
            ),
            Preference(
                name="cost_efficiency",
                weight=0.2,
                evaluator=Evaluator(
                    name="cost_eval",
                    description="Utilization, empty repositioning, and cost variance to plan.",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=cost_rubrics,
                ),
            ),
            Preference(
                name="risk_resilience",
                weight=0.15,
                evaluator=Evaluator(
                    name="risk_eval",
                    description="Contingency playbooks and disruption response effectiveness.",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=risk_rubrics,
                ),
            ),
        ]
    )


# ---------------------------
# Weight Update Requests (timeline)
# ---------------------------
def create_preference_update_requests() -> list[PreferenceWeightUpdateRequest]:
    """Stakeholder's weight changes over time (absolute, normalized)."""
    timeline: dict[int, PreferenceWeights] = {
        # Early: get schedule integrity + compliance foundation in place
        0: PreferenceWeights(
            preferences=[
                Preference(name="service_reliability", weight=0.4),
                Preference(name="compliance", weight=0.25),
                Preference(name="cost_efficiency", weight=0.2),
                Preference(name="risk_resilience", weight=0.15),
            ]
        ),
        # Mid: stabilize ops, tune costs, maintain strict compliance
        12: PreferenceWeights(
            preferences=[
                Preference(name="service_reliability", weight=0.35),
                Preference(name="compliance", weight=0.3),
                Preference(name="cost_efficiency", weight=0.2),
                Preference(name="risk_resilience", weight=0.15),
            ]
        ),
        # Late: after steady‑state, push for cost and risk posture improvements while protecting service levels
        30: PreferenceWeights(
            preferences=[
                Preference(name="service_reliability", weight=0.3),
                Preference(name="compliance", weight=0.25),
                Preference(name="cost_efficiency", weight=0.3),
                Preference(name="risk_resilience", weight=0.15),
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
    """Create goal achievement evaluator for end-to-end supply chain planning with integrated S&OP."""
    goal_achievement_rubrics = [
        # Critical planning and operational deliverables (must have for supply chain effectiveness)
        WorkflowRubric(
            name="demand_forecast_accuracy_achieved",
            llm_prompt=(
                "Does achieved demand forecast accuracy exist with: multi-horizon demand forecast completed, "
                "seasonality analysis integrated, confidence intervals published, and forecast accuracy validated against historical performance? "
                "Return true if demand forecast accuracy is achieved and reliable, false otherwise."
            ),
            max_score=15.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="vessel_capacity_allocation_optimized",
            llm_prompt=(
                "Does optimized vessel capacity allocation exist with: vessel slots allocated by lane, "
                "safety stock maintained for priority customers, capacity utilization optimized, and allocation strategy documented? "
                "Return true if vessel capacity allocation is optimized, false otherwise."
            ),
            max_score=12.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="customs_dg_compliance_operational",
            llm_prompt=(
                "Does operational customs and DG compliance exist with: dangerous goods procedures validated, "
                "customs documentation automated, compliance tracking active, and regulatory requirements met across all lanes? "
                "Return true if customs and DG compliance are operational, false otherwise."
            ),
            max_score=12.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="intermodal_network_coordination",
            llm_prompt=(
                "Does intermodal network coordination exist with: rail/road capacity balanced, "
                "yard space allocated efficiently, warehouse throughput optimized, and modal integration seamless? "
                "Return true if intermodal network coordination is effective, false otherwise."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Major operational efficiency deliverables (8-10 points each)
        WorkflowRubric(
            name="execution_control_system_active",
            llm_prompt=(
                "Does active execution control system exist with: real-time tracking operational, "
                "performance monitoring automated, exception handling procedures active, and control metrics reported? "
                "Return true if execution control system is active and effective, false otherwise."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="risk_contingency_plans_deployed",
            llm_prompt=(
                "Do deployed risk contingency plans exist with: disruption scenarios identified, "
                "contingency strategies documented, risk mitigation protocols active, and emergency response procedures tested? "
                "Return true if risk contingency plans are deployed, false otherwise."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="customer_booking_pipeline_integrated",
            llm_prompt=(
                "Does integrated customer booking pipeline exist with: CRM pipeline integrated, "
                "no-show/cancel rates incorporated, booking forecasts accurate, and customer demand patterns analyzed? "
                "Return true if customer booking pipeline is integrated, false otherwise."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="performance_kpi_dashboard_operational",
            llm_prompt=(
                "Does operational performance KPI dashboard exist with: key metrics tracked in real-time, "
                "performance indicators automated, dashboard accessibility ensured, and decision-support analytics active? "
                "Return true if performance KPI dashboard is operational, false otherwise."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="yard_warehouse_throughput_optimized",
            llm_prompt=(
                "Does optimized yard and warehouse throughput exist with: yard slots balanced to volumes, "
                "warehouse shifts aligned to forecasts, throughput bottlenecks identified and resolved, and efficiency maximized? "
                "Return true if yard and warehouse throughput are optimized, false otherwise."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Important supporting deliverables (5-7 points each)
        WorkflowRubric(
            name="disruption_weather_signals_monitoring",
            llm_prompt=(
                "Does disruption and weather signals monitoring exist with: weather indicators tracked, "
                "port congestion monitored, disruption signals integrated into forecasts, and scenario planning active? "
                "Return true if disruption and weather signals monitoring is operational, false otherwise."
            ),
            max_score=7.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="supplier_vendor_coordination",
            llm_prompt=(
                "Does supplier and vendor coordination exist with: supplier performance tracked, "
                "vendor relationships managed, coordination protocols established, and partnership value optimized? "
                "Return true if supplier and vendor coordination is effective, false otherwise."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="cost_optimization_analysis",
            llm_prompt=(
                "Does cost optimization analysis exist with: cost drivers identified, "
                "optimization opportunities analyzed, cost reduction strategies implemented, and ROI measured? "
                "Return true if cost optimization analysis is complete and actionable, false otherwise."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="route_convoy_planning_optimized",
            llm_prompt=(
                "Does optimized route and convoy planning exist with: route efficiency maximized, "
                "convoy coordination optimal, transportation costs minimized, and service levels maintained? "
                "Return true if route and convoy planning are optimized, false otherwise."
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="capacity_buffer_management",
            llm_prompt=(
                "Does capacity buffer management exist with: safety stock levels optimized, "
                "buffer allocation strategic, capacity flexibility maintained, and service level targets met? "
                "Return true if capacity buffer management is effective, false otherwise."
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Supporting deliverables (3-4 points each)
        WorkflowRubric(
            name="seasonality_historical_analysis",
            llm_prompt=(
                "Does seasonality and historical analysis exist with: 24-36 months data analyzed, "
                "seasonal effects captured, historical patterns documented, and trend analysis completed? "
                "Return true if seasonality and historical analysis are complete, false otherwise."
            ),
            max_score=4.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="documentation_procedures_maintained",
            llm_prompt=(
                "Do maintained documentation and procedures exist with: process documentation current, "
                "procedures standardized, knowledge management active, and operational guides accessible? "
                "Return true if documentation and procedures are maintained, false otherwise."
            ),
            max_score=4.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="cross_lane_optimization",
            llm_prompt=(
                "Does cross-lane optimization exist with: lane performance compared, "
                "optimization opportunities identified across lanes, resource allocation balanced, and synergies captured? "
                "Return true if cross-lane optimization is implemented, false otherwise."
            ),
            max_score=3.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="stakeholder_communication_active",
            llm_prompt=(
                "Does active stakeholder communication exist with: internal communication protocols established, "
                "external partner communication active, status reporting regular, and alignment maintained? "
                "Return true if stakeholder communication is active and effective, false otherwise."
            ),
            max_score=3.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    return Evaluator(
        name="supply_chain_planning_goal_achievement_eval",
        description="End-to-end supply chain planning and integrated S&OP deliverable achievement measurement",
        aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
        rubrics=goal_achievement_rubrics,
    )
