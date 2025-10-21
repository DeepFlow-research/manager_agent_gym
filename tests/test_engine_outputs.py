import pytest
from pathlib import Path
from uuid import uuid4

from manager_agent_gym.core.workflow.engine import WorkflowExecutionEngine
from manager_agent_gym.core.workflow.schemas.config import OutputConfig
from manager_agent_gym.schemas.domain.workflow import Workflow
from manager_agent_gym.schemas.domain.task import Task
from manager_agent_gym.core.agents.workflow_agents.tools.registry import AgentRegistry
from manager_agent_gym.core.agents.manager_agent.common.interface import ManagerAgent
from manager_agent_gym.schemas.preferences.preference import PreferenceSnapshot
from manager_agent_gym.schemas.manager.observation import ManagerObservation
from manager_agent_gym.schemas.domain.resource import Resource
from manager_agent_gym.core.agents.stakeholder_agent.stakeholder_agent import (
    StakeholderAgent,
)
from manager_agent_gym.schemas.agents.stakeholder import StakeholderConfig
from manager_agent_gym.core.execution.schemas.state import ExecutionState
from manager_agent_gym.schemas.agents.stakeholder import (
    StakeholderPublicProfile,
)
from manager_agent_gym.core.workflow.services import WorkflowMutations
from tests.helpers.stubs import ManagerNoOp


# Use shared Manager stub from tests.helpers.stubs


@pytest.mark.parametrize("enable_logs", [True, False])
@pytest.mark.asyncio
async def test_output_files_written_when_enabled(tmp_path: Path, enable_logs: bool):
    out = OutputConfig(base_output_dir=tmp_path, create_run_subdirectory=False)
    w = Workflow(name="w", workflow_goal="d", owner_id=uuid4())
    WorkflowMutations.add_task(w, Task(name="t", description="d"))
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
    stakeholder = StakeholderAgent(config=stakeholder_cfg)
    WorkflowMutations.add_agent(w, stakeholder)

    engine = WorkflowExecutionEngine(
        workflow=w,
        agent_registry=AgentRegistry(),
        manager_agent=ManagerNoOp(),
        stakeholder_agent=stakeholder,
        output_config=out,
        enable_timestep_logging=enable_logs,
        enable_final_metrics_logging=enable_logs,
        seed=42,
    )

    await engine.run_full_execution()
    if enable_logs:
        assert out.get_timestep_file_path(0).exists()
        assert out.get_final_metrics_path().exists()
    else:
        assert not out.get_timestep_file_path(0).exists()
        assert not out.get_final_metrics_path().exists()


@pytest.mark.asyncio
async def test_cost_bucket_and_cost_efficiency_when_agents_incur_cost(tmp_path: Path):
    # Run the real engine with cost-returning stub agents to ensure actual_cost is sourced from agents
    out = OutputConfig(base_output_dir=tmp_path, create_run_subdirectory=False)
    w = Workflow(name="w", workflow_goal="d", owner_id=uuid4())

    # Two tasks executed in order; second depends on the first to make assignment deterministic
    t1 = Task(name="A", description="d", estimated_cost=100.0)
    t2 = Task(
        name="B", description="d", estimated_cost=200.0, dependency_task_ids=[t1.id]
    )
    WorkflowMutations.add_task(w, t1)
    WorkflowMutations.add_task(w, t2)

    # Define costed stub agents
    from manager_agent_gym.core.agents.workflow_agents.common.interface import (
        AgentInterface,
    )

    class _CostAgent(AgentInterface):
        def __init__(self, agent_id: str, agent_type: str, cost: float):
            from manager_agent_gym.schemas.agents import AgentConfig

            super().__init__(
                AgentConfig(
                    agent_id=agent_id,
                    agent_type=agent_type,
                    system_prompt=f"stub {agent_type} agent",
                    model_name="none",
                    agent_description=f"stub {agent_type} agent",
                    agent_capabilities=[f"stub {agent_type} agent"],
                )
            )
            self._cost = float(cost)

        async def execute_task(self, task: Task, resources: list[Resource]):
            from manager_agent_gym.core.execution.schemas.results import create_task_result

            return create_task_result(
                task_id=task.id,
                agent_id=self.agent_id,
                success=True,
                execution_time=0.01,
                resources=[],
                cost=self._cost,
            )

    # Add two agents with distinct costs
    ai = _CostAgent("ai-1", "ai", cost=60.0)
    human = _CostAgent("human-1", "human", cost=80.0)
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
    stakeholder = StakeholderAgent(config=stakeholder_cfg)
    WorkflowMutations.add_agent(w, stakeholder)

    # Manager that alternates assignments so A->ai, B->human
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
                self._last_idx = (self._last_idx + 1) % len(
                    observation.available_agent_metadata
                )
                return AssignTaskAction(
                    reasoning="assign",
                    task_id=str(observation.ready_task_ids[0]),
                    agent_id=observation.available_agent_metadata[
                        self._last_idx
                    ].agent_id,
                    success=True,
                    result_summary="assign",
                )
            return NoOpAction(reasoning="idle", success=True, result_summary="idle")

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
            # Derive action via current observation
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

        def reset(self):
            pass

    engine = WorkflowExecutionEngine(
        workflow=w,
        agent_registry=AgentRegistry(),
        manager_agent=_AlternatingAssignManager(),
        stakeholder_agent=stakeholder,
        output_config=out,
        enable_timestep_logging=False,
        enable_final_metrics_logging=False,
        max_timesteps=10,
        seed=42,
    )

    await engine.run_full_execution()

    # Verify per-task costs reflect their executing agents
    a = next(t for t in engine.workflow.tasks.values() if t.name == "A")
    b = next(t for t in engine.workflow.tasks.values() if t.name == "B")
    assert pytest.approx(a.actual_cost or 0.0, rel=0, abs=1e-9) == 60.0
    assert pytest.approx(b.actual_cost or 0.0, rel=0, abs=1e-9) == 80.0

    # And total cost equals the sum of agent-reported costs
    total_actual = sum(
        float(t.actual_cost or 0.0) for t in engine.workflow.tasks.values()
    )
    assert pytest.approx(total_actual, rel=0, abs=1e-9) == 140.0
