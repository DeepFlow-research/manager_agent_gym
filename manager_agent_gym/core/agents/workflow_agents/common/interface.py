from abc import ABC, abstractmethod
from datetime import datetime
from typing import TypeVar, Generic
from uuid import UUID


from manager_agent_gym.schemas.agents import AgentConfig
from manager_agent_gym.schemas.domain import Task, Resource
from manager_agent_gym.core.execution.schemas.results import ExecutionResult
from manager_agent_gym.core.communication.service import COMMUNICATION_SERVICE_SINGLETON
from manager_agent_gym.core.agents.workflow_agents.schemas.telemetry import AgentToolUseEvent

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
        self.description: str

        self.communication_service = COMMUNICATION_SERVICE_SINGLETON
        self._seed: int | None = None

        self.name: str = config.agent_id
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
