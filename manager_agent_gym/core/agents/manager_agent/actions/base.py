"""
Base classes for manager actions.

Defines ActionResult and BaseManagerAction that all concrete actions inherit from.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Literal

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from manager_agent_gym.core.communication.service import CommunicationService
    from manager_agent_gym.schemas.domain.workflow import Workflow
    from manager_agent_gym.core.common.llm_generator import LLMGenerator


class ActionResult(BaseModel):
    """Structured result returned by manager actions.

    Example:
        ```python
        ActionResult(
            action_type="assign_task",
            summary="Assigned T123 to ai_writer",
            kind="mutation",
            data={"task_id": "...", "agent_id": "ai_writer"},
            timestep=3,
            success=True,
        )
        ```
    """

    action_type: Literal[
        "assign_task",
        "assign_all_pending_tasks",
        "create_task",
        "remove_task",
        "send_message",
        "noop",
        "get_workflow_status",
        "get_available_agents",
        "get_pending_tasks",
        "refine_task",
        "add_task_dependency",
        "remove_task_dependency",
        "failed_action",
        "inspect_task",
        "request_end_workflow",
        "decompose_task",
        "assign_tasks_to_agents",
        "ask_clarification_questions",
        "generate_preference_rubric",
        "signal_decomposition_complete",
    ] = Field(description="Type of action result")
    summary: str = Field(description="Short summary of what happened / info returned")
    kind: Literal[
        "mutation", "info", "noop", "message", "inspection", "failed_action", "unknown"
    ] = Field(description="Type of action result")
    data: dict[str, Any] = Field(
        description="Optional structured payload for follow-up use (empty if not applicable)",
    )
    timestep: int | None = Field(
        default=None, description="Timestep of the action, set by the engine"
    )
    success: bool = Field(
        default=True, description="Whether the action succeeded (set by execute)"
    )


class BaseManagerAction(BaseModel, ABC):
    """
    Base class for all manager actions.

    All action classes must inherit from this and implement the execute method.
    This ensures type safety and consistent execution interface.
    """

    reasoning: str = Field(
        default="",  # Made optional since top-level ConstrainedManagerAction has reasoning
        description="Concise 2–3 sentence rationale for the chosen action",
    )
    success: bool | None = Field(
        default=None,  # Set by execute method after action runs
        description="Whether the action succeeded (set by execute)",
    )
    result_summary: str | None = Field(
        default=None,  # Set by execute method after action runs
        description="Short human-readable summary of the result (set by execute)",
    )

    @abstractmethod
    async def execute(
        self,
        workflow: "Workflow",
        communication_service: "CommunicationService | None" = None,
        llm_generator: "LLMGenerator | None" = None,
    ) -> ActionResult:
        """
        Execute this action against the workflow.

        Args:
            workflow: The workflow to modify
            communication_service: Optional communication service for agent messaging
            llm_generator: Optional LLM generator for structured outputs (e.g., task decomposition)

        Returns:
            ActionResult summarizing the mutation or information retrieved

        Raises:
            ValueError: If action parameters are invalid for current workflow state
        """
        raise NotImplementedError
