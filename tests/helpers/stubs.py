from __future__ import annotations

import asyncio
from typing import Any
from uuid import UUID, uuid4

from manager_agent_gym.core.communication.service import CommunicationService
from manager_agent_gym.core.agents.manager_agent.common.interface import ManagerAgent
from manager_agent_gym.core.agents.workflow_agents.common.interface import (
    AgentInterface,
)
from manager_agent_gym.core.agents.stakeholder_agent.interface import StakeholderBase
from manager_agent_gym.schemas.domain.communication import MessageType
from manager_agent_gym.schemas.domain.resource import Resource
from manager_agent_gym.schemas.domain.task import Task
from manager_agent_gym.schemas.domain.workflow import Workflow
from manager_agent_gym.core.agents.manager_agent.actions import (
    RequestEndWorkflowAction,
    SendMessageAction,
)
from manager_agent_gym.core.execution.schemas.state import ExecutionState
from manager_agent_gym.schemas.preferences.preference import (
    PreferenceChangeEvent,
    PreferenceSnapshot,
)
from manager_agent_gym.core.execution.schemas.results import create_task_result
from manager_agent_gym.schemas.agents.stakeholder import (
    StakeholderConfig,
    StakeholderPublicProfile,
)
from manager_agent_gym.schemas.agents import AgentConfig
from manager_agent_gym.core.agents.manager_agent.actions import (
    AssignTaskAction,
    NoOpAction,
)


def make_empty_workflow() -> Workflow:
    return Workflow(
        name="test_workflow",
        workflow_goal="validate communication",
        owner_id=uuid4(),
        tasks={},
        resources={},
        agents={},
        messages=[],
    )


class StakeholderStub(StakeholderBase):
    """Stakeholder stub that replies directly and broadcasts once per timestep."""

    def __init__(self, agent_id: str = "stakeholder_1") -> None:
        config = StakeholderConfig(
            agent_id=agent_id,
            system_prompt="Stakeholder persona system prompt",
            name="Stakeholder",
            role="Owner",
            model_name="o3",
            preference_data=PreferenceSnapshot(preferences=[]),
            agent_description="Stakeholder",
            agent_capabilities=["Stakeholder"],
        )
        super().__init__(config)
        self._replied_timesteps: set[int] = set()

    async def execute_task(self, task: Task, resources: list[Resource]):
        return create_task_result(
            task_id=task.id,
            agent_id=self.agent_id,
            success=True,
            execution_time=0.001,
            resources=[],
            cost=0.0,
        )

    async def policy_step(self, current_timestep: int) -> None:
        if self.communication_service is None:
            return
        if current_timestep in self._replied_timesteps:
            return
        await self.communication_service.send_direct_message(
            from_agent=self.agent_id,
            to_agent="manager_agent",
            content=f"ack_t{current_timestep}",
            message_type=MessageType.RESPONSE,
        )
        await self.communication_service.broadcast_message(
            from_agent=self.agent_id,
            content=f"broadcast_t{current_timestep}",
            message_type=MessageType.BROADCAST,
        )
        self._replied_timesteps.add(current_timestep)

    def _build_public_profile(self):
        from manager_agent_gym.schemas.agents.stakeholder import (
            StakeholderPublicProfile,
        )

        return StakeholderPublicProfile(
            display_name="Stakeholder",
            role="Owner",
            preference_summary="Test preferences",
        )

    async def evaluate_for_timestep(
        self, timestep, validation_engine, workflow, communications, manager_actions
    ):
        """No-op evaluation for test stub."""
        pass

    def get_serializable_state(self, timestep: int) -> dict:
        """Return empty state for test stub."""
        return {"type": "test_stub", "timestep": timestep}

    def restore_from_state(self, state_dict: dict) -> None:
        """No-op restore for test stub."""
        pass

    def apply_weight_update(self, request: Any) -> PreferenceChangeEvent:
        """Stub weight update (returns no-op change event)."""
        return PreferenceChangeEvent(
            timestep=0,
            preferences=PreferenceSnapshot(preferences=[]),
            previous_weights={},
            new_weights={},
            change_type="none",
            magnitude=0.0,
            trigger_reason="test_stub",
        )

    def apply_weight_updates(self, requests: list[Any]) -> list[PreferenceChangeEvent]:
        return [self.apply_weight_update(r) for r in requests]


class ManagerSendsThenEnd(ManagerAgent):
    """Manager that sends a direct message to stakeholder on first step, then requests end."""

    def __init__(self, preferences: PreferenceSnapshot, receiver_id: str) -> None:
        super().__init__(agent_id="manager_agent", preferences=preferences)
        self._receiver_id = receiver_id
        self._sent_initial: bool = False

    async def step(
        self,
        workflow: Workflow,
        execution_state: ExecutionState,
        stakeholder_profile: StakeholderPublicProfile | None = None,
        current_timestep: int = 0,
        running_tasks: dict[UUID, asyncio.Task[Any]] | dict | None = None,
        completed_task_ids: set[UUID] | None = None,
        failed_task_ids: set[UUID] | None = None,
        communication_service: CommunicationService | None = None,
        previous_reward: float = 0.0,
        done: bool = False,
    ) -> SendMessageAction | RequestEndWorkflowAction:
        if not self._sent_initial:
            self._sent_initial = True
            return SendMessageAction(
                reasoning="Say hello",
                content="hello_stakeholder",
                receiver_id=self._receiver_id,
                success=True,
                result_summary="sent hello to stakeholder",
            )
        return RequestEndWorkflowAction(
            reasoning="finish",
            success=True,
            result_summary="finished workflow",
            reason="finished workflow",
        )

    def reset(self) -> None:
        self._sent_initial = False


class ManagerAssignFirstReady(ManagerAgent):
    """Manager that assigns the first READY task to the first available agent."""

    def __init__(self) -> None:
        super().__init__(
            agent_id="stub_manager", preferences=PreferenceSnapshot(preferences=[])
        )

    async def step(
        self,
        workflow: Workflow,
        execution_state: ExecutionState,
        stakeholder_profile: StakeholderPublicProfile | None = None,
        current_timestep: int = 0,
        running_tasks: dict[UUID, asyncio.Task[Any]] | dict | None = None,
        completed_task_ids: set[UUID] | None = None,
        failed_task_ids: set[UUID] | None = None,
        communication_service: CommunicationService | None = None,
        previous_reward: float = 0.0,
        done: bool = False,
    ) -> AssignTaskAction | NoOpAction:
        obs = await self.create_observation(
            workflow=workflow,
            execution_state=execution_state,
            current_timestep=current_timestep,
            running_tasks=running_tasks,
            completed_task_ids=completed_task_ids,
            failed_task_ids=failed_task_ids,
            communication_service=communication_service,
        )
        if obs.ready_task_ids and obs.available_agent_metadata:
            return AssignTaskAction(
                reasoning="assign first ready",
                task_id=str(obs.ready_task_ids[0]),
                agent_id=obs.available_agent_metadata[0].agent_id,
                success=True,
                result_summary="assigned first ready task",
            )
        return NoOpAction(reasoning="idle", success=True, result_summary="idle")

    def reset(self) -> None:
        pass


class ManagerNoOp(ManagerAgent):
    """Manager that always returns NoOpAction."""

    def __init__(self) -> None:
        super().__init__(
            agent_id="stub_manager", preferences=PreferenceSnapshot(preferences=[])
        )

    async def step(
        self,
        workflow: Workflow,
        execution_state: ExecutionState,
        stakeholder_profile: StakeholderPublicProfile | None = None,
        current_timestep: int = 0,
        running_tasks: dict[UUID, asyncio.Task[Any]] | dict | None = None,
        completed_task_ids: set[UUID] | None = None,
        failed_task_ids: set[UUID] | None = None,
        communication_service: CommunicationService | None = None,
        previous_reward: float = 0.0,
        done: bool = False,
    ) -> NoOpAction:
        return NoOpAction(reasoning="noop", success=True, result_summary="noop")

    def reset(self) -> None:
        pass


class StubAgent(AgentInterface[AgentConfig]):
    """Reusable worker stub for tests.

    Parameters:
        agent_id: stable ID for assertions
        agent_type: "ai" or "human_mock" to exercise code paths
        cost: actual_cost to report on completion
        seconds: simulated duration in seconds; converted to hours in result
        delay_s: real async sleep to simulate long-running execution
        resources_to_emit: list[Resource] to emit as outputs
    """

    def __init__(
        self,
        agent_id: str = "worker-1",
        agent_type: str = "ai",
        *,
        cost: float = 0.0,
        seconds: float = 0.0,
        delay_s: float = 0.0,
        resources_to_emit: list[Resource] | None = None,
    ) -> None:
        super().__init__(
            AgentConfig(
                agent_id=agent_id,
                agent_type=agent_type,
                system_prompt=f"stub {agent_type} agent",
                model_name="none",
                agent_description=f"stub {agent_type} agent",
                agent_capabilities=[f"stub {agent_type} agent"],
            )
        )
        self._cost = float(cost)
        self._seconds = float(seconds)
        self._delay_s = float(delay_s)
        self._resources = list(resources_to_emit or [])

    async def execute_task(self, task: Task, resources: list[Resource]):
        if self._delay_s > 0:
            await asyncio.sleep(self._delay_s)
        return create_task_result(
            task_id=task.id,
            agent_id=self.agent_id,
            success=True,
            execution_time=0.01,
            resources=self._resources,
            cost=self._cost,
            simulated_duration_hours=self._seconds / 3600.0 if self._seconds else 0.0,
        )


class FailingStubAgent(AgentInterface[AgentConfig]):
    """Worker stub that raises to exercise engine failure handling."""

    def __init__(self, agent_id: str = "failing-1", agent_type: str = "ai") -> None:
        super().__init__(
            AgentConfig(
                agent_id=agent_id,
                agent_type=agent_type,
                system_prompt=f"stub {agent_type} agent",
                model_name="none",
                agent_description=f"stub {agent_type} agent",
                agent_capabilities=[f"stub {agent_type} agent"],
            )
        )

    async def execute_task(self, task: Task, resources: list[Resource]):
        raise RuntimeError("stubbed execution failure")
