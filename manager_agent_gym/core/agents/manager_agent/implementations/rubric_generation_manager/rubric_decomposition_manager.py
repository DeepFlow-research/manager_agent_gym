"""
Rubric Decomposition Manager Agent.

Specialized manager for pre-execution phase that generates evaluation rubrics
through stakeholder clarification dialogue.
"""

import traceback
from typing import TYPE_CHECKING, cast
from collections import defaultdict

from manager_agent_gym.core.agents.manager_agent.implementations.chain_of_thought import (
    ChainOfThoughtManagerAgent,
)
from manager_agent_gym.core.agents.manager_agent.common.llm_action_utils import (
    get_action_descriptions,
)
from manager_agent_gym.core.agents.manager_agent.actions import (
    BaseManagerAction,
    AskClarificationQuestionsAction,
    GeneratePreferenceRubricAction,
)
from manager_agent_gym.core.common.logging import logger
from manager_agent_gym.core.common.llm_interface import (
    LLMInferenceTruncationError,
    generate_structured_response,
    StructuredLLMResponse,
    calculate_llm_cost,
)
from manager_agent_gym.core.agents.manager_agent.common.action_constraints import (
    build_context_constrained_action_schema,
)
from manager_agent_gym.core.agents.manager_agent.actions import (
    FailedAction,
)
from manager_agent_gym.core.agents.manager_agent.prompts.rubric_decomposition import (
    RUBRIC_DECOMPOSITION_SYSTEM_PROMPT,
)
from manager_agent_gym.schemas.manager import ManagerObservation

if TYPE_CHECKING:
    from manager_agent_gym.core.communication.service import CommunicationService
    from manager_agent_gym.schemas.domain.communication import Message


class RubricDecompositionManagerAgent(ChainOfThoughtManagerAgent):
    """Manager agent specialized for rubric decomposition pre-execution phase.

    This agent operates before the main workflow execution to:
    1. Discover evaluation criteria from workflow environment
    2. Ask clarification questions to stakeholder about what matters
    3. Generate evaluation rubrics based on clarifications
    4. Signal completion when all rubrics are ready

    It uses a restricted action set focused on decomposition tasks.

    NOTE: This agent does NOT receive preferences upfront - it must discover
    what needs to be evaluated by examining the workflow environment.
    """

    def __init__(
        self,
        model_name: str = "gpt-4o",
        max_clarification_budget: int = 1,
        seed: int = 42,
    ):
        """Initialize rubric decomposition manager.

        Args:
            model_name: LLM model for decision-making
            max_clarification_budget: Maximum clarification TURNS allowed (not individual questions)
            seed: Random seed for reproducibility

        Note:
            Preferences are NOT passed to this manager. It discovers what to evaluate
            from the workflow environment (tasks, resources, descriptions, etc.)
        """
        # Define decomposition-specific action set

        decomposition_actions: list[type[BaseManagerAction]] = cast(
            list[type[BaseManagerAction]],
            [
                AskClarificationQuestionsAction,
                GeneratePreferenceRubricAction,
            ],
        )

        super().__init__(
            preferences=None,  # No preferences - discovery-based!
            model_name=model_name,
            action_classes=decomposition_actions,
            manager_persona="Rubric Decomposition Specialist",
        )

        self.max_clarification_budget = max_clarification_budget
        self.current_clarification_budget = 0
        self.configure_seed(seed)

        # Track processed messages to avoid duplication
        self._processed_message_ids: set[str] = set()

        # Track LLM costs for rubric generation
        self.accumulated_llm_cost_usd: float = 0.0
        self.total_llm_calls: int = 0

        logger.info(
            f"Initialized RubricDecompositionManagerAgent (discovery mode), "
            f"budget={max_clarification_budget}, model={model_name}"
        )

    def _read_stakeholder_messages(
        self, communication_service: "CommunicationService"
    ) -> dict[str, list["Message"]]:
        """Read messages from communication service and group by sender.

        Returns:
            Dict mapping sender_id -> list of messages
        """
        try:
            all_messages = communication_service.get_messages_for_agent(
                agent_id="decomposition_manager",
                limit=100,
            )

            # Group by sender, filter out already processed
            messages_by_sender = defaultdict(list)
            for msg in all_messages:
                if str(msg.message_id) not in self._processed_message_ids:
                    messages_by_sender[msg.sender_id].append(msg)
                    self._processed_message_ids.add(str(msg.message_id))

            return dict(messages_by_sender)

        except Exception as e:
            logger.error(f"Failed to read messages: {e}")
            return {}

    def _prepare_context(self, observation: "ManagerObservation") -> str:
        """Prepare context for decomposition manager with stakeholder messages."""
        context_parts: list[str] = []

        # 1. Decomposition state
        context_parts.append("## Decomposition State")
        context_parts.append(f"Timestep: {observation.timestep}")

        # Add explicit budget warning if exhausted
        if self.current_clarification_budget >= self.max_clarification_budget:
            context_parts.append("")
            context_parts.append("⚠️ **CLARIFICATION BUDGET EXHAUSTED**")
            context_parts.append(
                "You MUST now generate preference rubrics. You CANNOT ask more clarification questions."
            )
            context_parts.append(
                "Use the information gathered from previous stakeholder responses to create evaluation criteria."
            )

        context_parts.append("")

        # 2. Stakeholder responses (if any)
        if self.communication_service:
            messages_by_sender = self._read_stakeholder_messages(
                self.communication_service
            )

            if messages_by_sender:
                context_parts.append("## Stakeholder Responses")
                for sender_id, messages in messages_by_sender.items():
                    context_parts.append(f"\nFrom {sender_id}:")
                    for msg in messages:
                        context_parts.append(f"  - {msg.content}")
                context_parts.append("")

        # 3. Workflow environment
        context_parts.append("## Workflow Environment")
        context_parts.append(observation.workflow_summary)
        context_parts.append(f"Tasks: {observation.task_status_counts}")
        context_parts.append("")

        # 4. Instructions
        context_parts.append("## Your Task")
        context_parts.append(
            "Generate evaluation rubrics through clarification dialogue:"
        )
        context_parts.append(
            "1. Ask clarification questions to understand evaluation criteria"
        )
        context_parts.append("2. Generate rubrics based on stakeholder responses")
        context_parts.append("3. Signal completion when all rubrics are ready")
        context_parts.append("")

        # 5. Available actions
        context_parts.append("## Available Actions")
        action_descriptions = get_action_descriptions(self.action_classes)
        for action_type, description in action_descriptions.items():
            context_parts.append(f"- {action_type}: {description}")
        context_parts.append("")

        return "\n".join(context_parts)

    def reset(self) -> None:
        """Reset manager state for new decomposition phase."""
        super().reset()
        self._processed_message_ids.clear()
        self.current_clarification_budget = 0
        self.accumulated_llm_cost_usd = 0.0
        self.total_llm_calls = 0
        logger.debug("RubricDecompositionManagerAgent reset")

    async def take_action(self, observation: ManagerObservation) -> BaseManagerAction:
        """
        Take an action based on workflow observation using constrained generation.

        Args:
            observation: Current workflow state

        Returns:
            Validated BaseManagerAction

        Raises:
            ValueError: If LLM generates invalid action
        """
        try:
            # Check budget to constrain available actions
            action_classes: list[type[BaseManagerAction]] = (
                self.action_classes
                if self.current_clarification_budget < self.max_clarification_budget
                else [GeneratePreferenceRubricAction]
            )

            # Build constrained schema for LLM using current valid IDs
            constrained_schema = build_context_constrained_action_schema(
                action_classes, observation
            )
            # Prepare context using prompt templates
            system_prompt = RUBRIC_DECOMPOSITION_SYSTEM_PROMPT
            user_prompt = self._prepare_context(observation)

            # Direct LLM call with structured output (validated by Pydantic)
            response = await generate_structured_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_type=constrained_schema,
                model=self.model_name,
                seed=self._seed,
                return_usage=True,  # Track token usage for cost calculation
            )

            # Extract result and calculate cost
            if isinstance(response, StructuredLLMResponse):
                parsed_action = response.result
                if response.usage:
                    cost = calculate_llm_cost(response.usage, self.model_name)
                    self.accumulated_llm_cost_usd += cost
                    self.total_llm_calls += 1
                    logger.debug(
                        f"LLM call cost: ${cost:.4f} (total: ${self.accumulated_llm_cost_usd:.4f}, calls: {self.total_llm_calls})"
                    )
            else:
                # Fallback if return_usage=False
                parsed_action = response

            action = parsed_action.action  # type: ignore[attr-defined]

            # Increment budget by 1 per turn (not per question)
            if isinstance(action, AskClarificationQuestionsAction):
                self.current_clarification_budget += 1
                logger.info(
                    f"Clarification turn {self.current_clarification_budget}/{self.max_clarification_budget}"
                )

            return action

        except LLMInferenceTruncationError as e:
            concise_reason = (
                (e.provider_fields.get("refusal_text") or "").strip()
                or (e.provider_fields.get("finish_reason") or "").strip()
                or "provider refusal"
            )
            failed_action = FailedAction(
                reasoning=f"Provider refusal: {concise_reason}. Observing without action this step.",
                metadata={
                    "refusal_text": e.refusal_text,
                    "finish_reason": e.finish_reason,
                },
                success=False,
                result_summary=f"Provider refusal: {concise_reason}. Observing without action this step.",
            )
            logger.warning(
                "LLM refusal when generating manager action; falling back to FailedAction: %s",
                str(e),
            )
            return failed_action

        except Exception as e:
            logger.error(f"Structured manager failed: {traceback.format_exc()}")
            return FailedAction(
                reasoning=f"Structured manager failed to take action: {traceback.format_exc()}",
                metadata={"error": str(e)},
                success=False,
                result_summary=f"Structured manager failed to take action: {traceback.format_exc()}",
            )
