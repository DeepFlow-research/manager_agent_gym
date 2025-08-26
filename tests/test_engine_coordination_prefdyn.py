import pytest
from uuid import uuid4

# Minimal stakeholder with empty preferences
from manager_agent_gym.core.workflow_agents.stakeholder_agent import StakeholderAgent
from manager_agent_gym.schemas.workflow_agents.stakeholder import StakeholderConfig
from manager_agent_gym.schemas.preferences.preference import PreferenceWeights

from manager_agent_gym.core.execution.engine import WorkflowExecutionEngine
from manager_agent_gym.schemas.core.workflow import Workflow
from manager_agent_gym.core.workflow_agents.registry import AgentRegistry
from manager_agent_gym.core.manager_agent.interface import ManagerAgent
from manager_agent_gym.schemas.execution.manager import ManagerObservation
from manager_agent_gym.schemas.execution.state import ExecutionState
from manager_agent_gym.schemas.workflow_agents.stakeholder import (
    StakeholderPublicProfile,
)


class _StubManager(ManagerAgent):
    def __init__(self):
        super().__init__(agent_id="m", preferences=PreferenceWeights(preferences=[]))

    async def take_action(self, observation: ManagerObservation):
        from manager_agent_gym.schemas.execution.manager_actions import NoOpAction

        return NoOpAction(reasoning="noop", success=True, result_summary="noop")

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
        from manager_agent_gym.schemas.execution.manager_actions import NoOpAction

        return NoOpAction(reasoning="noop", success=True, result_summary="noop")

    def reset(self) -> None:
        pass


@pytest.mark.asyncio
async def test_registry_scheduling_adds_agent_and_syncs_workflow() -> None:
    w = Workflow(name="w", workflow_goal="d", owner_id=uuid4())
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
    w.add_agent(stakeholder)
    engine = WorkflowExecutionEngine(
        workflow=w,
        agent_registry=AgentRegistry(),
        manager_agent=_StubManager(),
        stakeholder_agent=stakeholder,
        communication_service=None,
        output_config=None,
        enable_timestep_logging=False,
        enable_final_metrics_logging=False,
        seed=42,
    )

    # Schedule add via registry API (timestep 0)
    # Build a minimal AIAgentConfig compatible with registry API
    from manager_agent_gym.schemas.workflow_agents import AIAgentConfig

    ai_cfg = AIAgentConfig(
        agent_id="ai_dummy",
        agent_type="ai",
        system_prompt="simple agent",
        agent_description="simple agent",
        agent_capabilities=["simple agent"],
    )

    engine.agent_registry.schedule_agent_add(0, config=ai_cfg, reason="test add")

    await engine.execute_timestep()
    # Registry has the agent and workflow agents synced
    reg_agents = [a.agent_id for a in engine.agent_registry.list_agents()]
    # The scheduled DummyAI has default id "ai_dummy"
    assert "ai_dummy" in reg_agents
    assert "ai_dummy" in engine.workflow.agents
