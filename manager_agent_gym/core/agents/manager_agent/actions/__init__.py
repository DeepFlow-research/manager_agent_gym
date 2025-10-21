"""
Manager actions with execution logic.

Actions define both data models (Pydantic) and execution behavior (execute methods).
These have been moved from schemas/ to core/ since they contain state mutation logic.
"""

from manager_agent_gym.core.agents.manager_agent.actions.base import (
    ActionResult,
    BaseManagerAction,
)
from manager_agent_gym.core.agents.manager_agent.actions.assignment_actions import (
    AssignTaskAction,
    AssignAllPendingTasksAction,
    AssignTasksToAgentsAction,
    AssignmentPair,
)
from manager_agent_gym.core.agents.manager_agent.actions.task_actions import (
    CreateTaskAction,
    RemoveTaskAction,
    RefineTaskAction,
    AddTaskDependencyAction,
    RemoveTaskDependencyAction,
    InspectTaskAction,
    DecomposeTaskAction,
)
from manager_agent_gym.core.agents.manager_agent.actions.communication_actions import (
    SendMessageAction,
)
from manager_agent_gym.core.agents.manager_agent.actions.query_actions import (
    GetWorkflowStatusAction,
    GetAvailableAgentsAction,
    GetPendingTasksAction,
)
from manager_agent_gym.core.agents.manager_agent.actions.workflow_actions import (
    NoOpAction,
    RequestEndWorkflowAction,
    FailedAction,
)
from manager_agent_gym.core.agents.manager_agent.actions.preference_clarification import (
    AskClarificationQuestionsAction,
    GeneratePreferenceRubricAction,
)

__all__ = [
    # Base
    "ActionResult",
    "BaseManagerAction",
    # Assignment
    "AssignTaskAction",
    "AssignAllPendingTasksAction",
    "AssignTasksToAgentsAction",
    "AssignmentPair",
    # Task management
    "CreateTaskAction",
    "RemoveTaskAction",
    "RefineTaskAction",
    "AddTaskDependencyAction",
    "RemoveTaskDependencyAction",
    "InspectTaskAction",
    "DecomposeTaskAction",
    # Communication
    "SendMessageAction",
    # Query
    "GetWorkflowStatusAction",
    "GetAvailableAgentsAction",
    "GetPendingTasksAction",
    # Workflow control
    "NoOpAction",
    "RequestEndWorkflowAction",
    "FailedAction",
    # Decomposition
    "AskClarificationQuestionsAction",
    "GeneratePreferenceRubricAction",
]
