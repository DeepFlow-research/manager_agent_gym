"""
Thinking and planning tools for workflow agents.

Provides agents with explicit space to think through tasks, plan their approach,
and track progress through multi-step work.
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
async def reflect_on_approach(
    wrapper: RunContextWrapper[AgentExecutionContext],
    reflection: str,
) -> str:
    """
    Reflect on your current approach and consider adjustments.

    Use this tool to:
    - Pause and assess if your current approach is working
    - Consider alternative strategies or methods
    - Identify obstacles and how to overcome them
    - Evaluate if you're meeting the task requirements
    - Decide if you need to pivot or adjust your plan

    Reflection is a key part of high-quality work. Use this whenever you
    need to step back and evaluate your progress.

    Args:
        reflection: Your reflections on what's working, what's not, and potential adjustments

    Returns:
        Acknowledgment of your reflection
    """
    ctx = wrapper.context
    try:
        logger.debug(
            f"Agent {ctx.agent_id} reflecting on task {ctx.current_task_id}: {reflection[:100]}..."
        )

        ctx.record_tool_event(
            AgentToolUseEvent(
                agent_id=ctx.agent_id,
                task_id=ctx.current_task_id,
                tool_name="reflect_on_approach",
                succeeded=True,
            )
        )

        return (
            "✓ Reflection recorded. Based on your reflection, proceed with your "
            "chosen approach or make adjustments as needed."
        )

    except Exception as e:
        logger.error(f"Failed to record reflection: {e}")
        ctx.record_tool_event(
            AgentToolUseEvent(
                agent_id=ctx.agent_id,
                task_id=ctx.current_task_id,
                tool_name="reflect_on_approach",
                succeeded=False,
                error_type=type(e).__name__,
                error_message=str(e),
            )
        )
        return f"Failed to record reflection: {str(e)}"


# Export all thinking tools
THINKING_TOOLS: list[Tool] = [
    think_through_task,
    create_task_plan,
    update_plan_progress,
    reflect_on_approach,
]


def create_thinking_tools() -> list[Tool]:
    """
    Create thinking and planning tools for agents.

    Returns:
        List of thinking tools
    """
    return THINKING_TOOLS.copy()
