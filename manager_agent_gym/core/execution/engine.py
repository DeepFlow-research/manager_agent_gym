"""
Workflow execution engine for discrete timestep-based simulation.

Manages the core execution loop with discrete timesteps where the manager
agent can observe state and take actions between task executions.
"""

import asyncio
import json
import traceback
from datetime import datetime
from typing import cast
from typing import Awaitable, Callable, Sequence
from uuid import UUID

from ...schemas.core.communication import SenderMessagesView
from ...schemas.core.communication import Message, MessageType
from .state_restorer import WorkflowStateRestorer

from ..common.logging import logger
from asyncio import TaskGroup
from ..workflow_agents.interface import StakeholderBase
from ...schemas.config import OutputConfig
from .output_writer import WorkflowSerialiser
from ...schemas.core.base import TaskStatus
from ...schemas.core.resources import Resource
from ...schemas.core.tasks import Task
from ...schemas.core.workflow import Workflow
from ...schemas.execution.state import ExecutionState

from ...schemas.execution.callbacks import TimestepEndContext
from ...schemas.unified_results import ExecutionResult, create_timestep_result
from ..workflow_agents.registry import AgentRegistry
from ..manager_agent.interface import ManagerAgent
from ..workflow_agents.interface import AgentInterface
from ..workflow_agents.tool_factory import ToolFactory
from ...schemas.preferences.preference import (
    PreferenceWeights,
    PreferenceChange,
    Preference,
)
from ...schemas.preferences.rubric import RunCondition

# from ...schemas.evaluation.workflow_quality import CoordinationDeadtimeMetrics
from ..communication.service import CommunicationService
from ..evaluation.validation_engine import ValidationEngine
from ...schemas.preferences.evaluator import Evaluator
from ...schemas.evaluation.reward import BaseRewardAggregator, RewardProjection
from ...schemas.execution.manager_actions import ActionResult


class WorkflowExecutionEngine:
    """
    Core execution engine for workflow simulation.

    Manages discrete timesteps where tasks execute asynchronously but
    the manager agent can observe and act between timesteps.
    """

    def __init__(
        self,
        workflow: Workflow,
        agent_registry: AgentRegistry,
        stakeholder_agent: StakeholderBase,
        manager_agent: ManagerAgent,
        seed: int,
        evaluations: list[Evaluator] | None = None,
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
    ):
        self.workflow = workflow
        self.agent_registry = agent_registry
        self.evaluations = list(evaluations or [])
        self.manager_agent = manager_agent
        self.stakeholder_agent: StakeholderBase = stakeholder_agent
        self.workflow.add_agent(stakeholder_agent)
        # Global run seed (for deterministic behavior where supported)
        self.seed: int = seed

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
            max_concurrent_rubrics=max_concurrent_rubrics,
            log_preference_progress=log_preference_evaluation_progress,
            reward_aggregator=reward_aggregator,
            reward_projection=reward_projection,
            seed=self.seed,
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

        self.preference_history: list[tuple[int, PreferenceWeights]] = []
        self.recent_preference_change: PreferenceChange | None = None
        self.preference_change_total_count: int = 0

        # Ensure output directories exist (only if logging is enabled)
        if self.enable_timestep_logging or self.enable_final_metrics_logging:
            self.output_writer.ensure_directories()

        # Evaluation cadence configuration (default: BOTH) using rubric enum
        self.evaluation_cadence: RunCondition = RunCondition.ON_COMPLETION

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

        print(f"🔄 Restoring workflow state from timestep {timestep}")

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
                task.assigned_agent_id = task_data.get("assigned_agent_id")
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

    def _restore_stakeholder_preferences(self, prefs_data: dict) -> None:
        """Update stakeholder agent preferences to match snapshot."""
        self.stakeholder_agent.apply_preference_change(
            timestep=self.current_timestep,
            new_weights=PreferenceWeights(
                preferences=[
                    Preference(name=key, weight=value)
                    for key, value in prefs_data["weights"].items()
                ]
            ),
            change_event=None,
        )

    def _restore_communication_history(self, messages: list) -> None:
        """Restore communication message history from snapshot."""
        for msg_data in messages:
            message = Message(
                message_id=UUID(msg_data["message_id"]),
                sender_id=msg_data["sender_id"],
                receiver_id=msg_data.get("receiver_id"),
                recipients=msg_data.get("recipients", []),
                content=msg_data["content"],
                message_type=MessageType(msg_data["message_type"]),
                timestamp=datetime.fromisoformat(msg_data["timestamp"]),
                thread_id=UUID(msg_data["thread_id"])
                if msg_data.get("thread_id")
                else None,
                parent_message_id=UUID(msg_data["parent_message_id"])
                if msg_data.get("parent_message_id")
                else None,
                related_task_id=UUID(msg_data["related_task_id"])
                if msg_data.get("related_task_id")
                else None,
                priority=msg_data.get("priority", 1),
                read_by={
                    agent_id: datetime.fromisoformat(read_time)
                    for agent_id, read_time in msg_data.get("read_by", {}).items()
                },
                metadata=msg_data.get("metadata", {}),
            )

            # Add message to communication service
            self.communication_service.graph.add_message(message)

    def _get_preferences_from_stakeholder_agent(
        self, timestep: int
    ) -> PreferenceWeights:
        """Resolve stakeholder-owned preferences for the given timestep."""

        return self.stakeholder_agent.get_preferences_for_timestep(timestep)

    async def run_full_execution(
        self, save_outputs: bool = True
    ) -> list[ExecutionResult]:
        """
        Run the complete workflow execution until completion or failure.

        Returns:
            List of timestep results from the execution
        """
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
                if self.workflow.is_complete():
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
                and not self.workflow.is_complete()
            ):
                self.execution_state = ExecutionState.FAILED

        # Exiting TaskGroup ensures all scheduled validations completed
        self._task_group = None

        # Run final evaluation set
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
        await self.validation_engine.evaluate_timestep(
            workflow=self.workflow,
            timestep=self.current_timestep,
            preferences=self._get_preferences_from_stakeholder_agent(
                self.current_timestep
            ),
            workflow_evaluators=self.evaluations,
            cadence=RunCondition.ON_COMPLETION,
            communications=comms_by_sender,
            manager_actions=manager_actions,
        )

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

        manager_action = None
        if self.manager_agent:
            self.execution_state = ExecutionState.WAITING_FOR_MANAGER
            # Unified RL-style step: agent constructs observation internally
            done_flag = self._is_terminal_state() or self.workflow.is_complete()
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
                    self.workflow, self.communication_service
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

        # Coordination deadtime metrics moved to operational efficiency evaluator

        # Evaluate preferences for this timestep if configured
        did_eval_this_step = False
        if self.evaluation_cadence in (
            RunCondition.EACH_TIMESTEP,
            RunCondition.BOTH,
        ):
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
            await self.validation_engine.evaluate_timestep(
                workflow=self.workflow,
                timestep=self.current_timestep,
                preferences=self._get_preferences_from_stakeholder_agent(
                    self.current_timestep
                ),
                workflow_evaluators=self.evaluations,
                cadence=RunCondition.EACH_TIMESTEP,
                communications=comms_by_sender,
                manager_actions=manager_actions,
            )
            did_eval_this_step = True

        # If cadence is not EACH_TIMESTEP/BOTH, still evaluate on selected timesteps only
        elif (
            self.validation_engine.selected_timesteps
            and self.current_timestep in self.validation_engine.selected_timesteps
        ):
            communications_sender = (
                self.communication_service.get_messages_grouped_by_sender(
                    sort_within_group="time",
                    include_broadcasts=True,
                )
            )
            comms_by_sender = cast(list[SenderMessagesView], communications_sender)
            manager_actions = self.manager_agent.get_action_buffer()
            await self.validation_engine.evaluate_timestep(
                workflow=self.workflow,
                timestep=self.current_timestep,
                preferences=self._get_preferences_from_stakeholder_agent(
                    self.current_timestep
                ),
                workflow_evaluators=self.evaluations,
                cadence=RunCondition.EACH_TIMESTEP,
                communications=comms_by_sender,
                manager_actions=manager_actions,
            )
            did_eval_this_step = True
        # Ensure reward vector has an entry for this timestep even if no evals were run
        if not did_eval_this_step:
            rv = self.validation_engine.reward_vector
            if len(rv) <= self.current_timestep:
                rv.extend([0.0] * (self.current_timestep + 1 - len(rv)))

        # Run stakeholder policy step
        await self.stakeholder_agent.policy_step(self.current_timestep)

        execution_time = (datetime.now() - start_time).total_seconds()

        # Capture stakeholder preference state for this timestep
        # Serialize a safe snapshot that avoids dumping callable fields inside evaluators
        current_weights = self._get_preferences_from_stakeholder_agent(
            self.current_timestep
        )
        safe_stakeholder_pref_state = {
            "timestep": self.current_timestep,
            "weights": current_weights.get_preference_dict(),
            "preference_names": current_weights.get_preference_names(),
            "change_event": (
                self.recent_preference_change.model_dump(mode="json")
                if self.recent_preference_change is not None
                else None
            ),
        }

        # Build observation for outputs/callbacks
        # Note: this is a duplicicative secdondary observation, which is not used by the manager agent directly
        # TODO: move this around so we expose the last observ
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
                    try:
                        result = await done_task
                        if result.success:
                            tasks_completed.append(task_id)
                            self.completed_task_ids.add(task_id)

                            resource_ids = []
                            new_resources = []
                            for resource in result.output_resources:
                                self.workflow.add_resource(resource)
                                resource_ids.append(resource.id)
                                new_resources.append(resource)

                            # Validation system removed; skip resource validations

                            existing_task = self.workflow.tasks.get(task_id)
                            if existing_task is not None:
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
                                self.workflow.total_cost += float(result.actual_cost)

                            else:
                                logger.warning(
                                    f"Completed task {task_id} no longer exists in workflow (possibly removed). Skipping state update."
                                )

                        else:
                            tasks_failed.append(task_id)
                            self.failed_task_ids.add(task_id)

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
        ready_tasks = self.workflow.get_ready_tasks()

        for task in ready_tasks:
            if (
                task.id not in self.running_tasks
                and task.id not in self.completed_task_ids
            ):
                # Mark when dependencies became ready (for coordination deadtime calculation)
                if task.deps_ready_at is None:
                    task.deps_ready_at = datetime.now()

                # Get assigned agent
                agent = None
                if task.assigned_agent_id:
                    agent = self.workflow.agents.get(task.assigned_agent_id)

                if agent:
                    # Get task resources
                    resources = self._get_task_resources(task)

                    # Start task execution
                    execution_task = asyncio.create_task(
                        agent.execute_task(task, resources)
                    )
                    self.running_tasks[task.id] = execution_task

                    # Update task status and timing
                    # READY -> RUNNING when the engine actually starts execution
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
            # Remove completed/failed tasks from current task list
            agent.current_task_ids = [
                tid
                for tid in agent.current_task_ids
                if tid not in completed_tasks and tid not in failed_tasks
            ]

            # Update performance metrics
            if any(tid in completed_tasks for tid in agent.current_task_ids):
                agent.tasks_completed += len(
                    [tid for tid in completed_tasks if tid in agent.current_task_ids]
                )

        # Update workflow timestamps
        if self.workflow.started_at is None and (completed_tasks or self.running_tasks):
            self.workflow.started_at = datetime.now()

        if self.workflow.is_complete() and self.workflow.completed_at is None:
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
        except Exception:
            # Non-fatal; composite completion is a quality-of-life enhancement
            pass

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
            self.output_writer.save_timestep(
                timestep_result=timestep_result,
                workflow=self.workflow,
                current_timestep=timestep,
                manager_agent=self.manager_agent,
                stakeholder_weights=self._get_preferences_from_stakeholder_agent(
                    timestep
                ),
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
                "workflow_completed": self.workflow.is_complete(),
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
            for agent in self.agent_registry.list_agents():
                self.workflow.add_agent(agent)
        except Exception:
            logger.error(
                "failed to sync agent registry into workflow agents", exc_info=True
            )

        return changes
