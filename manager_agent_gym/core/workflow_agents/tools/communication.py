"""
Communication tools for agents.

These tools enable agents to send and receive messages during task execution,
with automatic context injection for agent ID and current task ID.
"""

from datetime import datetime, timedelta
from typing import TYPE_CHECKING
from uuid import UUID

from agents import function_tool

if TYPE_CHECKING:
    from ...communication.service import CommunicationService

from ...common.logging import logger


def create_communication_tools(
    communication_service: "CommunicationService",
    agent_id: str,
    current_task_id: UUID | None = None,
) -> list:
    """
    Create communication tools with injected context.

    This function creates tool instances with the communication service,
    agent ID, and current task ID automatically injected. The agent
    doesn't need to know these details - they're handled transparently.

    Args:
        communication_service: The communication service instance
        agent_id: The ID of the agent using these tools
        current_task_id: The ID of the current task (auto-injected)

    Returns:
        List of communication tools ready for use
    """

    @function_tool
    async def send_message(
        to_agent_id: str, content: str, message_type: str = "direct"
    ) -> str:
        """
        Send a message to another agent during task execution.

        Use this tool to communicate with other agents, ask questions,
        provide updates, or coordinate work. The message will be
        automatically linked to your current task.

        Args:
            to_agent_id: The ID of the agent you want to send the message to
            content: The message content
            message_type: Type of message - "direct", "request", "response", "status_update", "alert"

        Returns:
            Confirmation message

        Example:
            await send_message(
                to_agent_id="data_analyst_agent",
                content="Can you provide the latest metrics for the optimization task?",
                message_type="request"
            )
        """
        try:
            # Import here to avoid circular imports
            from ....schemas.core.communication import MessageType

            # Convert string to MessageType enum, fallback to DIRECT
            try:
                msg_type = MessageType(message_type.lower())
            except ValueError:
                msg_type = MessageType.DIRECT
                logger.warning(f"Unknown message type '{message_type}', using 'direct'")

            # Send the message with auto-injected context
            await communication_service.send_direct_message(
                from_agent=agent_id,  # Auto-injected!
                to_agent=to_agent_id,
                content=content,
                message_type=msg_type,
                related_task_id=current_task_id,
            )

            logger.info(
                f"Agent {agent_id} sent message to {to_agent_id}: {content[:50]}..."
            )

            return f"✅ Message sent to {to_agent_id}: {content[:50]}{'...' if len(content) > 50 else ''}"

        except Exception as e:
            logger.error(
                f"Failed to send message from {agent_id} to {to_agent_id}: {e}"
            )
            return f"Failed to send message: {str(e)}"

    @function_tool
    async def broadcast_message(content: str, message_type: str = "broadcast") -> str:
        """
        Send a broadcast message to all agents in the workflow.

        Use this for announcements, status updates, or information that
        all team members should know about. The message will be automatically
        linked to your current task.

        Args:
            content: The message content to broadcast
            message_type: Type of message - "broadcast", "alert", "status_update"

        Returns:
            Confirmation message

        Example:
            await broadcast_message(
                content="Database optimization is 75% complete, ETA 30 minutes",
                message_type="status_update"
            )
        """
        try:
            # Import here to avoid circular imports
            from ....schemas.core.communication import MessageType

            # Convert string to MessageType enum, fallback to BROADCAST
            try:
                msg_type = MessageType(message_type.lower())
            except ValueError:
                msg_type = MessageType.BROADCAST
                logger.warning(
                    f"Unknown message type '{message_type}', using 'broadcast'"
                )

            # Send the broadcast with auto-injected context
            message = await communication_service.broadcast_message(
                from_agent=agent_id,  # Auto-injected!
                content=content,
                message_type=msg_type,
                related_task_id=current_task_id,  # Auto-injected!
            )

            recipient_count = len(message.recipients)
            logger.info(
                f"Agent {agent_id} broadcast message to {recipient_count} agents: {content[:50]}..."
            )

            return f"📢 Broadcast sent to {recipient_count} agents: {content[:50]}{'...' if len(content) > 50 else ''}"

        except Exception as e:
            logger.error(f"Failed to broadcast message from {agent_id}: {e}")
            return f"Failed to broadcast message: {str(e)}"

    @function_tool
    async def get_recent_messages(
        limit: int = 10, since_minutes: int = 60, message_types: str = "all"
    ) -> str:
        """
        Retrieve recent messages sent to you.

        Use this to check for updates, questions, or communications from
        other agents that might be relevant to your current work.

        Args:
            limit: Maximum number of messages to retrieve (1-50)
            since_minutes: How many minutes back to look for messages (1-1440)
            message_types: Types to include - "all", "direct", "request", "broadcast", or comma-separated list

        Returns:
            Formatted list of recent messages

        Example:
            recent = await get_recent_messages(limit=5, since_minutes=30, message_types="request,direct")
        """
        try:
            # Import here to avoid circular imports
            from ....schemas.core.communication import MessageType

            # Validate and constrain parameters
            limit = max(1, min(50, limit))
            since_minutes = max(1, min(1440, since_minutes))  # Max 24 hours

            # Parse message types
            msg_types = None
            if message_types.lower() != "all":
                type_list = [t.strip().lower() for t in message_types.split(",")]
                msg_types = []
                for type_str in type_list:
                    try:
                        msg_types.append(MessageType(type_str))
                    except ValueError:
                        logger.warning(f"Unknown message type '{type_str}', ignoring")

            # Calculate since timestamp
            since_time = datetime.now() - timedelta(minutes=since_minutes)

            # Get messages for this agent
            messages = communication_service.get_messages_for_agent(
                agent_id=agent_id,  # Auto-injected!
                since=since_time,
                message_types=msg_types,
                limit=limit,
            )

            if not messages:
                return f"No recent messages found (last {since_minutes} minutes)"

            # Format messages for display
            formatted_messages = [f"Recent messages ({len(messages)} found):"]

            for msg in messages:
                time_str = msg.timestamp.strftime("%H:%M")
                msg_type_icon = {
                    "direct": "💬",
                    "request": "❓",
                    "response": "💭",
                    "broadcast": "📢",
                    "alert": "🚨",
                    "status_update": "📊",
                }.get(msg.message_type.value, "📝")

                # Truncate long messages
                content = msg.content
                if len(content) > 100:
                    content = content[:97] + "..."

                formatted_messages.append(
                    f"{msg_type_icon} [{time_str}] From {msg.sender_id}: {content}"
                )

            result = "\n".join(formatted_messages)
            logger.info(f"Agent {agent_id} retrieved {len(messages)} recent messages")

            return result

        except Exception as e:
            logger.error(f"Failed to get recent messages for {agent_id}: {e}")
            return f"Failed to retrieve messages: {str(e)}"

    @function_tool
    async def get_conversation_with(other_agent_id: str, limit: int = 20) -> str:
        """
        Get conversation history with a specific agent.

        Use this to review past communications with another agent
        to understand context or continue a conversation.

        Args:
            other_agent_id: The ID of the other agent
            limit: Maximum number of messages to retrieve (1-50)

        Returns:
            Formatted conversation history

        Example:
            history = await get_conversation_with("manager_agent", limit=10)
        """
        try:
            # Validate parameters
            limit = max(1, min(50, limit))

            # Get conversation history
            messages = communication_service.get_conversation_history(
                agent_id=agent_id,  # Auto-injected!
                other_agent=other_agent_id,
                limit=limit,
            )

            if not messages:
                return f"No conversation history found with {other_agent_id}"

            # Format conversation
            formatted_messages = [
                f"Conversation with {other_agent_id} ({len(messages)} messages):"
            ]

            for msg in messages:
                time_str = msg.timestamp.strftime("%H:%M")
                sender_name = "You" if msg.sender_id == agent_id else other_agent_id

                # Truncate long messages
                content = msg.content
                if len(content) > 150:
                    content = content[:147] + "..."

                formatted_messages.append(f"[{time_str}] {sender_name}: {content}")

            result = "\n".join(formatted_messages)
            logger.info(
                f"Agent {agent_id} retrieved conversation history with {other_agent_id}"
            )

            return result

        except Exception as e:
            logger.error(
                f"Failed to get conversation history for {agent_id} with {other_agent_id}: {e}"
            )
            return f"Failed to retrieve conversation: {str(e)}"

    @function_tool
    async def get_task_messages(task_id: str | None = None) -> str:
        """
        Get messages related to a specific task.

        Use this to see all communications about a particular task,
        which can help understand requirements, progress, or issues.

        Args:
            task_id: The task ID to get messages for (defaults to current task)

        Returns:
            Formatted list of task-related messages

        Example:
            task_comms = await get_task_messages()  # Current task
            task_comms = await get_task_messages("task-uuid-here")  # Specific task
        """
        try:
            # Use current task if none specified
            target_task_id = current_task_id
            if task_id:
                try:
                    target_task_id = UUID(task_id)
                except ValueError:
                    return "Invalid task ID format for task messages: {task_id}"

            if not target_task_id:
                return "No task ID available"

            # Get task-related messages
            messages = communication_service.get_task_communications(target_task_id)

            if not messages:
                return f"No messages found for task {target_task_id}"

            # Format messages
            formatted_messages = [
                f"Messages for task {target_task_id} ({len(messages)} found):"
            ]

            for msg in messages:
                time_str = msg.timestamp.strftime("%H:%M")

                # Show who the message was to/from
                if msg.is_broadcast():
                    direction = f"{msg.sender_id} → ALL"
                else:
                    recipients = ", ".join(msg.get_all_recipients())
                    direction = f"{msg.sender_id} → {recipients}"

                # Truncate long messages
                content = msg.content
                if len(content) > 100:
                    content = content[:97] + "..."

                formatted_messages.append(f"[{time_str}] {direction}: {content}")

            result = "\n".join(formatted_messages)
            logger.info(
                f"Agent {agent_id} retrieved {len(messages)} messages for task {target_task_id}"
            )

            return result

        except Exception as e:
            logger.error(f"Failed to get task messages for {agent_id}: {e}")
            return f"Failed to retrieve task messages: {str(e)}"

    # Return all the tools with injected context
    return [
        send_message,
        broadcast_message,
        get_recent_messages,
        get_conversation_with,
        get_task_messages,
    ]
