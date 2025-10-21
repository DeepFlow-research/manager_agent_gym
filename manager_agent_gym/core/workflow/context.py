"""
Execution context for agent runs.

Provides dependency injection for communication service and other runtime context.
"""

from __future__ import annotations
from typing import Callable, TYPE_CHECKING
from uuid import UUID

from pydantic import BaseModel, Field

from manager_agent_gym.core.communication.service import CommunicationService
from manager_agent_gym.core.agents.workflow_agents.schemas.telemetry import AgentToolUseEvent

if TYPE_CHECKING:
    from manager_agent_gym.schemas.domain.workflow import Workflow


class AgentExecutionContext(BaseModel):
    """Context passed to all agent tools and functions during execution."""

    communication_service: "CommunicationService"
    agent_id: str
    current_task_id: UUID | None = Field(default=None)

    # Optional sink the agent can set so tools can record usage telemetry
    tool_event_sink: Callable[[AgentToolUseEvent], None] | None = Field(default=None)

    # Optional workflow reference for actions that need it (e.g., decomposition)
    workflow: "Workflow | None" = Field(default=None)

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
