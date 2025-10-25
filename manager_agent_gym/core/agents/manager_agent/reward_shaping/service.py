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
        task_description=workflow.tasks[list(workflow.tasks.keys())[0]].description
        if workflow.tasks
        else "",
        stakeholder_manager_messages=stakeholder_manager_messages,
    )

    # LLM generates staged rubric spec using Agents SDK (not old Instructor approach)
    from manager_agent_gym.core.common.llm_generator import CloudLLMGenerator
    from agents import Agent
    from agents.run import Runner

    # Create generator for this model
    generator = CloudLLMGenerator(model_name=model_name)

    # Create agent with structured output type
    rubric_agent = Agent(
        name="rubric_generator",
        model=generator,
        instructions=system_prompt,
        output_type=ManagerAgentGeneratedStagedRubric,
    )

    # Run agent to get structured rubric
    result = await Runner.run(
        rubric_agent,
        user_prompt,
    )

    # Extract the structured output
    rubric_spec: ManagerAgentGeneratedStagedRubric = result.final_output  # type: ignore

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
        parts.extend(
            [
                "## Stakeholder Clarification Dialogue",
                "",
                "The following Q&A exchanges clarify what the stakeholder values:",
                "",
            ]
        )
        for msg in stakeholder_manager_messages:
            parts.append(f"**{msg.sender_id}**: {msg.content}")
            parts.append("")

    parts.extend(
        [
            "---",
            "",
            "Generate a staged evaluation rubric for this task that:",
            "1. Uses 2-3 sequential stages (gate → correctness → quality)",
            "2. Makes the first stage a required gate for format/structure",
            "3. Includes both code rules (for precision) and LLM judges (for quality)",
            "4. Has clear failure actions for each stage",
            "5. **IMPORTANT: Use high point values (20-50 total points) for numerical precision in GRPO**",
            "   - This gives finer granularity in advantage scores between outputs",
            "   - Example: max_total_score=40 with stages [8, 16, 16] is better than [2, 4, 4]",
            "",
            "Return a ManagerAgentGeneratedStagedRubric object.",
        ]
    )

    return "\n".join(parts)
