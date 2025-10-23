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
from datetime import datetime
from typing import Any, Callable, cast

from manager_agent_gym.core.evaluation.schemas.success_criteria import (
    ValidationContext,
)
from manager_agent_gym.schemas.domain.workflow import Workflow
from manager_agent_gym.schemas.preferences.preference import PreferenceSnapshot
from manager_agent_gym.core.common.logging import logger
from uuid import UUID
from manager_agent_gym.schemas.preferences.evaluation import (
    EvaluationResult,
    PreferenceScore,
    RubricResult,
    RubricGroupResult,
    StagedRubric,
    StagedRubricResult,
)
from manager_agent_gym.schemas.preferences.rubric import (
    RunCondition,
    RubricCriteria,
    AdditionalContextItem,
)
from manager_agent_gym.core.common.schemas.evaluators import EvaluatedScore
from manager_agent_gym.schemas.preferences.evaluator import (
    AggregationStrategy,
    Rubric,
)
from manager_agent_gym.schemas.domain.communication import SenderMessagesView
from manager_agent_gym.core.evaluation.schemas.reward import (
    BaseRewardAggregator,
    RewardProjection,
    ScalarUtilityReward,
    identity_float,
)
from manager_agent_gym.core.agents.workflow_agents.schemas.telemetry import (
    AgentPublicState,
    AgentToolUseEvent,
)
from manager_agent_gym.core.agents.manager_agent.actions import ActionResult
from manager_agent_gym.core.agents.workflow_agents.common.interface import (
    AgentInterface,
)


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
        preferences: PreferenceSnapshot | None = None,
        workflow_evaluators: list[Rubric] | None = None,
    ) -> EvaluationResult:
        """Evaluate all rubrics (preferences + floating) concurrently with one progress bar.
        
        .. deprecated::
            Use :meth:`evaluate_timestep_staged` instead. This method uses the old
            flat rubric evaluation path with complex aggregation logic. The new
            staged evaluation path is simpler, more powerful, and supports gate logic.
            
            To migrate:
            1. Convert flat rubrics to staged using `convert_flat_to_staged()`
            2. Call `evaluate_timestep_staged()` instead
            
            This method will be removed in a future version.
        """
        import warnings
        warnings.warn(
            "evaluate_timestep() is deprecated. Use evaluate_timestep_staged() instead. "
            "See STAGED_EVALUATION_DELETION_GUIDE.md for migration instructions.",
            DeprecationWarning,
            stacklevel=2,
        )

        # 1) Prepare mappings for aggregation after execution
        pref_name_to_eval: dict[str, Rubric] = {}
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

        workflow_eval_by_name: dict[str, Rubric] = {}
        if workflow_evaluators:
            for wf_ev in workflow_evaluators:
                workflow_eval_by_name[wf_ev.name] = wf_ev

        # 2) Collect all scheduled rubrics with an owner key
        owner_to_kind: dict[str, str] = {}  # owner_key -> "preference" | "workflow"
        scheduled: list[tuple[str, RubricCriteria]] = []

        if preferences is not None and cadence is not None:
            for p in preferences.preferences:
                pref_ev = p.evaluator
                if pref_ev is None:
                    continue
                for r in pref_ev.criteria:
                    if force_full_eval or r.run_condition == cadence:
                        scheduled.append((p.name, r))
                        owner_to_kind[p.name] = "preference"

        if workflow_evaluators:
            for wf_ev in workflow_evaluators:
                for r in wf_ev.criteria:
                    if (
                        force_full_eval
                        or r.run_condition == cadence
                        or cadence is not None
                    ):
                        scheduled.append((wf_ev.name, r))
                        owner_to_kind[wf_ev.name] = "workflow"

        # 3) Run all rubric crtieria concurrently using a single TaskGroup and tqdm
        rubric_results_by_owner: dict[str, list[RubricResult]] = {}
        normalized_by_owner: dict[str, list[float]] = {}
        execution_times_by_owner: dict[str, list[float]] = {}

        async def _eval_one(owner: str, r: RubricCriteria) -> None:
            import time

            start_time = time.perf_counter()

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

            execution_time = time.perf_counter() - start_time

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
            execution_times_by_owner.setdefault(owner, []).append(execution_time)
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

            # Update rubric metadata with execution metrics
            exec_times = execution_times_by_owner.get(pref_name, [])
            if exec_times and evaluator.metadata:
                total_exec_time = sum(exec_times)

                # Update execution time (accumulate if already calculated)
                current_time = evaluator.metadata.execution_wall_time_seconds
                if isinstance(current_time, (int, float)):
                    evaluator.metadata.execution_wall_time_seconds = (
                        current_time + total_exec_time
                    )
                else:
                    evaluator.metadata.execution_wall_time_seconds = total_exec_time

                evaluator.metadata.execution_count += 1
                evaluator.metadata.last_executed_at = datetime.now().isoformat()

                # Breakdown by criterion
                for rr, exec_time in zip(
                    rubric_results_by_owner.get(pref_name, []), exec_times
                ):
                    evaluator.metadata.execution_breakdown[rr.name] = (
                        evaluator.metadata.execution_breakdown.get(rr.name, 0)
                        + exec_time
                    )

            preference_scores[pref_name] = PreferenceScore(
                name=pref_name,
                score=aggregated,
                weight=weight,
                ruberic_group_results=RubricGroupResult(
                    evaluator_name=evaluator.name,
                    rubric_scores=rubric_results_by_owner.get(pref_name, []),
                    generation_metadata=evaluator.metadata,  # Pass through metadata
                ),
                aggregation_strategy=pref_agg_strategy,
            )
            preference_sum_weighted += aggregated * weight

        evaluation_results: list[RubricGroupResult] = []
        for name, ev in workflow_eval_by_name.items():
            rubrics = rubric_results_by_owner.get(name, [])

            # Update workflow evaluator metadata with execution metrics
            exec_times = execution_times_by_owner.get(name, [])
            if exec_times and ev.metadata:
                total_exec_time = sum(exec_times)

                # Update execution time (accumulate if already calculated)
                current_time = ev.metadata.execution_wall_time_seconds
                if isinstance(current_time, (int, float)):
                    ev.metadata.execution_wall_time_seconds = (
                        current_time + total_exec_time
                    )
                else:
                    ev.metadata.execution_wall_time_seconds = total_exec_time

                ev.metadata.execution_count += 1
                ev.metadata.last_executed_at = datetime.now().isoformat()

                # Breakdown by criterion
                for rr, exec_time in zip(rubrics, exec_times):
                    current_breakdown_time = ev.metadata.execution_breakdown.get(
                        rr.name, 0
                    )
                    ev.metadata.execution_breakdown[rr.name] = (
                        current_breakdown_time + exec_time
                    )
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
                    generation_metadata=ev.metadata,  # Pass through metadata
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
        self,
        workflow: Workflow,
        rubric_criteria: RubricCriteria,
        context: ValidationContext,
    ) -> tuple[EvaluatedScore, str | None, Any | None]:
        try:
            # Get evaluable resources (filtered to output role by default)
            resources = context.get_evaluable_resources()

            # === CODE RULES (stringified functions) ===
            if rubric_criteria.stringified_evaluator_function is not None:
                from manager_agent_gym.core.evaluation.engine.code_rule_executor import (
                    CodeRuleExecutor,
                )

                executor = CodeRuleExecutor()
                score, feedback = await executor.execute(
                    rubric_criteria.stringified_evaluator_function,
                    workflow,
                    context,
                )
                return (
                    EvaluatedScore(score=score, reasoning=feedback or ""),
                    None,
                    None,
                )

            # === LLM JUDGE RULES (multimodal) ===
            if rubric_criteria.llm_prompt is not None:
                from manager_agent_gym.core.evaluation.engine.multimodal_llm import (
                    MultimodalEvaluator,
                )

                evaluator = MultimodalEvaluator()
                score, reasoning = await evaluator.evaluate_with_vision(
                    prompt=rubric_criteria.llm_prompt,
                    resources=resources,
                    max_score=rubric_criteria.max_score,
                    model=rubric_criteria.llm_model,  # Use configured model
                )
                return (
                    EvaluatedScore(score=score, reasoning=reasoning),
                    None,
                    None,
                )

            # === LEGACY EVALUATOR FUNCTIONS (backwards compatibility) ===
            if rubric_criteria.evaluator_function is not None:
                # Try to call with various signatures for backwards compatibility
                fn = rubric_criteria.evaluator_function
                dyn_fn: Callable[..., Any] = cast(Callable[..., Any], fn)
                try:
                    params = list(inspect.signature(fn).parameters.values())  # type: ignore[arg-type]
                except Exception:
                    params = []

                # Try different call signatures
                if len(params) >= 2:
                    # (workflow, context)
                    if asyncio.iscoroutinefunction(fn):
                        result = await dyn_fn(workflow, context)
                    else:
                        result = dyn_fn(workflow, context)
                
                elif len(params) == 1:
                    # Single param - could be workflow, context, or resources
                    param_name = params[0].name if params else ""
                    if param_name == "resources":
                        # New signature: (resources)
                        if asyncio.iscoroutinefunction(fn):
                            result = await dyn_fn(resources)
                        else:
                            result = dyn_fn(resources)
                    elif param_name == "context":
                        # (context)
                        if asyncio.iscoroutinefunction(fn):
                            result = await dyn_fn(context)
                        else:
                            result = dyn_fn(context)
                    else:
                        # Legacy (workflow)
                        if asyncio.iscoroutinefunction(fn):
                            result = await dyn_fn(workflow)
                        else:
                            result = dyn_fn(workflow)
                else:
                    # No params - shouldn't happen but try workflow
                    if asyncio.iscoroutinefunction(fn):
                        result = await dyn_fn(workflow)
                    else:
                        result = dyn_fn(workflow)

                es, raw = self._normalize_user_result(result, rubric_criteria.max_score)
                return es, None, raw

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

    async def evaluate_staged_rubric(
        self,
        workflow: Workflow,
        staged_rubric: StagedRubric,
        context: ValidationContext,
    ) -> StagedRubricResult:
        """Execute staged rubric with sequential gate logic.
        
        Stages are evaluated in order. Each stage can act as a gate that stops
        evaluation if failed.
        
        Args:
            workflow: Workflow being evaluated
            staged_rubric: Staged rubric with sequential stages
            context: Validation context with helpers
            
        Returns:
            StagedRubricResult with total score and stage breakdown
        """
        results = {
            "total_score": 0.0,
            "max_score": staged_rubric.max_total_score,
            "stages_evaluated": 0,
            "stages_passed": 0,
            "failed_gate": None,
            "stopped_at": None,
            "stage_results": []
        }
        
        for stage in staged_rubric.stages:
            results["stages_evaluated"] += 1
            
            stage_score = 0.0
            rule_results = []
            
            # Evaluate all rules in this stage
            for rule_dict in stage.rules:
                try:
                    # Create temporary RubricCriteria for this rule
                    if rule_dict["type"] == "code":
                        criteria = RubricCriteria(
                            name=rule_dict["name"],
                            description=rule_dict["description"],
                            max_score=float(rule_dict["weight"]),
                            stringified_evaluator_function=rule_dict["code"],
                            llm_prompt=None,
                            run_condition=RunCondition.ON_COMPLETION,
                        )
                    elif rule_dict["type"] == "llm_judge":
                        criteria = RubricCriteria(
                            name=rule_dict["name"],
                            description=rule_dict["description"],
                            max_score=float(rule_dict["weight"]),
                            evaluator_function=None,
                            llm_prompt=rule_dict["judge_prompt"],
                            run_condition=RunCondition.ON_COMPLETION,
                        )
                    else:
                        logger.warning(f"Unknown rule type: {rule_dict['type']}")
                        continue
                    
                    # Evaluate the rule
                    score_obj, feedback, _ = await self._evaluate_single_rubric(
                        workflow, criteria, context
                    )
                    
                    stage_score += score_obj.score
                    rule_results.append({
                        "name": rule_dict["name"],
                        "type": rule_dict["type"],
                        "score": score_obj.score,
                        "max_score": rule_dict["weight"],
                        "feedback": feedback or score_obj.reasoning,
                    })
                    
                except Exception as e:
                    logger.error(f"Error evaluating rule {rule_dict.get('name')}: {e}")
                    rule_results.append({
                        "name": rule_dict.get("name", "unknown"),
                        "type": rule_dict.get("type", "unknown"),
                        "score": 0.0,
                        "max_score": rule_dict.get("weight", 0.0),
                        "error": str(e),
                    })
            
            # Cap stage score at max
            stage_score = min(stage_score, stage.max_points)
            
            # Check if stage passed
            score_ratio = stage_score / stage.max_points if stage.max_points > 0 else 0.0
            passed = score_ratio >= stage.min_score_to_pass
            
            results["stage_results"].append({
                "name": stage.name,
                "description": stage.description,
                "score": stage_score,
                "max_points": stage.max_points,
                "score_ratio": score_ratio,
                "passed": passed,
                "is_required": stage.is_required,
                "rules": rule_results,
            })
            
            if passed:
                results["stages_passed"] += 1
            
            # Handle gate failure
            if not passed and stage.is_required:
                results["failed_gate"] = stage.name
                
                if stage.on_failure_action == "zero_category":
                    # Zero out entire score
                    results["total_score"] = stage.on_failure_score
                    results["stopped_at"] = stage.name
                    logger.info(
                        f"Stage '{stage.name}' failed (required gate) - "
                        f"zeroing category score"
                    )
                    break
                    
                elif stage.on_failure_action == "skip_remaining":
                    # Stop evaluation, keep current score
                    results["stopped_at"] = stage.name
                    logger.info(
                        f"Stage '{stage.name}' failed (required gate) - "
                        f"skipping remaining stages"
                    )
                    break
                    
                # else: "continue" - proceed to next stage
            
            # Add stage score to total
            results["total_score"] += stage_score
        
        # Cap at maximum
        results["total_score"] = min(results["total_score"], staged_rubric.max_total_score)
        results["normalized_score"] = results["total_score"] / results["max_score"]
        
        return StagedRubricResult(
            category_name=staged_rubric.category_name,
            total_score=results["total_score"],
            max_score=results["max_score"],
            normalized_score=results["normalized_score"],
            stages_evaluated=results["stages_evaluated"],
            stages_passed=results["stages_passed"],
            failed_gate=results.get("failed_gate"),
            stopped_at=results.get("stopped_at"),
            stage_results=results["stage_results"],
        )

    async def evaluate_timestep_staged(
        self,
        workflow: Workflow,
        timestep: int,
        staged_rubrics: list[StagedRubric],
        communications: list[SenderMessagesView] | None = None,
        manager_actions: list[ActionResult] | None = None,
    ) -> dict[str, StagedRubricResult]:
        """Evaluate workflow using ONLY staged rubrics.
        
        This is the new simplified evaluation path that replaces the complex
        flat rubric evaluation logic.
        
        Args:
            workflow: Workflow to evaluate
            timestep: Current timestep
            staged_rubrics: List of staged rubrics to evaluate
            communications: Optional communications for context
            manager_actions: Optional manager actions for context
            
        Returns:
            Dict mapping rubric category_name to result
        """
        context = ValidationContext(
            workflow=workflow,
            timestep=timestep,
            manager_actions=manager_actions,
            communications_by_sender=communications,
        )
        
        results = {}
        
        # Evaluate all staged rubrics concurrently
        tasks = []
        for rubric in staged_rubrics:
            task = self.evaluate_staged_rubric(workflow, rubric, context)
            tasks.append((rubric.category_name, task))
        
        # Run with progress bar
        if self._log_preference_progress:
            from tqdm.asyncio import tqdm_asyncio
            completed = await tqdm_asyncio.gather(
                *[task for _, task in tasks],
                desc="Evaluating staged rubrics"
            )
        else:
            completed = await asyncio.gather(*[task for _, task in tasks])
        
        # Map results by category name
        for (category_name, _), result in zip(tasks, completed):
            results[category_name] = result
        
        return results

    def _build_context_for_rubric(
        self,
        workflow: Workflow,
        timestep: int,
        preferences: PreferenceSnapshot | None,
        required: set[AdditionalContextItem],
        communications: list[SenderMessagesView] | None,
        manager_actions: list[ActionResult] | None,
    ) -> ValidationContext:
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
