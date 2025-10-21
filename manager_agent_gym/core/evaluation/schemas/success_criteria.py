"""
Success criteria schemas for workflow, task, and resource validation.
"""

from typing import Callable, Any, Awaitable
from uuid import UUID
from pydantic import BaseModel, Field
from enum import Enum

from manager_agent_gym.schemas.domain.workflow import Workflow
from manager_agent_gym.schemas.domain.communication import (
    SenderMessagesView,
    ThreadMessagesView,
)
from manager_agent_gym.core.agents.manager_agent.actions import ActionResult
from manager_agent_gym.schemas.preferences import PreferenceSnapshot
from manager_agent_gym.core.agents.workflow_agents.schemas.telemetry import (
    AgentPublicState,
    AgentToolUseEvent,
)


class ValidationLevel(str, Enum):
    """Level at which validation is applied."""

    WORKFLOW = "workflow"
    TASK = "task"
    RESOURCE = "resource"
    PREFERENCE = "preference"


class ValidationFrequency(str, Enum):
    """Frequency at which validation rules are executed."""

    MANUAL = "manual"  # Only when explicitly called
    ON_COMPLETION = "on_completion"  # When task/workflow completes
    EVERY_TIMESTEP = "every_timestep"  # Every execution timestep


class ValidationMeta(BaseModel):
    """Metadata for validation results."""

    execution_time: float = Field(
        default=0.0, description="Time taken to execute validation in seconds"
    )
    error: str | None = Field(
        default=None, description="Error message if validation failed to run"
    )
    details: dict[str, Any] = Field(
        default_factory=dict, description="Additional validation details"
    )


class ValidationResult(BaseModel):
    """Result of running a single validation rule."""

    name: str = Field(..., description="Name of the validation rule")
    score: float = Field(default=1.0, description="Numeric score achieved")
    max_score: float = Field(default=1.0, description="Maximum possible score")
    passed: bool = Field(..., description="Whether the validation passed")
    message: str = Field(..., description="Human-readable result message")
    level: ValidationLevel = Field(..., description="Level of validation")
    # Optional metric grouping for higher-level aggregation (e.g., "quality", "safety")
    metric: str | None = Field(
        default=None, description="Logical metric this result contributes to"
    )
    # Optional rule weight for aggregation within a metric
    weight: float = Field(
        default=1.0, ge=0.0, description="Weight for metric aggregation"
    )
    meta: ValidationMeta = Field(
        default_factory=ValidationMeta, description="Validation metadata"
    )

    @property
    def normalized_score(self) -> float:
        """Return score normalized to [0,1] range."""
        return self.score / self.max_score if self.max_score > 0 else 0.0

    @property
    def regret(self) -> float:
        """Direct regret calculation: gap from perfect score."""
        return max(0.0, self.max_score - self.score) / self.max_score


class ValidationContext(BaseModel):
    """Context information provided to validation rules."""

    workflow: Workflow
    current_preferences: PreferenceSnapshot | None = None
    timestep: int = 0
    # Selectively included, typed supplemental context (only set when requested)
    manager_actions: list[ActionResult] | None = None
    communications_by_sender: list[SenderMessagesView] | None = None
    communications_by_thread: list[ThreadMessagesView] | None = None
    preference_history: list[dict[str, Any]] | None = None
    stakeholder_profile: dict[str, Any] | None = None
    resources_by_task: dict[UUID, list] | None = None
    all_resources: list | None = None
    agent_public_states: dict[str, AgentPublicState] | None = None
    agent_tool_usage_by_task: dict[UUID, list[AgentToolUseEvent]] | None = None


WorkflowValidatorFunc = Callable[[Workflow], bool | float | Awaitable[bool | float]]
