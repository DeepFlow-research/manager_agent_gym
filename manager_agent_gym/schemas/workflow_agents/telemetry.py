"""
Telemetry models for agent behavior and public state summaries.

These models are safe for exposure in evaluation contexts and outputs
as they avoid raw content and sensitive parameters.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class AgentToolUseEvent(BaseModel):
    """Compact, privacy-aware record of a single tool invocation."""

    timestamp: datetime = Field(default_factory=datetime.now)
    agent_id: str = Field(..., description="ID of the invoking agent")
    task_id: UUID | None = Field(
        default=None, description="Task the tool call was associated with"
    )
    tool_name: str = Field(..., description="Name of the tool invoked")
    succeeded: bool = Field(default=True, description="Whether the call succeeded")

    # Performance/usage metrics (optional, if available)
    duration_ms: int | None = Field(default=None)
    latency_ms: int | None = Field(default=None)
    tokens_in: int | None = Field(default=None)
    tokens_out: int | None = Field(default=None)
    result_size: int | None = Field(default=None, description="Approx size of result")
    external_calls: int | None = Field(default=None, description="Downstream calls")

    # Redacted parameters
    args_fingerprint: str | None = Field(
        default=None, description="Hash/shape of arguments; no raw content"
    )

    # Error reporting (if failed)
    error_type: str | None = Field(default=None)
    error_message: str | None = Field(default=None)

    # Provenance (if applicable)
    evidence_sources: list[str] | None = Field(
        default=None, description="List of domains/URLs referenced"
    )


class AgentPublicState(BaseModel):
    """Redacted public snapshot of an agent for evaluation purposes."""

    agent_id: str = Field(...)
    agent_type: str = Field(...)

    # Assignment and availability
    is_available: bool = Field(default=True)
    current_task_ids: list[UUID] = Field(default_factory=list)
    max_concurrent_tasks: int = Field(default=1)

    # Performance tracking
    tasks_completed: int = Field(default=0)
    joined_at: datetime = Field(default_factory=datetime.now)

    # Optional aggregates (if available)
    avg_tool_latency_ms: float | None = Field(default=None)
    avg_tokens_in: float | None = Field(default=None)
    avg_tokens_out: float | None = Field(default=None)
    avg_cost_per_task: float | None = Field(default=None)

    # Summaries (optional)
    tool_usage_summary: dict[str, int] | None = Field(
        default=None, description="Counts by tool name"
    )
    tool_error_rates: dict[str, float] | None = Field(
        default=None, description="Error rate per tool name (0..1)"
    )
    comms_summary: dict[str, Any] | None = Field(
        default=None, description="Communication behavior summary"
    )
