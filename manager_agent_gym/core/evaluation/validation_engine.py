"""
Stateless evaluation engine.

At each timestep, evaluates:
- Preference evaluators (from `PreferenceWeights`), batching all rubrics with a tqdm bar
- Optional floating evaluators provided explicitly for the workflow

Rubrics can be implemented as code functions or via LLM prompts. For LLM,
we reuse `WorkflowValidationRule` to format, call, and interpret responses.
"""

import asyncio
import inspect
import tqdm  # type: ignore
from typing import Any, Callable, cast

from ...schemas.evaluation.success_criteria import (
    ValidationContext,
    ValidationFrequency,
)
from ...schemas.core.workflow import Workflow
from ...schemas.preferences.preference import PreferenceWeights
from ..evaluation.validation_rules import WorkflowValidationRule
from ..common.logging import logger
from uuid import UUID
from ...schemas.preferences.evaluation import (
    EvaluationResult,
    PreferenceScore,
    RubricResult,
    RubricGroupResult,
)
from ...schemas.preferences.rubric import (
    RunCondition,
    WorkflowRubric,
    AdditionalContextItem,
)
from ...schemas.core.evaluators import EvaluatedScore
from ...schemas.preferences.evaluator import AggregationStrategy, Evaluator
from ...schemas.core.communication import SenderMessagesView
from ...schemas.evaluation.reward import (
    BaseRewardAggregator,
    RewardProjection,
    ScalarUtilityReward,
    identity_float,
)
from ...schemas.workflow_agents.telemetry import AgentPublicState, AgentToolUseEvent
from ...schemas.execution.manager_actions import ActionResult


def _make_pbar(total: int, disable: bool, desc: str):
    return tqdm.tqdm(total=total, disable=disable, desc=desc)


class ValidationEngine:
    """Stateless per-timestep evaluator for preferences and workflow rubrics.

    Runs rubric groups concurrently, normalizes scores, aggregates using
    configurable strategies, and maintains a reward vector over timesteps.

    Args:
        seed (int): Random seed for LLM rubric evaluation consistency.
        max_concurrent_rubrics (int): Concurrency limit for rubric execution.
        log_preference_progress (bool): Show tqdm progress when evaluating preferences.
        selected_timesteps (list[int] | None): Forced evaluation timesteps; if provided,
            cadence checks are augmented to include these timesteps.
        reward_aggregator (BaseRewardAggregator | None): Aggregator mapping evaluation
            results to a reward value (scalar or structured). Defaults to utility sum.
        reward_projection (RewardProjection | None): Optional projector to scalar reward.

    Attributes:
        evaluation_results (list[EvaluationResult]): History of evaluation outputs.
        reward_vector (list[float]): Scalar reward per timestep (zeros where not evaluated).
        most_recent_reward (float): Last projected reward value.
    """

    def __init__(
        self,
        seed: int,
        max_concurrent_rubrics: int = 100,
        log_preference_progress: bool = False,
        selected_timesteps: list[int] | None = None,
        reward_aggregator: BaseRewardAggregator[object] | None = None,
        reward_projection: RewardProjection[object] | None = None,
    ) -> None:
        self._rubric_semaphore: asyncio.Semaphore = asyncio.Semaphore(
            max(1, int(max_concurrent_rubrics))
        )
        self._log_preference_progress: bool = bool(log_preference_progress)
        self.evaluation_results: list[EvaluationResult] = []
        self.selected_timesteps: list[int] | None = selected_timesteps
        # Reward plumbing: allow arbitrary reward value + scalar projection
        self._reward_aggregator: BaseRewardAggregator[object] = (
            reward_aggregator
            if reward_aggregator is not None
            else ScalarUtilityReward()
        )
        self._reward_projection: RewardProjection[object] = (
            reward_projection if reward_projection is not None else identity_float
        )
        self._last_reward_value: object | None = None
        self.most_recent_reward: float = 0.0
        # Full reward vector (per timestep), defaulting to zeros for timesteps without eval
        self.reward_vector: list[float] = []
        # Seed for LLM-based rubric evaluation
        self.seed: int = seed

    async def evaluate_timestep(
        self,
        workflow: Workflow,
        timestep: int,
        cadence: RunCondition,
        communications: list[SenderMessagesView] | None,
        manager_actions: list[ActionResult] | None,
        preferences: PreferenceWeights | None = None,
        workflow_evaluators: list[Evaluator] | None = None,
    ) -> EvaluationResult:
        """Evaluate all rubrics (preferences + floating) concurrently with one progress bar."""

        # 1) Prepare mappings for aggregation after execution
        pref_name_to_eval: dict[str, Evaluator] = {}
        pref_name_to_weight: dict[str, float] = {}
        force_full_eval = bool(
            self.selected_timesteps and (timestep in self.selected_timesteps)
        )

        if preferences is not None and cadence is not None:
            for p in preferences.preferences:
                if p.evaluator is not None:
                    # p.evaluator is Optional[Evaluator]; assert non-None inside the block
                    pref_name_to_eval[p.name] = p.evaluator  # type: ignore[assignment]
                    pref_name_to_weight[p.name] = p.weight

        workflow_eval_by_name: dict[str, Evaluator] = {}
        if workflow_evaluators:
            for wf_ev in workflow_evaluators:
                workflow_eval_by_name[wf_ev.name] = wf_ev

        # 2) Collect all scheduled rubrics with an owner key
        owner_to_kind: dict[str, str] = {}  # owner_key -> "preference" | "workflow"
        scheduled: list[tuple[str, WorkflowRubric]] = []

        if preferences is not None and cadence is not None:
            for p in preferences.preferences:
                pref_ev = p.evaluator
                if pref_ev is None:
                    continue
                for r in pref_ev.rubrics:
                    if force_full_eval or r.run_condition == cadence:
                        scheduled.append((p.name, r))
                        owner_to_kind[p.name] = "preference"

        if workflow_evaluators:
            for wf_ev in workflow_evaluators:
                for r in wf_ev.rubrics:
                    if (
                        force_full_eval
                        or r.run_condition == cadence
                        or cadence is not None
                    ):
                        scheduled.append((wf_ev.name, r))
                        owner_to_kind[wf_ev.name] = "workflow"

        # 3) Run all rubrics concurrently using a single TaskGroup and tqdm
        rubric_results_by_owner: dict[str, list[RubricResult]] = {}
        normalized_by_owner: dict[str, list[float]] = {}

        async def _eval_one(owner: str, r: WorkflowRubric) -> None:
            async with self._rubric_semaphore:
                # Build minimal, per-rubric context on demand
                ctx = self._build_context_for_rubric(
                    workflow=workflow,
                    timestep=timestep,
                    preferences=preferences,
                    required=r.required_context,
                    communications=communications,
                    manager_actions=manager_actions,
                )
                es, error_message, raw_output = await self._evaluate_single_rubric(
                    workflow, r, ctx
                )
            clamped = max(0.0, min(r.max_score, float(es.score)))
            normalized = clamped / r.max_score if r.max_score > 0 else 0.0
            rr = RubricResult(
                name=r.name,
                score=clamped,
                max_score=r.max_score,
                normalized_score=normalized,
                message=es.reasoning,
                error=error_message,
                raw_output=raw_output,
            )
            rubric_results_by_owner.setdefault(owner, []).append(rr)
            normalized_by_owner.setdefault(owner, []).append(normalized)
            pbar.update(1)

        pbar = _make_pbar(
            total=len(scheduled),
            disable=(len(scheduled) == 0) or (not self._log_preference_progress),
            desc="Evaluating rubrics",
        )
        try:
            async with asyncio.TaskGroup() as tg:  # Python 3.11+
                for owner, r in scheduled:
                    tg.create_task(_eval_one(owner, r))
        finally:
            pbar.close()

        # 4) Aggregate back into the requested output schema
        preference_scores: dict[str, PreferenceScore] = {}
        preference_sum_weighted = 0.0
        for pref_name, evaluator in pref_name_to_eval.items():
            norm_scores = normalized_by_owner.get(pref_name, [])
            # Weighted-by-max aggregation: sum(score)/sum(max)
            rubrics_for_pref = rubric_results_by_owner.get(pref_name, [])
            if rubrics_for_pref:
                total_max = sum(float(r.max_score or 0.0) for r in rubrics_for_pref)
                total_raw = sum(float(r.score or 0.0) for r in rubrics_for_pref)
                aggregated = (total_raw / total_max) if total_max > 0 else 0.0
            else:
                aggregated = self._aggregate_scores(
                    normalized_scores=norm_scores,
                    strategy=evaluator.aggregation,
                    rubrics=rubric_results_by_owner.get(pref_name, []),
                    workflow=workflow,
                    context=None,
                )
            weight = pref_name_to_weight.get(pref_name, 0.0)
            pref_agg_strategy = (
                evaluator.aggregation.value
                if isinstance(evaluator.aggregation, AggregationStrategy)
                else "custom"
            )
            preference_scores[pref_name] = PreferenceScore(
                name=pref_name,
                score=aggregated,
                weight=weight,
                ruberic_group_results=RubricGroupResult(
                    evaluator_name=evaluator.name,
                    rubric_scores=rubric_results_by_owner.get(pref_name, []),
                ),
                aggregation_strategy=pref_agg_strategy,
            )
            preference_sum_weighted += aggregated * weight

        evaluation_results: list[RubricGroupResult] = []
        for name, ev in workflow_eval_by_name.items():
            rubrics = rubric_results_by_owner.get(name, [])
            # Weighted-by-max for workflow-level evaluators too
            if rubrics:
                total_max = sum(float(r.max_score or 0.0) for r in rubrics)
                total_raw = sum(float(r.score or 0.0) for r in rubrics)
                agg_score = (total_raw / total_max) if total_max > 0 else 0.0
            else:
                norm_scores_for_owner = normalized_by_owner.get(name, [])
                agg_score = self._aggregate_scores(
                    normalized_scores=norm_scores_for_owner,
                    strategy=ev.aggregation,
                    rubrics=rubrics,
                    workflow=workflow,
                    context=None,
                )
            evaluation_results.append(
                RubricGroupResult(
                    evaluator_name=name,
                    rubric_scores=rubrics,
                    aggregated_score=agg_score,
                    aggregation_strategy="weighted_by_max",
                )
            )

        result = EvaluationResult(
            workflow_id=workflow.id,
            timestep=timestep,
            preference_scores=preference_scores,
            evaluation_results=evaluation_results,
            weighted_preference_total=preference_sum_weighted,
        )
        # Only append to history when a cadence is specified (on-demand calls with
        # cadence=None should not mutate history as some tests expect)
        if cadence is not None:
            self.evaluation_results.append(result)
        # Compute and store reward value for this timestep (or accumulated if desired)
        try:
            self._last_reward_value = self._reward_aggregator.aggregate(result)
            self.most_recent_reward = float(
                self._reward_projection(self._last_reward_value)
            )
        except Exception:
            # Never raise from reward calculation; default to utility
            try:
                agg_name = type(self._reward_aggregator).__name__
            except Exception:
                agg_name = "<unknown>"
            logger.error(
                "Reward aggregation failed using %s; defaulting to weighted utility",
                agg_name,
                exc_info=True,
            )
            self._last_reward_value = preference_sum_weighted
            self.most_recent_reward = float(preference_sum_weighted)
        # Ensure reward_vector is timestep-aligned and zero for gaps
        # Expand with zeros if needed up to current timestep index
        if len(self.reward_vector) <= timestep:
            self.reward_vector.extend([0.0] * (timestep + 1 - len(self.reward_vector)))
        # Record reward only when an eval cadence was actually run; else keep zero
        if cadence is not None:
            self.reward_vector[timestep] = self.most_recent_reward
        return result

    # Generic setter supporting typed aggregator + scalar projection
    def set_reward_aggregator(
        self,
        aggregator: BaseRewardAggregator[object],
        projection: Callable[[object], float] | None = None,
    ) -> None:
        # Store as object-typed to avoid Any-typed attributes while permitting generics
        self._reward_aggregator = aggregator
        if projection is not None:
            self._reward_projection = projection

    def get_last_reward_value(self) -> object | None:
        return self._last_reward_value

    async def _evaluate_single_rubric(
        self, workflow: Workflow, rubric: WorkflowRubric, context: ValidationContext
    ) -> tuple[EvaluatedScore, str | None, Any | None]:
        try:
            if rubric.evaluator_function is not None:
                # Prefer calling (workflow, context) if function supports 2 args; fallback to (workflow)

                fn = rubric.evaluator_function
                dyn_fn: Callable[..., Any] = cast(Callable[..., Any], fn)
                try:
                    params = list(inspect.signature(fn).parameters.values())  # type: ignore[arg-type]
                except Exception:
                    params = []
                if len(params) >= 2:
                    if asyncio.iscoroutinefunction(fn):
                        result = await dyn_fn(workflow, context)
                    else:
                        result = dyn_fn(workflow, context)
                elif len(params) == 1 and params[0].name != "workflow":
                    # Single non-workflow parameter, assume it wants the context
                    if asyncio.iscoroutinefunction(fn):
                        result = await dyn_fn(context)
                    else:
                        result = dyn_fn(context)
                else:
                    # Legacy call with workflow only
                    if asyncio.iscoroutinefunction(fn):
                        result = await dyn_fn(workflow)
                    else:
                        result = dyn_fn(workflow)
                es, raw = self._normalize_user_result(result, rubric.max_score)
                return es, None, raw

            if rubric.llm_prompt is not None:
                # Reuse WorkflowValidationRule LLM flow for rubric evaluation
                temp_rule = WorkflowValidationRule(
                    name=f"rubric::{rubric.name}",
                    llm_prompt=rubric.llm_prompt,
                    max_score=float(rubric.max_score),
                    description=rubric.description or "",
                    frequency=ValidationFrequency.MANUAL,
                    seed=self.seed,
                )
                vr = await temp_rule.validate(context)
                reasoning = (
                    vr.meta.details.get("reasoning")
                    if vr.meta and vr.meta.details
                    else vr.message
                )
                return (
                    EvaluatedScore(score=float(vr.score), reasoning=str(reasoning)),
                    None,
                    None,
                )

            return (
                EvaluatedScore(score=0.0, reasoning="No evaluator provided"),
                "No evaluator provided",
                None,
            )
        except Exception as e:
            logger.error("rubric evaluation failed", exc_info=True)
            return (
                EvaluatedScore(score=0.0, reasoning=f"Error during evaluation: {e}"),
                str(e),
                None,
            )

    def _build_context_for_rubric(
        self,
        workflow: Workflow,
        timestep: int,
        preferences: PreferenceWeights | None,
        required: set[AdditionalContextItem],
        communications: list[SenderMessagesView] | None,
        manager_actions: list[ActionResult] | None,
    ) -> ValidationContext:
        from ...core.workflow_agents.interface import AgentInterface

        """Construct a minimal ValidationContext with only requested items."""
        ctx = ValidationContext(
            workflow=workflow,
            current_preferences=preferences,
            timestep=timestep,
        )
        if AdditionalContextItem.MANAGER_ACTIONS in required:
            ctx.manager_actions = manager_actions or []
        if AdditionalContextItem.COMMS_BY_SENDER in required:
            ctx.communications_by_sender = communications or []
        # Placeholders for future requested items
        if AdditionalContextItem.COMMS_BY_THREAD in required:
            ctx.communications_by_thread = None
        if AdditionalContextItem.PREFERENCE_HISTORY in required:
            ctx.preference_history = None
        if AdditionalContextItem.STAKEHOLDER_PROFILE in required:
            ctx.stakeholder_profile = None
        if AdditionalContextItem.RESOURCES_BY_TASK in required:
            ctx.resources_by_task = None
        if AdditionalContextItem.AGENT_PUBLIC_STATES in required:
            try:
                public_states: dict[str, AgentPublicState] = {}
                for agent_id, agent in workflow.agents.items():
                    agent = cast(AgentInterface, agent)
                    public_states[agent_id] = AgentPublicState(
                        agent_id=agent.agent_id,
                        agent_type=agent.agent_type,
                        is_available=agent.is_available,
                        current_task_ids=list(agent.current_task_ids),
                        max_concurrent_tasks=int(agent.max_concurrent_tasks),
                        tasks_completed=int(agent.tasks_completed),
                        joined_at=agent.joined_at,
                    )
                ctx.agent_public_states = public_states
            except Exception:
                logger.debug(
                    "Failed building agent public states for rubric context",
                    exc_info=True,
                )
                ctx.agent_public_states = {}
        if AdditionalContextItem.AGENT_TOOL_USAGE_BY_TASK in required:
            try:
                usage_by_task: dict[UUID, list[AgentToolUseEvent]] = {}
                # Walk all agents and merge their per-task tool usage
                for agent in workflow.agents.values():
                    try:
                        for task_id, events in agent.get_tool_usage_by_task().items():
                            usage_by_task.setdefault(task_id, []).extend(events)
                    except Exception:
                        logger.debug(
                            "Agent tool usage retrieval failed for one agent",
                            exc_info=True,
                        )
                        continue
                ctx.agent_tool_usage_by_task = usage_by_task
            except Exception:
                logger.warning(
                    "Failed aggregating agent tool usage by task; continuing with empty map",
                    exc_info=True,
                )
                ctx.agent_tool_usage_by_task = {}
        return ctx

    def _normalize_user_result(
        self, result: Any, max_score: float
    ) -> tuple[EvaluatedScore, Any]:
        try:
            if isinstance(result, tuple):
                if len(result) == 2:
                    score_value, reasoning_value = result
                    return (
                        EvaluatedScore(
                            score=float(score_value), reasoning=str(reasoning_value)
                        ),
                        result,
                    )
                if len(result) == 1:
                    (score_value,) = result
                    return EvaluatedScore(
                        score=float(score_value), reasoning=""
                    ), result
                return (
                    EvaluatedScore(
                        score=0.0, reasoning="Invalid tuple shape for score"
                    ),
                    result,
                )
            if isinstance(result, (int, float)):
                return EvaluatedScore(score=float(result), reasoning=""), result
            try:
                score_attr = result.score  # type: ignore[attr-defined]
                score_value = float(score_attr)
                try:
                    reasoning_attr = result.reasoning  # type: ignore[attr-defined]
                    reasoning_text = (
                        "" if reasoning_attr is None else str(reasoning_attr)
                    )
                except Exception:
                    logger.debug(
                        "Result object lacks 'reasoning' attribute or is invalid",
                        exc_info=True,
                    )
                    reasoning_text = ""
                return EvaluatedScore(
                    score=score_value, reasoning=reasoning_text
                ), result
            except Exception:
                logger.debug(
                    "Result object lacks 'score' attribute or is invalid; attempting float()",
                    exc_info=True,
                )
            return EvaluatedScore(score=float(result), reasoning=""), result
        except Exception:
            return EvaluatedScore(score=0.0, reasoning="Normalization failed"), result

    def _aggregate_scores(
        self,
        normalized_scores: list[float],
        strategy: AggregationStrategy | Callable[..., float],
        rubrics: list[RubricResult] | None = None,
        workflow: Workflow | None = None,
        context: ValidationContext | None = None,
    ) -> float:
        if not normalized_scores:
            return 0.0
        # Custom callable strategy
        if not isinstance(strategy, AggregationStrategy):
            try:
                fn = strategy
                params = list(inspect.signature(fn).parameters.values())
                # Dispatch by arity for flexibility
                if len(params) == 1:
                    return float(cast(Any, fn)(normalized_scores))
                if len(params) == 2:
                    return float(cast(Any, fn)(normalized_scores, rubrics))
                if len(params) == 3:
                    return float(cast(Any, fn)(normalized_scores, rubrics, workflow))
                # 4+ assume (scores, rubrics, workflow, context)
                return float(
                    cast(Any, fn)(normalized_scores, rubrics, workflow, context)
                )
            except Exception:
                logger.debug(
                    "Custom aggregation strategy failed; returning 0.0",
                    exc_info=True,
                )
                return 0.0
        # Built-in strategies
        match strategy:
            case AggregationStrategy.WEIGHTED_AVERAGE:
                return sum(normalized_scores) / len(normalized_scores)
            case AggregationStrategy.MIN:
                return min(normalized_scores)
            case AggregationStrategy.MAX:
                return max(normalized_scores)
            case AggregationStrategy.PRODUCT:
                product = 1.0
                for s in normalized_scores:
                    product *= s
                return product
            case AggregationStrategy.HARMONIC_MEAN:
                if any(s == 0 for s in normalized_scores):
                    return 0.0
                return len(normalized_scores) / sum(
                    1 / s for s in normalized_scores if s > 0
                )
