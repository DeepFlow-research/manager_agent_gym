"""
Core domain models for Manager Agent Gym.

This module provides the fundamental business entities used throughout the system:
tasks, resources, workflows, and communication structures.
"""

# Base types and enums
from manager_agent_gym.schemas.domain.base import (
    TaskStatus,
)

# Task types
from manager_agent_gym.schemas.domain.task import (
    Task,
    SubtaskData,
)

# TaskExecution types
from manager_agent_gym.schemas.domain.task_execution import (
    TaskExecution,
)

# Resource types
from manager_agent_gym.schemas.domain.resource import (
    Resource,
)

# Workflow types
from manager_agent_gym.schemas.domain.workflow import (
    Workflow,
)

# Communication types
from manager_agent_gym.schemas.domain.communication import (
    Message,
    MessageType,
    CommunicationThread,
    CommunicationEdge,
    CommunicationGraph,
    MessageGrouping,
    SenderMessagesView,
    ThreadMessagesView,
)

# Rebuild Workflow model now that TaskExecution is defined
Workflow.model_rebuild()

__all__ = [
    # Base types
    "TaskStatus",
    # Task types
    "Task",
    "SubtaskData",
    # TaskExecution types
    "TaskExecution",
    # Resource types
    "Resource",
    # Workflow types
    "Workflow",
    # Communication types
    "Message",
    "MessageType",
    "CommunicationThread",
    "CommunicationEdge",
    "CommunicationGraph",
    "MessageGrouping",
    "SenderMessagesView",
    "ThreadMessagesView",
]
