"""
Workflow metrics - computed values from workflow state.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from manager_agent_gym.schemas.domain.workflow import Workflow


class WorkflowMetrics:
    """Stateless metrics service for workflow calculations."""

    @staticmethod
    def total_budget(workflow: "Workflow") -> float:
        """Sum of estimated costs across all tasks and nested subtasks."""
        total = 0.0
        for task in workflow.tasks.values():
            # include top-level estimate
            if task.estimated_cost is not None:
                try:
                    total += float(task.estimated_cost)
                except Exception:
                    pass
            # include nested subtasks
            for subtask in task.get_all_subtasks_flat():
                if subtask.estimated_cost is not None:
                    total += float(subtask.estimated_cost)

        return total

    @staticmethod
    def total_expected_hours(workflow: "Workflow") -> float:
        """Sum of estimated duration hours across all tasks and nested subtasks."""
        total = 0.0
        for task in workflow.tasks.values():
            if task.estimated_duration_hours is not None:
                total += float(task.estimated_duration_hours)
            for subtask in task.get_all_subtasks_flat():
                if subtask.estimated_duration_hours is not None:
                    total += float(subtask.estimated_duration_hours)
        return total
