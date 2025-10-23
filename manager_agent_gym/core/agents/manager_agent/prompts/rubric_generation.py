"""Prompt templates for rubric decomposition (ported from preference_research)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from manager_agent_gym.schemas.preferences.preference import Preference
    from manager_agent_gym.schemas.domain.communication import Message




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
