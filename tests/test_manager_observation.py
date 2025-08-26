import pytest
from uuid import uuid4

from manager_agent_gym.core.manager_agent.interface import ManagerAgent
from manager_agent_gym.schemas.core.workflow import Workflow
from manager_agent_gym.schemas.core.tasks import Task
from manager_agent_gym.schemas.core.base import TaskStatus
from manager_agent_gym.schemas.preferences.preference import PreferenceWeights
from manager_agent_gym.core.communication.service import CommunicationService
from manager_agent_gym.schemas.execution.state import ExecutionState
from manager_agent_gym.schemas.execution.manager import ManagerObservation
from manager_agent_gym.schemas.workflow_agents.stakeholder import (
    StakeholderPublicProfile,
)


class _Mgr(ManagerAgent):
    def __init__(self):
        super().__init__(agent_id="m", preferences=PreferenceWeights(preferences=[]))

    async def take_action(self, observation: ManagerObservation):
        raise NotImplementedError

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

        # Provide a trivial implementation to satisfy abstract base class
        return NoOpAction(reasoning="noop", success=True, result_summary="noop")

    def reset(self) -> None:
        pass


@pytest.mark.asyncio
async def test_create_observation_counts_and_progress() -> None:
    w = Workflow(name="w", workflow_goal="d", owner_id=uuid4())
    t1 = Task(name="A", description="d")
    t2 = Task(name="B", description="d")
    w.add_task(t1)
    w.add_task(t2)
    # mark one completed
    t1.status = TaskStatus.COMPLETED

    svc = CommunicationService()
    # seed one message
    await svc.send_direct_message("a", "m", "hi")

    mgr = _Mgr()
    obs = await mgr.create_observation(
        workflow=w,
        execution_state=ExecutionState.RUNNING,
        stakeholder_profile=StakeholderPublicProfile(
            display_name="Test Stakeholder", role="Owner", preference_summary=""
        ),
        current_timestep=3,
        running_tasks={},
        completed_task_ids={t1.id},
        failed_task_ids=set(),
        communication_service=svc,
    )

    assert obs.timestep == 3
    assert obs.workflow_progress == 0.5
    assert obs.task_status_counts.get("completed") == 1
    assert len(obs.recent_messages) >= 1
    # ID universes contain known IDs
    assert t1.id in obs.task_ids and t2.id in obs.task_ids
