"""
Manager action schemas for constrained LLM generation.

Defines all possible manager actions as Pydantic models with strict
validation. These are used for structured output generation and validation.
"""

from abc import ABC, abstractmethod
from uuid import UUID
from pydantic import BaseModel, Field
from typing import Literal, TYPE_CHECKING, Any
from ...core.decomposition import decompose_task, get_workflow_context_string
from ...schemas.core.communication import Message, MessageType
from ...schemas.core.tasks import TaskStatus
from ...core.common.logging import logger

if TYPE_CHECKING:
    from ...schemas.core.workflow import Workflow
    from ...core.communication.service import CommunicationService


class ActionResult(BaseModel):
    """Structured result returned by manager actions."""

    action_type: Literal[
        "assign_task",
        "assign_all_pending_tasks",
        "create_task",
        "remove_task",
        "send_message",
        "noop",
        "get_workflow_status",
        "get_available_agents",
        "get_pending_tasks",
        "refine_task",
        "add_task_dependency",
        "remove_task_dependency",
        "failed_action",
        "inspect_task",
        "request_end_workflow",
        "decompose_task",
    ] = Field(description="Type of action result")
    summary: str = Field(description="Short summary of what happened / info returned")
    kind: Literal[
        "mutation", "info", "noop", "message", "inspection", "failed_action", "unknown"
    ] = Field(description="Type of action result")
    data: dict[str, Any] = Field(
        description="Optional structured payload for follow-up use (empty if not applicable)",
    )
    timestep: int | None = Field(
        default=None, description="Timestep of the action, set by the engine"
    )
    success: bool = Field(
        default=True, description="Whether the action succeeded (set by execute)"
    )


class BaseManagerAction(BaseModel, ABC):
    """
    Base class for all manager actions.

    All action classes must inherit from this and implement the execute method.
    This ensures type safety and consistent execution interface.
    """

    reasoning: str = Field(
        description="Reasoning for this action decision (should be around 2-3 sentences long.)"
    )
    success: bool | None = Field(
        description="Whether the action succeeded (set by execute)"
    )
    result_summary: str | None = Field(
        description="Short human-readable summary of the result (set by execute)",
    )

    @abstractmethod
    async def execute(
        self,
        workflow: "Workflow",
        communication_service: "CommunicationService | None" = None,
    ) -> ActionResult:
        """
        Execute this action against the workflow.

        Args:
            workflow: The workflow to modify
            communication_service: Optional communication service for agent messaging

        Returns:
            ActionResult summarizing the mutation or information retrieved

        Raises:
            ValueError: If action parameters are invalid for current workflow state
        """
        raise NotImplementedError


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


class CreateTaskAction(BaseManagerAction):
    """Create a new actionable task to advance the workflow.

    Use when:
    - Agents are idle and no READY tasks exist (pipeline gap)
    - You need explicit artifacts to satisfy constraints or evaluators
    - You want to introduce approvals/reviews as tasks to route to humans

    Examples:
    - Create "Stakeholder approval: v1 solution proposal" (assign to human approver)
    - Create "Compliance review: data lineage evidence" to satisfy a hard constraint
    - Create "Prepare stakeholder presentation" (later assign to the relevant human)
    - Create "Risk register update" to document tradeoffs and decisions
    """

    action_type: Literal["create_task"] = "create_task"
    name: str = Field(description="Clear, descriptive task name")
    description: str = Field(
        description="Detailed task description including objectives and deliverables"
    )
    estimated_duration_hours: float = Field(
        description="Estimated time to complete the task"
    )
    estimated_cost: float = Field(description="Estimated cost to complete the task")

    async def execute(
        self,
        workflow: "Workflow",
        communication_service: "CommunicationService | None" = None,
    ) -> ActionResult:
        """Execute task creation."""
        from ...schemas.core.tasks import Task, TaskStatus

        new_task = Task(
            name=self.name,
            description=self.description,
            status=TaskStatus.PENDING,
            estimated_duration_hours=self.estimated_duration_hours,
            estimated_cost=self.estimated_cost,
            dependency_task_ids=[],
        )

        workflow.tasks[new_task.task_id] = new_task
        logger.info(f"New task created: {self.name} (ID: {new_task.task_id})")
        summary = f"Created task '{self.name}' ({new_task.task_id})"
        data = {"task_id": str(new_task.task_id)}
        self.success = True
        self.result_summary = summary
        return ActionResult(
            summary=summary,
            kind="mutation",
            data=data,
            action_type=self.action_type,
            success=self.success,
        )


class RemoveTaskAction(BaseManagerAction):
    """Remove a task that is out of scope, duplicated, or obsolete; use to reduce clutter and eliminate work that no longer contributes to objectives."""

    action_type: Literal["remove_task"] = "remove_task"
    task_id: UUID = Field(description="ID of the task to remove")

    async def execute(
        self,
        workflow: "Workflow",
        communication_service: "CommunicationService | None" = None,
    ) -> ActionResult:
        """Execute task removal."""
        if self.task_id not in workflow.tasks:
            return ActionResult(
                summary=f"Failed: Task {self.task_id} not found in workflow from set of all tasks: {workflow.tasks.keys()}",
                kind="failed_action",
                data={},
                action_type=self.action_type,
                success=False,
            )

        del workflow.tasks[self.task_id]
        logger.info(f"Task {self.task_id} removed from workflow")
        summary = f"Removed task {self.task_id}"
        data = {"task_id": str(self.task_id)}
        self.success = True
        self.result_summary = summary
        return ActionResult(
            summary=summary,
            kind="mutation",
            data=data,
            action_type=self.action_type,
            success=self.success,
        )


class SendMessageAction(BaseManagerAction):
    """Send a direct or broadcast coordination message.

    Use to:
    - Elicit preference tradeoffs (quality vs speed vs cost) without revealing hidden rubrics
    - Request review/approval or stakeholder acceptance
    - Clarify requirements or confirm scope changes
    - Inform task agents about the manner in which they should proceed, give feedback, seek information on how they intend to work on tasks, ect.

    Examples:
    - To stakeholder: "Could you prioritize speed vs quality for the next milestone (choose one)?"
    - To stakeholder: "Please confirm: Is v1 acceptable to ship as-is, or should we add a validation step?"
    - Broadcast: "All agents: pause work on feature X pending stakeholder decision."

    Note: Messaging has communication/oversight costs in evaluators; ask crisp, high-value questions.
    """

    action_type: Literal["send_message"] = "send_message"
    content: str = Field(description="Message content")
    receiver_id: str | None = Field(
        description="Specific receiver ID, or None for broadcast"
    )

    async def execute(
        self,
        workflow: "Workflow",
        communication_service: "CommunicationService | None" = None,
    ) -> ActionResult:
        """Execute message sending using the injected communication service."""
        if communication_service:
            if self.receiver_id:
                # Direct message to specific agent
                await communication_service.send_direct_message(
                    from_agent="manager_agent",
                    to_agent=self.receiver_id,
                    content=self.content,
                    message_type=MessageType.ALERT,
                )
            else:
                # Broadcast to all agents
                await communication_service.broadcast_message(
                    from_agent="manager_agent",
                    content=self.content,
                    message_type=MessageType.ALERT,
                )
        else:
            # Fallback: add directly to workflow messages (backward compatibility)
            message = Message(
                sender_id="manager_agent",
                receiver_id=self.receiver_id,
                content=self.content,
                message_type=MessageType.ALERT,
            )
            workflow.messages.append(message)

        logger.info(f"Manager message sent: {self.content[:50]}...")
        summary = f"Sent message{' to ' + self.receiver_id if self.receiver_id else ' (broadcast)'}"
        data = {"receiver_id": self.receiver_id, "length": len(self.content)}
        self.success = True
        self.result_summary = summary
        return ActionResult(
            summary=summary,
            kind="message",
            data=data,
            action_type=self.action_type,
            success=self.success,
        )


class NoOpAction(BaseManagerAction):
    """
    Deliberately take no action; use only when observation is required and no safe or productive action is available.
    """

    action_type: Literal["noop"] = "noop"

    async def execute(
        self,
        workflow: "Workflow",
        communication_service: "CommunicationService | None" = None,
    ) -> ActionResult:
        """Execute no-op (no state modification)."""
        logger.info("Manager chose to observe without taking action")
        summary = "No operation"
        self.success = True
        self.result_summary = summary
        # No workflow modifications for no-op
        return ActionResult(
            summary=summary,
            kind="noop",
            data={},
            action_type=self.action_type,
            success=self.success,
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
        ready = [str(t.id) for t in workflow.get_ready_tasks()]
        available_agents = [a.agent_id for a in workflow.get_available_agents()]
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
        agents = workflow.get_available_agents()
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


class RefineTaskAction(BaseManagerAction):
    """Update a task’s instructions, scope, or estimates.

    Use to:
    - Remove ambiguity and add acceptance criteria
    - Adjust scope, estimates, or add manager instructions
    - Incorporate stakeholder feedback or clarifications

    Examples:
    - Add acceptance criteria: "Include A/B test metrics and success threshold >= 2% uplift"
    - Tighten scope: rename to "Draft 2-page summary (exec audience)"
    - Add manager instructions for assignee
    """

    action_type: Literal["refine_task"] = "refine_task"
    task_id: UUID = Field(description="ID of the task to refine")
    new_name: str | None = Field(description="Updated task name (optional)")
    new_description: str | None = Field(
        description="Updated task description with refined instructions"
    )
    new_estimated_duration: float | None = Field(
        description="Updated duration estimate in hours"
    )
    new_estimated_cost: float | None = Field(description="Updated cost estimate")
    additional_instructions: str | None = Field(
        description="Additional specific instructions for the assigned agent",
    )

    async def execute(
        self,
        workflow: "Workflow",
        communication_service: "CommunicationService | None" = None,
    ) -> ActionResult:
        """Execute task refinement."""
        if self.task_id not in workflow.tasks:
            return ActionResult(
                summary=f"Failed: Task {self.task_id} not found in workflow from set of all tasks: {workflow.tasks.keys()}",
                kind="failed_action",
                data={},
                action_type=self.action_type,
                success=False,
            )

        task = workflow.tasks[self.task_id]
        updates = []

        if self.new_name:
            task.name = self.new_name
            updates.append(f"name -> '{self.new_name}'")

        if self.new_description:
            task.description = self.new_description
            updates.append(
                f"description updated from {task.description} to {self.new_description}"
            )

        if self.new_estimated_duration:
            task.estimated_duration_hours = self.new_estimated_duration
            updates.append(
                f"duration updated from {task.estimated_duration_hours}h to {self.new_estimated_duration}h"
            )

        if self.new_estimated_cost:
            task.estimated_cost = self.new_estimated_cost
            updates.append(
                f"cost updated from ${task.estimated_cost} to ${self.new_estimated_cost}"
            )

        if self.additional_instructions:
            # Add to execution notes as structured instructions (execution_notes is list[str])
            instruction_marker = "MANAGER_INSTRUCTIONS:"
            instruction_note = f"{instruction_marker} {self.additional_instructions}"

            # Check if we already have manager instructions and replace them
            existing_instruction_index = None
            for i, note in enumerate(task.execution_notes):
                if instruction_marker in note:
                    existing_instruction_index = i
                    break

            if existing_instruction_index is not None:
                # Replace existing instructions
                old_instruction = task.execution_notes[existing_instruction_index]
                task.execution_notes[existing_instruction_index] = instruction_note
                updates.append(
                    f"instructions updated from '{old_instruction}' to '{instruction_note}'"
                )
            else:
                # Add new instructions
                task.execution_notes.append(instruction_note)
                updates.append(f"instructions added: '{instruction_note}'")

        logger.info(f"Task {task.name} refined: {', '.join(updates)}")
        summary = f"Refined task {self.task_id}: {', '.join(updates)}"
        data = {"task_id": self.task_id, "updates": updates}
        self.success = True
        self.result_summary = summary
        return ActionResult(
            summary=summary,
            kind="mutation",
            data=data,
            action_type=self.action_type,
            success=self.success,
        )


class AddTaskDependencyAction(BaseManagerAction):
    """Create a prerequisite relationship (A must finish before B starts); use to enforce correct sequencing and protect the critical path."""

    action_type: Literal["add_task_dependency"] = "add_task_dependency"
    prerequisite_task_id: UUID = Field(
        description="ID of the task that must complete first"
    )
    dependent_task_id: UUID = Field(
        description="ID of the task that depends on the prerequisite"
    )

    async def execute(
        self,
        workflow: "Workflow",
        communication_service: "CommunicationService | None" = None,
    ) -> ActionResult:
        """Execute dependency addition."""

        if self.prerequisite_task_id not in workflow.tasks:
            return ActionResult(
                summary=f"Failed: Prerequisite task {self.prerequisite_task_id} not found in workflow from set of all tasks: {workflow.tasks.keys()}",
                kind="failed_action",
                data={},
                action_type=self.action_type,
                success=False,
            )
        if self.dependent_task_id not in workflow.tasks:
            return ActionResult(
                summary=f"Failed: Dependent task {self.dependent_task_id} not found in workflow from set of all tasks: {workflow.tasks.keys()}",
                kind="failed_action",
                data={},
                action_type=self.action_type,
                success=False,
            )
        if self.prerequisite_task_id == self.dependent_task_id:
            return ActionResult(
                summary="Cannot create dependency on same task",
                kind="info",
                data={},
                action_type=self.action_type,
                success=False,
            )

        dependent_task = workflow.tasks[self.dependent_task_id]

        # Check for circular dependencies
        def has_circular_dependency(
            start_id: UUID, target_id: UUID, visited: set | None = None
        ) -> bool:
            if visited is None:
                visited = set()
            if start_id in visited:
                return start_id == target_id
            visited.add(start_id)

            if start_id not in workflow.tasks:
                return False

            for dep_id in workflow.tasks[start_id].dependency_task_ids:
                if has_circular_dependency(dep_id, target_id, visited.copy()):
                    return True
            return False

        # Use the UUIDs from the action fields directly
        prereq_uuid: UUID = self.prerequisite_task_id
        dependent_uuid: UUID = self.dependent_task_id

        if has_circular_dependency(prereq_uuid, dependent_uuid):
            return ActionResult(
                summary="Failed: Adding dependency would create circular dependency",
                kind="failed_action",
                data={},
                action_type=self.action_type,
                success=False,
            )

        # Add dependency if not already present
        if prereq_uuid not in dependent_task.dependency_task_ids:
            dependent_task.dependency_task_ids.append(prereq_uuid)
            logger.info(
                f"Added dependency: {workflow.tasks[prereq_uuid].name} -> {dependent_task.name}"
            )
            summary = f"Added dependency between {workflow.tasks[prereq_uuid].name} and {dependent_task.name}"
            data = {
                "prerequisite_task_id": self.prerequisite_task_id,
                "dependent_task_id": self.dependent_task_id,
            }
            self.success = True
            self.result_summary = summary
            return ActionResult(
                summary=summary,
                kind="mutation",
                data=data,
                action_type=self.action_type,
            )
        else:
            logger.info(
                f" Dependency already exists: {workflow.tasks[prereq_uuid].name} -> {dependent_task.name}"
            )
            summary = "Dependency already existed (no change)"
            data = {
                "prerequisite_task_id": self.prerequisite_task_id,
                "dependent_task_id": self.dependent_task_id,
            }
            self.success = True
            self.result_summary = summary
            return ActionResult(
                summary=summary,
                kind="info",
                data=data,
                action_type=self.action_type,
                success=self.success,
            )


class RemoveTaskDependencyAction(BaseManagerAction):
    """
    Remove an obsolete or incorrect prerequisite link; use when sequencing is no longer required or was added in error.

    Will return a summary of the dependency removed
    """

    action_type: Literal["remove_task_dependency"] = "remove_task_dependency"
    prerequisite_task_id: UUID = Field(description="ID of the prerequisite task")
    dependent_task_id: UUID = Field(description="ID of the dependent task")

    async def execute(
        self,
        workflow: "Workflow",
        communication_service: "CommunicationService | None" = None,
    ) -> ActionResult:
        """Execute dependency removal."""

        if self.dependent_task_id not in workflow.tasks:
            return ActionResult(
                summary=f"Failed: Dependent task {self.dependent_task_id} not found in workflow from set of all tasks: {workflow.tasks.keys()}",
                kind="failed_action",
                data={},
                action_type=self.action_type,
                success=False,
            )

        dependent_task = workflow.tasks[self.dependent_task_id]

        if self.prerequisite_task_id in dependent_task.dependency_task_ids:
            dependent_task.dependency_task_ids.remove(self.prerequisite_task_id)
            prereq_name = workflow.tasks[self.prerequisite_task_id].name
            logger.info(f"Removed dependency: {prereq_name} -> {dependent_task.name}")
            summary = f"Removed dependency {self.prerequisite_task_id} -> {self.dependent_task_id} between {prereq_name} and {dependent_task.name}"
            data = {
                "prerequisite_task_id": self.prerequisite_task_id,
                "dependent_task_id": self.dependent_task_id,
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
        else:
            logger.info(
                f"Dependency does not exist: {self.prerequisite_task_id} -> {dependent_task.name}"
            )
            summary = "Dependency did not exist (no change)"
            data = {
                "prerequisite_task_id": self.prerequisite_task_id,
                "dependent_task_id": self.dependent_task_id,
            }
            self.success = True
            self.result_summary = summary
            return ActionResult(
                summary=summary,
                kind="info",
                data=data,
                action_type=self.action_type,
                success=self.success,
            )


class InspectTaskAction(BaseManagerAction):
    """
    Review a specific task’s current status and outputs; use to investigate blockers, quality, or progress without changing state.

    Will return a summary of the task's status and the outputs, no state changes are made to the workflow.
    """

    action_type: Literal["inspect_task"] = "inspect_task"
    task_id: UUID = Field(description="ID of the task to inspect in detail")

    async def execute(
        self,
        workflow: "Workflow",
        communication_service: "CommunicationService | None" = None,
    ) -> ActionResult:
        """Execute task inspection (read-only)."""

        if self.task_id not in workflow.tasks:
            return ActionResult(
                summary=f"Failed: Task {self.task_id} not found in workflow from set of all tasks: {workflow.tasks.keys()}",
                kind="failed_action",
                data={},
                action_type=self.action_type,
                success=False,
            )

        task = workflow.tasks[self.task_id]
        logger.info(
            f"Manager inspected task '{task.name}' (Status: {task.status.value})"
        )
        summary = f"Inspected task {self.task_id} details: {task.pretty_print()}"
        data = {
            "task_id": self.task_id,
            "status": task.status.value,
            "task_details": task.pretty_print(),
        }
        self.success = True
        self.result_summary = summary
        return ActionResult(
            summary=summary,
            kind="inspection",
            data=data,
            action_type=self.action_type,
            success=self.success,
        )


class DecomposeTaskAction(BaseManagerAction):
    """Break a complex task into smaller subtasks via AI.

    Will return a summary of the decomposition and the subtasks created for the task

    Use when:
    - A task is too broad or ambiguous
    - Parallelization would increase throughput
    - Sequencing benefits from explicit dependencies

    Examples:
    - Split "Regulatory filing" into "Collect artifacts" -> "Draft sections" -> "Human approval"
    - Split "Model training" into data prep, training, evaluation, and packaging
    """

    action_type: Literal["decompose_task"] = "decompose_task"
    task_id: UUID = Field(..., description="UUID of the task id to decompose")

    async def execute(
        self,
        workflow: "Workflow",
        communication_service: "CommunicationService | None" = None,
    ) -> ActionResult:
        """Execute task decomposition."""
        logger.info(f"Manager is decomposing task {self.task_id}")
        try:
            # Find the task in the workflow
            target_task = workflow.find_task_by_id(self.task_id)

            if not target_task:
                logger.error(f"Task {self.task_id} not found in workflow")
                return ActionResult(
                    summary=f"Failed: Task {self.task_id} not found in workflow from set of all tasks: {workflow.tasks.keys()}",
                    kind="failed_action",
                    data={},
                    action_type=self.action_type,
                    success=False,
                )

            if target_task.subtasks:
                logger.warning(
                    f"Task {target_task.name} already has subtasks, skipping decomposition"
                )
                return ActionResult(
                    summary="Task already decomposed; skipping",
                    kind="info",
                    data={
                        "task_id": self.task_id,
                        "subtask_count": len(target_task.subtasks),
                    },
                    action_type=self.action_type,
                    success=False,
                )

            # Generate workflow context
            context = get_workflow_context_string(list(workflow.tasks.values()))

            # Decompose the task (thread workflow seed for reproducibility)
            await decompose_task(
                target_task, workflow_context=context, seed=workflow.seed
            )

            logger.info(
                f"Successfully decomposed task '{target_task.name}' into {len(target_task.subtasks)} subtasks"
            )
            summary = f"Decomposed task {self.task_id} -> {len(target_task.subtasks)} subtasks"
            data = {"task_id": self.task_id, "subtask_count": len(target_task.subtasks)}
            self.success = True
            self.result_summary = summary
            return ActionResult(
                summary=summary,
                kind="mutation",
                data=data,
                action_type=self.action_type,
                success=self.success,
            )

        except Exception as e:
            logger.error(f"Failed to decompose task {self.task_id}: {e}")
            raise


class RequestEndWorkflowAction(BaseManagerAction):
    """Request that the workflow end as soon as possible.

    Use when:
    - All required atomic tasks are completed and further work offers negligible utility
    - The stakeholder explicitly accepts the deliverables
    - Time/budget constraints imply continued work would reduce overall utility

    This action signals the engine via the communication service; the engine will terminate on the next check cycle.
    """

    action_type: Literal["request_end_workflow"] = "request_end_workflow"
    reason: str | None = Field(
        description="Optional short reason for requesting the workflow to end",
    )

    async def execute(
        self,
        workflow: "Workflow",
        communication_service: "CommunicationService | None" = None,
    ) -> ActionResult:
        """Signal end-of-workflow request through the communication service."""
        if communication_service is None:
            # Fallback: no-op with info result
            summary = "End-of-workflow request could not be sent (no communication service available)"
            self.success = False
            self.result_summary = summary
            return ActionResult(
                summary=summary, kind="info", data={}, action_type=self.action_type
            )

        try:
            reason_text = self.reason or "manager requested termination"
            communication_service.request_end_workflow(reason=reason_text)
            summary = "Requested workflow termination"
            data = {"reason": reason_text}
            self.success = True
            self.result_summary = summary
            return ActionResult(
                summary=summary, kind="info", data=data, action_type=self.action_type
            )
        except Exception as e:
            logger.error(f"Failed to request end of workflow: {e}")
            raise


class FailedAction(BaseManagerAction):
    """
    Not able to be directly called by the manager agent, but can be used to indicate that the manager agent is unable to take an action (usually due to a systems error like a llm provider refusal).
    Returns a summary of the error and the metadata, no changes are made to the workflow.
    """

    action_type: Literal["failed_action"] = "failed_action"
    metadata: dict[str, Any] = Field(description="Metadata about the failed action")

    async def execute(
        self,
        workflow: "Workflow",
        communication_service: "CommunicationService | None" = None,
    ) -> ActionResult:
        """Execute the failed action."""
        return ActionResult(
            summary=self.reasoning,
            kind="info",
            data=self.metadata,
            action_type=self.action_type,
        )
