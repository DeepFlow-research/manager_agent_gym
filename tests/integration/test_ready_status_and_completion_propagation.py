import pytest  # type: ignore[import-not-found]
from uuid import uuid4

from manager_agent_gym.schemas.core.workflow import Workflow
from manager_agent_gym.schemas.core.tasks import Task
from manager_agent_gym.schemas.core.base import TaskStatus
from manager_agent_gym.core.execution.engine import WorkflowExecutionEngine
from manager_agent_gym.core.workflow_agents.interface import AgentInterface
from manager_agent_gym.core.workflow_agents.registry import AgentRegistry
from manager_agent_gym.core.manager_agent.interface import ManagerAgent
from manager_agent_gym.schemas.execution.manager import ManagerObservation
from manager_agent_gym.schemas.unified_results import create_task_result
from manager_agent_gym.schemas.config import OutputConfig
from manager_agent_gym.schemas.preferences.preference import PreferenceWeights
from manager_agent_gym.schemas.execution.state import ExecutionState
from manager_agent_gym.core.workflow_agents.stakeholder_agent import StakeholderAgent
from manager_agent_gym.schemas.workflow_agents.stakeholder import StakeholderConfig
from manager_agent_gym.schemas.workflow_agents.stakeholder import (
    StakeholderPublicProfile,
)


class _StubAgent(AgentInterface):
    def __init__(self, agent_id: str):
        from manager_agent_gym.schemas.workflow_agents import AgentConfig

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


class _StubManager(ManagerAgent):
    def __init__(self):
        super().__init__(
            agent_id="stub_manager", preferences=PreferenceWeights(preferences=[])
        )

    async def take_action(self, observation: ManagerObservation):
        from manager_agent_gym.schemas.execution.manager_actions import (
            AssignTaskAction,
            NoOpAction,
        )

        if observation.ready_task_ids and observation.available_agent_metadata:
            return AssignTaskAction(
                reasoning="assign first ready",
                task_id=str(observation.ready_task_ids[0]),
                agent_id=observation.available_agent_metadata[0].agent_id,
                success=True,
                result_summary="assigned first ready task",
            )
        return NoOpAction(reasoning="idle", success=True, result_summary="idle")

    def reset(self):
        pass

    async def step(
        self,
        workflow: Workflow,
        execution_state: ExecutionState,
        stakeholder_profile: StakeholderPublicProfile,
        current_timestep: int,
        running_tasks: dict,
        completed_task_ids: set,
        failed_task_ids: set,
        communication_service=None,
        previous_reward: float = 0.0,
        done: bool = False,
    ):
        # Build observation and delegate to take_action for test compatibility
        obs = await self.create_observation(
            workflow=workflow,
            execution_state=execution_state,
            stakeholder_profile=StakeholderPublicProfile(
                display_name="Test Stakeholder", role="Owner", preference_summary=""
            ),
            current_timestep=current_timestep,
            running_tasks=running_tasks,
            completed_task_ids=completed_task_ids,
            failed_task_ids=failed_task_ids,
            communication_service=communication_service,
        )
        return await self.take_action(obs)


def _chain_workflow() -> Workflow:
    w = Workflow(name="w", workflow_goal="d", owner_id=uuid4())
    a = Task(name="A", description="d")
    b = Task(name="B", description="d", dependency_task_ids=[a.id])
    c = Task(name="C", description="d", dependency_task_ids=[b.id])
    for t in (a, b, c):
        t.assigned_agent_id = "worker-1"
        w.add_task(t)
    return w


@pytest.mark.asyncio
async def test_ready_state_and_chain_completion(tmp_path):
    w = _chain_workflow()
    agent = _StubAgent("worker-1")
    w.add_agent(agent)

    stakeholder_cfg = StakeholderConfig(
        agent_id="stakeholder",
        agent_type="stakeholder",
        system_prompt="Stakeholder",
        model_name="o3",
        name="Stakeholder",
        role="Owner",
        initial_preferences=PreferenceWeights(preferences=[]),
        agent_description="Stakeholder",
        agent_capabilities=["Stakeholder"],
    )
    stakeholder = StakeholderAgent(config=stakeholder_cfg)
    w.add_agent(stakeholder)
    engine = WorkflowExecutionEngine(
        workflow=w,
        agent_registry=AgentRegistry(),
        manager_agent=_StubManager(),
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
    ready0 = w.get_ready_tasks()
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

    assert w.is_complete()


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
    w.add_task(parent)
    # Assign agent ID for automatic start when ready
    for t in (ga, gb, hb1, hb2):
        t.assigned_agent_id = "worker-1"
    return w


@pytest.mark.asyncio
async def test_nested_subtasks_chain_and_parallel(tmp_path):
    w = _nested_subtask_workflow()
    agent = _StubAgent("worker-1")
    w.add_agent(agent)
    # Minimal stakeholder to satisfy engine requirement
    from manager_agent_gym.core.workflow_agents.stakeholder_agent import (
        StakeholderAgent,
    )
    from manager_agent_gym.schemas.workflow_agents.stakeholder import StakeholderConfig

    stakeholder_cfg = StakeholderConfig(
        agent_id="stakeholder",
        agent_type="stakeholder",
        system_prompt="Stakeholder",
        model_name="o3",
        name="Stakeholder",
        role="Owner",
        initial_preferences=PreferenceWeights(preferences=[]),
        agent_description="Stakeholder",
        agent_capabilities=["Stakeholder"],
    )
    stakeholder = StakeholderAgent(config=stakeholder_cfg)
    w.add_agent(stakeholder)
    engine = WorkflowExecutionEngine(
        workflow=w,
        agent_registry=AgentRegistry(),
        manager_agent=_StubManager(),
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
    ready0 = {t.name for t in w.get_ready_tasks()}
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
