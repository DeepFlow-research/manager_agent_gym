"""
Manager agent observation and action data models.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

from ...schemas.core import Message
from ...schemas.preferences.constraints import Constraint
from ...schemas.workflow_agents.stakeholder import StakeholderPublicProfile
from ...schemas.workflow_agents.config import AgentConfig


class AvailabilityNotice(BaseModel):
    """An outage or rate limit on one worker, as shown to the manager (specialist-loss benchmark).

    Public information only: it names the worker and the effect, never a task or a substitute.
    """

    timestep: int = Field(..., description="Timestep at which the event took effect")
    agent_id: str
    kind: Literal["outage", "rate_limit"]
    status: Literal["unavailable", "recovered"] = Field(
        ..., description="unavailable: in effect now; recovered: the worker is available again"
    )
    reset_timestep: int | None = Field(
        default=None,
        description="Timestep at which the worker is available again; None if not before the run ends",
    )
    message: str = Field(default="", description="Human-readable statement of the effect")


class RunningTaskInfo(BaseModel):
    """A task currently running, as shown to the manager."""

    task_id: UUID
    name: str
    agent_id: str | None = None
    started_timestep: int | None = None


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

    running_task_info: list[RunningTaskInfo] = Field(
        default_factory=list,
        description="Running tasks with their worker and start timestep (empty unless team awareness is on)",
    )
    availability_notices: list[AvailabilityNotice] = Field(
        default_factory=list,
        description="Outages and rate limits so far, oldest first (empty outside the specialist-loss benchmark)",
    )

    stakeholder_profile: StakeholderPublicProfile = Field(
        description="Public stakeholder profile",
    )
