"""
Manager agent prompt templates.

Organized by function:
- rubric_generation: Prompts for decomposing preferences into rubrics
- rubric_decomposition: Manager agent system prompts for rubric decomposition phase
- structured_manager_prompts: Prompts for structured output generation
- task_decomposition: Prompts for breaking down complex tasks
"""

from manager_agent_gym.core.agents.manager_agent.prompts.rubric_generation import (
    CLARIFICATION_SYSTEM_PROMPT,
    build_decomposer_user_prompt,
    build_clarification_prompt,
)
from manager_agent_gym.core.agents.manager_agent.prompts.rubric_decomposition import (
    RUBRIC_DECOMPOSITION_SYSTEM_PROMPT,
)
from manager_agent_gym.core.agents.manager_agent.prompts.task_decomposition.prompts import (
    TASK_DECOMPOSITION_PROMPT,
)

__all__ = [
    # Rubric generation
    "CLARIFICATION_SYSTEM_PROMPT",
    "build_decomposer_user_prompt",
    "build_clarification_prompt",
    # Rubric decomposition manager
    "RUBRIC_DECOMPOSITION_SYSTEM_PROMPT",
    # Task decomposition
    "TASK_DECOMPOSITION_PROMPT",
]
