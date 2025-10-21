"""
Manager action schemas for constrained LLM generation.

Defines all possible manager actions as Pydantic models with strict
validation. These are used for structured output generation and validation.
"""

from typing import Literal, TYPE_CHECKING
from manager_agent_gym.schemas.domain.task import TaskStatus
from manager_agent_gym.core.common.logging import logger
from manager_agent_gym.core.workflow.services import WorkflowQueries

if TYPE_CHECKING:
    from manager_agent_gym.schemas.domain.workflow import Workflow
    from manager_agent_gym.core.communication.service import CommunicationService


from manager_agent_gym.core.agents.manager_agent.actions.base import (
    BaseManagerAction,
    ActionResult,
)


class GetWorkflowStatusAction(BaseManagerAction):
    """
    Inspect overall workflow health and key metrics; use to inform planning when choosing between assignment, task creation, or optimization.
    """

    action_type: Literal["get_workflow_status"] = "get_workflow_status"

    async def execute(
        self,
        workflow: "Workflow",
        communication_service: "CommunicationService | None" = None,
    ) -> ActionResult:
        """Execute workflow status check (no state modification)."""
        logger.info("📊 Manager analyzed workflow status")
        # Return meaningful summary to avoid loops
        from collections import Counter

        status_counts = Counter(t.status.value for t in workflow.tasks.values())
        ready = [str(t.id) for t in WorkflowQueries.get_ready_tasks(workflow)]
        available_agents = [
            a.agent_id for a in WorkflowQueries.get_available_agents(workflow)
        ]
        summary = f"Status: tasks={dict(status_counts)}, ready={len(ready)}, agents_available={len(available_agents)}"
        data = {
            "task_status": dict(status_counts),
            "ready_task_ids": ready,
            # Backward-compatible key expected by tests
            "available_agents": available_agents,
        }
        self.success = True
        self.result_summary = "Analyzed workflow status"
        return ActionResult(
            summary=summary,
            kind="info",
            data=data,
            action_type=self.action_type,
            success=self.success,
        )


class GetAvailableAgentsAction(BaseManagerAction):
    """List currently available agents and capacity; use when selecting an assignee or verifying idle capacity for immediate deployment."""

    action_type: Literal["get_available_agents"] = "get_available_agents"

    async def execute(
        self,
        workflow: "Workflow",
        communication_service: "CommunicationService | None" = None,
    ) -> ActionResult:
        """Execute agent info check (no state modification)."""
        logger.info("👥 Manager analyzed available agents")
        agents = WorkflowQueries.get_available_agents(workflow)
        summary = f"Available agents: {[a.config.get_agent_capability_summary() for a in agents]}"
        self.success = True
        self.result_summary = "Analyzed available agents"
        return ActionResult(
            summary=summary,
            kind="info",
            data={"available_agent_ids": [a.config.agent_id for a in agents]},
            action_type=self.action_type,
            success=self.success,
        )


class GetPendingTasksAction(BaseManagerAction):
    """List tasks in PENDING state awaiting assignment; use to triage the backlog when none are currently selected for assignment."""

    action_type: Literal["get_pending_tasks"] = "get_pending_tasks"

    async def execute(
        self,
        workflow: "Workflow",
        communication_service: "CommunicationService | None" = None,
    ) -> ActionResult:
        """Execute pending tasks check (no state modification)."""
        logger.info("📋 Manager analyzed pending tasks")
        pending = [t for t in workflow.tasks.values() if t.status == TaskStatus.PENDING]
        names = [t.name for t in pending][:5]
        summary = f"Pending tasks: {len(pending)} (showing {len(names)}): {names}"
        data = {
            "pending_task_ids": [str(t.id) for t in pending],
            "preview_names": names,
        }
        self.success = True
        self.result_summary = "Analyzed pending tasks"
        return ActionResult(
            summary=summary,
            kind="info",
            data=data,
            action_type=self.action_type,
            success=self.success,
        )
