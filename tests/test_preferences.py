from manager_agent_gym.schemas.preferences.preference import PreferenceWeights
from manager_agent_gym.schemas.preferences.evaluator import (
    Evaluator,
    AggregationStrategy,
)
from manager_agent_gym.schemas.preferences.preference import Preference


def test_preference_weights_utilities() -> None:
    pw = PreferenceWeights(
        preferences=[
            Preference(
                name="quality",
                weight=0.6,
                evaluator=Evaluator(
                    name="quality_eval",
                    description="placeholder",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=[],
                ),
            ),
            Preference(
                name="cost",
                weight=0.4,
                evaluator=Evaluator(
                    name="cost_eval",
                    description="placeholder",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=[],
                ),
            ),
        ]
    )

    assert abs(sum(p.weight for p in pw.preferences) - 1.0) < 1e-6
    names = pw.get_preference_names()
    assert set(names) == {"quality", "cost"}
    weights = pw.get_preference_dict()
    assert set(weights.keys()) == {"quality", "cost"}
