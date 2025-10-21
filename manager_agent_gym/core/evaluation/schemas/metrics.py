"""
Workflow Quality Metrics Schema.

Types for workflow-level quality assessment metrics from the paper.
"""

from pydantic import BaseModel, Field


class CoordinationDeadtimeMetrics(BaseModel):
    """
    Coordination deadtime metrics for workflow execution.

    Based on the paper's formula: T_dead = Σ max(0, t_start - t_deps_ready)
    Measures workflow inefficiencies from suboptimal task scheduling.
    """

    total_coordination_deadtime_seconds: float = Field(
        ..., ge=0.0, description="Total coordination deadtime across entire workflow"
    )
    average_coordination_deadtime_per_task: float = Field(
        ..., ge=0.0, description="Average coordination deadtime per task"
    )
    tasks_started_count: int = Field(
        ..., ge=0, description="Number of tasks that were started"
    )
    tasks_with_deadtime_count: int = Field(
        ..., ge=0, description="Number of tasks that experienced deadtime > 0"
    )
    deadtime_efficiency: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Efficiency score: 1.0 - (tasks_with_deadtime / tasks_started)",
    )

    def get_deadtime_efficiency_grade(self) -> str:
        """Get a human-readable efficiency grade."""
        if self.deadtime_efficiency >= 0.95:
            return "Excellent"
        elif self.deadtime_efficiency >= 0.8:
            return "Good"
        elif self.deadtime_efficiency >= 0.6:
            return "Fair"
        else:
            return "Poor"


class ResourceCostMetrics(BaseModel):
    """
    Enhanced resource cost metrics for workflow execution.

    Implements comprehensive economic cost modeling from the paper's c_total specification.
    """

    total_workflow_cost: float = Field(
        ..., ge=0.0, description="Total economic cost of workflow execution"
    )

    # Cost breakdown by type
    human_labor_cost: float = Field(
        default=0.0, ge=0.0, description="Total cost for human worker hours"
    )
    ai_agent_cost: float = Field(
        default=0.0,
        ge=0.0,
        description="Total cost for AI agent usage (API calls, etc.)",
    )
    tool_usage_cost: float = Field(
        default=0.0, ge=0.0, description="Total cost for tool and API invocations"
    )
    resource_cost: float = Field(
        default=0.0, ge=0.0, description="Total cost for computational resources"
    )

    # Cost efficiency metrics
    cost_per_task: float = Field(
        default=0.0, ge=0.0, description="Average cost per completed task"
    )
    cost_efficiency_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Cost efficiency relative to estimated budget",
    )

    # Metadata
    completed_tasks_count: int = Field(
        ..., ge=0, description="Number of tasks completed"
    )
    estimated_total_cost: float | None = Field(
        default=None, description="Originally estimated total cost"
    )
