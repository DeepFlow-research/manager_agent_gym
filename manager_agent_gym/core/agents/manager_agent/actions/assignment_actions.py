"""
Manager action schemas for constrained LLM generation.

Defines all possible manager actions as Pydantic models with strict
validation. These are used for structured output generation and validation.
"""

from uuid import UUID
from pydantic import BaseModel, Field
from typing import Literal, TYPE_CHECKING
from manager_agent_gym.schemas.domain.task import TaskStatus
from manager_agent_gym.core.common.logging import logger

if TYPE_CHECKING:
    from manager_agent_gym.schemas.domain.workflow import Workflow
    from manager_agent_gym.core.communication.service import CommunicationService


from manager_agent_gym.core.agents.manager_agent.actions.base import (
    BaseManagerAction,
    ActionResult,
)


class AssignTaskAction(BaseManagerAction):
    """Assign a ready task to an available, appropriate agent.

    Use when:
    - A validated task is READY and a matching agent has capacity
    - You have confirmed the task does not require human approval/sign-off

    Examples:
    - Assign "Draft technical memo" to `ai_analyst_1` (READY and cheap to parallelize)
    - Assign "Generate regulatory filing draft" to `ai_writer` after requirements clarified

    Never assign to AI when the task involves approval, sign-off, certification, stakeholder-facing presentation, or strategic decision-making; these must go to a human agent.
    """

    action_type: Literal["assign_task"] = "assign_task"
    task_id: str = Field(description="ID of the task to assign")
    agent_id: str = Field(description="ID of the agent to assign the task to")

    async def execute(
        self,
        workflow: "Workflow",
        communication_service: "CommunicationService | None" = None,
    ) -> ActionResult:
        """Execute task assignment."""
        task_uuid = (
            UUID(self.task_id) if isinstance(self.task_id, str) else self.task_id
        )
        # Validation
        if task_uuid not in workflow.tasks:
            return ActionResult(
                summary=f"Failed: Task {self.task_id} not found in workflow from set of all tasks: {workflow.tasks.keys()}",
                kind="failed_action",
                data={},
                action_type=self.action_type,
                success=False,
            )
        if self.agent_id not in workflow.agents:
            return ActionResult(
                summary=f"Failed: Agent {self.agent_id} not found in workflow from set of all agents: {workflow.agents.keys()}",
                kind="failed_action",
                data={},
                action_type=self.action_type,
                success=False,
            )

        # Execute assignment
        workflow.tasks[task_uuid].assigned_agent_id = self.agent_id
        logger.info(f"Task {self.task_id} assigned to agent {self.agent_id}")
        summary = f"Assigned task {self.task_id} to {self.agent_id}"
        data = {"task_id": str(task_uuid), "agent_id": self.agent_id}
        self.success = True
        self.result_summary = summary
        return ActionResult(
            summary=summary,
            kind="mutation",
            data=data,
            action_type=self.action_type,
            success=self.success,
        )


class AssignAllPendingTasksAction(BaseManagerAction):
    """
    Bulk-assign all unassigned, non-completed tasks to one agent; use only for simple demos or quick triage when skill matching is non-critical—avoid if tasks have dependencies or require specific expertise.
    """

    action_type: Literal["assign_all_pending_tasks"] = "assign_all_pending_tasks"
    agent_id: str | None = Field(description="Agent ID to assign tasks to (optional)")

    async def execute(
        self,
        workflow: "Workflow",
        communication_service: "CommunicationService | None" = None,
    ) -> ActionResult:
        """Assign all pending tasks that have no assigned agent to the chosen agent."""
        # Choose an agent if not provided
        target_agent_id = self.agent_id
        if not target_agent_id:
            if not workflow.agents:
                logger.info("No agents available to assign tasks")
                return ActionResult(
                    summary="No agents available to assign tasks",
                    kind="info",
                    data={},
                    action_type=self.action_type,
                    success=False,
                )
            # Pick any agent deterministically for reproducibility
            target_agent_id = next(iter(workflow.agents.keys()))

        assigned_count = 0
        for task in workflow.tasks.values():
            if task.assigned_agent_id:
                continue
            if task.status in (
                TaskStatus.COMPLETED,
                TaskStatus.FAILED,
            ):
                continue
            task.assigned_agent_id = target_agent_id
            assigned_count += 1

        logger.info(
            f"Assigned {assigned_count} pending task(s) to agent {target_agent_id}"
        )
        summary = f"Assigned {assigned_count} pending tasks to {target_agent_id}"
        data = {"assigned_count": assigned_count, "agent_id": target_agent_id}
        self.success = True
        self.result_summary = summary
        return ActionResult(
            summary=summary,
            kind="mutation",
            data=data,
            action_type=self.action_type,
            success=self.success,
        )


class AssignmentPair(BaseModel):
    task_id: UUID = Field(description="Task to assign")
    agent_id: str = Field(description="Agent ID to assign to")


class AssignTasksToAgentsAction(BaseManagerAction):
    """Bulk-assign specific tasks to specific agents in one action.

    Applies a task->agent mapping (e.g., produced by an LLM) in a single mutation.
    """

    action_type: Literal["assign_tasks_to_agents"] = "assign_tasks_to_agents"
    assignments: list[AssignmentPair] = Field(
        default_factory=list, description="List of task->agent assignments to apply"
    )

    async def execute(
        self,
        workflow: "Workflow",
        communication_service: "CommunicationService | None" = None,
    ) -> ActionResult:
        assigned = 0
        skipped: list[str] = []
        for pair in self.assignments:
            task = workflow.tasks.get(pair.task_id)
            if task is None:
                skipped.append(f"missing:{pair.task_id}")
                continue
            if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
                skipped.append(f"terminal:{pair.task_id}")
                continue
            if pair.agent_id not in workflow.agents:
                skipped.append(f"no_agent:{pair.agent_id}")
                continue
            task.assigned_agent_id = pair.agent_id
            assigned += 1

        summary = f"Applied {assigned} assignment(s)" + (
            f"; skipped {len(skipped)}" if skipped else ""
        )
        data = {
            "assigned_count": assigned,
            "skipped": skipped,
        }
        self.success = True
        self.result_summary = summary
        return ActionResult(
            summary=summary,
            kind="mutation",
            data=data,
            action_type=self.action_type,
            success=self.success,
        )
