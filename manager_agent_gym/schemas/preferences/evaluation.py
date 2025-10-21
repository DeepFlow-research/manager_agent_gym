from __future__ import annotations
from datetime import datetime
from uuid import UUID
from typing import Any, TypeAlias
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
