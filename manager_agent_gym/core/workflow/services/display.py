"""
Workflow display utilities - formatting and pretty printing.
"""

from typing import TYPE_CHECKING

from manager_agent_gym.core.workflow.services.metrics import WorkflowMetrics

if TYPE_CHECKING:
    from manager_agent_gym.schemas.domain.workflow import Workflow


class WorkflowDisplay:
    """Stateless display service for workflow formatting."""

    @staticmethod
    def pretty_print(
        workflow: "Workflow",
        include_resources: bool = True,
        max_preview_chars: int = 300,
    ) -> str:
        """Return a human-readable summary of the workflow, tasks, and selected resources."""
        lines: list[str] = []
        lines.append("-" * 70)
        lines.append(f"Workflow: {workflow.name} (ID: {workflow.id})")
        lines.append(f"Goal: {workflow.workflow_goal}")

        # Use metrics service
        total_budget = WorkflowMetrics.total_budget(workflow)
        total_expected_hours = WorkflowMetrics.total_expected_hours(workflow)

        lines.append(
            f"Budget (est): ${total_budget:.2f} | Expected hours: {total_expected_hours:.2f}"
        )
        lines.append(f"Cost (actual): ${workflow.total_cost:.2f}")
        lines.append(
            f"Agents: {len(workflow.agents)} | Resources: {len(workflow.resources)} | Tasks: {len(workflow.tasks)}"
        )
        lines.append("-" * 70)
        lines.append("Tasks:")
        for t in workflow.tasks.values():
            lines.append(t.pretty_print(indent=1))
        if include_resources and workflow.resources:
            lines.append("\nResources:")
            for r in workflow.resources.values():
                try:
                    lines.append(r.pretty_print(max_preview_chars=max_preview_chars))
                except Exception:
                    lines.append(f"Resource: {r.name} (ID: {r.id})")
        return "\n".join(lines)
