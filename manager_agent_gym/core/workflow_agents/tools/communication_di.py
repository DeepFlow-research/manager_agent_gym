"""
Communication tools using dependency injection context.

Much cleaner than the closure-based approach - uses agents library DI pattern.
"""

from datetime import datetime, timedelta

from agents import function_tool, RunContextWrapper, Tool

from ...execution.context import AgentExecutionContext
from ....schemas.workflow_agents.telemetry import AgentToolUseEvent
from ....schemas.core.communication import MessageType
from ...common.logging import logger


@function_tool
async def send_message(
    wrapper: RunContextWrapper[AgentExecutionContext],
    to_agent: str,
    content: str,
    message_type: str = "general",
) -> str:
    """
    Send a direct message to another agent.

    Args:
        to_agent: ID of the agent to send message to
        content: Message content
        message_type: Type of message (general, request, response, alert, status_update)

    Returns:
        Confirmation message
    """
    ctx = wrapper.context
    try:
        # Convert string to enum
        msg_type = MessageType(message_type)

        message = await ctx.communication_service.send_direct_message(
            from_agent=ctx.agent_id,
            to_agent=to_agent,
            content=content,
            message_type=msg_type,
            related_task_id=ctx.current_task_id,
        )

        logger.info(
            f"Message sent from {ctx.agent_id} to {to_agent}: {content[:50]}..."
        )
        # Telemetry record
        ctx.record_tool_event(
            AgentToolUseEvent(
                agent_id=ctx.agent_id,
                task_id=ctx.current_task_id,
                tool_name="send_message",
                succeeded=True,
            )
        )
        return f"✅ Message sent to {to_agent}: {message}"

    except Exception as e:
        logger.error(f"Failed to send message from {ctx.agent_id}: {e}")
        ctx.record_tool_event(
            AgentToolUseEvent(
                agent_id=ctx.agent_id,
                task_id=ctx.current_task_id,
                tool_name="send_message",
                succeeded=False,
                error_type=type(e).__name__,
                error_message=str(e),
            )
        )
        return f"Failed to send message: {str(e)}"


@function_tool
async def broadcast_message(
    wrapper: RunContextWrapper[AgentExecutionContext],
    content: str,
    message_type: str = "general",
) -> str:
    """
    Send a broadcast message to all agents.

    Args:
        content: Message content
        message_type: Type of message (general, alert, status_update)

    Returns:
        Confirmation mess
    """
    ctx = wrapper.context
    try:
        # Convert string to enum
        msg_type = MessageType(message_type)

        broadcast_message = await ctx.communication_service.broadcast_message(
            from_agent=ctx.agent_id,
            content=content,
            message_type=msg_type,
            related_task_id=ctx.current_task_id,
        )

        logger.info(f"Broadcast sent from {ctx.agent_id}: {content[:50]}...")
        ctx.record_tool_event(
            AgentToolUseEvent(
                agent_id=ctx.agent_id,
                task_id=ctx.current_task_id,
                tool_name="broadcast_message",
                succeeded=True,
            )
        )
        return f"✅ Broadcast message sent to all agents: {broadcast_message}"

    except Exception as e:
        logger.error(f"Failed to broadcast from {ctx.agent_id}: {e}")
        ctx.record_tool_event(
            AgentToolUseEvent(
                agent_id=ctx.agent_id,
                task_id=ctx.current_task_id,
                tool_name="broadcast_message",
                succeeded=False,
                error_type=type(e).__name__,
                error_message=str(e),
            )
        )
        return f"Failed to broadcast: {str(e)}"


@function_tool
async def get_recent_messages(
    wrapper: RunContextWrapper[AgentExecutionContext],
    hours: float = 1.0,
    limit: int = 10,
) -> str:
    """
    Get recent messages sent to this agent.

    Args:
        hours: How many hours back to look (default: 1.0)
        limit: Maximum number of messages to return (default: 10)

    Returns:
        Formatted list of recent messages
    """
    ctx = wrapper.context

    try:
        since = datetime.now() - timedelta(hours=hours)
        messages = ctx.communication_service.get_messages_for_agent(
            agent_id=ctx.agent_id, since=since, limit=limit
        )

        if not messages:
            return "📭 No recent messages"

        formatted_messages = []
        for msg in messages:
            time_str = msg.timestamp.strftime("%H:%M")
            sender = msg.sender_id
            content = msg.content
            if len(content) > 100:
                content = content[:97] + "..."

            formatted_messages.append(f"[{time_str}] {sender}: {content}")

        result = "\n".join(formatted_messages)
        logger.info(f"Agent {ctx.agent_id} retrieved {len(messages)} recent messages")

        ctx.record_tool_event(
            AgentToolUseEvent(
                agent_id=ctx.agent_id,
                task_id=ctx.current_task_id,
                tool_name="get_recent_messages",
                succeeded=True,
            )
        )
        return result

    except Exception as e:
        logger.error(f"Failed to get messages: {e}")
        ctx.record_tool_event(
            AgentToolUseEvent(
                agent_id=ctx.agent_id,
                task_id=ctx.current_task_id,
                tool_name="get_recent_messages",
                succeeded=False,
                error_type=type(e).__name__,
                error_message=str(e),
            )
        )
        return f"Failed to retrieve messages: {str(e)}"


COMMUNICATION_TOOLS: list[Tool] = [send_message, broadcast_message, get_recent_messages]


@function_tool
async def end_workflow(
    wrapper: RunContextWrapper[AgentExecutionContext],
    reason: str = "ended by agent",
) -> str:
    """
    Request to end the workflow execution immediately after the current step.

    Should be only ever called by the manager agent when it thinks the workflow is complete and there is no further work to be done.

    Args:
        reason: Optional reason for termination

    Returns:
        Confirmation string
    """
    ctx = wrapper.context
    try:
        ctx.communication_service.request_end_workflow(reason)
        logger.warning(f"{ctx.agent_id} requested workflow end: {reason}")
        ctx.record_tool_event(
            AgentToolUseEvent(
                agent_id=ctx.agent_id,
                task_id=ctx.current_task_id,
                tool_name="end_workflow",
                succeeded=True,
            )
        )
        return "✅ Workflow end requested"
    except Exception as e:
        logger.error(f"Failed to request workflow end: {e}")
        ctx.record_tool_event(
            AgentToolUseEvent(
                agent_id=ctx.agent_id,
                task_id=ctx.current_task_id,
                tool_name="end_workflow",
                succeeded=False,
                error_type=type(e).__name__,
                error_message=str(e),
            )
        )
        return f"Failed to request workflow end: {str(e)}"


COMMUNICATION_TOOLS.append(end_workflow)
