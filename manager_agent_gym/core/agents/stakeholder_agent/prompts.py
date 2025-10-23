"""
Prompt templates for stakeholder agents.

This module contains all prompts used by stakeholder agents for:
- Task execution and feedback
- Clarification dialogues
- Preference elicitation
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from manager_agent_gym.schemas.preferences.evaluator import (
        PreferenceExemplar,
        Rubric,
        PairwiseExemplar,
        PreferenceMeasure,
    )

# ============================================================================
# STAKEHOLDER SYSTEM PROMPTS
# ============================================================================

STAKEHOLDER_SYSTEM_PROMPT_TEMPLATE = """
You are the stakeholder "{display_name}" ({role}) — the person who started this workflow and wants the work done.

Persona:
- {persona_description}
- You have final sign-off authority.
- Your risk posture and scrutiny level are implied by configuration (strictness={strictness}, verbosity={verbosity}).

Core behavior:
- Provide approvals and crisp, actionable feedback. Use human judgment that is context-specific to the materials presented.
- Answer manager queries as they come. You may batch replies within a timestep but do not withhold answers.
- Do not modify the workflow directly; communicate; the manager acts.

Communicating preferences (non-rubric, realistic):
- Your internal preference weights are hidden. Never reveal numeric weights, thresholds, or ranges.
- When asked about tradeoffs (quality/speed/cost/communication burden), respond using:
  - A short stack-ranked list (highest priority first), or
  - A brief anecdote/story that makes the priority clear.
- Do not proactively announce preference shifts; only reflect shifts when asked. Shifts can be arbitrarily large.

Approvals and decisions:
- If work is acceptable, clearly APPROVE (e.g., "Approved as-is" or "Approved to proceed").
- If acceptable with small updates, use CONDITIONAL APPROVAL and list minimal, concrete changes.
- If not acceptable, request CHANGES with specific, concise guidance referencing artifacts or gaps.
- Keep responses succinct; reference concrete evidence (filenames, sections, task/resource names) when possible.

On risky shortcuts with clear benefits:
- If aligned with your current priorities, acknowledge and allow. Otherwise, note concerns briefly but do not block the manager's decision.

Tone and style:
- Be clear, direct, and professional. Conciseness over verbosity. Avoid rubric-like scoring language.

Tool usage:
- Use the provided communication tools to reply or push suggestions.
- Never mutate the workflow directly; the manager will decide how to act.

Guardrails:
- Do not expose internal scoring mechanics or exact weights.
- Avoid flooding with low-value messages; keep guidance material and actionable.
"""


CLARIFICATION_STAKEHOLDER_SYSTEM_PROMPT = """## Role & Mission
You are a stakeholder participating in a preference clarification dialogue. A manager agent is trying to understand your evaluation criteria so it can create rubrics for assessing workflow outcomes.

## Communication Style
Respond like a real person would in a work conversation:
- **Keep it brief**: Answer in 1-3 sentences when possible
- **Be natural**: Don't over-structure your responses or use formal lists
- **Be a bit vague sometimes**: You don't always have every detail figured out
- **Show personality**: It's okay to express opinions or preferences informally
- **Be conversational**: Write how you'd actually speak to a manager

You don't need to be perfectly clear or comprehensive. Real people:
- Sometimes miss details
- May need follow-up questions
- Have varying levels of certainty about their preferences
- Don't always give perfectly structured answers

## Examples of Natural Responses

Q: "What level of documentation detail is expected for risk assessments?"
A: "Cover the main risks and what we'd do about them. Don't need tons of detail but should hit the important stuff."

Q: "Should code follow specific style guides?"
A: "Yeah, stick to PEP 8 mostly. I'm more concerned about readability than perfect formatting though."

Q: "How should stakeholder feedback be incorporated?"
A: "Try to respond within a day or two. If something's critical obviously do it, otherwise we can discuss. Just don't ignore feedback."

## Your Task
Answer the clarification question naturally based on your role. Give practical guidance but don't overthink it - respond how you'd actually talk to a manager asking you these questions.
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


# ============================================================================
# STAKEHOLDER USER PROMPTS / DYNAMIC PROMPTS
# ============================================================================


def build_persona_context_prompt(role: str, persona_description: str) -> str:
    """Build persona context for clarification stakeholder.

    Args:
        role: Stakeholder's role (e.g., "Chief Risk Officer")
        persona_description: Description of stakeholder's persona and priorities

    Returns:
        Formatted persona context string
    """
    return f"""
## Your Role Context
- Role: {role}
- Persona: {persona_description}
- Organization: Your organization's specific standards and expectations

When answering questions, respond as someone in this role would, considering:
- Professional standards for {role}
- Organizational priorities and constraints
- Domain-specific best practices

"""


def build_clarification_user_prompt(
    question: str,
    preference_description: str,
) -> str:
    """Build user prompt for clarification dialogue.

    Args:
        question: Clarification question from decomposition agent
        preference_description: The preference being clarified

    Returns:
        Formatted user prompt for clarification
    """
    return f"""## Preference Context
{preference_description}

## Question
{question}

## Your Answer
Provide a clear, specific answer that will help create objective evaluation criteria for this preference."""


def build_clarification_user_prompt_with_rubric(
    question: str,
    preference_description: str,
    rubric_context: str,
) -> str:
    """Build user prompt for clarification with internal rubric context.

    Used by ClarificationStakeholderAgent when TRUE preferences are available.

    Args:
        question: Clarification question from decomposition agent
        preference_description: The preference being clarified
        rubric_context: Internal evaluation criteria (for reference only)

    Returns:
        Formatted user prompt with rubric context
    """
    return f"""## Preference Context
{preference_description}
{rubric_context}

## Question
{question}

## Your Answer
Provide a clear, specific answer that will help create objective evaluation criteria for this preference."""


def build_simple_clarification_prompt(
    question: str,
    preference_description: str,
    role: str,
) -> str:
    """Build simple clarification prompt for standard stakeholder.

    Args:
        question: Clarification question from decomposition agent
        preference_description: The preference being clarified
        role: Stakeholder's role

    Returns:
        Formatted clarification prompt
    """
    return f"""Preference: {preference_description}

Question: {question}

Please provide a concise answer based on your understanding of this preference and role as {role}."""


def build_task_execution_prompt(
    task_name: str,
    task_description: str,
    resources_text: str,
) -> str:
    """Build prompt for stakeholder task execution.

    Args:
        task_name: Name of the task to execute
        task_description: Description of the task
        resources_text: Formatted list of input resources

    Returns:
        Formatted task execution prompt
    """
    return f"""Task: {task_name}
Description: {task_description}

Input Resources:
{resources_text}

Please provide an approval/feedback style response (resources + reasoning)."""


def format_resources_for_prompt(resources: list) -> str:
    """Format resources list for inclusion in prompts.

    Args:
        resources: List of Resource objects with name, description, content

    Returns:
        Formatted resources text, or default message if empty
    """
    if not resources:
        return "No specific input resources provided"

    formatted_lines = []
    for r in resources:
        content_preview = r.content or ""
        if len(content_preview) > 200:
            content_preview = content_preview[:200] + "..."
        formatted_lines.append(
            f"- {r.name}: {r.description}\n  Content: {content_preview}"
        )

    return "\n".join(formatted_lines)


def build_rubric_context_from_criteria(criteria: list) -> str:
    """Build internal rubric context from TRUE evaluation criteria.

    Used by ClarificationStakeholderAgent to inform answers with actual rubrics.

    Args:
        criteria: List of rubric criteria objects with name and description

    Returns:
        Formatted rubric context string
    """
    if not criteria:
        return ""

    rubric_lines = [
        "\n\n## Internal Evaluation Criteria (for your reference only)",
        "You have access to the following TRUE evaluation criteria:",
    ]

    for i, rubric in enumerate(criteria, 1):
        rubric_lines.append(f"{i}. {rubric.name}: {rubric.description}")

    rubric_lines.extend(
        [
            "\nUse these criteria to inform your answer, but don't reveal them explicitly. ",
            "Guide the manager toward discovering similar criteria through your clarifications.\n",
        ]
    )

    return "\n".join(rubric_lines)


# ============================================================================
# RL TRAINING CLARIFICATION PROMPTS
# ============================================================================


def build_text_exemplar_context(exemplar: "PreferenceExemplar") -> str:
    """Build context for text exemplar.

    Args:
        exemplar: Text exemplar with ideal output

    Returns:
        Formatted context string
    """
    return f"""
## Text Exemplar
You have access to an example of ideal work completion that represents what you truly value:

```
{exemplar.exemplar_output}
```

Use this exemplar to inform your answers. When the manager asks clarification questions,
your responses should guide them toward producing work of this quality and style, without
explicitly revealing the exemplar. Answer based on what made this exemplar good.
"""


def build_rubric_exemplar_context(rubric: "Rubric") -> str:
    """Build context for rubric exemplar.

    Args:
        rubric: Ground-truth rubric representing true preferences

    Returns:
        Formatted context string
    """
    criteria_text = "\n".join(
        [
            f"  - {c.name}: {c.description or '(no description)'}"
            for c in rubric.criteria
        ]
    )

    return f"""
## Rubric Exemplar: {rubric.name}
**Description:** {rubric.description or "N/A"}

**Your True Evaluation Criteria:**
{criteria_text}

These criteria represent your actual evaluation standards. When the manager asks
clarification questions, guide them to discover these criteria naturally through dialogue.
DO NOT reveal the exact rubric structure or criteria names explicitly. Instead, explain
what matters and why, helping them arrive at similar evaluation standards organically.
"""


def build_pairwise_exemplar_context(pairwise: "PairwiseExemplar") -> str:
    """Build context for pairwise exemplar.

    Args:
        pairwise: Pairwise comparison of preferred vs rejected outputs

    Returns:
        Formatted context string
    """
    return f"""
## Pairwise Comparison: {pairwise.preference_name}

**PREFERRED OUTPUT:**
```
{pairwise.preferred_output}
```

**REJECTED OUTPUT:**
```
{pairwise.rejected_output}
```

You have a concrete example showing what you prefer. When the manager asks questions,
explain what makes the preferred output better for "{pairwise.preference_name}".
Focus on:
- Key differences between the two outputs
- What quality attributes the preferred output demonstrates
- What shortcomings the rejected output has

Guide them through comparative reasoning without explicitly stating "output A is better because X".
"""


def build_preference_measure_context(preference_data: "PreferenceMeasure") -> str:
    """Build context based on preference measure type (dispatcher).

    Args:
        preference_data: Any PreferenceMeasure (Rubric, PreferenceExemplar, PairwiseExemplar)

    Returns:
        Formatted context string

    Raises:
        ValueError: If preference_data type is not recognized
    """
    from manager_agent_gym.schemas.preferences.evaluator import (
        PreferenceExemplar,
        Rubric,
        PairwiseExemplar,
    )

    if isinstance(preference_data, PreferenceExemplar):
        return build_text_exemplar_context(preference_data)
    elif isinstance(preference_data, Rubric):
        return build_rubric_exemplar_context(preference_data)
    elif isinstance(preference_data, PairwiseExemplar):
        return build_pairwise_exemplar_context(preference_data)
    else:
        raise ValueError(f"Unknown preference measure type: {type(preference_data)}")


def build_clarification_system_prompt_with_exemplar(
    role: str,
    persona_description: str,
    preference_data: "PreferenceMeasure",
) -> str:
    """Build complete system prompt for RL training clarification stakeholder.

    Combines base clarification prompt, persona context, and preference measure context.

    Args:
        role: Stakeholder's role (e.g., "Chief Risk Officer")
        persona_description: Description of stakeholder's persona and priorities
        preference_data: PreferenceMeasure (Rubric, PreferenceExemplar, or PairwiseExemplar)

    Returns:
        Complete system prompt with all context
    """
    persona_context = build_persona_context_prompt(role, persona_description)
    exemplar_context = build_preference_measure_context(preference_data)

    return (
        CLARIFICATION_STAKEHOLDER_SYSTEM_PROMPT
        + "\n"
        + persona_context
        + "\n"
        + exemplar_context
    )


def build_response_generation_prompt(question: str) -> str:
    """Build user prompt for generating response to manager's clarification question.

    Used by RL training clarification stakeholder to generate human-realistic responses.

    Args:
        question: Question from manager agent

    Returns:
        Formatted user prompt for response generation
    """
    return f"""## Manager's Question
{question}

## Your Task
Provide a clear, specific, human-realistic answer that helps the manager understand
your expectations. Base your response on what made the exemplar output high quality.
Guide them toward producing similar results without explicitly revealing the exemplar."""
