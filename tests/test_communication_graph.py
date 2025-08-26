import pytest

from manager_agent_gym.core.communication.service import CommunicationService
from manager_agent_gym.schemas.core.communication import MessageType


@pytest.mark.asyncio
async def test_multicast_threads_and_read_tracking() -> None:
    svc = CommunicationService()

    # Direct messages to seed agent registry
    await svc.send_direct_message("a", "b", "hello b")
    await svc.send_direct_message("b", "a", "hi a")

    # Multicast
    await svc.send_multicast_message(
        "a", ["b", "c"], "group ping", message_type=MessageType.REQUEST
    )

    # Thread
    thread = svc.create_thread(["a", "b"], topic="ops")
    # Broadcast within thread (recipients derived from thread participants minus sender)
    await svc.add_message_to_thread(thread.thread_id, "a", None, "in thread")

    # Read tracking via view
    view_a = svc.get_agent_view("a")
    assert view_a["agent_id"] == "a"
    assert "recent_messages" in view_a

    # Analytics sanity
    analytics = svc.get_communication_analytics()
    assert analytics["total_messages"] >= 3
