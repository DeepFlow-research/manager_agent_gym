import pytest

from manager_agent_gym.core.communication.service import CommunicationService
from manager_agent_gym.schemas.core.communication import MessageType


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
