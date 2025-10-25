"""
Base class for rubric-guided execution phases.

Provides shared functionality for generating rubrics, creating workers with
rubric injection, and tracking all metadata required for GRPO training.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Union

from manager_agent_gym.core.common.logging import logger
from manager_agent_gym.core.agents.manager_agent.actions import (
    GeneratePreferenceRubricAction,
)
from manager_agent_gym.core.execution.schemas.state import ExecutionState
from manager_agent_gym.core.execution.schemas.pre_execution import (
    ClarificationTurn,
    DifficultyOfClarificationQuestions,
)
from manager_agent_gym.core.workflow.phases.interface import PreExecutionPhase
from manager_agent_gym.core.agents.manager_agent.implementations.rubric_generation_manager.rubric_generation import (
    ManagerAgentGeneratedStagedRubricWithMetadata,
    RubricGenerationMetadata,
)
from manager_agent_gym.schemas.domain.task_execution import TaskExecution
from manager_agent_gym.schemas.domain.base import TaskStatus
from manager_agent_gym.schemas.agents import AIAgentConfig
from manager_agent_gym.schemas.domain.communication import Message

if TYPE_CHECKING:
    from manager_agent_gym.schemas.domain.workflow import Workflow
    from manager_agent_gym.schemas.domain.task import Task
    from manager_agent_gym.core.communication.service import CommunicationService
    from manager_agent_gym.core.agents.manager_agent.implementations.rubric_generation_manager.rubric_decomposition_manager import (
        RubricDecompositionManagerAgent,
    )
    from manager_agent_gym.core.agents.stakeholder_agent.rubric_stakeholder import (
        ClarificationStakeholderAgent,
    )
    from manager_agent_gym.core.agents.workflow_agents.tools.registry import (
        AgentRegistry,
    )
    from manager_agent_gym.core.common.llm_generator import LLMGenerator


class RubricExecutionPhaseBase(PreExecutionPhase):
    """Shared logic for rubric-guided execution phases.

    Provides common functionality:
    - Rubric generation via manager-stakeholder dialogue
    - Worker creation with rubric injection
    - Metadata tracking (cost, cognitive burden, etc.)

    Subclasses implement specific execution strategies:
    - MultiRubricTrainingPhase: N synthetic + 1 ground truth (GRPO)
    - BestOfNBaseline: N workers with no rubric
    - GroundTruthRubricBaseline: 1 worker with ground truth
    - TrainedPolicyRubricBaseline: 1 worker with trained policy
    """

    def __init__(
        self,
        base_worker_config: AIAgentConfig,
        agent_registry: "AgentRegistry",
        rubric_manager: "RubricDecompositionManagerAgent",
        stakeholder: "ClarificationStakeholderAgent",
        communication_service: "CommunicationService",
        llm_generator: "LLMGenerator",
        additional_tools: list[Any] | None = None,
        max_turns: int = 5,
    ):
        """Initialize rubric execution phase.

        Args:
            base_worker_config: Base worker agent configuration
            agent_registry: Registry for creating agents
            rubric_manager: Manager agent for rubric generation
            stakeholder: Stakeholder agent for clarification
            communication_service: Service for manager-stakeholder dialogue
            llm_generator: LLM generator for structured outputs
            additional_tools: Tools to inject into worker agents
            max_turns: Maximum dialogue turns for rubric generation
        """
        self.base_worker_config = base_worker_config
        self.agent_registry = agent_registry
        self.rubric_manager = rubric_manager
        self.stakeholder = stakeholder
        self.communication_service = communication_service
        self.additional_tools = additional_tools
        self.max_turns = max_turns
        self.llm_generator = llm_generator

        # Wire up communication
        self.rubric_manager.set_communication_service(self.communication_service)
        self.stakeholder.communication_service = self.communication_service

    async def _generate_single_rubric(
        self,
        workflow: "Workflow",
        variant_index: int,
        seed: int | None = None,
    ) -> tuple[ManagerAgentGeneratedStagedRubricWithMetadata, RubricGenerationMetadata]:
        """Generate one STAGED rubric with full metadata tracking.

        Runs manager-stakeholder dialogue loop to generate a rubric, tracking
        LLM costs, cognitive burden of questions, and execution time.

        Args:
            workflow: Workflow context
            variant_index: Index of this variant (for logging)
            seed: Random seed for reproducibility

        Returns:
            Tuple of (rubric_with_metadata, standalone_metadata)
        """
        logger.info(
            f"🔄 Generating rubric variant {variant_index} "
            f"(seed={seed}, max_turns={self.max_turns})"
        )

        # Reset manager state for fresh generation
        self.rubric_manager.reset()
        if seed is not None:
            self.rubric_manager._seed = seed

        started_at = datetime.now()

        # Store manager_id in metadata for action execution
        if "decomposition_state" not in workflow.metadata:
            workflow.metadata["decomposition_state"] = {}
        workflow.metadata["decomposition_state"]["manager_id"] = (
            self.rubric_manager.agent_id
        )

        # Main dialogue loop
        rubric: ManagerAgentGeneratedStagedRubricWithMetadata | None = None

        for turn in range(self.max_turns):
            logger.info(
                f"📍 Rubric generation turn {turn + 1}/{self.max_turns} "
                f"(variant {variant_index})"
            )

            # 1. Stakeholder responds to pending questions
            await self.stakeholder.policy_step(
                current_timestep=turn,
                communication_service=self.communication_service,
            )

            # 2. Manager observes and acts
            observation = await self.rubric_manager.create_observation(
                workflow=workflow,
                execution_state=ExecutionState.INITIALIZED,
                current_timestep=turn,
            )

            action = await self.rubric_manager.take_action(observation)

            action_result = await action.execute(
                workflow=workflow,
                communication_service=self.communication_service,
                llm_generator=self.llm_generator,
            )

            # Track rubric generation (completion signal)
            if (
                isinstance(action, GeneratePreferenceRubricAction)
                and action_result.success
            ):
                pref_name = action_result.data.get("preference_name")
                rubric_spec_dict = action_result.data.get("rubric_spec")

                if pref_name and rubric_spec_dict:
                    logger.info(
                        f"✅ Rubric '{pref_name}' generated for variant {variant_index}"
                    )

                    # Create STAGED rubric and populate generation cost metadata
                    rubric = (
                        ManagerAgentGeneratedStagedRubricWithMetadata.model_validate(
                            rubric_spec_dict
                        )
                    )
                    rubric.metadata.generation_llm_cost_usd = (
                        self.rubric_manager.accumulated_llm_cost_usd
                    )
                    rubric.metadata.generation_llm_calls = (
                        self.rubric_manager.total_llm_calls
                    )
                    logger.info(
                        f"💰 Rubric generation cost: "
                        f"${rubric.metadata.generation_llm_cost_usd:.4f} "
                        f"({rubric.metadata.generation_llm_calls} LLM calls)"
                    )

                    # Analyze cognitive burden of clarification questions
                    clarification_turns = (
                        self._build_clarification_turns_from_messages()
                    )
                    if clarification_turns:
                        logger.info(
                            "🧠 Analyzing cognitive burden of clarification questions..."
                        )
                        cognitive_burden = await self._analyze_cognitive_burden(
                            clarification_turns=clarification_turns,
                            llm_generator=self.llm_generator,
                            seed=self.rubric_manager._seed,
                        )
                        rubric.metadata.cognitive_burden = cognitive_burden
                        logger.info(
                            f"📊 Cognitive burden: "
                            f"{cognitive_burden.number_of_easy_questions} easy, "
                            f"{cognitive_burden.number_of_medium_questions} medium, "
                            f"{cognitive_burden.number_of_hard_questions} hard"
                        )

                    # Update stakeholder's rubric with metadata-enriched version
                    if self.stakeholder.generated_rubrics:
                        from manager_agent_gym.core.agents.manager_agent.implementations.rubric_generation_manager.utils import (
                            convert_staged_rubric_to_executable,
                        )

                        enriched_evaluator = convert_staged_rubric_to_executable(rubric)
                        # Replace the last rubric (the one just added without metadata)
                        self.stakeholder.generated_rubrics[-1] = enriched_evaluator
                        logger.info(
                            f"✅ Updated stakeholder rubric with metadata: "
                            f"cost=${rubric.metadata.generation_llm_cost_usd}, "
                            f"calls={rubric.metadata.generation_llm_calls}"
                        )

                    break
        else:
            # Max turns reached without completion
            logger.warning(
                f"⚠️ Rubric generation variant {variant_index} reached max turns "
                f"({self.max_turns}) without completion"
            )

        # Create standalone metadata object
        completed_at = datetime.now()
        execution_time = (completed_at - started_at).total_seconds()

        if rubric is None:
            # Return empty STAGED rubric with failure metadata
            from manager_agent_gym.core.agents.manager_agent.implementations.rubric_generation_manager.rubric_generation import (
                EvaluationStageSpec,
                CodeRule,
            )

            rubric = ManagerAgentGeneratedStagedRubricWithMetadata(
                category_name="Failed Generation",
                rationale="Rubric generation failed to complete",
                max_total_score=1,
                stages=[
                    EvaluationStageSpec(
                        name="Placeholder Stage",
                        description="Generation failed",
                        is_required=False,
                        max_points=1.0,
                        min_score_to_pass=0.0,
                        on_failure_action="continue",
                        rules=[
                            CodeRule(
                                name="Placeholder",
                                description="Generation failed",
                                weight=0.0,
                                code="def evaluate(workflow, context): return 0.0",
                            )
                        ],
                    )
                ],
                metadata=RubricGenerationMetadata(),
            )

        # Create standalone metadata (copy from rubric)
        standalone_metadata = RubricGenerationMetadata(
            generation_llm_cost_usd=rubric.metadata.generation_llm_cost_usd,
            generation_llm_calls=rubric.metadata.generation_llm_calls,
            cognitive_burden=rubric.metadata.cognitive_burden,
            execution_wall_time_seconds=execution_time,
            execution_count=1,
        )

        return rubric, standalone_metadata

    def _build_clarification_turns_from_messages(self) -> list[ClarificationTurn]:
        """Extract and pair questions/responses from conversation history.

        Returns:
            List of ClarificationTurn objects with matched Q&A pairs
        """
        # Get full conversation between manager and stakeholder
        all_messages = self.communication_service.get_conversation_history(
            agent_id=self.rubric_manager.agent_id,
            other_agent=self.stakeholder.config.agent_id,
            limit=1000,
        )

        logger.info(f"Retrieved {len(all_messages)} messages from conversation history")

        # Separate questions (from manager) and responses (from stakeholder)
        questions = [
            msg for msg in all_messages if msg.sender_id == self.rubric_manager.agent_id
        ]
        responses = [
            msg
            for msg in all_messages
            if msg.sender_id == self.stakeholder.config.agent_id
        ]

        logger.info(f"Found {len(questions)} questions and {len(responses)} responses")

        # Build turns by pairing questions with their responses
        turns: list[ClarificationTurn] = []
        for turn_idx, question_msg in enumerate(questions):
            # Find first response after this question (chronological matching)
            matching_response = None
            response_msg_id = None

            for resp_msg in responses:
                if resp_msg.timestamp > question_msg.timestamp:
                    matching_response = resp_msg.content
                    response_msg_id = str(resp_msg.message_id)
                    # Remove from list so we don't match it again
                    responses = [
                        r for r in responses if r.message_id != resp_msg.message_id
                    ]
                    break

            turns.append(
                ClarificationTurn(
                    turn=turn_idx,
                    timestep=turn_idx,
                    manager_question=question_msg.content,
                    stakeholder_response=matching_response,
                    timestamp=question_msg.timestamp,
                    question_message_id=str(question_msg.message_id),
                    response_message_id=response_msg_id,
                )
            )

        return turns

    @staticmethod
    async def _analyze_cognitive_burden(
        clarification_turns: Union[list[ClarificationTurn], list[Message]],
        llm_generator: "LLMGenerator",
        seed: int = 42,
    ) -> DifficultyOfClarificationQuestions:
        """Analyze the cognitive burden of clarification questions using an LLM.

        Args:
            clarification_turns: List of clarification turns or messages
            llm_generator: LLM generator for structured outputs
            seed: Random seed for reproducibility

        Returns:
            DifficultyOfClarificationQuestions classification
        """
        if not clarification_turns:
            return DifficultyOfClarificationQuestions(
                reasoning="No clarification questions were asked.",
                number_of_easy_questions=0,
                number_of_medium_questions=0,
                number_of_hard_questions=0,
            )

        # Build conversation summary
        conversation_summary = []
        for turn in clarification_turns:
            # Handle both ClarificationTurn and Message types
            if isinstance(turn, ClarificationTurn):
                if turn.manager_question:
                    conversation_summary.append(
                        f"Manager asked: {turn.manager_question}"
                    )
                if turn.stakeholder_response:
                    conversation_summary.append(
                        f"Stakeholder responded: {turn.stakeholder_response}"
                    )
            else:
                # Handle Message objects
                conversation_summary.append(f"{turn.sender_id}: {turn.content}")

        system_prompt = """You are an expert at analyzing the cognitive burden of questions.
You will be shown a conversation between a manager agent and a stakeholder.
Your task is to identify ALL questions asked by the manager and classify each one by cognitive difficulty:

- **Easy**: Simple yes/no questions, factual recall, or straightforward preference statements
- **Medium**: Questions requiring comparison, explanation of reasoning, or moderate domain knowledge
- **Hard**: Questions requiring deep analysis, complex trade-off evaluation, or significant mental effort

Provide your reasoning and then count the total number of questions in each difficulty category."""

        user_prompt = f"""Analyze this manager-stakeholder conversation and classify ALL questions by difficulty:

{chr(10).join(conversation_summary)}

Count every distinct question the manager asked and classify them as easy, medium, or hard based on the cognitive burden they place on the stakeholder."""

        try:
            # Use Agents SDK approach
            from agents import Agent
            from agents.run import Runner

            agent = Agent(
                name="cognitive_burden_analyzer",
                model=llm_generator,
                instructions=system_prompt,
                output_type=DifficultyOfClarificationQuestions,
            )

            agent_result = await Runner.run(agent, user_prompt)
            result = agent_result.final_output
            return result  # type: ignore[return-value]
        except Exception as e:
            logger.warning(f"Failed to analyze cognitive burden: {e}")
            # Return fallback with all questions marked as medium difficulty
            total_turns = len(clarification_turns)
            return DifficultyOfClarificationQuestions(
                reasoning=f"Failed to analyze: {str(e)}. Marking all {total_turns} questions as medium difficulty.",
                number_of_easy_questions=0,
                number_of_medium_questions=total_turns,
                number_of_hard_questions=0,
            )

    def _create_worker_with_rubric(
        self,
        workflow: "Workflow",
        task: "Task",
        rubric: ManagerAgentGeneratedStagedRubricWithMetadata | None,
        rubric_type: str,
        variant_index: int,
        rubric_metadata: RubricGenerationMetadata,
        generation_seed: int | None = None,
    ) -> TaskExecution:
        """Create worker agent with rubric injected and return TaskExecution.

        Args:
            workflow: Workflow context
            task: Task to execute
            rubric: Generated rubric (or None for no-rubric baselines)
            rubric_type: Type label (e.g., "synthetic_v0", "ground_truth")
            variant_index: Index of this variant
            rubric_metadata: Generation metadata
            generation_seed: Seed used for rubric generation

        Returns:
            TaskExecution object tracking this worker's execution
        """
        agent_id = f"{self.base_worker_config.agent_id}__task_{task.id}__{rubric_type}_v{variant_index}"

        # Create TaskExecution with full metadata
        execution = TaskExecution(
            task_id=task.id,
            agent_id=agent_id,
            variant_index=variant_index,
            status=TaskStatus.PENDING,
            metadata={
                "rubric_type": rubric_type,
                "variant_index": variant_index,
                "generation_seed": generation_seed,
                "rubric_generation": rubric_metadata.model_dump(),
                "rubric_text": self._format_rubric_for_agent(rubric)
                if rubric
                else None,
            },
        )

        workflow.task_executions[execution.id] = execution
        task.execution_ids.append(execution.id)

        # Register agent with rubric in system prompt
        if rubric:
            agent_config = self._create_agent_config_with_rubric(
                agent_id, rubric, rubric_type
            )
        else:
            # No rubric injection (for baselines like best-of-N)
            agent_config = self.base_worker_config.model_copy()
            agent_config.agent_id = agent_id

        self.agent_registry.register_ai_agent(
            config=agent_config,
            additional_tools=self.additional_tools,  # type: ignore[arg-type]
        )

        logger.info(
            f"✅ Created worker '{agent_id}' for task '{task.name}' "
            f"(rubric_type={rubric_type}, variant={variant_index})"
        )

        return execution

    def _create_agent_config_with_rubric(
        self,
        agent_id: str,
        rubric: ManagerAgentGeneratedStagedRubricWithMetadata,
        rubric_type: str,
    ) -> AIAgentConfig:
        """Create agent config with rubric injected in system prompt.

        Args:
            agent_id: Unique agent ID
            rubric: Rubric to inject
            rubric_type: Type label for display

        Returns:
            Agent configuration with enhanced description
        """
        rubric_text = self._format_rubric_for_agent(rubric)

        enhanced_description = (
            f"{self.base_worker_config.agent_description}\n\n"
            f"EVALUATION CRITERIA ({rubric_type}):\n"
            f"{rubric_text}\n"
            f"Your work will be evaluated against these criteria."
        )

        config = self.base_worker_config.model_copy()
        config.agent_id = agent_id
        config.agent_description = enhanced_description
        return config

    def _format_rubric_for_agent(
        self, rubric: ManagerAgentGeneratedStagedRubricWithMetadata
    ) -> str:
        """Format STAGED rubric as readable text for agent prompt.

        Args:
            rubric: Rubric to format

        Returns:
            Formatted text representation with stages and gates
        """
        from manager_agent_gym.core.agents.manager_agent.utils.rubric_formatting import (
            format_staged_rubric_for_worker,
        )

        return format_staged_rubric_for_worker(rubric)

    async def run(self, workflow: "Workflow", llm_generator: "LLMGenerator") -> None:
        """Run pre-execution phase. Must be implemented by subclasses.

        Args:
            workflow: Workflow to prepare
            llm_generator: LLM generator for structured outputs
        """
        raise NotImplementedError("Subclasses must implement run()")
