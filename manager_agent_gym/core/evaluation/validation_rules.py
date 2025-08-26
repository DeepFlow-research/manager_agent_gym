"""
Concrete implementations of validation rules for workflow, task, and resource validation.
"""

import time
import inspect
import traceback

from ..common.llm_interface import (
    generate_structured_response,
    LLMInferenceTruncationError,
)
from ...schemas.common.llm_responses import (
    LLMScoredResponse,
    LLMScoreLevel,
)
from ...schemas.evaluation.success_criteria import (
    ValidationContext,
    ValidationResult,
    ValidationLevel,
    ValidationFrequency,
    WorkflowValidatorFunc,
)
from ..common.logging import logger
from ...schemas.evaluation.workflow_scope import WorkflowScope, WorkflowSection
from ...schemas.evaluation.success_criteria import ValidationMeta


class WorkflowValidationRule:
    """Validation rule that operates on workflow-level properties."""

    def __init__(
        self,
        name: str,
        seed: int,
        validator: WorkflowValidatorFunc | None = None,
        llm_prompt: str | None = None,
        model: str = "o3",
        max_score: float = 1.0,
        description: str = "",
        frequency: ValidationFrequency = ValidationFrequency.ON_COMPLETION,
        metric: str | None = None,
        weight: float = 1.0,
        scope: WorkflowScope | None = None,
    ):
        # Inline BaseValidationRule fields
        self.name = name
        self.max_score = max_score
        self.description = description
        self.frequency = frequency
        self.metric = metric
        self.weight = weight

        if validator is None and llm_prompt is None:
            raise ValueError("Either validator function or llm_prompt must be provided")
        if validator is not None and llm_prompt is not None:
            raise ValueError(
                "Provide either validator function OR llm_prompt, not both"
            )

        self.validator = validator
        self.llm_prompt = llm_prompt
        self.model = model
        self.scope = scope
        self.seed: int = seed

    def to_dict(self) -> dict:
        """Convert validation rule to serializable dictionary."""
        return {
            "name": self.name,
            "max_score": self.max_score,
            "description": self.description,
            "frequency": self.frequency.value,
            "validation_type": "llm" if self.llm_prompt else "function",
            "llm_prompt": self.llm_prompt,
            "model": self.model,
            "has_validator": self.validator is not None,
            "metric": self.metric,
            "weight": self.weight,
            "scope": self.scope.model_dump() if self.scope else None,
        }

    async def validate(self, context: ValidationContext) -> ValidationResult:
        """Run workflow-level validation."""
        start_time = time.time()

        try:
            if self.validator:
                # Use custom function validation (handle both sync and async)

                if inspect.iscoroutinefunction(self.validator):
                    result = await self.validator(context.workflow)
                else:
                    result = self.validator(context.workflow)

                # Handle different return types from validator functions
                if isinstance(result, bool):
                    # Boolean result: convert to score
                    score = self.max_score if result else 0.0
                    passed = result
                elif isinstance(result, (int, float)):
                    # Numeric result: use as score
                    # result might be a float or an awaitable (checked above); coerce safely
                    score = float(result)  # type: ignore[arg-type]
                    passed = score >= (self.max_score * 0.8)  # 80% threshold
                else:
                    # Fallback: treat as boolean
                    score = self.max_score if bool(result) else 0.0
                    passed = bool(result)

                message = f"Workflow validation '{self.name}': {'PASSED' if passed else 'FAILED'} ({score:.2f}/{self.max_score})"
                if self.description:
                    message += f" - {self.description}"

                return self._create_result(
                    score=score,
                    message=message,
                    level=ValidationLevel.WORKFLOW,
                    passed=passed,
                    details={
                        "validation_type": "function",
                        "description": self.description,
                    },
                    execution_time=time.time() - start_time,
                )

            else:
                # Use LLM validation
                return await self._llm_validate(context, start_time)

        except LLMInferenceTruncationError as e:
            logger.warning(
                "LLM workflow validation '%s' refused by provider: %s",
                self.name,
                str(e),
            )
            return self._create_result(
                score=0.0,
                message=(
                    f"Workflow validation '{self.name}' not evaluated due to provider refusal"
                    + (f": {e.refusal_text}")
                ),
                level=ValidationLevel.WORKFLOW,
                passed=False,
                error=str(e),
                execution_time=time.time() - start_time,
            )
        except Exception as e:
            logger.error(
                f"Workflow validation '{self.name}' failed with error: {e} traceback: {traceback.format_exc()}"
            )
            return self._create_result(
                score=0.0,
                message=f"Workflow validation '{self.name}' failed with error",
                level=ValidationLevel.WORKFLOW,
                passed=False,
                error=str(e),
                execution_time=time.time() - start_time,
            )

    async def _llm_validate(
        self, context: ValidationContext, start_time: float
    ) -> ValidationResult:
        """Run LLM-based workflow validation."""
        try:
            # Prepare workflow context for LLM
            workflow_context = self._prepare_scoped_workflow_context(
                context, self.scope
            )

            validation_prompt = f"""
You are an LLM evaluator for multi-agent workflows.

Definition and setting:
- A workflow in this system is a structured plan of tasks, resources, and communications executed by a team of specialized agents (and sometimes humans) collaborating to achieve a stated project goal.
- The provided workflow context below contains the full, current state: goal, agents, tasks with dependencies and status, produced resources, costs, quality metrics, and communications.

Evaluation framing:
- We want to evaluate how well the workflow performed on specific aspects (e.g., quality, governance/compliance, completeness, timeliness, coordination). The VALIDATION CRITERIA below defines the exact aspect and how to judge it for this evaluation (treat it like a rubric).

Instructions:
- Carefully read the VALIDATION CRITERIA and operationalize them as checkable conditions.
- Use only the WORKFLOW CONTEXT as evidence. If evidence is missing or inconclusive, state that explicitly and score conservatively.
- Return a single field named score whose type matches what the criteria requests: boolean (true/false), a categorical level ("low" | "medium" | "high"), or a numeric value in [0, {self.max_score}].
- In reasoning, include brief citations to evidence from the workflow and short, actionable next steps to pass/improve.

Scoring guide for numeric scores (apply these rules uniformly):
- 0: No relevant evidence, contradictory evidence, or explicit failures against the criteria.
- 0.25×max: Minimal evidence or weak/indirect signals; at most one element satisfied with major gaps.
- 0.5×max: Partial fulfillment; roughly half of the required elements satisfied with cited evidence; notable gaps remain.
- 0.75×max: Strong fulfillment; most elements satisfied with high-quality evidence; only minor gaps or missing citations.
- 1.0×max (i.e., {self.max_score}): Complete fulfillment across all required elements with explicit, verifiable citations; quantitative KPIs where applicable.

Partial-credit rules when criteria enumerate elements (e.g., items (a)-(d) or bullet lists):
- Divide the maximum score evenly across the N enumerated elements.
- For each element: award 0 for absent/contradictory, 0.5 of the element share for incomplete or weak evidence, and 1.0 of the element share for clear, well-cited satisfaction.
- If evidence is entirely missing for the criterion, cap the total at 0.5×max.
- If there is contradictory evidence, reduce the total by at least 0.25×max (not below 0).

VALIDATION CRITERIA:
{self.llm_prompt}

WORKFLOW CONTEXT (full):
{workflow_context}

OUTPUT REQUIREMENTS (JSON only, no prose outside JSON):
- score: true/false, "low"/"medium"/"high", or a number in [0, {self.max_score}] as directed by the criteria
- reasoning: 3–6 sentences with evidence-based justification and specific next steps
- confidence: number in [0,1]
"""
            llm_response = await generate_structured_response(
                system_prompt="You are a validation expert.",
                user_prompt=validation_prompt,
                response_type=LLMScoredResponse,
                model=self.model,
                # temperature=0.1,
                seed=self.seed,
            )

            # Interpret union score (bool | level | numeric)
            raw_score = llm_response.score
            final_score: float
            if isinstance(raw_score, bool):
                passed = raw_score
                final_score = self.max_score if raw_score else 0.0
                level_for_msg = "high" if raw_score else "low"
            elif isinstance(raw_score, LLMScoreLevel):
                if raw_score == LLMScoreLevel.HIGH:
                    weighting = 1.0
                elif raw_score == LLMScoreLevel.MEDIUM:
                    weighting = 0.66
                else:
                    weighting = 0.33
                final_score = self.max_score * weighting
                passed = final_score >= (self.max_score * 0.8)
                level_for_msg = raw_score.value
            elif isinstance(raw_score, (int, float)):
                # Raw numeric score is already in the same scale as max_score
                final_score = max(0.0, min(self.max_score, float(raw_score)))
                passed = final_score >= (self.max_score * 0.8)
                if final_score >= (self.max_score * 0.8):
                    level_for_msg = "high"
                elif final_score >= (self.max_score * 0.5):
                    level_for_msg = "medium"
                else:
                    level_for_msg = "low"
            else:
                # Accept string levels for robustness
                try:
                    level_str = str(raw_score).lower()
                    if level_str == "high":
                        final_score = self.max_score
                        passed = True
                    elif level_str == "medium":
                        final_score = self.max_score * 0.66
                        passed = False
                    else:
                        final_score = self.max_score * 0.33
                        passed = False
                    level_for_msg = level_str
                except Exception:
                    raise ValueError(f"Invalid score type: {type(raw_score)}")

            message = f"LLM workflow validation '{self.name}': {'PASSED' if passed else 'FAILED'} REASONING: {llm_response.reasoning} ({final_score:.2f}/{self.max_score}, level={level_for_msg})"

            return self._create_result(
                score=final_score,
                message=message,
                level=ValidationLevel.WORKFLOW,
                passed=passed,
                details={
                    "validation_type": "llm",
                    "reasoning": llm_response.reasoning,
                    "model": self.model,
                    "prompt": self.llm_prompt,
                },
                execution_time=time.time() - start_time,
            )

        except LLMInferenceTruncationError as e:
            logger.warning(
                "LLM workflow validation '%s' refused by provider: %s",
                self.name,
                str(e),
            )
            return self._create_result(
                score=0.0,
                message=(
                    f"LLM workflow validation '{self.name}' not evaluated due to provider refusal"
                    + (f": {e.refusal_text}")
                ),
                level=ValidationLevel.WORKFLOW,
                passed=False,
                error=str(e),
                execution_time=time.time() - start_time,
            )
        except Exception as e:
            logger.error(
                f"LLM workflow validation '{self.name}' failed with error: {e} traceback: {traceback.format_exc()}"
            )
            return self._create_result(
                score=0.0,
                message=f"LLM workflow validation '{self.name}' failed with error",
                level=ValidationLevel.WORKFLOW,
                passed=False,
                error=str(e),
                execution_time=time.time() - start_time,
            )

    def _prepare_scoped_workflow_context(
        self, context: ValidationContext, scope: WorkflowScope | None
    ) -> str:
        """Construct an evidence string limited to the requested workflow sections and filters."""
        workflow = context.workflow
        if scope is None:
            return workflow.pretty_print(include_resources=True)

        lines: list[str] = []

        # Workflow headline
        if WorkflowSection.WORKFLOW in scope.sections:
            lines.append("-" * 70)
            lines.append(f"Workflow: {workflow.name} (ID: {workflow.id})")
            lines.append(f"Goal: {workflow.workflow_goal}")
            lines.append(
                f"Budget (est): ${workflow.total_budget:.2f} | Expected hours: {workflow.total_expected_hours:.2f}"
            )
            lines.append(f"Cost (actual): ${workflow.total_cost:.2f}")

        # Agents
        if WorkflowSection.AGENTS in scope.sections:
            lines.append("Agents:")
            lines.append(f"- Count: {len(workflow.agents)}")
            if workflow.agents:
                sample = list(workflow.agents.keys())[:10]
                lines.append(
                    f"- IDs: {', '.join(sample)}{'...' if len(workflow.agents) > 10 else ''}"
                )

        # Tasks
        if WorkflowSection.TASKS in scope.sections:
            lines.append("Tasks:")
            for t in workflow.tasks.values():
                if scope.task_ids and t.id not in scope.task_ids:
                    continue
                lines.append(t.pretty_print(indent=1))
                if not scope.include_subtasks:
                    # Optionally trim subtask sections by clipping preview
                    pass

        # Resources
        lines.append("Resources:")
        if not scope.sections or WorkflowSection.RESOURCES in scope.sections:
            for r in workflow.resources.values():
                if scope.resource_ids and r.id not in scope.resource_ids:
                    continue
                if scope.resource_types and r.content_type not in scope.resource_types:
                    continue
                try:
                    lines.append(r.pretty_print())
                except Exception:
                    lines.append(f"Resource: {r.name} (ID: {r.id})")
        else:
            lines.append("(not shown)")

        # Messages
        lines.append("Messages:")
        if not scope.sections or WorkflowSection.MESSAGES in scope.sections:
            shown = 0
            for m in sorted(workflow.messages, key=lambda x: x.timestamp, reverse=True):
                if scope.since and m.timestamp < scope.since:
                    continue
                if scope.message_types and m.message_type not in scope.message_types:
                    continue
                if scope.related_task_ids and (
                    m.related_task_id is None
                    or m.related_task_id not in scope.related_task_ids
                ):
                    continue
                lines.append(
                    f"[{m.timestamp.isoformat()}] {m.sender_id} -> {sorted(m.get_all_recipients())}: {m.content}"
                )
                shown += 1
                if shown >= 50:
                    break
        else:
            lines.append("(not shown)")

        # Preferences
        lines.append("Preferences:")
        if not scope.sections or WorkflowSection.PREFERENCES in scope.sections:
            if context.current_preferences:
                for pref in context.current_preferences.preferences:
                    lines.append(f"- {pref.name}: {pref.weight:.2f}")
            else:
                lines.append("(not shown)")
        else:
            lines.append("(not shown)")

        return (
            "\n".join(lines) if lines else workflow.pretty_print(include_resources=True)
        )

    def _create_result(
        self,
        score: float,
        message: str,
        level: ValidationLevel,
        passed: bool | None = None,
        details: dict[str, object] | None = None,
        error: str | None = None,
        execution_time: float = 0.0,
    ) -> ValidationResult:
        # Default pass threshold at 80% of max unless explicitly provided
        if passed is None:
            passed = score >= (self.max_score * 0.8)
        meta = ValidationMeta(
            execution_time=execution_time,
            error=error,
            details=details or {},
        )
        return ValidationResult(
            name=self.name,
            score=score,
            max_score=self.max_score,
            passed=passed,
            message=message,
            level=level,
            metric=self.metric,
            weight=self.weight,
            meta=meta,
        )
