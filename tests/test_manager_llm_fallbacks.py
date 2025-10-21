from uuid import uuid4

from manager_agent_gym.schemas.manager.observation import ManagerObservation
from manager_agent_gym.schemas.agents.stakeholder import (
    StakeholderPublicProfile,
)


def _obs() -> ManagerObservation:
    return ManagerObservation(
        timestep=0,
        workflow_summary="",
        workflow_id=uuid4(),
        execution_state="running",
        task_status_counts={},
        ready_task_ids=[],
        running_task_ids=[],
        completed_task_ids=[],
        failed_task_ids=[],
        available_agent_metadata=[],
        recent_messages=[],
        workflow_progress=0.0,
        constraints=[],
        task_ids=[],
        resource_ids=[],
        agent_ids=[],
        stakeholder_profile=StakeholderPublicProfile(
            display_name="Test Stakeholder", role="Owner", preference_summary=""
        ),
    )
