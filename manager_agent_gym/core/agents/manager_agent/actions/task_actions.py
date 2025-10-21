"""
Manager action schemas for constrained LLM generation.

Defines all possible manager actions as Pydantic models with strict
validation. These are used for structured output generation and validation.
"""

from uuid import UUID
from pydantic import Field
from typing import Literal, TYPE_CHECKING
from manager_agent_gym.core.agents.manager_agent.actions.task_decomposition import (
    decompose_task,
    get_workflow_context_string,
)
from manager_agent_gym.core.common.logging import logger
from manager_agent_gym.core.workflow.services import WorkflowQueries

if TYPE_CHECKING:
    from manager_agent_gym.schemas.domain.workflow import Workflow
    from manager_agent_gym.core.communication.service import CommunicationService


from manager_agent_gym.core.agents.manager_agent.actions.base import (
    BaseManagerAction,
    ActionResult,
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
        from manager_agent_gym.schemas.domain.task import Task, TaskStatus

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
            target_task = WorkflowQueries.find_task_by_id(workflow, self.task_id)

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
