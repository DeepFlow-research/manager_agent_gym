import datetime
from uuid import uuid4

from manager_agent_gym.schemas.domain.workflow import Workflow
from manager_agent_gym.schemas.domain.task import Task
from manager_agent_gym.schemas.domain.base import TaskStatus
from manager_agent_gym.core.workflow.services import WorkflowGraph
from manager_agent_gym.core.workflow.services import WorkflowQueries
from manager_agent_gym.core.workflow.services import WorkflowMutations


def test_get_ready_tasks_respects_dependencies() -> None:
    w = Workflow(
        name="w",
        workflow_goal="desc",
        owner_id=uuid4(),
    )

    t_done = Task(name="A", description="done")
    t_done.status = TaskStatus.COMPLETED

    t_blocked = Task(name="B", description="blocked", dependency_task_ids=[t_done.id])
    t_not_atomic = Task(name="C", description="composite")
    t_not_atomic.subtasks = [Task(name="C1", description="sub")]  # non-atomic

    WorkflowMutations.add_task(w, t_done)
    WorkflowMutations.add_task(w, t_blocked)
    WorkflowMutations.add_task(w, t_not_atomic)

    ready = WorkflowQueries.get_ready_tasks(w)
    assert t_blocked in ready
    assert all(t.is_atomic_task() for t in ready)
    assert t_not_atomic not in ready


def test_is_complete_only_when_all_atomic_done() -> None:
    w = Workflow(name="w", workflow_goal="d", owner_id=uuid4())
    # Composite with one atomic leaf
    parent = Task(name="Parent", description="d")
    leaf1 = Task(name="Leaf1", description="d")
    parent.add_subtask(leaf1)

    # Atomic standalone task
    leaf2 = Task(name="Leaf2", description="d")

    WorkflowMutations.add_task(w, parent)
    WorkflowMutations.add_task(w, leaf2)

    # Not complete initially
    assert not WorkflowQueries.is_complete(w)

    # Completing one atomic is not enough
    leaf1.status = TaskStatus.COMPLETED
    assert not WorkflowQueries.is_complete(w)

    # Complete all atomic tasks
    leaf2.status = TaskStatus.COMPLETED
    assert WorkflowQueries.is_complete(w)


def test_validate_task_graph_detects_cycle() -> None:
    w = Workflow(name="w", workflow_goal="d", owner_id=uuid4())
    a = Task(name="A", description="d")
    b = Task(name="B", description="d")
    # Create cycle A->B, B->A
    a.dependency_task_ids = [b.id]
    b.dependency_task_ids = [a.id]
    WorkflowMutations.add_task(w, a)
    WorkflowMutations.add_task(w, b)

    assert not WorkflowGraph.validate_task_graph(w)

    # Break cycle
    b.dependency_task_ids = []
    assert WorkflowGraph.validate_task_graph(w)


def test_composite_dependencies_are_expanded_to_leaves_for_validation_and_readiness() -> (
    None
):
    # Build a workflow where a composite parent is depended upon
    w = Workflow(name="w", workflow_goal="d", owner_id=uuid4())
    phase = Task(name="Phase", description="composite parent")
    leaf1 = Task(name="L1", description="leaf1")
    leaf2 = Task(name="L2", description="leaf2")
    phase.add_subtask(leaf1)
    phase.add_subtask(leaf2)

    after_phase = Task(name="AfterPhase", description="depends on phase")
    # Depend on the composite parent (Phase)
    after_phase.dependency_task_ids = [phase.id]

    WorkflowMutations.add_task(w, phase)
    WorkflowMutations.add_task(w, after_phase)

    # Validation should pass because composite dependencies are expanded to leaves
    assert WorkflowGraph.validate_task_graph(w)

    # Initially nothing is completed, so AfterPhase is not ready
    ready = WorkflowQueries.get_ready_tasks(w)
    assert after_phase not in ready

    # Complete only one leaf: still not ready
    leaf1.status = TaskStatus.COMPLETED
    ready = WorkflowQueries.get_ready_tasks(w)
    assert after_phase not in ready

    # Complete both leaves: AfterPhase becomes ready
    leaf2.status = TaskStatus.COMPLETED
    ready = WorkflowQueries.get_ready_tasks(w)
    assert any(t.name == "AfterPhase" for t in ready)


def test_task_deadtime_calculation() -> None:
    t = Task(name="T", description="d")
    # Missing timestamps => 0
    assert t.calculate_coordination_deadtime_seconds() == 0.0

    now = datetime.datetime.now()
    t.deps_ready_at = now
    t.started_at = now + datetime.timedelta(seconds=5)
    assert t.calculate_coordination_deadtime_seconds() == 5.0
