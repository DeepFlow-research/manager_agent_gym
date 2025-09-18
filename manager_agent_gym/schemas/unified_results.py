"""
Unified result types to replace duplicate execution result schemas.

This consolidates TaskExecutionResult, TimestepResult, and ExecutionMetadata
into clean, focused types that eliminate duplication.
"""

from datetime import datetime
from typing import Any, TYPE_CHECKING
from uuid import UUID

from pydantic import BaseModel, Field

from ..schemas.core import Resource
from ..core.common.logging import logger
from ..schemas.preferences.preference import PreferenceChange

if TYPE_CHECKING:
    from ..schemas.execution.manager import ManagerObservation


class ExecutionResult(BaseModel):
    """
    Unified result type for any execution (task, timestep, workflow).

    Replaces: TaskExecutionResult, TimestepResult, ExecutionMetadata
    """

    # Core identification
    id: str = Field(..., description="Unique identifier for this execution")
    executor_id: str = Field(..., description="ID of the agent/manager that executed")

    # What was executed
    target_type: str = Field(
        ..., description="Type of target: 'task', 'timestep', 'workflow'"
    )
    target_ids: list[UUID] = Field(
        ..., description="IDs of tasks/items that were executed"
    )

    # Execution outcome
    success: bool = Field(..., description="Whether execution was successful")
    error_message: str | None = Field(
        default=None, description="Error message if failed"
    )

    # Outputs produced
    output_resources: list[Resource] = Field(
        default_factory=list, description="Resources created by execution"
    )

    # Timing
    execution_time_seconds: float = Field(
        ..., description="Actual wall-clock execution time"
    )
    simulated_duration_hours: float = Field(
        ..., description="Simulated/realistic duration for metrics"
    )
    completed_at: datetime = Field(default_factory=datetime.now)

    # Cost and usage
    actual_cost: float = Field(default=0.0, description="Actual cost of execution")
    tokens_used: int = Field(default=0, description="Tokens used (for AI agents)")

    # Flexible metadata for specific use cases
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional execution metadata"
    )

    # Notes and reasoning
    execution_notes: list[str] = Field(
        default_factory=list, description="Notes about execution process"
    )
    reasoning: str | None = Field(
        default=None, description="Reasoning for approach taken"
    )


# Convenience constructors for common cases
def create_task_result(
    task_id: UUID,
    agent_id: str,
    success: bool,
    execution_time: float,
    resources: list[Resource] | None = None,
    cost: float = 0.0,
    error: str | None = None,
    simulated_duration_hours: float = 0.0,
    **metadata,
) -> ExecutionResult:
    """Create a result for task execution."""
    return ExecutionResult(
        id=f"task_{task_id}",
        executor_id=agent_id,
        target_type="task",
        target_ids=[task_id],
        success=success,
        error_message=error,
        output_resources=resources or [],
        execution_time_seconds=execution_time,
        simulated_duration_hours=simulated_duration_hours,
        actual_cost=cost,
        metadata=metadata,
    )


def create_timestep_result(
    timestep: int,
    manager_id: str,
    tasks_started: list[UUID],
    tasks_completed: list[UUID],
    tasks_failed: list[UUID],
    execution_time: float,
    completed_tasks_simulated_hours: float,
    manager_action=None,
    manager_observation: "ManagerObservation | None" = None,
    workflow_snapshot: dict | None = None,
    preference_change_event=None,
    **metadata,
) -> ExecutionResult:
    """Create a result for timestep execution."""
    all_tasks = tasks_started + tasks_completed + tasks_failed
    success = len(tasks_failed) == 0

    # Build comprehensive metadata including preference tracking
    timestep_metadata = {
        "timestep": timestep,
        "tasks_started": [str(t) for t in tasks_started],
        "tasks_completed": [str(t) for t in tasks_completed],
        "tasks_failed": [str(t) for t in tasks_failed],
        **metadata,
    }

    # Add manager action and observation if provided
    if manager_action:
        try:
            timestep_metadata["manager_action"] = manager_action.model_dump(mode="json")
        except AttributeError:
            raise
    if manager_observation:
        try:
            timestep_metadata["manager_observation"] = manager_observation.model_dump(
                mode="json"
            )
        except AttributeError:
            raise
    if workflow_snapshot:
        timestep_metadata["workflow_snapshot"] = workflow_snapshot

    # Track preference changes at this timestep
    if preference_change_event:
        try:
            # New minimal event; serialize known fields if present
            if isinstance(preference_change_event, PreferenceChange):
                timestep_metadata["preference_change"] = {
                    "timestep": preference_change_event.timestep,
                    "previous_weights": preference_change_event.previous_weights,
                    "new_weights": preference_change_event.new_weights,
                    "change_type": preference_change_event.change_type,
                    "magnitude": preference_change_event.magnitude,
                    "trigger_reason": preference_change_event.trigger_reason,
                }
        except Exception:
            logger.debug(
                "Failed to serialize preference change event; continuing without it",
                exc_info=True,
            )

    return ExecutionResult(
        id=f"timestep_{timestep}",
        executor_id=manager_id,
        target_type="timestep",
        target_ids=all_tasks,
        success=success,
        execution_time_seconds=execution_time,
        simulated_duration_hours=completed_tasks_simulated_hours,
        metadata=timestep_metadata,
    )
