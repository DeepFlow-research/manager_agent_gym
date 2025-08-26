"""
Execution context for agent runs.

Provides dependency injection for communication service and other runtime context.
"""

from uuid import UUID

from pydantic import BaseModel, Field

from typing import Callable
from ..communication.service import CommunicationService
from ...schemas.workflow_agents.telemetry import AgentToolUseEvent


class AgentExecutionContext(BaseModel):
    """Context passed to all agent tools and functions during execution."""

    communication_service: "CommunicationService"
    agent_id: str
    current_task_id: UUID | None = Field(default=None)
    # Optional sink the agent can set so tools can record usage telemetry
    tool_event_sink: Callable[[AgentToolUseEvent], None] | None = Field(default=None)

    model_config = {"arbitrary_types_allowed": True}

    def set_current_task(self, task_id: UUID) -> None:
        """Update the current task ID for this execution context."""
        self.current_task_id = task_id

    def record_tool_event(self, event: AgentToolUseEvent) -> None:
        """Record a tool event if a sink is configured."""
        if self.tool_event_sink is not None:
            try:
                self.tool_event_sink(event)
            except Exception:
                # Best-effort; never raise from telemetry
                pass
