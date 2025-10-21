import pytest  # type: ignore[import-not-found]
from uuid import uuid4

from manager_agent_gym.schemas.domain.workflow import Workflow
from manager_agent_gym.schemas.domain.task import Task
from manager_agent_gym.schemas.domain.base import TaskStatus
from manager_agent_gym.core.workflow.engine import WorkflowExecutionEngine
from manager_agent_gym.core.agents.workflow_agents.common.interface import (
    AgentInterface,
)
from manager_agent_gym.core.agents.workflow_agents.tools.registry import AgentRegistry
from manager_agent_gym.core.execution.schemas.results import create_task_result
from manager_agent_gym.core.workflow.schemas.config import OutputConfig
from manager_agent_gym.schemas.preferences.preference import PreferenceSnapshot
from manager_agent_gym.core.agents.stakeholder_agent.stakeholder_agent import (
    StakeholderAgent,
)
from manager_agent_gym.schemas.agents.stakeholder import StakeholderConfig
from tests.helpers.stubs import (
    ManagerAssignFirstReady,
    StubAgent,
    ManagerNoOp,
    FailingStubAgent,
)
from manager_agent_gym.core.workflow.services import WorkflowQueries
from manager_agent_gym.core.workflow.services import WorkflowMutations

pytestmark = pytest.mark.integration


class _StubAgent(AgentInterface):
    def __init__(self, agent_id: str):
        from manager_agent_gym.schemas.agents import AgentConfig

        super().__init__(
            AgentConfig(
                agent_id=agent_id,
                agent_type="ai",
                system_prompt="stub agent",
                model_name="none",
                agent_description="stub agent",
                agent_capabilities=["stub agent"],
            )
        )

    async def execute_task(self, task, resources):
        return create_task_result(
            task_id=task.id,
            agent_id=self.agent_id,
            success=True,
            execution_time=0.01,
            resources=[],
        )


# Use shared Manager stub from tests.helpers.stubs


def _chain_workflow() -> Workflow:
    w = Workflow(name="w", workflow_goal="d", owner_id=uuid4())
    a = Task(name="A", description="d")
    b = Task(name="B", description="d", dependency_task_ids=[a.id])
    c = Task(name="C", description="d", dependency_task_ids=[b.id])
    for t in (a, b, c):
        t.assigned_agent_id = "worker-1"
        WorkflowMutations.add_task(w, t)
    return w


@pytest.mark.asyncio
async def test_ready_state_and_chain_completion(tmp_path):
    w = _chain_workflow()
    agent = _StubAgent("worker-1")
    WorkflowMutations.add_agent(w, agent)

    stakeholder_cfg = StakeholderConfig(
        agent_id="stakeholder",
        agent_type="stakeholder",
        system_prompt="Stakeholder",
        model_name="o3",
        name="Stakeholder",
        role="Owner",
        preference_data=PreferenceSnapshot(preferences=[]),
        agent_description="Stakeholder",
        agent_capabilities=["Stakeholder"],
    )
    stakeholder = StakeholderAgent(config=stakeholder_cfg)
    WorkflowMutations.add_agent(w, stakeholder)
    engine = WorkflowExecutionEngine(
        workflow=w,
        agent_registry=AgentRegistry(),
        manager_agent=ManagerAssignFirstReady(),
        stakeholder_agent=stakeholder,
        output_config=OutputConfig(
            base_output_dir=tmp_path, create_run_subdirectory=False
        ),
        max_timesteps=10,
        enable_timestep_logging=False,
        enable_final_metrics_logging=False,
        seed=42,
    )

    # T0: A should be marked READY; B and C remain PENDING
    ready0 = WorkflowQueries.get_ready_tasks(w)
    if not ready0:
        assert False, "Could not find task A"
    assert any(t.name == "A" and t.status == TaskStatus.READY for t in ready0)

    task_a = w.tasks[next(t.id for t in ready0 if t.name == "A")]
    if task_a.status != TaskStatus.READY:
        raise Exception(f"A should be READY, but is {task_a.status}")

    # Execute steps to drive A->B->C
    await engine.execute_timestep()  # starts A (READY->RUNNING)
    await engine.execute_timestep()  # completes A and immediately starts B (assigned)

    # After A completes, B should be RUNNING (engine starts READY tasks immediately when assigned)
    b = next(t for t in w.tasks.values() if t.name == "B")
    assert b.status == TaskStatus.RUNNING

    await engine.execute_timestep()  # completes B (and starts C)

    # After B completes, C should be RUNNING (immediate start)
    c = next(t for t in w.tasks.values() if t.name == "C")
    assert c.status == TaskStatus.RUNNING

    await engine.execute_timestep()  # completes C

    assert WorkflowQueries.is_complete(w)


def _nested_subtask_workflow() -> Workflow:
    w = Workflow(name="nested", workflow_goal="d", owner_id=uuid4())

    # Parent composite P
    parent = Task(name="P", description="parent")

    # ChildA composite with chain GA -> GB
    ga = Task(name="GA", description="leaf chain start")
    gb = Task(name="GB", description="leaf chain next", dependency_task_ids=[ga.id])
    child_a = Task(name="ChildA", description="chain container")
    child_a.add_subtask(ga)
    child_a.add_subtask(gb)

    # ChildB composite with parallel leaves HB1, HB2
    hb1 = Task(name="HB1", description="leaf parallel 1")
    hb2 = Task(name="HB2", description="leaf parallel 2")
    child_b = Task(name="ChildB", description="parallel container")
    child_b.add_subtask(hb1)
    child_b.add_subtask(hb2)

    # Wire children under parent
    parent.add_subtask(child_a)
    parent.add_subtask(child_b)

    # Register only the parent at top-level; leaves will be auto-registered for readiness
    WorkflowMutations.add_task(w, parent)
    # Assign agent ID for automatic start when ready
    for t in (ga, gb, hb1, hb2):
        t.assigned_agent_id = "worker-1"
    return w


@pytest.mark.asyncio
async def test_nested_subtasks_chain_and_parallel(tmp_path):
    w = _nested_subtask_workflow()
    agent = _StubAgent("worker-1")
    WorkflowMutations.add_agent(w, agent)
    # Minimal stakeholder to satisfy engine requirement
    from manager_agent_gym.core.agents.stakeholder_agent.stakeholder_agent import (
        StakeholderAgent,
    )
    from manager_agent_gym.schemas.agents.stakeholder import StakeholderConfig

    stakeholder_cfg = StakeholderConfig(
        agent_id="stakeholder",
        agent_type="stakeholder",
        system_prompt="Stakeholder",
        model_name="o3",
        name="Stakeholder",
        role="Owner",
        preference_data=PreferenceSnapshot(preferences=[]),
        agent_description="Stakeholder",
        agent_capabilities=["Stakeholder"],
    )
    stakeholder = StakeholderAgent(config=stakeholder_cfg)
    WorkflowMutations.add_agent(w, stakeholder)
    engine = WorkflowExecutionEngine(
        workflow=w,
        agent_registry=AgentRegistry(),
        manager_agent=ManagerAssignFirstReady(),
        stakeholder_agent=stakeholder,
        output_config=OutputConfig(
            base_output_dir=tmp_path, create_run_subdirectory=False
        ),
        max_timesteps=50,
        enable_timestep_logging=False,
        enable_final_metrics_logging=False,
        seed=42,
    )

    # Initial ready should include GA, HB1, HB2; GB should not be ready yet
    ready0 = {t.name for t in WorkflowQueries.get_ready_tasks(w)}
    assert {"GA", "HB1", "HB2"} <= ready0
    assert "GB" not in ready0

    # Run timesteps until GA completes; afterwards GB should become READY/RUNNING next
    ga_completed = False
    gb_started_or_ready = False
    for _ in range(10):
        await engine.execute_timestep()
        # Check GA completion
        if (
            next(t for t in w.tasks.values() if t.name == "GA").status
            == TaskStatus.COMPLETED
        ):
            ga_completed = True

        # Check GB transitions
        gb_status = next(t for t in w.tasks.values() if t.name == "GB").status
        if gb_status in (TaskStatus.READY, TaskStatus.RUNNING, TaskStatus.COMPLETED):
            gb_started_or_ready = True
        if ga_completed and gb_started_or_ready:
            break

    assert ga_completed
    assert gb_started_or_ready

    # Continue until all leaves complete
    for _ in range(20):
        if all(
            next(t for t in w.tasks.values() if t.name == n).status
            == TaskStatus.COMPLETED
            for n in ("GA", "GB", "HB1", "HB2")
        ):
            break
        await engine.execute_timestep()

    # All leaves should be completed
    assert all(
        next(t for t in w.tasks.values() if t.name == n).status == TaskStatus.COMPLETED
        for n in ("GA", "GB", "HB1", "HB2")
    )

    # Helper to find nested task by name from any top-level root
    def _find_by_name(name: str) -> Task:
        def _dfs(node: Task) -> Task | None:
            if node.name == name:
                return node
            for st in node.subtasks:
                found = _dfs(st)
                if found:
                    return found
            return None

        for top in w.tasks.values():
            found = _dfs(top)
            if found:
                return found
        raise StopIteration

    # Composite containers and parent should be marked completed via propagation
    assert _find_by_name("ChildA").status == TaskStatus.COMPLETED
    assert _find_by_name("ChildB").status == TaskStatus.COMPLETED
    assert _find_by_name("P").status == TaskStatus.COMPLETED


@pytest.mark.asyncio
async def test_parent_never_ready_or_running_and_only_completes_after_all_leaves(
    tmp_path,
):
    w = Workflow(name="nested2", workflow_goal="d", owner_id=uuid4())
    parent = Task(name="P", description="parent")
    ga = Task(name="GA", description="leaf chain start")
    gb = Task(name="GB", description="leaf chain next", dependency_task_ids=[ga.id])
    c1 = Task(name="C1", description="container 1")
    c1.add_subtask(ga)
    c1.add_subtask(gb)
    hc = Task(name="HC", description="leaf single")
    c2 = Task(name="C2", description="container 2")
    c2.add_subtask(hc)
    parent.add_subtask(c1)
    parent.add_subtask(c2)
    WorkflowMutations.add_task(w, parent)

    agent = StubAgent(agent_id="worker-1", agent_type="ai", seconds=0.0)
    WorkflowMutations.add_agent(w, agent)
    for leaf in (ga, gb, hc):
        leaf.assigned_agent_id = agent.agent_id

    stakeholder = StakeholderAgent(
        config=StakeholderConfig(
            agent_id="stakeholder",
            agent_type="stakeholder",
            system_prompt="Stakeholder",
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
        manager_agent=ManagerNoOp(),
        stakeholder_agent=stakeholder,
        output_config=OutputConfig(
            base_output_dir=tmp_path, create_run_subdirectory=False
        ),
        enable_timestep_logging=False,
        enable_final_metrics_logging=False,
        max_timesteps=50,
        seed=42,
    )

    ready0 = {t.name for t in WorkflowQueries.get_ready_tasks(w)}
    assert {"GA", "HC"} <= ready0
    assert "P" not in ready0 and "C1" not in ready0 and "C2" not in ready0

    for _ in range(5):
        await engine.execute_timestep()
        if (
            next(t for t in w.tasks.values() if t.name == "GA").status
            == TaskStatus.COMPLETED
        ):
            break
    assert (
        next(t for t in w.tasks.values() if t.name == "GA").status
        == TaskStatus.COMPLETED
    )
    assert parent.status != TaskStatus.COMPLETED

    for _ in range(10):
        if all(
            next(t for t in w.tasks.values() if t.name == n).status
            == TaskStatus.COMPLETED
            for n in ("GB", "HC")
        ):
            break
        await engine.execute_timestep()

    assert all(
        next(t for t in w.tasks.values() if t.name == n).status == TaskStatus.COMPLETED
        for n in ("GB", "HC")
    )
    assert parent.status == TaskStatus.COMPLETED


@pytest.mark.asyncio
async def test_failed_leaf_blocks_dependents_and_parent_incomplete(tmp_path):
    w = Workflow(name="fail-prop", workflow_goal="d", owner_id=uuid4())
    parent = Task(name="P", description="parent")
    a = Task(name="A", description="will fail")
    b = Task(name="B", description="will succeed")
    parent.add_subtask(a)
    parent.add_subtask(b)
    WorkflowMutations.add_task(w, parent)

    q = Task(name="Q", description="depends on P")
    q.dependency_task_ids = [parent.id]
    WorkflowMutations.add_task(w, q)

    failer = FailingStubAgent(agent_id="failer")
    ok = StubAgent(agent_id="ok", agent_type="ai", seconds=0.0)
    WorkflowMutations.add_agent(w, failer)
    WorkflowMutations.add_agent(w, ok)
    a.assigned_agent_id = "failer"
    b.assigned_agent_id = "ok"

    stakeholder = StakeholderAgent(
        config=StakeholderConfig(
            agent_id="stakeholder",
            agent_type="stakeholder",
            system_prompt="Stakeholder",
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
        manager_agent=ManagerNoOp(),
        stakeholder_agent=stakeholder,
        output_config=OutputConfig(
            base_output_dir=tmp_path, create_run_subdirectory=False
        ),
        enable_timestep_logging=False,
        enable_final_metrics_logging=False,
        max_timesteps=50,
        seed=42,
    )

    for _ in range(6):
        await engine.execute_timestep()

    assert (
        next(t for t in w.tasks.values() if t.name == "A").status == TaskStatus.FAILED
    )
    assert parent.status != TaskStatus.COMPLETED
    ready = {t.id for t in WorkflowQueries.get_ready_tasks(w)}
    assert q.id not in ready
