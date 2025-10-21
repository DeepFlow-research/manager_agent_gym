"""
Manager agent API schemas.

This module provides the observation and action types used by manager agents
to interact with the workflow execution system.
"""

from manager_agent_gym.schemas.manager.observation import (
    ManagerObservation,
)

# Re-export all actions
from manager_agent_gym.schemas.manager.actions import (
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
    "ManagerObservation",
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

