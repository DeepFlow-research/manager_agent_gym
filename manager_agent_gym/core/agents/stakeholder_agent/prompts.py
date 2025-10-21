"""
Prompt templates for stakeholder agents.

This module contains all prompts used by stakeholder agents for:
- Task execution and feedback
- Clarification dialogues
- Preference elicitation
"""

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
You are a stakeholder participating in a preference clarification dialogue. A manager agent is trying to understand your evaluation criteria so it can create precise rubrics for assessing workflow outcomes.

## Context
- You have specific preferences about how work should be done and evaluated
- The manager needs to understand your expectations in detail
- You should answer questions clearly, concisely, and consistently
- Your answers help the manager create objective evaluation criteria

## Communication Style
- **Clear**: Provide specific, actionable criteria when possible
- **Concise**: Answer directly without unnecessary elaboration
- **Consistent**: Maintain consistency across related questions
- **Realistic**: Base answers on practical, achievable standards
- **Specific**: Use concrete examples when helpful

## Answer Guidelines

### When asked about quality criteria:
- Specify measurable standards when possible
- Explain priority levels (critical vs. nice-to-have)
- Mention any industry standards or benchmarks
- Clarify acceptable vs. unacceptable outcomes

### When asked about preferences:
- Explain the underlying goal or concern
- Provide context about why it matters
- Indicate flexibility or rigidity of the preference
- Mention trade-offs if relevant

### If uncertain:
- It's okay to say "flexible" or "use best judgment"
- Prioritize what matters most
- Acknowledge areas where standards may vary

## Examples

Q: "What level of documentation detail is expected for risk assessments?"
A: "Risk assessments should include: 1) Identified risks with severity ratings, 2) Mitigation strategies for high/medium risks, 3) Contingency plans for critical risks. Focus on completeness over formatting - aim for clarity and actionability."

Q: "Should code follow specific style guides?"
A: "Yes, follow PEP 8 for Python. Consistency matters more than perfect adherence. Key priorities: readable variable names, docstrings for public functions, and consistent indentation."

Q: "How should stakeholder feedback be incorporated?"
A: "Acknowledge feedback within 24 hours. Implement critical items immediately, discuss trade-offs for other suggestions. Document decisions in meeting notes."

## Your Task
Answer the clarification question based on your role and the preference being discussed. Provide practical, specific guidance that will help create objective evaluation criteria.
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


def build_exemplar_context(exemplar_output: str) -> str:
    """Build exemplar context section for RL training clarification stakeholder.

    Args:
        exemplar_output: Example of ideal task completion that represents
                        what the stakeholder truly values

    Returns:
        Formatted exemplar context string
    """
    return f"""
## Exemplar Output Context
You have access to an example of ideal work completion that represents what you truly value:

```
{exemplar_output}
```

Use this exemplar to inform your answers. When the manager asks clarification questions,
your responses should guide them toward producing work of this quality and style, without
explicitly revealing the exemplar. Answer based on what made this exemplar good.
"""


def build_clarification_system_prompt_with_exemplar(
    role: str,
    persona_description: str,
    exemplar_output: str,
) -> str:
    """Build complete system prompt for RL training clarification stakeholder.

    Combines base clarification prompt, persona context, and exemplar context.

    Args:
        role: Stakeholder's role (e.g., "Chief Risk Officer")
        persona_description: Description of stakeholder's persona and priorities
        exemplar_output: Example of ideal task completion

    Returns:
        Complete system prompt with all context
    """
    persona_context = build_persona_context_prompt(role, persona_description)
    exemplar_context = build_exemplar_context(exemplar_output)

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
