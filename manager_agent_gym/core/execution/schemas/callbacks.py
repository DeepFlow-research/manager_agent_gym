"""
Pydantic models for execution callbacks.

Defines the context object provided to end-of-timestep callbacks so that
logging/metrics hooks can observe the full state for that timestep.
"""

from typing import List, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

# Import simple types directly
from manager_agent_gym.core.execution.schemas.state import ExecutionState


class ManagerActionEntry(BaseModel):
    """Entry for a manager action taken at a specific timestep."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    timestep: int
    action: Any = None  # BaseManagerAction | None


class TimestepEndContext(BaseModel):
    """
    Context delivered to callbacks at the end of a timestep.

    Contains the manager observation/action, workflow snapshot reference,
    task transitions, preference changes, and the unified timestep result.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Timing and identification
    timestep: int = Field(..., description="Timestep index that just completed")
    execution_state: ExecutionState = Field(
        ..., description="Engine execution state at end of timestep"
    )

    # Core state
    workflow: Any = Field(
        ..., description="Current workflow state (reference)"
    )  # Workflow
    manager_observation: Any = Field(
        ..., description="Observation provided to the manager for this timestep"
    )  # ManagerObservation
    manager_action: Any = Field(
        default=None,
        description="Action chosen by the manager for this timestep, if any",
    )  # BaseManagerAction | None

    # Task transitions and queues
    tasks_started: List[UUID] = Field(default_factory=list)
    tasks_completed: List[UUID] = Field(default_factory=list)
    tasks_failed: List[UUID] = Field(default_factory=list)
    running_task_ids: List[UUID] = Field(
        default_factory=list, description="Tasks still running after this timestep"
    )
    completed_task_ids: List[UUID] = Field(default_factory=list)
    failed_task_ids: List[UUID] = Field(default_factory=list)

    # Preference and coordination events
    preference_change_event: Any = Field(default=None)  # PreferenceChange | None
    agent_coordination_changes: List[str] = Field(default_factory=list)

    # Metrics and outputs
    execution_time_seconds: float = Field(
        ..., description="Wall-clock time spent in this timestep"
    )
    execution_result: Any = Field(
        ..., description="Unified result object for this timestep"
    )  # ExecutionResult
