"""
TaskExecution data models for Manager Agent Gym.

TaskExecution represents a concrete execution attempt of a Task by a specific agent.
This is a first-class workflow entity that owns its output resources and evaluation results.
"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

from manager_agent_gym.schemas.domain.base import TaskStatus


class TaskExecution(BaseModel):
    """A concrete execution attempt of a Task by a specific agent.

    Represents one variant's execution in multi-agent mode, or the single
    execution in single-agent mode. Owns its output resources and
    evaluation results.

    In the workflow graph:
    - TaskExecution.task_id points to the Task being executed
    - TaskExecution.output_resource_ids points to Resources produced
    - Task.execution_ids tracks all TaskExecutions for that task
    """

    id: UUID = Field(
        default_factory=uuid4,
        description="Unique identifier for this execution attempt",
    )
    task_id: UUID = Field(
        ..., description="ID of the Task this execution attempts to complete"
    )
    agent_id: str = Field(..., description="ID of the agent/worker executing this task")
    variant_index: int | None = Field(
        default=None,
        description="Index for multi-agent variants (0, 1, 2...). None for single-agent.",
    )

    # Execution lifecycle
    status: TaskStatus = Field(
        default=TaskStatus.PENDING, description="Current execution status"
    )
    started_at: datetime | None = Field(
        default=None, description="When this execution started"
    )
    completed_at: datetime | None = Field(
        default=None, description="When this execution completed or failed"
    )

    # Outputs (owned by this execution until selection)
    output_resource_ids: list[UUID] = Field(
        default_factory=list, description="IDs of resources produced by this execution"
    )

    # Evaluation results (set during ranking phase)
    evaluation_scores: dict[str, float] = Field(
        default_factory=dict,
        description="Scores from each evaluator (evaluator_name -> score)",
    )
    aggregate_score: float | None = Field(
        default=None, description="Combined score across all evaluators"
    )
    evaluation_details: dict[str, Any] = Field(
        default_factory=dict,
        description="Full evaluation outputs per evaluator (reasoning, metadata, etc.)",
    )
    rank: int | None = Field(
        default=None, description="Rank among all executions for this task (1 = best)"
    )

    # Execution metadata
    execution_result: Any | None = Field(
        default=None,
        description="Full ExecutionResult object from agent",
        exclude=True,  # Don't serialize the full result
    )
    error_message: str | None = Field(
        default=None, description="Error message if execution failed"
    )
    actual_duration_hours: float | None = Field(
        default=None, description="Actual duration in hours (reported by agent)"
    )
    actual_cost: float | None = Field(
        default=None, description="Actual cost in currency units (reported by agent)"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (rubric info, generation costs, etc.)",
    )

    def is_completed(self) -> bool:
        """Check if this execution completed successfully."""
        return self.status == TaskStatus.COMPLETED

    def is_failed(self) -> bool:
        """Check if this execution failed."""
        return self.status == TaskStatus.FAILED

    def is_running(self) -> bool:
        """Check if this execution is currently running."""
        return self.status == TaskStatus.RUNNING
