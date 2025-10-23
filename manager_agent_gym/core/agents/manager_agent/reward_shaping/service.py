"""
Rubric decomposition service.

Converts natural language preferences into structured evaluation rubrics
using LLM-based decomposition with optional stakeholder clarification.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from manager_agent_gym.core.agents.manager_agent.implementations.rubric_generation_manager.rubric_generation import (
    ManagerAgentGeneratedStagedRubric,
)
from manager_agent_gym.core.agents.manager_agent.implementations.rubric_generation_manager.utils import (
    convert_staged_rubric_to_executable,
)
from manager_agent_gym.schemas.preferences.evaluation import StagedRubric
from manager_agent_gym.core.common.llm_interface import generate_structured_response
from manager_agent_gym.core.common.logging import logger

# Import staged rubric system prompt (best practices from GDPEval)
from manager_agent_gym.core.agents.manager_agent.prompts.rubric_decomposition import (
    STAGED_RUBRIC_SYSTEM_PROMPT,
)

if TYPE_CHECKING:
    from manager_agent_gym.schemas.domain.workflow import Workflow
    from manager_agent_gym.schemas.domain.communication import Message


async def decompose_preference_to_evaluator(
    workflow: Workflow,
    stakeholder_manager_messages: list[Message],
    model_name: str,
    seed: int,
) -> tuple[StagedRubric, ManagerAgentGeneratedStagedRubric]:
    """Convert natural language preference → structured STAGED rubric.

    Pipeline:
    1. LLM generates ManagerAgentGeneratedStagedRubric (with stages, gates, rules)
    2. Convert to executable StagedRubric (compile code, prepare for evaluation)

    This now generates STAGED rubrics matching the GDPEval format, enabling:
    - Sequential evaluation with gates
    - Failure actions (skip_remaining, zero_category, continue)
    - Compatibility with gold GDPEval rubrics for training

    Args:
        workflow: Workflow context
        stakeholder_manager_messages: Clarification dialogue
        model_name: LLM to use for generation
        seed: Random seed for reproducibility

    Returns:
        Tuple of (executable StagedRubric, raw spec for logging/metadata)

    Raises:
        Exception: If LLM generation or code compilation fails
    """
    logger.info(
        f"Generating STAGED rubric with {len(stakeholder_manager_messages)} stakeholder-manager messages"
    )

    # Build prompt using GDPEval-style system prompt
    system_prompt = STAGED_RUBRIC_SYSTEM_PROMPT
    
    # Build user prompt from task + clarification context
    user_prompt = _build_staged_rubric_user_prompt(
        task_summary=workflow.workflow_goal,
        task_description=workflow.tasks[list(workflow.tasks.keys())[0]].description if workflow.tasks else "",
        stakeholder_manager_messages=stakeholder_manager_messages,
    )

    # LLM generates staged rubric spec
    rubric_spec: ManagerAgentGeneratedStagedRubric = await generate_structured_response(  # type: ignore
        model=model_name,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        response_type=ManagerAgentGeneratedStagedRubric,
        temperature=1.0,
        seed=seed,
    )

    # Convert to executable StagedRubric
    executable_rubric = convert_staged_rubric_to_executable(rubric_spec)

    logger.info(
        f"Generated staged rubric '{rubric_spec.category_name}' with {len(rubric_spec.stages)} stages"
    )

    return executable_rubric, rubric_spec


def _build_staged_rubric_user_prompt(
    task_summary: str,
    task_description: str,
    stakeholder_manager_messages: list[Message],
) -> str:
    """Build user prompt for staged rubric generation.
    
    Args:
        task_summary: High-level task goal
        task_description: Detailed task description
        stakeholder_manager_messages: Clarification dialogue
    
    Returns:
        User prompt for LLM
    """
    parts = [
        "# Task Context",
        "",
        "## Task Summary",
        task_summary,
        "",
        "## Task Description",
        task_description,
        "",
    ]
    
    if stakeholder_manager_messages:
        parts.extend([
            "## Stakeholder Clarification Dialogue",
            "",
            "The following Q&A exchanges clarify what the stakeholder values:",
            "",
        ])
        for msg in stakeholder_manager_messages:
            parts.append(f"**{msg.sender_id}**: {msg.content}")
            parts.append("")
    
    parts.extend([
        "---",
        "",
        "Generate a staged evaluation rubric for this task that:",
        "1. Uses 2-3 sequential stages (gate → correctness → quality)",
        "2. Makes the first stage a required gate for format/structure",
        "3. Includes both code rules (for precision) and LLM judges (for quality)",
        "4. Has clear failure actions for each stage",
        "",
        "Return a ManagerAgentGeneratedStagedRubric object.",
    ])
    
    return "\n".join(parts)
