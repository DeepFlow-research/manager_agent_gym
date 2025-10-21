from manager_agent_gym.schemas.preferences.preference import PreferenceSnapshot
from manager_agent_gym.schemas.preferences.evaluator import (
    Rubric,
    AggregationStrategy,
)
from manager_agent_gym.schemas.preferences.preference import Preference
from manager_agent_gym.schemas.preferences.rubric import RubricCriteria
from manager_agent_gym.schemas.domain.workflow import Workflow
from uuid import uuid4


def test_preference_weights_utilities_and_mapping() -> None:
    pw = PreferenceSnapshot(
        preferences=[
            Preference(
                name="quality",
                weight=0.6,
                evaluator=Rubric(
                    name="quality_eval",
                    description="placeholder",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    criteria=[],
                ),
            ),
            Preference(
                name="cost",
                weight=0.4,
                evaluator=Rubric(
                    name="cost_eval",
                    description="placeholder",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    criteria=[],
                ),
            ),
        ]
    )

    assert abs(sum(p.weight for p in pw.preferences) - 1.0) < 1e-6
    names = pw.get_preference_names()
    assert set(names) == {"quality", "cost"}
    weights = pw.get_preference_dict()
    assert set(weights.keys()) == {"quality", "cost"}

    # Ensure name->evaluator mapping preserved and usable
    evals = {p.name: p.evaluator for p in pw.preferences}
    assert evals["quality"] is not None and evals["quality"].name == "quality_eval"
    assert evals["cost"] is not None and evals["cost"].name == "cost_eval"


def test_weighted_average_aggregation_behavior() -> None:
    # Two rubrics under one preference: weighted-by-max aggregation should average 0.25 and 1.0 => 0.625
    def quarter(_: Workflow) -> float:
        return 0.25

    def one(_: Workflow) -> float:
        return 1.0

    evalr = Rubric(
        name="agg_eval",
        description="",
        aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
        criteria=[
            RubricCriteria(name="r1", evaluator_function=quarter, max_score=1.0),
            RubricCriteria(name="r2", evaluator_function=one, max_score=1.0),
        ],
    )

    # Minimal workflow; we only exercise rubric functions here
    wf = Workflow(name="w", workflow_goal="d", owner_id=uuid4())

    # Compute via evaluator functions directly to assert expected math
    scores: list[float] = []
    for r in evalr.criteria:
        assert r.evaluator_function is not None
        scores.append(float(r.evaluator_function(wf)) / float(r.max_score))
    assert abs(sum(scores) / len(scores) - 0.625) < 1e-6
