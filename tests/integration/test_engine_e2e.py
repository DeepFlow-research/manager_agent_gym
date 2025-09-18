import pytest
from uuid import uuid4

from manager_agent_gym.schemas.core.workflow import Workflow
from manager_agent_gym.schemas.core.tasks import Task
from manager_agent_gym.schemas.preferences.preference import PreferenceWeights
from manager_agent_gym.schemas.config import OutputConfig
from manager_agent_gym.core.execution.engine import WorkflowExecutionEngine
from manager_agent_gym.core.workflow_agents.interface import AgentInterface
from manager_agent_gym.core.workflow_agents.registry import AgentRegistry
from manager_agent_gym.schemas.unified_results import create_task_result
from manager_agent_gym.core.workflow_agents.stakeholder_agent import StakeholderAgent
from manager_agent_gym.schemas.workflow_agents.stakeholder import StakeholderConfig
from typing import cast
from tests.helpers.stubs import ManagerAssignFirstReady

pytestmark = pytest.mark.integration


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
        # Immediate success with no resources
        return create_task_result(
            task_id=task.id,
            agent_id=self.agent_id,
            success=True,
            execution_time=0.01,
            resources=[],
        )


# Use shared Manager stub from tests.helpers.stubs


def _workflow_two_step():
    w = Workflow(name="w", workflow_goal="d", owner_id=uuid4())
    t1 = Task(name="A", description="d")
    t2 = Task(name="B", description="d", dependency_task_ids=[t1.id])
    w.add_task(t1)
    w.add_task(t2)
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
async def test_full_execution_completes_workflow(tmp_path, monkeypatch):
    # Disable output writing for speed and isolation
    out = OutputConfig(base_output_dir=tmp_path, create_run_subdirectory=False)
    engine = WorkflowExecutionEngine(
        workflow=_workflow_two_step(),
        agent_registry=AgentRegistry(),
        manager_agent=ManagerAssignFirstReady(),
        stakeholder_agent=cast(
            StakeholderAgent,
            next(
                a
                for a in _workflow_two_step().agents.values()
                if a.agent_type == "stakeholder"
            ),
        ),
        output_config=out,
        max_timesteps=5,
        enable_timestep_logging=False,
        enable_final_metrics_logging=False,
        seed=42,
    )

    results = await engine.run_full_execution()
    assert engine.execution_state.value in {"completed", "failed", "cancelled"}
    # Expect completion in this simple setup
    assert engine.execution_state.value == "completed"
    assert engine.workflow.is_complete()
    assert len(results) >= 1


@pytest.mark.asyncio
async def test_engine_honors_end_workflow_request(tmp_path):
    out = OutputConfig(base_output_dir=tmp_path, create_run_subdirectory=False)
    engine = WorkflowExecutionEngine(
        workflow=_workflow_two_step(),
        agent_registry=AgentRegistry(),
        manager_agent=ManagerAssignFirstReady(),
        stakeholder_agent=cast(
            StakeholderAgent,
            next(
                a
                for a in _workflow_two_step().agents.values()
                if a.agent_type == "stakeholder"
            ),
        ),
        output_config=out,
        max_timesteps=5,
        enable_timestep_logging=False,
        enable_final_metrics_logging=False,
        seed=42,
    )

    # Request end immediately
    engine.communication_service.request_end_workflow("test cancel")
    results = await engine.run_full_execution()
    assert engine.execution_state.value == "cancelled"
    assert isinstance(results, list)
