import pytest

from uuid import uuid4

from manager_agent_gym.schemas.domain.workflow import Workflow
from manager_agent_gym.schemas.domain.task import Task
from manager_agent_gym.schemas.preferences.preference import PreferenceSnapshot
from manager_agent_gym.core.workflow.schemas.config import OutputConfig
from manager_agent_gym.core.workflow.engine import WorkflowExecutionEngine
from manager_agent_gym.core.agents.workflow_agents.common.interface import (
    AgentInterface,
)
from manager_agent_gym.core.agents.workflow_agents.tools.registry import AgentRegistry
from manager_agent_gym.core.agents.manager_agent.common.interface import ManagerAgent
from manager_agent_gym.schemas.manager.observation import ManagerObservation
from manager_agent_gym.core.execution.schemas.results import create_task_result
from manager_agent_gym.core.agents.stakeholder_agent.stakeholder_agent import (
    StakeholderAgent,
)
from manager_agent_gym.schemas.agents.stakeholder import StakeholderConfig
from manager_agent_gym.schemas.agents.stakeholder import (
    StakeholderPublicProfile,
)
from manager_agent_gym.core.workflow.services import WorkflowQueries
from manager_agent_gym.core.workflow.services import WorkflowMutations
from manager_agent_gym.core.execution.schemas.state import ExecutionState

pytestmark = pytest.mark.integration


class _CostTimeStubAgent(AgentInterface):
    def __init__(self, agent_id: str, agent_type: str, cost: float, seconds: float):
        from manager_agent_gym.schemas.agents import AgentConfig

        super().__init__(
            AgentConfig(
                agent_id=agent_id,
                agent_type=agent_type,
                system_prompt=f"stub {agent_type} agent system prompt",
                model_name="none",
                agent_description=f"stub {agent_type} agent",
                agent_capabilities=[f"stub {agent_type} agent"],
            )
        )
        self._cost = float(cost)
        self._seconds = float(seconds)

    async def execute_task(self, task, resources):
        # Produce no resources; focus on cost and wall-time
        return create_task_result(
            task_id=task.id,
            agent_id=self.agent_id,
            success=True,
            execution_time=0.01,  # real wall time is fast
            resources=[],
            cost=self._cost,
            simulated_duration_hours=self._seconds / 3600.0,
        )


class _AlternatingAssignManager(ManagerAgent):
    def __init__(self):
        super().__init__(
            agent_id="stub_manager", preferences=PreferenceSnapshot(preferences=[])
        )
        self._last_idx = -1

    async def take_action(self, observation: ManagerObservation):
        from manager_agent_gym.core.agents.manager_agent.actions import (
            AssignTaskAction,
            NoOpAction,
        )

        if observation.ready_task_ids and observation.available_agent_metadata:
            # Alternate across available agent_ids to exercise both AI and human
            self._last_idx = (self._last_idx + 1) % len(
                observation.available_agent_metadata
            )
            return AssignTaskAction(
                reasoning="alternate assignment",
                task_id=str(observation.ready_task_ids[0]),
                agent_id=observation.available_agent_metadata[self._last_idx].agent_id,
                success=True,
                result_summary="alternate assignment",
            )
        return NoOpAction(reasoning="idle", success=True, result_summary="idle")

    def reset(self):
        pass

    async def step(
        self,
        workflow: Workflow,
        execution_state: ExecutionState,
        stakeholder_profile: StakeholderPublicProfile | None = None,
        current_timestep: int = 0,
        running_tasks: dict | None = None,
        completed_task_ids: set | None = None,
        failed_task_ids: set | None = None,
        communication_service=None,
        previous_reward: float = 0.0,
        done: bool = False,
    ):
        obs = await self.create_observation(
            workflow=workflow,
            execution_state=execution_state,
            current_timestep=current_timestep,
            running_tasks=running_tasks,
            completed_task_ids=completed_task_ids,
            failed_task_ids=failed_task_ids,
            communication_service=communication_service,
        )
        return await self.take_action(obs)


@pytest.fixture
def cost_time_workflow():
    # Two tasks in dependency chain so both execute within a few timesteps
    w = Workflow(name="cost-time-w", workflow_goal="d", owner_id=uuid4())
    t1 = Task(
        name="A", description="d", estimated_cost=100.0, estimated_duration_hours=1.0
    )
    t2 = Task(
        name="B",
        description="d",
        estimated_cost=200.0,
        estimated_duration_hours=2.0,
        dependency_task_ids=[t1.id],
    )
    WorkflowMutations.add_task(w, t1)
    WorkflowMutations.add_task(w, t2)

    # Register one AI and one Human stub agent with distinct costs and times
    ai = _CostTimeStubAgent("ai-1", "ai", cost=60.0, seconds=3.6)  # 0.001 hours
    human = _CostTimeStubAgent(
        "human-1", "human_mock", cost=80.0, seconds=7.2
    )  # 0.002 hours
    WorkflowMutations.add_agent(w, ai)
    WorkflowMutations.add_agent(w, human)
    # Minimal stakeholder with empty preferences to satisfy evaluation
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
    WorkflowMutations.add_agent(w, StakeholderAgent(config=stakeholder_cfg))
    return w


@pytest.mark.asyncio
async def test_costs_are_aggregated_from_task_results(tmp_path, cost_time_workflow):
    out = OutputConfig(base_output_dir=tmp_path, create_run_subdirectory=False)
    engine = WorkflowExecutionEngine(
        workflow=cost_time_workflow,
        agent_registry=AgentRegistry(),
        manager_agent=_AlternatingAssignManager(),
        stakeholder_agent=next(
            a
            for a in cost_time_workflow.agents.values()
            if a.agent_type == "stakeholder"
        ),
        output_config=out,
        max_timesteps=10,
        enable_timestep_logging=False,
        enable_final_metrics_logging=False,
        seed=42,
    )

    results = await engine.run_full_execution()
    assert WorkflowQueries.is_complete(engine.workflow)
    # Sum actual_cost stored on tasks
    total_actual = sum(
        float(t.actual_cost or 0.0) for t in engine.workflow.tasks.values()
    )
    # Expect 60 + 80 = 140
    assert pytest.approx(total_actual, rel=0, abs=1e-6) == 140.0
    # Workflow total_cost should match aggregated task costs
    assert pytest.approx(engine.workflow.total_cost, rel=0, abs=1e-6) == total_actual
    assert len(results) >= 1


@pytest.mark.asyncio
async def test_task_actual_duration_hours_matches_wall_time(
    tmp_path, cost_time_workflow
):
    out = OutputConfig(base_output_dir=tmp_path, create_run_subdirectory=False)
    engine = WorkflowExecutionEngine(
        workflow=cost_time_workflow,
        agent_registry=AgentRegistry(),
        manager_agent=_AlternatingAssignManager(),
        stakeholder_agent=next(
            a
            for a in cost_time_workflow.agents.values()
            if a.agent_type == "stakeholder"
        ),
        output_config=out,
        max_timesteps=10,
        enable_timestep_logging=False,
        enable_final_metrics_logging=False,
        seed=42,
    )

    await engine.run_full_execution()
    # Check conversion on tasks: execution_time_seconds / 3600 stored as actual_duration_hours
    a = next(t for t in engine.workflow.tasks.values() if t.name == "A")
    b = next(t for t in engine.workflow.tasks.values() if t.name == "B")
    assert (
        pytest.approx(a.actual_duration_hours or 0.0, rel=0, abs=1e-9) == 3.6 / 3600.0
    )
    assert (
        pytest.approx(b.actual_duration_hours or 0.0, rel=0, abs=1e-9) == 7.2 / 3600.0
    )
    # Check total simulated duration across tasks matches the sum of agent-reported times
    total_sim_hours = sum(
        float(t.actual_duration_hours or 0.0) for t in engine.workflow.tasks.values()
    )
    expected_hours = (3.6 + 7.2) / 3600.0
    assert pytest.approx(total_sim_hours, rel=0, abs=1e-9) == expected_hours
    # Workflow aggregate should match
    assert (
        pytest.approx(engine.workflow.total_simulated_hours, rel=0, abs=1e-9)
        == expected_hours
    )
    # Sanity: timestamps present and ordered
    assert engine.workflow.started_at is not None
    assert engine.workflow.completed_at is not None
    assert engine.workflow.completed_at >= engine.workflow.started_at
