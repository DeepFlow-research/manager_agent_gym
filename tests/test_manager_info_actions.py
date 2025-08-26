# pyright: reportMissingImports=false, reportMissingTypeStubs=false
import pytest  # type: ignore[import-not-found]
from uuid import uuid4

from manager_agent_gym.schemas.core.workflow import Workflow
from manager_agent_gym.schemas.core.tasks import Task
from manager_agent_gym.schemas.execution.manager_actions import (
    GetWorkflowStatusAction,
    GetAvailableAgentsAction,
    GetPendingTasksAction,
    SendMessageAction,
)
from manager_agent_gym.core.communication.service import CommunicationService


@pytest.mark.asyncio
async def test_info_actions_return_expected_payloads() -> None:
    w = Workflow(name="w", workflow_goal="d", owner_id=uuid4())
    t = Task(name="A", description="d")
    w.add_task(t)

    res = await GetWorkflowStatusAction(
        reasoning="r", success=True, result_summary="status"
    ).execute(w)
    assert res.kind == "info"
    assert "task_status" in res.data and "ready_task_ids" in res.data

    res2 = await GetAvailableAgentsAction(
        reasoning="r", success=True, result_summary="agents"
    ).execute(w)
    assert res2.kind == "info"
    assert "available_agent_ids" in res2.data

    res3 = await GetPendingTasksAction(
        reasoning="r", success=True, result_summary="pending"
    ).execute(w)
    assert res3.kind == "info"
    assert "pending_task_ids" in res3.data


@pytest.mark.asyncio
async def test_send_message_action_uses_communication_service() -> None:
    w = Workflow(name="w", workflow_goal="d", owner_id=uuid4())
    svc = CommunicationService()

    # Broadcast path
    res = await SendMessageAction(
        reasoning="r",
        content="hello",
        receiver_id=None,
        success=True,
        result_summary="message",
    ).execute(w, communication_service=svc)
    assert res.kind == "message"
    assert any(m.content == "hello" for m in svc.get_all_messages())

    # Direct path
    res2 = await SendMessageAction(
        reasoning="r",
        content="hi b",
        receiver_id="b",
        success=True,
        result_summary="message",
    ).execute(w, communication_service=svc)
    assert res2.kind == "message"
    assert any(
        m.content == "hi b" and m.receiver_id == "b" for m in svc.get_all_messages()
    )
