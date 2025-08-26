from __future__ import annotations

import pytest

from uuid import uuid4

from manager_agent_gym.core.communication.service import CommunicationService
from manager_agent_gym.core.manager_agent.structured_manager import (
    ChainOfThoughtManagerAgent,
)
from manager_agent_gym.schemas.core.workflow import Workflow
from manager_agent_gym.schemas.preferences.preference import PreferenceWeights
from manager_agent_gym.schemas.execution.state import ExecutionState
from manager_agent_gym.schemas.workflow_agents.stakeholder import (
    StakeholderPublicProfile,
)


@pytest.mark.asyncio
async def test_structured_manager_prompt_includes_stakeholder_messages() -> None:
    # Arrange: minimal workflow and communication service
    workflow = Workflow(
        name="w",
        workflow_goal="g",
        owner_id=uuid4(),
        tasks={},
        resources={},
        agents={},
        messages=[],
    )
    comms = CommunicationService()

    # Manager under test
    manager = ChainOfThoughtManagerAgent(preferences=PreferenceWeights(preferences=[]))

    # Simulate stakeholder sending a direct message to this manager's agent_id
    stake_id = "stakeholder_1"
    target_manager_id = manager.agent_id  # "structured_manager"
    message_text = "stake_msg_123_included"
    await comms.send_direct_message(
        from_agent=stake_id, to_agent=target_manager_id, content=message_text
    )

    # Act: build observation and prepare context prompt
    observation = await manager.create_observation(
        workflow=workflow,
        execution_state=ExecutionState.RUNNING,
        current_timestep=0,
        running_tasks={},
        completed_task_ids=set(),
        failed_task_ids=set(),
        communication_service=comms,
        stakeholder_profile=StakeholderPublicProfile(
            display_name="Test Stakeholder", role="Owner", preference_summary=""
        ),
    )
    observation.max_timesteps = 10

    prompt = manager._prepare_context(
        observation
    )  # Access internal to inspect prompt content
    print(prompt)
    # Assert: stakeholder message appears in the "Recent Communications (sample)" section
    assert stake_id in prompt
    assert target_manager_id in prompt
    assert message_text in prompt
    # remove debug assertion
