from collections import deque
from typing import TYPE_CHECKING
from abc import ABC, abstractmethod

from manager_agent_gym.schemas.manager import ManagerObservation
from manager_agent_gym.core.agents.manager_agent.actions import (
    BaseManagerAction,
    ActionResult,
)
from manager_agent_gym.schemas.preferences.preference import PreferenceSnapshot
from manager_agent_gym.schemas.domain.base import TaskStatus
from manager_agent_gym.schemas.agents.stakeholder import (
    StakeholderPublicProfile,
)
from manager_agent_gym.core.workflow.services import WorkflowQueries, WorkflowDisplay

if TYPE_CHECKING:
    from manager_agent_gym.schemas.domain.workflow import Workflow
    from manager_agent_gym.core.execution.schemas.state import ExecutionState
    from manager_agent_gym.core.communication.service import CommunicationService


class ManagerAgent(ABC):
    """Abstract interface for manager agents.

    Implementations observe the workflow, choose an action each timestep,
    and maintain a compact action history for downstream evaluation.

    Args:
        agent_id (str): Unique identifier for the manager agent.
        preferences (PreferenceWeights): Initial normalized preference weights.

    Attributes:
        agent_id (str): Identifier for logging and communications.
        preferences (PreferenceWeights): Current preference weights.
        _action_buffer (deque[ActionResult]): Recent actions (maxlen 50).

    Example:
        ```python
        class MyManager(ManagerAgent):
            async def step(self, workflow, execution_state, stakeholder_profile,
                           current_timestep, running_tasks, completed_task_ids,
                           failed_task_ids, communication_service=None,
                           previous_reward=0.0, done=False) -> BaseManagerAction:
                # decide an action...
                return NoOpAction(reasoning="Observing")
        ```
    """

    def __init__(self, agent_id: str, preferences: PreferenceSnapshot | None = None):
        self.agent_id = agent_id
        self.preferences = (
            preferences  # Optional - may be None for discovery-based agents
        )
        self._action_buffer: deque[ActionResult] = deque(maxlen=50)
        # Execution horizon awareness (optional; set by engine)
        self._max_timesteps: int | None = None
        # Seed configured by engine (if any)
        self._seed: int = 42
        # Communication service (set by engine/runner)
        self.communication_service: "CommunicationService | None" = None

    def configure_seed(self, seed: int) -> None:
        """Configure deterministic seed for this manager (overridable)."""
        self._seed = seed

    def set_communication_service(self, service: "CommunicationService") -> None:
        """Set communication service for this manager."""
        self.communication_service = service

    def record_action(self, brief: ActionResult) -> None:
        self._action_buffer.append(brief)

    def get_action_buffer(
        self, number_most_recent_actions: int | None = None
    ) -> list[ActionResult]:
        if number_most_recent_actions is None or number_most_recent_actions <= 0:
            return list(self._action_buffer)

        return list(self._action_buffer)[-number_most_recent_actions:]

    def set_max_timesteps(self, max_timesteps: int | None) -> None:
        """Set the maximum timesteps for the current execution (set by engine)."""
        self._max_timesteps = (
            max_timesteps if (max_timesteps is None or max_timesteps >= 0) else None
        )

    async def create_observation(
        self,
        workflow: "Workflow",
        execution_state: "ExecutionState",
        current_timestep: int = 0,
        running_tasks: dict | None = None,
        completed_task_ids: set | None = None,
        failed_task_ids: set | None = None,
        communication_service: "CommunicationService | None" = None,
        stakeholder_profile: StakeholderPublicProfile | None = None,
    ) -> ManagerObservation:
        """
        Create manager observation from workflow state.

        Subclasses can override this to customize what they observe.

        Args:
            workflow: Current workflow state
            execution_state: Current execution state
            current_timestep: Current timestep number
            running_tasks: Currently executing tasks
            completed_task_ids: Set of completed task IDs
            failed_task_ids: Set of failed task IDs
            communication_service: Optional communication service for messages
            stakeholder_profile: Optional public stakeholder profile

        Returns:
            ManagerObservation with workflow state data
        """
        # Get task status summary
        task_statuses = {}
        for status in TaskStatus:
            task_statuses[status.value] = sum(
                1 for task in workflow.tasks.values() if task.status == status
            )

        # Get ready tasks
        ready_tasks = WorkflowQueries.get_ready_tasks(workflow)

        # Get available agents
        available_agents = WorkflowQueries.get_available_agents(workflow)

        # Get recent messages from communication service if available
        recent_messages = []
        if communication_service:
            all_comm_messages = communication_service.get_all_messages()
            recent_messages = all_comm_messages[:10]  # Last 10 messages
        else:
            # Fallback to workflow messages for backward compatibility
            recent_messages = workflow.messages[-5:]  # Last 5 messages

        # Compute timeline awareness fields if configured
        max_ts = self._max_timesteps
        ts_remaining = None
        time_progress = None
        if isinstance(max_ts, int) and max_ts > 0:
            ts_remaining = max(0, max_ts - current_timestep - 1)
            # Clamp progress in [0,1]
            time_progress = min(1.0, max(0.0, float(current_timestep) / float(max_ts)))

        # Handle optional parameters with defaults
        running_tasks = running_tasks or {}
        completed_task_ids = completed_task_ids or set()
        failed_task_ids = failed_task_ids or set()

        return ManagerObservation(
            workflow_summary=WorkflowDisplay.pretty_print(workflow),
            timestep=current_timestep,
            workflow_id=workflow.id,
            execution_state=execution_state,
            task_status_counts=task_statuses,
            ready_task_ids=[task.id for task in ready_tasks],
            running_task_ids=list(running_tasks.keys()),
            completed_task_ids=list(completed_task_ids),
            failed_task_ids=list(failed_task_ids),
            available_agent_metadata=[agent.config for agent in available_agents],
            recent_messages=recent_messages,
            workflow_progress=len(completed_task_ids) / len(workflow.tasks)
            if workflow.tasks
            else 0.0,
            max_timesteps=max_ts,
            timesteps_remaining=ts_remaining,
            time_progress=time_progress,
            constraints=workflow.constraints,
            task_ids=list(workflow.tasks.keys()),
            resource_ids=list(workflow.resources.keys()),
            agent_ids=list(workflow.agents.keys()),
            stakeholder_profile=stakeholder_profile,
        )

    # Note: take_action(observation) has been removed from the abstract interface in favor of step(...).

    @abstractmethod
    async def step(
        self,
        workflow: "Workflow",
        execution_state: "ExecutionState",
        stakeholder_profile: StakeholderPublicProfile | None = None,
        current_timestep: int = 0,
        running_tasks: dict | None = None,
        completed_task_ids: set | None = None,
        failed_task_ids: set | None = None,
        communication_service: "CommunicationService | None" = None,
        previous_reward: float = 0.0,
        done: bool = False,
    ) -> BaseManagerAction:
        """
        One-call RL-friendly step: build observation and return an action.

        Args:
            stakeholder_profile: Optional stakeholder profile. Discovery-based agents
                                (e.g., rubric generation) may not need this.
            running_tasks: Optional dict of running tasks (defaults to empty dict)
            completed_task_ids: Optional set of completed task IDs (defaults to empty set)
            failed_task_ids: Optional set of failed task IDs (defaults to empty set)
        """
        raise NotImplementedError

    def on_action_executed(
        self,
        timestep: int,
        action: BaseManagerAction,
        action_result: ActionResult | None,
    ) -> None:
        """
        Hook invoked by the engine after a manager action has been executed.

        Default implementation records a compact action brief, including a short
        outcome summary when available. Manager implementations can override
        this to customize how actions are logged or persisted.
        """
        reasoning = action.reasoning
        if action_result and action_result.summary:
            reasoning += f" | Outcome of action: {action_result.summary}"

        self.record_action(
            ActionResult(
                kind=action_result.kind if action_result else "unknown",
                timestep=timestep,
                action_type=action.action_type,  # type: ignore[attr-defined]
                summary=action_result.summary
                if action_result
                else "Could not find summary of result, action may have been attempted, but failed to run.",
                data={},
                success=action_result.success if action_result else False,
            )
        )

    @abstractmethod
    def reset(self) -> None:
        """
        Reset the manager agent state for a new workflow execution.
        """
        self._action_buffer.clear()
