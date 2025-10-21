"""
Default end-of-timestep callbacks for logging and visibility.

These can be passed to the engine via the `timestep_end_callbacks` parameter.
"""

from __future__ import annotations


from manager_agent_gym.core.common.logging import logger
from manager_agent_gym.core.execution.schemas.callbacks import TimestepEndContext
from manager_agent_gym.schemas.domain.base import TaskStatus
from manager_agent_gym.core.workflow.services import WorkflowQueries


def _group_tasks_by_status(ctx: TimestepEndContext) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {s.value: [] for s in TaskStatus}
    for task in ctx.workflow.tasks.values():
        groups.setdefault(task.status.value, []).append(f"{task.name} ({task.id})")
    return groups


async def log_workflow_brief_summary(ctx: TimestepEndContext) -> None:
    """Log a concise workflow summary at end of timestep."""
    try:
        total = len(ctx.workflow.tasks)
        completed = len(
            [t for t in ctx.workflow.tasks.values() if t.status == TaskStatus.COMPLETED]
        )
        running = len(
            [t for t in ctx.workflow.tasks.values() if t.status == TaskStatus.RUNNING]
        )
        pending = len(
            [t for t in ctx.workflow.tasks.values() if t.status == TaskStatus.PENDING]
        )
        ready = len(
            [t for t in ctx.workflow.tasks.values() if t.status == TaskStatus.READY]
        )
        # Available agents snapshot
        available_agents = WorkflowQueries.get_available_agents(ctx.workflow)
        available_count = len(available_agents)
        progress = (completed / total) if total else 0.0
        logger.info(
            f"TS {ctx.timestep} | Exec={ctx.execution_state.value} | Tasks: total={total}, completed={completed}, running={running}, ready={ready}, pending={pending} | Agents available={available_count} | Progress={progress:.1%} | dt={ctx.execution_time_seconds:.2f}s"
        )
    except Exception:
        logger.error("log_workflow_brief_summary failed", exc_info=True)


async def log_tasks_grouped_by_status(ctx: TimestepEndContext) -> None:
    """Log an itemized list of tasks grouped by status."""
    try:
        groups = _group_tasks_by_status(ctx)
        parts: list[str] = [f"TS {ctx.timestep} | Tasks by status:"]
        for status_name, items in groups.items():
            if not items:
                continue
            parts.append(f"  - {status_name}: {len(items)}")
            # Limit verbosity to first 5 per status to keep logs readable
            for item in items[:5]:
                parts.append(f"      • {item}")
            if len(items) > 5:
                parts.append(f"      … and {len(items) - 5} more")
        logger.info("\n".join(parts))
    except Exception:
        logger.error("log_tasks_grouped_by_status failed", exc_info=True)


async def log_available_agents(ctx: TimestepEndContext) -> None:
    """Log which agents are currently available this timestep (preview)."""
    try:
        agents = WorkflowQueries.get_available_agents(ctx.workflow)
        count = len(agents)
        preview_items: list[str] = []
        for agent in agents[:5]:
            try:
                preview_items.append(f"{agent.agent_id}({agent.agent_type})")
            except Exception:
                # Best-effort: if agent lacks expected attributes, skip detailed preview
                preview_items.append("<agent>")
        suffix = "" if count <= 5 else f" (+{count - 5} more)"
        logger.info(
            f"TS {ctx.timestep} | Available agents: {count} | {', '.join(preview_items)}{suffix}"
        )
    except Exception:
        logger.error("log_available_agents failed", exc_info=True)


async def log_most_recent_manager_agent_action(ctx: TimestepEndContext) -> None:
    """Pretty-print manager action history for the past N timesteps (N=5)."""
    try:
        action = ctx.manager_action
        if action:
            logger.info(
                f"TS {ctx.timestep} | Manager action: {action.__class__.__name__}"
            )
            logger.info(f"  Reasoning: {action.reasoning}")
            logger.info(f"  Action: {action.model_dump(mode='json')}")
        else:
            logger.info(f"TS {ctx.timestep} | No manager action taken")
    except Exception:
        logger.error("log_recent_manager_actions failed", exc_info=True)


async def log_running_metric_calculations(ctx: TimestepEndContext) -> None:
    """Log currently pending/scheduled validation and metric calculations."""
    try:
        logger.info(
            f"TS {ctx.timestep} | Metrics: coordination_deadtime={ctx.execution_result.metadata.get('coordination_deadtime_seconds', 'n/a')}s"
        )
    except Exception:
        logger.error("log_running_metric_calculations failed", exc_info=True)


async def log_task_flow_transitions(ctx: TimestepEndContext) -> None:
    """Log per-timestep task movements and status deltas.

    Uses the manager's pre-step observation for the "before" snapshot and
    the end-of-step workflow state for the "after" snapshot.
    """
    try:
        # Before snapshot (from observation at start of step)
        before_counts = dict(ctx.manager_observation.task_status_counts or {})
        before_pending = int(before_counts.get(TaskStatus.PENDING.value, 0))
        before_ready = int(before_counts.get(TaskStatus.READY.value, 0))
        before_running = int(before_counts.get(TaskStatus.RUNNING.value, 0))
        before_completed = int(before_counts.get(TaskStatus.COMPLETED.value, 0))
        before_failed = int(before_counts.get(TaskStatus.FAILED.value, 0))

        ready_before = set(ctx.manager_observation.ready_task_ids or [])

        # After snapshot (end of step)
        after_pending = sum(
            1 for t in ctx.workflow.tasks.values() if t.status == TaskStatus.PENDING
        )
        after_ready = sum(
            1 for t in ctx.workflow.tasks.values() if t.status == TaskStatus.READY
        )
        after_running = sum(
            1 for t in ctx.workflow.tasks.values() if t.status == TaskStatus.RUNNING
        )
        after_completed = sum(
            1 for t in ctx.workflow.tasks.values() if t.status == TaskStatus.COMPLETED
        )
        after_failed = sum(
            1 for t in ctx.workflow.tasks.values() if t.status == TaskStatus.FAILED
        )

        ready_after = {
            t.id for t in ctx.workflow.tasks.values() if t.status == TaskStatus.READY
        }

        # Movements and deltas
        started = len(ctx.tasks_started)
        completed = len(ctx.tasks_completed)
        failed = len(ctx.tasks_failed)

        became_ready = len(ready_after - ready_before)
        left_ready = len(ready_before - ready_after)

        d_pending = after_pending - before_pending
        d_ready = after_ready - before_ready
        d_running = after_running - before_running
        d_completed = after_completed - before_completed
        d_failed = after_failed - before_failed

        logger.info(
            (
                f"TS {ctx.timestep} | Flow: started={started}, completed={completed}, failed={failed} | "
                f"became_ready={became_ready}, left_ready={left_ready} | "
                f"Δ pending={d_pending}, ready={d_ready}, running={d_running}, completed={d_completed}, failed={d_failed}"
            )
        )
    except Exception:
        logger.error("log_task_flow_transitions failed", exc_info=True)


def default_timestep_callbacks() -> list:
    """Convenience factory returning the default set of logging callbacks."""
    return [
        log_workflow_brief_summary,
        log_tasks_grouped_by_status,
        log_task_flow_transitions,
        log_available_agents,
        log_most_recent_manager_agent_action,
        # log_running_metric_calculations,  # optional, reduced noise by default
    ]


async def run_final_validations_with_progress(*_args, **_kwargs) -> None:  # legacy shim
    logger.info("Final validations disabled in simplified system")
