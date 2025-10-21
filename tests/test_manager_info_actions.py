# pyright: reportMissingImports=false, reportMissingTypeStubs=false
import pytest  # type: ignore[import-not-found]
from uuid import uuid4

from manager_agent_gym.schemas.domain.workflow import Workflow
from manager_agent_gym.schemas.domain.task import Task
from manager_agent_gym.core.agents.manager_agent.actions import (
    GetWorkflowStatusAction,
    GetAvailableAgentsAction,
    GetPendingTasksAction,
    SendMessageAction,
)
from manager_agent_gym.core.workflow.services import WorkflowMutations
from manager_agent_gym.core.communication.service import CommunicationService


@pytest.mark.asyncio
async def test_info_actions_return_expected_payloads() -> None:
    # Build a small workflow with dependency so READY reflects correct logic
    w = Workflow(name="w", workflow_goal="d", owner_id=uuid4())
    a = Task(name="A", description="d")
    b = Task(name="B", description="d", dependency_task_ids=[a.id])
    WorkflowMutations.add_task(w, a)
    WorkflowMutations.add_task(w, b)

    # Initially: A is READY, B is PENDING
    status_res = await GetWorkflowStatusAction(
        reasoning="r", success=True, result_summary="status"
    ).execute(w)
    assert status_res.kind == "info"
    data = status_res.data
    # task_status counts include pending/ready; ready list contains A only
    assert isinstance(data.get("task_status"), dict)
    ready_ids = set(data.get("ready_task_ids", []))
    assert str(a.id) in ready_ids and str(b.id) not in ready_ids

    # No agents registered: available list is empty for status and GetAvailableAgentsAction
    agents_res = await GetAvailableAgentsAction(
        reasoning="r", success=True, result_summary="agents"
    ).execute(w)
    assert agents_res.kind == "info"
    assert agents_res.data.get("available_agent_ids") == []

    # Pending tasks should include only B before any assignment/start (A is READY)
    pending_res = await GetPendingTasksAction(
        reasoning="r", success=True, result_summary="pending"
    ).execute(w)
    assert pending_res.kind == "info"
    pend = set(pending_res.data.get("pending_task_ids", []))
    assert pend == {str(b.id)}


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
