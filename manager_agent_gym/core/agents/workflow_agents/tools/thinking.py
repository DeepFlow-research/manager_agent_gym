"""
Thinking and planning tools for workflow agents.

Provides agents with explicit space to think through tasks, plan their approach,
track progress, and create stakeholder-facing documentation of their methodology.
"""

from agents import function_tool, RunContextWrapper, Tool
from manager_agent_gym.core.workflow.context import AgentExecutionContext
from manager_agent_gym.core.agents.workflow_agents.schemas.telemetry import (
    AgentToolUseEvent,
)
from manager_agent_gym.core.common.logging import logger


@function_tool
async def think_through_task(
    wrapper: RunContextWrapper[AgentExecutionContext],
    thoughts: str,
) -> str:
    """
    Think through the task at hand and organize your thoughts.

    Use this tool to:
    - Break down complex tasks into manageable steps
    - Reason about the best approach to take
    - Consider potential challenges and solutions
    - Reflect on requirements and evaluation criteria
    - Make sense of available resources and how to use them

    This is your private thinking space - use it to work through problems
    before taking action. There's no limit to how many times you can use this.

    Args:
        thoughts: Your thinking process, analysis, and reasoning about the task

    Returns:
        Acknowledgment that your thoughts have been recorded
    """
    ctx = wrapper.context
    try:
        # Log the thinking for traceability
        logger.debug(
            f"Agent {ctx.agent_id} thinking on task {ctx.current_task_id}: {thoughts[:100]}..."
        )

        ctx.record_tool_event(
            AgentToolUseEvent(
                agent_id=ctx.agent_id,
                task_id=ctx.current_task_id,
                tool_name="think_through_task",
                succeeded=True,
            )
        )

        return (
            "✓ Thoughts recorded. Continue thinking or proceed with your next action. "
            "Remember: you can use this tool as many times as needed to work through the problem."
        )

    except Exception as e:
        logger.error(f"Failed to record thinking: {e}")
        ctx.record_tool_event(
            AgentToolUseEvent(
                agent_id=ctx.agent_id,
                task_id=ctx.current_task_id,
                tool_name="think_through_task",
                succeeded=False,
                error_type=type(e).__name__,
                error_message=str(e),
            )
        )
        return f"Failed to record thoughts: {str(e)}"


@function_tool
async def create_task_plan(
    wrapper: RunContextWrapper[AgentExecutionContext],
    plan_steps: str,
) -> str:
    """
    Create a structured plan for completing the current task.

    Use this tool to:
    - Outline the specific steps you'll take to complete the task
    - Sequence your work logically
    - Identify dependencies between steps
    - Set checkpoints for quality assessment
    - Note which tools or resources you'll use for each step

    This helps you work systematically through complex tasks and track your progress.
    You can update your plan as you go by calling this tool again with a revised plan.

    Args:
        plan_steps: Your step-by-step plan, formatted clearly (e.g., numbered steps)

    Returns:
        Acknowledgment with your plan summary
    """
    ctx = wrapper.context
    try:
        # Count the steps in the plan
        step_count = len([line for line in plan_steps.split("\n") if line.strip()])

        logger.info(
            f"Agent {ctx.agent_id} created plan for task {ctx.current_task_id} with ~{step_count} steps"
        )

        ctx.record_tool_event(
            AgentToolUseEvent(
                agent_id=ctx.agent_id,
                task_id=ctx.current_task_id,
                tool_name="create_task_plan",
                succeeded=True,
            )
        )

        return (
            f"✓ Task plan created with approximately {step_count} steps. "
            f"You can refer back to this plan as you work and update it as needed. "
            f"Use 'update_plan_progress' to track which steps you've completed."
        )

    except Exception as e:
        logger.error(f"Failed to create plan: {e}")
        ctx.record_tool_event(
            AgentToolUseEvent(
                agent_id=ctx.agent_id,
                task_id=ctx.current_task_id,
                tool_name="create_task_plan",
                succeeded=False,
                error_type=type(e).__name__,
                error_message=str(e),
            )
        )
        return f"Failed to create plan: {str(e)}"


@function_tool
async def update_plan_progress(
    wrapper: RunContextWrapper[AgentExecutionContext],
    completed_steps: str,
    next_steps: str,
) -> str:
    """
    Update your progress on the current task plan.

    Use this tool to:
    - Track which steps you've completed
    - Reflect on what you've accomplished so far
    - Identify what needs to be done next
    - Adjust your approach based on what you've learned
    - Stay organized during multi-step work

    This helps you maintain clarity and direction throughout the task.

    Args:
        completed_steps: Summary of what you've finished so far
        next_steps: What you plan to do next

    Returns:
        Acknowledgment with progress summary
    """
    ctx = wrapper.context
    try:
        logger.info(
            f"Agent {ctx.agent_id} updating progress on task {ctx.current_task_id}"
        )

        ctx.record_tool_event(
            AgentToolUseEvent(
                agent_id=ctx.agent_id,
                task_id=ctx.current_task_id,
                tool_name="update_plan_progress",
                succeeded=True,
            )
        )

        return (
            "✓ Progress updated. Keep going with your next steps. "
            "You're making measurable progress on the task."
        )

    except Exception as e:
        logger.error(f"Failed to update progress: {e}")
        ctx.record_tool_event(
            AgentToolUseEvent(
                agent_id=ctx.agent_id,
                task_id=ctx.current_task_id,
                tool_name="update_plan_progress",
                succeeded=False,
                error_type=type(e).__name__,
                error_message=str(e),
            )
        )
        return f"Failed to update progress: {str(e)}"


@function_tool
async def document_approach_for_stakeholder(
    wrapper: RunContextWrapper[AgentExecutionContext],
    approach_overview: str,
    methodology_notes: str,
    key_decisions: str,
    considerations: str,
) -> str:
    """
    Create a stakeholder-facing document explaining your approach and methodology.

    This tool creates a Markdown document that demonstrates your systematic thinking
    and professional approach to the task. This document:
    - Shows stakeholders your thought process and rationale
    - Provides transparency into your methodology
    - Demonstrates thoroughness and strategic thinking
    - Can be evaluated for quality and professionalism

    **When to use this:**
    - For complex analytical tasks where methodology matters
    - When stakeholders value transparency in your process
    - For tasks requiring justification of approach
    - To demonstrate systematic and professional work habits

    **✨ AUTOMATIC FILE TRACKING:**
    The created document is automatically tracked as an intermediary resource
    that evaluators and stakeholders can review.

    Args:
        approach_overview: High-level summary of your approach (2-3 sentences)
        methodology_notes: Detailed explanation of methods, tools, or techniques used
        key_decisions: Important decisions made and why you made them
        considerations: Alternatives considered, risks identified, or constraints addressed

    Returns:
        Confirmation message with file details

    Example:
        document_approach_for_stakeholder(
            approach_overview="I am using NPV analysis to compare suppliers...",
            methodology_notes="NPV calculation uses 10% discount rate based on...",
            key_decisions="Chose 5-year time horizon because...",
            considerations="Considered IRR but NPV is more appropriate because..."
        )
    """
    ctx = wrapper.context
    try:
        # Build formatted markdown content
        content = f"""# Methodology & Approach Documentation

**Task:** {ctx.current_task_id}
**Agent:** {ctx.agent_id}

---

## Approach Overview

{approach_overview}

---

## Methodology Notes

{methodology_notes}

---

## Key Decisions & Rationale

{key_decisions}

---

## Considerations & Alternatives

{considerations}

---

*This document provides transparency into the analytical approach and decision-making process used to complete this task.*
"""

        # Save as markdown file
        import tempfile
        from pathlib import Path
        from manager_agent_gym.schemas.domain.resource import Resource

        # Create file in temp directory
        temp_dir = Path(tempfile.gettempdir())
        file_name = f"methodology_notes_{ctx.current_task_id}.md"
        file_path = temp_dir / file_name

        # Write content
        file_path.write_text(content, encoding="utf-8")

        # Register as intermediary resource
        ctx.register_created_resource(
            Resource(
                name=f"Methodology Documentation: {ctx.agent_id}",
                description="Stakeholder-facing documentation of analytical approach, methodology, key decisions, and considerations",
                file_path=str(file_path),
                mime_type="text/markdown",
                size_bytes=len(content.encode("utf-8")),
                resource_role="intermediary",
            )
        )

        logger.info(
            f"Agent {ctx.agent_id} created methodology documentation for task {ctx.current_task_id}"
        )

        ctx.record_tool_event(
            AgentToolUseEvent(
                agent_id=ctx.agent_id,
                task_id=ctx.current_task_id,
                tool_name="document_approach_for_stakeholder",
                succeeded=True,
            )
        )

        word_count = len(content.split())
        return (
            f"✅ Created methodology documentation: {file_name}\n"
            f"📄 {word_count} words documenting your approach\n"
            f"This document will be visible to stakeholders and evaluators as supporting evidence of your systematic approach."
        )

    except Exception as e:
        logger.error(f"Failed to create methodology documentation: {e}")
        ctx.record_tool_event(
            AgentToolUseEvent(
                agent_id=ctx.agent_id,
                task_id=ctx.current_task_id,
                tool_name="document_approach_for_stakeholder",
                succeeded=False,
                error_type=type(e).__name__,
                error_message=str(e),
            )
        )
        return f"Failed to create methodology documentation: {str(e)}"


# Export all thinking tools
THINKING_TOOLS: list[Tool] = [
    think_through_task,
    create_task_plan,
    update_plan_progress,
    document_approach_for_stakeholder,
]


def create_thinking_tools() -> list[Tool]:
    """
    Create thinking and planning tools for agents.

    Returns:
        List of thinking tools
    """
    return THINKING_TOOLS.copy()
