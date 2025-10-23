"""Staged evaluation rubric schema.

Extends MA-Gym rubrics with:
- Sequential evaluation stages
- Gates (mandatory prerequisites)
- Thresholds (minimum scores to proceed)
- Conditional evaluation (skip stages if gates fail)
"""

from pydantic import BaseModel, Field
from typing import Literal
from manager_agent_gym.core.agents.manager_agent.implementations.rubric_generation_manager.rubric_generation import (
    CodeRule,
    LLMJudgeRule,
)


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
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum score ratio (score/max_points) to 'pass' stage",
    )

    rules: list[CodeRule | LLMJudgeRule] = Field(
        description="Rules evaluated in this stage", min_length=1
    )

    max_points: float = Field(gt=0, description="Maximum points for this stage")

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

    def validate_stages(self) -> None:
        """Validate that stages make sense."""
        total_max = sum(stage.max_points for stage in self.stages)
        if total_max > self.max_total_score:
            raise ValueError(
                f"Sum of stage max points ({total_max}) exceeds "
                f"category max ({self.max_total_score})"
            )

    def evaluate(
        self, task_input: str, candidate_output: str, verbose: bool = False
    ) -> dict:
        """Evaluate output using staged rubric.

        Args:
            task_input: Original task description
            candidate_output: Submitted output to evaluate
            verbose: If True, include detailed stage/rule results

        Returns:
            dict with:
                - total_score: Final score (0 to max_total_score)
                - max_score: Maximum possible score
                - normalized_score: total_score / max_score
                - stages_evaluated: Number of stages evaluated
                - stages_passed: Number of stages passed
                - failed_gate: Name of gate that failed (if any)
                - stopped_at: Stage where evaluation stopped (if any)
                - stages: List of stage results (if verbose=True)
        """
        results = {
            "total_score": 0.0,
            "max_score": self.max_total_score,
            "stages_evaluated": 0,
            "stages_passed": 0,
            "failed_gate": None,
            "stopped_at": None,
        }

        if verbose:
            results["stages"] = []

        for stage_idx, stage in enumerate(self.stages):
            results["stages_evaluated"] += 1

            stage_result = {
                "name": stage.name,
                "score": 0.0,
                "max_points": stage.max_points,
                "passed": False,
                "is_required": stage.is_required,
            }

            if verbose:
                stage_result["rules"] = []

            # Evaluate all rules in stage
            for rule in stage.rules:
                try:
                    # Execute rule evaluation
                    if rule.type == "code":
                        # Execute code rule
                        exec_globals = {}
                        exec(rule.code, exec_globals)
                        evaluate_fn = exec_globals.get("evaluate")
                        if evaluate_fn:
                            rule_score = evaluate_fn(task_input, candidate_output)
                        else:
                            rule_score = 0.0

                    elif rule.type == "llm_judge":
                        # For now, mock LLM evaluation (will integrate properly later)
                        # In real implementation, this would call LLM
                        rule_score = 0.5  # Placeholder

                    else:
                        rule_score = 0.0

                    stage_result["score"] += rule_score

                    if verbose:
                        stage_result["rules"].append(
                            {"name": rule.name, "type": rule.type, "score": rule_score}
                        )

                except Exception as e:
                    # Rule execution failed
                    if verbose:
                        stage_result["rules"].append(
                            {
                                "name": rule.name,
                                "type": rule.type,
                                "score": 0.0,
                                "error": str(e),
                            }
                        )

            # Cap score at stage maximum
            stage_result["score"] = min(stage_result["score"], stage.max_points)

            # Check if stage passed
            score_ratio = stage_result["score"] / stage.max_points
            stage_result["passed"] = score_ratio >= stage.min_score_to_pass

            if stage_result["passed"]:
                results["stages_passed"] += 1

            # Handle stage failure
            if not stage_result["passed"] and stage.is_required:
                results["failed_gate"] = stage.name

                if stage.on_failure_action == "zero_category":
                    # Zero out entire category
                    results["total_score"] = stage.on_failure_score
                    results["stopped_at"] = stage.name

                    if verbose:
                        results["stages"].append(stage_result)

                    results["normalized_score"] = (
                        results["total_score"] / results["max_score"]
                    )
                    return results

                elif stage.on_failure_action == "skip_remaining":
                    # Stop here, keep current score
                    results["stopped_at"] = stage.name

                    if verbose:
                        results["stages"].append(stage_result)

                    results["normalized_score"] = (
                        results["total_score"] / results["max_score"]
                    )
                    return results

            # Add stage score to total
            results["total_score"] += stage_result["score"]

            if verbose:
                results["stages"].append(stage_result)

        # Cap at maximum
        results["total_score"] = min(results["total_score"], self.max_total_score)
        results["normalized_score"] = results["total_score"] / results["max_score"]

        return results


class GDPEvalStagedRubric(BaseModel):
    """Wrapper for GDPEval task rubric with staged evaluation."""

    task_id: str = Field(description="GDPEval task ID")
    rubric: StagedRubric = Field(description="Staged rubric")
