import pytest
from uuid import uuid4

from manager_agent_gym.schemas.core.workflow import Workflow
from manager_agent_gym.schemas.core.tasks import Task
from manager_agent_gym.core.workflow_agents.interface import AgentInterface
from manager_agent_gym.schemas.workflow_agents import AgentConfig
from manager_agent_gym.schemas.unified_results import create_task_result
from manager_agent_gym.schemas.core.resources import Resource
from manager_agent_gym.schemas.execution.manager_actions import (
    AssignTaskAction,
    AssignAllPendingTasksAction,
)


class _StubAgent(AgentInterface[AgentConfig]):
    def __init__(self, agent_id: str) -> None:
        super().__init__(
            AgentConfig(
                agent_id=agent_id,
                agent_type="ai",
                system_prompt="stub agent for manager actions tests",
                model_name="none",
                agent_description="stub agent for manager actions tests",
                agent_capabilities=["stub agent for manager actions tests"],
            )
        )

    async def execute_task(self, task: Task, resources: list[Resource]):
        return create_task_result(
            task_id=task.id,
            agent_id=self.agent_id,
            success=True,
            execution_time=0.0,
            resources=[],
        )


def _workflow_with_task_and_agent() -> tuple[Workflow, Task, _StubAgent]:
    w = Workflow(name="w", workflow_goal="d", owner_id=uuid4())
    t = Task(name="T", description="d")
    w.add_task(t)
    agent = _StubAgent("agent-1")
    w.add_agent(agent)
    return w, t, agent


@pytest.mark.asyncio
async def test_assign_task_happy_path() -> None:
    w, t, agent = _workflow_with_task_and_agent()
    action = AssignTaskAction(
        reasoning="r",
        task_id=str(t.id),
        agent_id=agent.agent_id,
        success=True,
        result_summary="assign",
    )
    result = await action.execute(w)
    assert w.tasks[t.id].assigned_agent_id == agent.agent_id
    assert result.kind == "mutation"
    assert result.data == {"task_id": str(t.id), "agent_id": agent.agent_id}


@pytest.mark.asyncio
async def test_assign_task_invalid_ids() -> None:
    w, t, agent = _workflow_with_task_and_agent()
    # Bad task id
    bad_task_action = AssignTaskAction(
        reasoning="r",
        task_id=str(uuid4()),
        agent_id=agent.agent_id,
        success=True,
        result_summary="assign",
    )
    with pytest.raises(ValueError):
        await bad_task_action.execute(w)

    # Bad agent id
    bad_agent_action = AssignTaskAction(
        reasoning="r",
        task_id=str(t.id),
        agent_id="nope",
        success=True,
        result_summary="assign",
    )
    with pytest.raises(ValueError):
        await bad_agent_action.execute(w)


@pytest.mark.asyncio
async def test_assign_all_pending_tasks_assigns_unassigned_only() -> None:
    w = Workflow(name="w", workflow_goal="d", owner_id=uuid4())
    a1 = _StubAgent("a1")
    w.add_agent(a1)

    t1 = Task(name="t1", description="d")
    t2 = Task(name="t2", description="d")
    t3 = Task(name="t3", description="d")
    t3.assigned_agent_id = "preassigned"
    w.add_task(t1)
    w.add_task(t2)
    w.add_task(t3)

    action = AssignAllPendingTasksAction(
        reasoning="bulk", agent_id=a1.agent_id, success=True, result_summary="assign"
    )
    res = await action.execute(w)
    # t1 and t2 should be assigned; t3 should remain as-is
    assert w.tasks[t1.id].assigned_agent_id == "a1"
    assert w.tasks[t2.id].assigned_agent_id == "a1"
    assert w.tasks[t3.id].assigned_agent_id == "preassigned"
    assert res.kind in {"info", "mutation"}
