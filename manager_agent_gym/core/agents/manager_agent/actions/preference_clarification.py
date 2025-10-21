"""
Manager actions for preference clarification and rubric generation.

Clean, communication-driven actions for the pre-execution phase.
"""

from pydantic import Field
from typing import Literal, TYPE_CHECKING
from manager_agent_gym.schemas.domain.communication import MessageType
from manager_agent_gym.core.common.logging import logger
from manager_agent_gym.core.agents.manager_agent.reward_shaping.service import (
    decompose_preference_to_evaluator,
)
from manager_agent_gym.core.agents.stakeholder_agent.rubric_stakeholder import (
    ClarificationStakeholderAgent,
)

if TYPE_CHECKING:
    from manager_agent_gym.schemas.domain.workflow import Workflow
    from manager_agent_gym.core.communication.service import CommunicationService

from manager_agent_gym.core.agents.manager_agent.actions.base import (
    BaseManagerAction,
    ActionResult,
)


class AskClarificationQuestionsAction(BaseManagerAction):
    """Send clarification questions to stakeholder via communication service.

    Sends questions as REQUEST messages. Does not wait for responses -
    responses are collected in subsequent timesteps when manager reads messages.
    """

    action_type: Literal["ask_clarification_questions"] = "ask_clarification_questions"
    question: str = Field(
        description="Questions to ask the stakeholder to understand their preferences on how to complete the task best.",
    )

    async def execute(
        self,
        workflow: "Workflow",
        communication_service: "CommunicationService | None" = None,
    ) -> ActionResult:
        """Send questions to stakeholder."""

        if not communication_service:
            return ActionResult(
                action_type=self.action_type,
                summary="Communication service required",
                kind="failed_action",
                data={},
                success=False,
            )

        # Get stakeholder and manager from workflow
        stakeholder = workflow.stakeholder_agent
        if not stakeholder or not isinstance(stakeholder, ClarificationStakeholderAgent):
            return ActionResult(
                action_type=self.action_type,
                summary="No clarification stakeholder found on workflow",
                kind="failed_action",
                data={},
                success=False,
            )

        stakeholder_id = stakeholder.config.agent_id
        manager_id = workflow.metadata.get("decomposition_state", {}).get(
            "manager_id", "decomposition_manager"
        )

        # Send question
        message_ids = []
        try:
            # Include preference context in question
            full_question = self.question

            message = await communication_service.send_direct_message(
                from_agent=manager_id,
                to_agent=stakeholder_id,
                content=full_question,
                message_type=MessageType.REQUEST,
            )
            message_ids.append(str(message.message_id))

        except Exception as e:
            logger.error(f"Failed to send question: {e}")
            return ActionResult(
                action_type=self.action_type,
                summary=f"Send failed: {str(e)}",
                kind="failed_action",
                data={},
                success=False,
            )

        logger.info(f"Sent question to {stakeholder_id}")

        return ActionResult(
            action_type=self.action_type,
            summary="Sent question to stakeholder",
            kind="mutation",
            data={
                "question": self.question,
                "message_ids": message_ids,
            },
            success=True,
        )


class GeneratePreferenceRubricAction(BaseManagerAction):
    """Generate and broadcast evaluation rubric for a preference.

    Uses LLM to decompose preference + clarification context into structured rubric,
    then broadcasts to all workflow agents.
    """

    action_type: Literal["generate_preference_rubric"] = "generate_preference_rubric"
    preference_name: str = Field(description="Preference to generate rubric for")

    async def execute(
        self,
        workflow: "Workflow",
        communication_service: "CommunicationService | None" = None,
    ) -> ActionResult:
        """Generate rubric and broadcast to agents."""

        if not communication_service:
            return ActionResult(
                action_type=self.action_type,
                summary="Communication service required",
                kind="failed_action",
                data={},
                success=False,
            )

        # Get stakeholder and manager from workflow
        stakeholder = workflow.stakeholder_agent
        if not stakeholder or not isinstance(stakeholder, ClarificationStakeholderAgent):
            return ActionResult(
                action_type=self.action_type,
                summary="No clarification stakeholder found on workflow",
                kind="failed_action",
                data={},
                success=False,
            )

        stakeholder_id = stakeholder.config.agent_id
        manager_id = workflow.metadata.get("decomposition_state", {}).get(
            "manager_id", "decomposition_manager"
        )

        # Get clarification context
        communication_history = communication_service.get_conversation_history(
            agent_id=manager_id,
            other_agent=stakeholder_id,
            limit=1000,
        )

        # Generate rubric
        evaluator, rubric_spec = await decompose_preference_to_evaluator(
            workflow=workflow,
            stakeholder_manager_messages=communication_history,
            model_name="gpt-5",  # TODO: make this configurable
            seed=workflow.seed,
        )

        # Store rubric on clarification stakeholder for evaluation
        stakeholder.generated_rubrics.append(evaluator)
        logger.info(
            f"Added rubric '{evaluator.name}' to stakeholder.generated_rubrics "
            f"(total: {len(stakeholder.generated_rubrics)})"
        )

        # Broadcast rubric to all agents
        agent_ids = list(workflow.agents.keys())
        manager_id = workflow.metadata.get("decomposition_state", {}).get(
            "manager_id", "decomposition_manager"
        )

        await communication_service.send_multicast_message(
            from_agent=manager_id,
            to_agents=agent_ids,
            content=f"Rubric generated for the task. Here is the rubric: {rubric_spec.model_dump_json()}",
            message_type=MessageType.RUBRIC_UPDATE,
        )
        logger.info(f"Broadcast rubric to {len(agent_ids)} agents")

        return ActionResult(
            action_type=self.action_type,
            summary=f"Generated and broadcast rubric with {len(evaluator.criteria)} rules",
            kind="mutation",
            data={
                "preference_name": self.preference_name,
                "rules_count": len(evaluator.criteria),
                "rule_names": [r.name for r in evaluator.criteria],
                "rubric_spec": rubric_spec.model_dump(mode="json"),
            },
            success=True,
        )
