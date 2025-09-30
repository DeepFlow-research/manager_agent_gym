## Preferences Models

Preferences define stakeholder objectives and the evaluation machinery used to score
workflow outcomes.

### Preference

A single objective with weight, description, and evaluator metadata.

::: manager_agent_gym.schemas.preferences.preference.Preference

### Preference Weights

A collection of weighted objectives that drive manager optimization and evaluation.

::: manager_agent_gym.schemas.preferences.preference.PreferenceWeights

### Evaluation Result

Structured output from preference evaluators summarising scores and reasoning.

::: manager_agent_gym.schemas.preferences.evaluation.EvaluationResult

### Workflow Rubric

Declarative rubric configuration for rule-based or LLM-based evaluation hooks.

::: manager_agent_gym.schemas.preferences.rubric.WorkflowRubric

