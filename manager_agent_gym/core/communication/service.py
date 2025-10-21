"""
Communication service for managing all agent interactions.

This service implements the communication component (C) from the POSG state model,
providing centralized message routing, storage, and retrieval capabilities.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Callable, Awaitable
from uuid import UUID
from typing import cast

from manager_agent_gym.schemas.domain.communication import (
    Message,
    MessageType,
    CommunicationGraph,
    CommunicationThread,
    SenderMessagesView,
    ThreadMessagesView,
    MessageGrouping,
)

from manager_agent_gym.core.common.logging import logger


class CommunicationService:
    """Centralized message hub for agent interactions.

    Implements the Communication (C) component of the POSG model. Provides
    direct, multicast, and broadcast messaging, conversation threads, and
    grouped views for manager oversight.

    Example:
        ```python
        comm = CommunicationService()
        await comm.broadcast_message(from_agent="manager", content="Kickoff")
        inbox = comm.get_messages_for_agent("agent_a", limit=20)
        ```
    """

    def __init__(self):
        """Initialize the communication service."""
        self.graph = CommunicationGraph()
        self._message_listeners: dict[
            str, list[Callable[[Message], Awaitable[None]] | Callable[[Message], None]]
        ] = {}
        self._lock = asyncio.Lock()
        # Workflow control flags (per-instance)
        self._end_workflow_requested: bool = False

    def request_end_workflow(self, reason: str | None = None) -> None:
        """Signal that the current workflow should end as soon as possible."""
        self._end_workflow_requested = True
        if reason:
            logger.warning(f"End workflow requested: {reason}")
        else:
            logger.warning("End workflow requested")

    def is_end_workflow_requested(self) -> bool:
        """Return True if an end-of-workflow has been requested."""
        return self._end_workflow_requested

    async def send_direct_message(
        self,
        from_agent: str,
        to_agent: str,
        content: str,
        message_type: MessageType = MessageType.DIRECT,
        related_task_id: UUID | None = None,
        thread_id: UUID | None = None,
        priority: int = 1,
    ) -> Message:
        """
        Send a direct message between two agents.

        Args:
            from_agent: ID of the sending agent
            to_agent: ID of the receiving agent
            content: Message content
            message_type: Type of message
            related_task_id: Optional task this message relates to
            thread_id: Optional conversation thread
            priority: Message priority (1-5)

        Returns:
            The created Message object
        """
        async with self._lock:
            message = Message(
                sender_id=from_agent,
                receiver_id=to_agent,
                content=content,
                message_type=message_type,
                related_task_id=related_task_id,
                thread_id=thread_id,
                priority=priority,
            )

            # Add to graph
            self.graph.add_message(message)

            # Notify listeners
            await self._notify_listeners(message)

            logger.info(
                f"Direct message sent: {from_agent} -> {to_agent} "
                f"[{message_type.value}]: {content[:50]}..."
            )

            return message

    async def broadcast_message(
        self,
        from_agent: str,
        content: str,
        message_type: MessageType = MessageType.BROADCAST,
        related_task_id: UUID | None = None,
        exclude_agents: list[str] | None = None,
        priority: int = 1,
    ) -> Message:
        """
        Broadcast a message to all agents in the system.

        Args:
            from_agent: ID of the sending agent
            content: Message content
            message_type: Type of message
            related_task_id: Optional task this message relates to
            exclude_agents: Optional list of agents to exclude from broadcast
            priority: Message priority (1-5)

        Returns:
            The created Message object
        """
        async with self._lock:
            # Get all known agents except sender and excluded agents
            all_agents = self.graph.agent_registry.copy()
            all_agents.discard(from_agent)

            if exclude_agents:
                for excluded in exclude_agents:
                    all_agents.discard(excluded)

            message = Message(
                sender_id=from_agent,
                receiver_id=None,  # None indicates broadcast
                recipients=list(all_agents),
                content=content,
                message_type=message_type,
                related_task_id=related_task_id,
                priority=priority,
            )

            # Add to graph
            self.graph.add_message(message)

            # Notify listeners
            await self._notify_listeners(message)

            logger.info(
                f"Broadcast message sent: {from_agent} -> ALL "
                f"[{message_type.value}]: {content[:50]}... "
                f"({len(all_agents)} recipients)"
            )

            return message

    async def send_multicast_message(
        self,
        from_agent: str,
        to_agents: list[str],
        content: str,
        message_type: MessageType = MessageType.DIRECT,
        related_task_id: UUID | None = None,
        thread_id: UUID | None = None,
        priority: int = 1,
    ) -> Message:
        """
        Send a message to multiple specific agents.

        Args:
            from_agent: ID of the sending agent
            to_agents: List of recipient agent IDs
            content: Message content
            message_type: Type of message
            related_task_id: Optional task this message relates to
            thread_id: Optional conversation thread
            priority: Message priority (1-5)

        Returns:
            The created Message object
        """
        async with self._lock:
            message = Message(
                sender_id=from_agent,
                receiver_id=to_agents[0] if to_agents else None,
                recipients=to_agents,
                content=content,
                message_type=message_type,
                related_task_id=related_task_id,
                thread_id=thread_id,
                priority=priority,
            )

            # Add to graph
            self.graph.add_message(message)

            # Notify listeners
            await self._notify_listeners(message)

            logger.info(
                f"Multicast message sent: {from_agent} -> {to_agents} "
                f"[{message_type.value}]: {content[:50]}..."
            )

            return message

    def get_messages_for_agent(
        self,
        agent_id: str,
        since: datetime | None = None,
        message_types: list[MessageType] | None = None,
        related_to_task: UUID | None = None,
        limit: int | None = None,
        include_broadcasts: bool = True,
    ) -> list[Message]:
        """
        Get messages sent to a specific agent with filtering.

        Args:
            agent_id: The agent to get messages for
            since: Only return messages after this timestamp
            message_types: Only return messages of these types
            related_to_task: Only return messages related to this task
            limit: Maximum number of messages to return
            include_broadcasts: Whether to include broadcast messages

        Returns:
            List of messages sorted by timestamp (newest first)
        """
        messages = self.graph.get_messages_for_agent(
            agent_id=agent_id, since=since, message_types=message_types, limit=limit
        )

        # Additional filtering
        if related_to_task is not None:
            messages = [m for m in messages if m.related_task_id == related_to_task]

        if not include_broadcasts:
            messages = [m for m in messages if not m.is_broadcast()]

        return messages

    def get_conversation_history(
        self, agent_id: str, other_agent: str, limit: int = 50
    ) -> list[Message]:
        """
        Get conversation history between two agents.

        Args:
            agent_id: First agent ID
            other_agent: Second agent ID
            limit: Maximum number of messages to return

        Returns:
            List of messages in chronological order
        """
        return self.graph.get_conversation_history(
            agent_id=agent_id, other_agent=other_agent, limit=limit
        )

    def get_task_communications(self, task_id: UUID) -> list[Message]:
        """
        Get all communications related to a specific task.

        Args:
            task_id: The task ID to get communications for

        Returns:
            List of task-related messages sorted by timestamp
        """
        task_messages = [
            msg
            for msg in self.graph.messages.values()
            if msg.related_task_id == task_id
        ]

        # Sort by timestamp
        task_messages.sort(key=lambda m: m.timestamp)
        return task_messages

    def get_recent_broadcasts(
        self, since_minutes: int = 60, limit: int = 10
    ) -> list[Message]:
        """
        Get recent broadcast messages.

        Args:
            since_minutes: How many minutes back to look
            limit: Maximum number of broadcasts to return

        Returns:
            List of recent broadcast messages
        """
        since_time = datetime.now() - timedelta(minutes=since_minutes)

        broadcasts = [
            msg
            for msg in self.graph.messages.values()
            if msg.is_broadcast() and msg.timestamp >= since_time
        ]

        # Sort by timestamp (newest first) and apply limit
        broadcasts.sort(key=lambda m: m.timestamp, reverse=True)
        return broadcasts[:limit] if limit else broadcasts

    def get_all_messages(self) -> list[Message]:
        """
        Get all messages in the communication system.

        Useful for manager oversight and debugging/examples.

        Returns:
            List of all messages sorted by timestamp (newest first)
        """
        all_messages = list(self.graph.messages.values())
        return sorted(all_messages, key=lambda m: m.timestamp, reverse=True)

    def get_all_messages_grouped(
        self,
        grouping: MessageGrouping = MessageGrouping.BY_SENDER,
        sort_within_group: str = "time",  # "time" or "thread"
        include_broadcasts: bool = True,
    ) -> list[SenderMessagesView] | list[ThreadMessagesView]:
        """
        Return a strongly-typed view of all messages grouped by sender or thread.

        Args:
            grouping: How to group messages (by sender or by thread).
            sort_within_group: Sort messages inside each group by "time" (default) or by "thread" id.
            include_broadcasts: Whether to include broadcast messages in groups.

        Returns:
            A list of `SenderMessagesView` when grouping by sender, or a list of
            `ThreadMessagesView` when grouping by thread.
        """
        messages = list(self.graph.messages.values())
        if not include_broadcasts:
            messages = [m for m in messages if not m.is_broadcast()]

        if grouping == MessageGrouping.BY_SENDER:
            by_sender: dict[str, list[Message]] = {}
            for msg in messages:
                by_sender.setdefault(msg.sender_id, []).append(msg)

            views: list[SenderMessagesView] = []
            for sender_id, msgs in by_sender.items():
                # Sort within group
                if sort_within_group == "thread":
                    msgs.sort(
                        key=lambda m: (
                            str(m.thread_id) if m.thread_id else "",
                            m.timestamp,
                        )
                    )
                else:
                    msgs.sort(key=lambda m: m.timestamp)

                most_recent = max(msgs, key=lambda m: m.timestamp).timestamp
                views.append(
                    SenderMessagesView(
                        sender_id=sender_id,
                        total_messages=len(msgs),
                        most_recent_at=most_recent,
                        messages=msgs,
                    )
                )

            # Sort groups by most recent activity desc
            views.sort(key=lambda v: v.most_recent_at, reverse=True)
            return views

        # Grouping by thread
        by_thread: dict[str, list[Message]] = {}
        for msg in messages:
            key = str(msg.thread_id) if msg.thread_id else "NO_THREAD"
            by_thread.setdefault(key, []).append(msg)

        views_t: list[ThreadMessagesView] = []
        for key, msgs in by_thread.items():
            # Sort within group
            if sort_within_group == "thread":
                msgs.sort(
                    key=lambda m: (str(m.thread_id) if m.thread_id else "", m.timestamp)
                )
            else:
                msgs.sort(key=lambda m: m.timestamp)

            last_activity = max(msgs, key=lambda m: m.timestamp).timestamp
            thread_uuid = msgs[0].thread_id if msgs and msgs[0].thread_id else None
            thread_meta = self.graph.threads.get(thread_uuid) if thread_uuid else None
            participants: list[str] = sorted(
                list(
                    {m.sender_id for m in msgs}
                    | set.union(*[m.get_all_recipients() for m in msgs])
                    if msgs
                    else set()
                )
            )
            views_t.append(
                ThreadMessagesView(
                    thread_id=thread_uuid,
                    topic=thread_meta.topic if thread_meta else None,
                    participants=participants,
                    related_task_id=thread_meta.related_task_id
                    if thread_meta
                    else None,
                    total_messages=len(msgs),
                    last_activity=last_activity,
                    messages=msgs,
                )
            )

        # Sort groups by last activity desc; ensure NO_THREAD group comes last
        views_t.sort(key=lambda v: (v.last_activity, v.thread_id is None), reverse=True)
        return views_t

    def get_messages_grouped_by_sender(
        self,
        sort_within_group: str = "time",
        include_broadcasts: bool = True,
    ) -> list[SenderMessagesView]:
        """Typed helper: return messages grouped by sender."""
        views = self.get_all_messages_grouped(
            grouping=MessageGrouping.BY_SENDER,
            sort_within_group=sort_within_group,
            include_broadcasts=include_broadcasts,
        )
        return cast(list[SenderMessagesView], views)

    def get_manager_view(self) -> dict[str, Any]:
        """
        Get complete communication overview for manager agent.

        Provides full visibility into all communications for oversight.

        Returns:
            Dictionary containing comprehensive communication data
        """
        total_messages = len(self.graph.messages)
        active_threads = len([t for t in self.graph.threads.values() if t.is_active])

        # Recent activity summary
        recent_time = datetime.now() - timedelta(hours=1)
        recent_messages = [
            msg for msg in self.graph.messages.values() if msg.timestamp >= recent_time
        ]

        # Communication patterns
        agent_stats = {}
        for agent_id in self.graph.agent_registry:
            agent_stats[agent_id] = self.graph.get_agent_communication_stats(agent_id)

        return {
            "total_messages": total_messages,
            "active_threads": active_threads,
            "recent_messages_count": len(recent_messages),
            "known_agents": list(self.graph.agent_registry),
            "agent_statistics": agent_stats,
            "communication_edges": len(self.graph.edges),
            "recent_activity": [
                {
                    "message_id": str(msg.message_id),
                    "sender": msg.sender_id,
                    "recipient": msg.receiver_id,
                    "type": msg.message_type.value,
                    "timestamp": msg.timestamp.isoformat(),
                    "content_preview": msg.content[:100] + "..."
                    if len(msg.content) > 100
                    else msg.content,
                }
                for msg in sorted(
                    recent_messages, key=lambda m: m.timestamp, reverse=True
                )[:20]
            ],
        }

    def get_agent_view(self, agent_id: str) -> dict[str, Any]:
        """
        Get filtered communication view for a specific agent.

        Args:
            agent_id: The agent to get the view for

        Returns:
            Dictionary containing agent-specific communication data
        """
        # Get recent messages for this agent
        recent_messages = self.get_messages_for_agent(
            agent_id=agent_id, since=datetime.now() - timedelta(hours=2), limit=20
        )

        # Get agent statistics
        stats = self.graph.get_agent_communication_stats(agent_id)

        # Get active conversations
        active_conversations = {}
        for msg in recent_messages:
            if not msg.is_broadcast():
                other_agent = (
                    msg.sender_id if msg.sender_id != agent_id else msg.receiver_id
                )
                if other_agent and other_agent not in active_conversations:
                    active_conversations[other_agent] = self.get_conversation_history(
                        agent_id, other_agent, limit=5
                    )

        return {
            "agent_id": agent_id,
            "recent_messages": [
                {
                    "from": msg.sender_id,
                    "content": msg.content,
                    "type": msg.message_type.value,
                    "timestamp": msg.timestamp.isoformat(),
                    "task_id": str(msg.related_task_id)
                    if msg.related_task_id
                    else None,
                }
                for msg in recent_messages
            ],
            "statistics": stats,
            "active_conversations": {
                other_agent: [
                    {
                        "from": msg.sender_id,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat(),
                    }
                    for msg in messages
                ]
                for other_agent, messages in active_conversations.items()
            },
        }

    def mark_message_read(self, message_id: UUID, agent_id: str) -> bool:
        """
        Mark a message as read by an agent.

        Args:
            message_id: The message to mark as read
            agent_id: The agent who read the message

        Returns:
            True if successful, False if message not found
        """
        if message_id in self.graph.messages:
            self.graph.messages[message_id].mark_read_by(agent_id)
            return True
        return False

    def create_thread(
        self,
        participants: list[str],
        topic: str | None = None,
        related_task_id: UUID | None = None,
    ) -> CommunicationThread:
        """
        Create a new conversation thread.

        Args:
            participants: List of agent IDs to include in the thread
            topic: Optional topic for the thread
            related_task_id: Optional task this thread relates to

        Returns:
            The created CommunicationThread
        """
        thread = CommunicationThread(
            participants=set(participants), topic=topic, related_task_id=related_task_id
        )

        self.graph.threads[thread.thread_id] = thread

        logger.info(
            f"Created conversation thread {thread.thread_id} "
            f"with participants: {participants}"
        )

        return thread

    async def add_message_to_thread(
        self,
        thread_id: UUID,
        from_agent: str,
        to_agent: str | None,
        content: str,
        message_type: MessageType = MessageType.DIRECT,
        priority: int = 1,
    ) -> Message:
        """Add a message into an existing thread (direct to one or multicast to participants)."""
        async with self._lock:
            # If recipient omitted, default to broadcast within thread participants (excluding sender)
            recipients: list[str] | None = None
            receiver_id: str | None = None
            if to_agent is None and thread_id in self.graph.threads:
                participants = list(self.graph.threads[thread_id].participants)
                if from_agent in participants:
                    participants.remove(from_agent)
                recipients = participants
            else:
                receiver_id = to_agent

            related_task = (
                self.graph.threads[thread_id].related_task_id
                if thread_id in self.graph.threads
                else None
            )

            if not recipients:
                raise ValueError(
                    "No recipients specified for sending a message to a thread."
                )

            message = Message(
                sender_id=from_agent,
                receiver_id=receiver_id,
                recipients=recipients,
                content=content,
                message_type=message_type,
                related_task_id=related_task,
                thread_id=thread_id,
                priority=priority,
            )

            self.graph.add_message(message)
            await self._notify_listeners(message)
            logger.info(
                f"Thread message sent: {from_agent} -> {to_agent or 'thread'} [{message_type.value}]"
            )
            return message

    async def add_message_listener(
        self,
        agent_id: str,
        callback: Callable[[Message], Awaitable[None]] | Callable[[Message], None],
    ) -> None:
        """
        Add a listener for new messages to an agent.

        Args:
            agent_id: The agent to listen for messages to
            callback: Function to call when new messages arrive
        """
        if agent_id not in self._message_listeners:
            self._message_listeners[agent_id] = []

        self._message_listeners[agent_id].append(callback)
        logger.info(f"Added message listener for agent {agent_id}")

    async def _notify_listeners(self, message: Message) -> None:
        """Notify all registered listeners about a new message."""
        # Notify listeners for specific recipients
        for recipient in message.get_all_recipients():
            if recipient in self._message_listeners:
                for callback in self._message_listeners[recipient]:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(message)
                        else:
                            callback(message)
                    except Exception as e:
                        logger.error(f"Error notifying message listener: {e}")

        # Notify broadcast listeners if it's a broadcast
        if message.is_broadcast() and "BROADCAST" in self._message_listeners:
            for callback in self._message_listeners["BROADCAST"]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(message)
                    else:
                        callback(message)
                except Exception as e:
                    logger.error(f"Error notifying broadcast listener: {e}")

    def get_communication_analytics(self) -> dict[str, Any]:
        """
        Get analytics and insights about communication patterns.

        Returns:
            Dictionary containing communication analytics
        """
        total_messages = len(self.graph.messages)
        if total_messages == 0:
            return {"total_messages": 0, "analytics": "No messages to analyze"}

        # Message type distribution
        type_counts: dict[str, int] = {}
        for msg in self.graph.messages.values():
            msg_type = msg.message_type.value
            type_counts[msg_type] = type_counts.get(msg_type, 0) + 1

        # Most active agents
        agent_activity: dict[str, int] = {}
        for msg in self.graph.messages.values():
            sender = msg.sender_id
            agent_activity[sender] = agent_activity.get(sender, 0) + 1

        most_active = sorted(agent_activity.items(), key=lambda x: x[1], reverse=True)[
            :5
        ]

        # Recent activity trend (messages per hour for last 24 hours)
        now = datetime.now()
        hourly_counts = []
        for i in range(24):
            hour_start = now - timedelta(hours=i + 1)
            hour_end = now - timedelta(hours=i)
            hour_count = sum(
                1
                for msg in self.graph.messages.values()
                if hour_start <= msg.timestamp < hour_end
            )
            hourly_counts.append(hour_count)

        return {
            "total_messages": total_messages,
            "message_type_distribution": type_counts,
            "most_active_agents": most_active,
            "hourly_activity_last_24h": list(reversed(hourly_counts)),
            "total_agents": len(self.graph.agent_registry),
            "active_threads": len(
                [t for t in self.graph.threads.values() if t.is_active]
            ),
            "communication_edges": len(self.graph.edges),
        }


COMMUNICATION_SERVICE_SINGLETON = CommunicationService()
