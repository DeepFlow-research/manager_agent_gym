"""
Manager action schemas - re-exported from core implementation.

This module provides access to all manager actions that can be taken
during workflow execution. The actual implementations live in
core/agents/manager_agent/actions/ to keep business logic with the code.
"""

# Re-export all action classes from core
from manager_agent_gym.core.agents.manager_agent.actions import (
    ActionResult,
    BaseManagerAction,
    AssignTaskAction,
    AssignAllPendingTasksAction,
    AssignTasksToAgentsAction,
    AssignmentPair,
    CreateTaskAction,
    RemoveTaskAction,
    RefineTaskAction,
    AddTaskDependencyAction,
    RemoveTaskDependencyAction,
    InspectTaskAction,
    DecomposeTaskAction,
    SendMessageAction,
    GetWorkflowStatusAction,
    GetAvailableAgentsAction,
    GetPendingTasksAction,
    NoOpAction,
    RequestEndWorkflowAction,
    FailedAction,
)

__all__ = [
    "ActionResult",
    "BaseManagerAction",
    "AssignTaskAction",
    "AssignAllPendingTasksAction",
    "AssignTasksToAgentsAction",
    "AssignmentPair",
    "CreateTaskAction",
    "RemoveTaskAction",
    "RefineTaskAction",
    "AddTaskDependencyAction",
    "RemoveTaskDependencyAction",
    "InspectTaskAction",
    "DecomposeTaskAction",
    "SendMessageAction",
    "GetWorkflowStatusAction",
    "GetAvailableAgentsAction",
    "GetPendingTasksAction",
    "NoOpAction",
    "RequestEndWorkflowAction",
    "FailedAction",
]
