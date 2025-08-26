from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable, Generic, Iterable, TypeVar

from ..preferences.evaluation import EvaluationResult


RewardValueT = TypeVar("RewardValueT", covariant=True)


class BaseRewardAggregator(Generic[RewardValueT], ABC):
    """Abstract interface for mapping evaluation results to a reward value.

    Implementations decide how to turn an `EvaluationResult` (per timestep) or a
    sequence of results (e.g., cumulative) into a reward value. The reward value
    can be a scalar, a vector, or any user-defined structure.
    """

    @abstractmethod
    def aggregate(self, evaluation: EvaluationResult) -> RewardValueT:
        """Aggregate a single timestep's evaluation into a reward value."""

    def accumulate(self, history: Iterable[EvaluationResult]) -> RewardValueT:
        """Aggregate a sequence of evaluations into a reward value.

        Default behavior: returns the aggregation of the last evaluation in the
        iterable. Override for cumulative or discounted behaviors.
        """
        last: EvaluationResult | None = None
        for item in history:
            last = item
        if last is None:
            raise ValueError("Cannot accumulate empty evaluation history")
        return self.aggregate(last)


# Projects an arbitrary reward value to a scalar for RL-style agents
RewardProjection = Callable[[RewardValueT], float]


class ScalarUtilityReward(BaseRewardAggregator[float]):
    """Returns the weighted total utility as the scalar reward."""

    def aggregate(self, evaluation: EvaluationResult) -> float:  # noqa: D401
        return float(evaluation.weighted_preference_total)


class PreferenceVectorReward(BaseRewardAggregator[list[float]]):
    """Returns a vector of per-preference normalized scores.

    Args:
        include_weights: if True, multiply each score by its weight
        order_by_name: if True, order by preference name (deterministic)
                      if False, keep arbitrary dict order (not recommended)
    """

    def __init__(
        self, include_weights: bool = False, order_by_name: bool = True
    ) -> None:
        self.include_weights = include_weights
        self.order_by_name = order_by_name

    def aggregate(self, evaluation: EvaluationResult) -> list[float]:  # noqa: D401
        items_list = list(evaluation.preference_scores.items())
        if self.order_by_name:
            items_list.sort(key=lambda kv: kv[0])
        values: list[float] = []
        for _, ps in items_list:
            val = float(ps.score)
            if self.include_weights:
                val *= float(ps.weight)
            values.append(val)
        return values


class PreferenceDictReward(BaseRewardAggregator[dict[str, float]]):
    """Returns a mapping of preference name -> normalized score (optionally weighted)."""

    def __init__(self, include_weights: bool = False) -> None:
        self.include_weights = include_weights

    def aggregate(self, evaluation: EvaluationResult) -> dict[str, float]:  # noqa: D401
        out: dict[str, float] = {}
        for name, ps in evaluation.preference_scores.items():
            val = float(ps.score)
            if self.include_weights:
                val *= float(ps.weight)
            out[name] = val
        return out


T = TypeVar("T")


class CallableRewardAggregator(BaseRewardAggregator[T], Generic[T]):
    """Wraps a user-provided callable mapping EvaluationResult -> T."""

    def __init__(self, fn: Callable[[EvaluationResult], T]) -> None:
        self._fn = fn

    def aggregate(self, evaluation: EvaluationResult) -> T:  # noqa: D401
        return self._fn(evaluation)


# Simple projector helpers
def identity_float(value: object) -> float:
    try:
        return float(value)  # type: ignore[arg-type]
    except Exception:
        return 0.0


def mean_of_list(values: list[float]) -> float:
    if not values:
        return 0.0
    return float(sum(values) / len(values))


def sum_of_list(values: list[float]) -> float:
    return float(sum(values))


def sum_of_dict_values(d: dict[str, float]) -> float:
    return float(sum(d.values()))
