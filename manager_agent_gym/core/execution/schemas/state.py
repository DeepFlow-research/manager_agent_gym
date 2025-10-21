"""
Execution state definitions.
"""

from enum import Enum


class ExecutionState(str, Enum):
    """Possible states of workflow execution."""

    INITIALIZED = "initialized"
    RUNNING = "running"
    WAITING_FOR_MANAGER = "waiting_for_manager"
    EXECUTING_TASKS = "executing_tasks"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
