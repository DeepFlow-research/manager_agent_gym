"""
Multi-rubric training phase for GRPO.

Generates N synthetic rubrics, creates N workers guided by those rubrics,
then evaluates ALL outputs with the ground truth rubric.
"""

from typing import TYPE_CHECKING, Any

from manager_agent_gym.core.common.logging import logger
from manager_agent_gym.core.workflow.phases.rubric_execution_base import (
    RubricExecutionPhaseBase,
)
from manager_agent_gym.core.agents.manager_agent.implementations.rubric_generation_manager.rubric_generation import (
    ManagerAgentGeneratedStagedRubricWithMetadata,
    RubricGenerationMetadata,
)
from manager_agent_gym.schemas.agents import AIAgentConfig
from manager_agent_gym.core.workflow.phases.parallel_rubric_generation import (
    generate_rubrics_parallel,
)

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


class MultiRubricTrainingPhase(RubricExecutionPhaseBase):
    """GRPO training phase: generates N synthetic rubrics, creates N workers.

    For each workflow run:
    - Generates N synthetic rubrics from policy with different seeds
    - Creates N workers, each guided by a different synthetic rubric
    - Stores ground truth rubric in workflow metadata for evaluation
    - ALL worker outputs evaluated with ground truth rubric (not their guiding rubrics)

    This enables GRPO-style training where:
    - Each worker is guided by a synthetic rubric during execution
    - ALL workers are evaluated with the SAME ground truth rubric
    - Advantage = GT_score(worker_i) - baseline measures rubric quality
    - Rubric generation costs and cognitive burden are regularization terms
    """

    def __init__(
        self,
        n_synthetic_rubrics: int,
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
        """Initialize multi-rubric training phase.

        Args:
            n_synthetic_rubrics: Number of synthetic rubrics to generate
            ground_truth_rubric: Ground truth STAGED rubric with metadata (from GDPEval)
            base_worker_config: Base configuration for worker agents
            agent_registry: Registry for creating agents
            rubric_manager: Manager for rubric generation
            stakeholder: Stakeholder for clarification
            communication_service: Service for manager-stakeholder dialogue
            additional_tools: Tools to inject into worker agents
            max_turns: Maximum dialogue turns per rubric generation
        """
        super().__init__(
            base_worker_config=base_worker_config,
            agent_registry=agent_registry,
            rubric_manager=rubric_manager,
            stakeholder=stakeholder,
            communication_service=communication_service,
            additional_tools=additional_tools,
            max_turns=max_turns,
            llm_generator=llm_generator,
        )
        self.n_synthetic = n_synthetic_rubrics
        self.gt_rubric = ground_truth_rubric

    async def run(self, workflow: "Workflow", llm_generator: "LLMGenerator") -> None:
        """Generate N synthetic rubrics and create N workers.

        Workflow:
        1. Generate N synthetic rubrics with different seeds
        2. Store ground truth rubric in workflow metadata (for evaluation)
        3. For each atomic task in workflow:
           - Create N workers, each guided by a synthetic rubric
           - Inject rubric into worker's system prompt
           - Store all metadata in TaskExecution

        Note: Ground truth rubric is NOT used to create a worker - it's only
        used for evaluation after all workers complete.

        Args:
            workflow: Workflow to prepare
        """
        logger.info("=" * 80)
        logger.info("🚀 Multi-Rubric Training Phase (GRPO) - PARALLEL")
        logger.info("=" * 80)
        logger.info(f"Synthetic rubrics to generate: {self.n_synthetic}")
        logger.info(f"Ground truth rubric: {self.gt_rubric.category_name}")
        logger.info(f"Max turns per rubric: {self.max_turns}")
        logger.info("Parallel execution: max 8 concurrent")
        logger.info("=" * 80)
        logger.info("")

        # Generate N synthetic rubrics IN PARALLEL using thread isolation
        logger.info(
            f"📝 Generating {self.n_synthetic} synthetic rubrics in parallel..."
        )

        base_seed = workflow.seed if workflow.seed else 42

        parallel_results = await generate_rubrics_parallel(
            n_variants=self.n_synthetic,
            workflow=workflow,
            rubric_manager=self.rubric_manager,
            stakeholder=self.stakeholder,
            communication_service=self.communication_service,
            llm_generator=self.llm_generator,
            max_turns=self.max_turns,
            max_concurrent=8,  # Rate limit to avoid API throttling
            base_seed=base_seed,
        )

        # Convert parallel results to expected format
        synthetic_rubrics_with_metadata: list[
            tuple[
                str,  # rubric_type
                ManagerAgentGeneratedStagedRubricWithMetadata,  # rubric (STAGED format with metadata)
                RubricGenerationMetadata,  # metadata
                int,  # variant_idx
                int | None,  # seed
            ]
        ] = []

        for i, (thread_id, rubric, metadata) in enumerate(parallel_results):
            variant_seed = base_seed + i
            synthetic_rubrics_with_metadata.append(
                (f"synthetic_v{i}", rubric, metadata, i, variant_seed)
            )

            logger.info(
                f"✅ Synthetic rubric {i + 1}/{len(parallel_results)} packaged: "
                f"'{rubric.category_name}' "
                f"(thread={thread_id}, seed={variant_seed})"
            )

        # Store ground truth rubric in workflow metadata for evaluation
        logger.info(
            f"📋 Storing ground truth rubric for evaluation: '{self.gt_rubric.category_name}'"
        )
        if "grpo_training" not in workflow.metadata:
            workflow.metadata["grpo_training"] = {}
        workflow.metadata["grpo_training"]["ground_truth_rubric"] = (
            self.gt_rubric.model_dump()
        )
        workflow.metadata["grpo_training"]["evaluation_mode"] = "ground_truth"

        # Convert ground truth STAGED rubric to executable format for ALL tasks
        from manager_agent_gym.core.agents.manager_agent.implementations.rubric_generation_manager.utils import (
            convert_staged_rubric_to_executable,
        )

        gt_rubric_evaluator = convert_staged_rubric_to_executable(self.gt_rubric)

        # Set ground truth evaluator on ALL atomic tasks
        for task in workflow.tasks.values():
            if task.is_atomic_task():
                # Override task evaluators with ground truth rubric
                task.completion_evaluators = [gt_rubric_evaluator]
                logger.info(
                    f"✓ Task '{task.name}' will be evaluated with ground truth rubric"
                )

        logger.info("")
        logger.info(
            f"✅ Total synthetic rubrics: {len(synthetic_rubrics_with_metadata)}"
        )
        logger.info(
            "✅ Ground truth rubric configured for evaluation (no worker created)"
        )
        logger.info("")

        # Store synthetic rubrics for later access (calibration analysis)
        self.synthetic_rubrics = [rubric for _, rubric, _, _, _ in synthetic_rubrics_with_metadata]
        logger.info(f"Stored {len(self.synthetic_rubrics)} synthetic rubrics for calibration")

        # Create workers ONLY for synthetic rubrics
        logger.info("👷 Creating workers for synthetic rubrics...")
        total_workers_created = 0

        for task in workflow.tasks.values():
            if not task.is_atomic_task():
                logger.debug(f"Skipping non-atomic task: {task.name}")
                continue

            logger.info(f"Task: '{task.name}' ({task.id})")

            for (
                rubric_type,
                rubric,
                metadata,
                variant_idx,
                seed,
            ) in synthetic_rubrics_with_metadata:
                execution = self._create_worker_with_rubric(
                    workflow=workflow,
                    task=task,
                    rubric=rubric,
                    rubric_type=rubric_type,
                    variant_index=variant_idx,
                    rubric_metadata=metadata,
                    generation_seed=seed,
                )
                total_workers_created += 1

                logger.info(
                    f"  ✓ Worker {variant_idx + 1}/{len(synthetic_rubrics_with_metadata)}: "
                    f"{execution.agent_id} (guided by {rubric_type})"
                )

        logger.info("")
        logger.info("=" * 80)
        logger.info("✅ Multi-Rubric Training Phase Complete")
        logger.info("=" * 80)
        logger.info(
            f"Total workers created: {total_workers_created} "
            f"({self.n_synthetic} synthetic per task)"
        )
        logger.info("Workers will be evaluated with ground truth rubric")
        logger.info("Ready for N-way parallel execution")
        logger.info("=" * 80)
        logger.info("")
