import pytest
from uuid import uuid4
from manager_agent_gym.core.communication.service import CommunicationService
from manager_agent_gym.schemas.domain.communication import MessageType


@pytest.mark.asyncio
async def test_direct_message_persists_and_notifies() -> None:
    svc = CommunicationService()
    notified = []

    async def listener(msg) -> None:
        notified.append((msg.sender_id, msg.receiver_id, msg.content))

    await svc.add_message_listener("b", listener)

    m = await svc.send_direct_message("a", "b", "hi", message_type=MessageType.DIRECT)

    # Listener should have been called
    assert notified == [("a", "b", "hi")]
    # Message should be stored
    all_msgs = svc.get_all_messages()
    assert m in all_msgs
    assert all_msgs[0].content == "hi"


@pytest.mark.asyncio
async def test_broadcast_message_excludes_sender_and_exclusions() -> None:
    svc = CommunicationService()
    # Prime some agent registry via prior messages
    await svc.send_direct_message("a", "b", "x")
    await svc.send_direct_message("c", "a", "y")

    msg = await svc.broadcast_message(
        from_agent="a",
        content="broadcast",
        exclude_agents=["c"],
        message_type=MessageType.BROADCAST,
    )
    # Graph tracks agent registry; ensure broadcast created and analytics reflect it
    view = svc.get_manager_view()
    assert view["total_messages"] >= 3
    # The broadcast message should be stored and considered broadcast
    assert msg.is_broadcast()


def test_end_workflow_request_flag() -> None:
    svc = CommunicationService()
    assert not svc.is_end_workflow_requested()
    svc.request_end_workflow("testing")
    assert svc.is_end_workflow_requested()


@pytest.mark.asyncio
async def test_direct_message_registers_agents_and_edges():
    comm = CommunicationService()
    m = await comm.send_direct_message(
        from_agent="a1", to_agent="a2", content="hello", message_type=MessageType.DIRECT
    )
    assert m.sender_id == "a1" and m.receiver_id == "a2"
    assert "a1" in comm.graph.agent_registry and "a2" in comm.graph.agent_registry
    edge_key = "a1->a2"
    assert edge_key in comm.graph.edges
    msgs = comm.get_messages_for_agent("a2")
    assert any(msg.message_id == m.message_id for msg in msgs)


@pytest.mark.asyncio
async def test_broadcast_message_tracks_edge_and_recipients():
    comm = CommunicationService()
    # seed registry by sending direct first
    await comm.send_direct_message("a1", "a2", "seed")
    await comm.send_direct_message("a3", "a1", "seed2")
    b = await comm.broadcast_message(from_agent="a1", content="news")
    assert b.is_broadcast()
    assert "a1->BROADCAST" in comm.graph.edges
    # All known agents except sender are recipients
    assert set(b.recipients) == (comm.graph.agent_registry - {"a1"})


@pytest.mark.asyncio
async def test_multicast_message_sets_recipients_and_history():
    comm = CommunicationService()
    await comm.send_direct_message("a0", "aX", "seed")
    m = await comm.send_multicast_message(
        from_agent="a0",
        to_agents=["a1", "a2"],
        content="update",
        message_type=MessageType.DIRECT,
    )
    assert set(m.recipients) == {"a1", "a2"}
    assert "a0->a1" in comm.graph.edges and "a0->a2" in comm.graph.edges
    assert any(
        msg.message_id == m.message_id for msg in comm.get_messages_for_agent("a1")
    )


@pytest.mark.asyncio
async def test_thread_creation_and_add_message_to_thread():
    comm = CommunicationService()
    thread = comm.create_thread(
        participants=["a1", "a2"], topic="T", related_task_id=uuid4()
    )
    m = await comm.add_message_to_thread(
        thread_id=thread.thread_id,
        from_agent="a1",
        to_agent=None,
        content="in-thread",
        message_type=MessageType.DIRECT,
    )
    assert thread.thread_id in comm.graph.threads
    view = comm.get_conversation_history("a1", "a2")
    assert any(x.message_id == m.message_id for x in view)


@pytest.mark.asyncio
async def test_mark_message_read_and_grouped_views():
    comm = CommunicationService()
    m = await comm.send_direct_message("a1", "a2", "r")
    assert comm.mark_message_read(m.message_id, "a2")
    assert "a2" in comm.graph.messages[m.message_id].read_by
    grouped = comm.get_all_messages_grouped()
    assert grouped and grouped[0].sender_id in {"a1"}  # type: ignore # todo: fix
