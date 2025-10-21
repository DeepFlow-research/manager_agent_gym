from __future__ import annotations

from typing import List, Tuple

from manager_agent_gym.schemas.domain.workflow import Workflow
from manager_agent_gym.core.evaluation.schemas.success_criteria import ValidationContext
from manager_agent_gym.schemas.preferences.evaluator import Rubric
from manager_agent_gym.schemas.preferences.rubric import RubricCriteria, RunCondition
from examples.end_to_end_examples.standard_rules import agent_utilization_efficiency


def _collect_task_deadtime_seconds(workflow: Workflow) -> List[float]:
    deadtimes: List[float] = []
    for task in workflow.tasks.values():
        # Include only tasks that actually started (engine uses started_at check)
        if task.started_at is not None:
            deadtimes.append(float(task.calculate_coordination_deadtime_seconds()))
    return deadtimes


def coordination_deadtime_score(
    workflow: Workflow, context: ValidationContext
) -> Tuple[float, str]:
    """Score in [0,1] favoring lower average coordination deadtime.

    Mapping: score = 1 / (1 + avg_deadtime_minutes)
    """
    deadtimes = _collect_task_deadtime_seconds(workflow)
    if not deadtimes:
        return 1.0, "no started tasks"
    avg_seconds = sum(deadtimes) / float(len(deadtimes))
    avg_minutes = avg_seconds / 60.0
    score = 1.0 / (1.0 + max(0.0, avg_minutes))
    return score, f"avg_deadtime_min={avg_minutes:.2f}"


def deadtime_efficiency_score(
    workflow: Workflow, context: ValidationContext
) -> Tuple[float, str]:
    """Fraction of started tasks with zero coordination deadtime.

    Score = (# tasks with 0 deadtime) / (# started tasks)
    """
    deadtimes = _collect_task_deadtime_seconds(workflow)
    if not deadtimes:
        return 1.0, "no started tasks"
    zero_count = sum(1 for d in deadtimes if d <= 0.0)
    score = zero_count / float(len(deadtimes))
    return score, f"zero_deadtime={zero_count}/{len(deadtimes)}"


def build_operational_efficiency_evaluator() -> Rubric:
    rubrics: list[RubricCriteria] = [
        RubricCriteria(
            name="coordination_deadtime",
            description="Lower average coordination deadtime yields higher score.",
            evaluator_function=coordination_deadtime_score,  # type: ignore[arg-type]
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="deadtime_efficiency",
            description="Fraction of started tasks with zero coordination deadtime.",
            evaluator_function=deadtime_efficiency_score,  # type: ignore[arg-type]
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="agent_utilization_efficiency",
            description="Fraction of started tasks with zero coordination deadtime.",
            evaluator_function=agent_utilization_efficiency,  # type: ignore[arg-type]
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="parallelism_opportunity_exploitation",
            llm_prompt=(
                "You are evaluating operational efficiency with a focus on PARALLEL WORK.\n"
                "Instructions:\n"
                "- Inspect the task dependency graph, current statuses, and agent capacities.\n"
                "- Determine: (a) inherent parallelism available now (number of READY tasks without dependencies),\n"
                "  (b) whether the manager has started enough tasks in parallel given available agents/capacity,\n"
                "  (c) presence of avoidable bottlenecks (e.g., many READY tasks but only one RUNNING),\n"
                "  (d) signs of batching/parallel scheduling across workstreams.\n"
                "Scoring guidance (0..10):\n"
                "- 0-2: Parallelism available but not used; serial execution dominates.\n"
                "- 3-5: Some parallel work started, but clear unused capacity or bottlenecks remain.\n"
                "- 6-8: Good exploitation of available parallelism with minimal idle capacity.\n"
                "- 9-10: Aggressive and well-coordinated parallel scheduling with balanced load across agents.\n"
            ),
            max_score=10.0,
            run_condition=RunCondition.EACH_TIMESTEP,
        ),
        RubricCriteria(
            name="planning_scope_quality",
            llm_prompt=(
                "Evaluate WELL-SCOPEDNESS and FORWARD PLANNING of the workflow.\n"
                "Consider:\n"
                "- Presence of a clear end-to-end roadmap (milestones, dependencies, acceptance criteria).\n"
                "- Depth of task decomposition ahead of execution (e.g., multiple future READY tasks vs. only next-step).\n"
                "- Evidence that the manager avoids purely autoregressive single-task assignment (looks ahead, prepares parallel tracks).\n"
                "- Quality of task definitions (specific deliverables, owners, timelines) and coverage of critical workstreams.\n"
                "Scoring (0..10):\n"
                "- 0-2: Mostly next-step actions; roadmap unclear; tasks vague.\n"
                "- 3-5: Partial roadmap; some forward tasks but gaps; limited decomposition.\n"
                "- 6-8: Solid multi-step plan with clear scope and parallel preparation.\n"
                "- 9-10: Comprehensive roadmap, well-scoped tasks across all streams, proactive planning minimizing idle time.\n"
            ),
            max_score=10.0,
            run_condition=RunCondition.EACH_TIMESTEP,
        ),
    ]

    return Rubric(
        name="operational_efficiency",
        description="Operational efficiency including coordination deadtime, utilization, parallelism, and planning quality",
        criteria=rubrics,
    )
