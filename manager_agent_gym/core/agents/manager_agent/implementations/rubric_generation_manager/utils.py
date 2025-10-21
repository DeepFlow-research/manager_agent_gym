"""
Convert LLM-generated rubrics to executable WorkflowRubric objects.

Handles compilation of code rules and construction of LLM-judge rubrics.
"""

from manager_agent_gym.core.agents.manager_agent.implementations.rubric_generation_manager.rubric_generation import (
    ManagerAgentGeneratedRubric,
    CodeRule,
    LLMJudgeRule,
)
from manager_agent_gym.schemas.preferences.rubric import RubricCriteria, RunCondition
from manager_agent_gym.schemas.preferences.evaluator import (
    Rubric,
    AggregationStrategy,
)
from manager_agent_gym.core.common.logging import logger


def convert_to_workflow_rubrics(
    spec: ManagerAgentGeneratedRubric,
    preference_name: str,
    run_condition: RunCondition = RunCondition.ON_COMPLETION,
) -> list[RubricCriteria]:
    """Convert LLM-generated spec to executable WorkflowRubric objects.

    Args:
        spec: Generated rubric specification from LLM
        preference_name: Name of preference (for rubric naming)
        run_condition: When rubrics should run (default: on completion)

    Returns:
        List of WorkflowRubric objects ready for evaluation

    Raises:
        ValueError: If code compilation fails
    """
    workflow_rubrics: list[RubricCriteria] = []

    logger.info(
        f"Converting {len(spec.rules)} rules to WorkflowRubrics for '{preference_name}'"
    )

    for rule in spec.rules:
        try:
            match rule:
                case CodeRule():
                    workflow_rubrics.append(
                        RubricCriteria(
                            name=rule.name,
                            description=rule.description,
                            max_score=float(rule.weight),
                            stringified_evaluator_function=rule.code,
                            llm_prompt=None,
                            run_condition=run_condition,
                        )
                    )
                case LLMJudgeRule():
                    workflow_rubrics.append(
                        RubricCriteria(
                            name=rule.name,
                            description=rule.description,
                            max_score=float(rule.weight),
                            evaluator_function=None,
                            llm_prompt=rule.judge_prompt,
                            run_condition=run_condition,
                        )
                    )

        except Exception as e:
            logger.error(f"Failed to convert rule '{rule.name}': {e}")
            # Re-raise to fail fast - we don't want partial rubrics
            raise

    return workflow_rubrics


def convert_to_evaluator(
    spec: ManagerAgentGeneratedRubric,
    preference_name: str,
    run_condition: RunCondition = RunCondition.ON_COMPLETION,
    aggregation: AggregationStrategy = AggregationStrategy.WEIGHTED_AVERAGE,
) -> Rubric:
    """Convert LLM-generated spec to complete Evaluator.

    Args:
        spec: Generated rubric specification from LLM
        preference_name: Name of preference
        run_condition: When rubrics should run
        aggregation: How to combine rubric scores

    Returns:
        Evaluator with all rubrics ready to use
    """
    rubrics = convert_to_workflow_rubrics(spec, preference_name, run_condition)

    return Rubric(
        name=f"{preference_name}_auto_generated",
        description=spec.rationale or f"Auto-generated rubric for {preference_name}",
        criteria=rubrics,
        aggregation=aggregation,
    )
