from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from agents import Agent, Runner, RunResult

from manager_agent_gym.schemas.agents.stakeholder import StakeholderConfig
from manager_agent_gym.schemas.domain import Task, Resource
from manager_agent_gym.core.execution.schemas.results import ExecutionResult
from manager_agent_gym.schemas.preferences.evaluator import PreferenceExemplar
from manager_agent_gym.core.agents.stakeholder_agent.interface import StakeholderBase
from manager_agent_gym.core.common.logging import logger

from manager_agent_gym.core.agents.stakeholder_agent.prompts import (
    build_clarification_system_prompt_with_exemplar,
    build_response_generation_prompt,
)
from manager_agent_gym.schemas.agents.stakeholder import (
    StakeholderPublicProfile,
)
from manager_agent_gym.schemas.preferences.evaluator import (
    Rubric,
    PairwiseExemplar,
)
from manager_agent_gym.schemas.preferences.evaluation import StagedRubric

if TYPE_CHECKING:
    from manager_agent_gym.core.communication.service import CommunicationService
    from manager_agent_gym.core.common.llm_generator import LLMGenerator


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
        llm_generator: "LLMGenerator",
        seed: int | None = 42,
    ):
        """Initialize clarification stakeholder for RL training.

        Args:
            config: Stakeholder configuration (role, persona, preferences)
            llm_generator: LLM generator (shared across workflow for training)
            seed: Random seed for reproducibility
        """

        # Validate preference data type before calling super
        if not isinstance(
            config.preference_data,
            (PreferenceExemplar, Rubric, PairwiseExemplar, StagedRubric),
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
        self.generated_rubrics: list[
            StagedRubric
        ] = []  # Populated with StagedRubric objects

        # Thread context for parallel rubric generation (None = backward compatible)
        self.current_thread_id: UUID | None = None

        # Create LLM agent for generating responses
        self._clarification_agent: Agent = Agent(
            model=llm_generator,  # Use our custom generator (shared across workflow)
            name=f"{self.config.agent_id}_clarification",
            instructions=build_clarification_system_prompt_with_exemplar(
                role=self.config.role,
                persona_description=self.config.persona_description,
                preference_data=self.preference_measure,
            ),
        )

    def set_thread_context(self, thread_id: UUID | None) -> None:
        """Set thread context for scoped operation.

        Args:
            thread_id: Thread ID to scope operations to, or None for global
        """
        self.current_thread_id = thread_id
        if thread_id:
            logger.debug(
                f"ClarificationStakeholderAgent: Set thread context to {thread_id}"
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

        If thread context is set, only processes messages from that thread.

        Args:
            current_timestep: Current simulation timestep
            communication_service: Service for reading/sending messages
        """
        logger.info(
            f"🔍 DEBUG: Stakeholder {self.config.agent_id} policy_step called at timestep {current_timestep}, thread_id={self.current_thread_id}"
        )

        comm = communication_service or self.communication_service
        if comm is None:
            logger.warning(
                f"{self.config.agent_id}: No communication service available"
            )
            return

        # 1. Get messages addressed to this stakeholder (thread-scoped if context set)
        try:
            if self.current_thread_id:
                # Thread-scoped: only get messages from current thread
                all_messages = comm.get_messages_in_thread(
                    thread_id=self.current_thread_id,
                    limit=50,
                )
                # Filter to messages addressed to this stakeholder
                # Check both direct messages (receiver_id) and multicast (recipients list)
                messages = [
                    msg
                    for msg in all_messages
                    if msg.receiver_id == self.config.agent_id  # Direct messages
                    or self.config.agent_id in msg.recipients  # Multicast messages
                    or msg.is_broadcast()  # Broadcast messages
                ]
                logger.info(
                    f"🔍 DEBUG: Stakeholder got {len(messages)} messages in thread {self.current_thread_id}"
                )
            else:
                # Global: get all messages for this agent (backward compatible)
                messages = comm.get_messages_for_agent(
                    agent_id=self.config.agent_id,
                    limit=50,  # Process up to 50 messages per timestep
                )
                logger.info(
                    f"🔍 DEBUG: Stakeholder got {len(messages)} messages (no thread context)"
                )
        except Exception as e:
            logger.error(f"Failed to get messages for {self.config.agent_id}: {e}")
            return

        logger.info(
            f"🔍 DEBUG: Stakeholder processing {len(messages)} messages, already responded to {len(self._responded_message_ids)} messages"
        )

        # 2. Process each message and generate responses
        for msg in messages:
            # Skip if we've already responded to this message
            if msg.message_id in self._responded_message_ids:
                logger.debug(
                    f"🔍 DEBUG: {self.config.agent_id}: Skipping message {msg.message_id} (already responded)"
                )
                continue

            # Only respond to messages from other agents (likely manager)
            if msg.sender_id == self.config.agent_id:
                logger.debug("🔍 DEBUG: Skipping message from self")
                continue

            logger.info(
                f"🔍 DEBUG: Stakeholder processing message {msg.message_id} from {msg.sender_id} (thread={msg.thread_id}, type={msg.message_type})"
            )
            logger.info(f"🔍 DEBUG: Message preview: {msg.content[:100]}...")

            try:
                # Generate response using LLM + exemplar context
                response = await self._generate_response_to_question(msg.content)

                # 3. Send response back to sender via communication service
                # Keep response in same thread if thread context is set
                await comm.send_direct_message(
                    from_agent=self.config.agent_id,
                    to_agent=msg.sender_id,
                    content=response,
                    thread_id=self.current_thread_id
                    or msg.thread_id,  # Preserve thread
                )

                # Mark as responded
                self._responded_message_ids.add(msg.message_id)

                logger.info(
                    f"🔍 DEBUG: {self.config.agent_id} responded to message {msg.message_id} from {msg.sender_id}"
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

        # Trigger validation with our generated rubrics using NEW staged evaluation
        await validation_engine.evaluate_timestep(
            workflow=workflow,
            timestep=timestep,
            staged_rubrics=self.generated_rubrics,
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
            "rubric_names": [r.category_name for r in self.generated_rubrics],
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
