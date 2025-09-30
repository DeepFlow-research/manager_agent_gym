## Evaluation

Evaluation components score workflow performance against stakeholder objectives.

### Validation Engine

Runs rubrics, aggregates preference scores, and computes multi-objective regret.

::: manager_agent_gym.core.evaluation.validation_engine.ValidationEngine

### Reward Aggregators

Reusable utilities that turn per-objective scores into scalar or vector rewards.

::: manager_agent_gym.schemas.evaluation.reward.BaseRewardAggregator

::: manager_agent_gym.schemas.evaluation.reward.ScalarUtilityReward

::: manager_agent_gym.schemas.evaluation.reward.PreferenceVectorReward

::: manager_agent_gym.schemas.evaluation.reward.PreferenceDictReward

