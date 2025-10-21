import pytest
from uuid import uuid4

from manager_agent_gym.core.agents.manager_agent.common.interface import ManagerAgent
from manager_agent_gym.schemas.domain.workflow import Workflow
from manager_agent_gym.schemas.domain.task import Task
from manager_agent_gym.schemas.domain.base import TaskStatus
from manager_agent_gym.schemas.preferences.preference import PreferenceSnapshot
from manager_agent_gym.core.communication.service import CommunicationService
from manager_agent_gym.core.execution.schemas.state import ExecutionState
from manager_agent_gym.schemas.manager.observation import ManagerObservation
from manager_agent_gym.schemas.agents.stakeholder import (
    StakeholderPublicProfile,
)
from manager_agent_gym.core.workflow.services import WorkflowMutations


class _Mgr(ManagerAgent):
    def __init__(self):
        super().__init__(agent_id="m", preferences=PreferenceSnapshot(preferences=[]))

    async def take_action(self, observation: ManagerObservation):
        raise NotImplementedError

    async def step(
        self,
        workflow: Workflow,
        execution_state: ExecutionState,
        stakeholder_profile: StakeholderPublicProfile | None = None,
        current_timestep: int = 0,
        running_tasks: dict | None = None,
        completed_task_ids: set | None = None,
        failed_task_ids: set | None = None,
        communication_service=None,
        previous_reward: float = 0.0,
        done: bool = False,
    ):
        from manager_agent_gym.core.agents.manager_agent.actions import NoOpAction

        # Provide a trivial implementation to satisfy abstract base class
        return NoOpAction(reasoning="noop", success=True, result_summary="noop")

    def reset(self) -> None:
        pass


@pytest.mark.asyncio
async def test_create_observation_counts_and_progress() -> None:
    w = Workflow(name="w", workflow_goal="d", owner_id=uuid4())
    t1 = Task(name="A", description="d")
    t2 = Task(name="B", description="d")
    WorkflowMutations.add_task(w, t1)
    WorkflowMutations.add_task(w, t2)
    # mark one completed
    t1.status = TaskStatus.COMPLETED

    svc = CommunicationService()
    # seed one message
    await svc.send_direct_message("a", "m", "hi")

    mgr = _Mgr()
    obs = await mgr.create_observation(
        workflow=w,
        execution_state=ExecutionState.RUNNING,
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
