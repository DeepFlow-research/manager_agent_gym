from typing import Any, Callable, Set
from enum import Enum
from pydantic import BaseModel, Field, model_validator, model_serializer


class RunCondition(str, Enum):
    EACH_TIMESTEP = "each_timestep"
    ON_COMPLETION = "on_completion"
    BOTH = "both"


class AdditionalContextItem(str, Enum):
    """Declarative context signals a criterion can request for evaluation."""

    MANAGER_ACTIONS = "manager_actions"
    COMMS_BY_SENDER = "communications_by_sender"
    COMMS_BY_THREAD = "communications_by_thread"
    PREFERENCE_HISTORY = "preference_history"
    STAKEHOLDER_PROFILE = "stakeholder_profile"
    RESOURCES_BY_TASK = "resources_by_task"
    AGENT_TOOL_USAGE_BY_TASK = "agent_tool_usage_by_task"
    AGENT_PUBLIC_STATES = "agent_public_states"


class RubricCriteria(BaseModel):
    """
    Workflow-level criterion that evaluates a workflow using either a Python function
    or an LLM prompt. Exactly one evaluation source must be provided.
    """

    name: str = Field(..., description="Name of the criterion")
    description: str | None = Field(
        default=None, description="Description of what this criterion measures"
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
    stringified_evaluator_function: str | None = Field(
        default=None,
        description="Stringified evaluator function",  # TODO: this is tech debt till we find a better way to parse the function from the string
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
        description="When this criterion should be evaluated",
    )
    required_context: Set[AdditionalContextItem] = Field(
        default_factory=set,
        description="Optional set of context items this criterion needs at evaluation time",
    )

    @model_validator(mode="after")
    def check_evaluator_source(self) -> "RubricCriteria":
        if (
            self.evaluator_function is None
            and self.llm_prompt is None
            and self.stringified_evaluator_function is None
        ):
            raise ValueError(
                "Must provide either evaluator_function or llm_prompt or stringified_evaluator_function"
            )
        if (
            self.evaluator_function is not None
            and self.llm_prompt is not None
            and self.stringified_evaluator_function is not None
        ):
            raise ValueError(
                "Provide only one of evaluator_function, llm_prompt, or stringified_evaluator_function"
            )
        return self

    @model_serializer
    def serialize_model(self) -> dict[str, Any]:
        """Custom serializer to handle function objects."""
        data = {
            "name": self.name,
            "description": self.description,
            "max_score": self.max_score,
            "llm_prompt": self.llm_prompt,
            "llm_model": self.llm_model,
            "run_condition": self.run_condition.value,
            "required_context": [item.value for item in self.required_context],
        }

        # Handle evaluator_function serialization
        if callable(self.evaluator_function):
            # Serialize callable as a marker string
            data["evaluator_function"] = "<compiled_function>"
        else:
            data["evaluator_function"] = self.evaluator_function

        return data
