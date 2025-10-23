"""
Manager agent observation and action data models.
"""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

from manager_agent_gym.schemas.domain.communication import Message
from manager_agent_gym.schemas.preferences.constraints import Constraint
from manager_agent_gym.schemas.agents.stakeholder import (
    StakeholderPublicProfile,
)
from manager_agent_gym.schemas.agents.base import AgentConfig


class ResourcePreview(BaseModel):
    """Lightweight preview of a resource for manager observation."""

    resource_id: UUID = Field(..., description="Unique resource identifier")
    task_id: UUID = Field(..., description="Task that created this resource")
    name: str = Field(..., description="Resource name")
    description: str = Field(..., description="Resource description")
    mime_type: str = Field(..., description="MIME type")
    size_bytes: int = Field(..., description="File size in bytes")
    preview_text: str | None = Field(
        default=None, description="Text preview or summary (for text resources)"
    )
    thumbnail_available: bool = Field(
        default=False,
        description="Whether full visual content available via inspection tool",
    )


class ManagerObservation(BaseModel):
    """Observation provided to manager agent at each timestep."""

    # Allow non-Pydantic types like AgentInterface in fields
    model_config = ConfigDict(arbitrary_types_allowed=True)
    workflow_summary: str
    timestep: int = Field(..., description="Current timestep number")
    workflow_id: UUID = Field(..., description="ID of the workflow being executed")
    execution_state: str = Field(..., description="Current execution state")
    task_status_counts: dict[str, int] = Field(
        default_factory=dict, description="Count of tasks by status"
    )
    ready_task_ids: list[UUID] = Field(
        default_factory=list, description="Tasks ready to start"
    )
    running_task_ids: list[UUID] = Field(
        default_factory=list, description="Currently running tasks"
    )
    completed_task_ids: list[UUID] = Field(
        default_factory=list, description="Completed task IDs"
    )
    failed_task_ids: list[UUID] = Field(
        default_factory=list, description="Failed task IDs"
    )
    available_agent_metadata: list[AgentConfig] = Field(
        default_factory=list, description="Available agent metadata"
    )
    recent_messages: list[Message] = Field(
        default_factory=list, description="Recent communications"
    )
    workflow_progress: float = Field(
        ..., ge=0.0, le=1.0, description="Completion percentage"
    )
    observation_timestamp: datetime = Field(default_factory=datetime.now)

    # Optional timeline awareness
    max_timesteps: int | None = Field(
        default=None, description="Configured maximum timesteps for this run"
    )
    timesteps_remaining: int | None = Field(
        default=None, description="Remaining timesteps before reaching the limit"
    )
    time_progress: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Fraction of timestep budget consumed (0..1)",
    )

    # Constraints visibility
    constraints: list[Constraint] = Field(
        default_factory=list, description="Workflow constraints (hard/soft/etc.)"
    )

    # Dynamic ID universes for schema-constrained action generation
    # These allow the manager agents to constrain IDs to valid values at generation time
    task_ids: list[UUID] = Field(
        default_factory=list, description="All task IDs currently in the workflow"
    )
    resource_ids: list[UUID] = Field(
        default_factory=list, description="All resource IDs currently in the workflow"
    )
    agent_ids: list[str] = Field(
        default_factory=list, description="All agent IDs registered in the workflow"
    )

    stakeholder_profile: StakeholderPublicProfile | None = Field(
        default=None,
        description="Public stakeholder profile",
    )

    # Multimodal resource previews
    recent_resource_previews: list[ResourcePreview] = Field(
        default_factory=list, description="Previews of recently created resources"
    )
