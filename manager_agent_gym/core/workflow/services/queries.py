"""
Workflow query operations - read-only access to workflow state.
"""

from uuid import UUID
from typing import TYPE_CHECKING

from manager_agent_gym.schemas.domain.base import TaskStatus
from manager_agent_gym.core.common.logging import logger

if TYPE_CHECKING:
    from manager_agent_gym.schemas.domain.workflow import Workflow
    from manager_agent_gym.schemas.domain.task import Task
    from manager_agent_gym.schemas.domain.resource import Resource
    from manager_agent_gym.core.agents.workflow_agents.common.interface import (
        AgentInterface,
    )


class WorkflowQueries:
    """Stateless query service for workflow read operations."""

    @staticmethod
    def find_task_by_id(workflow: "Workflow", task_id: UUID) -> "Task | None":
        """Find a task by ID in the workflow."""
        if task_id in workflow.tasks:
            return workflow.tasks[task_id]

        # Search in task hierarchies (subtasks)
        for task in workflow.tasks.values():
            found = task.find_task_by_id(task_id)
            if found:
                return found
        return None

    @staticmethod
    def get_task_output_resources(
        workflow: "Workflow", task: "Task"
    ) -> list["Resource"]:
        """Return realized output resources for a given task by id lookup."""
        from manager_agent_gym.schemas.domain.resource import Resource

        results: list[Resource] = []
        for rid in task.output_resource_ids:
            res = workflow.resources.get(rid)
            if isinstance(res, Resource):
                results.append(res)
        return results

    @staticmethod
    def get_all_resources(workflow: "Workflow") -> list["Resource"]:
        """Return all resources currently registered in the workflow."""
        return list(workflow.resources.values())

    @staticmethod
    def get_available_agents(workflow: "Workflow") -> list["AgentInterface"]:
        """Get agents that are currently available for task assignment."""
        return [agent for agent in workflow.agents.values() if agent.is_available]

    @staticmethod
    def is_complete(workflow: "Workflow") -> bool:
        """Check if all atomic tasks in the workflow are completed."""
        atomic_tasks = [
            task for task in workflow.tasks.values() if task.is_atomic_task()
        ]
        if not atomic_tasks:
            return False
        return all(task.status == TaskStatus.COMPLETED for task in atomic_tasks)

    @staticmethod
    def get_task_dependencies_graph(workflow: "Workflow") -> dict[UUID, list[UUID]]:
        """Get the task dependency graph as adjacency list."""
        return {
            task_id: task.dependency_task_ids
            for task_id, task in workflow.tasks.items()
        }

    @staticmethod
    def get_ready_tasks(workflow: "Workflow") -> list["Task"]:
        """Get atomic tasks that are ready to start (all dependencies satisfied).

        Recursively considers leaf subtasks and ensures they are registered as
        executable tasks so downstream systems can schedule and update them.
        """
        # 1) Propagate dependencies from composite parents down to all leaf subtasks,
        # then register any leaf subtasks into the top-level task registry so they
        # can be scheduled and updated consistently by the engine/manager actions.
        try:

            def _expand_to_leaf_dependencies(dep_ids: set[UUID]) -> set[UUID]:
                """Expand any composite task IDs in dep_ids into their atomic descendant IDs."""
                expanded: set[UUID] = set()
                for dep_id in dep_ids:
                    dep_task = WorkflowQueries.find_task_by_id(workflow, dep_id)
                    if dep_task is None:
                        # Keep unknown dependency to let validation catch it later
                        expanded.add(dep_id)
                        continue
                    if dep_task.is_atomic_task():
                        expanded.add(dep_task.id)
                    else:
                        for leaf in dep_task.get_atomic_subtasks():
                            expanded.add(leaf.id)
                return expanded

            def _propagate_and_register(
                task: "Task", inherited_deps: set[UUID]
            ) -> None:
                # Aggregate dependencies from ancestors including this node
                aggregated_raw: set[UUID] = set(inherited_deps)
                aggregated_raw.update(task.dependency_task_ids)
                # Expand any composite dependencies to their leaf IDs
                aggregated_expanded = _expand_to_leaf_dependencies(aggregated_raw)

                # If composite, push aggregated deps to children and recurse
                if not task.is_atomic_task():
                    for child in task.subtasks:
                        child_deps_raw = set(child.dependency_task_ids)
                        child_deps_expanded = _expand_to_leaf_dependencies(
                            child_deps_raw
                        )
                        merged = child_deps_expanded.union(aggregated_expanded)
                        child.dependency_task_ids = list(merged)
                        _propagate_and_register(child, aggregated_expanded)
                else:
                    # Atomic leaf: rewrite its deps to the expanded set (including its own)
                    own_expanded = _expand_to_leaf_dependencies(
                        set(task.dependency_task_ids)
                    )
                    effective = own_expanded.union(aggregated_expanded)
                    task.dependency_task_ids = list(effective)
                    # Ensure it is available at top level for scheduling
                    if task.id not in workflow.tasks:
                        workflow.tasks[task.id] = task

            for root in list(workflow.tasks.values()):
                _propagate_and_register(root, set())
        except Exception:
            logger.error(
                "When trying to add dependencies from a parent to its children, an error occurred",
                exc_info=True,
            )
            # Defensive: if any malformed structure, fallback to current registry only
            pass

        # 2) Compute readiness based on completed tasks
        completed_task_ids = {
            tid
            for tid, task in workflow.tasks.items()
            if task.status == TaskStatus.COMPLETED
        }

        ready = []
        for task in workflow.tasks.values():
            if (
                task.status in (TaskStatus.PENDING, TaskStatus.READY)
                and task.is_atomic_task()
                and task.is_ready_to_start(completed_task_ids)
            ):
                # Mark as READY to make the state explicit for observers
                task.status = TaskStatus.READY
                ready.append(task)
        return ready
