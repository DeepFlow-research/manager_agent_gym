"""
Convert LLM-generated rubrics to executable WorkflowRubric objects.

Handles compilation of code rules and construction of LLM-judge rubrics.
"""

from manager_agent_gym.core.agents.manager_agent.implementations.rubric_generation_manager.rubric_generation import (
    ManagerAgentGeneratedRubricWithMetadata,
    ManagerAgentGeneratedStagedRubric,
    ManagerAgentGeneratedStagedRubricWithMetadata,
    EvaluationStageSpec,
    CodeRule,
    LLMJudgeRule,
)
from manager_agent_gym.schemas.preferences.rubric import RubricCriteria, RunCondition
from manager_agent_gym.schemas.preferences.evaluator import (
    Rubric,
    AggregationStrategy,
)
from manager_agent_gym.schemas.preferences.evaluation import (
    StagedRubric,
    EvaluationStage,
)
from manager_agent_gym.core.common.logging import logger


def convert_to_rubric_criteria(
    spec: ManagerAgentGeneratedRubricWithMetadata,
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


def convert_to_rubric(
    spec: ManagerAgentGeneratedRubricWithMetadata,
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
    rubrics = convert_to_rubric_criteria(spec, preference_name, run_condition)

    return Rubric(
        name=f"{preference_name}_auto_generated",
        description=spec.rationale or f"Auto-generated rubric for {preference_name}",
        criteria=rubrics,
        aggregation=aggregation,
        metadata=spec.metadata,  # Preserve metadata from generation (as Pydantic object)
    )


def convert_stage_spec_to_execution(
    stage_spec: EvaluationStageSpec,
    run_condition: RunCondition = RunCondition.ON_COMPLETION,
) -> EvaluationStage:
    """Convert stage specification to executable evaluation stage.
    
    Args:
        stage_spec: Stage specification from LLM/GDPEval
        run_condition: When rules should run
        
    Returns:
        EvaluationStage ready for execution with converted rules
    """
    # Convert rules to dict format (will be parsed at execution time)
    rules_dict = []
    for rule in stage_spec.rules:
        if isinstance(rule, CodeRule):
            rules_dict.append({
                "type": "code",
                "name": rule.name,
                "description": rule.description,
                "weight": rule.weight,
                "code": rule.code,
            })
        elif isinstance(rule, LLMJudgeRule):
            rules_dict.append({
                "type": "llm_judge",
                "name": rule.name,
                "description": rule.description,
                "weight": rule.weight,
                "judge_prompt": rule.judge_prompt,
                "expectation": rule.expectation,
            })
    
    return EvaluationStage(
        name=stage_spec.name,
        description=stage_spec.description,
        is_required=stage_spec.is_required,
        min_score_to_pass=stage_spec.min_score_to_pass,
        rules=rules_dict,
        max_points=stage_spec.max_points,
        on_failure_action=stage_spec.on_failure_action,
        on_failure_score=stage_spec.on_failure_score,
    )


def convert_staged_rubric_to_executable(
    staged_spec: ManagerAgentGeneratedStagedRubric | ManagerAgentGeneratedStagedRubricWithMetadata,
) -> StagedRubric:
    """Convert staged rubric specification to executable format.
    
    IMPORTANT: If staged_spec has metadata, it will be preserved in the executable
    rubric so that execution costs can be tracked back to the same metadata object.
    
    Args:
        staged_spec: Staged rubric from LLM or GDPEval (with or without metadata)
        
    Returns:
        StagedRubric ready for execution (with metadata reference if provided)
    """
    logger.info(
        f"Converting staged rubric '{staged_spec.category_name}' "
        f"with {len(staged_spec.stages)} stages"
    )
    
    # Convert each stage
    execution_stages = []
    for stage_spec in staged_spec.stages:
        execution_stages.append(
            convert_stage_spec_to_execution(stage_spec)
        )
    
    # Extract metadata if present (for WithMetadata variant)
    metadata_ref = None
    if isinstance(staged_spec, ManagerAgentGeneratedStagedRubricWithMetadata):
        metadata_ref = staged_spec.metadata
        logger.info(
            f"Preserving metadata reference: "
            f"generation_cost=${metadata_ref.generation_llm_cost_usd}, "
            f"calls={metadata_ref.generation_llm_calls}"
        )
    
    rubric = StagedRubric(
        category_name=staged_spec.category_name,
        rationale=staged_spec.rationale,
        max_total_score=staged_spec.max_total_score,
        stages=execution_stages,
        metadata=metadata_ref,  # Preserve metadata reference for execution cost tracking
    )
    
    # Validate stages
    rubric.validate_stages()
    
    return rubric


def convert_flat_to_staged(
    flat_spec: ManagerAgentGeneratedRubricWithMetadata,
    preference_name: str | None = None,
) -> ManagerAgentGeneratedStagedRubric:
    """Convert flat rubric to single-stage rubric for backward compatibility.
    
    This allows legacy flat rubrics to work in the staged-only evaluation system.
    The flat rubric becomes a single stage with no gating (always passes).
    
    Args:
        flat_spec: Flat rubric specification from LLM
        preference_name: Optional name for the category
        
    Returns:
        Staged rubric with one stage containing all rules
    """
    total_weight = sum(rule.weight for rule in flat_spec.rules)
    
    # Create single stage with all rules (no gating)
    stage = EvaluationStageSpec(
        name="Evaluation",
        description=flat_spec.rationale or f"Evaluation for {preference_name or flat_spec.rubric_id}",
        is_required=False,  # Not a gate
        min_score_to_pass=0.0,  # Always passes
        rules=flat_spec.rules,
        max_points=total_weight,
        on_failure_action="continue",  # Never stops
        on_failure_score=0.0,
    )
    
    return ManagerAgentGeneratedStagedRubric(
        category_name=preference_name or flat_spec.rubric_id,
        rationale=flat_spec.rationale,
        max_total_score=total_weight,
        stages=[stage],
    )
