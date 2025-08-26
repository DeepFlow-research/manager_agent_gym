"""
Scope and section controls for workflow-level validation.

Defines what parts of a workflow should be considered when constructing
an LLM context or running per-entity function checks.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Set
from uuid import UUID

from pydantic import BaseModel, Field

from ..core.communication import MessageType


class WorkflowSection(str, Enum):
    """Parts of a workflow that can be included in validation context."""

    WORKFLOW = "workflow"  # headline stats and summary
    TASKS = "tasks"
    RESOURCES = "resources"
    MESSAGES = "messages"
    AGENTS = "agents"
    PREFERENCES = "preferences"


class WorkflowScope(BaseModel):
    """Declarative scope for selecting workflow subsets to include.

    All filters are optional; when unset, they include all for that section.
    """

    sections: Set[WorkflowSection] = Field(
        default_factory=lambda: {WorkflowSection.WORKFLOW}
    )

    # Task filters
    task_ids: Set[UUID] | None = None
    include_subtasks: bool = True

    # Resource filters
    resource_ids: Set[UUID] | None = None
    resource_types: Set[str] | None = None

    # Message filters
    message_types: Set[MessageType] | None = None
    since: datetime | None = None
    related_task_ids: Set[UUID] | None = None
