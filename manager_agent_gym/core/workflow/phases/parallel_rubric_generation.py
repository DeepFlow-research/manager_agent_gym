"""
Parallel rubric generation using thread-based isolation.

This module provides infrastructure for generating N rubric variants concurrently
using thread-scoped message isolation instead of duplicating services.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from manager_agent_gym.core.common.logging import logger
from manager_agent_gym.core.agents.manager_agent.actions import (
    GeneratePreferenceRubricAction,
)
from manager_agent_gym.core.agents.manager_agent.implementations.rubric_generation_manager.rubric_generation import (
    ManagerAgentGeneratedStagedRubricWithMetadata,
    RubricGenerationMetadata,
)
from manager_agent_gym.schemas.domain.communication import CommunicationThread
from manager_agent_gym.core.execution.schemas.state import ExecutionState

if TYPE_CHECKING:
    from manager_agent_gym.schemas.domain.workflow import Workflow
    from manager_agent_gym.core.communication.service import CommunicationService
    from manager_agent_gym.core.agents.manager_agent.implementations.rubric_generation_manager.rubric_decomposition_manager import (
        RubricDecompositionManagerAgent,
    )
    from manager_agent_gym.core.agents.stakeholder_agent.rubric_stakeholder import (
        ClarificationStakeholderAgent,
    )
    from manager_agent_gym.core.common.llm_generator import LLMGenerator


async def generate_rubrics_parallel(
    n_variants: int,
    workflow: Workflow,
    rubric_manager: RubricDecompositionManagerAgent,
    stakeholder: ClarificationStakeholderAgent,
    communication_service: CommunicationService,
    llm_generator: LLMGenerator,
    max_turns: int = 5,
    max_concurrent: int = 8,
    base_seed: int = 42,
) -> list[
    tuple[UUID, ManagerAgentGeneratedStagedRubricWithMetadata, RubricGenerationMetadata]
]:
    """Generate N rubric variants in parallel using thread isolation.

    This uses thread-scoped messaging to enable parallel generation without
    creating duplicate services. Each variant gets its own thread_id, ensuring
    complete message isolation.

    Args:
        n_variants: Number of rubrics to generate
        workflow: Workflow context (shared read-only)
        rubric_manager: Shared manager (operates across threads)
        stakeholder: Shared stakeholder (operates across threads)
        communication_service: Shared service (thread-isolated messages)
        llm_generator: LLM generator for structured outputs
        max_turns: Max clarification turns per variant
        max_concurrent: Max parallel generations (rate limiting for API)
        base_seed: Base seed (variants use base_seed + variant_idx)

    Returns:
        List of (thread_id, rubric_with_metadata, standalone_metadata) tuples
    """

    async def generate_variant(
        variant_idx: int,
        seed: int,
    ) -> tuple[
        UUID, ManagerAgentGeneratedStagedRubricWithMetadata, RubricGenerationMetadata
    ]:
        """Generate one variant in isolated thread."""

        # Create isolated thread
        thread_id = uuid4()
        thread = CommunicationThread(
            thread_id=thread_id,
            topic=f"Rubric Generation Variant {variant_idx}",
            participants={rubric_manager.agent_id, stakeholder.config.agent_id},
        )
        communication_service.graph.threads[thread_id] = thread

        logger.info(
            f"🔄 Generating variant {variant_idx} (seed={seed}, thread={thread_id})"
        )

        # Set thread context for both agents
        rubric_manager.set_thread_context(thread_id)
        stakeholder.set_thread_context(thread_id)

        # Reset manager state but keep thread context
        rubric_manager.reset()
        rubric_manager.current_thread_id = thread_id  # Preserve after reset
        rubric_manager._seed = seed

        # Store thread context in workflow metadata for action execution
        if "decomposition_state" not in workflow.metadata:
            workflow.metadata["decomposition_state"] = {}
        workflow.metadata["decomposition_state"]["thread_id"] = thread_id
        workflow.metadata["decomposition_state"]["manager_id"] = rubric_manager.agent_id

        started_at = datetime.now()

        # Dialogue loop (same as before, but thread-scoped)
        rubric: ManagerAgentGeneratedStagedRubricWithMetadata | None = None

        for turn in range(max_turns):
            logger.debug(
                f"📍 Rubric generation turn {turn + 1}/{max_turns} "
                f"(variant {variant_idx}, thread={thread_id})"
            )

            # Stakeholder responds (thread-scoped)
            await stakeholder.policy_step(
                current_timestep=turn,
                communication_service=communication_service,
            )

            # Manager acts (thread-scoped)
            observation = await rubric_manager.create_observation(
                workflow=workflow,
                execution_state=ExecutionState.INITIALIZED,
                current_timestep=turn,
            )

            action = await rubric_manager.take_action(observation)

            # Action executes in thread context
            action_result = await action.execute(
                workflow=workflow,
                communication_service=communication_service,
            )

            # Check for completion
            if (
                isinstance(action, GeneratePreferenceRubricAction)
                and action_result.success
            ):
                rubric_spec_dict = action_result.data.get("rubric_spec")
                rubric = ManagerAgentGeneratedStagedRubricWithMetadata.model_validate(
                    rubric_spec_dict
                )
                rubric.metadata.generation_llm_cost_usd = (
                    rubric_manager.accumulated_llm_cost_usd
                )
                rubric.metadata.generation_llm_calls = rubric_manager.total_llm_calls

                logger.info(
                    f"✅ Variant {variant_idx} complete: "
                    f"'{rubric.category_name}' "
                    f"(cost=${rubric.metadata.generation_llm_cost_usd:.4f}, "
                    f"calls={rubric.metadata.generation_llm_calls})"
                )

                break

        if rubric is None:
            raise RuntimeError(
                f"Variant {variant_idx} failed to generate rubric in {max_turns} turns"
            )

        # Analyze cognitive burden (similar to _generate_single_rubric)
        # Get thread-scoped messages
        clarification_turns = communication_service.get_messages_in_thread(
            thread_id=thread_id
        )

        # Compute cognitive burden if available
        cognitive_burden: Any = "not_calculated"
        if clarification_turns:
            try:
                from manager_agent_gym.core.workflow.phases.rubric_execution_base import (
                    RubricExecutionPhaseBase,
                )

                cognitive_burden_result = (
                    await RubricExecutionPhaseBase._analyze_cognitive_burden(
                        clarification_turns=clarification_turns,
                        llm_generator=llm_generator,
                        seed=seed,
                    )
                )
                rubric.metadata.cognitive_burden = cognitive_burden_result
                cognitive_burden = cognitive_burden_result
                logger.info(
                    f"📊 Cognitive burden (variant {variant_idx}): "
                    f"{cognitive_burden_result.number_of_easy_questions} easy, "
                    f"{cognitive_burden_result.number_of_medium_questions} medium, "
                    f"{cognitive_burden_result.number_of_hard_questions} hard"
                )
            except Exception as e:
                logger.warning(f"Failed to analyze cognitive burden: {e}")

        # Create standalone metadata object
        metadata = RubricGenerationMetadata(
            generation_llm_cost_usd=rubric.metadata.generation_llm_cost_usd,
            generation_llm_calls=rubric.metadata.generation_llm_calls,
            cognitive_burden=cognitive_burden,
        )

        # Clear thread context
        rubric_manager.set_thread_context(None)
        stakeholder.set_thread_context(None)

        # Clean up thread from workflow metadata
        if "decomposition_state" in workflow.metadata:
            workflow.metadata["decomposition_state"].pop("thread_id", None)

        return (thread_id, rubric, metadata)

    # Execute with rate limiting
    semaphore = asyncio.Semaphore(max_concurrent)

    async def rate_limited_generate(idx: int, seed: int):
        async with semaphore:
            return await generate_variant(idx, seed)

    # Launch all variants in parallel
    tasks = [rate_limited_generate(i, base_seed + i) for i in range(n_variants)]

    logger.info(
        f"🚀 Launching {n_variants} parallel rubric generations "
        f"(max {max_concurrent} concurrent)"
    )

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Handle failures
    successful_results: list[
        tuple[
            UUID,
            ManagerAgentGeneratedStagedRubricWithMetadata,
            RubricGenerationMetadata,
        ]
    ] = []
    failed_count = 0
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Variant {i} failed: {result}", exc_info=result)
            failed_count += 1
        else:
            # Type guard: result is the tuple we expect
            successful_results.append(result)  # type: ignore[arg-type]

    logger.info(
        f"✅ Parallel generation complete: "
        f"{len(successful_results)}/{n_variants} successful, "
        f"{failed_count} failed"
    )

    return successful_results  # type: ignore[return-value]
