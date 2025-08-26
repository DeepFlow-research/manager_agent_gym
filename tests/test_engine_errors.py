import pytest
from uuid import uuid4

from manager_agent_gym.core.execution.engine import WorkflowExecutionEngine
from manager_agent_gym.schemas.core.workflow import Workflow
from manager_agent_gym.core.workflow_agents.registry import AgentRegistry
from manager_agent_gym.schemas.core.tasks import Task
from typing import cast
from manager_agent_gym.core.manager_agent.interface import ManagerAgent


@pytest.mark.asyncio
async def test_execute_timestep_requires_manager() -> None:
    w = Workflow(name="w", workflow_goal="d", owner_id=uuid4())
    w.add_task(Task(name="t", description="d"))
    # Minimal stakeholder to satisfy engine signature
    from manager_agent_gym.core.workflow_agents.stakeholder_agent import (
        StakeholderAgent,
    )
    from manager_agent_gym.schemas.workflow_agents.stakeholder import StakeholderConfig
    from manager_agent_gym.schemas.preferences.preference import PreferenceWeights

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
    with pytest.raises(ValueError):
        _ = WorkflowExecutionEngine(
            workflow=w,
            agent_registry=AgentRegistry(),
            manager_agent=cast(ManagerAgent, None),
            stakeholder_agent=stakeholder,
            enable_timestep_logging=False,
            enable_final_metrics_logging=False,
            seed=42,
        )
