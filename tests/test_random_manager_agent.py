import pytest  # type: ignore[import-not-found]
from uuid import uuid4

from manager_agent_gym.core.agents.manager_agent.implementations.random_manager import (
    RandomManagerAgent,
)
from manager_agent_gym.schemas.preferences.preference import PreferenceSnapshot
from manager_agent_gym.schemas.manager.observation import ManagerObservation
from manager_agent_gym.schemas.agents.stakeholder import (
    StakeholderPublicProfile,
)


def _obs(ready: bool = True, available: bool = True) -> ManagerObservation:
    return ManagerObservation(
        timestep=0,
        workflow_summary="",
        workflow_id=uuid4(),
        execution_state="running",
        task_status_counts={},
        ready_task_ids=[uuid4()] if ready else [],
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


@pytest.mark.asyncio
async def test_random_manager_action_type_and_ids(monkeypatch) -> None:
    # Eliminate sleep delay
    monkeypatch.setattr("time.sleep", lambda *_args, **_kwargs: None)

    mgr = RandomManagerAgent(preferences=PreferenceSnapshot(preferences=[]), seed=42)

    # Case 1: both ready and available -> may choose AssignTaskAction
    action = await mgr.take_action(_obs(ready=True, available=True))
    # Must be one of the allowed action classes
    from manager_agent_gym.core.agents.manager_agent.actions import (
        AssignTaskAction,
        NoOpAction,
        GetWorkflowStatusAction,
        GetAvailableAgentsAction,
        GetPendingTasksAction,
    )

    assert isinstance(
        action,
        (
            AssignTaskAction,
            NoOpAction,
            GetWorkflowStatusAction,
            GetAvailableAgentsAction,
            GetPendingTasksAction,
        ),
    )
    if isinstance(action, AssignTaskAction):
        # IDs must come from observation
        assert action.agent_id == "a1"
        # task_id string parses as UUID
        import uuid

        uuid.UUID(action.task_id)

    # Case 2: missing availability -> should not be AssignTaskAction
    action2 = await mgr.take_action(_obs(ready=True, available=False))
    assert not action2.__class__.__name__.lower().startswith("assigntask")
