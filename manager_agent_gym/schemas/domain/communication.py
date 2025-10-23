"""
Communication data models for Manager Agent Gym.

This module implements the communication component (C) from the POSG state model
described in the paper, enabling graph-based message storage and agent coordination.
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4, UUID

from pydantic import BaseModel, Field, field_validator


class MessageType(str, Enum):
    """Types of messages that can be sent between agents."""

    DIRECT = "direct"  # 1:1 communication between agents
    BROADCAST = "broadcast"  # 1:many announcement to all agents
    REQUEST = "request"  # Request for action/information
    RESPONSE = "response"  # Response to a request
    ALERT = "alert"  # System alerts and notifications
    STATUS_UPDATE = "status_update"  # Progress and status updates
    RUBRIC_UPDATE = "rubric_update"  # Rubric/evaluation criteria distribution (STICKY)
    GENERAL = "general"  # General communication (backward compatibility)


# Sticky message types: delivered to ALL agents regardless of when they join
# or whether they were in the original recipient list
STICKY_MESSAGE_TYPES = {MessageType.RUBRIC_UPDATE}


class CommunicationThread(BaseModel):
    """
    A conversation thread between multiple agents.

    Threads help organize related messages and maintain conversation context.
    """

    thread_id: UUID = Field(default_factory=uuid4)
    participants: set[str] = Field(
        default_factory=set, description="Set of agent IDs participating in this thread"
    )
    topic: str | None = Field(
        default=None, description="Optional topic or subject of the conversation"
    )
    related_task_id: UUID | None = Field(
        default=None, description="Task this thread is related to, if any"
    )
    created_at: datetime = Field(default_factory=datetime.now)
    last_activity: datetime = Field(default_factory=datetime.now)
    is_active: bool = Field(default=True)

    def add_participant(self, agent_id: str) -> None:
        """Add a new participant to the thread."""
        self.participants.add(agent_id)
        self.last_activity = datetime.now()

    def update_activity(self) -> None:
        """Update the last activity timestamp."""
        self.last_activity = datetime.now()


class Message(BaseModel):
    """
    A communication message in the system.

    Messages form part of the communication history (C in the POSG state).
    Enhanced with thread support, multiple recipients, and read tracking.
    """

    message_id: UUID = Field(default_factory=uuid4, description="Unique message ID")
    sender_id: str = Field(..., description="ID of the sender (agent or manager)")
    receiver_id: str | None = Field(
        default=None, description="Primary receiver ID, None for broadcast"
    )
    recipients: list[str] = Field(
        default_factory=list,
        description="List of recipient agent IDs (for multi-cast messages)",
    )
    content: str = Field(
        ...,
        description="Message content body (avoid PII in shared environments)",
        examples=["Kickoff in 5 minutes"],
    )
    message_type: MessageType = Field(
        default=MessageType.GENERAL,
        description="Type of message for categorization and filtering",
    )
    timestamp: datetime = Field(default_factory=datetime.now, description="Send time")

    # Thread and conversation context
    thread_id: UUID | None = Field(
        default=None, description="Thread this message belongs to"
    )
    parent_message_id: UUID | None = Field(
        default=None, description="Message this is replying to"
    )

    # Task and workflow context
    related_task_id: UUID | None = Field(
        default=None, description="Task this message is related to"
    )

    # Message metadata and tracking
    priority: int = Field(
        default=1, ge=1, le=5, description="Message priority (1=low, 5=critical)"
    )
    read_by: dict[str, datetime] = Field(
        default_factory=dict,
        description="Tracking of when each recipient read the message",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata for the message"
    )

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate message content is not empty."""
        if not v or not v.strip():
            raise ValueError("Message content cannot be empty")
        return v.strip()

    @field_validator("recipients")
    @classmethod
    def validate_recipients(cls, v: list[str]) -> list[str]:
        """Ensure recipient list has unique values."""
        return list(set(v)) if v else []

    def mark_read_by(self, agent_id: str) -> None:
        """Mark this message as read by an agent."""
        self.read_by[agent_id] = datetime.now()

    def is_broadcast(self) -> bool:
        """Check if this is a broadcast message."""
        return self.message_type == MessageType.BROADCAST or self.receiver_id is None

    def get_all_recipients(self) -> set[str]:
        """Get all recipients including primary receiver."""
        recipients = set(self.recipients)
        if self.receiver_id:
            recipients.add(self.receiver_id)
        return recipients


class CommunicationEdge(BaseModel):
    """
    An edge in the communication graph representing interaction between two agents.

    Tracks communication patterns and frequency between agent pairs.
    """

    from_agent: str = Field(..., description="Source agent ID")
    to_agent: str | None = Field(
        default=None, description="Target agent ID, None for broadcast edges"
    )
    message_count: int = Field(
        default=0, description="Total number of messages sent along this edge"
    )
    last_communication: datetime | None = Field(
        default=None, description="Timestamp of the most recent message"
    )
    communication_frequency: float = Field(
        default=0.0, description="Messages per hour (rolling average)"
    )
    message_types: dict[MessageType, int] = Field(
        default_factory=dict,
        description="Count of each message type sent along this edge",
    )

    def update_for_message(self, message: Message) -> None:
        """Update edge statistics when a new message is sent."""
        self.message_count += 1
        self.last_communication = message.timestamp

        # Update message type counts
        if message.message_type not in self.message_types:
            self.message_types[message.message_type] = 0
        self.message_types[message.message_type] += 1

    def get_edge_key(self) -> str:
        """Get a unique key for this edge."""
        return f"{self.from_agent}->{self.to_agent or 'BROADCAST'}"


class CommunicationGraph(BaseModel):
    """
    Graph representation of all communications in the system.

    Implements the communication component (C) from the POSG state model,
    storing message relationships and enabling communication pattern analysis.
    """

    edges: dict[str, CommunicationEdge] = Field(
        default_factory=dict, description="Communication edges indexed by edge key"
    )
    threads: dict[UUID, CommunicationThread] = Field(
        default_factory=dict, description="Active conversation threads"
    )
    messages: dict[UUID, Message] = Field(
        default_factory=dict, description="All messages indexed by message ID"
    )
    agent_registry: set[str] = Field(
        default_factory=set, description="Set of all known agent IDs"
    )

    def add_message(self, message: Message) -> None:
        """
        Add a message to the graph and update all related structures.

        Args:
            message: The message to add to the graph
        """
        # Store the message
        self.messages[message.message_id] = message

        # Register agents
        self.agent_registry.add(message.sender_id)
        for recipient in message.get_all_recipients():
            self.agent_registry.add(recipient)

        # Update or create edges
        if message.is_broadcast():
            self._update_broadcast_edge(message)
        else:
            for recipient in message.get_all_recipients():
                self._update_direct_edge(message, recipient)

        # Update thread if applicable
        if message.thread_id:
            self._update_thread(message)

    def _update_direct_edge(self, message: Message, recipient: str) -> None:
        """Update a direct communication edge."""
        edge_key = f"{message.sender_id}->{recipient}"

        if edge_key not in self.edges:
            self.edges[edge_key] = CommunicationEdge(
                from_agent=message.sender_id, to_agent=recipient
            )

        self.edges[edge_key].update_for_message(message)

    def _update_broadcast_edge(self, message: Message) -> None:
        """Update a broadcast communication edge."""
        edge_key = f"{message.sender_id}->BROADCAST"

        if edge_key not in self.edges:
            self.edges[edge_key] = CommunicationEdge(
                from_agent=message.sender_id, to_agent=None
            )

        self.edges[edge_key].update_for_message(message)

    def _update_thread(self, message: Message) -> None:
        """Update thread information for a message."""
        if message.thread_id is None:
            return

        if message.thread_id not in self.threads:
            # Create new thread
            self.threads[message.thread_id] = CommunicationThread(
                thread_id=message.thread_id, related_task_id=message.related_task_id
            )

        thread = self.threads[message.thread_id]
        thread.add_participant(message.sender_id)
        for recipient in message.get_all_recipients():
            thread.add_participant(recipient)
        thread.update_activity()

    def get_messages_for_agent(
        self,
        agent_id: str,
        since: datetime | None = None,
        message_types: list[MessageType] | None = None,
        limit: int | None = None,
    ) -> list[Message]:
        """
        Get messages sent to a specific agent with optional filtering.

        Sticky message types (RUBRIC_UPDATE) are delivered to ALL agents regardless
        of when they joined or whether they were in the original recipient list.

        Args:
            agent_id: The agent to get messages for
            since: Only return messages after this timestamp
            message_types: Only return messages of these types
            limit: Maximum number of messages to return

        Returns:
            List of messages sorted by timestamp (newest first)
        """
        relevant_messages = []

        for message in self.messages.values():
            # Check if message is for this agent:
            # 1. Agent is explicitly in recipients OR it's a broadcast
            # 2. OR it's a sticky message type (delivered to all agents)
            is_addressed_to_agent = (
                agent_id in message.get_all_recipients() or message.is_broadcast()
            )
            is_sticky_message = message.message_type in STICKY_MESSAGE_TYPES

            if not (is_addressed_to_agent or is_sticky_message):
                continue

            # Apply time filter
            if since and message.timestamp < since:
                continue

            # Apply message type filter
            if message_types and message.message_type not in message_types:
                continue

            relevant_messages.append(message)

        # Sort by timestamp (newest first)
        relevant_messages.sort(key=lambda m: m.timestamp, reverse=True)

        # Apply limit
        if limit:
            relevant_messages = relevant_messages[:limit]

        return relevant_messages

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
        conversation = []

        for message in self.messages.values():
            # Check if message is between these two agents
            sender = message.sender_id
            recipients = message.get_all_recipients()

            if (sender == agent_id and other_agent in recipients) or (
                sender == other_agent and agent_id in recipients
            ):
                conversation.append(message)

        # Sort chronologically and apply limit
        conversation.sort(key=lambda m: m.timestamp)
        return conversation[-limit:] if limit else conversation

    def get_agent_communication_stats(self, agent_id: str) -> dict[str, Any]:
        """Get communication statistics for an agent."""
        sent_count = sum(
            1 for msg in self.messages.values() if msg.sender_id == agent_id
        )
        received_count = sum(
            1
            for msg in self.messages.values()
            if agent_id in msg.get_all_recipients() or msg.is_broadcast()
        )

        return {
            "messages_sent": sent_count,
            "messages_received": received_count,
            "communication_partners": len(
                [
                    edge
                    for edge in self.edges.values()
                    if edge.from_agent == agent_id or edge.to_agent == agent_id
                ]
            ),
            "active_threads": len(
                [
                    thread
                    for thread in self.threads.values()
                    if agent_id in thread.participants and thread.is_active
                ]
            ),
        }


# Strongly-typed grouped message views


class MessageGrouping(str, Enum):
    """Grouping options for message views."""

    BY_SENDER = "sender"
    BY_THREAD = "thread"


class SenderMessagesView(BaseModel):
    """Messages grouped by the sending agent."""

    sender_id: str
    total_messages: int
    most_recent_at: datetime
    messages: list[Message]


class ThreadMessagesView(BaseModel):
    """Messages grouped by thread."""

    thread_id: UUID | None
    topic: str | None = None
    participants: list[str] = Field(default_factory=list)
    related_task_id: UUID | None = None
    total_messages: int
    last_activity: datetime
    messages: list[Message]
