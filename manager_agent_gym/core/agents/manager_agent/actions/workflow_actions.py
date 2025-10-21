"""
Manager action schemas for constrained LLM generation.

Defines all possible manager actions as Pydantic models with strict
validation. These are used for structured output generation and validation.
"""

from pydantic import Field
from typing import Literal, TYPE_CHECKING, Any
from manager_agent_gym.core.common.logging import logger

if TYPE_CHECKING:
    from manager_agent_gym.schemas.domain.workflow import Workflow
    from manager_agent_gym.core.communication.service import CommunicationService


from manager_agent_gym.core.agents.manager_agent.actions.base import (
    BaseManagerAction,
    ActionResult,
)


class NoOpAction(BaseManagerAction):
    """
    Deliberately take no action; use only when observation is required and no safe or productive action is available.
    """

    action_type: Literal["noop"] = "noop"

    async def execute(
        self,
        workflow: "Workflow",
        communication_service: "CommunicationService | None" = None,
    ) -> ActionResult:
        """Execute no-op (no state modification)."""
        logger.info("Manager chose to observe without taking action")
        summary = "No operation"
        self.success = True
        self.result_summary = summary
        # No workflow modifications for no-op
        return ActionResult(
            summary=summary,
            kind="noop",
            data={},
            action_type=self.action_type,
            success=self.success,
        )


class RequestEndWorkflowAction(BaseManagerAction):
    """Request that the workflow end as soon as possible.

    Use when:
    - All required atomic tasks are completed and further work offers negligible utility
    - The stakeholder explicitly accepts the deliverables
    - Time/budget constraints imply continued work would reduce overall utility

    This action signals the engine via the communication service; the engine will terminate on the next check cycle.
    """

    action_type: Literal["request_end_workflow"] = "request_end_workflow"
    reason: str | None = Field(
        description="Optional short reason for requesting the workflow to end",
    )

    async def execute(
        self,
        workflow: "Workflow",
        communication_service: "CommunicationService | None" = None,
    ) -> ActionResult:
        """Signal end-of-workflow request through the communication service."""
        if communication_service is None:
            # Fallback: no-op with info result
            summary = "End-of-workflow request could not be sent (no communication service available)"
            self.success = False
            self.result_summary = summary
            return ActionResult(
                summary=summary, kind="info", data={}, action_type=self.action_type
            )

        try:
            reason_text = self.reason or "manager requested termination"
            communication_service.request_end_workflow(reason=reason_text)
            summary = "Requested workflow termination"
            data = {"reason": reason_text}
            self.success = True
            self.result_summary = summary
            return ActionResult(
                summary=summary, kind="info", data=data, action_type=self.action_type
            )
        except Exception as e:
            logger.error(f"Failed to request end of workflow: {e}")
            raise


class FailedAction(BaseManagerAction):
    """
    Not able to be directly called by the manager agent, but can be used to indicate that the manager agent is unable to take an action (usually due to a systems error like a llm provider refusal).
    Returns a summary of the error and the metadata, no changes are made to the workflow.
    """

    action_type: Literal["failed_action"] = "failed_action"
    metadata: dict[str, Any] = Field(description="Metadata about the failed action")

    async def execute(
        self,
        workflow: "Workflow",
        communication_service: "CommunicationService | None" = None,
    ) -> ActionResult:
        """Execute the failed action."""
        return ActionResult(
            summary=self.reasoning,
            kind="info",
            data=self.metadata,
            action_type=self.action_type,
        )
