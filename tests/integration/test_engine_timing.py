import pytest
from uuid import uuid4

from manager_agent_gym.schemas.core.workflow import Workflow
from manager_agent_gym.schemas.core.tasks import Task
from manager_agent_gym.schemas.config import OutputConfig
from manager_agent_gym.core.execution.engine import WorkflowExecutionEngine
from manager_agent_gym.core.workflow_agents.registry import AgentRegistry
from manager_agent_gym.schemas.preferences.preference import PreferenceWeights
from tests.helpers.stubs import (
    StubAgent,
    ManagerNoOp,
)

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_human_simulated_time_inflates_workflow_time(tmp_path):
    w = Workflow(name="timing-w1", workflow_goal="d", owner_id=uuid4())
    # Two-step chain so both complete in sequence
    a = Task(name="A", description="d")
    b = Task(name="B", description="d", dependency_task_ids=[a.id])
    w.add_task(a)
    w.add_task(b)

    # One human-like stub that reports 1 hour per task and is pre-assigned
    human = StubAgent(agent_id="human-1", agent_type="human_mock", seconds=3600.0)
    w.add_agent(human)
    a.assigned_agent_id = human.agent_id
    b.assigned_agent_id = human.agent_id

    # Minimal stakeholder with empty preferences to satisfy engine signature
    from manager_agent_gym.core.workflow_agents.stakeholder_agent import (
        StakeholderAgent,
    )
    from manager_agent_gym.schemas.workflow_agents.stakeholder import StakeholderConfig

    stakeholder = StakeholderAgent(
        config=StakeholderConfig(
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
    )
    # Build engine with a no-op manager; tasks are pre-assigned
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
        max_timesteps=10,
        seed=42,
    )
    w.add_agent(stakeholder)
    # Avoid stakeholder being selected as available by other code paths
    stakeholder.is_available = False

    await engine.run_full_execution()

    # Each task contributes 1.0 simulated hour
    assert pytest.approx(w.total_simulated_hours, rel=0, abs=1e-9) == 2.0
    tA = next(t for t in w.tasks.values() if t.name == "A")
    tB = next(t for t in w.tasks.values() if t.name == "B")
    assert pytest.approx(float(tA.actual_duration_hours or 0.0), rel=0, abs=1e-9) == 1.0
    assert pytest.approx(float(tB.actual_duration_hours or 0.0), rel=0, abs=1e-9) == 1.0


@pytest.mark.asyncio
async def test_parallel_ready_humans_sum_in_timestep(tmp_path):
    w = Workflow(name="timing-w2", workflow_goal="d", owner_id=uuid4())
    # Two independent tasks
    t1 = Task(name="T1", description="d")
    t2 = Task(name="T2", description="d")
    # Pre-assign to distinct agents so engine starts both when ready
    t1.assigned_agent_id = "h1"
    t2.assigned_agent_id = "h2"
    w.add_task(t1)
    w.add_task(t2)

    # Each reports 0.5 hour (1800 seconds)
    h1 = StubAgent(agent_id="h1", agent_type="human_mock", seconds=1800.0)
    h2 = StubAgent(agent_id="h2", agent_type="human_mock", seconds=1800.0)
    w.add_agent(h1)
    w.add_agent(h2)

    # Manager not needed for assignment since tasks are pre-assigned
    from manager_agent_gym.core.workflow_agents.stakeholder_agent import (
        StakeholderAgent,
    )
    from manager_agent_gym.schemas.workflow_agents.stakeholder import StakeholderConfig

    stakeholder = StakeholderAgent(
        config=StakeholderConfig(
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
    )
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
        max_timesteps=10,
        seed=42,
    )
    w.add_agent(stakeholder)
    stakeholder.is_available = False

    # T0 starts both -> tasks_started populated
    res0 = await engine.execute_timestep()
    assert set(res0.metadata.get("tasks_started", [])) == {str(t1.id), str(t2.id)}
    # T1 completes both -> accumulated simulated hours = 1.0 (0.5+0.5)
    res1 = await engine.execute_timestep()
    assert set(res1.metadata.get("tasks_completed", [])) == {str(t1.id), str(t2.id)}
    assert (
        pytest.approx(float(res1.simulated_duration_hours or 0.0), rel=0, abs=1e-9)
        == 1.0
    )


@pytest.mark.asyncio
async def test_missing_simulated_hours_raises_if_agent_omits_it(tmp_path):
    # Agents must now set simulated_duration_hours explicitly for tasks.
    from manager_agent_gym.schemas.unified_results import create_task_result
    from manager_agent_gym.core.workflow_agents.interface import AgentInterface
    from manager_agent_gym.schemas.workflow_agents import AgentConfig

    class _AgentNoSimHours(AgentInterface[AgentConfig]):
        def __init__(self) -> None:
            super().__init__(
                AgentConfig(
                    agent_id="no-sim",
                    agent_type="ai",
                    system_prompt="stub prompt ok",
                    model_name="none",
                    agent_description="stub",
                    agent_capabilities=["stub"],
                )
            )

        async def execute_task(self, task: Task, resources: list):
            # Explicitly set 0.0 to satisfy strict schema (no implicit fallback)
            return create_task_result(
                task_id=task.id,
                agent_id=self.agent_id,
                success=True,
                execution_time=7200.0,
                resources=[],
                simulated_duration_hours=0.0,
            )

    w = Workflow(name="timing-w3", workflow_goal="d", owner_id=uuid4())
    t = Task(name="X", description="d")
    t.assigned_agent_id = "no-sim"
    w.add_task(t)
    w.add_agent(_AgentNoSimHours())

    from manager_agent_gym.core.workflow_agents.stakeholder_agent import (
        StakeholderAgent,
    )
    from manager_agent_gym.schemas.workflow_agents.stakeholder import StakeholderConfig

    stakeholder = StakeholderAgent(
        config=StakeholderConfig(
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
    )
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
        max_timesteps=5,
        seed=42,
    )
    w.add_agent(stakeholder)
    stakeholder.is_available = False

    # Start then complete
    await engine.execute_timestep()
    _ = await engine.execute_timestep()
    # The engine should not have inflated totals; task.actual_duration_hours remains 0.0
    task = next(iter(w.tasks.values()))
    assert (
        pytest.approx(float(task.actual_duration_hours or 0.0), rel=0, abs=1e-9) == 0.0
    )
    assert pytest.approx(float(w.total_simulated_hours), rel=0, abs=1e-9) == 0.0
