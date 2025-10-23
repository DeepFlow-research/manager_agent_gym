"""
Public API schemas for Manager Agent Gym.

This module exports all public-facing types that users and examples interact with.
Private implementation schemas are located in core/*/schemas/ directories.
"""

# Domain models (core business entities)
from manager_agent_gym.schemas.domain import (
    TaskStatus,
    Task,
    SubtaskData,
    Resource,
    Workflow,
    Message,
    MessageType,
    CommunicationThread,
    CommunicationEdge,
    CommunicationGraph,
    MessageGrouping,
    SenderMessagesView,
    ThreadMessagesView,
)

# Agent configuration
from manager_agent_gym.schemas.agents import (
    AgentConfig,
    AIAgentConfig,
    HumanAgentConfig,
    AITaskOutput,
    HumanWorkOutput,
    HumanTimeEstimation,
    StakeholderConfig,
    StakeholderPublicProfile,
    StakeholderPreferenceState,
)

# Manager agent API
from manager_agent_gym.schemas.manager import (
    ManagerObservation,
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

# Preferences (already well-organized, keep as-is)
from manager_agent_gym.schemas.preferences import (
    RubricCriteria,
    Preference,
    PreferenceSnapshot,
    PreferenceChangeEvent,
    PreferenceWeightUpdateRequest,
    WeightUpdateMode,
    MissingPreferencePolicy,
    RedistributionStrategy,
    AggregationStrategy,
    Rubric,
    PreferenceExemplar,
    RubricResult,
    PreferenceScore,
    EvaluationResult,
    Constraint,
)

__all__ = [
    # Domain models
    "TaskStatus",
    "Task",
    "SubtaskData",
    "Resource",
    "Workflow",
    "Message",
    "MessageType",
    "CommunicationThread",
    "CommunicationEdge",
    "CommunicationGraph",
    "MessageGrouping",
    "SenderMessagesView",
    "ThreadMessagesView",
    # Agent configuration
    "AgentConfig",
    "AIAgentConfig",
    "HumanAgentConfig",
    "AITaskOutput",
    "HumanWorkOutput",
    "HumanTimeEstimation",
    "StakeholderConfig",
    "StakeholderPublicProfile",
    "StakeholderPreferenceState",
    # Manager agent API
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
    # Preferences
    "RubricCriteria",
    "Preference",
    "PreferenceSnapshot",
    "PreferenceChangeEvent",
    "PreferenceWeightUpdateRequest",
    "WeightUpdateMode",
    "MissingPreferencePolicy",
    "RedistributionStrategy",
    "AggregationStrategy",
    "Rubric",
    "PreferenceExemplar",
    "RubricResult",
    "PreferenceScore",
    "EvaluationResult",
    "Constraint",
]
