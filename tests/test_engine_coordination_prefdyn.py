import pytest
from uuid import uuid4

# Minimal stakeholder with empty preferences
from manager_agent_gym.core.agents.stakeholder_agent.stakeholder_agent import (
    StakeholderAgent,
)
from manager_agent_gym.schemas.agents.stakeholder import StakeholderConfig
from manager_agent_gym.schemas.preferences.preference import PreferenceSnapshot

from manager_agent_gym.core.workflow.engine import WorkflowExecutionEngine
from manager_agent_gym.schemas.domain.workflow import Workflow
from manager_agent_gym.core.agents.workflow_agents.tools.registry import AgentRegistry
from tests.helpers.stubs import ManagerNoOp
from manager_agent_gym.core.workflow.services import WorkflowMutations


# Use shared Manager stub from tests.helpers.stubs


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
        communication_service=None,
        output_config=None,
        enable_timestep_logging=False,
        enable_final_metrics_logging=False,
        seed=42,
    )

    # Schedule add via registry API (timestep 0)
    # Build a minimal AIAgentConfig compatible with registry API
    from manager_agent_gym.schemas.agents import AIAgentConfig

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


@pytest.mark.asyncio
async def test_registry_scheduling_remove_syncs_workflow() -> None:
    w = Workflow(name="w", workflow_goal="d", owner_id=uuid4())
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
        communication_service=None,
        output_config=None,
        enable_timestep_logging=False,
        enable_final_metrics_logging=False,
        seed=42,
    )

    # First, add then remove the same agent across timesteps 0 and 1
    from manager_agent_gym.schemas.agents import AIAgentConfig

    ai_cfg = AIAgentConfig(
        agent_id="ai_tmp",
        agent_type="ai",
        system_prompt="simple agent",
        agent_description="simple agent",
        agent_capabilities=["simple agent"],
    )

    engine.agent_registry.schedule_agent_add(0, config=ai_cfg, reason="add tmp")
    await engine.execute_timestep()
    assert "ai_tmp" in {a.agent_id for a in engine.agent_registry.list_agents()}
    assert "ai_tmp" in engine.workflow.agents

    engine.agent_registry.schedule_agent_remove(1, agent_id="ai_tmp", reason="rm tmp")
    await engine.execute_timestep()
    assert "ai_tmp" not in {a.agent_id for a in engine.agent_registry.list_agents()}
    # Workflow sync mirrors registry removals after the tick
    assert "ai_tmp" not in engine.workflow.agents
