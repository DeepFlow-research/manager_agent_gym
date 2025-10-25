"""
Workflow execution engine for discrete timestep-based simulation.

Manages the core execution loop with discrete timesteps where the manager
agent can observe state and take actions between task executions.
"""

from typing import TYPE_CHECKING, Any
import asyncio
import json
import traceback
from datetime import datetime
from typing import cast
from typing import Awaitable, Callable, Sequence
from uuid import UUID
from pydantic import BaseModel, Field

from manager_agent_gym.schemas.domain.communication import SenderMessagesView
from manager_agent_gym.core.workflow.state.state_restorer import WorkflowStateRestorer

from manager_agent_gym.core.common.logging import logger
from asyncio import TaskGroup
from manager_agent_gym.core.agents.stakeholder_agent.interface import StakeholderBase
from manager_agent_gym.core.workflow.schemas.config import OutputConfig
from manager_agent_gym.core.workflow.state.output_writer import WorkflowSerialiser
from manager_agent_gym.schemas.domain.base import TaskStatus
from manager_agent_gym.schemas.domain.resource import Resource
from manager_agent_gym.schemas.domain.task import Task
from manager_agent_gym.schemas.domain.workflow import Workflow
from manager_agent_gym.schemas.domain.task_execution import TaskExecution
from manager_agent_gym.core.execution.schemas.state import ExecutionState

from manager_agent_gym.core.execution.schemas.callbacks import TimestepEndContext
from manager_agent_gym.core.execution.schemas.results import (
    ExecutionResult,
    create_timestep_result,
)
from manager_agent_gym.core.agents.workflow_agents.tools.registry import AgentRegistry
from manager_agent_gym.core.agents.manager_agent.common.interface import ManagerAgent
from manager_agent_gym.core.agents.workflow_agents.common.interface import (
    AgentInterface,
)
from manager_agent_gym.core.agents.workflow_agents.tools.tool_factory import ToolFactory
from manager_agent_gym.schemas.preferences.preference import (
    PreferenceSnapshot,
    PreferenceChangeEvent,
)

from manager_agent_gym.core.communication.service import CommunicationService
from manager_agent_gym.core.evaluation.engine.validation_engine import ValidationEngine
from manager_agent_gym.core.workflow.services import WorkflowQueries, WorkflowMutations
from manager_agent_gym.schemas.preferences.evaluator import Rubric
from manager_agent_gym.core.evaluation.schemas.reward import (
    BaseRewardAggregator,
    RewardProjection,
)
from manager_agent_gym.core.agents.manager_agent.actions import ActionResult
from manager_agent_gym.schemas.preferences.evaluation import (
    StagedRubric,
    StagedRubricResult,
)

if TYPE_CHECKING:
    from manager_agent_gym.core.workflow.phases.interface import (
        PreExecutionPhase,
    )
    from manager_agent_gym.core.common.llm_generator import LLMGenerator


class TaskExecutionEvaluationResult(BaseModel):
    """Result from evaluating and ranking multi-agent task execution outputs.

    Used by task evaluators to return both a score and metadata when
    comparing different agent outputs for the same task. This is an internal
    helper class, distinct from the public WorkflowEvaluationResult.
    """

    score: float
    evaluation_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Flexible metadata (reasoning, error, criteria details, etc.)",
    )


class WorkflowExecutionEngine:
    """Timestep-based workflow execution engine.

    Orchestrates agents and evaluations in a discrete-time loop. Tasks run
    concurrently, while a manager agent observes state and takes actions
    between timesteps. Produces rich artifacts (snapshots, metrics, logs)
    for analysis and benchmarking.

    Args:
        workflow (Workflow): The workflow graph (tasks, resources, constraints).
        agent_registry (AgentRegistry): Dynamic registry used to join/leave agents.
        stakeholder_agent (StakeholderBase): Stakeholder simulator providing
            preferences and messages over time.
        manager_agent (ManagerAgent): The decision-making manager agent.
        seed (int): Global deterministic seed to propagate to components.
        evaluations (list[Evaluator] | None): Optional workflow-level evaluators to run.
        output_config (OutputConfig | None): Output directories and filenames.
        max_timesteps (int): Maximum number of timesteps to execute.
        enable_timestep_logging (bool): Persist per-timestep snapshots and metrics.
        enable_final_metrics_logging (bool): Persist final metrics and summary.
        communication_service (CommunicationService | None): Message bus; a default
            service is created if not provided.
        timestep_end_callbacks (Sequence[Callable[[TimestepEndContext], Awaitable[None]]] | None):
            Optional hooks fired at the end of each timestep (failures logged and ignored).
        log_preference_evaluation_progress (bool): Show tqdm progress for preference evals.
        max_concurrent_rubrics (int): Concurrency limit for rubric evaluation.
        reward_aggregator (BaseRewardAggregator | None): Aggregator used by the evaluator.
        reward_projection (RewardProjection | None): Optional projection to scalar reward.

    Attributes:
        current_timestep (int): Zero-based timestep index.
        execution_state (ExecutionState): Current engine state.
        timestep_results (list[ExecutionResult]): Accumulated per-timestep outputs.
        validation_engine (ValidationEngine): Evaluator used to compute rewards.
        communication_service (CommunicationService): Message hub used by agents.

    Example:
        ```python
        engine = WorkflowExecutionEngine(
            workflow=my_workflow,
            agent_registry=registry,
            stakeholder_agent=stakeholder,
            manager_agent=manager,
            seed=42,
            evaluations=[...],
        )
        results = await engine.run_full_execution()
        ```
    """

    def __init__(
        self,
        workflow: Workflow,
        llm_generator: "LLMGenerator",
        agent_registry: AgentRegistry,
        stakeholder_agent: StakeholderBase,
        manager_agent: ManagerAgent,
        seed: int,
        evaluations: list[Rubric] | None = None,
        output_config: OutputConfig | None = None,
        max_timesteps: int = 50,
        enable_timestep_logging: bool = True,
        enable_final_metrics_logging: bool = True,
        communication_service: CommunicationService | None = None,
        timestep_end_callbacks: Sequence[
            Callable[[TimestepEndContext], Awaitable[None]]
        ]
        | None = None,
        # Preference evaluation controls
        log_preference_evaluation_progress: bool = True,
        max_concurrent_rubrics: int = 100,
        reward_aggregator: BaseRewardAggregator[object] | None = None,
        reward_projection: RewardProjection[object] | None = None,
        # Pre-execution phases
        pre_execution_phases: "list[PreExecutionPhase] | None" = None,
        # Gold standard evaluation rubrics (GDPEval)
        gold_rubrics: "list[StagedRubric] | None" = None,
        ignore_validation_gates: bool = True,
        # LLM generator for structured outputs (rubric generation, etc.)
    ):
        self.workflow = workflow
        self.agent_registry = agent_registry
        self.evaluations = list(evaluations or [])
        self.manager_agent = manager_agent
        self.stakeholder_agent: StakeholderBase = stakeholder_agent
        self.gold_rubrics = gold_rubrics or []

        # Set agent IDs on workflow for easy lookup from actions
        self.workflow.stakeholder_agent_id = stakeholder_agent.config.agent_id
        self.workflow.manager_agent_id = manager_agent.agent_id

        WorkflowMutations.add_agent(self.workflow, stakeholder_agent)
        # Global run seed (for deterministic behavior where supported)
        self.seed: int = seed
        # Pre-execution phases (optional list of phases to run before main loop)
        self.pre_execution_phases = pre_execution_phases or []
        # LLM generator for structured outputs (passed to phases)
        self.llm_generator = llm_generator

        self.output_config = output_config or OutputConfig()
        self.enable_timestep_logging = enable_timestep_logging
        self.enable_final_metrics_logging = enable_final_metrics_logging
        self._timestep_end_callbacks: list[
            Callable[[TimestepEndContext], Awaitable[None]]
        ] = list(timestep_end_callbacks or [])

        # Execution state
        self.current_timestep = 0
        self.execution_state = ExecutionState.INITIALIZED
        self.timestep_results: list[ExecutionResult] = []

        # Task execution tracking
        self.running_tasks: dict[UUID, asyncio.Task] = {}
        self.completed_task_ids: set[UUID] = set()
        self.failed_task_ids: set[UUID] = set()

        self.max_timesteps = max_timesteps
        self._task_group: TaskGroup | None = None

        self.validation_engine = ValidationEngine(
            seed=self.seed,
            ignore_gates=ignore_validation_gates,
            max_concurrent_rubrics=max_concurrent_rubrics,
            log_preference_progress=log_preference_evaluation_progress,
            reward_aggregator=reward_aggregator,
            reward_projection=reward_projection,
        )

        self.communication_service = (
            communication_service
            if communication_service is not None
            else CommunicationService()
        )
        # Inject communication service and propagate seed to all agents
        self._inject_communication_service()
        if self.manager_agent is None:
            raise ValueError("Manager agent must be provided")

        self.manager_agent.configure_seed(self.seed)
        self.stakeholder_agent.configure_seed(self.seed)

        self.output_writer = WorkflowSerialiser(
            self.output_config,
            self.communication_service,
            self.workflow,
        )

        self.preference_history: list[tuple[int, PreferenceSnapshot]] = []
        self.recent_preference_change: PreferenceChangeEvent | None = None
        self.preference_change_total_count: int = 0

        # Track which agents in the workflow were mirrored from the registry.
        # This lets us safely prune only those, leaving user-added agents intact.
        self._registry_mirrored_agent_ids: set[str] = set()

        # Ensure output directories exist (only if logging is enabled)
        if self.enable_timestep_logging or self.enable_final_metrics_logging:
            self.output_writer.ensure_directories()

    def restore_from_snapshot(self, snapshot_dir: str, timestep: int) -> None:
        """
        Restore engine state from a previous simulation snapshot.

        This updates the existing engine with state from a snapshot without
        reconstructing the entire engine. The engine should already be
        constructed with fresh components (workflow, agents, etc.).

        Args:
            snapshot_dir: Path to simulation run directory containing timestep_data/
            timestep: Target timestep to restore from
        """
        # Create and configure state restorer
        restorer = WorkflowStateRestorer(snapshot_dir, timestep)
        restorer.load_snapshot_data()

        logger.info("Restoring workflow state from timestep %s", timestep)

        # Restore all state components
        restorer.restore_workflow_state(self.workflow)
        restorer.restore_stakeholder_preferences(self.stakeholder_agent)
        restorer.restore_communication_history(self.communication_service)
        restorer.restore_manager_action_buffer(self.manager_agent)
        restorer.restore_active_agents(self.agent_registry)

        # Set current timestep and execution state
        self.current_timestep = timestep
        self.execution_state = ExecutionState.RUNNING

    def _restore_workflow_state(self, workflow_snapshot: dict) -> None:
        """Update workflow task and resource states from snapshot."""
        # Update task states
        tasks_data = workflow_snapshot.get("tasks", {})
        for task_id_str, task_data in tasks_data.items():
            task_id = UUID(task_id_str)
            if task_id in self.workflow.tasks:
                task = self.workflow.tasks[task_id]
                # Update key state information
                task.status = TaskStatus(task_data["status"])
                # Note: assigned_agent_id is now tracked in TaskExecution, not Task
                task.actual_duration_hours = task_data.get("actual_duration_hours")
                task.actual_cost = task_data.get("actual_cost")
                task.quality_score = task_data.get("quality_score")
                if task_data.get("started_at"):
                    task.started_at = datetime.fromisoformat(task_data["started_at"])
                if task_data.get("completed_at"):
                    task.completed_at = datetime.fromisoformat(
                        task_data["completed_at"]
                    )
                task.execution_notes = task_data.get("execution_notes", [])

        # Synchronize embedded subtasks with the updated registry to fix status inconsistencies
        for task in self.workflow.tasks.values():
            task.sync_embedded_tasks_with_registry(self.workflow.tasks)

        # Update workflow-level state
        self.workflow.total_cost = workflow_snapshot.get("total_cost", 0.0)
        if workflow_snapshot.get("started_at"):
            self.workflow.started_at = datetime.fromisoformat(
                workflow_snapshot["started_at"]
            )
        if workflow_snapshot.get("completed_at"):
            self.workflow.completed_at = datetime.fromisoformat(
                workflow_snapshot["completed_at"]
            )
        self.workflow.is_active = workflow_snapshot.get("is_active", True)

    async def run_full_execution(
        self, save_outputs: bool = True
    ) -> list[ExecutionResult]:
        """
        Run the complete workflow execution until completion or failure.

        Returns:
            List of timestep results from the execution
        """
        # Run all pre-execution phases (e.g., rubric decomposition, clarification)
        if self.pre_execution_phases:
            logger.info(
                f"Running {len(self.pre_execution_phases)} pre-execution phase(s)..."
            )

            for idx, phase in enumerate(self.pre_execution_phases, 1):
                logger.info(
                    f"Pre-execution phase {idx}/{len(self.pre_execution_phases)}: {phase.__class__.__name__}"
                )
                await phase.run(
                    workflow=self.workflow,
                    llm_generator=self.llm_generator,
                )
                logger.info(f"Phase {idx} complete")

            logger.info("All pre-execution phases complete")

            self.output_writer.save_pre_execution_phase(
                workflow=self.workflow,
            )

        self.manager_agent.set_max_timesteps(self.max_timesteps)
        self.execution_state = ExecutionState.RUNNING

        # Structured concurrency: all validation tasks run under a TaskGroup and
        # must complete before exiting this context
        async with TaskGroup() as tg:
            self._task_group = tg

            while (
                not self._is_terminal_state()
                and self.current_timestep < self.max_timesteps
            ):
                timestep_result = await self.execute_timestep()
                self.timestep_results.append(timestep_result)

                # Save workflow state after each timestep
                await self._save_workflow_state(timestep_result)

                # Check for completion
                if WorkflowQueries.is_complete(self.workflow):
                    self.execution_state = ExecutionState.COMPLETED
                    break

                # Check for explicit end request from agents
                try:
                    if (
                        self.communication_service is not None
                        and self.communication_service.is_end_workflow_requested()
                    ):
                        self.execution_state = ExecutionState.CANCELLED
                        break
                except Exception:
                    logger.error("Error checking end-workflow request", exc_info=True)

            # Check if we hit the timestep limit without completing
            if (
                self.current_timestep >= self.max_timesteps
                and not WorkflowQueries.is_complete(self.workflow)
            ):
                self.execution_state = ExecutionState.FAILED

        # Exiting TaskGroup ensures all scheduled validations completed
        self._task_group = None

        # Run final evaluation
        communications_sender = (
            self.communication_service.get_messages_grouped_by_sender(
                sort_within_group="time",
                include_broadcasts=True,
            )
        )
        comms_by_sender: list[SenderMessagesView] = cast(
            list[SenderMessagesView], communications_sender
        )
        manager_actions = self.manager_agent.get_action_buffer()

        # Terminal evaluation: Evaluate with gold standard rubrics
        from manager_agent_gym.schemas.preferences.evaluation import (
            TimestepEvaluationResult,
        )

        logger.info(
            f"Evaluating with {len(self.gold_rubrics)} gold standard rubric(s)..."
        )

        # Use per-execution evaluation with GRPO metrics
        grpo_evaluation: TimestepEvaluationResult = (
            await self.validation_engine.evaluate_timestep(
                workflow=self.workflow,
                timestep=self.current_timestep,
                staged_rubrics=self.gold_rubrics,
                communications=comms_by_sender,
                manager_actions=manager_actions,
            )
        )

        # Store structured GRPO training data
        if not hasattr(self.workflow, "metadata") or self.workflow.metadata is None:
            self.workflow.metadata = {}

        self.workflow.metadata["timestep_evaluation"] = grpo_evaluation

        # Also store summary for backward compatibility
        self.workflow.metadata["gold_evaluation_results"] = {
            "mean_baseline": grpo_evaluation.mean_baseline_across_tasks,
            "total_executions": grpo_evaluation.total_executions,
            "total_tasks": grpo_evaluation.total_tasks,
            "per_task_baselines": {
                task_id: metrics.baseline
                for task_id, metrics in grpo_evaluation.per_task_metrics.items()
            },
        }

        logger.info(
            f"Gold standard evaluation complete - {grpo_evaluation.total_executions} executions evaluated"
        )
        logger.info(f"Mean baseline: {grpo_evaluation.mean_baseline_across_tasks:.3f}")

        # Save enhanced evaluation data for calibration
        if save_outputs:
            try:
                # Get synthetic rubrics from pre-execution phase
                synthetic_rubrics: list = []
                if self.pre_execution_phases and len(self.pre_execution_phases) > 0:
                    # pre_execution_phases is a list, get the first phase
                    first_phase = self.pre_execution_phases[0]
                    synthetic_rubrics = getattr(first_phase, 'synthetic_rubrics', [])
                
                # Get task executions grouped by task
                task_executions = {}
                for task in self.workflow.tasks.values():
                    if task.execution_ids:
                        execs = [
                            self.workflow.task_executions[exec_id]
                            for exec_id in task.execution_ids
                            if exec_id in self.workflow.task_executions
                        ]
                        if execs:
                            task_executions[task.id] = execs
                
                # Save enhanced data
                if synthetic_rubrics and task_executions:
                    self.output_writer.save_enhanced_evaluation_data(
                        synthetic_rubrics=synthetic_rubrics,
                        ground_truth_rubrics=self.gold_rubrics,
                        task_executions=task_executions,
                        workflow=self.workflow,
                    )
                    logger.info(f"✅ Saved enhanced evaluation data: {len(synthetic_rubrics)} rubrics, {len(task_executions)} tasks")
                else:
                    logger.info(f"ℹ️  Skipping enhanced data save: synthetic_rubrics={len(synthetic_rubrics)}, task_executions={len(task_executions)}")
            except Exception as e:
                logger.warning(f"Failed to save enhanced evaluation data: {e}", exc_info=True)

        # TODO: Compute utility gap if proxy rubrics were generated
        # If workflow.metadata contains both "true_preferences" and "decomposition_state"
        # with proxy preferences, we could:
        # 1. Re-evaluate with proxy preferences
        # 2. Compute gap between TRUE and PROXY scores
        # 3. Store gap metrics in workflow.metadata["utility_gap_analysis"]

        if save_outputs:
            self.serialise_workflow_states_and_metrics()

        return self.timestep_results

    async def execute_timestep(self) -> ExecutionResult:
        """
        Execute a single timestep of the workflow.

        Returns:
            ExecutionResult with details of what happened
        """
        if not self.manager_agent:
            raise ValueError("Manager agent not configured")

        start_time = datetime.now()
        timestep = self.current_timestep

        agent_coordination_changes = self._check_and_apply_agent_changes()

        # DEBUG: Log agent sync status
        logger.info(
            f"🔍 DEBUG: After agent sync - workflow.agents: {list(self.workflow.agents.keys())}"
        )

        manager_action = None
        if self.manager_agent:
            self.execution_state = ExecutionState.WAITING_FOR_MANAGER
            # Unified RL-style step: agent constructs observation internally
            done_flag = self._is_terminal_state() or WorkflowQueries.is_complete(
                self.workflow
            )
            manager_action = await self.manager_agent.step(
                workflow=self.workflow,
                execution_state=self.execution_state,
                current_timestep=self.current_timestep,
                running_tasks=self.running_tasks,
                completed_task_ids=self.completed_task_ids,
                failed_task_ids=self.failed_task_ids,
                communication_service=self.communication_service,
                previous_reward=self.validation_engine.most_recent_reward,
                done=done_flag,
                stakeholder_profile=self.stakeholder_agent.public_profile,
            )
            try:
                action_result = await manager_action.execute(
                    self.workflow, self.communication_service, self.llm_generator
                )
            except Exception:
                logger.error("failed to execute manager action", exc_info=True)
                action_result = None

            # Delegate action logging to the manager agent hook
            self.manager_agent.on_action_executed(
                timestep=timestep,
                action=manager_action,
                action_result=action_result,
            )

        self.execution_state = ExecutionState.EXECUTING_TASKS
        tasks_started, tasks_completed, tasks_failed = await self._execute_ready_tasks()

        self._update_workflow_state(tasks_completed, tasks_failed)

        # Run stakeholder policy step (skip at timestep 0 to avoid processing pre-execution messages)
        if self.current_timestep > 0:
            logger.info(
                f"🔍 DEBUG: Calling stakeholder.policy_step() at timestep {self.current_timestep}"
            )
            await self.stakeholder_agent.policy_step(self.current_timestep)
            logger.info(
                f"🔍 DEBUG: Stakeholder.policy_step() completed at timestep {self.current_timestep}"
            )
        else:
            logger.info(
                "🔍 DEBUG: Skipping stakeholder.policy_step() at timestep 0 (pre-execution messages handled)"
            )

        execution_time = (datetime.now() - start_time).total_seconds()

        # Capture stakeholder preference state for this timestep
        # NEW: Get serializable state from stakeholder via get_serializable_state() hook
        safe_stakeholder_pref_state = self.stakeholder_agent.get_serializable_state(
            self.current_timestep
        )

        # Add change event if present (for backwards compatibility with existing logs)
        if self.recent_preference_change is not None:
            safe_stakeholder_pref_state["change_event"] = (
                self.recent_preference_change.model_dump(mode="json")
            )

        # Build observation for outputs/callbacks
        # Note: this is a duplicicative secdondary observation, which is not used by the manager agent directly
        # TODO: move this around so we expose the last observation to the manager agent
        observation = await self.manager_agent.create_observation(
            workflow=self.workflow,
            execution_state=self.execution_state,
            current_timestep=self.current_timestep,
            running_tasks=self.running_tasks,
            completed_task_ids=self.completed_task_ids,
            failed_task_ids=self.failed_task_ids,
            communication_service=self.communication_service,
            stakeholder_profile=self.stakeholder_agent.public_profile,
        )

        # Calculate total simulated time from completed tasks in this timestep
        total_simulated_hours = 0.0
        for task_id in tasks_completed:
            task = self.workflow.tasks.get(task_id)
            if task and task.actual_duration_hours is not None:
                total_simulated_hours += task.actual_duration_hours

        result = create_timestep_result(
            timestep=timestep,
            manager_id="workflow_engine",
            tasks_started=tasks_started,
            tasks_completed=tasks_completed,
            tasks_failed=tasks_failed,
            execution_time=execution_time,
            completed_tasks_simulated_hours=total_simulated_hours,
            manager_action=manager_action,
            manager_observation=observation,
            workflow_snapshot={
                **self.workflow.model_dump(
                    mode="json", exclude={"agents", "success_criteria"}
                ),
                "agents": self.output_writer._serialize_agents_for_snapshot(),
                "success_criteria": [],
            },
            preference_change_event=self.recent_preference_change,
            agent_coordination_changes=agent_coordination_changes,
            stakeholder_preference_state=safe_stakeholder_pref_state,
            # operational efficiency metrics are computed by evaluators
        )

        # Fire end-of-timestep callbacks with full context, without blocking engine on failures
        if self._timestep_end_callbacks:
            ctx = TimestepEndContext(
                timestep=timestep,
                execution_state=self.execution_state,
                workflow=self.workflow,
                manager_observation=observation,
                manager_action=manager_action,
                tasks_started=tasks_started,
                tasks_completed=tasks_completed,
                tasks_failed=tasks_failed,
                running_task_ids=list(self.running_tasks.keys()),
                completed_task_ids=list(self.completed_task_ids),
                failed_task_ids=list(self.failed_task_ids),
                preference_change_event=self.recent_preference_change,
                agent_coordination_changes=agent_coordination_changes,
                execution_time_seconds=execution_time,
                execution_result=result,
            )
            for cb in self._timestep_end_callbacks:
                try:
                    await cb(ctx)
                except Exception:
                    logger.error(
                        f"timestep_end callback failed: {traceback.format_exc()}"
                    )

        self.current_timestep += 1
        return result

    def _inject_communication_service(self) -> None:
        """Inject communication service into all agents in the workflow."""
        for agent in self.workflow.agents.values():
            # Simple: just set the communication service reference
            # Agents are responsible for using it properly in their tools
            if isinstance(agent, AgentInterface):
                agent.communication_service = self.communication_service
                agent.configure_seed(self.seed)

    async def _execute_ready_tasks(self) -> tuple[list[UUID], list[UUID], list[UUID]]:
        """
        Execute all tasks that are ready to start.

        Returns:
            Tuple of (tasks_started, tasks_completed, tasks_failed)
        """
        tasks_started = []
        tasks_completed = []
        tasks_failed = []

        if self.running_tasks:
            done_tasks, pending_tasks = await asyncio.wait(
                self.running_tasks.values(),
                return_when=asyncio.ALL_COMPLETED,
                timeout=300,
            )

            for done_task in done_tasks:
                task_id = None
                for tid, atask in self.running_tasks.items():
                    if atask == done_task:
                        task_id = tid
                        break

                if task_id:
                    # Get the task to check if it's multi-agent
                    task_obj = self.workflow.tasks.get(task_id)

                    try:
                        # Check if this is a multi-agent task
                        if task_obj and task_obj.is_multi_agent_task():
                            # Handle multi-agent completion
                            await self._handle_multi_agent_completion(
                                task_obj, done_task
                            )
                            tasks_completed.append(task_id)
                        else:
                            # Standard single-agent completion
                            result = await done_task

                            # Get the single execution for this task
                            existing_task = self.workflow.tasks.get(task_id)
                            if existing_task and existing_task.execution_ids:
                                execution: TaskExecution = (
                                    self.workflow.task_executions[
                                        existing_task.execution_ids[0]
                                    ]
                                )

                                if result.success:
                                    tasks_completed.append(task_id)
                                    self.completed_task_ids.add(task_id)

                                    resource_ids = []
                                    new_resources = []
                                    for resource in result.output_resources:
                                        WorkflowMutations.add_resource(
                                            self.workflow, resource
                                        )
                                        resource_ids.append(resource.id)
                                        new_resources.append(resource)

                                    # Update execution
                                    execution.status = TaskStatus.COMPLETED
                                    execution.completed_at = result.completed_at
                                    execution.output_resource_ids = resource_ids
                                    execution.actual_duration_hours = (
                                        result.simulated_duration_hours
                                    )
                                    execution.actual_cost = result.actual_cost
                                    execution.execution_result = result

                                    # Update task
                                    completed_task = existing_task.model_copy(
                                        update={
                                            "status": TaskStatus.COMPLETED,
                                            "completed_at": result.completed_at,
                                            "actual_duration_hours": float(
                                                result.simulated_duration_hours
                                            ),
                                            "actual_cost": result.actual_cost,
                                            "output_resource_ids": existing_task.output_resource_ids
                                            + resource_ids,
                                        }
                                    )
                                    self.workflow.tasks[task_id] = completed_task
                                    # Synchronize embedded subtasks with updated registry to fix inconsistencies
                                    for sync_task in self.workflow.tasks.values():
                                        sync_task.sync_embedded_tasks_with_registry(
                                            self.workflow.tasks
                                        )
                                    self.workflow.total_simulated_hours += float(
                                        result.simulated_duration_hours
                                    )
                                    self.workflow.total_cost += float(
                                        result.actual_cost
                                    )

                                else:
                                    logger.warning(
                                        f"Completed task {task_id} no longer exists in workflow (possibly removed). Skipping state update."
                                    )

                            elif existing_task and existing_task.execution_ids:
                                # Handle failure
                                execution = self.workflow.task_executions[
                                    existing_task.execution_ids[0]
                                ]

                                tasks_failed.append(task_id)
                                self.failed_task_ids.add(task_id)

                                # Update execution
                                execution.status = TaskStatus.FAILED
                                execution.completed_at = (
                                    result.completed_at
                                    if hasattr(result, "completed_at")
                                    else datetime.now()
                                )
                                execution.error_message = (
                                    result.error_message
                                    if hasattr(result, "error_message")
                                    else "Unknown error"
                                )
                                execution.execution_result = result

                                # Update task
                                task = self.workflow.tasks.get(task_id)
                                if task is not None:
                                    task.status = TaskStatus.FAILED
                                    task.execution_notes.append(
                                        f"Failed: {result.error_message}"
                                    )
                                    # Synchronize embedded subtasks with updated registry to fix inconsistencies
                                    for sync_task in self.workflow.tasks.values():
                                        sync_task.sync_embedded_tasks_with_registry(
                                            self.workflow.tasks
                                        )
                                else:
                                    logger.warning(
                                        f"Failed task {task_id} no longer exists in workflow (possibly removed). Skipping state update."
                                    )

                    except Exception as e:
                        logger.error(
                            f"Task {task_id} failed with exception: {traceback.format_exc()}"
                        )
                        tasks_failed.append(task_id)
                        self.failed_task_ids.add(task_id)

                        # Update task status if task still exists
                        task = self.workflow.tasks.get(task_id)
                        if task is not None:
                            task.status = TaskStatus.FAILED
                            task.execution_notes.append(f"Exception: {str(e)}")
                        else:
                            logger.warning(
                                f"Exception for task {task_id}, but task no longer exists in workflow. Skipping state update."
                            )

                    del self.running_tasks[task_id]

        # Start new tasks that are ready
        ready_tasks = WorkflowQueries.get_ready_tasks(self.workflow)

        for task in ready_tasks:
            if (
                task.id not in self.running_tasks
                and task.id not in self.completed_task_ids
            ):
                # Mark when dependencies became ready (for coordination deadtime calculation)
                if task.deps_ready_at is None:
                    task.deps_ready_at = datetime.now()

                # Check if this is a multi-agent task
                if task.is_multi_agent_task():
                    # Handle multi-agent execution
                    await self._start_multi_agent_task(task)
                    tasks_started.append(task.id)
                else:
                    # Standard single-agent execution
                    # If no execution exists, create one
                    if not task.execution_ids:
                        # Create a single execution for this task
                        # Try to find an agent from agents dict or use a default
                        agent_id = None
                        for aid in self.workflow.agents.keys():
                            # Simple heuristic: use first available agent
                            agent_id = aid
                            break

                        if not agent_id:
                            logger.warning(
                                f"No agent available for single-agent task '{task.name}'"
                            )
                            continue

                        execution = TaskExecution(
                            task_id=task.id,
                            agent_id=agent_id,
                            status=TaskStatus.PENDING,
                        )
                        self.workflow.task_executions[execution.id] = execution
                        task.execution_ids.append(execution.id)

                    execution = self.workflow.task_executions[task.execution_ids[0]]
                    agent = self.workflow.agents.get(execution.agent_id)

                    if agent:
                        # Get task resources
                        resources = self._get_task_resources(task)

                        # Add task to agent's current workload
                        if task.id not in agent.current_task_ids:
                            agent.current_task_ids.append(task.id)

                        # Update execution status
                        execution.status = TaskStatus.RUNNING
                        execution.started_at = datetime.now()

                        # Start task execution
                        execution_task = asyncio.create_task(
                            agent.execute_task(task, resources)
                        )
                        self.running_tasks[task.id] = execution_task

                        # Update task status and timing
                        task.status = TaskStatus.RUNNING
                        task.started_at = datetime.now()

                        tasks_started.append(task.id)

        return tasks_started, tasks_completed, tasks_failed

    def _get_task_resources(self, task: Task) -> list[Resource]:
        """
        Get input resources for a task.

        Args:
            task: The task to get resources for

        Returns:
            List of available input resources
        """
        # Gather input resources
        input_resources = []
        for resource_id in task.input_resource_ids:
            if resource_id in self.workflow.resources:
                input_resources.append(self.workflow.resources[resource_id])
        return input_resources

    def _update_workflow_state(
        self, completed_tasks: list[UUID], failed_tasks: list[UUID]
    ) -> None:
        """
        Update workflow state after task completions.

        Args:
            completed_tasks: List of completed task IDs
            failed_tasks: List of failed task IDs
        """
        # Update agent states
        for agent in self.workflow.agents.values():
            # Count completed tasks BEFORE removing them
            completed_by_agent = [
                tid for tid in agent.current_task_ids if tid in completed_tasks
            ]
            agent.tasks_completed += len(completed_by_agent)

            # Remove completed/failed tasks from current task list
            agent.current_task_ids = [
                tid
                for tid in agent.current_task_ids
                if tid not in completed_tasks and tid not in failed_tasks
            ]

        # Update workflow timestamps
        if self.workflow.started_at is None and (completed_tasks or self.running_tasks):
            self.workflow.started_at = datetime.now()

        if (
            WorkflowQueries.is_complete(self.workflow)
            and self.workflow.completed_at is None
        ):
            self.workflow.completed_at = datetime.now()

        # Propagate completion to all composite tasks whose atomic subtasks are all completed (recursive)
        try:
            status_updated = False

            def _update_composite_completion(node: Task) -> None:
                nonlocal status_updated
                if not node.is_atomic_task():
                    atomic_children = node.get_atomic_subtasks()

                    def _is_leaf_completed(leaf: Task) -> bool:
                        current = self.workflow.tasks.get(leaf.id)
                        return (
                            current and current.status == TaskStatus.COMPLETED
                        ) or leaf.status == TaskStatus.COMPLETED

                    if atomic_children and all(
                        _is_leaf_completed(leaf) for leaf in atomic_children
                    ):
                        if node.status != TaskStatus.COMPLETED:
                            node.status = TaskStatus.COMPLETED
                            node.completed_at = datetime.now()
                            status_updated = True
                    # Recurse into children for nested composites
                    for child in node.subtasks:
                        _update_composite_completion(child)

            for top in self.workflow.tasks.values():
                _update_composite_completion(top)

            # Synchronize embedded subtasks if any status was updated to fix inconsistencies
            if status_updated:
                for task in self.workflow.tasks.values():
                    task.sync_embedded_tasks_with_registry(self.workflow.tasks)

            # Normalize composite task states: composites should never be READY/RUNNING
            for task in self.workflow.tasks.values():
                try:
                    if not task.is_atomic_task() and task.status in (
                        TaskStatus.READY,
                        TaskStatus.RUNNING,
                    ):
                        task.status = TaskStatus.PENDING
                except Exception:
                    continue

            # Update derived effective_status for all tasks (including embedded composites)
            def _leaf_statuses(node: Task) -> list[TaskStatus]:
                if node.is_atomic_task():
                    reg = self.workflow.tasks.get(node.id)
                    return [reg.status if reg is not None else node.status]
                statuses: list[TaskStatus] = []
                for leaf in node.get_atomic_subtasks():
                    reg = self.workflow.tasks.get(leaf.id)
                    statuses.append(reg.status if reg is not None else leaf.status)
                return statuses

            def _set_effective_status_recursive(node: Task) -> None:
                try:
                    if node.is_atomic_task():
                        node.effective_status = node.status.value
                    else:
                        leaves = _leaf_statuses(node)
                        if leaves and all(s == TaskStatus.COMPLETED for s in leaves):
                            node.effective_status = TaskStatus.COMPLETED.value
                        elif any(s == TaskStatus.RUNNING for s in leaves):
                            node.effective_status = TaskStatus.RUNNING.value
                        elif any(s == TaskStatus.READY for s in leaves):
                            node.effective_status = TaskStatus.READY.value
                        else:
                            node.effective_status = TaskStatus.PENDING.value
                    # Recurse into children so embedded composites get their own value
                    for child in node.subtasks:
                        _set_effective_status_recursive(child)
                except Exception:
                    node.effective_status = node.status.value

            for root in self.workflow.tasks.values():
                _set_effective_status_recursive(root)
        except Exception:
            # Non-fatal; composite completion is a quality-of-life enhancement
            logger.error("Composite completion propagation failed", exc_info=True)

    def _is_terminal_state(self) -> bool:
        """Check if execution is in a terminal state."""
        return self.execution_state in [
            ExecutionState.COMPLETED,
            ExecutionState.FAILED,
            ExecutionState.CANCELLED,
        ]

    async def _save_workflow_state(self, timestep_result: ExecutionResult) -> None:
        """
        Save workflow state to disk.

        Args:
            timestep_result: The timestep result to save
        """
        if not self.enable_timestep_logging:
            return

        timestep = timestep_result.metadata.get("timestep", 0)
        filepath = self.output_config.get_timestep_file_path(timestep)

        # Ensure parent directory exists (robust against parallel runs)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Delegate writing to OutputWriter
        try:
            # Get serializable state from stakeholder
            stakeholder_state = self.stakeholder_agent.get_serializable_state(timestep)

            self.output_writer.save_timestep(
                timestep_result=timestep_result,
                workflow=self.workflow,
                current_timestep=timestep,
                manager_agent=self.manager_agent,
                stakeholder_state=stakeholder_state,
            )
        except Exception:
            logger.error("output writer failed saving timestep", exc_info=True)

        metrics = {
            "execution_summary": {
                "total_timesteps": self.current_timestep,
                "total_tasks": len(self.workflow.tasks),
                "completed_tasks": len(self.completed_task_ids),
                "failed_tasks": len(self.failed_task_ids),
                "success_rate": len(self.completed_task_ids) / len(self.workflow.tasks)
                if self.workflow.tasks
                else 0.0,
                "execution_state": self.execution_state.value,
                "workflow_completed": WorkflowQueries.is_complete(self.workflow),
            },
            "timing": {
                "started_at": self.workflow.started_at.isoformat()
                if self.workflow.started_at
                else None,
                "completed_at": self.workflow.completed_at.isoformat()
                if self.workflow.completed_at
                else None,
                "total_execution_time_seconds": sum(
                    tr.execution_time_seconds for tr in self.timestep_results
                ),
            },
            "timestep_results": [
                tr.model_dump(mode="json") for tr in self.timestep_results
            ],
        }

        filepath = self.output_config.get_final_metrics_path()
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(metrics, f, indent=2, default=str)

    def serialise_workflow_states_and_metrics(self) -> None:
        """Write high-level execution logs (manager actions) into execution_logs directory."""
        try:
            briefs = self.manager_agent.get_action_buffer()
            converted: list[tuple[int, ActionResult | None]] = [
                (b.timestep, b) for b in briefs if b.timestep is not None
            ]
            self.output_writer.save_execution_logs(converted)

        except Exception:
            logger.error("output writer failed saving execution logs", exc_info=True)

        try:
            self.output_writer.save_evaluation_outputs(
                self.validation_engine.evaluation_results,
                reward_vector=self.validation_engine.reward_vector,
            )
        except Exception:
            logger.error(
                "output writer failed saving evaluation outputs", exc_info=True
            )
        try:
            self.output_writer.save_workflow_summary(
                workflow=self.workflow,
                completed_task_ids=self.completed_task_ids,
                failed_task_ids=self.failed_task_ids,
                current_timestep=self.current_timestep,
            )
        except Exception:
            logger.error("output writer failed saving workflow summary", exc_info=True)

    def get_current_workflow_state(self) -> Workflow:
        """
        Get a snapshot of the current workflow state for external evaluation.

        This enables decoupled evaluation where external evaluators can
        assess the current state without being tightly coupled to the engine.

        Returns:
            Current workflow state with all tasks, resources, and metadata
        """
        return self.workflow

    def get_current_execution_context(self) -> dict:
        """
        Get current execution context for evaluation.

        Returns execution metadata that evaluators might need.
        """
        return {
            "timestep": self.current_timestep,
            "execution_state": self.execution_state.value,
            "completed_task_ids": list(self.completed_task_ids),
            "failed_task_ids": list(self.failed_task_ids),
            "running_tasks": len(self.running_tasks),
        }

    def _check_and_apply_agent_changes(self) -> list[str]:
        """
        Check if agents should change and apply changes if needed.

        Returns:
            List of change descriptions for logging
        """
        changes: list[str] = []

        changes = self.agent_registry.apply_scheduled_changes_for_timestep(
            timestep=self.current_timestep,
            communication_service=self.communication_service,
            tool_factory=ToolFactory(),
        )

        # Mirror registry agents into workflow so observations/assignments can see them
        try:
            # 1) Add or update agents that exist in the registry
            current_registry_agents = {
                a.agent_id: a for a in self.agent_registry.list_agents()
            }
            for agent in current_registry_agents.values():
                WorkflowMutations.add_agent(self.workflow, agent)
            # Update mirrored set to current registry snapshot
            current_registry_ids = set(current_registry_agents.keys())

            # 2) Prune only previously mirrored agents that are no longer in the registry
            #    Keep the stakeholder agent which is owned by the engine/workflow
            stakeholder_id = self.stakeholder_agent.agent_id
            previously_mirrored = set(self._registry_mirrored_agent_ids)
            to_remove = [
                agent_id
                for agent_id in previously_mirrored
                if agent_id != stakeholder_id
                and agent_id not in current_registry_ids
                and agent_id in self.workflow.agents
            ]
            for agent_id in to_remove:
                try:
                    del self.workflow.agents[agent_id]
                except Exception:
                    # Defensive: continue even if an entry cannot be deleted
                    pass

            # 3) Commit mirrored set to current for next timestep
            self._registry_mirrored_agent_ids = current_registry_ids
        except Exception:
            logger.error(
                "failed to sync agent registry into workflow agents", exc_info=True
            )

        return changes

    async def _start_multi_agent_task(self, task: Task) -> None:
        """Start parallel execution by all assigned executions."""

        # Get all executions for this task
        executions = [
            self.workflow.task_executions[eid]
            for eid in task.execution_ids
            if eid in self.workflow.task_executions
        ]

        if not executions:
            logger.warning(f"No executions found for multi-agent task '{task.name}'")
            return

        resources = self._get_task_resources(task)

        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()

        logger.info(f"Starting {len(executions)} executions for task '{task.name}'")

        # DEBUG: Log available agents
        logger.info(
            f"🔍 DEBUG: Available agents in workflow.agents: {list(self.workflow.agents.keys())}"
        )
        logger.info(
            f"🔍 DEBUG: Required agents for executions: {[e.agent_id for e in executions]}"
        )

        # Create futures for all executions
        variant_futures = []
        for execution in executions:
            logger.info(
                f"🔍 DEBUG: Looking for agent '{execution.agent_id}' (execution {execution.id})"
            )
            agent = self.workflow.agents.get(execution.agent_id)
            if not agent:
                logger.error(
                    f"❌ DEBUG: Agent {execution.agent_id} NOT FOUND in workflow.agents!"
                )
                logger.error(
                    f"❌ DEBUG: Execution {execution.id} status: {execution.status}"
                )
                continue
            logger.info(f"✅ DEBUG: Found agent {execution.agent_id}")

            # Mark execution as running
            execution.status = TaskStatus.RUNNING
            execution.started_at = datetime.now()

            # Add task to agent's workload
            if task.id not in agent.current_task_ids:
                agent.current_task_ids.append(task.id)

            # Start execution
            future = asyncio.create_task(
                self._execute_single_variant(task, execution, agent, resources)
            )
            variant_futures.append(future)

        # Store as group (gather all)
        # asyncio.gather returns a Future which is compatible with Task for awaiting
        multi_future: asyncio.Task[Any] = asyncio.gather(
            *variant_futures, return_exceptions=True
        )  # type: ignore
        self.running_tasks[task.id] = multi_future

    async def _execute_single_variant(
        self,
        task: Task,
        execution: "TaskExecution",
        agent: "AgentInterface",
        resources: list[Resource],
    ) -> tuple[UUID, Any]:
        """Execute single variant and track result.

        Args:
            task: The task being executed
            execution: The TaskExecution object tracking this attempt
            agent: The agent performing the execution
            resources: Input resources for the task

        Returns:
            Tuple of (execution_id, result)
        """
        logger.info(
            f"🔍 DEBUG: Starting execution {execution.id} with agent {execution.agent_id}"
        )
        try:
            # Execute task
            result = await agent.execute_task(task, resources)

            logger.info(
                f"🔍 DEBUG: Execution {execution.id} returned result.success={result.success}"
            )

            # Update execution state
            execution.status = (
                TaskStatus.COMPLETED if result.success else TaskStatus.FAILED
            )
            execution.completed_at = datetime.now()
            execution.execution_result = result
            execution.output_resource_ids = [r.id for r in result.output_resources]
            execution.actual_duration_hours = result.simulated_duration_hours
            execution.actual_cost = result.actual_cost

            if not result.success:
                execution.error_message = result.error_message
                logger.warning(
                    f"🔍 DEBUG: Execution {execution.id} failed with error: {result.error_message}"
                )

            # Add resources to workflow
            for resource in result.output_resources:
                WorkflowMutations.add_resource(self.workflow, resource)

            logger.info(
                f"Execution {execution.id} (agent {execution.agent_id}) completed for '{task.name}' with status={execution.status}"
            )
            return execution.id, result

        except Exception as e:
            logger.error(
                f"❌ DEBUG: Exception in _execute_single_variant for execution {execution.id}: {type(e).__name__}: {e}",
                exc_info=True,
            )

            execution.status = TaskStatus.FAILED
            execution.completed_at = datetime.now()
            execution.error_message = str(e)

            raise

    async def _handle_multi_agent_completion(
        self, task: Task, future: asyncio.Future
    ) -> None:
        """Handle completion of multi-agent task."""

        # Wait for all execution results
        await future  # List of (execution_id, result) or exceptions

        # Get all executions for this task
        executions = [
            self.workflow.task_executions[eid]
            for eid in task.execution_ids
            if eid in self.workflow.task_executions
        ]

        # DEBUG: Log execution statuses in detail
        logger.info(f"🔍 DEBUG: Checking execution statuses for task '{task.name}':")
        for e in executions:
            logger.info(
                f"  - Execution {e.id} (agent {e.agent_id}): status={e.status}, error={e.error_message}"
            )

        # Count successes and failures
        successful_executions = [
            e for e in executions if e.status == TaskStatus.COMPLETED
        ]
        failed_executions = [e for e in executions if e.status == TaskStatus.FAILED]
        pending_executions = [e for e in executions if e.status == TaskStatus.PENDING]

        logger.info(
            f"All executions finished for '{task.name}': "
            f"{len(successful_executions)} succeeded, {len(failed_executions)} failed, {len(pending_executions)} still pending"
        )

        # If all executions failed, mark task as failed
        if not successful_executions:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            self.failed_task_ids.add(task.id)
            logger.error(
                f"Multi-agent task '{task.name}' FAILED: all {len(failed_executions)} executions failed"
            )
            return

        # At least one execution succeeded - evaluate and rank
        # OPTIMIZATION: Skip if gold_rubrics will evaluate at timestep end (avoids double evaluation)
        if task.completion_evaluators and not self.gold_rubrics:
            await self._evaluate_and_rank_executions(task, successful_executions)

        else:
            # No evaluators OR gold_rubrics will handle it: propagate all outputs without ranking
            if self.gold_rubrics:
                logger.info(
                    "Skipping task completion evaluation (gold_rubrics will evaluate at timestep end)"
                )
            task.output_resource_ids = [
                rid for ex in successful_executions for rid in ex.output_resource_ids
            ]

        # Mark task complete
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()
        self.completed_task_ids.add(task.id)

        logger.info(
            f"Multi-agent task '{task.name}' COMPLETED. "
            f"{len(successful_executions)}/{len(executions)} executions succeeded. "
            f"Propagating {len(task.output_resource_ids)} resources"
        )

    async def _evaluate_and_rank_executions(
        self, task: Task, executions: list["TaskExecution"]
    ) -> None:
        """Evaluate and rank TaskExecutions by their resource bundles.

        Each execution's full resource bundle is evaluated as a unit.

        Supports three evaluator types:
        - StagedRubric: New staged evaluation system with gates
        - Rubric: Legacy flat rubric system
        - Callable: Custom evaluation functions

        Args:
            task: The task being evaluated
            executions: List of successful TaskExecution objects to evaluate
        """
        import inspect

        if not task.completion_evaluators or not executions:
            return

        logger.info(f"Evaluating {len(executions)} executions for task '{task.name}'")

        # Get communications and manager actions for context (needed for staged rubrics)
        communications_sender = (
            self.communication_service.get_messages_grouped_by_sender(
                sort_within_group="time",
                include_broadcasts=True,
            )
            if self.communication_service
            else None
        )
        comms_by_sender: list[SenderMessagesView] = cast(
            list[SenderMessagesView], communications_sender or []
        )
        manager_actions = self.manager_agent.get_action_buffer()

        # Evaluate each execution IN PARALLEL
        async def evaluate_single_execution(execution):
            # Get execution's resource bundle
            resources = [
                self.workflow.resources[rid]
                for rid in execution.output_resource_ids
                if rid in self.workflow.resources
            ]

            if not resources:
                logger.warning(f"No resources found for execution {execution.id}")
                return execution.id, {}, {}

            evaluation_scores: dict[str, float] = {}
            evaluation_details: dict[str, Any] = {}

            # Run each evaluator on the full resource bundle
            for evaluator in task.completion_evaluators:
                try:
                    # === Handle StagedRubric objects (NEW) ===
                    if isinstance(evaluator, StagedRubric):
                        # Evaluate THIS execution with the staged rubric
                        rubric_results = await self.validation_engine.evaluate_execution_with_staged_rubrics(
                            workflow=self.workflow,
                            execution=execution,
                            timestep=self.current_timestep,
                            staged_rubrics=[evaluator],
                            communications=comms_by_sender,
                            manager_actions=manager_actions,
                        )

                        # Extract results for each rubric category
                        for category_name, result in rubric_results.items():
                            evaluator_name = category_name
                            evaluation_scores[evaluator_name] = result.normalized_score
                            evaluation_details[evaluator_name] = {
                                "score": result.normalized_score,
                                "max_score": result.max_score,
                                "total_score": result.total_score,
                                "stages_evaluated": result.stages_evaluated,
                                "stages_passed": result.stages_passed,
                                "failed_gate": result.failed_gate,
                                "stopped_at": result.stopped_at,
                                "stage_results": result.stage_results,  # Already list[dict[str, Any]]
                            }

                            logger.info(
                                f"Staged rubric '{evaluator_name}' evaluated: "
                                f"{result.normalized_score:.2%} "
                                f"({result.stages_passed}/{result.stages_evaluated} stages passed)"
                            )

                    # === Handle Rubric objects (legacy) ===
                    elif isinstance(evaluator, Rubric):
                        from manager_agent_gym.core.evaluation.schemas.success_criteria import (
                            ValidationContext,
                        )

                        # Create context for these specific resources
                        context = ValidationContext(
                            workflow=self.workflow,
                            timestep=0,  # Task completion context
                        )
                        context.set_evaluable_resources(resources)

                        # Use existing ValidationEngine to evaluate each criterion
                        criterion_results: dict[str, dict[str, float | str]] = {}
                        for criterion in evaluator.criteria:
                            (
                                score_result,
                                _,
                                _,
                            ) = await self.validation_engine._evaluate_single_rubric(
                                workflow=self.workflow,
                                rubric_criteria=criterion,
                                context=context,
                            )
                            criterion_results[criterion.name] = {
                                "score": score_result.score,
                                "reasoning": score_result.reasoning,
                                "max_score": float(criterion.max_score),
                            }

                        # Aggregate using rubric's weighted average
                        total_weighted = sum(
                            float(r["score"]) * float(r["max_score"])  # type: ignore[arg-type]
                            for r in criterion_results.values()
                        )
                        total_weight = sum(
                            float(r["max_score"])  # type: ignore[arg-type]
                            for r in criterion_results.values()
                        )
                        aggregate_score = (
                            total_weighted / total_weight if total_weight > 0 else 0.0
                        )

                        evaluator_name = evaluator.name
                        evaluation_scores[evaluator_name] = aggregate_score
                        evaluation_details[evaluator_name] = {
                            "score": aggregate_score,
                            "criteria": criterion_results,
                        }

                        logger.info(
                            f"Rubric '{evaluator_name}' evaluated: {aggregate_score:.2f} "
                            f"({len(criterion_results)} criteria)"
                        )

                    # === Handle callable functions ===
                    else:
                        # Call the scorer function with the resource bundle
                        result = evaluator(resources, task, self.workflow)

                        # Handle async callables
                        if inspect.iscoroutine(result):
                            result = await result

                        # Normalize result to TaskExecutionEvaluationResult
                        if isinstance(result, (int, float)):
                            score = float(result)
                            metadata: dict[str, Any] = {}
                        elif isinstance(result, tuple) and len(result) == 2:
                            score, metadata = result
                        elif isinstance(result, TaskExecutionEvaluationResult):
                            score = result.score
                            metadata = result.evaluation_metadata
                        else:
                            logger.warning(
                                f"Unexpected scorer result type: {type(result)}"
                            )
                            score = 0.0
                            metadata = {}

                        evaluator_name = getattr(evaluator, "__name__", str(evaluator))
                        evaluation_scores[evaluator_name] = score
                        evaluation_details[evaluator_name] = {
                            "score": score,
                            **metadata,
                        }

                except Exception as e:
                    logger.error(f"Evaluator failed: {e}", exc_info=True)
                    # Extract evaluator name (StagedRubric uses category_name, others use name)
                    evaluator_name = getattr(
                        evaluator,
                        "category_name",
                        getattr(
                            evaluator,
                            "name",
                            getattr(evaluator, "__name__", str(evaluator)),
                        ),
                    )
                    evaluation_scores[evaluator_name] = 0.0
                    evaluation_details[evaluator_name] = {"error": str(e)}

            # Return evaluation results
            return execution.id, evaluation_scores, evaluation_details

        # Run all evaluations in PARALLEL
        logger.info(f"Evaluating {len(executions)} executions for task '{task.name}'")
        eval_results = await asyncio.gather(
            *[evaluate_single_execution(exec) for exec in executions]
        )

        # Store evaluation results in executions
        for exec_id, evaluation_scores, evaluation_details in eval_results:
            execution = next(e for e in executions if e.id == exec_id)
            execution.evaluation_scores = evaluation_scores
            execution.evaluation_details = evaluation_details
            execution.aggregate_score = (
                sum(evaluation_scores.values()) / len(evaluation_scores)
                if evaluation_scores
                else 0.0
            )

        # Rank executions by aggregate score
        ranked = sorted(
            executions, key=lambda e: e.aggregate_score or 0.0, reverse=True
        )
        for idx, execution in enumerate(ranked):
            execution.rank = idx + 1

        # Apply output selection strategy
        output_selection = task.__dict__.get("metadata", {}).get(
            "output_selection", "all"
        )
        k_outputs = task.__dict__.get("metadata", {}).get("k_outputs")

        if output_selection == "best":
            selected = ranked[:1]
        elif output_selection == "top_k" and k_outputs:
            selected = ranked[:k_outputs]
        else:  # "all"
            selected = ranked

        # Propagate selected resources to task
        task.output_resource_ids = [
            rid for ex in selected for rid in ex.output_resource_ids
        ]

        logger.info(
            f"Ranked {len(ranked)} executions. "
            f"Selected {len(selected)} (output_selection={output_selection}). "
            f"Best score: {ranked[0].aggregate_score:.3f}"
            if ranked
            else "No executions to rank"
        )

    async def evaluate_with_staged_rubrics(
        self,
        timestep: int,
        staged_rubrics: list["StagedRubric"],
    ) -> dict[str, "StagedRubricResult"]:
        """Evaluate workflow using staged rubrics (NEW evaluation path).

        This method evaluates the workflow using the new staged rubric system,
        which supports sequential evaluation with gates and failure actions.

        Args:
            timestep: Current timestep
            staged_rubrics: List of staged rubrics to evaluate

        Returns:
            Dict mapping rubric category_name to evaluation result

        Example:
            >>> gold_rubric = convert_staged_rubric_to_executable(gdpeval_spec)
            >>> results = await engine.evaluate_with_staged_rubrics(
            ...     timestep=engine.current_timestep,
            ...     staged_rubrics=[gold_rubric],
            ... )
            >>> print(f"Score: {results['Quality'].total_score}/{results['Quality'].max_score}")
        """

        # Get communications and manager actions for context
        communications_sender = (
            self.communication_service.get_messages_grouped_by_sender(
                sort_within_group="time",
                include_broadcasts=True,
            )
            if self.communication_service
            else []
        )
        comms_by_sender: list[SenderMessagesView] = cast(
            list[SenderMessagesView], communications_sender
        )
        manager_actions = self.manager_agent.get_action_buffer()

        # Evaluate using staged rubrics
        results = await self.validation_engine.evaluate_timestep_staged(
            workflow=self.workflow,
            timestep=timestep,
            staged_rubrics=staged_rubrics,
            communications=comms_by_sender,
            manager_actions=manager_actions,
        )

        # Store results in workflow for reward calculation
        for category_name, result in results.items():
            # Update task executions with evaluation results
            for task in self.workflow.tasks.values():
                for execution in task.get_executions(self.workflow):
                    if execution.is_completed():
                        # Store normalized score (0-1) as aggregate_score for compatibility
                        execution.aggregate_score = (
                            result.normalized_score * 10
                        )  # Scale to 0-10
                        execution.evaluation_details = {
                            "category": category_name,
                            "total_score": result.total_score,
                            "max_score": result.max_score,
                            "normalized_score": result.normalized_score,
                            "stages_passed": result.stages_passed,
                            "stages_evaluated": result.stages_evaluated,
                            "failed_gate": result.failed_gate,
                            "stopped_at": result.stopped_at,
                            "stage_results": result.stage_results,
                        }

        logger.info(f"Staged evaluation complete: {len(results)} categories evaluated")

        return results
