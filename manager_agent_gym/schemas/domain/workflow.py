"""
Workflow data models for Manager Agent Gym.

The Workflow class is a Pydantic model that delegates business logic to
service modules in core/workflow/services/.
"""

from datetime import datetime
from typing import Any, TYPE_CHECKING
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from pydantic import ConfigDict

from manager_agent_gym.schemas.domain.task import Task
from manager_agent_gym.schemas.domain.resource import Resource

from manager_agent_gym.schemas.domain.communication import Message
from manager_agent_gym.schemas.preferences import Constraint

if TYPE_CHECKING:
    from manager_agent_gym.core.agents.workflow_agents.common import AgentInterface


class Workflow(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    """
    A complete workflow containing tasks, agents, and execution state.

    This represents the core environment for the Manager Agent POSG.
    """

    # Essential fields (previously from BaseEntity)
    id: UUID = Field(
        default_factory=uuid4,
        description="Unique identifier for this workflow instance.",
        examples=[str(uuid4())],
    )
    name: str = Field(
        ...,
        description="Human-readable name for dashboards and logs.",
        examples=["IPO Readiness"],
    )
    workflow_goal: str = Field(
        ...,
        description="Detailed objective and acceptance criteria for the workflow run.",
        examples=[
            "Objective: Secure AOC and Operating Licence. Acceptance: AOC issued, OL granted, inspections passed.",
        ],
    )
    owner_id: UUID = Field(
        ...,
        description="ID of the workflow owner (tenant/user)",
        examples=[str(uuid4())],
    )

    # Core POSG state components
    tasks: dict[UUID, Task] = Field(
        default_factory=dict,
        description="Task graph nodes (G). Keys are task UUIDs; values are Task models.",
        examples=[
            {str(uuid4()): Task(name="Draft plan", description="...").model_dump()}
        ],
    )
    resources: dict[UUID, Resource] = Field(
        default_factory=dict,
        description="Resource registry (R). Keys are resource UUIDs; values are Resource models.",
    )
    agents: dict[str, Any] = Field(
        default_factory=dict,
        description="Available agents (W). Keys are agent ids; values are live AgentInterface instances.",
    )
    messages: list[Message] = Field(
        default_factory=list,
        description="Communication history (C). Appended by the communication service.",
    )

    # Core orchestration agent IDs (set by engine, looked up from agents dict)
    stakeholder_agent_id: str | None = Field(
        default=None,
        description="ID of the stakeholder agent providing preferences/feedback for this workflow",
    )
    manager_agent_id: str | None = Field(
        default=None,
        description="ID of the manager agent orchestrating this workflow",
    )

    # Workflow metadata
    constraints: list[Constraint] = Field(
        default_factory=list,
        description="Hard/soft constraints used by evaluators and planning",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary metadata for workflow execution (e.g., clarification transcripts)",
    )

    # Execution tracking
    started_at: datetime | None = Field(
        default=None, description="When execution started (set by engine)"
    )
    # Optional run seed for reproducibility; engine sets this when provided
    seed: int = Field(default=42, description="Run-level seed for reproducibility")
    completed_at: datetime | None = Field(
        default=None, description="When execution completed (set by engine)"
    )
    is_active: bool = Field(
        default=False, description="Whether the workflow is currently active"
    )

    # Metrics for evaluation
    total_cost: float = Field(
        default=0.0, description="Cumulative actual cost reported by agents"
    )
    # Sum of all task-level simulated durations (hours), reported by agents
    total_simulated_hours: float = Field(
        default=0.0,
        description="Total simulated time across all completed tasks (hours)",
    )

    @property
    def workflow_id(self) -> UUID:
        """Alias for id field to maintain compatibility."""
        return self.id

    @property
    def total_budget(self) -> float:
        """Sum of estimated costs across all tasks and nested subtasks.

        Use WorkflowMetrics.total_budget(workflow) for direct access.
        """
        from manager_agent_gym.core.workflow.services import WorkflowMetrics

        return WorkflowMetrics.total_budget(self)

    @property
    def total_expected_hours(self) -> float:
        """Sum of estimated duration hours across all tasks and nested subtasks.

        Use WorkflowMetrics.total_expected_hours(workflow) for direct access.
        """
        from manager_agent_gym.core.workflow.services import WorkflowMetrics

        return WorkflowMetrics.total_expected_hours(self)

    @property
    def stakeholder_agent(self) -> "AgentInterface | None":  # type: ignore
        """Get the stakeholder agent instance from the agents registry."""
        if self.stakeholder_agent_id:
            return self.agents.get(self.stakeholder_agent_id)
        return None

    @property
    def manager_agent(self) -> "AgentInterface | None":  # type: ignore
        """Get the manager agent instance (if stored as an agent in the workflow)."""
        if self.manager_agent_id:
            return self.agents.get(self.manager_agent_id)
        return None
