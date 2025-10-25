"""
Tests for thread-based parallel rubric generation.

Verifies that thread isolation prevents message contamination between
parallel rubric generation variants.
"""

import pytest
from uuid import uuid4

from manager_agent_gym.core.communication.service import CommunicationService


class TestThreadIsolation:
    """Test thread-based message isolation."""

    @pytest.mark.asyncio
    async def test_messages_isolated_by_thread(self):
        """Verify messages in different threads don't contaminate each other."""
        comm_service = CommunicationService()

        thread_1 = uuid4()
        thread_2 = uuid4()

        # Variant 1 sends message
        msg1 = await comm_service.send_direct_message(
            from_agent="manager",
            to_agent="stakeholder",
            content="Question for variant 1",
            thread_id=thread_1,
        )

        # Variant 2 sends message
        msg2 = await comm_service.send_direct_message(
            from_agent="manager",
            to_agent="stakeholder",
            content="Question for variant 2",
            thread_id=thread_2,
        )

        # Verify thread 1 only sees its message
        thread_1_msgs = comm_service.get_messages_in_thread(thread_1)
        assert len(thread_1_msgs) == 1
        assert thread_1_msgs[0].content == "Question for variant 1"
        assert thread_1_msgs[0].thread_id == thread_1

        # Verify thread 2 only sees its message
        thread_2_msgs = comm_service.get_messages_in_thread(thread_2)
        assert len(thread_2_msgs) == 1
        assert thread_2_msgs[0].content == "Question for variant 2"
        assert thread_2_msgs[0].thread_id == thread_2

    @pytest.mark.asyncio
    async def test_conversation_history_scoped_to_thread(self):
        """Verify conversation history is correctly scoped to threads."""
        comm_service = CommunicationService()

        thread_1 = uuid4()
        thread_2 = uuid4()

        # Thread 1: manager asks, stakeholder responds
        await comm_service.send_direct_message(
            from_agent="manager",
            to_agent="stakeholder",
            content="Q1 in thread 1",
            thread_id=thread_1,
        )
        await comm_service.send_direct_message(
            from_agent="stakeholder",
            to_agent="manager",
            content="A1 in thread 1",
            thread_id=thread_1,
        )

        # Thread 2: manager asks, stakeholder responds
        await comm_service.send_direct_message(
            from_agent="manager",
            to_agent="stakeholder",
            content="Q1 in thread 2",
            thread_id=thread_2,
        )
        await comm_service.send_direct_message(
            from_agent="stakeholder",
            to_agent="manager",
            content="A1 in thread 2",
            thread_id=thread_2,
        )

        # Thread 1 should only see its 2 messages
        thread_1_conversation = comm_service.get_conversation_history_in_thread(
            thread_id=thread_1,
            agent_id="manager",
            other_agent="stakeholder",
        )
        assert len(thread_1_conversation) == 2
        assert all(msg.thread_id == thread_1 for msg in thread_1_conversation)
        assert thread_1_conversation[0].content == "Q1 in thread 1"
        assert thread_1_conversation[1].content == "A1 in thread 1"

        # Thread 2 should only see its 2 messages
        thread_2_conversation = comm_service.get_conversation_history_in_thread(
            thread_id=thread_2,
            agent_id="manager",
            other_agent="stakeholder",
        )
        assert len(thread_2_conversation) == 2
        assert all(msg.thread_id == thread_2 for msg in thread_2_conversation)
        assert thread_2_conversation[0].content == "Q1 in thread 2"
        assert thread_2_conversation[1].content == "A1 in thread 2"

    @pytest.mark.asyncio
    async def test_no_cross_contamination_with_many_threads(self):
        """Verify no contamination even with many concurrent threads."""
        comm_service = CommunicationService()

        # Create 10 threads with unique messages
        threads = [uuid4() for _ in range(10)]

        for i, thread_id in enumerate(threads):
            await comm_service.send_direct_message(
                from_agent="manager",
                to_agent="stakeholder",
                content=f"Message from variant {i}",
                thread_id=thread_id,
            )

        # Verify each thread only sees its own message
        for i, thread_id in enumerate(threads):
            thread_msgs = comm_service.get_messages_in_thread(thread_id)
            assert len(thread_msgs) == 1, f"Thread {i} should have exactly 1 message"
            assert thread_msgs[0].content == f"Message from variant {i}", (
                f"Thread {i} has wrong message"
            )

    @pytest.mark.asyncio
    async def test_messages_without_thread_not_in_thread_queries(self):
        """Verify messages without thread_id don't appear in thread-scoped queries."""
        comm_service = CommunicationService()

        thread_id = uuid4()

        # Send message WITHOUT thread_id (global message)
        await comm_service.send_direct_message(
            from_agent="manager",
            to_agent="stakeholder",
            content="Global message",
            thread_id=None,
        )

        # Send message WITH thread_id
        await comm_service.send_direct_message(
            from_agent="manager",
            to_agent="stakeholder",
            content="Threaded message",
            thread_id=thread_id,
        )

        # Thread query should only see threaded message
        thread_msgs = comm_service.get_messages_in_thread(thread_id)
        assert len(thread_msgs) == 1
        assert thread_msgs[0].content == "Threaded message"

        # Global query should see both
        all_msgs = comm_service.get_conversation_history(
            agent_id="manager",
            other_agent="stakeholder",
        )
        assert len(all_msgs) == 2

    @pytest.mark.asyncio
    async def test_thread_scoped_conversation_with_limit(self):
        """Verify limit works correctly with thread-scoped queries."""
        comm_service = CommunicationService()

        thread_id = uuid4()

        # Send 10 messages in thread
        for i in range(10):
            await comm_service.send_direct_message(
                from_agent="manager",
                to_agent="stakeholder",
                content=f"Message {i}",
                thread_id=thread_id,
            )

        # Query with limit=5 should return 5 most recent
        limited_msgs = comm_service.get_conversation_history_in_thread(
            thread_id=thread_id,
            agent_id="manager",
            other_agent="stakeholder",
            limit=5,
        )
        assert len(limited_msgs) == 5
        # Should be messages 5-9 (most recent)
        assert limited_msgs[0].content == "Message 5"
        assert limited_msgs[4].content == "Message 9"


class TestBackwardCompatibility:
    """Test that thread-less queries still work (backward compatibility)."""

    @pytest.mark.asyncio
    async def test_global_conversation_history_without_threads(self):
        """Verify old code path works when no threads are used."""
        comm_service = CommunicationService()

        # Send messages WITHOUT thread_id (old behavior)
        await comm_service.send_direct_message(
            from_agent="manager",
            to_agent="stakeholder",
            content="Q1",
        )
        await comm_service.send_direct_message(
            from_agent="stakeholder",
            to_agent="manager",
            content="A1",
        )

        # Old get_conversation_history should work
        conversation = comm_service.get_conversation_history(
            agent_id="manager",
            other_agent="stakeholder",
        )
        assert len(conversation) == 2
        assert conversation[0].content == "Q1"
        assert conversation[1].content == "A1"

    @pytest.mark.asyncio
    async def test_mixed_threaded_and_global_messages(self):
        """Verify global queries see all messages, thread queries see only threaded."""
        comm_service = CommunicationService()

        thread_id = uuid4()

        # Mix of global and threaded messages
        await comm_service.send_direct_message(
            from_agent="manager",
            to_agent="stakeholder",
            content="Global 1",
            thread_id=None,
        )
        await comm_service.send_direct_message(
            from_agent="manager",
            to_agent="stakeholder",
            content="Threaded 1",
            thread_id=thread_id,
        )
        await comm_service.send_direct_message(
            from_agent="manager",
            to_agent="stakeholder",
            content="Global 2",
            thread_id=None,
        )

        # Global query sees all 3
        global_msgs = comm_service.get_conversation_history(
            agent_id="manager",
            other_agent="stakeholder",
        )
        assert len(global_msgs) == 3

        # Thread query sees only 1
        thread_msgs = comm_service.get_conversation_history_in_thread(
            thread_id=thread_id,
            agent_id="manager",
            other_agent="stakeholder",
        )
        assert len(thread_msgs) == 1
        assert thread_msgs[0].content == "Threaded 1"
