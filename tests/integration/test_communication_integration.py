from __future__ import annotations

from typing import Any, cast

import pytest

from manager_agent_gym.core.communication.service import CommunicationService
from manager_agent_gym.core.execution.engine import WorkflowExecutionEngine
from manager_agent_gym.core.workflow_agents.registry import AgentRegistry
from manager_agent_gym.schemas.config import OutputConfig
from manager_agent_gym.schemas.core.communication import (
    MessageGrouping,
    MessageType,
)
from manager_agent_gym.schemas.core.communication import ThreadMessagesView
from manager_agent_gym.schemas.execution.state import ExecutionState
from manager_agent_gym.schemas.preferences.preference import PreferenceWeights
from tests.helpers.stubs import (
    make_empty_workflow,
    ManagerSendsThenEnd,
    StakeholderStub,
)

pytestmark = pytest.mark.integration


def _mk_empty_workflow():
    return make_empty_workflow()


class _StakeholderStub(StakeholderStub):
    pass


class _ManagerSendsThenEnd(ManagerSendsThenEnd):
    pass


@pytest.mark.integration
@pytest.mark.asyncio
async def test_manager_to_stakeholder_direct_and_stakeholder_reply_and_broadcast_in_engine(
    tmp_path: Any,
) -> None:
    workflow = _mk_empty_workflow()
    registry = AgentRegistry()
    comms = CommunicationService()
    stakeholder = _StakeholderStub(agent_id="stakeholder_1")
    manager = _ManagerSendsThenEnd(
        preferences=PreferenceWeights(preferences=[]), receiver_id="stakeholder_1"
    )

    engine = WorkflowExecutionEngine(
        workflow=workflow,
        agent_registry=registry,
        stakeholder_agent=stakeholder,
        manager_agent=manager,
        communication_service=comms,
        output_config=OutputConfig(
            base_output_dir=tmp_path, run_id="comm_test", create_run_subdirectory=True
        ),
        max_timesteps=5,
        enable_timestep_logging=False,
        enable_final_metrics_logging=False,
        evaluations=[],
        seed=0,
        timestep_end_callbacks=[],
    )

    results = await engine.run_full_execution()

    # Engine should end via cancel (request_end_workflow) or complete
    assert engine.execution_state in {
        ExecutionState.CANCELLED,
        ExecutionState.COMPLETED,
    }
    assert len(results) >= 1

    # Direct message present
    history = comms.get_conversation_history("manager_agent", "stakeholder_1", limit=10)
    contents = [m.content for m in history]
    assert "hello_stakeholder" in contents
    # Stakeholder reply present
    assert any(c.startswith("ack_t") for c in contents)

    # Broadcast present and visible to manager (sender excluded by service)
    broadcasts = [m for m in comms.get_all_messages() if m.is_broadcast()]
    assert any("broadcast_t" in m.content for m in broadcasts)
    # Manager inbox should include at least one broadcast
    manager_inbox = comms.get_messages_for_agent(
        agent_id="manager_agent", include_broadcasts=True
    )
    assert any(m.is_broadcast() and "broadcast_t" in m.content for m in manager_inbox)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_thread_multicast_and_grouping() -> None:
    svc = CommunicationService()
    # Seed registry
    await svc.send_direct_message("a", "b", "hi")

    thread = svc.create_thread(participants=["a", "b", "c"], topic="coord")
    msg = await svc.add_message_to_thread(
        thread_id=thread.thread_id,
        from_agent="a",
        to_agent=None,
        content="sync",
        message_type=MessageType.DIRECT,
    )

    assert set(msg.recipients) == {"b", "c"}
    views_u = svc.get_all_messages_grouped(grouping=MessageGrouping.BY_THREAD)
    views_t = cast(list[ThreadMessagesView], views_u)
    assert any(
        v.thread_id == thread.thread_id and v.total_messages >= 1 for v in views_t
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_mark_message_read_and_agent_view() -> None:
    svc = CommunicationService()
    m = await svc.send_direct_message("x", "y", "please read")
    ok = svc.mark_message_read(message_id=m.message_id, agent_id="y")
    assert ok is True
    stored = svc.graph.messages[m.message_id]
    assert "y" in stored.read_by
    agent_view = svc.get_agent_view("y")
    assert agent_view["agent_id"] == "y"
    assert any(item.get("from") == "x" for item in agent_view["recent_messages"])
