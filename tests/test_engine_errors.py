import pytest
from uuid import uuid4

from manager_agent_gym.core.workflow.engine import WorkflowExecutionEngine
from manager_agent_gym.schemas.domain.workflow import Workflow
from manager_agent_gym.core.agents.workflow_agents.tools.registry import AgentRegistry
from manager_agent_gym.schemas.domain.task import Task
from typing import cast
from manager_agent_gym.core.agents.manager_agent.common.interface import ManagerAgent
from manager_agent_gym.core.workflow.services import WorkflowMutations


@pytest.mark.asyncio
async def test_execute_timestep_requires_manager() -> None:
    w = Workflow(name="w", workflow_goal="d", owner_id=uuid4())
    WorkflowMutations.add_task(w, Task(name="t", description="d"))
    # Minimal stakeholder to satisfy engine signature
    from manager_agent_gym.core.agents.stakeholder_agent.stakeholder_agent import (
        StakeholderAgent,
    )
    from manager_agent_gym.schemas.agents.stakeholder import StakeholderConfig
    from manager_agent_gym.schemas.preferences.preference import PreferenceSnapshot

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
