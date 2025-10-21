from pydantic import BaseModel, Field

from manager_agent_gym.schemas.preferences.rubric import RubricCriteria
from enum import Enum
from typing import Callable, Literal


class AggregationStrategy(str, Enum):
    WEIGHTED_AVERAGE = "weighted_average"
    MIN = "min"
    MAX = "max"
    PRODUCT = "product"
    HARMONIC_MEAN = "harmonic_mean"


class PreferenceMeasure(BaseModel):
    """
    We have different ways of expressing preferences.

    Currently, we have the following ways of expressing preferences:
    - Rubric: A set of criteria and their weights.
    - Exemplar: An output of a task that is desirable under the preference.
    """

    type: Literal["rubric", "exemplar"] = Field(
        default="rubric", description="Type of preference metric"
    )


class Rubric(PreferenceMeasure):
    """Container for a set of criteria and an aggregation policy.

    This replaces the previous pattern where `Preference` directly embedded criteria
    and an aggregation strategy. Use this wherever you want to evaluate a quantity
    (standalone) or wrap it inside a `Preference` for weighted aggregation.
    """

    name: str = Field(..., description="Rubric name")
    description: str | None = Field(
        default=None, description="Optional human-readable description"
    )
    aggregation: AggregationStrategy | Callable[..., float] = Field(
        default=AggregationStrategy.WEIGHTED_AVERAGE,
        description="Strategy to aggregate criteria scores. Is a simple strategy, or a callable if you want to use a custom aggregation function (eg: mean if something is True else zero).",
    )
    criteria: list[RubricCriteria] = Field(
        default_factory=list, description="List of criteria this rubric will run"
    )


class PreferenceExemplar(PreferenceMeasure):
    """
    Instead of an explicit 'criteria', we allow for the preference to be expressed via an exemplar output for a task.
    """

    exemplar_output: str = Field(..., description="The output of the exemplar")

    def get_preference_summary(self) -> str:
        """Get human-readable summary for this exemplar-based preference.

        Returns:
            Summary string describing the exemplar approach
        """
        output_preview = (
            self.exemplar_output[:100] + "..."
            if len(self.exemplar_output) > 100
            else self.exemplar_output
        )
        return f"Exemplar-based evaluation (output: {output_preview})"
