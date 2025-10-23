from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from agents import Agent, Runner, RunResult
from agents.extensions.models.litellm_model import LitellmModel

from manager_agent_gym.schemas.agents.stakeholder import StakeholderConfig
from manager_agent_gym.schemas.domain import Task, Resource
from manager_agent_gym.core.execution.schemas.results import ExecutionResult
from manager_agent_gym.schemas.preferences.evaluator import PreferenceExemplar
from manager_agent_gym.core.agents.stakeholder_agent.interface import StakeholderBase
from manager_agent_gym.core.common.logging import logger
from manager_agent_gym.core.common.llm_interface import build_litellm_model_id

from manager_agent_gym.core.agents.stakeholder_agent.prompts import (
    build_clarification_system_prompt_with_exemplar,
    build_response_generation_prompt,
)
from manager_agent_gym.schemas.agents.stakeholder import (
    StakeholderPublicProfile,
)
from manager_agent_gym.schemas.preferences.rubric import RunCondition
from manager_agent_gym.schemas.preferences.evaluator import (
    Rubric,
    PairwiseExemplar,
)

if TYPE_CHECKING:
    from manager_agent_gym.core.communication.service import CommunicationService


class ClarificationStakeholderAgent(StakeholderBase):
    """Communication-driven stakeholder for RL training of clarification dialogue.

    This agent is designed for training manager agents to ask effective clarification
    questions. It uses an exemplar output (representing ideal task completion) to
    inform realistic, human-like responses to manager questions.

    Key characteristics:
    - Communication-driven: responds to messages at each timestep via policy_step()
    - Uses exemplar output as ground truth for what "good" looks like
    - Provides human-realistic answers to help manager scope projects effectively
    - Simplified interface: minimal task execution, focus on dialogue

    Usage in RL Pipeline:
    - Exemplar output encapsulates the stakeholder's utility function maximization
    - Manager learns to ask questions that elicit the information needed to recreate
      the exemplar quality through better understanding of stakeholder preferences
    """

    def __init__(
        self,
        config: StakeholderConfig,
        seed: int | None = 42,
    ):
        """Initialize clarification stakeholder for RL training.

        Args:
            config: Stakeholder configuration (role, persona, preferences)
            seed: Random seed for reproducibility
        """

        # Validate preference data type before calling super
        if not isinstance(
            config.preference_data, (PreferenceExemplar, Rubric, PairwiseExemplar)
        ):
            raise ValueError(
                "ClarificationStakeholderAgent requires PreferenceMeasure "
                "(PreferenceExemplar, Rubric, or PairwiseExemplar) preference data"
            )

        self._preference_data = config.preference_data
        super().__init__(config)

        # Store preference measure (ground truth for "good" work)
        self.preference_measure = self._preference_data

        # Track messages we've already responded to (avoid duplicates)
        self._responded_message_ids: set[UUID] = set()

        # Generated rubrics (populated during pre-execution phase)
        self.generated_rubrics: list = []  # Will be list[Rubric] once populated

        # Create LLM agent for generating responses
        self._clarification_agent: Agent = Agent(
            model=LitellmModel(model=build_litellm_model_id(self.config.model_name)),
            name=f"{self.config.agent_id}_clarification",
            instructions=build_clarification_system_prompt_with_exemplar(
                role=self.config.role,
                persona_description=self.config.persona_description,
                preference_data=self.preference_measure,
            ),
        )

    async def policy_step(
        self,
        current_timestep: int,
        communication_service: "CommunicationService | None" = None,
    ) -> None:
        """Run one policy tick: check for manager questions and respond.

        This is the main control flow for the clarification stakeholder:
        1. Check communication service for new messages from manager
        2. Generate human-realistic responses using exemplar context
        3. Send responses back via communication service

        Args:
            current_timestep: Current simulation timestep
            communication_service: Service for reading/sending messages
        """
        comm = communication_service or self.communication_service
        if comm is None:
            logger.warning(
                f"{self.config.agent_id}: No communication service available"
            )
            return

        # 1. Get messages addressed to this stakeholder
        try:
            messages = comm.get_messages_for_agent(
                agent_id=self.config.agent_id,
                limit=50,  # Process up to 50 messages per timestep
            )
        except Exception as e:
            logger.error(f"Failed to get messages for {self.config.agent_id}: {e}")
            return

        # 2. Process each message and generate responses
        for msg in messages:
            # Skip if we've already responded to this message
            if msg.message_id in self._responded_message_ids:
                logger.debug(
                    f"{self.config.agent_id}: Skipping message {msg.message_id} because we've already responded"
                )
                continue

            # Only respond to messages from other agents (likely manager)
            if msg.sender_id == self.config.agent_id:
                continue

            try:
                # Generate response using LLM + exemplar context
                response = await self._generate_response_to_question(msg.content)

                # 3. Send response back to sender via communication service
                await comm.send_direct_message(
                    from_agent=self.config.agent_id,
                    to_agent=msg.sender_id,
                    content=response,
                )

                # Mark as responded
                self._responded_message_ids.add(msg.message_id)

                logger.debug(
                    f"{self.config.agent_id} responded to message from {msg.sender_id} "
                    f"(Q: {msg.content[:50]}...)"
                )

            except Exception as e:
                logger.error(
                    f"Failed to respond to message {msg.message_id} for {self.config.agent_id}: {e}",
                    exc_info=True,
                )
                # Mark as responded even on error to avoid infinite retry loops
                self._responded_message_ids.add(msg.message_id)

    async def _generate_response_to_question(self, question: str) -> str:
        """Generate a human-realistic response to a clarification question.

        Uses the LLM with exemplar context to produce responses that guide
        the manager toward understanding what "good" looks like.

        Args:
            question: Question from manager agent

        Returns:
            Response string with clarification details
        """
        # Build user prompt with the question
        user_prompt = build_response_generation_prompt(question)

        try:
            # Use LLM agent to generate response
            run_result: RunResult = await Runner.run(
                self._clarification_agent,
                user_prompt,
            )

            # Extract text from output
            output = run_result.final_output
            if isinstance(output, str):
                return output
            return getattr(output, "text", str(output))

        except Exception as e:
            logger.error(
                f"Response generation failed for {self.config.agent_id}: {e}",
                exc_info=True,
            )
            return (
                "I'm unable to provide a clear answer at this time. "
                "Could you rephrase your question or provide more context?"
            )

    # ============================================================================
    # INTERFACE IMPLEMENTATION: New hooks-based interface
    # ============================================================================

    def _build_public_profile(self):
        """Build public profile with exemplar-based summary."""
        return StakeholderPublicProfile(
            display_name=self.config.name,
            role=self.config.role,
            preference_summary=self._preference_data.get_preference_summary(),
        )

    async def evaluate_for_timestep(
        self,
        timestep: int,
        validation_engine,
        workflow,
        communications,
        manager_actions,
    ) -> None:
        """Evaluate using generated rubrics."""
        if not self.generated_rubrics:
            logger.warning(
                f"{self.config.agent_id}: No rubrics generated yet, skipping evaluation at timestep {timestep}"
            )
            return

        # Trigger validation with our generated rubrics
        await validation_engine.evaluate_timestep(
            workflow=workflow,
            timestep=timestep,
            preferences=None,  # No traditional preferences!
            workflow_evaluators=self.generated_rubrics,  # Use our rubrics instead
            cadence=RunCondition.EACH_TIMESTEP,
            communications=communications,
            manager_actions=manager_actions,
        )

    def get_serializable_state(self, timestep: int) -> dict:
        """Serialize preference measure state for logging."""
        return {
            "type": "clarification",
            "timestep": timestep,
            "preference_measure_summary": self.preference_measure.get_preference_summary(),
            "rubric_count": len(self.generated_rubrics),
            "rubric_names": [r.name for r in self.generated_rubrics],
        }

    def restore_from_state(self, state_dict: dict) -> None:
        """Restore exemplar state from checkpoint."""
        if state_dict.get("type") != "exemplar":
            raise ValueError("Invalid state type for ClarificationStakeholderAgent")

        # Exemplar stakeholder state is mostly static
        # Rubrics would need to be restored from workflow metadata if needed
        logger.info(
            f"Restored clarification stakeholder with {state_dict.get('rubric_count', 0)} rubrics"
        )

    # ============================================================================
    # Task Execution (Not used by clarification stakeholder)
    # ============================================================================

    async def execute_task(
        self, task: Task, resources: list[Resource]
    ) -> ExecutionResult:
        """Clarification stakeholder doesn't execute tasks.

        This agent is focused on communication/clarification dialogue only.
        """
        logger.debug(
            f"{self.config.agent_id}: execute_task called (not supported for clarification stakeholder)"
        )
        raise NotImplementedError("Clarification stakeholder does not execute tasks")
