"""
Baseline phases for validation/test runs.

Provides various baseline execution strategies:
- BestOfNBaseline: N workers with no rubric guidance
- GroundTruthRubricBaseline: 1 worker with ground truth rubric
- TrainedPolicyRubricBaseline: 1 worker with trained policy rubric
"""

from typing import TYPE_CHECKING, Any, Literal

from manager_agent_gym.core.common.logging import logger
from manager_agent_gym.core.workflow.phases.rubric_execution_base import (
    RubricExecutionPhaseBase,
)
from manager_agent_gym.core.agents.manager_agent.implementations.rubric_generation_manager.rubric_generation import (
    ManagerAgentGeneratedStagedRubricWithMetadata,
    RubricGenerationMetadata,
)
from manager_agent_gym.schemas.agents import AIAgentConfig
from manager_agent_gym.schemas.domain.task_execution import TaskExecution
from manager_agent_gym.schemas.domain.base import TaskStatus

if TYPE_CHECKING:
    from manager_agent_gym.schemas.domain.workflow import Workflow
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


BaselineType = Literal["best_of_n", "ground_truth", "trained_policy"]


class BestOfNBaseline(RubricExecutionPhaseBase):
    """Best-of-N baseline: no rubric guidance, just sample N times.

    Creates N worker variants with identical configuration (except agent_id).
    This baseline tests whether rubric guidance improves quality beyond
    simple sampling diversity.
    """

    def __init__(
        self,
        n: int,
        base_worker_config: AIAgentConfig,
        agent_registry: "AgentRegistry",
        rubric_manager: "RubricDecompositionManagerAgent",
        stakeholder: "ClarificationStakeholderAgent",
        communication_service: "CommunicationService",
        llm_generator: "LLMGenerator",
        additional_tools: list[Any] | None = None,
        max_turns: int = 5,
    ):
        """Initialize best-of-N baseline.

        Args:
            n: Number of worker variants to create
            base_worker_config: Base configuration for workers
            agent_registry: Registry for creating agents
            rubric_manager: Manager (unused but required by base class)
            stakeholder: Stakeholder (unused but required by base class)
            communication_service: Service (unused but required by base class)
            llm_generator: LLM generator (unused but required by base class)
            additional_tools: Tools to inject into workers
            max_turns: Max turns (unused but required by base class)
        """
        super().__init__(
            base_worker_config=base_worker_config,
            agent_registry=agent_registry,
            rubric_manager=rubric_manager,
            stakeholder=stakeholder,
            communication_service=communication_service,
            llm_generator=llm_generator,
            additional_tools=additional_tools,
            max_turns=max_turns,
        )
        self.n = n

    async def run(self, workflow: "Workflow", llm_generator: "LLMGenerator") -> None:
        """Create N workers with NO rubric guidance.

        Args:
            workflow: Workflow to prepare
            llm_generator: LLM generator (not used in this baseline)
        """
        logger.info("=" * 80)
        logger.info("🎲 Best-of-N Baseline")
        logger.info("=" * 80)
        logger.info(f"Number of variants: {self.n}")
        logger.info("Rubric guidance: None")
        logger.info("=" * 80)
        logger.info("")

        total_workers_created = 0

        for task in workflow.tasks.values():
            if not task.is_atomic_task():
                continue

            logger.info(f"Task: '{task.name}' ({task.id})")

            for i in range(self.n):
                agent_id = (
                    f"{self.base_worker_config.agent_id}__task_{task.id}__"
                    f"best_of_n_v{i}"
                )

                # Create TaskExecution with no rubric metadata
                execution = TaskExecution(
                    task_id=task.id,
                    agent_id=agent_id,
                    variant_index=i,
                    status=TaskStatus.PENDING,
                    metadata={
                        "baseline": "best_of_n",
                        "variant_index": i,
                        "rubric_type": "none",
                    },
                )

                workflow.task_executions[execution.id] = execution
                task.execution_ids.append(execution.id)

                # Register agent WITHOUT rubric injection
                config = self.base_worker_config.model_copy()
                config.agent_id = agent_id
                self.agent_registry.register_ai_agent(
                    config=config,
                    additional_tools=self.additional_tools,  # type: ignore[arg-type]
                )

                total_workers_created += 1
                logger.info(f"  ✓ Worker {i + 1}/{self.n}: {agent_id} (no rubric)")

        logger.info("")
        logger.info("=" * 80)
        logger.info("✅ Best-of-N Baseline Complete")
        logger.info("=" * 80)
        logger.info(f"Total workers created: {total_workers_created}")
        logger.info("=" * 80)
        logger.info("")


class GroundTruthRubricBaseline(RubricExecutionPhaseBase):
    """Ground truth baseline: 1 worker with GT rubric.

    Creates a single worker with the ground truth rubric injected.
    This baseline represents the best-case scenario where the rubric
    perfectly captures stakeholder preferences.
    """

    def __init__(
        self,
        ground_truth_rubric: ManagerAgentGeneratedStagedRubricWithMetadata,
        base_worker_config: AIAgentConfig,
        agent_registry: "AgentRegistry",
        rubric_manager: "RubricDecompositionManagerAgent",
        stakeholder: "ClarificationStakeholderAgent",
        communication_service: "CommunicationService",
        llm_generator: "LLMGenerator",
        additional_tools: list[Any] | None = None,
        max_turns: int = 5,
    ):
        """Initialize ground truth rubric baseline.

        Args:
            ground_truth_rubric: Ground truth rubric to use
            base_worker_config: Base configuration for worker
            agent_registry: Registry for creating agents
            rubric_manager: Manager (unused but required by base class)
            stakeholder: Stakeholder (unused but required by base class)
            communication_service: Service (unused but required by base class)
            llm_generator: LLM generator (unused but required by base class)
            additional_tools: Tools to inject into worker
            max_turns: Max turns (unused but required by base class)
        """
        super().__init__(
            base_worker_config=base_worker_config,
            agent_registry=agent_registry,
            rubric_manager=rubric_manager,
            stakeholder=stakeholder,
            communication_service=communication_service,
            llm_generator=llm_generator,
            additional_tools=additional_tools,
            max_turns=max_turns,
        )
        self.gt_rubric = ground_truth_rubric

    async def run(self, workflow: "Workflow", llm_generator: "LLMGenerator") -> None:
        """Create 1 worker with ground truth rubric.

        Args:
            workflow: Workflow to prepare
            llm_generator: LLM generator (not used in this baseline)
        """
        logger.info("=" * 80)
        logger.info("📋 Ground Truth Rubric Baseline")
        logger.info("=" * 80)
        logger.info(f"Rubric: '{self.gt_rubric.category_name}'")
        logger.info("Number of variants: 1")
        logger.info("=" * 80)
        logger.info("")

        gt_metadata = RubricGenerationMetadata()  # Defaults (no generation cost)
        total_workers_created = 0

        for task in workflow.tasks.values():
            if not task.is_atomic_task():
                continue

            logger.info(f"Task: '{task.name}' ({task.id})")

            execution = self._create_worker_with_rubric(
                workflow=workflow,
                task=task,
                rubric=self.gt_rubric,
                rubric_type="ground_truth",
                variant_index=0,
                rubric_metadata=gt_metadata,
            )

            total_workers_created += 1
            logger.info(f"  ✓ Worker: {execution.agent_id} (ground truth rubric)")

        logger.info("")
        logger.info("=" * 80)
        logger.info("✅ Ground Truth Rubric Baseline Complete")
        logger.info("=" * 80)
        logger.info(f"Total workers created: {total_workers_created}")
        logger.info("=" * 80)
        logger.info("")


class TrainedPolicyRubricBaseline(RubricExecutionPhaseBase):
    """Trained policy baseline: generate 1 synthetic rubric from trained model.

    Generates a single rubric using the trained policy, then creates one worker
    with that rubric injected. This baseline tests the trained policy's ability
    to generate useful rubrics.
    """

    async def run(self, workflow: "Workflow", llm_generator: "LLMGenerator") -> None:
        """Generate 1 synthetic rubric and create worker.

        Args:
            workflow: Workflow to prepare
            llm_generator: LLM generator for rubric generation
        """
        logger.info("=" * 80)
        logger.info("🤖 Trained Policy Rubric Baseline")
        logger.info("=" * 80)
        logger.info(f"Max turns for rubric generation: {self.max_turns}")
        logger.info("Number of variants: 1")
        logger.info("=" * 80)
        logger.info("")

        # Generate single rubric from trained policy
        logger.info("📝 Generating rubric from trained policy...")
        rubric, metadata = await self._generate_single_rubric(
            workflow=workflow,
            variant_index=0,
            seed=workflow.seed,
        )

        logger.info(
            f"✅ Rubric generated: '{rubric.category_name}' "
            f"(cost=${metadata.generation_llm_cost_usd if metadata.generation_llm_cost_usd != 'not_calculated' else 0:.4f}, "
            f"calls={metadata.generation_llm_calls})"
        )
        logger.info("")

        total_workers_created = 0

        for task in workflow.tasks.values():
            if not task.is_atomic_task():
                continue

            logger.info(f"Task: '{task.name}' ({task.id})")

            execution = self._create_worker_with_rubric(
                workflow=workflow,
                task=task,
                rubric=rubric,
                rubric_type="trained_policy",
                variant_index=0,
                rubric_metadata=metadata,
                generation_seed=workflow.seed,
            )

            total_workers_created += 1
            logger.info(f"  ✓ Worker: {execution.agent_id} (trained policy rubric)")

        logger.info("")
        logger.info("=" * 80)
        logger.info("✅ Trained Policy Rubric Baseline Complete")
        logger.info("=" * 80)
        logger.info(f"Total workers created: {total_workers_created}")
        logger.info("=" * 80)
        logger.info("")


def create_baseline_phase(
    baseline: BaselineType,
    base_worker_config: AIAgentConfig,
    agent_registry: "AgentRegistry",
    rubric_manager: "RubricDecompositionManagerAgent",
    stakeholder: "ClarificationStakeholderAgent",
    communication_service: "CommunicationService",
    llm_generator: "LLMGenerator",
    ground_truth_rubric: ManagerAgentGeneratedStagedRubricWithMetadata | None = None,
    n: int = 1,
    additional_tools: list[Any] | None = None,
    max_turns: int = 5,
) -> RubricExecutionPhaseBase:
    """Factory to create baseline phase by type.

    Args:
        baseline: Which baseline to run
        base_worker_config: Base configuration for workers
        agent_registry: Registry for creating agents
        rubric_manager: Manager for rubric generation
        stakeholder: Stakeholder for clarification
        communication_service: Service for dialogue
        llm_generator: LLM generator for structured outputs
        ground_truth_rubric: Required for "ground_truth" baseline
        n: Number of samples for "best_of_n"
        additional_tools: Tools to inject into workers
        max_turns: Maximum dialogue turns

    Returns:
        Appropriate baseline phase

    Raises:
        ValueError: If baseline type is unknown or required args missing
    """
    if baseline == "best_of_n":
        return BestOfNBaseline(
            n=n,
            base_worker_config=base_worker_config,
            agent_registry=agent_registry,
            rubric_manager=rubric_manager,
            stakeholder=stakeholder,
            communication_service=communication_service,
            llm_generator=llm_generator,
            additional_tools=additional_tools,
            max_turns=max_turns,
        )
    elif baseline == "ground_truth":
        if not ground_truth_rubric:
            raise ValueError("ground_truth_rubric required for ground_truth baseline")
        return GroundTruthRubricBaseline(
            ground_truth_rubric=ground_truth_rubric,
            base_worker_config=base_worker_config,
            agent_registry=agent_registry,
            rubric_manager=rubric_manager,
            stakeholder=stakeholder,
            communication_service=communication_service,
            llm_generator=llm_generator,
            additional_tools=additional_tools,
            max_turns=max_turns,
        )
    elif baseline == "trained_policy":
        return TrainedPolicyRubricBaseline(
            base_worker_config=base_worker_config,
            agent_registry=agent_registry,
            rubric_manager=rubric_manager,
            stakeholder=stakeholder,
            communication_service=communication_service,
            llm_generator=llm_generator,
            additional_tools=additional_tools,
            max_turns=max_turns,
        )
    else:
        raise ValueError(f"Unknown baseline: {baseline}")
