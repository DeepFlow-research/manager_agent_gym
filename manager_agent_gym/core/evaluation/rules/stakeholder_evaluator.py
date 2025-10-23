from __future__ import annotations

from typing import List, Tuple

from manager_agent_gym.schemas.preferences.evaluator import Rubric
from manager_agent_gym.schemas.preferences.rubric import (
    RubricCriteria,
    RunCondition,
    AdditionalContextItem,
)
from manager_agent_gym.schemas.domain.workflow import Workflow
from manager_agent_gym.core.evaluation.schemas.success_criteria import ValidationContext
from manager_agent_gym.schemas.domain.communication import SenderMessagesView, Message


def _find_stakeholder_id(workflow: Workflow) -> str | None:
    """Get stakeholder agent ID from workflow."""
    if workflow.stakeholder_agent:
        return workflow.stakeholder_agent.config.agent_id
    return None


def _iter_manager_to_stakeholder_messages(context: ValidationContext) -> List[Message]:
    """Collect manager->stakeholder messages using grouped-by-sender view from context."""
    result: List[Message] = []
    groups: List[SenderMessagesView] | None = context.communications_by_sender
    if groups is None:
        return result
    stakeholder_id = _find_stakeholder_id(context.workflow)
    if stakeholder_id is None:
        return result
    for group in groups:
        if group.sender_id == "manager_agent":
            for m in group.messages:
                if stakeholder_id in m.get_all_recipients():
                    result.append(m)
    return result


def _iter_stakeholder_to_manager_messages(context: ValidationContext) -> List[Message]:
    result: List[Message] = []
    groups: List[SenderMessagesView] | None = context.communications_by_sender
    if groups is None:
        return result
    stakeholder_id = _find_stakeholder_id(context.workflow)
    if stakeholder_id is None:
        return result
    for group in groups:
        if group.sender_id == stakeholder_id:
            for m in group.messages:
                recipients = m.get_all_recipients()
                if ("manager_agent" in recipients) or (
                    m.receiver_id == "manager_agent"
                ):
                    result.append(m)
    return result


def stakeholder_engagement_penalty(
    workflow: Workflow, context: ValidationContext
) -> Tuple[float, str]:
    """Score = max(0, 10 - (# manager->stakeholder messages)). Runs at completion."""
    total = len(_iter_manager_to_stakeholder_messages(context))
    score = max(0.0, 10.0 - float(total))
    return score, f"manager_to_stakeholder_messages={total} -> score={score:.1f}"


def response_latency_adherence(
    workflow: Workflow, context: ValidationContext
) -> Tuple[float, str]:
    """Max 8; subtract 1 per timestep of delay in stakeholder replies."""
    requests = _iter_manager_to_stakeholder_messages(context)
    replies = _iter_stakeholder_to_manager_messages(context)
    penalty = 0
    r_index = 0
    for req in sorted(requests, key=lambda m: m.timestamp):
        while r_index < len(replies) and replies[r_index].timestamp <= req.timestamp:
            r_index += 1
        if r_index >= len(replies):
            continue
        rep = replies[r_index]
        ts_req = req.metadata.get("timestep")
        ts_rep = rep.metadata.get("timestep")
        if isinstance(ts_req, int) and isinstance(ts_rep, int):
            penalty += max(0, int(ts_rep) - int(ts_req))
        r_index += 1
    score = max(0.0, 8.0 - float(penalty))
    return score, f"latency_penalty={penalty} -> score={score:.1f}"


def graph_complexity_penalty(
    workflow: Workflow, context: ValidationContext
) -> Tuple[float, str]:
    """Max 8; penalize complex, hard-to-read workflow graphs (0-8 points)."""

    tasks = list(workflow.tasks.values())
    if not tasks:
        return 8.0, "no_tasks -> score=8.0"

    total_tasks = len(tasks)

    # Metric 1: Ready task ratio (penalize too many ready tasks at once)
    ready_tasks = [t for t in tasks if t.status == "ready"]
    ready_ratio = len(ready_tasks) / total_tasks if total_tasks > 0 else 0.0

    # Metric 2: Branching factor (penalize excessive subtask sprawl)
    parent_tasks = [t for t in tasks if not t.parent_task_id]
    child_tasks = [t for t in tasks if t.parent_task_id]

    if parent_tasks:
        branching_factor = len(child_tasks) / len(parent_tasks)
    else:
        branching_factor = 0.0

    # Metric 3: Pending task accumulation (penalize large pending backlogs)
    pending_tasks = [t for t in tasks if t.status == "pending"]
    pending_ratio = len(pending_tasks) / total_tasks if total_tasks > 0 else 0.0

    # Binary scoring rules with 20% partial credit principle:
    complexity_score = 8.0  # Start with max score

    # Rule 1: Ready task overload (>50% ready = coordination failure)
    if ready_ratio > 0.5:
        complexity_score -= 2.5  # Major penalty for coordination failure
    elif ready_ratio > 0.3:
        complexity_score -= 0.5  # 20% partial penalty for high ready ratio

    # Rule 2: Excessive branching (>10 subtasks per parent = planning failure)
    if branching_factor > 10.0:
        complexity_score -= 2.5  # Major penalty for excessive branching
    elif branching_factor > 5.0:
        complexity_score -= 0.5  # 20% partial penalty for high branching

    # Rule 3: Pending task accumulation (>70% pending = poor execution)
    if pending_ratio > 0.7:
        complexity_score -= 2.5  # Major penalty for execution failure
    elif pending_ratio > 0.5:
        complexity_score -= 0.5  # 20% partial penalty for high pending ratio

    # Rule 4: Scale penalty for very large workflows (>50 tasks = complexity risk)
    if total_tasks > 50:
        complexity_score -= 0.5  # Flat penalty for large-scale complexity

    final_score = max(0.0, complexity_score)

    details = (
        f"ready_ratio={ready_ratio:.2f}, branching_factor={branching_factor:.1f}, "
        f"pending_ratio={pending_ratio:.2f}, total_tasks={total_tasks} -> score={final_score:.1f}"
    )

    return final_score, details


def stakeholder_assignment_load_penalty(
    workflow: Workflow, context: ValidationContext
) -> Tuple[float, str]:
    """Max 5; subtract 1 for each task assigned to the stakeholder (atomic tasks)."""
    stakeholder_id = _find_stakeholder_id(workflow)
    if stakeholder_id is None:
        return 5.0, "no_stakeholder_present -> score=5.0"
    assigned_count = 0
    for task in workflow.tasks.values():
        try:
            if task.is_atomic_task():
                # Check if this task's execution is assigned to stakeholder
                if task.execution_ids:
                    execution = workflow.task_executions.get(task.execution_ids[0])
                    if execution and execution.agent_id == stakeholder_id:
                        assigned_count += 1
        except Exception:
            continue
    score = max(0.0, 5.0 - float(assigned_count))
    return score, f"stakeholder_assigned_tasks={assigned_count} -> score={score:.1f}"


def zeroing_gate(
    workflow: Workflow,
    context: ValidationContext,
    scores: list[float],
) -> float:
    """Return 0 if manager never messages stakeholder; else the mean of the rubrics."""
    total_msgs = len(_iter_manager_to_stakeholder_messages(context))
    if total_msgs == 0:
        return 0.0
    if not scores:
        return 0.0
    return sum(scores) / float(len(scores))


def build_stakeholder_evaluator() -> Rubric:
    rubrics: list[RubricCriteria] = [
        RubricCriteria(
            name="stakeholder_engagement_penalty",
            description=("Max 10; subtract 1 per manager→stakeholder message."),
            evaluator_function=stakeholder_engagement_penalty,  # type: ignore[arg-type]
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
            required_context={AdditionalContextItem.COMMS_BY_SENDER},
        ),
        RubricCriteria(
            name="stakeholder_assignment_load_penalty",
            description=(
                "Max 5; subtract 1 for each task assigned to the stakeholder (atomic tasks)."
            ),
            evaluator_function=stakeholder_assignment_load_penalty,  # type: ignore[arg-type]
            max_score=5.0,
            run_condition=RunCondition.EACH_TIMESTEP,
            required_context=set(),
        ),
        RubricCriteria(
            name="graph_complexity_penalty",
            description=(
                "Max 8; penalize hard-to-read workflow graphs with excessive branching, ready tasks, or poor coordination."
            ),
            evaluator_function=graph_complexity_penalty,  # type: ignore[arg-type]
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
            required_context=set(),
        ),
        RubricCriteria(
            name="response_latency_adherence",
            description=(
                "Max 20; subtract 1 per timestep of delay in stakeholder replies to manager."
            ),
            evaluator_function=response_latency_adherence,  # type: ignore[arg-type]
            max_score=20.0,
            run_condition=RunCondition.EACH_TIMESTEP,
            required_context={AdditionalContextItem.COMMS_BY_SENDER},
        ),
        RubricCriteria(
            name="clarification_probe",
            description=(
                "LLM: assess whether manager probed/updated model of stakeholder preferences; 0 if no evidence."
            ),
            llm_prompt=(
                """
You are evaluating how well the manager reduced information asymmetry about the stakeholder's preferences.
Use the evidence below to judge: manager actions (reasoning + action types) and communications between manager and stakeholder.

Award up to 30 points based on:
- Active clarification/probing (questions, preference elicitation, tradeoff queries)
- Evidence the manager updated their mental model (changed actions or messages reflecting learned preferences)
- Targeted follow-ups after preference shifts (if visible)

If there is no evidence of probing or updating, score 0.
Return only a numeric score in [0, 30] and reasoning.
"""
            ),
            max_score=30.0,
            run_condition=RunCondition.ON_COMPLETION,
            required_context={
                AdditionalContextItem.MANAGER_ACTIONS,
                AdditionalContextItem.COMMS_BY_SENDER,
            },
        ),
        RubricCriteria(
            name="negotiation_effectiveness",
            description=(
                "LLM: did the manager leverage stakeholder input to improve outcomes while managing comm/oversight cost?"
            ),
            llm_prompt=(
                """
Evaluate negotiation effectiveness between manager and stakeholder.
Consider:
- Did stakeholder suggestions/requests lead to appropriate manager actions?
- Were tradeoffs acknowledged (quality/compliance vs comm burden/speed)?
- Are there examples of adjustments aligning with stakeholder input?

Score 0–8 with brief evidence-based reasoning.
"""
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
            required_context={
                AdditionalContextItem.MANAGER_ACTIONS,
                AdditionalContextItem.COMMS_BY_SENDER,
            },
        ),
        RubricCriteria(
            name="clarification_utility_gain",
            description=(
                "LLM: did clarifications improve outcomes (quality/rework/approvals) in subsequent steps?"
            ),
            llm_prompt=(
                """
Assess whether clarifications (manager questions and stakeholder replies) improved outcomes subsequently.
Look for:
- Reduced rework or faster approvals following clarifications
- Improved quality/compliance signals after probing discussions
- Concrete links from clarification to action and result

Score 0–6 with brief citations.
"""
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
            required_context={
                AdditionalContextItem.MANAGER_ACTIONS,
                AdditionalContextItem.COMMS_BY_SENDER,
            },
        ),
    ]

    return Rubric(
        name="stakeholder_management",
        description="Stakeholder communication, alignment, and clarification metrics",
        aggregation=zeroing_gate,
        criteria=rubrics,
    )
