import datetime
from uuid import uuid4

from manager_agent_gym.schemas.core.workflow import Workflow
from manager_agent_gym.schemas.core.tasks import Task
from manager_agent_gym.schemas.core.base import TaskStatus


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

    w.add_task(t_done)
    w.add_task(t_blocked)
    w.add_task(t_not_atomic)

    ready = w.get_ready_tasks()
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

    w.add_task(parent)
    w.add_task(leaf2)

    # Not complete initially
    assert not w.is_complete()

    # Completing one atomic is not enough
    leaf1.status = TaskStatus.COMPLETED
    assert not w.is_complete()

    # Complete all atomic tasks
    leaf2.status = TaskStatus.COMPLETED
    assert w.is_complete()


def test_validate_task_graph_detects_cycle() -> None:
    w = Workflow(name="w", workflow_goal="d", owner_id=uuid4())
    a = Task(name="A", description="d")
    b = Task(name="B", description="d")
    # Create cycle A->B, B->A
    a.dependency_task_ids = [b.id]
    b.dependency_task_ids = [a.id]
    w.add_task(a)
    w.add_task(b)

    assert not w.validate_task_graph()

    # Break cycle
    b.dependency_task_ids = []
    assert w.validate_task_graph()


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

    w.add_task(phase)
    w.add_task(after_phase)

    # Validation should pass because composite dependencies are expanded to leaves
    assert w.validate_task_graph()

    # Initially nothing is completed, so AfterPhase is not ready
    ready = w.get_ready_tasks()
    assert after_phase not in ready

    # Complete only one leaf: still not ready
    leaf1.status = TaskStatus.COMPLETED
    ready = w.get_ready_tasks()
    assert after_phase not in ready

    # Complete both leaves: AfterPhase becomes ready
    leaf2.status = TaskStatus.COMPLETED
    ready = w.get_ready_tasks()
    assert any(t.name == "AfterPhase" for t in ready)


def test_task_deadtime_calculation() -> None:
    t = Task(name="T", description="d")
    # Missing timestamps => 0
    assert t.calculate_coordination_deadtime_seconds() == 0.0

    now = datetime.datetime.now()
    t.deps_ready_at = now
    t.started_at = now + datetime.timedelta(seconds=5)
    assert t.calculate_coordination_deadtime_seconds() == 5.0
