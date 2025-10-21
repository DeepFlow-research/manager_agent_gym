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

__all__ = [
    # Base types
    "TaskStatus",
    # Task types
    "Task",
    "SubtaskData",
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

