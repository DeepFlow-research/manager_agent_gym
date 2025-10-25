"""
Simple task decomposition service that breaks down tasks into subtasks.
"""

from uuid import UUID


from typing import TYPE_CHECKING

from manager_agent_gym.schemas.domain.task import Task
from manager_agent_gym.core.common.schemas.llm_responses import SubtaskResponse
from manager_agent_gym.core.agents.manager_agent.prompts.task_decomposition.prompts import (
    TASK_DECOMPOSITION_PROMPT,
)
from manager_agent_gym.core.common.logging import logger

if TYPE_CHECKING:
    from manager_agent_gym.core.common.llm_generator import LLMGenerator


class TaskDecompositionError(Exception):
    """Raised when LLM-based task decomposition fails."""

    pass


async def decompose_task(
    task: Task,
    llm_generator: "LLMGenerator",
    seed: int,
    workflow_context: str = "",
) -> Task:
    """
    Decompose a task into subtasks using LLM.

    Args:
        task: The task to decompose
        llm_generator: LLM generator for structured outputs
        seed: Random seed for reproducibility
        workflow_context: Optional context about the broader workflow

    Returns:
        The same task object with subtasks added

    Raises:
        Exception: If decomposition fails
    """

    try:
        prompt = TASK_DECOMPOSITION_PROMPT.format(
            task_name=task.name, task_description=task.description
        )

        if workflow_context:
            prompt += f"\n\n## Workflow Context\n{workflow_context}\n"
            prompt += "Ensure your subtasks fit within this broader context and don't duplicate other work.\n"

        # Use Agents SDK approach
        from agents import Agent
        from agents.run import Runner

        agent = Agent(
            name="task_decomposer",
            model=llm_generator,
            instructions=prompt,
            output_type=SubtaskResponse,
        )

        agent_result = await Runner.run(agent, "Decompose the task into subtasks.")
        response = agent_result.final_output

        for subtask_data in response.subtasks:  # type: ignore
            description = f"""Executive Summary: {subtask_data.executive_summary}

Implementation Plan: {subtask_data.implementation_plan}

Acceptance Criteria: {subtask_data.acceptance_criteria}"""

            subtask = Task(
                name=subtask_data.name,
                description=description,
                parent_task_id=task.id,
                input_resource_ids=task.input_resource_ids.copy(),
                output_resource_ids=task.output_resource_ids.copy(),
            )

            task.add_subtask(subtask)

        return task

    except Exception as e:
        logger.error("Task decomposition failed", exc_info=True)
        raise TaskDecompositionError(str(e)) from e


def find_task_in_workflow(task_id: UUID, workflow_tasks: list[Task]) -> Task | None:
    """
    Find a task by ID in a list of workflow tasks (searches recursively).

    Args:
        task_id: UUID of the task to find
        workflow_tasks: List of tasks to search

    Returns:
        The task if found, None otherwise
    """
    for task in workflow_tasks:
        found = task.find_task_by_id(task_id)
        if found:
            return found
    return None


def get_workflow_context_string(workflow_tasks: list[Task]) -> str:
    """
    Generate a context string describing the current workflow structure.

    Args:
        workflow_tasks: List of tasks in the workflow

    Returns:
        String describing the workflow structure
    """
    if not workflow_tasks:
        return "No existing workflow context."

    context_lines = ["Current workflow structure:"]
    for task in workflow_tasks:
        context_lines.append(f"- {task.name}: {task.description}")
        for subtask in task.subtasks:
            context_lines.append(f"  - {subtask.name}: {subtask.description}")

    return "\n".join(context_lines)
