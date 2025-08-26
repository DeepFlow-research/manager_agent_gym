import pytest  # type: ignore[import-not-found]
from uuid import uuid4

from manager_agent_gym.schemas.core.workflow import Workflow
from manager_agent_gym.schemas.core.tasks import Task
from manager_agent_gym.schemas.core.base import TaskStatus
from manager_agent_gym.schemas.preferences.preference import PreferenceWeights
from manager_agent_gym.schemas.config import OutputConfig
from manager_agent_gym.core.execution.engine import WorkflowExecutionEngine
from manager_agent_gym.core.workflow_agents.interface import AgentInterface
from manager_agent_gym.core.workflow_agents.registry import AgentRegistry
from manager_agent_gym.core.manager_agent.interface import ManagerAgent
from manager_agent_gym.schemas.execution.manager import ManagerObservation
from manager_agent_gym.schemas.unified_results import create_task_result
from manager_agent_gym.core.workflow_agents.stakeholder_agent import StakeholderAgent
from manager_agent_gym.schemas.workflow_agents.stakeholder import StakeholderConfig
from manager_agent_gym.schemas.execution.state import ExecutionState
from manager_agent_gym.schemas.workflow_agents.stakeholder import (
    StakeholderPublicProfile,
)
from typing import cast


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
        # Complete immediately with no outputs
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
        obs = await self.create_observation(
            workflow=workflow,
            execution_state=execution_state,
            stakeholder_profile=stakeholder_profile,
            current_timestep=current_timestep,
            running_tasks=running_tasks,
            completed_task_ids=completed_task_ids,
            failed_task_ids=failed_task_ids,
            communication_service=communication_service,
        )
        return await self.take_action(obs)


def _workflow_three_step_chain() -> Workflow:
    w = Workflow(name="w", workflow_goal="d", owner_id=uuid4())
    t1 = Task(name="A", description="d")
    t2 = Task(name="B", description="d", dependency_task_ids=[t1.id])
    t3 = Task(name="C", description="d", dependency_task_ids=[t2.id])
    w.add_task(t1)
    w.add_task(t2)
    w.add_task(t3)
    agent = _StubAgent("worker-1")
    w.add_agent(agent)
    # Minimal stakeholder with empty preferences to satisfy evaluation
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
    w.add_agent(StakeholderAgent(config=stakeholder_cfg))
    return w


@pytest.mark.asyncio
async def test_scheduler_moves_ready_to_running_then_completed_in_chain(tmp_path):
    out = OutputConfig(base_output_dir=tmp_path, create_run_subdirectory=False)
    engine = WorkflowExecutionEngine(
        workflow=_workflow_three_step_chain(),
        agent_registry=AgentRegistry(),
        manager_agent=_StubManager(),
        stakeholder_agent=cast(
            StakeholderAgent,
            next(
                a
                for a in _workflow_three_step_chain().agents.values()
                if a.agent_type == "stakeholder"
            ),
        ),
        output_config=out,
        max_timesteps=10,
        enable_timestep_logging=False,
        enable_final_metrics_logging=False,
        seed=42,
    )

    # Helper to resolve fresh task objects each timestep
    def get_task(name: str) -> Task:
        return next(t for t in engine.workflow.tasks.values() if t.name == name)

    # Timestep 0: manager assigns A, engine starts it
    res0 = await engine.execute_timestep()
    assert get_task("A").status == TaskStatus.RUNNING
    assert get_task("B").status == TaskStatus.PENDING
    assert get_task("C").status == TaskStatus.PENDING
    assert res0.metadata.get("tasks_started", []) == [str(get_task("A").id)]
    assert res0.metadata.get("tasks_completed", []) == []

    # Timestep 1: engine first processes running tasks (A completes) before manager acts; B not assigned yet
    res1 = await engine.execute_timestep()
    assert get_task("A").status == TaskStatus.COMPLETED
    # With READY semantics, B should become READY at this point
    assert get_task("B").status == TaskStatus.READY
    assert get_task("C").status == TaskStatus.PENDING
    assert res1.metadata.get("tasks_completed", []) == [str(get_task("A").id)]
    # No new starts until next timestep when manager assigns B
    assert res1.metadata.get("tasks_started", []) == []

    # Timestep 2: manager assigns B, engine starts it
    res2 = await engine.execute_timestep()
    assert get_task("B").status == TaskStatus.RUNNING
    assert get_task("C").status == TaskStatus.PENDING
    assert res2.metadata.get("tasks_started", []) == [str(get_task("B").id)]
    assert res2.metadata.get("tasks_completed", []) == []

    # Timestep 3: engine completes B; C becomes READY (engine marks READY when computing readiness)
    res3 = await engine.execute_timestep()
    assert get_task("B").status == TaskStatus.COMPLETED
    assert get_task("C").status == TaskStatus.READY
    assert res3.metadata.get("tasks_completed", []) == [str(get_task("B").id)]
    assert res3.metadata.get("tasks_started", []) == []

    # Timestep 4: manager assigns C, engine starts it
    res4 = await engine.execute_timestep()
    assert get_task("C").status == TaskStatus.RUNNING
    assert res4.metadata.get("tasks_started", []) == [str(get_task("C").id)]
    assert res4.metadata.get("tasks_completed", []) == []

    # Timestep 5: engine completes C; workflow complete
    res5 = await engine.execute_timestep()
    assert get_task("C").status == TaskStatus.COMPLETED
    assert engine.workflow.is_complete()
    assert res5.metadata.get("tasks_completed", []) == [str(get_task("C").id)]

    # Now extend with a composite task having two atomic children that depend on C
    # Parent 'P' should not be considered complete while any child is incomplete.
    parent = Task(name="P", description="parent")
    child1 = Task(
        name="P1", description="child1", dependency_task_ids=[get_task("C").id]
    )
    child2 = Task(
        name="P2", description="child2", dependency_task_ids=[get_task("C").id]
    )
    # Attach as subtasks for hierarchy and also register atomic children for execution
    parent.add_subtask(child1)
    parent.add_subtask(child2)
    engine.workflow.add_task(parent)
    engine.workflow.add_task(child1)
    engine.workflow.add_task(child2)

    # Execute forward until both children complete. Parent must not be considered complete
    # while any child remains incomplete. Also, parent should never appear in ready tasks.
    remaining = {child1.id, child2.id}
    for _ in range(10):
        res = await engine.execute_timestep()
        # Parent is composite: not in ready list
        ready_ids = {t.id for t in engine.workflow.get_ready_tasks()}
        assert parent.id not in ready_ids
        # Mark any completed child
        for cid_str in res.metadata.get("tasks_completed", []):
            try:
                # UUIDs are serialized as strings
                from uuid import UUID

                cid = UUID(cid_str)
            except Exception:
                continue
            if cid in remaining:
                remaining.remove(cid)
        # If any child remains, workflow must not be complete
        if remaining:
            assert not engine.workflow.is_complete()
        else:
            break

    # After loop, both children should be completed and therefore workflow complete
    assert not remaining
    assert engine.workflow.is_complete()


def _workflow_n_step_chain(n: int) -> Workflow:
    w = Workflow(name="w20", workflow_goal="d", owner_id=uuid4())
    prev = None
    for i in range(n):
        if prev is None:
            t = Task(name=f"T{i + 1}", description="d")
        else:
            t = Task(name=f"T{i + 1}", description="d", dependency_task_ids=[prev])
        w.add_task(t)
        prev = t.id
    w.add_agent(_StubAgent("worker-1"))
    # Minimal stakeholder with empty preferences to satisfy evaluation
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
    w.add_agent(StakeholderAgent(config=stakeholder_cfg))
    return w


@pytest.mark.asyncio
async def test_20_node_chain_completes_within_500_timesteps(tmp_path):
    out = OutputConfig(base_output_dir=tmp_path, create_run_subdirectory=False)
    engine = WorkflowExecutionEngine(
        workflow=_workflow_n_step_chain(20),
        agent_registry=AgentRegistry(),
        manager_agent=_StubManager(),
        stakeholder_agent=cast(
            StakeholderAgent,
            next(
                a
                for a in _workflow_n_step_chain(20).agents.values()
                if a.agent_type == "stakeholder"
            ),
        ),
        output_config=out,
        max_timesteps=500,
        enable_timestep_logging=False,
        enable_final_metrics_logging=False,
        seed=42,
    )

    await engine.run_full_execution()
    # Completed successfully and did not exhaust timestep budget
    assert engine.workflow.is_complete()
    assert engine.current_timestep <= 500
    # All 20 top-level tasks should be completed
    statuses = [
        t.status for t in engine.workflow.tasks.values() if t.name.startswith("T")
    ]
    assert len(statuses) == 20 and all(s == TaskStatus.COMPLETED for s in statuses)
