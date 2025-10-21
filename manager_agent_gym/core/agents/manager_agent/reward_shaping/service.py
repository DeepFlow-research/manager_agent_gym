"""
Rubric decomposition service.

Converts natural language preferences into structured evaluation rubrics
using LLM-based decomposition with optional stakeholder clarification.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from manager_agent_gym.core.agents.manager_agent.implementations.rubric_generation_manager.rubric_generation import (
    ManagerAgentGeneratedRubric,
)
from manager_agent_gym.core.agents.manager_agent.implementations.rubric_generation_manager.utils import (
    convert_to_evaluator,
)
from manager_agent_gym.schemas.preferences.evaluator import Rubric
from manager_agent_gym.core.common.llm_interface import generate_structured_response
from manager_agent_gym.core.common.logging import logger
from manager_agent_gym.core.agents.manager_agent.prompts.rubric_generation import (
    build_decomposer_system_prompt,
    build_decomposer_user_prompt,
)

if TYPE_CHECKING:
    from manager_agent_gym.schemas.domain.workflow import Workflow
    from manager_agent_gym.schemas.domain.communication import Message


async def decompose_preference_to_evaluator(
    workflow: Workflow,
    stakeholder_manager_messages: list[Message],
    model_name: str,
    seed: int,
) -> tuple[Rubric, ManagerAgentGeneratedRubric]:
    """Convert natural language preference → structured Evaluator.

    Pipeline:
    1. LLM generates RubricGenerationSpec (strings only, LLM-friendly)
    2. Convert to WorkflowRubric objects (compile code, etc.)
    3. Package into Evaluator

    Args:
        preference: Preference object with name + description
        clarification_context: Q&A pairs from prior clarifications
        model_name: LLM to use for generation
        seed: Random seed for reproducibility

    Returns:
        Tuple of (Evaluator with executable rubrics, Raw RubricGenerationSpec for logging)

    Raises:
        Exception: If LLM generation or code compilation fails
    """
    logger.info(
        f"Decomposing preference with {len(stakeholder_manager_messages)} stakeholder-manager messages"
    )

    # Build prompt
    system_prompt = build_decomposer_system_prompt()
    user_prompt = build_decomposer_user_prompt(
        task_summary=workflow.workflow_goal,
        stakeholder_manager_messages=stakeholder_manager_messages,
    )

    # LLM generates RubricGenerationSpec (pure data, strings only)
    rubric_spec: ManagerAgentGeneratedRubric = await generate_structured_response(
        model=model_name,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        response_type=ManagerAgentGeneratedRubric,
        temperature=1.0,
        seed=seed,
    )

    # Convert to executable Evaluator (compiles code, etc.)
    evaluator = convert_to_evaluator(
        spec=rubric_spec,
        preference_name=rubric_spec.rubric_id,
    )

    logger.info(
        f"Converted to Evaluator with {len(evaluator.criteria)} rubrics for '{rubric_spec.rubric_id}'"
    )

    return evaluator, rubric_spec
