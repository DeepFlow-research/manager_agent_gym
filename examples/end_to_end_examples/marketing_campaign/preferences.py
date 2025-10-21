"""
Renewable Energy Marketing – Preferences, Evaluators, and Weight Updates

Preferences modeled for an integrated campaign:
  - performance  : pipeline efficacy & experimentation rigor
  - brand        : brand lift & message coherence
  - compliance   : environmental claims substantiation + privacy/email rules
  - accessibility: WCAG 2.1 AA readiness

Mirrors example schema usage:
  * PreferenceWeights / Preference
  * Rubric(aggregation=AggregationStrategy.WEIGHTED_AVERAGE, criteria=[RubricCriteria...])
  * RubricCriteria with llm_prompt or evaluator_function
  * create_*_preference_update_requests(): absolute, normalized timeline updates
"""

from typing import List
from manager_agent_gym.schemas.preferences.preference import (
    Preference,
    PreferenceSnapshot,
)
from manager_agent_gym.schemas.preferences.evaluator import (
    Rubric,
    AggregationStrategy,
)
from manager_agent_gym.schemas.preferences.rubric import RubricCriteria, RunCondition
from manager_agent_gym.schemas.preferences import PreferenceWeightUpdateRequest
from manager_agent_gym.schemas.domain import Workflow
from manager_agent_gym.schemas.domain.base import TaskStatus


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
    """Penalize unrealistic cost discrepancies for marketing campaigns."""
    expected_min_cost = 30000.0  # Minimum realistic cost
    total_estimated = sum(
        task.estimated_cost for task in workflow.tasks.values() if task.estimated_cost
    )
    total_actual = sum(
        task.actual_cost for task in workflow.tasks.values() if task.actual_cost
    )

    if total_estimated == 0:
        return 0.0  # No cost planning penalty

    if total_actual < expected_min_cost:
        return 0.0  # Marketing campaigns should cost more than $30k

    cost_variance = abs(total_actual - total_estimated) / total_estimated
    if cost_variance > 0.3:  # >30% cost variance penalty for marketing
        return 0.2
    elif cost_variance > 0.15:  # >15% cost variance partial penalty
        return 0.6
    else:
        return 1.0


def _require_external_validation(
    workflow: Workflow, validation_keywords: List[str]
) -> float:
    """Require evidence of external validation for marketing claims and compliance."""
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
                    "certified",
                    "audited",
                ]
            ):
                validation_evidence += 1

    return min(
        1.0, validation_evidence / max(1, total_tasks * 0.25)
    )  # Require 25% external validation


def _marketing_adversarial_pressure_score(workflow: Workflow) -> float:
    """Score based on handling marketing adversarial pressure and challenges."""
    pressure_indicators = [
        "competitor response",
        "negative publicity",
        "brand crisis",
        "claim challenge",
        "regulatory inquiry",
        "consumer complaint",
        "media criticism",
        "public backlash",
        "legal challenge",
        "greenwashing accusation",
        "false advertising",
        "compliance issue",
    ]

    pressure_handled = 0
    for indicator in pressure_indicators:
        for res in workflow.resources.values():
            if indicator.lower() in str(res.content or "").lower():
                # Check for resolution evidence
                if any(
                    resolution.lower() in str(res.content or "").lower()
                    for resolution in [
                        "resolved",
                        "mitigated",
                        "addressed",
                        "corrected",
                        "defended",
                    ]
                ):
                    pressure_handled += 1
                break

    return min(
        1.0, pressure_handled / max(1, len(pressure_indicators) * 0.3)
    )  # Expect 30% pressure scenarios


# PERFORMANCE rules (pipeline + experimentation signals)
def rule_foundations_ready(workflow: Workflow) -> float:
    """
    Proxy readiness for launch performance: completion of web conversion and CRM enablement.
    """
    return 0.5 * _task_completed(
        workflow, "Web & Conversion Experience"
    ) + 0.5 * _task_completed(workflow, "CRM Enablement")


def rule_experimentation_live(workflow: Workflow) -> float:
    """
    Proxy for disciplined testing impacting performance: Measurement Framework and Experimentation tasks completed.
    """
    return 0.5 * _task_completed(
        workflow, "Measurement Framework"
    ) + 0.5 * _task_completed(workflow, "Experimentation & Optimization")


# BRAND rules (brand lift instrumentation + creative integrity)
def rule_brand_lift_instrumented(workflow: Workflow) -> float:
    """
    Proxy for brand study readiness: Brand Lift Study task completed.
    """
    return _task_completed(workflow, "Brand Lift Study")


def rule_creative_toolkit_complete(workflow: Workflow) -> float:
    """
    Proxy for coherent creative system: Creative Toolkit & Asset Production completed.
    """
    return _task_completed(workflow, "Creative Toolkit")


# COMPLIANCE rules (green claims + consent/email hygiene)
def rule_green_claims_playbook_in_place(workflow: Workflow) -> float:
    """
    Proxy for claims substantiation readiness: Messaging House & Green Claims Playbook completed.
    """
    return _task_completed(workflow, "Green Claims Playbook") or _task_completed(
        workflow, "Messaging House & Green Claims"
    )


def rule_privacy_controls_live(workflow: Workflow) -> float:
    """
    Proxy for consent and preference management: Web & Conversion Experience completed.
    """
    return _task_completed(workflow, "Web & Conversion Experience")


# ACCESSIBILITY rules (AA readiness across web and key assets)
def rule_wcag_passes(workflow: Workflow) -> float:
    """
    Proxy for WCAG AA readiness: Accessibility Pass subtask (under Creative Toolkit) AND Web & Conversion Experience completed.
    Note: we approximate via parent-task completion.
    """
    return 0.5 * _task_completed(workflow, "Creative Toolkit") + 0.5 * _task_completed(
        workflow, "Web & Conversion Experience"
    )


# ---------------------------
# LLM Rubrics
# ---------------------------
performance_rubrics: List[RubricCriteria] = [
    RubricCriteria(
        name="pipeline_quality_and_flow",
        llm_prompt=(
            "Evaluate whether the campaign is set up to generate qualified pipeline efficiently: "
            "(a) clear ICPs/personas and segment-specific offers; "
            "(b) working lead capture with consent, scoring, dedup, and routing SLAs; "
            "(c) defined KPIs with UTM governance; and "
            "(d) experimentation plan that can impact CAC and conversion rates. "
            "Cite concrete workflow evidence (tasks, artifacts, dashboards). Return a numeric score [0, 10]."
        ),
        max_score=10.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    RubricCriteria(
        name="rule_foundations_ready",
        evaluator_function=rule_foundations_ready,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    RubricCriteria(
        name="rule_experimentation_live",
        evaluator_function=rule_experimentation_live,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
]

brand_rubrics: List[RubricCriteria] = [
    RubricCriteria(
        name="creative_system_coherence",
        llm_prompt=(
            "Assess whether creative assets reflect a coherent brand system: "
            "consistent narrative across hero/variants, inclusive language, and alignment to the messaging house. "
            "Consider QA (alt text/captions) and partner co-branding guidance. Return a numeric score [0, 8]."
        ),
        max_score=8.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    RubricCriteria(
        name="brand_lift_readiness",
        llm_prompt=(
            "Assess readiness to measure brand lift: sampling plan, survey constructs (ad recall, awareness, consideration), "
            "fielding schedule, and integration with dashboards. Return a numeric score [0, 6]."
        ),
        max_score=6.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    RubricCriteria(
        name="rule_brand_lift_instrumented",
        evaluator_function=rule_brand_lift_instrumented,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    RubricCriteria(
        name="rule_creative_toolkit_complete",
        evaluator_function=rule_creative_toolkit_complete,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
]

compliance_rubrics: List[RubricCriteria] = [
    RubricCriteria(
        name="environmental_claims_substantiation",
        llm_prompt=(
            "Evaluate environmental claims for compliance and substantiation: "
            "avoid broad unqualified 'green' claims; require specific, evidenced claims with clear qualifications; "
            "maintain a substantiation log (e.g., RECs, LCA references). Return a numeric score [0, 10]."
        ),
        max_score=10.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    RubricCriteria(
        name="privacy_and_email_compliance",
        llm_prompt=(
            "Assess consent and email compliance posture: explicit consent for non-essential cookies and direct marketing; "
            "functional one‑click unsubscribe; clear sender identity and postal address. "
            "Return a numeric score [0, 8]."
        ),
        max_score=8.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    RubricCriteria(
        name="rule_green_claims_playbook_in_place",
        evaluator_function=rule_green_claims_playbook_in_place,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    RubricCriteria(
        name="rule_privacy_controls_live",
        evaluator_function=rule_privacy_controls_live,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    RubricCriteria(
        name="marketing_crisis_scenarios",
        llm_prompt=(
            """Evaluate handling of marketing crisis and adversarial scenarios:
            - shows preparation for competitor response and competitive challenges
            - demonstrates handling of negative publicity and brand crisis management
            - shows response to regulatory inquiries and compliance challenges
            - demonstrates preparation for greenwashing accusations and claim challenges
            - shows crisis communication strategies and damage control measures
            Score 0 if no crisis scenarios addressed. Partial credit only with evidence of scenarios AND response strategies. Return score [0, 10]."""
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

accessibility_rubrics: List[RubricCriteria] = [
    RubricCriteria(
        name="wcag_aa_conformance",
        llm_prompt=(
            "Evaluate whether key campaign web pages and assets conform to WCAG 2.1 AA: text alternatives, captions, "
            "sufficient contrast, focus order, and keyboard access; include evidence of automated and manual checks. "
            "Return a numeric score [0, 10]."
        ),
        max_score=10.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
    RubricCriteria(
        name="rule_wcag_passes",
        evaluator_function=rule_wcag_passes,
        max_score=1.0,
        run_condition=RunCondition.ON_COMPLETION,
    ),
]


# ---------------------------
# Preferences + Evaluators
# ---------------------------
def create_marketing_preferences() -> PreferenceSnapshot:
    """Initial stakeholder weights for Renewables Marketing (t=0 snapshot)."""
    return PreferenceSnapshot(
        preferences=[
            Preference(
                name="performance",
                weight=0.45,
                evaluator=Rubric(
                    name="performance_eval",
                    description="Evaluates pipeline readiness and experimentation rigor.",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    criteria=performance_rubrics,
                ),
            ),
            Preference(
                name="brand",
                weight=0.25,
                evaluator=Rubric(
                    name="brand_eval",
                    description="Evaluates creative coherence and brand lift readiness.",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    criteria=brand_rubrics,
                ),
            ),
            Preference(
                name="compliance",
                weight=0.2,
                evaluator=Rubric(
                    name="compliance_eval",
                    description="Evaluates environmental claims substantiation and privacy/email controls.",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    criteria=compliance_rubrics,
                ),
            ),
            Preference(
                name="accessibility",
                weight=0.1,
                evaluator=Rubric(
                    name="accessibility_eval",
                    description="Evaluates WCAG 2.1 AA readiness across web and key assets.",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    criteria=accessibility_rubrics,
                ),
            ),
        ]
    )


# ---------------------------
# Weight Update Requests (timeline)
# ---------------------------
def create_preference_update_requests() -> list[PreferenceWeightUpdateRequest]:
    """Stakeholder's weight changes over time (absolute, normalized)."""
    timeline: dict[int, PreferenceSnapshot] = {
        # Early: speed/performance bias to stand up the campaign
        0: PreferenceSnapshot(
            preferences=[
                Preference(name="performance", weight=0.45),
                Preference(name="brand", weight=0.25),
                Preference(name="compliance", weight=0.2),
                Preference(name="accessibility", weight=0.1),
            ]
        ),
        # Mid-flight: brand quality weighs more as creative stabilizes and reach scales
        20: PreferenceSnapshot(
            preferences=[
                Preference(name="performance", weight=0.35),
                Preference(name="brand", weight=0.35),
                Preference(name="compliance", weight=0.2),
                Preference(name="accessibility", weight=0.1),
            ]
        ),
        # Late: compliance & accessibility take priority as scale and scrutiny increase
        45: PreferenceSnapshot(
            preferences=[
                Preference(name="performance", weight=0.2),
                Preference(name="brand", weight=0.2),
                Preference(name="compliance", weight=0.4),
                Preference(name="accessibility", weight=0.2),
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
    """Create goal achievement evaluator for renewable energy integrated marketing campaign."""
    goal_achievement_rubrics = [
        # Critical campaign performance deliverables (must have for campaign success)
        RubricCriteria(
            name="brand_tracking_framework_operational",
            llm_prompt=(
                "Does operational brand tracking framework exist with: measurement approach documented, "
                "key metrics defined, tracking methodology outlined, and reporting framework established? "
                "Return true if brand tracking components are documented and ready for deployment, false otherwise."
            ),
            max_score=18.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="lead_generation_system_designed",
            llm_prompt=(
                "Does designed lead generation system exist with: lead scoring strategy documented, "
                "tracking frameworks established, target audience segments defined, and measurement approach specified? "
                "Return true if lead generation components are documented and ready for implementation, false otherwise."
            ),
            max_score=15.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="seo_optimization_strategy_implemented",
            llm_prompt=(
                "Does implemented SEO optimization strategy exist with: keyword research and strategy documented, "
                "content optimization guidelines established, SEO best practices framework created, and tracking approach defined? "
                "Return true if SEO optimization components are documented and ready for execution, false otherwise."
            ),
            max_score=12.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="b2b_sales_pipeline_framework_ready",
            llm_prompt=(
                "Does ready B2B sales pipeline framework exist with: opportunity qualification approach documented, "
                "scoring criteria established, handoff procedures defined, and pipeline tracking methodology created? "
                "Return true if B2B pipeline components are documented and ready for implementation, false otherwise."
            ),
            max_score=12.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Major campaign infrastructure and compliance deliverables (8-10 points each)
        RubricCriteria(
            name="messaging_claims_substantiation",
            llm_prompt=(
                "Does messaging claims substantiation exist with: substantiation log maintained, "
                "environmental claims validated, no greenwashing violations, and compliance audit passed? "
                "Return true if messaging claims substantiation is complete and compliant, false otherwise."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="wcag_accessibility_compliance",
            llm_prompt=(
                "Does WCAG accessibility compliance exist with: WCAG 2.1 AA compliance achieved for key web assets, "
                "accessibility audit completed, user testing with assistive technologies performed, and compliance certified? "
                "Return true if WCAG accessibility compliance is achieved, false otherwise."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="consent_opt_in_rates_achieved",
            llm_prompt=(
                "Do achieved consent opt-in rates exist with: ≥85% consent opt-in rates maintained, "
                "privacy compliance validated, consent management system operational, and GDPR/CCPA compliance confirmed? "
                "Return true if consent opt-in rates are achieved, false otherwise."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="integrated_campaign_execution",
            llm_prompt=(
                "Does integrated campaign execution exist with: multi-channel strategy deployed (paid/owned/earned), "
                "cross-channel messaging consistency maintained, campaign coordination operational, and unified customer experience delivered? "
                "Return true if integrated campaign execution is successful, false otherwise."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="measurement_framework_operational",
            llm_prompt=(
                "Does operational measurement framework exist with: MMM/MTA-compatible tracking implemented, "
                "UTM governance established, attribution models validated, and measurement accuracy confirmed? "
                "Return true if measurement framework is operational, false otherwise."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Important supporting deliverables (5-7 points each)
        RubricCriteria(
            name="creative_toolkit_deployed",
            llm_prompt=(
                "Does deployed creative toolkit exist with: brand guidelines implemented, "
                "creative assets produced across channels, visual identity consistency maintained, and creative performance tracked? "
                "Return true if creative toolkit is deployed and effective, false otherwise."
            ),
            max_score=7.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="pr_analyst_program_active",
            llm_prompt=(
                "Does active PR and analyst program exist with: media relations strategy executed, "
                "analyst engagement program operational, thought leadership content published, and industry recognition achieved? "
                "Return true if PR and analyst program is active, false otherwise."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="events_field_marketing_executed",
            llm_prompt=(
                "Does executed events and field marketing exist with: events program launched, "
                "field marketing campaigns deployed, in-person engagement activities completed, and lead generation from events tracked? "
                "Return true if events and field marketing are executed, false otherwise."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="partner_co_marketing_assets",
            llm_prompt=(
                "Do partner co-marketing assets exist with: partner marketing materials developed, "
                "co-marketing agreements executed, joint campaigns launched, and partner channel performance tracked? "
                "Return true if partner co-marketing assets are operational, false otherwise."
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="experimentation_cadence_established",
            llm_prompt=(
                "Does established experimentation cadence exist with: A/B testing framework operational, "
                "test planning and execution systematic, results analysis automated, and optimization cycles active? "
                "Return true if experimentation cadence is established, false otherwise."
            ),
            max_score=5.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        # Supporting deliverables (3-4 points each)
        RubricCriteria(
            name="executive_dashboard_operational",
            llm_prompt=(
                "Does operational executive dashboard exist with: weekly performance reporting active, "
                "KPI tracking automated, executive stakeholder access configured, and actionable insights provided? "
                "Return true if executive dashboard is operational, false otherwise."
            ),
            max_score=4.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="crm_lead_routing_system",
            llm_prompt=(
                "Does CRM lead routing system exist with: automated lead scoring implemented, "
                "routing workflows configured, sales team integration complete, and lead management processes operational? "
                "Return true if CRM lead routing system is functional, false otherwise."
            ),
            max_score=4.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="web_conversion_flows_optimized",
            llm_prompt=(
                "Do optimized web conversion flows exist with: conversion funnel analysis completed, "
                "user experience optimization implemented, conversion rate improvements achieved, and customer journey mapped? "
                "Return true if web conversion flows are optimized, false otherwise."
            ),
            max_score=3.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="audience_persona_validation",
            llm_prompt=(
                "Does audience persona validation exist with: target personas researched and validated, "
                "customer interviews completed, persona-based messaging tested, and audience segmentation optimized? "
                "Return true if audience persona validation is complete, false otherwise."
            ),
            max_score=3.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    return Rubric(
        name="marketing_campaign_goal_achievement_eval",
        description="Renewable energy integrated marketing campaign performance and compliance achievement measurement",
        aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
        criteria=goal_achievement_rubrics,
    )
