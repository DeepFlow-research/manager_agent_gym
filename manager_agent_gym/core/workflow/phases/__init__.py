"""
Execution phases for workflow orchestration.

Phases allow for pluggable pre-execution logic (e.g., rubric generation,
planning) before the main workflow execution loop.
"""

from manager_agent_gym.core.workflow.phases.interface import PreExecutionPhase
from manager_agent_gym.core.workflow.phases.no_op import NoOpPreExecutionPhase
from manager_agent_gym.core.workflow.phases.rubric_execution_base import (
    RubricExecutionPhaseBase,
)
from manager_agent_gym.core.workflow.phases.multi_rubric_training import (
    MultiRubricTrainingPhase,
)
from manager_agent_gym.core.workflow.phases.baseline_phases import (
    BestOfNBaseline,
    GroundTruthRubricBaseline,
    TrainedPolicyRubricBaseline,
    create_baseline_phase,
    BaselineType,
)

__all__ = [
    "PreExecutionPhase",
    "NoOpPreExecutionPhase",
    "RubricExecutionPhaseBase",
    "MultiRubricTrainingPhase",
    "BestOfNBaseline",
    "GroundTruthRubricBaseline",
    "TrainedPolicyRubricBaseline",
    "create_baseline_phase",
    "BaselineType",
]
