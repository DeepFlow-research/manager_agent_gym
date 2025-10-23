"""
NoOp Manager Agent implementation.

This manager agent always takes no action, allowing workflows to execute
with agent variants without any manager intervention.
"""

from typing import TYPE_CHECKING
from uuid import UUID
import asyncio

from manager_agent_gym.core.agents.manager_agent.common.interface import ManagerAgent
from manager_agent_gym.core.agents.manager_agent.actions import NoOpAction
from manager_agent_gym.core.execution.schemas.state import ExecutionState

if TYPE_CHECKING:
    from manager_agent_gym.schemas.domain.workflow import Workflow
    from manager_agent_gym.schemas.manager.observation import ManagerObservation
    from manager_agent_gym.core.agents.manager_agent.actions.base import (
        BaseManagerAction,
    )
    from manager_agent_gym.schemas.preferences.preference import PreferenceSnapshot
    from manager_agent_gym.schemas.agents.stakeholder import StakeholderPublicProfile
    from manager_agent_gym.core.communication.service import CommunicationService


class NoOpManagerAgent(ManagerAgent):
    """
    Manager agent that always takes no action.

    This is useful for workflows where you want agent variants to execute
    independently without manager intervention, such as:
    - Best-of-N scaling experiments
    - Model ensemble comparisons
    - Pure agent execution benchmarks

    Example:
        ```python
        manager = NoOpManagerAgent(preferences=PreferenceSnapshot(...))

        engine = WorkflowExecutionEngine(
            workflow=workflow,
            manager_agent=manager,
            ...
        )
        ```
    """

    def __init__(self, agent_id: str, preferences: "PreferenceSnapshot"):
        """Initialize NoOp manager with preferences."""
        super().__init__(agent_id="noop_manager", preferences=preferences)

    def reset(self) -> None:
        """Reset the manager agent state for a new workflow execution."""
        super().reset()

    async def step(
        self,
        workflow: "Workflow",
        execution_state: ExecutionState,
        stakeholder_profile: "StakeholderPublicProfile | None" = None,
        current_timestep: int = 0,
        running_tasks: dict[UUID, asyncio.Task] | None = None,
        completed_task_ids: set[UUID] | None = None,
        failed_task_ids: set[UUID] | None = None,
        communication_service: "CommunicationService | None" = None,
        previous_reward: float = 0.0,
        done: bool = False,
    ) -> NoOpAction:
        """Always return NoOpAction (RL-friendly step interface)."""
        return NoOpAction(reasoning="NoOp manager - no actions taken by design")

    async def take_action(
        self, observation: "ManagerObservation"
    ) -> "BaseManagerAction":
        """Always return NoOpAction (legacy interface)."""
        return NoOpAction(reasoning="NoOp manager - no actions taken by design")

    async def create_observation(
        self,
        workflow: "Workflow",
        execution_state: ExecutionState,
        current_timestep: int = 0,
        running_tasks: dict | None = None,
        completed_task_ids: set | None = None,
        failed_task_ids: set | None = None,
        communication_service: "CommunicationService | None" = None,
        stakeholder_profile: "StakeholderPublicProfile | None" = None,
    ) -> "ManagerObservation":
        """Create minimal observation (not used since we always NoOp)."""
        # Return minimal observation to avoid unnecessary computation
        from manager_agent_gym.schemas.manager.observation import ManagerObservation

        return ManagerObservation(
            timestep=current_timestep,
            workflow_id=workflow.id,
            execution_state=execution_state.value,
            workflow_summary="NoOp manager - no observation needed",
            task_status_counts={},
            workflow_progress=0.0,
        )
