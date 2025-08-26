"""
Workflow data models for Manager Agent Gym.
"""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from pydantic import ConfigDict

from .base import TaskStatus
from .tasks import Task
from .resources import Resource

from .communication import Message
from ..preferences import Constraint
from ...core.common.logging import logger
from ...core.workflow_agents.interface import AgentInterface


class Workflow(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    """
    A complete workflow containing tasks, agents, and execution state.

    This represents the core environment for the Manager Agent POSG.
    """

    # Essential fields (previously from BaseEntity)
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., description="Human-readable name")
    workflow_goal: str = Field(
        ...,
        description="Detailed description of what the workflow attempts to achieve.",
    )
    owner_id: UUID = Field(..., description="ID of the workflow owner")

    # Core POSG state components
    tasks: dict[UUID, Task] = Field(
        default_factory=dict, description="Task graph nodes (G)"
    )
    resources: dict[UUID, Resource] = Field(
        default_factory=dict, description="Resource registry (R)"
    )
    agents: dict[str, AgentInterface] = Field(
        default_factory=dict, description="Available agents (W)"
    )
    messages: list[Message] = Field(
        default_factory=list, description="Communication history (C)"
    )

    # Workflow metadata
    constraints: list[Constraint] = Field(default_factory=list)

    # Execution tracking
    started_at: datetime | None = Field(default=None)
    # Optional run seed for reproducibility; engine sets this when provided
    seed: int = Field(default=42, description="Run-level seed for reproducibility")
    completed_at: datetime | None = Field(default=None)
    is_active: bool = Field(default=False)

    # Metrics for evaluation
    total_cost: float = Field(default=0.0)
    # Sum of all task-level simulated durations (hours), reported by agents
    total_simulated_hours: float = Field(
        default=0.0,
        description="Total simulated time across all completed tasks (hours)",
    )

    @property
    def workflow_id(self) -> UUID:
        """Alias for id field to maintain compatibility."""
        return self.id

    @property
    def total_budget(self) -> float:
        """Sum of estimated costs across all tasks and nested subtasks."""
        total = 0.0
        for task in self.tasks.values():
            # include top-level estimate
            if task.estimated_cost is not None:
                try:
                    total += float(task.estimated_cost)
                except Exception:
                    pass
            # include nested subtasks
            for subtask in task.get_all_subtasks_flat():
                if subtask.estimated_cost is not None:
                    total += float(subtask.estimated_cost)

        return total

    @property
    def total_expected_hours(self) -> float:
        """Sum of estimated duration hours across all tasks and nested subtasks."""
        total = 0.0
        for task in self.tasks.values():
            if task.estimated_duration_hours is not None:
                total += float(task.estimated_duration_hours)
            for subtask in task.get_all_subtasks_flat():
                if subtask.estimated_duration_hours is not None:
                    total += float(subtask.estimated_duration_hours)
        return total

    def add_task(self, task: Task) -> None:
        """Add a task to the workflow."""
        self.tasks[task.id] = task

    def add_resource(self, resource: Resource) -> None:
        """Add a resource to the workflow."""
        self.resources[resource.id] = resource

    def get_task_output_resources(self, task: Task) -> list[Resource]:
        """Return realized output resources for a given task by id lookup."""
        results: list[Resource] = []
        for rid in task.output_resource_ids:
            res = self.resources.get(rid)
            if isinstance(res, Resource):
                results.append(res)
        return results

    def get_all_resources(self) -> list[Resource]:
        """Return all resources currently registered in the workflow."""
        return list(self.resources.values())

    def add_agent(self, agent: AgentInterface) -> None:
        """Add an agent to the workflow."""
        self.agents[agent.agent_id] = agent

    def get_ready_tasks(self) -> list[Task]:
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
                    dep_task = self.find_task_by_id(dep_id)
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

            def _propagate_and_register(task: Task, inherited_deps: set[UUID]) -> None:
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
                    if task.id not in self.tasks:
                        self.tasks[task.id] = task

            for root in list(self.tasks.values()):
                _propagate_and_register(root, set())
        except Exception:
            logger.error(
                "When trying to add dependancies from a parent to its children, an error occurred",
                exc_info=True,
            )
            # Defensive: if any malformed structure, fallback to current registry only
            pass

        # 2) Compute readiness based on completed tasks
        completed_task_ids = {
            tid
            for tid, task in self.tasks.items()
            if task.status == TaskStatus.COMPLETED
        }

        ready = []
        for task in self.tasks.values():
            if (
                task.status in (TaskStatus.PENDING, TaskStatus.READY)
                and task.is_atomic_task()
                and task.is_ready_to_start(completed_task_ids)
            ):
                # Mark as READY to make the state explicit for observers
                task.status = TaskStatus.READY
                ready.append(task)
        return ready

    def get_available_agents(self) -> list[AgentInterface]:
        """Get agents that are currently available for task assignment."""
        return [agent for agent in self.agents.values() if agent.is_available]

    def find_task_by_id(self, task_id: UUID) -> Task | None:
        """Find a task by ID in the workflow."""
        if task_id in self.tasks:
            return self.tasks[task_id]

        # Search in task hierarchies (subtasks)
        for task in self.tasks.values():
            found = task.find_task_by_id(task_id)
            if found:
                return found
        return None

    def is_complete(self) -> bool:
        """Check if all atomic tasks in the workflow are completed."""
        atomic_tasks = [task for task in self.tasks.values() if task.is_atomic_task()]
        if not atomic_tasks:
            return False
        return all(task.status == TaskStatus.COMPLETED for task in atomic_tasks)

    def get_task_dependencies_graph(self) -> dict[UUID, list[UUID]]:
        """Get the task dependency graph as adjacency list."""
        return {
            task_id: task.dependency_task_ids for task_id, task in self.tasks.items()
        }

    def validate_task_graph(self) -> bool:
        """Validate that the task graph is executable.

        Checks:
        - No cycles in the effective atomic dependency graph
        - All referenced dependencies exist in the workflow
        - The effective atomic-task dependency graph has at least one start
          and is acyclic (i.e., the workflow is completable without deadlock)
        """
        # Build a registry of all tasks including nested subtasks, and a parent map
        all_tasks: dict[UUID, Task] = {}
        parent_of: dict[UUID, UUID] = {}

        def register_task_tree(task: Task) -> None:
            all_tasks[task.id] = task
            for child in task.subtasks:
                parent_of[child.id] = task.id
                register_task_tree(child)

        for root in self.tasks.values():
            register_task_tree(root)

        # Identify atomic (leaf) tasks
        leaf_tasks = [t for t in all_tasks.values() if t.is_atomic_task()]
        if not leaf_tasks:
            return False

        leaf_ids = {t.id for t in leaf_tasks}

        def expand_to_leaf_ids(dep_ids: set[UUID]) -> set[UUID]:
            expanded: set[UUID] = set()
            for dep_id in dep_ids:
                dep_task = all_tasks.get(dep_id)
                if dep_task is None:
                    # Unknown dependency
                    expanded.add(dep_id)
                    continue
                if dep_task.is_atomic_task():
                    expanded.add(dep_task.id)
                else:
                    for leaf in dep_task.get_atomic_subtasks():
                        expanded.add(leaf.id)
            return expanded

        # Compute effective dependencies for leaves (including ancestors), expanded to leaves
        effective_deps: dict[UUID, set[UUID]] = {}
        for leaf in leaf_tasks:
            agg: set[UUID] = set(leaf.dependency_task_ids)
            ancestor_id = parent_of.get(leaf.id)
            while ancestor_id is not None:
                ancestor = all_tasks.get(ancestor_id)
                if ancestor is None:
                    break
                agg.update(ancestor.dependency_task_ids)
                ancestor_id = parent_of.get(ancestor_id)
            expanded = expand_to_leaf_ids(agg)
            # Validate that all deps exist and are leaf IDs after expansion
            for dep_id in expanded:
                if dep_id not in all_tasks:
                    return False
                if dep_id not in leaf_ids:
                    return False
            # Avoid self-dependency
            expanded.discard(leaf.id)
            effective_deps[leaf.id] = expanded

        # Build atomic graph
        indegree: dict[UUID, int] = {t.id: 0 for t in leaf_tasks}
        successors: dict[UUID, list[UUID]] = {t.id: [] for t in leaf_tasks}

        for leaf_id, deps in effective_deps.items():
            for dep_id in deps:
                indegree[leaf_id] += 1
                successors[dep_id].append(leaf_id)

        # Kahn's algorithm to detect cycles / ensure at least one start node
        queue: list[UUID] = [lid for lid, deg in indegree.items() if deg == 0]
        if not queue:
            return False

        processed = 0
        while queue:
            nid = queue.pop()
            processed += 1
            for m in successors.get(nid, []):
                indegree[m] -= 1
                if indegree[m] == 0:
                    queue.append(m)

        if processed < len(leaf_tasks):
            return False

        return True

    def pretty_print(
        self, include_resources: bool = True, max_preview_chars: int = 300
    ) -> str:
        """Return a human-readable summary of the workflow, tasks, and selected resources."""
        lines: list[str] = []
        lines.append("-" * 70)
        lines.append(f"Workflow: {self.name} (ID: {self.id})")
        lines.append(f"Goal: {self.workflow_goal}")
        lines.append(
            f"Budget (est): ${self.total_budget:.2f} | Expected hours: {self.total_expected_hours:.2f}"
        )
        lines.append(f"Cost (actual): ${self.total_cost:.2f}")
        lines.append(
            f"Agents: {len(self.agents)} | Resources: {len(self.resources)} | Tasks: {len(self.tasks)}"
        )
        lines.append("-" * 70)
        lines.append("Tasks:")
        for t in self.tasks.values():
            lines.append(t.pretty_print(indent=1))
        if include_resources and self.resources:
            lines.append("\nResources:")
            for r in self.resources.values():
                try:
                    lines.append(r.pretty_print(max_preview_chars=max_preview_chars))
                except Exception:
                    lines.append(f"Resource: {r.name} (ID: {r.id})")
        return "\n".join(lines)
