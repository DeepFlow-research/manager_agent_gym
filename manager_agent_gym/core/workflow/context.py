"""
Execution context for agent runs.

Provides dependency injection for communication service and other runtime context.
"""

from __future__ import annotations
from typing import Callable, TYPE_CHECKING
from uuid import UUID

from pydantic import BaseModel, Field

from manager_agent_gym.core.communication.service import CommunicationService
from manager_agent_gym.core.agents.workflow_agents.schemas.telemetry import (
    AgentToolUseEvent,
)

if TYPE_CHECKING:
    from manager_agent_gym.schemas.domain.workflow import Workflow
    from manager_agent_gym.schemas.domain.resource import Resource


class AgentExecutionContext(BaseModel):
    """Context passed to all agent tools and functions during execution."""

    communication_service: "CommunicationService"
    agent_id: str
    current_task_id: UUID | None = Field(default=None)

    # Optional sink the agent can set so tools can record usage telemetry
    tool_event_sink: Callable[[AgentToolUseEvent], None] | None = Field(default=None)

    # Optional workflow reference for actions that need it (e.g., decomposition)
    workflow: "Workflow | None" = Field(default=None)

    # Input resources for the current task (for code execution tools)
    input_resources: list["Resource"] = Field(default_factory=list)

    # AUTO-TRACKED: Resources created by tools during execution
    # Tools auto-register files they create here (e.g., execute_python_code, create_text_file)
    # Provides ground truth of what was actually created, avoiding LLM Resource construction errors
    intermediary_resources: list["Resource"] = Field(
        default_factory=list,
        description="Resources automatically created and tracked by tools during execution (role='intermediary')",
    )

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

    def register_created_resource(self, resource: "Resource") -> None:
        """
        Register a resource that was created by a tool.

        Tools should call this whenever they create files (e.g., code execution outputs,
        text files, downloads). This provides automatic ground truth tracking of created
        resources without requiring the LLM to manually construct Resource objects.

        Args:
            resource: The Resource object representing the created file (should have role='intermediary')
        """
        self.intermediary_resources.append(resource)
        from manager_agent_gym.core.common.logging import logger

        logger.debug(
            f"[{self.agent_id}] Auto-registered intermediary resource: {resource.name} "
            f"at {resource.file_path} ({resource.size_bytes} bytes)"
        )

    def get_all_available_resources(self) -> list["Resource"]:
        """
        Get all resources available in this execution context.

        Returns input resources + intermediary resources created so far.
        Useful for multi-step workflows where later tools need access to files
        created by earlier tools.

        Returns:
            Combined list of input and intermediary resources
        """
        return self.input_resources + self.intermediary_resources


# Rebuild model after all forward references are available
# This resolves the Pydantic forward reference issue with Workflow and Resource
def _rebuild_context_model():
    """Rebuild AgentExecutionContext to resolve forward references."""
    try:
        from manager_agent_gym.schemas.domain.workflow import Workflow  # noqa: F401
        from manager_agent_gym.schemas.domain.resource import Resource  # noqa: F401

        AgentExecutionContext.model_rebuild()
    except Exception:
        # If rebuild fails, context will still work but without workflow field validation
        pass


_rebuild_context_model()
