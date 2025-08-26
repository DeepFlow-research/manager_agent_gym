"""
Simple task decomposition service that breaks down tasks into subtasks.
"""

from uuid import UUID


from ...schemas.core.tasks import Task
from ...schemas.common.llm_responses import SubtaskResponse
from ..decomposition.prompts import TASK_DECOMPOSITION_PROMPT
from ..common.logging import logger
from ..common.llm_interface import (
    generate_structured_response,
    LLMInferenceTruncationError,
)


class TaskDecompositionError(Exception):
    """Raised when LLM-based task decomposition fails."""

    pass


class TaskDecompositionRefusalError(TaskDecompositionError):
    """Raised specifically when the LLM provider refuses the request."""

    pass


async def decompose_task(
    task: Task,
    seed: int,
    workflow_context: str = "",
    model: str = "o3",
) -> Task:
    """
    Decompose a task into subtasks using LLM.

    Args:
        task: The task to decompose
        workflow_context: Optional context about the broader workflow
        model: LLM model to use for decomposition

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

        response = await generate_structured_response(
            model=model,
            system_prompt=prompt,
            user_prompt=None,
            response_type=SubtaskResponse,
            temperature=1,
            seed=seed,
        )

        for subtask_data in response.subtasks:
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

    except LLMInferenceTruncationError as e:
        logger.warning("Task decomposition refused by provider: %s", str(e))
        raise TaskDecompositionRefusalError(str(e)) from e
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
