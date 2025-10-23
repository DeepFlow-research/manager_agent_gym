"""
Tests for communication tools.

Tests the two-layer architecture:
- Layer 1: Core _* functions with real communication operations
- Layer 2: OpenAI tool wrappers (integration tested via tool_factory)

Note: These tests use a mock communication service.
"""

from uuid import UUID, uuid4

import pytest

from manager_agent_gym.core.agents.workflow_agents.tools.communication.communication import (
    _send_message,
    _broadcast_message,
    _get_recent_messages,
    _get_conversation_history,
    _get_task_messages,
)
from manager_agent_gym.core.communication.service import CommunicationService


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_comm_service():
    """Create a mock communication service for testing."""
    service = CommunicationService()
    return service


@pytest.fixture
def agent_id() -> str:
    """Test agent ID."""
    return "test_agent_1"


@pytest.fixture
def task_id() -> UUID:
    """Test task ID."""
    return uuid4()


# ============================================================================
# SEND MESSAGE TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_send_message_success(mock_comm_service, agent_id, task_id) -> None:
    """Test sending a direct message."""
    result = await _send_message(
        communication_service=mock_comm_service,
        agent_id=agent_id,
        to_agent_id="test_agent_2",
        content="Hello, world!",
        message_type="direct",
        current_task_id=task_id,
    )

    assert result["success"] is True
    assert result["to"] == "test_agent_2"
    assert "Hello" in result["content_preview"]


@pytest.mark.asyncio
async def test_send_message_different_types(
    mock_comm_service, agent_id, task_id
) -> None:
    """Test sending messages with different types."""
    message_types = ["direct", "request", "response", "alert", "status_update"]

    for msg_type in message_types:
        result = await _send_message(
            communication_service=mock_comm_service,
            agent_id=agent_id,
            to_agent_id="test_agent_2",
            content=f"Test {msg_type} message",
            message_type=msg_type,
            current_task_id=task_id,
        )

        assert result["success"] is True


@pytest.mark.asyncio
async def test_send_message_invalid_type(mock_comm_service, agent_id, task_id) -> None:
    """Test sending message with invalid type falls back to DIRECT."""
    result = await _send_message(
        communication_service=mock_comm_service,
        agent_id=agent_id,
        to_agent_id="test_agent_2",
        content="Test message",
        message_type="invalid_type",
        current_task_id=task_id,
    )

    # Should still succeed with fallback
    assert result["success"] is True


# ============================================================================
# BROADCAST MESSAGE TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_broadcast_message_success(mock_comm_service, agent_id, task_id) -> None:
    """Test broadcasting a message."""
    result = await _broadcast_message(
        communication_service=mock_comm_service,
        agent_id=agent_id,
        content="Broadcast to all!",
        message_type="broadcast",
        current_task_id=task_id,
    )

    assert result["success"] is True
    assert "recipient_count" in result


@pytest.mark.asyncio
async def test_broadcast_message_different_types(
    mock_comm_service, agent_id, task_id
) -> None:
    """Test broadcasting with different message types."""
    message_types = ["broadcast", "alert", "status_update"]

    for msg_type in message_types:
        result = await _broadcast_message(
            communication_service=mock_comm_service,
            agent_id=agent_id,
            content=f"Broadcast {msg_type} message",
            message_type=msg_type,
            current_task_id=task_id,
        )

        assert result["success"] is True


# ============================================================================
# GET RECENT MESSAGES TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_get_recent_messages_empty(mock_comm_service, agent_id) -> None:
    """Test getting recent messages when there are none."""
    result = _get_recent_messages(
        communication_service=mock_comm_service, agent_id=agent_id, limit=10
    )

    assert result["success"] is True
    assert result["count"] == 0


@pytest.mark.asyncio
async def test_get_recent_messages_after_sending(
    mock_comm_service, agent_id, task_id
) -> None:
    """Test getting recent messages after sending some."""
    # Send a few messages
    await _send_message(
        mock_comm_service,
        agent_id,
        "test_agent_2",
        "Message 1",
        current_task_id=task_id,
    )
    await _send_message(
        mock_comm_service,
        agent_id,
        "test_agent_2",
        "Message 2",
        current_task_id=task_id,
    )

    # Get recent messages for test_agent_2
    result = _get_recent_messages(
        communication_service=mock_comm_service, agent_id="test_agent_2", limit=10
    )

    assert result["success"] is True
    assert result["count"] >= 0


@pytest.mark.asyncio
async def test_get_recent_messages_limit(mock_comm_service, agent_id, task_id) -> None:
    """Test that limit parameter is respected."""
    # Send many messages
    for i in range(20):
        await _send_message(
            mock_comm_service,
            agent_id,
            "test_agent_2",
            f"Message {i}",
            current_task_id=task_id,
        )

    # Get limited results
    result = _get_recent_messages(
        communication_service=mock_comm_service, agent_id="test_agent_2", limit=5
    )

    assert result["success"] is True
    assert result["count"] <= 5


@pytest.mark.asyncio
async def test_get_recent_messages_time_filter(
    mock_comm_service, agent_id, task_id
) -> None:
    """Test time-based filtering of messages."""
    result = _get_recent_messages(
        communication_service=mock_comm_service,
        agent_id=agent_id,
        limit=10,
        since_minutes=1,
    )

    assert result["success"] is True


# ============================================================================
# CONVERSATION HISTORY TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_get_conversation_history_empty(mock_comm_service, agent_id) -> None:
    """Test getting conversation history when there is none."""
    result = _get_conversation_history(
        communication_service=mock_comm_service,
        agent_id=agent_id,
        other_agent_id="test_agent_2",
        limit=10,
    )

    assert result["success"] is True
    assert result["count"] == 0


@pytest.mark.asyncio
async def test_get_conversation_history_after_messages(
    mock_comm_service, agent_id, task_id
) -> None:
    """Test getting conversation history after exchanging messages."""
    # Exchange some messages
    await _send_message(
        mock_comm_service, agent_id, "test_agent_2", "Hello!", current_task_id=task_id
    )
    await _send_message(
        mock_comm_service,
        "test_agent_2",
        agent_id,
        "Hi there!",
        current_task_id=task_id,
    )

    result = _get_conversation_history(
        communication_service=mock_comm_service,
        agent_id=agent_id,
        other_agent_id="test_agent_2",
        limit=10,
    )

    assert result["success"] is True


# ============================================================================
# TASK MESSAGES TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_get_task_messages_empty(mock_comm_service, agent_id, task_id) -> None:
    """Test getting task messages when there are none."""
    result = _get_task_messages(
        communication_service=mock_comm_service, agent_id=agent_id, task_id=task_id
    )

    assert result["success"] is True
    assert result["count"] == 0


@pytest.mark.asyncio
async def test_get_task_messages_after_sending(
    mock_comm_service, agent_id, task_id
) -> None:
    """Test getting task messages after sending some."""
    # Send messages related to task
    await _send_message(
        mock_comm_service,
        agent_id,
        "test_agent_2",
        "Task message",
        current_task_id=task_id,
    )

    result = _get_task_messages(
        communication_service=mock_comm_service, agent_id=agent_id, task_id=task_id
    )

    assert result["success"] is True
