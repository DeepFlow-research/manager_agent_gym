from __future__ import annotations
from datetime import datetime
from uuid import UUID
from typing import Any, TypeAlias, Literal
from pydantic import BaseModel, Field


class RubricResult(BaseModel):
    """Result of a single criteria evaluation."""

    name: str = Field(..., description="Name of the criteria")
    score: float = Field(
        ..., ge=0.0, description="Score achieved by the criteria (raw units)"
    )
    max_score: float = Field(
        ..., gt=0.0, description="Maximum possible score for the criteria"
    )
    normalized_score: float = Field(
        ..., ge=0.0, le=1.0, description="Score normalized to [0,1]"
    )
    message: str | None = Field(None, description="Optional message or explanation")
    error: str | None = Field(None, description="Error message if evaluation failed")
    raw_output: Any | None = Field(
        None,
        description="Optional raw output returned by the criteria evaluator for transparency",
    )


class RubricGroupResult(BaseModel):
    evaluator_name: str = Field(..., description="Name of the rubric")
    generation_metadata: Any = Field(
        None,
        description="Metadata from rubric generation (RubricGenerationMetadata object: costs, cognitive burden, execution time)",
    )
    rubric_scores: list[RubricResult] = Field(
        ..., description="Scores for each criterion"
    )
    aggregated_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional aggregated normalized score across rubric_scores [0,1]",
    )
    aggregation_strategy: str | None = Field(
        default=None, description="Aggregation strategy used for aggregated_score"
    )


class PreferenceScore(BaseModel):
    """Score for a single preference dimension."""

    name: str = Field(..., description="Name of the preference")
    score: float = Field(
        ..., ge=0.0, le=1.0, description="Normalized score for this preference [0,1]"
    )
    weight: float = Field(
        ..., ge=0.0, le=1.0, description="Normalized weight of this preference"
    )
    ruberic_group_results: RubricGroupResult = Field(
        ..., description="Results of all the criteria runs"
    )
    aggregation_strategy: str = Field(
        ..., description="Strategy used to aggregate criteria scores"
    )


class EvaluationResult(BaseModel):
    """Comprehensive evaluation result for a single timestep."""

    workflow_id: UUID = Field(..., description="ID of the workflow evaluated")
    timestep: int = Field(..., description="Timestep of the evaluation")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Time of evaluation"
    )
    preference_scores: dict[str, PreferenceScore] = Field(
        ..., description="Scores for each preference dimension"
    )
    evaluation_results: list[RubricGroupResult] = Field(
        ..., description="Results of all the evaluations run outside of preferences"
    )
    weighted_preference_total: float = Field(
        ..., description="Weighted sum of all preference scores"
    )
    metrics: dict[str, Any] = Field(
        default_factory=dict, description="Additional aggregated metrics"
    )

    def pretty_print(self) -> str:
        """Return a compact, human-readable summary of the evaluation."""
        lines: list[str] = []
        lines.append(f"Evaluation (timestep={self.timestep})")
        # Preferences
        if self.preference_scores:
            lines.append("- Preferences:")
            for name, ps in self.preference_scores.items():
                lines.append(
                    f"  • {name}: score={ps.score:.3f}, weight={ps.weight:.3f}"
                )
        # Workflow-level rubrics
        if self.evaluation_results:
            lines.append("- Workflow Rubrics:")
            for group in self.evaluation_results:
                agg = (
                    f" (agg={group.aggregated_score:.3f}"
                    f" via {group.aggregation_strategy})"
                    if group.aggregated_score is not None
                    else ""
                )
                lines.append(f"  • {group.evaluator_name}{agg}")
                for rr in group.rubric_scores[:5]:
                    lines.append(
                        f"     - {rr.name}: {rr.normalized_score:.3f} (raw={rr.score:.3f}/{rr.max_score:.1f})"
                    )
                if len(group.rubric_scores) > 5:
                    lines.append(
                        f"     … and {len(group.rubric_scores) - 5} more criteria"
                    )
        # Utility
        lines.append(f"- Total utility: {self.weighted_preference_total:.3f}")
        return "\n".join(lines)


# Backwards-compatibility alias (fixes earlier typo)
RubericGroupResult: TypeAlias = RubricGroupResult


# === Staged Rubric Support (GDPEval-style evaluation) ===


class EvaluationStage(BaseModel):
    """Sequential stage in evaluation pipeline.

    Stages evaluate in order. Each stage can be:
    - A gate (must pass to continue)
    - Optional (failure doesn't stop evaluation)
    - Scored (contributes to total score)
    """

    name: str = Field(description="Stage name (e.g., 'Format Validation Gate')")

    description: str = Field(description="What this stage evaluates")

    is_required: bool = Field(
        default=True, description="Must pass this stage to proceed to next stages"
    )

    min_score_to_pass: float = Field(
        default=0.0,
        ge=0.0,
        description=(
            "Minimum absolute score needed to pass this stage. "
            "Must be <= max_points. "
            "Example: If max_points=8 and min_score_to_pass=6, agent needs 6+ points to pass."
        ),
    )

    rules: list[dict[str, Any]] = Field(
        description="Rules evaluated in this stage (CodeRule or LLMJudgeRule dicts)",
        min_length=1,
    )

    max_points: float = Field(gt=0, description="Maximum points for this stage")

    resource_filter: Literal["final_outputs_only", "include_intermediary", "all"] = (
        Field(
            default="final_outputs_only",
            description=(
                "Which resources this stage should evaluate:\n"
                "- 'final_outputs_only': Only resources with role='output' (default, good for format gates)\n"
                "- 'include_intermediary': Include resources with role='intermediary' (good for quality checks)\n"
                "- 'all': All output and intermediary resources (good for comprehensive process evaluation)\n"
                "Note: Input resources are never included in any mode."
            ),
        )
    )

    on_failure_action: Literal["skip_remaining", "zero_category", "continue"] = Field(
        default="skip_remaining",
        description=(
            "What to do if stage fails:\n"
            "- 'skip_remaining': Stop evaluation, return current score\n"
            "- 'zero_category': Set entire category score to 0\n"
            "- 'continue': Continue to next stage regardless"
        ),
    )

    on_failure_score: float = Field(
        default=0.0,
        description="Score if stage fails and on_failure_action='zero_category'",
    )


class StagedRubric(BaseModel):
    """Rubric with sequential evaluation stages.

    Evaluation proceeds through stages in order:
    1. Evaluate all rules in stage
    2. Check if stage passed (score >= threshold)
    3. If failed and required: apply failure action
    4. If passed or not required: continue to next stage

    Final score is sum of all evaluated stages (capped at max_total_score).
    """

    category_name: str = Field(description="High-level category name")

    rationale: str | None = Field(
        default=None, description="Explanation of rubric design and stage structure"
    )

    max_total_score: float = Field(
        gt=0, description="Maximum possible total score across all stages"
    )

    stages: list[EvaluationStage] = Field(
        description="Evaluation stages in order", min_length=1
    )

    metadata: Any | None = Field(
        default=None,
        description="Optional metadata reference for tracking generation and execution costs",
    )

    def validate_stages(self) -> None:
        """Validate and auto-normalize stage points.

        Instead of raising an error when stage points exceed max_total_score,
        automatically reweight all stages proportionally. This works because
        evaluation scores are relative - what matters for ranking is the ratio
        between outputs, not absolute values.

        Auto-normalization:
        - Preserves relative importance (Stage2 is still 2x Stage1 if designed that way)
        - Ensures all rubrics are valid without complex retry logic
        - Provides better numerical precision when properly scaled
        """
        total_max = sum(stage.max_points for stage in self.stages)

        if total_max > self.max_total_score:
            # Auto-normalize: scale all stage points proportionally
            scaling_factor = self.max_total_score / total_max

            from manager_agent_gym.core.common.logging import logger

            logger.info(
                f"Auto-normalizing stage points: sum={total_max} > max={self.max_total_score}. "
                f"Scaling by {scaling_factor:.3f} to fit within category max."
            )

            # Scale and round all stages
            for stage in self.stages:
                original_points = stage.max_points
                stage.max_points = round(stage.max_points * scaling_factor, 1)
                logger.debug(
                    f"  Stage '{stage.name}': {original_points} → {stage.max_points}"
                )

            # Fix floating point accumulation errors by adjusting the last stage
            new_total = sum(stage.max_points for stage in self.stages)
            difference = new_total - self.max_total_score

            # If there's a small overshoot, adjust the last stage
            if abs(difference) > 0.001 and len(self.stages) > 0:
                last_stage = self.stages[-1]
                adjusted_value = last_stage.max_points - difference
                logger.debug(
                    f"  Adjusting last stage '{last_stage.name}' by {-difference:.2f} "
                    f"to fix floating point accumulation: {last_stage.max_points} → {adjusted_value}"
                )
                last_stage.max_points = round(adjusted_value, 1)

            # Verify final total
            final_total = sum(stage.max_points for stage in self.stages)
            logger.info(
                f"After normalization: sum={final_total} ≤ max={self.max_total_score} ✓"
            )

    def get_preference_summary(self) -> str:
        """Get a summary of the rubric."""
        return f"Rubric for {self.category_name} with {len(self.stages)} stages"


class StagedRubricResult(BaseModel):
    """Result of executing a staged rubric."""

    category_name: str = Field(description="Name of the rubric category")
    total_score: float = Field(description="Final accumulated score")
    max_score: float = Field(description="Maximum possible score")
    normalized_score: float = Field(
        ge=0.0, le=1.0, description="Normalized score [0,1]"
    )
    stages_evaluated: int = Field(description="Number of stages that were evaluated")
    stages_passed: int = Field(description="Number of stages that passed threshold")
    failed_gate: str | None = Field(
        default=None, description="Name of gate that failed (if any)"
    )
    stopped_at: str | None = Field(
        default=None, description="Stage where evaluation stopped (if early exit)"
    )
    stage_results: list[dict[str, Any]] = Field(
        default_factory=list, description="Detailed results per stage"
    )


# === GRPO Training Evaluation Results ===


class ExecutionEvaluationResult(BaseModel):
    """Result of evaluating a single TaskExecution.

    This represents the evaluation of one worker's attempt at a task,
    including their score, advantage (for GRPO), and full rubric results.
    """

    execution_id: UUID = Field(description="ID of the TaskExecution")
    variant_index: int = Field(description="Worker variant index (0, 1, 2, ...)")
    task_id: UUID = Field(description="ID of the parent task")
    task_name: str = Field(description="Name of the parent task")

    # Scores
    aggregate_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Aggregate normalized score (averaged across all rubric categories)",
    )
    advantage: float = Field(
        description="Group-relative advantage: A_k = r_k - baseline. Used for GRPO loss."
    )

    # Rubric results
    rubric_results: dict[str, StagedRubricResult] = Field(
        description="Full evaluation results per rubric category"
    )
    rubric_scores: dict[str, float] = Field(
        description="Normalized scores per rubric category [0,1]"
    )

    # Metadata for GRPO regularization terms
    rubric_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata from rubric generation (costs, cognitive burden, etc.)",
    )
    rubric_type: str | None = Field(
        default=None,
        description="Type of rubric used (e.g., 'gold', 'synthetic', 'baseline')",
    )
    generation_seed: int | None = Field(
        default=None,
        description="Random seed used for this execution (for reproducibility)",
    )


class TaskEvaluationMetrics(BaseModel):
    """Evaluation metrics for all executions of a single task.

    For GRPO, we compute group-relative advantages per task:
    - K workers attempt the same task
    - Each gets a score r_k
    - Baseline = mean(r_1, ..., r_K)
    - Advantage A_k = r_k - baseline
    """

    task_id: UUID = Field(description="ID of the task")
    task_name: str = Field(description="Name of the task")
    num_executions: int = Field(ge=1, description="Number of executions (K)")

    baseline: float = Field(
        ge=0.0,
        le=1.0,
        description="Group-relative baseline: mean score across K executions",
    )

    executions: list[ExecutionEvaluationResult] = Field(
        description="Per-execution results with advantages"
    )


class TimestepEvaluationResult(BaseModel):
    """Complete evaluation result for a timestep.

    This is the main output of `ValidationEngine.evaluate_timestep()`.
    It contains per-task metrics, aggregate statistics, and detailed
    per-execution results ready for GRPO training.
    """

    workflow_id: UUID = Field(description="ID of the evaluated workflow")
    timestep: int = Field(description="Timestep of evaluation")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Time of evaluation"
    )

    # Per-task metrics (for GRPO)
    per_task_metrics: dict[str, TaskEvaluationMetrics] = Field(
        description="Evaluation metrics grouped by task (key = task_id as string)"
    )

    # Aggregate metrics (for multi-task workflows)
    total_executions: int = Field(description="Total number of executions evaluated")
    total_tasks: int = Field(
        description="Total number of tasks with completed executions"
    )
    mean_baseline_across_tasks: float = Field(
        ge=0.0,
        le=1.0,
        description="Mean of per-task baselines (for multi-task workflows)",
    )

    # Detailed execution results (for training loop / analysis)
    execution_details: dict[str, ExecutionEvaluationResult] = Field(
        description="Per-execution results (key = execution_id as string)"
    )

    def pretty_print(self) -> str:
        """Return a human-readable summary."""
        lines = [
            f"Timestep Evaluation (t={self.timestep})",
            f"  Workflow: {self.workflow_id}",
            f"  Tasks: {self.total_tasks}",
            f"  Executions: {self.total_executions}",
            f"  Mean Baseline: {self.mean_baseline_across_tasks:.3f}",
            "",
            "Per-Task Metrics:",
        ]

        for task_metrics in self.per_task_metrics.values():
            lines.append(f"  {task_metrics.task_name}:")
            lines.append(f"    Baseline: {task_metrics.baseline:.3f}")
            lines.append(f"    Executions: {task_metrics.num_executions}")
            for ex in task_metrics.executions:
                lines.append(
                    f"      Variant {ex.variant_index}: "
                    f"score={ex.aggregate_score:.3f}, "
                    f"advantage={ex.advantage:+.3f}"
                )

        return "\n".join(lines)
