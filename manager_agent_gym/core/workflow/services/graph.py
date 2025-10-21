"""
Workflow graph operations - task dependency graph validation.
"""

from uuid import UUID
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from manager_agent_gym.schemas.domain.workflow import Workflow
    from manager_agent_gym.schemas.domain.task import Task


class WorkflowGraph:
    """Stateless graph service for task dependency operations."""

    @staticmethod
    def validate_task_graph(workflow: "Workflow") -> bool:
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

        def register_task_tree(task: "Task") -> None:
            all_tasks[task.id] = task
            for child in task.subtasks:
                parent_of[child.id] = task.id
                register_task_tree(child)

        for root in workflow.tasks.values():
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
