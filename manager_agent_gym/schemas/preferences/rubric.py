from typing import Any, Callable, Set
from enum import Enum
from pydantic import BaseModel, Field, model_validator


class RunCondition(str, Enum):
    EACH_TIMESTEP = "each_timestep"
    ON_COMPLETION = "on_completion"
    BOTH = "both"


class AdditionalContextItem(str, Enum):
    """Declarative context signals a rubric can request for evaluation."""

    MANAGER_ACTIONS = "manager_actions"
    COMMS_BY_SENDER = "communications_by_sender"
    COMMS_BY_THREAD = "communications_by_thread"
    PREFERENCE_HISTORY = "preference_history"
    STAKEHOLDER_PROFILE = "stakeholder_profile"
    RESOURCES_BY_TASK = "resources_by_task"
    AGENT_TOOL_USAGE_BY_TASK = "agent_tool_usage_by_task"
    AGENT_PUBLIC_STATES = "agent_public_states"


class WorkflowRubric(BaseModel):
    """
    Workflow-level rubric that evaluates a workflow using either a Python function
    or an LLM prompt. Exactly one evaluation source must be provided.
    """

    name: str = Field(..., description="Name of the rubric")
    description: str | None = Field(
        default=None, description="Description of what this rubric measures"
    )
    max_score: float = Field(1.0, gt=0.0, description="Maximum possible score")
    evaluator_function: Callable[..., Any] | None = Field(
        default=None,
        description=(
            "Python function taking a workflow and returning either a numeric score,"
            " a (score, reasoning) tuple, an EvaluatedScore-like object with 'score' and"
            " 'reasoning', or any custom type (captured as raw_output)."
        ),
    )
    llm_prompt: str | None = Field(
        default=None,
        description="LLM prompt to use for evaluation (0..max_score output)",
    )
    llm_model: str = Field(
        default="o3", description="LLM model name to use if llm_prompt is provided"
    )

    run_condition: RunCondition = Field(
        default=RunCondition.EACH_TIMESTEP,
        description="When this rubric should be evaluated",
    )
    required_context: Set[AdditionalContextItem] = Field(
        default_factory=set,
        description="Optional set of context items this rubric needs at evaluation time",
    )

    @model_validator(mode="after")
    def check_evaluator_source(self) -> "WorkflowRubric":
        if self.evaluator_function is None and self.llm_prompt is None:
            raise ValueError("Must provide either evaluator_function or llm_prompt")
        if self.evaluator_function is not None and self.llm_prompt is not None:
            raise ValueError(
                "Provide either evaluator_function OR llm_prompt, not both"
            )
        return self
