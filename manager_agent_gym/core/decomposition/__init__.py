"""
Task decomposition module for breaking down tasks into structured subtasks.
"""

from .service import (
    decompose_task,
    find_task_in_workflow,
    get_workflow_context_string,
)

__all__ = [
    "decompose_task",
    "find_task_in_workflow",
    "get_workflow_context_string",
]
