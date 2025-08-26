"""
Pydantic models for execution callbacks.

Defines the context object provided to end-of-timestep callbacks so that
logging/metrics hooks can observe the full state for that timestep.
"""

from typing import List
from uuid import UUID

from pydantic import BaseModel, Field

from ..core.workflow import Workflow
from ..preferences.preference import PreferenceChange
from ..execution.manager import ManagerObservation
from ..execution.manager_actions import BaseManagerAction
from ..execution.state import ExecutionState
from ..unified_results import ExecutionResult


class ManagerActionEntry(BaseModel):
    """Entry for a manager action taken at a specific timestep."""

    timestep: int
    action: BaseManagerAction | None = None


class TimestepEndContext(BaseModel):
    """
    Context delivered to callbacks at the end of a timestep.

    Contains the manager observation/action, workflow snapshot reference,
    task transitions, preference changes, and the unified timestep result.
    """

    # Timing and identification
    timestep: int = Field(..., description="Timestep index that just completed")
    execution_state: ExecutionState = Field(
        ..., description="Engine execution state at end of timestep"
    )

    # Core state
    workflow: Workflow = Field(..., description="Current workflow state (reference)")
    manager_observation: ManagerObservation = Field(
        ..., description="Observation provided to the manager for this timestep"
    )
    manager_action: BaseManagerAction | None = Field(
        default=None,
        description="Action chosen by the manager for this timestep, if any",
    )

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
    preference_change_event: PreferenceChange | None = Field()
    agent_coordination_changes: List[str] = Field(default_factory=list)

    # Metrics and outputs
    execution_time_seconds: float = Field(
        ..., description="Wall-clock time spent in this timestep"
    )
    execution_result: ExecutionResult = Field(
        ..., description="Unified result object for this timestep"
    )
