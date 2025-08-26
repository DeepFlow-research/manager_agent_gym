from __future__ import annotations

import asyncio
from typing import Any
from uuid import UUID, uuid4

import pytest

from manager_agent_gym.core.communication.service import CommunicationService
from manager_agent_gym.core.execution.engine import WorkflowExecutionEngine
from manager_agent_gym.core.manager_agent.interface import ManagerAgent
from manager_agent_gym.core.workflow_agents.interface import StakeholderBase
from manager_agent_gym.core.workflow_agents.registry import AgentRegistry
from manager_agent_gym.schemas.config import OutputConfig
from manager_agent_gym.schemas.core.communication import (
    MessageGrouping,
    MessageType,
)
from manager_agent_gym.schemas.core.resources import Resource
from manager_agent_gym.schemas.core.tasks import Task
from manager_agent_gym.schemas.core.workflow import Workflow
from manager_agent_gym.schemas.workflow_agents.stakeholder import (
    StakeholderPublicProfile,
)
from manager_agent_gym.schemas.execution.manager_actions import (
    RequestEndWorkflowAction,
    SendMessageAction,
)
from manager_agent_gym.schemas.execution.state import ExecutionState
from manager_agent_gym.schemas.preferences.preference import (
    PreferenceChange,
    PreferenceWeights,
)
from manager_agent_gym.schemas.core.communication import ThreadMessagesView


def _mk_empty_workflow() -> Workflow:
    return Workflow(
        name="test_workflow",
        workflow_goal="validate communication",
        owner_id=uuid4(),
        tasks={},
        resources={},
        agents={},
        messages=[],
    )


class _StakeholderStub(StakeholderBase):
    """Stakeholder stub that replies directly and broadcasts once per timestep."""

    def __init__(self, agent_id: str = "stakeholder_1") -> None:
        from manager_agent_gym.schemas.workflow_agents.stakeholder import (
            StakeholderConfig,
        )

        config = StakeholderConfig(
            agent_id=agent_id,
            system_prompt="Stakeholder persona system prompt",
            name="Stakeholder",
            role="Owner",
            model_name="o3",
            initial_preferences=PreferenceWeights(preferences=[]),
            agent_description="Stakeholder",
            agent_capabilities=["Stakeholder"],
        )
        super().__init__(config)
        self._replied_timesteps: set[int] = set()

    async def execute_task(self, task: Task, resources: list[Resource]):
        from manager_agent_gym.schemas.unified_results import create_task_result

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
        # Direct reply to manager
        await self.communication_service.send_direct_message(
            from_agent=self.agent_id,
            to_agent="manager_agent",
            content=f"ack_t{current_timestep}",
            message_type=MessageType.RESPONSE,
        )
        # Broadcast once per timestep as well (should reach all known agents except sender)
        await self.communication_service.broadcast_message(
            from_agent=self.agent_id,
            content=f"broadcast_t{current_timestep}",
            message_type=MessageType.BROADCAST,
        )
        self._replied_timesteps.add(current_timestep)

    def get_preferences_for_timestep(self, timestep: int) -> PreferenceWeights:
        return PreferenceWeights(preferences=[])

    def apply_preference_change(
        self,
        timestep: int,
        new_weights: PreferenceWeights,
        change_event: PreferenceChange | None,
    ) -> None:
        return None

    def apply_weight_update(self, request: Any) -> PreferenceChange:
        return PreferenceChange(
            timestep=0,
            preferences=PreferenceWeights(preferences=[]),
            previous_weights={},
            new_weights={},
            change_type="none",
            magnitude=0.0,
            trigger_reason="test",
        )

    def apply_weight_updates(self, requests: list[Any]) -> list[PreferenceChange]:
        return [self.apply_weight_update(r) for r in requests]


class _ManagerSendsThenEnd(ManagerAgent):
    """Manager that sends a direct message to stakeholder on first step, then requests end."""

    def __init__(self, preferences: PreferenceWeights, receiver_id: str) -> None:
        super().__init__(agent_id="manager_agent", preferences=preferences)
        self._receiver_id = receiver_id
        self._sent_initial: bool = False

    async def step(
        self,
        workflow: Workflow,
        execution_state: ExecutionState,
        stakeholder_profile: StakeholderPublicProfile,
        current_timestep: int,
        running_tasks: dict[UUID, asyncio.Task[Any]] | dict,
        completed_task_ids: set[UUID],
        failed_task_ids: set[UUID],
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


@pytest.mark.asyncio
async def test_manager_to_stakeholder_direct_and_stakeholder_reply_and_broadcast_in_engine(
    tmp_path: Any,
) -> None:
    workflow = _mk_empty_workflow()
    registry = AgentRegistry()
    comms = CommunicationService()
    stakeholder = _StakeholderStub(agent_id="stakeholder_1")
    manager = _ManagerSendsThenEnd(
        preferences=PreferenceWeights(preferences=[]), receiver_id="stakeholder_1"
    )

    engine = WorkflowExecutionEngine(
        workflow=workflow,
        agent_registry=registry,
        stakeholder_agent=stakeholder,
        manager_agent=manager,
        communication_service=comms,
        output_config=OutputConfig(
            base_output_dir=tmp_path, run_id="comm_test", create_run_subdirectory=True
        ),
        max_timesteps=5,
        enable_timestep_logging=False,
        enable_final_metrics_logging=False,
        evaluations=[],
        seed=0,
        timestep_end_callbacks=[],
    )

    results = await engine.run_full_execution()

    # Engine should end via cancel (request_end_workflow) or complete
    assert engine.execution_state in {
        ExecutionState.CANCELLED,
        ExecutionState.COMPLETED,
    }
    assert len(results) >= 1

    # Direct message present
    history = comms.get_conversation_history("manager_agent", "stakeholder_1", limit=10)
    contents = [m.content for m in history]
    assert "hello_stakeholder" in contents
    # Stakeholder reply present
    assert any(c.startswith("ack_t") for c in contents)

    # Broadcast present and visible to manager (sender excluded by service)
    broadcasts = [m for m in comms.get_all_messages() if m.is_broadcast()]
    assert any("broadcast_t" in m.content for m in broadcasts)
    # Manager inbox should include at least one broadcast
    manager_inbox = comms.get_messages_for_agent(
        agent_id="manager_agent", include_broadcasts=True
    )
    assert any(m.is_broadcast() and "broadcast_t" in m.content for m in manager_inbox)


@pytest.mark.asyncio
async def test_thread_multicast_and_grouping() -> None:
    svc = CommunicationService()
    # Seed registry
    await svc.send_direct_message("a", "b", "hi")

    thread = svc.create_thread(participants=["a", "b", "c"], topic="coord")
    msg = await svc.add_message_to_thread(
        thread_id=thread.thread_id,
        from_agent="a",
        to_agent=None,
        content="sync",
        message_type=MessageType.DIRECT,
    )

    assert set(msg.recipients) == {"b", "c"}
    views_u = svc.get_all_messages_grouped(grouping=MessageGrouping.BY_THREAD)
    views_t: list[ThreadMessagesView] = (
        views_u  # narrow the union for type checker #type: ignore[assignment]
    )
    assert any(
        v.thread_id == thread.thread_id and v.total_messages >= 1 for v in views_t
    )


@pytest.mark.asyncio
async def test_mark_message_read_and_agent_view() -> None:
    svc = CommunicationService()
    m = await svc.send_direct_message("x", "y", "please read")
    ok = svc.mark_message_read(message_id=m.message_id, agent_id="y")
    assert ok is True
    stored = svc.graph.messages[m.message_id]
    assert "y" in stored.read_by
    agent_view = svc.get_agent_view("y")
    assert agent_view["agent_id"] == "y"
    assert any(item.get("from") == "x" for item in agent_view["recent_messages"])
