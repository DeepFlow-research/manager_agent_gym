"""
Workflow execution engine for Manager Agent Gym.

Provides the core execution loop that manages discrete timesteps,
task execution, and workflow state transitions.
"""

from manager_agent_gym.core.common.callbacks import (
    default_timestep_callbacks,
    log_workflow_brief_summary,
    log_tasks_grouped_by_status,
    log_most_recent_manager_agent_action,
    log_running_metric_calculations,
)
from manager_agent_gym.core.workflow.phases.interface import PreExecutionPhase
from manager_agent_gym.core.workflow.phases.no_op import NoOpPreExecutionPhase
from manager_agent_gym.core.workflow.state.state_restorer import (
    WorkflowStateRestorer,
)
from manager_agent_gym.core.workflow.state.output_writer import (
    WorkflowSerialiser,
)

__all__ = [
    "default_timestep_callbacks",
    "log_workflow_brief_summary",
    "log_tasks_grouped_by_status",
    "log_most_recent_manager_agent_action",
    "log_running_metric_calculations",
    "PreExecutionPhase",
    "NoOpPreExecutionPhase",
    "WorkflowStateRestorer",
    "WorkflowSerialiser",
]
