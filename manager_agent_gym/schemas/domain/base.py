"""
Base types and enums for the Manager Agent Gym.
"""

from enum import Enum


class TaskStatus(str, Enum):
    """Status of a task in the workflow."""

    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    UNKNOWN = "unknown"
