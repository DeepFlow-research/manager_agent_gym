"""
Airline Launch Program Demo

Real-world use case: UK airline startup securing AOC and Operating Licence.

Demonstrates:
- Multi-track regulatory certification coordination with critical path dependencies
- Complex aviation safety and security compliance management under CAA oversight
- Resource-constrained project execution with parallel workstream management
- Stakeholder coordination across aviation authorities, lessors, airports, and service providers
- Risk-based decision making in heavily regulated industry with safety-critical requirements
- Escalation management for regulatory findings and compliance gaps
"""

from examples.end_to_end_examples.standard_rules import (
    speed_rubric,
    cost_rubric,
)
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
        """Penalize unrealistic cost discrepancies for airline launches."""
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
            return 0.0  # Airline launches should cost >$100k

        cost_variance = abs(total_actual - total_estimated) / total_estimated
        if cost_variance > 0.5:  # Aviation projects have high uncertainty
            return 0.2
        elif cost_variance > 0.3:
            return 0.6
        else:
            return 1.0

    def _airline_adversarial_pressure_score(workflow: Workflow) -> float:
        """Score based on handling airline launch adversarial pressure."""
        pressure_indicators = [
            "caa objection",
            "regulatory delay",
            "safety concern",
            "security issue",
            "slot denial",
            "route restriction",
            "airport rejection",
            "operational challenge",
            "compliance failure",
            "certification delay",
            "insurance issue",
            "licensing problem",
        ]

        pressure_handled = 0
        for indicator in pressure_indicators:
            for res in workflow.resources.values():
                if indicator.lower() in str(res.content or "").lower():
                    if any(
                        resolution.lower() in str(res.content or "").lower()
                        for resolution in [
                            "resolved",
                            "addressed",
                            "mitigated",
                            "approved",
                            "certified",
                        ]
                    ):
                        pressure_handled += 1
                    break

        return min(1.0, pressure_handled / max(1, len(pressure_indicators) * 0.3))

    def aviation_safety_artifact_density(workflow: Workflow) -> float:
        """Reward presence of safety-related documentation and evidence (0..1)."""
        safety_keywords = (
            "safety",
            "sms",
            "hazard",
            "risk assessment",
            "safety policy",
            "safety case",
        )
        total = 0
        hits = 0
        for res in workflow.resources.values():
            total += 1
            try:
                content = (res.content or "").lower()
                if any(k in content for k in safety_keywords):
                    hits += 1
            except Exception:
                continue
        if total == 0:
            return 0.0
        return min(1.0, hits / max(1, total))

    def regulatory_compliance_coverage(workflow: Workflow) -> float:
        """Check coverage of key regulatory requirements (0..1)."""
        compliance_keywords = (
            "aoc",
            "operating licence",
            "caa",
            "regulatory",
            "compliance",
            "certification",
        )
        total = 0
        hits = 0
        for res in workflow.resources.values():
            total += 1
            try:
                content = (res.content or "").lower()
                if any(k in content for k in compliance_keywords):
                    hits += 1
            except Exception:
                continue
        if total == 0:
            return 0.0
        return min(1.0, hits / max(1, total))

    def airworthiness_documentation_presence(workflow: Workflow) -> float:
        """Assess presence of airworthiness and maintenance documentation (0..1)."""
        airworthiness_keywords = (
            "camo",
            "part-145",
            "maintenance",
            "airworthiness",
            "cofa",
            "arc",
            "mel",
        )
        total = 0
        hits = 0
        for res in workflow.resources.values():
            total += 1
            try:
                content = (res.content or "").lower()
                if any(k in content for k in airworthiness_keywords):
                    hits += 1
            except Exception:
                continue
        if total == 0:
            return 0.0
        return min(1.0, hits / max(1, total))

    def security_programme_completeness(workflow: Workflow) -> float:
        """Evaluate completeness of aviation security programme elements (0..1)."""
        security_keywords = (
            "security programme",
            "nasp",
            "vetting",
            "screening",
            "security training",
        )
        total = 0
        hits = 0
        for res in workflow.resources.values():
            total += 1
            try:
                content = (res.content or "").lower()
                if any(k in content for k in security_keywords):
                    hits += 1
            except Exception:
                continue
        if total == 0:
            return 0.0
        return min(1.0, hits / max(1, total))

    def operations_manual_integration(workflow: Workflow) -> float:
        """Check integration and completeness of operations manual components (0..1)."""
        om_keywords = (
            "operations manual",
            "om-a",
            "om-b",
            "om-c",
            "om-d",
            "procedures",
            "training program",
        )
        total = 0
        hits = 0
        for res in workflow.resources.values():
            total += 1
            try:
                content = (res.content or "").lower()
                if any(k in content for k in om_keywords):
                    hits += 1
            except Exception:
                continue
        if total == 0:
            return 0.0
        return min(1.0, hits / max(1, total))

    def financial_fitness_evidence_strength(workflow: Workflow) -> float:
        """Assess strength of financial fitness evidence and documentation (0..1)."""
        financial_keywords = (
            "financial fitness",
            "business plan",
            "cash flow",
            "insurance",
            "funding",
        )
        total = 0
        hits = 0
        for res in workflow.resources.values():
            total += 1
            try:
                content = (res.content or "").lower()
                if any(k in content for k in financial_keywords):
                    hits += 1
            except Exception:
                continue
        if total == 0:
            return 0.0
        return min(1.0, hits / max(1, total))

    def proving_flight_readiness(workflow: Workflow) -> float:
        """Evaluate readiness for proving flights and operational demonstrations (0..1)."""
        proving_keywords = (
            "proving flight",
            "demonstration",
            "operational readiness",
            "flight test",
            "validation",
        )
        total = 0
        hits = 0
        for res in workflow.resources.values():
            total += 1
            try:
                content = (res.content or "").lower()
                if any(k in content for k in proving_keywords):
                    hits += 1
            except Exception:
                continue
        if total == 0:
            return 0.0
        return min(1.0, hits / max(1, total))

    def airport_coordination_effectiveness(workflow: Workflow) -> float:
        """Measure effectiveness of airport and slot coordination activities (0..1)."""
        airport_keywords = (
            "slot",
            "airport",
            "handling",
            "ground operations",
            "coordination",
        )
        recent = workflow.messages[-50:]
        if not recent:
            return 0.0
        hits = 0
        for m in recent:
            try:
                text = m.content.lower()
                if any(k in text for k in airport_keywords):
                    hits += 1
            except Exception:
                continue
        return max(0.0, min(1.0, hits / max(1, len(recent))))

    def caa_engagement_tracking(workflow: Workflow) -> float:
        """Track quality of CAA engagement and regulatory interaction (0..1)."""
        caa_keywords = (
            "caa",
            "inspector",
            "finding",
            "approval",
            "submission",
            "response",
        )
        recent = workflow.messages[-100:]
        if not recent:
            return 0.0
        hits = 0
        for m in recent:
            try:
                text = m.content.lower()
                if any(k in text for k in caa_keywords):
                    hits += 1
            except Exception:
                continue
        return max(0.0, min(1.0, hits / max(1, len(recent))))

    # ---------------------------
    # AVIATION SAFETY & SMS
    # ---------------------------
    aviation_safety_rubrics = [
        WorkflowRubric(
            name="sms_implementation_completeness",
            llm_prompt=(
                """Evaluate SMS implementation completeness against ICAO Annex 19. Award partial credit for:
                (a) safety policy and objectives with accountable manager commitment,
                (b) safety risk management processes including hazard identification,
                (c) safety assurance and monitoring systems,
                (d) safety promotion and training programs.
                Cite specific workflow resources/messages for evidence. Output a numeric score in [0, 10]."""
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="safety_risk_assessment_quality",
            llm_prompt=(
                """Assess quality of safety risk assessments and hazard identification processes.
                Look for systematic approach, risk matrix application, and mitigation strategies.
                Penalize incomplete or superficial analysis. Output a numeric score in [0, 7]."""
            ),
            max_score=7.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="proving_flight_safety_readiness",
            llm_prompt=(
                """Evaluate safety readiness for proving flights: (1) aircraft airworthiness validation,
                (2) crew competency and training completion, (3) operational procedures validation,
                (4) emergency response preparedness. Award equal partial credit. Output numeric score [0, 8]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="safety_culture_development",
            llm_prompt=(
                """Assess development of safety culture and reporting systems including just culture principles,
                safety communication, and continuous improvement mechanisms. Output numeric score [0, 6]."""
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="aviation_safety_artifact_density",
            evaluator_function=aviation_safety_artifact_density,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="proving_flight_readiness",
            evaluator_function=proving_flight_readiness,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # ---------------------------
    # REGULATORY COMPLIANCE
    # ---------------------------
    regulatory_compliance_rubrics = [
        WorkflowRubric(
            name="aoc_application_completeness",
            llm_prompt=(
                """Evaluate AOC application completeness against CAA requirements. Award partial credit for:
                operations manual approval, SMS implementation, airworthiness arrangements, and proving flight readiness.
                Cite specific compliance evidence. Output numeric score [0, 10]."""
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="operating_licence_requirements",
            llm_prompt=(
                """Assess Operating Licence requirements compliance: UK principal place of business,
                ownership/control demonstration, financial fitness evidence, and insurance coverage validation.
                Award partial credit with citations. Output numeric score [0, 9]."""
            ),
            max_score=9.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="operations_manual_regulatory_alignment",
            llm_prompt=(
                """Evaluate Operations Manual (OM-A/B/C/D) alignment with UK Reg (EU) 965/2012 and ANO 2016.
                Assess procedure completeness, regulatory compliance, and integration across manual sections.
                Provide partial credit with citations. Output numeric score [0, 8]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="caa_inspection_response_quality",
            llm_prompt=(
                """Assess quality of CAA inspection response and finding closure processes.
                Look for systematic finding management, corrective action planning, and compliance demonstration.
                Output numeric score [0, 7]."""
            ),
            max_score=7.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="aviation_security_nasp_compliance",
            llm_prompt=(
                """Evaluate aviation security programme compliance with NASP requirements including
                security procedures, staff vetting, training programs, and equipment arrangements.
                Output numeric score [0, 8]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="regulatory_compliance_coverage",
            evaluator_function=regulatory_compliance_coverage,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="security_programme_completeness",
            evaluator_function=security_programme_completeness,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # ---------------------------
    # AIRWORTHINESS & MAINTENANCE
    # ---------------------------
    airworthiness_rubrics = [
        WorkflowRubric(
            name="camo_part145_arrangements_validation",
            llm_prompt=(
                """Evaluate CAMO and Part-145 arrangements: organizational approvals, maintenance program development,
                reliability monitoring systems, and continuing airworthiness management compliance.
                Award partial credit with citations. Output numeric score [0, 9]."""
            ),
            max_score=9.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="aircraft_certification_completeness",
            llm_prompt=(
                """Assess aircraft certification completeness: registration certificates, certificates of airworthiness (CofA),
                airworthiness review certificates (ARC), and MEL/GMEL program approvals.
                Partial credit with citations. Output numeric score [0, 8]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="maintenance_program_quality",
            llm_prompt=(
                """Evaluate maintenance program quality including scheduled maintenance planning,
                reliability monitoring, component tracking, and maintenance control systems.
                Output numeric score [0, 7]."""
            ),
            max_score=7.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="airworthiness_documentation_presence",
            evaluator_function=airworthiness_documentation_presence,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # ---------------------------
    # OPERATIONAL READINESS
    # ---------------------------
    operational_readiness_rubrics = [
        WorkflowRubric(
            name="airport_operations_coordination",
            llm_prompt=(
                """Evaluate airport operations coordination: slot confirmations, ground handling contracts,
                disruption management plans, and passenger rights compliance under UK261.
                Award partial credit with citations. Output numeric score [0, 8]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="financial_fitness_demonstration",
            llm_prompt=(
                """Assess financial fitness demonstration including business plan quality, cash flow projections,
                funding evidence, and insurance coverage adequacy for Operating Licence requirements.
                Cite evidence. Output numeric score [0, 7]."""
            ),
            max_score=7.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="crew_training_program_readiness",
            llm_prompt=(
                """Evaluate crew training program readiness including OM-D development, competency standards,
                checking requirements, and training delivery capability. Output numeric score [0, 6]."""
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="operations_manual_integration",
            evaluator_function=operations_manual_integration,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="financial_fitness_evidence_strength",
            evaluator_function=financial_fitness_evidence_strength,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="airport_coordination_effectiveness",
            evaluator_function=airport_coordination_effectiveness,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # ---------------------------
    # GOVERNANCE & OVERSIGHT
    # ---------------------------
    governance_rubrics = [
        WorkflowRubric(
            name="nominated_postholder_compliance",
            llm_prompt=(
                """Evaluate nominated postholder appointments and compliance: competency validation,
                experience requirements, role definitions, and CAA acceptance evidence.
                Award partial credit with citations. Output numeric score [0, 8]."""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="corporate_governance_structure",
            llm_prompt=(
                """Assess corporate governance structure including UK corporate establishment,
                board composition, decision-making authorities, and accountability frameworks.
                Output numeric score [0, 6]."""
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="launch_readiness_governance",
            llm_prompt=(
                """Evaluate launch readiness governance including final approvals, go/no-go decision processes,
                and executive sign-offs from accountable manager and board. Output numeric score [0, 5]."""
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="caa_engagement_tracking",
            evaluator_function=caa_engagement_tracking,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # ---------------------------
    # SPEED
    # ---------------------------
    speed_rubrics = [
        WorkflowRubric(
            name="certification_timeline_adherence",
            llm_prompt=(
                """Evaluate adherence to certification timeline including AOC and Operating Licence application processing,
                proving flight scheduling, and critical path management. Cite evidence.
                Output numeric score [0, 7]."""
            ),
            max_score=7.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="regulatory_response_timeliness",
            llm_prompt=(
                """Assess timeliness of regulatory responses including CAA finding closure,
                application submissions, and inspection support. Output numeric score [0, 5]."""
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
            name="certification_cost_optimization",
            llm_prompt=(
                """Assess certification cost optimization including efficient use of consultants,
                regulatory fees management, and cost-benefit analysis of certification activities.
                Cite evidence. Output numeric score [0, 6]."""
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="operational_setup_cost_effectiveness",
            llm_prompt=(
                """Evaluate operational setup cost effectiveness including insurance arrangements,
                slot costs, handling contracts, and equipment procurement. Output numeric score [0, 4]."""
            ),
            max_score=4.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="airline_adversarial_scenarios",
            llm_prompt=(
                """Evaluate handling of airline launch adversarial scenarios and regulatory challenges:
                - shows preparation for CAA objections and regulatory delays
                - demonstrates response to safety concerns and security issues
                - shows handling of slot denials and route restrictions
                - demonstrates preparation for airport rejections and operational challenges
                - shows certification delay management and compliance failure resolution
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
                name="aviation_safety",
                weight=0.3,
                evaluator=Evaluator(
                    name="aviation_safety_eval",
                    description="aviation safety and SMS evaluator",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=aviation_safety_rubrics,
                ),
            ),
            Preference(
                name="regulatory_compliance",
                weight=0.25,
                evaluator=Evaluator(
                    name="regulatory_compliance_eval",
                    description="regulatory compliance evaluator",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=regulatory_compliance_rubrics,
                ),
            ),
            Preference(
                name="airworthiness",
                weight=0.2,
                evaluator=Evaluator(
                    name="airworthiness_eval",
                    description="airworthiness and maintenance evaluator",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=airworthiness_rubrics,
                ),
            ),
            Preference(
                name="operational_readiness",
                weight=0.15,
                evaluator=Evaluator(
                    name="operational_readiness_eval",
                    description="operational readiness evaluator",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=operational_readiness_rubrics,
                ),
            ),
            Preference(
                name="governance",
                weight=0.06,
                evaluator=Evaluator(
                    name="governance_eval",
                    description="governance and oversight evaluator",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=governance_rubrics,
                ),
            ),
            Preference(
                name="speed",
                weight=0.03,
                evaluator=Evaluator(
                    name="speed_eval",
                    description="speed and timeliness evaluator",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=speed_rubrics,
                ),
            ),
            Preference(
                name="cost",
                weight=0.01,
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
    """Build stakeholder weight update requests for the Airline Launch Program scenario.

    Timeline shifts from initial setup and safety foundation to regulatory compliance
    focus as AOC and Operating Licence submissions approach.
    """
    timeline: dict[int, PreferenceWeights] = {
        0: PreferenceWeights(
            preferences=[
                Preference(
                    name="aviation_safety",
                    weight=0.35,
                    evaluator=Evaluator(
                        name="aviation_safety_eval",
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
                Preference(name="airworthiness", weight=0.2),
                Preference(name="operational_readiness", weight=0.15),
                Preference(name="governance", weight=0.06),
                Preference(name="speed", weight=0.03),
                Preference(name="cost", weight=0.01),
            ]
        ),
        15: PreferenceWeights(
            preferences=[
                Preference(name="aviation_safety", weight=0.3),
                Preference(name="regulatory_compliance", weight=0.25),
                Preference(name="airworthiness", weight=0.2),
                Preference(name="operational_readiness", weight=0.15),
                Preference(name="governance", weight=0.06),
                Preference(name="speed", weight=0.03),
                Preference(name="cost", weight=0.01),
            ]
        ),
        25: PreferenceWeights(
            preferences=[
                Preference(name="aviation_safety", weight=0.25),
                Preference(name="regulatory_compliance", weight=0.35),
                Preference(name="airworthiness", weight=0.2),
                Preference(name="operational_readiness", weight=0.12),
                Preference(name="governance", weight=0.05),
                Preference(name="speed", weight=0.02),
                Preference(name="cost", weight=0.01),
            ]
        ),
        35: PreferenceWeights(
            preferences=[
                Preference(name="aviation_safety", weight=0.2),
                Preference(name="regulatory_compliance", weight=0.4),
                Preference(name="airworthiness", weight=0.15),
                Preference(name="operational_readiness", weight=0.15),
                Preference(name="governance", weight=0.07),
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


def create_evaluator_to_measure_goal_achievement() -> Evaluator:
    """Create goal achievement evaluator based on actual airline launch requirements."""
    goal_achievement_rubrics = [
        # Critical regulatory deliverables (absolutely must have for legal operation)
        WorkflowRubric(
            name="aoc_application_package_ready",
            llm_prompt=(
                "Does ready AOC application package exist with: complete CAA application forms prepared, "
                "Operations Manual documentation compiled, Supporting evidence assembled, and submission checklist validated? "
                "Return true if AOC application package is ready for submission, false otherwise."
            ),
            max_score=15.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="operating_licence_application_prepared",
            llm_prompt=(
                "Does prepared Operating Licence application exist with: comprehensive application documentation ready, "
                "financial fitness demonstration compiled, UK ownership/control validation documented, and insurance framework established? "
                "Return true if Operating Licence application is prepared for submission, false otherwise."
            ),
            max_score=15.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="airworthiness_certification_framework_ready",
            llm_prompt=(
                "Does ready airworthiness certification framework exist with: CofA application documentation prepared, "
                "ARC renewal procedures established, aircraft registration framework documented, and maintenance program designed? "
                "Return true if airworthiness certification framework is ready for implementation, false otherwise."
            ),
            max_score=12.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="aviation_security_programme_documented",
            llm_prompt=(
                "Does documented aviation security programme exist with: NASP compliance framework established, "
                "security programme documentation prepared, staff vetting procedures defined, and security training curriculum designed? "
                "Return true if security programme is fully documented and ready for implementation, false otherwise."
            ),
            max_score=12.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Major operational deliverables (8-9 points each)
        WorkflowRubric(
            name="operations_manual_comprehensive",
            llm_prompt=(
                "Does comprehensive Operations Manual exist with: OM-A General Procedures documented, "
                "OM-B Aircraft Operating Procedures completed, OM-C Route & Aerodrome Information compiled, and OM-D Training Program designed? "
                "Return true if complete Operations Manual is documented and ready for CAA review, false otherwise."
            ),
            max_score=9.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="safety_management_system_operational",
            llm_prompt=(
                "Does operational Safety Management System exist with: safety policy implementation, "
                "risk management processes, safety assurance monitoring, and safety promotion programs? "
                "Return true if SMS is fully operational per ICAO Annex 19, false otherwise."
            ),
            max_score=9.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="camo_part145_arrangements_validated",
            llm_prompt=(
                "Do validated airworthiness arrangements exist with: Part-CAMO approval or contracts, "
                "Part-145 maintenance organization arrangements, reliability monitoring systems, and MEL/GMEL approvals? "
                "Return true if continuing airworthiness arrangements are validated, false otherwise."  
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="insurance_coverage_binding",
            llm_prompt=(
                "Do binding insurance certificates exist with: passenger liability coverage, "
                "baggage and cargo liability, third-party liability coverage, and regulatory minimum compliance? "
                "Return true if all required insurance is binding and compliant, false otherwise."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="nominated_postholders_appointed",
            llm_prompt=(
                "Are nominated postholders appointed with: Flight Operations postholder, "
                "Ground Operations postholder, Continuing Airworthiness postholder, Crew Training postholder, "
                "Safety postholder, Security postholder, and CAA competency requirements met? "
                "Return true if all required postholders are appointed and qualified, false otherwise."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Important supporting deliverables (5-6 points each)
        WorkflowRubric(
            name="proving_flights_completed",
            llm_prompt=(
                "Do completed proving flights exist with: successful flight demonstrations, "
                "operational competency validation, CAA inspector observations, and no unresolved findings? "
                "Return true if proving flights are successfully completed, false otherwise."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="airport_slots_confirmed",
            llm_prompt=(
                "Do confirmed airport slots exist with: slot confirmations at coordinated airports, "
                "ACL coordination evidence, handling contract agreements, and operational access arrangements? "
                "Return true if airport slots are confirmed and operational, false otherwise."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="staff_vetting_training_complete",
            llm_prompt=(
                "Does complete staff vetting and training exist with: 100% security vetting completion, "
                "aviation security training records, competency assessments, and ongoing training programs? "
                "Return true if all staff vetting and training is complete, false otherwise."
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="ground_handling_contracts_finalized",
            llm_prompt=(
                "Do finalized ground handling contracts exist with: passenger handling agreements, "
                "baggage handling contracts, cargo handling arrangements, and ramp service contracts? "
                "Return true if ground handling contracts are finalized, false otherwise."
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="maintenance_programs_approved",
            llm_prompt=(
                "Do approved maintenance programs exist with: aircraft maintenance programs, "
                "MEL (Minimum Equipment List) approval, GMEL (General Minimum Equipment List), and reliability monitoring? "
                "Return true if maintenance programs are approved, false otherwise."
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="financial_fitness_demonstrated",
            llm_prompt=(
                "Does demonstrated financial fitness exist with: business plan documentation, "
                "cash flow projections, funding evidence, and financial monitoring systems? "
                "Return true if financial fitness is demonstrated and documented, false otherwise."
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Supporting deliverables (3-4 points each)
        WorkflowRubric(
            name="uk_principal_place_business",
            llm_prompt=(
                "Does UK principal place of business exist with: UK corporate structure, "
                "principal place of business establishment, ownership/control validation, and governance framework? "
                "Return true if UK principal place of business is established, false otherwise."
            ),
            max_score=4.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="disruption_management_procedures",
            llm_prompt=(
                "Do disruption management procedures exist with: disruption management plans, "
                "passenger rights compliance under UK261, contingency procedures, and customer communication protocols? "
                "Return true if disruption management procedures are established, false otherwise."
            ),
            max_score=4.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="dangerous_goods_approval",
            llm_prompt=(
                "Does dangerous goods approval exist with: CAA Form SRG2807 submission, "
                "DG training program approval, Operations Manual DG procedures, and compliance monitoring integration? "
                "Return true if dangerous goods approval is obtained (or N/A if not applicable), false otherwise."
            ),
            max_score=3.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="final_governance_approvals",
            llm_prompt=(
                "Do final governance approvals exist with: Board of Directors approval, "
                "Accountable Manager certification, postholder sign-offs, and launch readiness validation? "
                "Return true if final governance approvals are obtained, false otherwise."
            ),
            max_score=3.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="caa_inspection_findings_closed",
            llm_prompt=(
                "Are CAA inspection findings closed with: inspection completion records, "
                "corrective action implementation, finding closure confirmations, and compliance demonstration? "
                "Return true if all CAA findings are closed, false otherwise."
            ),
            max_score=3.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    return Evaluator(
        name="airline_launch_goal_achievement_eval",
        description="Aviation-specific deliverable achievement measurement for airline launch certification",
        aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
        rubrics=goal_achievement_rubrics,
    )
