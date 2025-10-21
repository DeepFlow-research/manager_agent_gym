"""
Manager action schemas for constrained LLM generation.

Defines all possible manager actions as Pydantic models with strict
validation. These are used for structured output generation and validation.
"""

from pydantic import Field
from typing import Literal, TYPE_CHECKING
from manager_agent_gym.schemas.domain.communication import Message, MessageType
from manager_agent_gym.core.common.logging import logger

if TYPE_CHECKING:
    from manager_agent_gym.schemas.domain.workflow import Workflow
    from manager_agent_gym.core.communication.service import CommunicationService


from manager_agent_gym.core.agents.manager_agent.actions.base import (
    BaseManagerAction,
    ActionResult,
)


class SendMessageAction(BaseManagerAction):
    """Send a direct or broadcast coordination message.

    Use to:
    - Elicit preference tradeoffs (quality vs speed vs cost) without revealing hidden rubrics
    - Request review/approval or stakeholder acceptance
    - Clarify requirements or confirm scope changes
    - Inform task agents about the manner in which they should proceed, give feedback, seek information on how they intend to work on tasks, ect.

    Examples:
    - To stakeholder: "Could you prioritize speed vs quality for the next milestone (choose one)?"
    - To stakeholder: "Please confirm: Is v1 acceptable to ship as-is, or should we add a validation step?"
    - Broadcast: "All agents: pause work on feature X pending stakeholder decision."

    Note: Messaging has communication/oversight costs in evaluators; ask crisp, high-value questions.
    """

    action_type: Literal["send_message"] = "send_message"
    content: str = Field(description="Message content")
    receiver_id: str | None = Field(
        description="Specific receiver ID, or None for broadcast"
    )

    async def execute(
        self,
        workflow: "Workflow",
        communication_service: "CommunicationService | None" = None,
    ) -> ActionResult:
        """Execute message sending using the injected communication service."""
        if communication_service:
            if self.receiver_id:
                # Direct message to specific agent
                await communication_service.send_direct_message(
                    from_agent="manager_agent",
                    to_agent=self.receiver_id,
                    content=self.content,
                    message_type=MessageType.ALERT,
                )
            else:
                # Broadcast to all agents
                await communication_service.broadcast_message(
                    from_agent="manager_agent",
                    content=self.content,
                    message_type=MessageType.ALERT,
                )
        else:
            # Fallback: add directly to workflow messages (backward compatibility)
            message = Message(
                sender_id="manager_agent",
                receiver_id=self.receiver_id,
                content=self.content,
                message_type=MessageType.ALERT,
            )
            workflow.messages.append(message)

        logger.info(f"Manager message sent: {self.content[:50]}...")
        summary = f"Sent message{' to ' + self.receiver_id if self.receiver_id else ' (broadcast)'}"
        data = {"receiver_id": self.receiver_id, "length": len(self.content)}
        self.success = True
        self.result_summary = summary
        return ActionResult(
            summary=summary,
            kind="message",
            data=data,
            action_type=self.action_type,
            success=self.success,
        )
