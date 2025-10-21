import pytest  # type: ignore[import-not-found]
from uuid import uuid4

from manager_agent_gym.schemas.domain.workflow import Workflow
from manager_agent_gym.schemas.domain.task import Task
from manager_agent_gym.schemas.domain.base import TaskStatus
from manager_agent_gym.schemas.preferences.preference import PreferenceSnapshot
from manager_agent_gym.core.workflow.schemas.config import OutputConfig
from manager_agent_gym.core.workflow.engine import WorkflowExecutionEngine
from manager_agent_gym.core.agents.workflow_agents.common.interface import (
    AgentInterface,
)
from manager_agent_gym.core.agents.workflow_agents.tools.registry import AgentRegistry
from manager_agent_gym.core.execution.schemas.results import create_task_result
from manager_agent_gym.core.agents.stakeholder_agent.stakeholder_agent import (
    StakeholderAgent,
)
from manager_agent_gym.schemas.agents.stakeholder import StakeholderConfig
from typing import cast
from tests.helpers.stubs import ManagerAssignFirstReady
from manager_agent_gym.core.workflow.services import WorkflowMutations
from manager_agent_gym.core.workflow.services import WorkflowQueries

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
        # Complete immediately with no outputs
        return create_task_result(
            task_id=task.id,
            agent_id=self.agent_id,
            success=True,
            execution_time=0.01,
            resources=[],
        )


# Use shared Manager stub from tests.helpers.stubs


def _workflow_three_step_chain() -> Workflow:
    w = Workflow(name="w", workflow_goal="d", owner_id=uuid4())
    t1 = Task(name="A", description="d")
    t2 = Task(name="B", description="d", dependency_task_ids=[t1.id])
    t3 = Task(name="C", description="d", dependency_task_ids=[t2.id])
    WorkflowMutations.add_task(w, t1)
    WorkflowMutations.add_task(w, t2)
    WorkflowMutations.add_task(w, t3)
    agent = _StubAgent("worker-1")
    WorkflowMutations.add_agent(w, agent)
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
async def test_scheduler_moves_ready_to_running_then_completed_in_chain(tmp_path):
    out = OutputConfig(base_output_dir=tmp_path, create_run_subdirectory=False)
    engine = WorkflowExecutionEngine(
        workflow=_workflow_three_step_chain(),
        agent_registry=AgentRegistry(),
        manager_agent=ManagerAssignFirstReady(),
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
    assert WorkflowQueries.is_complete(engine.workflow)
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
    WorkflowMutations.add_task(engine.workflow, parent)
    WorkflowMutations.add_task(engine.workflow, child1)
    WorkflowMutations.add_task(engine.workflow, child2)

    # Execute forward until both children complete. Parent must not be considered complete
    # while any child remains incomplete. Also, parent should never appear in ready tasks.
    remaining = {child1.id, child2.id}
    for _ in range(10):
        res = await engine.execute_timestep()
        # Parent is composite: not in ready list
        ready_ids = {t.id for t in WorkflowQueries.get_ready_tasks(engine.workflow)}
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
            assert not WorkflowQueries.is_complete(engine.workflow)
        else:
            break

    # After loop, both children should be completed and therefore workflow complete
    assert not remaining
    assert WorkflowQueries.is_complete(engine.workflow)


def _workflow_n_step_chain(n: int) -> Workflow:
    w = Workflow(name="w20", workflow_goal="d", owner_id=uuid4())
    prev = None
    for i in range(n):
        if prev is None:
            t = Task(name=f"T{i + 1}", description="d")
        else:
            t = Task(name=f"T{i + 1}", description="d", dependency_task_ids=[prev])
        WorkflowMutations.add_task(w, t)
        prev = t.id
    WorkflowMutations.add_agent(w, _StubAgent("worker-1"))
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
async def test_20_node_chain_completes_within_500_timesteps(tmp_path):
    out = OutputConfig(base_output_dir=tmp_path, create_run_subdirectory=False)
    engine = WorkflowExecutionEngine(
        workflow=_workflow_n_step_chain(20),
        agent_registry=AgentRegistry(),
        manager_agent=ManagerAssignFirstReady(),
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
    assert WorkflowQueries.is_complete(engine.workflow)
    assert engine.current_timestep <= 500
    # All 20 top-level tasks should be completed
    statuses = [
        t.status for t in engine.workflow.tasks.values() if t.name.startswith("T")
    ]
    assert len(statuses) == 20 and all(s == TaskStatus.COMPLETED for s in statuses)
