"""
Task decomposition capability for manager agents.

Provides LLM-based task decomposition into structured subtasks.
"""

from manager_agent_gym.core.agents.manager_agent.actions.task_decomposition.service import (
    decompose_task,
    find_task_in_workflow,
    get_workflow_context_string,
    TaskDecompositionError,
    TaskDecompositionRefusalError,
)

__all__ = [
    "decompose_task",
    "find_task_in_workflow",
    "get_workflow_context_string",
    "TaskDecompositionError",
    "TaskDecompositionRefusalError",
]
