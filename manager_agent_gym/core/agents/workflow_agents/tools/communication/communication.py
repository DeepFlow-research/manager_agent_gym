"""Communication tools - two-layer architecture.

Layer 1: Core functions (_*) - pure business logic, testable, returns typed results
Layer 2: OpenAI tool wrappers - thin adapters for OpenAI SDK, handle JSON serialization
"""

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any
from uuid import UUID

from agents import function_tool

if TYPE_CHECKING:
    from manager_agent_gym.core.communication.service import CommunicationService


# ============================================================================
# LAYER 1: COMMUNICATION OPERATIONS (Core Business Logic)
# ============================================================================


async def _send_message(
    communication_service: "CommunicationService",
    agent_id: str,
    to_agent_id: str,
    content: str,
    message_type: str = "direct",
    current_task_id: UUID | None = None,
) -> dict[str, Any]:
    """Send a message to another agent."""
    try:
        from manager_agent_gym.schemas.domain.communication import MessageType

        # Convert string to MessageType enum
        try:
            msg_type = MessageType(message_type.lower())
        except ValueError:
            msg_type = MessageType.DIRECT

        await communication_service.send_direct_message(
            from_agent=agent_id,
            to_agent=to_agent_id,
            content=content,
            message_type=msg_type,
            related_task_id=current_task_id,
        )

        return {
            "success": True,
            "to": to_agent_id,
            "content_preview": content[:50],
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


async def _broadcast_message(
    communication_service: "CommunicationService",
    agent_id: str,
    content: str,
    message_type: str = "broadcast",
    current_task_id: UUID | None = None,
) -> dict[str, Any]:
    """Broadcast a message to all agents."""
    try:
        from manager_agent_gym.schemas.domain.communication import MessageType

        try:
            msg_type = MessageType(message_type.lower())
        except ValueError:
            msg_type = MessageType.BROADCAST

        message = await communication_service.broadcast_message(
            from_agent=agent_id,
            content=content,
            message_type=msg_type,
            related_task_id=current_task_id,
        )

        return {
            "success": True,
            "recipient_count": len(message.recipients),
            "content_preview": content[:50],
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def _get_recent_messages(
    communication_service: "CommunicationService",
    agent_id: str,
    limit: int = 10,
    since_minutes: int = 60,
    message_types: str = "all",
) -> dict[str, Any]:
    """Get recent messages for an agent."""
    try:
        from manager_agent_gym.schemas.domain.communication import MessageType

        # Validate parameters
        limit = max(1, min(50, limit))
        since_minutes = max(1, min(1440, since_minutes))

        # Parse message types
        msg_types = None
        if message_types.lower() != "all":
            type_list = [t.strip().lower() for t in message_types.split(",")]
            msg_types = []
            for type_str in type_list:
                try:
                    msg_types.append(MessageType(type_str))
                except ValueError:
                    pass

        # Calculate since timestamp
        since_time = datetime.now() - timedelta(minutes=since_minutes)

        # Get messages
        messages = communication_service.get_messages_for_agent(
            agent_id=agent_id,
            since=since_time,
            message_types=msg_types,
            limit=limit,
        )

        formatted_messages = []
        for msg in messages:
            formatted_messages.append(
                {
                    "timestamp": msg.timestamp.isoformat(),
                    "from": msg.sender_id,
                    "type": msg.message_type.value,
                    "content": msg.content,
                }
            )

        return {"success": True, "messages": formatted_messages, "count": len(messages)}

    except Exception as e:
        return {"success": False, "error": str(e)}


def _get_conversation_history(
    communication_service: "CommunicationService",
    agent_id: str,
    other_agent_id: str,
    limit: int = 20,
) -> dict[str, Any]:
    """Get conversation history with another agent."""
    try:
        limit = max(1, min(50, limit))

        messages = communication_service.get_conversation_history(
            agent_id=agent_id,
            other_agent=other_agent_id,
            limit=limit,
        )

        formatted_messages = []
        for msg in messages:
            formatted_messages.append(
                {
                    "timestamp": msg.timestamp.isoformat(),
                    "from": msg.sender_id,
                    "content": msg.content,
                }
            )

        return {"success": True, "messages": formatted_messages, "count": len(messages)}

    except Exception as e:
        return {"success": False, "error": str(e)}


def _get_task_messages(
    communication_service: "CommunicationService",
    agent_id: str,
    task_id: UUID,
) -> dict[str, Any]:
    """Get messages related to a task."""
    try:
        messages = communication_service.get_task_communications(task_id)

        formatted_messages = []
        for msg in messages:
            recipients = (
                ", ".join(msg.get_all_recipients()) if not msg.is_broadcast() else "ALL"
            )
            formatted_messages.append(
                {
                    "timestamp": msg.timestamp.isoformat(),
                    "from": msg.sender_id,
                    "to": recipients,
                    "content": msg.content,
                }
            )

        return {"success": True, "messages": formatted_messages, "count": len(messages)}

    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================================
# LAYER 2: OPENAI TOOL WRAPPERS
# ============================================================================


def create_communication_tools(
    communication_service: "CommunicationService",
    agent_id: str,
    current_task_id: UUID | None = None,
) -> list:
    """Create communication tools with injected context."""

    @function_tool
    async def send_message(
        to_agent_id: str, content: str, message_type: str = "direct"
    ) -> str:
        """
        Send a direct message to another agent in the workflow system.

        This tool enables communication between agents working on related tasks. Use it
        to request information, provide updates, ask questions, or coordinate work with
        other agents. Messages are delivered immediately and can be retrieved by the
        recipient using their message tools.

        Parameters:
            to_agent_id (str):
                The unique identifier of the agent you want to message.
                Example: "analyst_001" or "data_processor"
            content (str):
                The message content to send. Be clear and specific about what you need
                or want to communicate. Example: "Can you provide the Q4 sales data?"
            message_type (str):
                The type of message. Options:
                - "direct": Standard direct message (default)
                - "request": When asking for something
                - "response": When replying to a request
                - "alert": For urgent or important notifications
                Default: "direct"

        Returns:
            str:
                Success confirmation with the recipient and message preview, or an error
                message if sending fails (e.g., recipient not found).

        Usage:
            Call this tool when you need to communicate with another agent. Common uses:
            requesting data from another agent, asking questions, providing updates,
            coordinating tasks, or alerting others about important information. Always
            be clear about what you need or want to communicate.
        """
        result = await _send_message(
            communication_service,
            agent_id,
            to_agent_id,
            content,
            message_type,
            current_task_id,
        )
        if result["success"]:
            return f"✅ Message sent to {to_agent_id}: {result['content_preview']}..."
        return f"Failed to send message: {result.get('error')}"

    @function_tool
    async def broadcast_message(content: str, message_type: str = "broadcast") -> str:
        """
        Send a broadcast message to all agents in the workflow system simultaneously.

        This tool sends a message to all agents at once, useful for announcements,
        system-wide alerts, status updates, or any information that everyone needs to
        know. All agents in the workflow will receive and can read this message.

        Parameters:
            content (str):
                The message content to broadcast. Keep it clear and relevant for all
                recipients. Example: "All agents: System maintenance in 30 minutes"
            message_type (str):
                The type of broadcast. Options:
                - "broadcast": General announcement (default)
                - "alert": Urgent or important notification
                - "status_update": System or workflow status information
                Default: "broadcast"

        Returns:
            str:
                Success confirmation with the number of agents reached and message preview,
                or an error message if broadcasting fails.

        Usage:
            Use this tool when you need to communicate with all agents simultaneously.
            Common uses include: important announcements, system-wide alerts, workflow
            status updates, emergency notifications, or sharing information that affects
            all agents. Use sparingly to avoid message overload.
        """
        result = await _broadcast_message(
            communication_service, agent_id, content, message_type, current_task_id
        )
        if result["success"]:
            return f"📢 Broadcast sent to {result['recipient_count']} agents: {result['content_preview']}..."
        return f"Failed to broadcast message: {result.get('error')}"

    @function_tool
    async def get_recent_messages(
        limit: int = 10, since_minutes: int = 60, message_types: str = "all"
    ) -> str:
        """
        Retrieve recent messages that have been sent to you by other agents.

        This tool fetches messages you've received, filtered by time and optionally by
        message type. Use it regularly to check for new communications, requests, or
        updates from other agents. Messages are formatted with timestamps and type icons
        for easy reading.

        Parameters:
            limit (int):
                Maximum number of messages to retrieve (1-50). Default: 10.
            since_minutes (int):
                How far back in time to look for messages, in minutes (1-1440, i.e., up
                to 24 hours). Default: 60 (last hour).
            message_types (str):
                Filter by message type. Options:
                - "all": All message types (default)
                - "direct": Only direct messages
                - "request": Only requests
                - "broadcast": Only broadcasts
                - Or comma-separated list: "direct,request"
                Default: "all"

        Returns:
            str:
                Formatted list of recent messages with timestamps, sender names, and
                content, or a message indicating no messages were found.

        Usage:
            Call this tool regularly to check for new messages from other agents. Common
            uses include: checking for incoming requests, reading updates from other agents,
            reviewing broadcasts, or staying informed about workflow communications. Check
            at the start of your tasks and periodically during execution.
        """
        result = _get_recent_messages(
            communication_service, agent_id, limit, since_minutes, message_types
        )
        if result["success"]:
            if result["count"] == 0:
                return f"No recent messages found (last {since_minutes} minutes)"

            formatted = [f"Recent messages ({result['count']} found):"]
            for msg in result["messages"]:
                msg_type_icon = {
                    "direct": "💬",
                    "request": "❓",
                    "response": "💭",
                    "broadcast": "📢",
                    "alert": "🚨",
                    "status_update": "📊",
                }.get(msg["type"], "📝")

                content = msg["content"]
                if len(content) > 100:
                    content = content[:97] + "..."

                time_obj = datetime.fromisoformat(msg["timestamp"])
                time_str = time_obj.strftime("%H:%M")
                formatted.append(
                    f"{msg_type_icon} [{time_str}] From {msg['from']}: {content}"
                )

            return "\n".join(formatted)
        return f"Failed to retrieve messages: {result.get('error')}"

    @function_tool
    async def get_conversation_with(other_agent_id: str, limit: int = 20) -> str:
        """
        Retrieve the complete conversation history with a specific agent.

        This tool fetches all messages exchanged between you and another agent, showing
        the full conversation thread. Useful for reviewing past communications,
        understanding context, or tracking what was discussed with a specific agent.
        Messages are chronologically ordered for easy review.

        Parameters:
            other_agent_id (str):
                The unique identifier of the agent whose conversation history you want
                to retrieve. Example: "data_analyst" or "project_manager"
            limit (int):
                Maximum number of messages to retrieve from the conversation (1-50).
                Default: 20.

        Returns:
            str:
                Formatted conversation history showing messages exchanged with timestamps
                and sender identification (You vs. the other agent), or a message if no
                conversation history exists.

        Usage:
            Call this tool when you need to review past communications with a specific
            agent. Common uses include: reviewing what was discussed, understanding
            context for a current request, checking if information was already provided,
            or tracking the conversation flow with a particular agent.
        """
        result = _get_conversation_history(
            communication_service, agent_id, other_agent_id, limit
        )
        if result["success"]:
            if result["count"] == 0:
                return f"No conversation history found with {other_agent_id}"

            formatted = [
                f"Conversation with {other_agent_id} ({result['count']} messages):"
            ]
            for msg in result["messages"]:
                time_obj = datetime.fromisoformat(msg["timestamp"])
                time_str = time_obj.strftime("%H:%M")
                sender_name = "You" if msg["from"] == agent_id else other_agent_id

                content = msg["content"]
                if len(content) > 150:
                    content = content[:147] + "..."

                formatted.append(f"[{time_str}] {sender_name}: {content}")

            return "\n".join(formatted)
        return f"Failed to retrieve conversation: {result.get('error')}"

    @function_tool
    async def get_task_messages(task_id: str | None = None) -> str:
        """
        Retrieve all messages related to a specific task for context and coordination.

        This tool fetches all communications (messages, broadcasts, requests) that are
        related to a particular task. Useful for understanding task context, reviewing
        coordination efforts, or tracking all communications about a specific work item.
        If no task_id is provided, uses the current task.

        Parameters:
            task_id (str | None):
                Optional. The unique identifier of the task whose messages you want to
                retrieve. If None, uses the current task you're working on.
                Example: "123e4567-e89b-12d3-a456-426614174000"
                Default: None (uses current task)

        Returns:
            str:
                Formatted list of all messages related to the task, showing timestamps,
                sender/recipient information, and message content. Returns a message if
                no communications exist for the task.

        Usage:
            Call this tool when you need to understand all communications about a specific
            task. Common uses include: reviewing task coordination history, understanding
            what's been discussed about a task, checking task-related requests or updates,
            or getting full context before continuing work on a task.
        """
        target_task_id = current_task_id
        if task_id:
            try:
                target_task_id = UUID(task_id)
            except ValueError:
                return f"Invalid task ID format: {task_id}"

        if not target_task_id:
            return "No task ID available"

        result = _get_task_messages(communication_service, agent_id, target_task_id)
        if result["success"]:
            if result["count"] == 0:
                return f"No messages found for task {target_task_id}"

            formatted = [
                f"Messages for task {target_task_id} ({result['count']} found):"
            ]
            for msg in result["messages"]:
                time_obj = datetime.fromisoformat(msg["timestamp"])
                time_str = time_obj.strftime("%H:%M")
                direction = f"{msg['from']} → {msg['to']}"

                content = msg["content"]
                if len(content) > 100:
                    content = content[:97] + "..."

                formatted.append(f"[{time_str}] {direction}: {content}")

            return "\n".join(formatted)
        return f"Failed to retrieve task messages: {result.get('error')}"

    return [
        send_message,
        broadcast_message,
        get_recent_messages,
        get_conversation_with,
        get_task_messages,
    ]
