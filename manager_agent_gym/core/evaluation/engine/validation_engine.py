"""
Stateless evaluation engine.

At each timestep, evaluates:
- Preference evaluators (from `PreferenceWeights`), batching all rubrics with a tqdm bar
- Optional floating evaluators provided explicitly for the workflow

Rubrics can be implemented as:
- Code functions (via `CodeRuleExecutor`)
- LLM prompts (via `MultimodalEvaluator` with vision support)
- Legacy evaluator functions (backwards compatibility)
"""

import asyncio
import inspect
import tqdm  # type: ignore
from typing import Any, Callable, cast

from manager_agent_gym.core.evaluation.schemas.success_criteria import (
    ValidationContext,
)
from manager_agent_gym.schemas.domain.workflow import Workflow
from manager_agent_gym.schemas.domain.task_execution import TaskExecution
from manager_agent_gym.schemas.preferences.preference import PreferenceSnapshot
from manager_agent_gym.core.common.logging import logger
from uuid import UUID
from manager_agent_gym.schemas.preferences.evaluation import (
    EvaluationResult,
    RubricResult,
    StagedRubric,
    StagedRubricResult,
    TimestepEvaluationResult,
    TaskEvaluationMetrics,
    ExecutionEvaluationResult,
)
from manager_agent_gym.schemas.preferences.rubric import (
    RunCondition,
    RubricCriteria,
    AdditionalContextItem,
)
from manager_agent_gym.core.common.schemas.evaluators import EvaluatedScore
from manager_agent_gym.schemas.preferences.evaluator import AggregationStrategy
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
        ignore_gates: bool = False,
        max_concurrent_rubrics: int = 100,
        log_preference_progress: bool = False,
        reward_aggregator: BaseRewardAggregator[object] | None = None,
        reward_projection: RewardProjection[object] | None = None,
    ) -> None:
        self._rubric_semaphore: asyncio.Semaphore = asyncio.Semaphore(
            max(1, int(max_concurrent_rubrics))
        )
        self._log_preference_progress: bool = bool(log_preference_progress)
        self.evaluation_results: list[EvaluationResult] = []
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
        self._seed = seed
        self._ignore_gates = ignore_gates

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
            "stage_results": [],
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
                    rule_results.append(
                        {
                            "name": rule_dict["name"],
                            "type": rule_dict["type"],
                            "score": score_obj.score,
                            "max_score": rule_dict["weight"],
                            "feedback": feedback or score_obj.reasoning,
                        }
                    )

                except Exception as e:
                    logger.error(f"Error evaluating rule {rule_dict.get('name')}: {e}")
                    rule_results.append(
                        {
                            "name": rule_dict.get("name", "unknown"),
                            "type": rule_dict.get("type", "unknown"),
                            "score": 0.0,
                            "max_score": rule_dict.get("weight", 0.0),
                            "error": str(e),
                        }
                    )

            # Cap stage score at max
            stage_score = min(stage_score, stage.max_points)

            # Check if stage passed (using absolute score)
            score_ratio = (
                stage_score / stage.max_points if stage.max_points > 0 else 0.0
            )
            passed = stage_score >= stage.min_score_to_pass

            results["stage_results"].append(
                {
                    "name": stage.name,
                    "description": stage.description,
                    "score": stage_score,
                    "max_points": stage.max_points,
                    "score_ratio": score_ratio,
                    "passed": passed,
                    "is_required": stage.is_required,
                    "rules": rule_results,
                }
            )

            if passed:
                results["stages_passed"] += 1

            # Handle gate failure (unless gates are ignored)
            if not passed and stage.is_required and not self._ignore_gates:
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
            elif not passed and stage.is_required and self._ignore_gates:
                # Record failure but continue evaluation
                results["failed_gate"] = (
                    stage.name
                    if results.get("failed_gate") is None
                    else results["failed_gate"]
                )
                logger.info(
                    f"Stage '{stage.name}' failed (required gate) - "
                    f"but continuing evaluation (ignore_gates=True)"
                )

            # Add stage score to total
            results["total_score"] += stage_score

        # Cap at maximum
        results["total_score"] = min(
            results["total_score"], staged_rubric.max_total_score
        )
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
                *[task for _, task in tasks], desc="Evaluating staged rubrics"
            )
        else:
            completed = await asyncio.gather(*[task for _, task in tasks])

        # Map results by category name
        for (category_name, _), result in zip(tasks, completed):
            results[category_name] = result

        return results

    async def evaluate_execution_with_staged_rubrics(
        self,
        workflow: Workflow,
        execution: TaskExecution,
        timestep: int,
        staged_rubrics: list[StagedRubric],
        communications: list[SenderMessagesView] | None = None,
        manager_actions: list[ActionResult] | None = None,
    ) -> dict[str, StagedRubricResult]:
        """Evaluate a SINGLE execution with staged rubrics.

        Scopes evaluation to only the resources produced by this execution.

        Args:
            workflow: Full workflow (for context)
            execution: Specific TaskExecution to evaluate
            timestep: Current timestep
            staged_rubrics: Rubrics to evaluate with
            communications: Optional communications
            manager_actions: Optional manager actions

        Returns:
            Dict mapping rubric category_name to result for THIS execution
        """

        # Create context scoped to this execution's resources
        context = ValidationContext(
            workflow=workflow,
            timestep=timestep,
            manager_actions=manager_actions,
            communications_by_sender=communications,
        )

        # Get this execution's output resources
        execution_resources = [
            workflow.resources[res_id]
            for res_id in execution.output_resource_ids
            if res_id in workflow.resources
        ]

        logger.info(
            f"📊 Evaluating execution {execution.id} (agent={execution.agent_id}): "
            f"{len(execution_resources)} output resources"
        )
        for idx, res in enumerate(execution_resources):
            logger.info(
                f"  Output {idx + 1}: {res.name} ({res.mime_type}, {res.size_bytes} bytes) at {res.file_path}"
            )

        # Override context to ONLY see this execution's resources
        context.set_evaluable_resources(execution_resources)

        # Evaluate all rubrics against this execution
        results = {}
        tasks = []
        for rubric in staged_rubrics:
            task = self.evaluate_staged_rubric(workflow, rubric, context)
            tasks.append((rubric.category_name, task))

        # Run evaluations
        if self._log_preference_progress:
            from tqdm.asyncio import tqdm_asyncio

            completed = await tqdm_asyncio.gather(
                *[task for _, task in tasks],
                desc=f"Evaluating execution {execution.variant_index}",
            )
        else:
            completed = await asyncio.gather(*[task for _, task in tasks])

        # Map results by category
        for (category_name, _), result in zip(tasks, completed):
            results[category_name] = result

        return results

    async def evaluate_timestep(
        self,
        workflow: Workflow,
        timestep: int,
        staged_rubrics: list[StagedRubric],
        communications: list[SenderMessagesView] | None = None,
        manager_actions: list[ActionResult] | None = None,
    ) -> TimestepEvaluationResult:
        """Evaluate all task executions for GRPO training.

        This is the main entry point for evaluation. It:
        1. Evaluates each completed execution separately with gold rubrics
        2. Groups executions by task
        3. Computes group-relative advantages per task
        4. Returns structured Pydantic result ready for GRPO loss computation

        Args:
            workflow: Workflow to evaluate
            timestep: Current timestep
            staged_rubrics: Gold standard rubrics (typically from GDPEval)
            communications: Optional communications
            manager_actions: Optional manager actions

        Returns:
            TimestepEvaluationResult containing per-task metrics, advantages, and full details
        """

        logger.info("=" * 80)
        logger.info("📊 Timestep Evaluation (GRPO Mode)")
        logger.info("=" * 80)

        # ============================================================
        # Phase 1: Collect and group executions by task
        # ============================================================
        task_executions: dict[UUID, list] = {}

        for task in workflow.tasks.values():
            if not task.is_atomic_task():
                continue

            completed_execs = [
                workflow.task_executions[exec_id]
                for exec_id in task.execution_ids
                if workflow.task_executions[exec_id].is_completed()
            ]

            if completed_execs:
                task_executions[task.id] = completed_execs

        total_executions = sum(len(execs) for execs in task_executions.values())
        logger.info(
            f"Found {total_executions} completed executions across "
            f"{len(task_executions)} tasks"
        )

        if not task_executions:
            logger.warning("No completed executions found for evaluation")
            # Return empty result
            return TimestepEvaluationResult(
                workflow_id=workflow.id,
                timestep=timestep,
                per_task_metrics={},
                total_executions=0,
                total_tasks=0,
                mean_baseline_across_tasks=0.0,
                execution_details={},
            )

        # ============================================================
        # Phase 2: Evaluate each execution separately
        # ============================================================
        execution_results: dict[UUID, dict] = {}  # exec_id -> {scores, results}

        for task_id, executions in task_executions.items():
            task = workflow.tasks[task_id]
            logger.info(
                f"Evaluating {len(executions)} executions for task '{task.name}'"
            )

            # Create evaluation tasks for parallel execution
            eval_tasks = []
            for execution in executions:
                logger.info(
                    f"  ⏳ Queueing evaluation for execution {execution.id} (agent={execution.agent_id})"
                )
                eval_task = self.evaluate_execution_with_staged_rubrics(
                    workflow=workflow,
                    execution=execution,
                    timestep=timestep,
                    staged_rubrics=staged_rubrics,
                    communications=communications,
                    manager_actions=manager_actions,
                )
                eval_tasks.append((execution, eval_task))

            # Run evaluations in PARALLEL (much faster!)
            logger.info(f"  🚀 Running {len(eval_tasks)} evaluations in parallel...")
            eval_results = await asyncio.gather(*[task for _, task in eval_tasks])

            # Process results
            for (execution, _), rubric_results in zip(eval_tasks, eval_results):
                # Extract scores per rubric category
                rubric_scores = {
                    category: result.normalized_score
                    for category, result in rubric_results.items()
                }

                # Aggregate score (average across rubrics)
                aggregate_score = (
                    sum(rubric_scores.values()) / len(rubric_scores)
                    if rubric_scores
                    else 0.0
                )

                # Store results
                execution_results[execution.id] = {
                    "task_id": task_id,
                    "task_name": task.name,
                    "variant_index": execution.variant_index,
                    "rubric_scores": rubric_scores,
                    "aggregate_score": aggregate_score,
                    "rubric_results": rubric_results,
                    "rubric_metadata": execution.metadata.get("rubric_generation", {}),
                    "rubric_type": execution.metadata.get("rubric_type"),
                    "generation_seed": execution.metadata.get("generation_seed"),
                }

                logger.info(
                    f"  Execution {execution.variant_index}: score={aggregate_score:.3f}"
                )

        # ============================================================
        # Phase 3: Compute advantages per task
        # ============================================================
        per_task_metrics: dict[str, TaskEvaluationMetrics] = {}

        for task_id, executions in task_executions.items():
            task = workflow.tasks[task_id]

            # Extract scores for this task (K scores)
            task_scores = {
                ex.id: execution_results[ex.id]["aggregate_score"] for ex in executions
            }

            # Compute group-relative baseline
            K = len(task_scores)
            baseline = sum(task_scores.values()) / K if K > 0 else 0.0

            # Compute advantages: A_k = r_k - baseline
            advantages = {
                ex_id: score - baseline for ex_id, score in task_scores.items()
            }

            # Build ExecutionEvaluationResult objects
            execution_results_list = []
            for execution in executions:
                ex_result = execution_results[execution.id]
                execution_results_list.append(
                    ExecutionEvaluationResult(
                        execution_id=execution.id,
                        variant_index=execution.variant_index,
                        task_id=task_id,
                        task_name=task.name,
                        aggregate_score=ex_result["aggregate_score"],
                        advantage=advantages[execution.id],
                        rubric_results=ex_result["rubric_results"],
                        rubric_scores=ex_result["rubric_scores"],
                        rubric_metadata=ex_result["rubric_metadata"],
                        rubric_type=ex_result["rubric_type"],
                        generation_seed=ex_result["generation_seed"],
                    )
                )

            per_task_metrics[str(task_id)] = TaskEvaluationMetrics(
                task_id=task_id,
                task_name=task.name,
                num_executions=K,
                baseline=baseline,
                executions=execution_results_list,
            )

            logger.info(
                f"Task '{task.name}': K={K}, baseline={baseline:.3f}, "
                f"advantages=[{', '.join(f'{advantages[ex.id]:.3f}' for ex in executions)}]"
            )

        # ============================================================
        # Phase 4: Build execution details lookup
        # ============================================================
        execution_details: dict[str, ExecutionEvaluationResult] = {}

        for task_metrics in per_task_metrics.values():
            execution_result: ExecutionEvaluationResult
            for execution_result in task_metrics.executions:
                execution_details[str(execution_result.execution_id)] = execution_result

        # ============================================================
        # Phase 5: Compute aggregate metrics
        # ============================================================
        mean_baseline = (
            sum(m.baseline for m in per_task_metrics.values()) / len(per_task_metrics)
            if per_task_metrics
            else 0.0
        )

        result = TimestepEvaluationResult(
            workflow_id=workflow.id,
            timestep=timestep,
            per_task_metrics=per_task_metrics,
            total_executions=total_executions,
            total_tasks=len(task_executions),
            mean_baseline_across_tasks=mean_baseline,
            execution_details=execution_details,
        )

        logger.info("=" * 80)
        logger.info("✅ Timestep Evaluation Complete")
        logger.info(f"   Tasks: {result.total_tasks}")
        logger.info(f"   Executions: {result.total_executions}")
        logger.info(f"   Mean Baseline: {result.mean_baseline_across_tasks:.3f}")
        logger.info("=" * 80)

        return result

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
