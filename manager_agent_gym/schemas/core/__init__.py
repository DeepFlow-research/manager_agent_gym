"""
Core type definitions for Manager Agent Gym.

This module provides all the data models needed for implementing
the Manager Agent research challenge as described in the POSG formalization.
"""

# Base types and enums
from .base import (
    TaskStatus,
)

# Resource types
from .resources import (
    Resource,
)

# Task types
from .tasks import (
    Task,
)

# Communication types
from .communication import (
    Message,
)

# Agent coordination types (deprecated)
from .agent_coordination import (
    ScheduledAgentChange,
)

# Workflow types
from .workflow import (
    Workflow,
)

__all__ = [
    # Base types
    "TaskStatus",
    # Resource types
    "Resource",
    # Task types
    "Task",
    # Communication types
    "Message",
    # Agent coordination types (deprecated)
    "ScheduledAgentChange",
    # Workflow types
    "Workflow",
]
