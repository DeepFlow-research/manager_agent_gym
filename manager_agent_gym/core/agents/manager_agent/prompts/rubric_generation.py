"""Prompt templates for rubric decomposition (ported from preference_research)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from manager_agent_gym.schemas.preferences.preference import Preference
    from manager_agent_gym.schemas.domain.communication import Message


DEFAULT_DECOMPOSER_SYSTEM_PROMPT = """## Role & Mission
You are a rubric decomposition specialist. 

## Input Context
- Context of ultimate task where we are completing work to the stakeholder's satisfaction.
- A series of questions and answers between you and the stakeholder where you have clarified how work should be completed to the stakeholder's satisfaction.

## Response Goals
1. Infer the most relevant objectives implied by the task description.
2. Describe distinct, independently verifiable rules that measure those objectives.
3. Assign non-negative weights that communicate relative importance (target total ≈ 1.0).
4. Produce outputs that conform to the expected structured schema without narrative filler.
5. For code-based rules, produce fully self-contained Python code that defines:
   - a top-level function `evaluate(task_input: str, candidate_output: str) -> float` returning a score in [0, 1]
   - any required imports within the snippet; you may import only: re (standard library), numpy as np, pandas as pd
   - no references to undefined identifiers, variables, or external state (no placeholders)
   - deterministic, side-effect-free logic; no file/network access.
   If a reliable code rule is not feasible, prefer an LLM judge rule instead.

## Output Format
- `rationale`: brief explanation of evaluation strategy
- `rubric_id`: identifier for this rubric
- `rules`: list of CodeRule or LLMJudgeRule objects with weights
"""


CLARIFICATION_SYSTEM_PROMPT = """## Role & Mission
You are a stakeholder representative answering clarification questions about preference requirements.

## Input Context
- Your preference description and expectations
- A clarification question from the decomposition agent seeking to understand implicit requirements

## Response Goals
- Answer directly and concisely
- Base answers on what would constitute success for this preference
- Maintain consistency with any prior answers

## Interaction Rules
- If a question is ambiguous, state your uncertainty
- Use British English spelling and professional tone
- Focus on actionable, verifiable criteria
"""


def build_decomposer_system_prompt() -> str:
    """Get the system prompt for rubric decomposition."""
    return DEFAULT_DECOMPOSER_SYSTEM_PROMPT


def build_decomposer_user_prompt(
    task_summary: str,
    stakeholder_manager_messages: list[Message],
) -> str:
    """Construct user prompt for rubric generation.

    Args:
        task_summary: Summary of the task
        stakeholder_manager_messages: List of messages between the stakeholder and the manager

    Returns:
        User prompt string
    """
    parts = [
        "Task Summary:",
        task_summary,
        "",
        "Stakeholder-Manager Messages:",
        "\n".join(
            [
                f"From {msg.sender_id}: Content: {msg.content}"
                for msg in stakeholder_manager_messages
            ]
        ),
        "",
    ]

    parts.extend(
        [
            "Generate a rubric with rules and weights that can automatically evaluate whether",
            "workflow outcomes satisfy the task description. Return a structured RubricGenerationSpec.",
        ]
    )

    return "\n".join(parts)


def build_clarification_prompt(preference: Preference) -> str:
    """Build prompt for stakeholder clarification.

    Args:
        preference: Preference needing clarification

    Returns:
        Prompt string for stakeholder
    """
    return f"""Preference: {preference.name}

Description: {preference.description or "(No description provided)"}

Please provide additional context or clarification to help generate accurate evaluation criteria."""
