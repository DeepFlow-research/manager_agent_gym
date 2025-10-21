import pytest
from uuid import uuid4

from manager_agent_gym.schemas.domain.workflow import Workflow
from manager_agent_gym.schemas.domain.task import Task
from manager_agent_gym.schemas.domain.base import TaskStatus
from manager_agent_gym.core.workflow.engine import WorkflowExecutionEngine
from manager_agent_gym.core.agents.workflow_agents.tools.registry import AgentRegistry
from manager_agent_gym.core.workflow.schemas.config import OutputConfig
from manager_agent_gym.schemas.preferences.preference import PreferenceSnapshot
from manager_agent_gym.core.agents.stakeholder_agent.stakeholder_agent import (
    StakeholderAgent,
)
from manager_agent_gym.schemas.agents.stakeholder import StakeholderConfig
from tests.helpers.stubs import StubAgent, ManagerAssignFirstReady
from manager_agent_gym.core.workflow.services import WorkflowQueries
from manager_agent_gym.core.workflow.services import WorkflowMutations


pytestmark = pytest.mark.integration


def _make_composite() -> Workflow:
    w = Workflow(name="wf", workflow_goal="g", owner_id=uuid4())
    parent = Task(name="Parent", description="parent")
    a = Task(name="A", description="leaf 1")
    b = Task(name="B", description="leaf 2", dependency_task_ids=[a.id])
    container = Task(name="Container", description="container")
    container.add_subtask(a)
    container.add_subtask(b)
    parent.add_subtask(container)
    WorkflowMutations.add_task(w, parent)
    for t in (a, b):
        t.assigned_agent_id = "worker"
    return w


@pytest.mark.asyncio
async def test_composite_effective_status_and_never_schedulable(tmp_path):
    w = _make_composite()
    agent = StubAgent(agent_id="worker", agent_type="ai", seconds=0.0)
    WorkflowMutations.add_agent(w, agent)

    stakeholder = StakeholderAgent(
        config=StakeholderConfig(
            agent_id="stakeholder",
            agent_type="stakeholder",
            system_prompt="Stakeholder agent sufficiently long prompt",
            model_name="o3",
            name="Stakeholder",
            role="Owner",
            preference_data=PreferenceSnapshot(preferences=[]),
            agent_description="Stakeholder",
            agent_capabilities=["Stakeholder"],
        )
    )
    WorkflowMutations.add_agent(w, stakeholder)

    engine = WorkflowExecutionEngine(
        workflow=w,
        agent_registry=AgentRegistry(),
        manager_agent=ManagerAssignFirstReady(),
        stakeholder_agent=stakeholder,
        output_config=OutputConfig(
            base_output_dir=tmp_path, create_run_subdirectory=False
        ),
        enable_timestep_logging=False,
        enable_final_metrics_logging=False,
        max_timesteps=20,
        seed=7,
    )

    # T0: A should be READY, B PENDING; composites not READY/RUNNING
    ready0 = {t.name for t in WorkflowQueries.get_ready_tasks(w)}
    assert "A" in ready0 and "B" not in ready0
    parent = next(t for t in w.tasks.values() if t.name == "Parent")
    container = next((st for st in parent.subtasks if st.name == "Container"), None)
    assert container is not None
    assert parent.status == TaskStatus.PENDING
    assert container.status == TaskStatus.PENDING
    assert parent.effective_status in (None, TaskStatus.PENDING.value)
    assert container.effective_status in (None, TaskStatus.PENDING.value)

    # Step once: A starts RUNNING -> parent/container effective_status becomes RUNNING
    await engine.execute_timestep()
    assert parent.status == TaskStatus.PENDING
    assert container.status == TaskStatus.PENDING
    assert parent.effective_status == TaskStatus.RUNNING.value
    assert container.effective_status == TaskStatus.RUNNING.value
    # Composites must not be in READY list
    assert "Parent" not in {t.name for t in WorkflowQueries.get_ready_tasks(w)}
    assert "Container" not in {t.name for t in WorkflowQueries.get_ready_tasks(w)}

    # Step until A completes and B becomes READY/RUNNING
    for _ in range(5):
        await engine.execute_timestep()
        a_status = next(t for t in w.tasks.values() if t.name == "A").status
        b_status = next(t for t in w.tasks.values() if t.name == "B").status
        if a_status == TaskStatus.COMPLETED and b_status in (
            TaskStatus.READY,
            TaskStatus.RUNNING,
            TaskStatus.COMPLETED,
        ):
            break

    # While B is pending/ready/running, composites mirror READY/RUNNING appropriately
    b_status = next(t for t in w.tasks.values() if t.name == "B").status
    if b_status == TaskStatus.READY:
        assert parent.effective_status == TaskStatus.READY.value
        assert container.effective_status == TaskStatus.READY.value
    else:
        assert parent.effective_status in (
            TaskStatus.RUNNING.value,
            TaskStatus.COMPLETED.value,
        )

    # Finish the workflow
    for _ in range(10):
        if WorkflowQueries.is_complete(w):
            break
        await engine.execute_timestep()

    # Parents must be COMPLETED only after all leaves COMPLETED
    assert WorkflowQueries.is_complete(w)
    assert parent.status == TaskStatus.COMPLETED
    assert container.status == TaskStatus.COMPLETED
    assert parent.effective_status == TaskStatus.COMPLETED.value
    assert container.effective_status == TaskStatus.COMPLETED.value
