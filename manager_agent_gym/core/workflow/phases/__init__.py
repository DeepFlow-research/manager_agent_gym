"""
Execution phases for workflow orchestration.

Phases allow for pluggable pre-execution logic (e.g., rubric generation,
planning) before the main workflow execution loop.
"""

from manager_agent_gym.core.workflow.phases.interface import PreExecutionPhase
from manager_agent_gym.core.workflow.phases.no_op import NoOpPreExecutionPhase

__all__ = ["PreExecutionPhase", "NoOpPreExecutionPhase"]
