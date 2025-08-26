"""
Base agent interface for Manager Agent Gym.

Defines the core abstractions for agents that execute tasks
and produce resources in the workflow system.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import TypeVar, Generic, TYPE_CHECKING
from uuid import UUID

from ...schemas.workflow_agents import AgentConfig, StakeholderConfig
from ...schemas.preferences.preference import PreferenceWeights, PreferenceChange
from ...schemas.preferences.weight_update import (
    PreferenceWeightUpdateRequest,
)
from ...schemas.core import Task, Resource
from ...schemas.unified_results import ExecutionResult
from ...schemas.workflow_agents.stakeholder import (
    StakeholderPublicProfile,
)
from ..communication.service import COMMUNICATION_SERVICE_SINGLETON
from ...schemas.workflow_agents.telemetry import AgentToolUseEvent

if TYPE_CHECKING:
    pass

ConfigType = TypeVar("ConfigType", bound=AgentConfig)


class AgentInterface(ABC, Generic[ConfigType]):
    """
    Abstract base class for all agents in the system.

    Agents execute tasks and form the core workforce in workflows.
    They combine execution capabilities with business logic like
    availability and capacity management.
    """

    def __init__(
        self,
        config: ConfigType,
    ):
        self.config = config
        self.communication_service = COMMUNICATION_SERVICE_SINGLETON
        self._seed: int | None = None

        self.name: str = config.agent_id
        self.description: str
        self.is_available: bool = True
        self.max_concurrent_tasks: int = 1  # Humans limited, AI can override
        self.current_task_ids: list[UUID] = []

        # Performance tracking
        self.tasks_completed: int = 0
        self.joined_at: datetime = datetime.now()
        # Tool usage buffer keyed by task id
        self.tool_usage_by_task: dict[UUID, list[AgentToolUseEvent]] = {}

    def configure_seed(self, seed: int) -> None:
        """Configure deterministic seed for this agent (overridable)."""
        self._seed = seed

    @property
    def agent_id(self) -> str:
        """Get the agent's unique identifier."""
        return self.config.agent_id

    @property
    def agent_type(self) -> str:
        """Get the agent's type."""
        return self.config.agent_type

    def can_handle_task(self, task: Task) -> bool:
        """Check if agent can handle a given task based on availability."""
        if not self.is_available:
            return False
        if len(self.current_task_ids) >= self.max_concurrent_tasks:
            return False
        return True

    def record_tool_use_event(self, event: AgentToolUseEvent) -> None:
        """Record a tool usage event under the current task bucket."""
        task_id = event.task_id
        if task_id is None:
            return
        self.tool_usage_by_task.setdefault(task_id, []).append(event)

    def get_tool_usage_by_task(self) -> dict[UUID, list[AgentToolUseEvent]]:
        """Return a copy of per-task tool usage events for this agent."""
        return {k: list(v) for k, v in self.tool_usage_by_task.items()}

    @abstractmethod
    async def execute_task(
        self, task: Task, resources: list[Resource]
    ) -> ExecutionResult:
        """
        Execute a task given the task and available resources.

        Args:
            task: The task to execute
            resources: Available input resources (optional)

        Returns:
            ExecutionResult with outputs and metadata

        Raises:
            Exception: If execution fails in an unrecoverable way
        """
        pass


class StakeholderBase(AgentInterface[StakeholderConfig], ABC):
    """Abstract base for stakeholder agents.

    Defines the required policy step and preference ownership API so the engine
    can interact without concrete type knowledge.
    """

    def __init__(self, config: StakeholderConfig):
        super().__init__(config)
        self.public_profile: StakeholderPublicProfile = StakeholderPublicProfile(
            display_name=self.config.name,
            role=self.config.role,
            preference_summary=self.config.initial_preferences.get_preference_summary(),
        )

    @abstractmethod
    async def policy_step(
        self,
        current_timestep: int,
    ) -> None: ...

    @abstractmethod
    def get_preferences_for_timestep(self, timestep: int) -> PreferenceWeights: ...

    @abstractmethod
    def apply_preference_change(
        self,
        timestep: int,
        new_weights: PreferenceWeights,
        change_event: PreferenceChange | None,
    ) -> None: ...

    @abstractmethod
    def apply_weight_update(
        self,
        request: PreferenceWeightUpdateRequest,
    ) -> PreferenceChange: ...

    @abstractmethod
    def apply_weight_updates(
        self,
        requests: list[PreferenceWeightUpdateRequest],
    ) -> list[PreferenceChange]: ...
