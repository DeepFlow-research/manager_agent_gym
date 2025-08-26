from pydantic import BaseModel, Field

from .rubric import WorkflowRubric
from enum import Enum
from typing import Callable


class AggregationStrategy(str, Enum):
    WEIGHTED_AVERAGE = "weighted_average"
    MIN = "min"
    MAX = "max"
    PRODUCT = "product"
    HARMONIC_MEAN = "harmonic_mean"


class Evaluator(BaseModel):
    """Container for a set of rubrics and an aggregation policy.

    This replaces the previous pattern where `Preference` directly embedded rubrics
    and an aggregation strategy. Use this wherever you want to evaluate a quantity
    (standalone) or wrap it inside a `Preference` for weighted aggregation.
    """

    name: str = Field(..., description="Evaluator name")
    description: str | None = Field(
        default=None, description="Optional human-readable description"
    )
    aggregation: AggregationStrategy | Callable[..., float] = Field(
        default=AggregationStrategy.WEIGHTED_AVERAGE,
        description="Strategy to aggregate rubric scores. Is a simple strategy, or a callable if you want to use a custom aggregation function (eg: mean if something is True else zero).",
    )
    rubrics: list[WorkflowRubric] = Field(
        default_factory=list, description="List of rubrics this evaluator will run"
    )
