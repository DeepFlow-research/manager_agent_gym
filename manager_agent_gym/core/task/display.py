"""
Task display utilities - formatting and pretty printing.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from manager_agent_gym.schemas.domain.task import Task
    from manager_agent_gym.schemas.domain.workflow import Workflow


class TaskDisplay:
    """Stateless display service for task formatting."""

    @staticmethod
    def pretty_print(
        task: "Task", indent: int = 0, workflow: "Workflow | None" = None
    ) -> str:
        """Return a human-readable summary of the task and its subtasks.

        Args:
            task: Task to display
            indent: Indentation level
            workflow: Optional workflow to resolve execution details
        """
        from manager_agent_gym.schemas.domain.base import TaskStatus

        prefix = "  " * indent
        lines = [f"{prefix}[{task.status.value.upper()}] {task.name} (ID: {task.id})"]

        if task.description:
            lines.append(f"{prefix}  Description: {task.description}")

        # Get assigned agent from execution if available
        if task.execution_ids and workflow:
            execution = workflow.task_executions.get(task.execution_ids[0])
            if execution:
                lines.append(f"{prefix}  Assigned to: {execution.agent_id}")

        if task.estimated_duration_hours:
            lines.append(
                f"{prefix}  Estimated: {task.estimated_duration_hours}h, ${task.estimated_cost}"
            )

        if task.execution_notes:
            lines.append(f"{prefix}  Notes: {'; '.join(task.execution_notes[:2])}")

        if task.dependency_task_ids:
            lines.append(
                f"{prefix}  Dependencies: {[str(dep) for dep in task.dependency_task_ids]}"
            )

        # Show completion info for completed tasks
        if task.status == TaskStatus.COMPLETED:
            lines.append(
                f"{prefix}  Completed: {task.actual_duration_hours}h actual, ${task.actual_cost} cost"
            )
            if task.completed_at:
                lines.append(f"{prefix}  Finished at: {task.completed_at}")

        # Recursively print subtasks
        if task.subtasks:
            lines.append(f"{prefix}  Subtasks:")
            for subtask in task.subtasks:
                lines.append(TaskDisplay.pretty_print(subtask, indent + 2))

        return "\n".join(lines)
