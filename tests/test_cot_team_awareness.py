"""Chain-of-thought manager: failed-action causes and running tasks in the prompt (awareness on only)."""

import asyncio
from uuid import uuid4

from manager_agent_gym.core.manager_agent.structured_manager import ChainOfThoughtManagerAgent
from manager_agent_gym.schemas.execution.manager import ManagerObservation, RunningTaskInfo
from manager_agent_gym.schemas.execution.manager_actions import ActionResult
from manager_agent_gym.schemas.preferences.preference import Preference, PreferenceWeights
from manager_agent_gym.schemas.workflow_agents.stakeholder import StakeholderPublicProfile


def manager(team_awareness):
    m = ChainOfThoughtManagerAgent(
        preferences=PreferenceWeights(preferences=[Preference(name="quality", weight=1.0)])
    )
    m.set_team_awareness(team_awareness)
    return m


def obs(timestep, running=()):
    return ManagerObservation(
        timestep=timestep,
        workflow_summary="",
        workflow_id=uuid4(),
        execution_state="running",
        task_status_counts={},
        ready_task_ids=[],
        running_task_ids=[],
        completed_task_ids=[],
        failed_task_ids=[],
        available_agent_metadata=[],
        recent_messages=[],
        workflow_progress=0.0,
        constraints=[],
        task_ids=[],
        resource_ids=[],
        agent_ids=[],
        running_task_info=list(running),
        stakeholder_profile=StakeholderPublicProfile(display_name="S", role="Owner"),
    )


def record(m, timestep, action_type, summary, success):
    m.record_action(ActionResult(action_type=action_type, summary=summary, kind="mutation",
                                 data={}, timestep=timestep, success=success))


def test_history_shows_flag_and_cause_only_for_failures():
    m = manager(True)
    record(m, 1, "assign_task", "Assigned T1 to a", True)
    record(m, 2, "assign_task", "Failed: agent zz is not on the roster", False)
    text = m._prepare_context(obs(3))
    assert "t=1: assign_task [SUCCESS] — Result: Assigned T1 to a" in text
    assert "t=2: assign_task [FAILED] — Cause: Failed: agent zz is not on the roster" in text
    assert "Cause" not in text.split("[SUCCESS]")[1].split("\n")[0]
    assert "do not repeat an action that failed for the same reason" in text


def test_history_without_failures_has_no_failure_instruction():
    m = manager(True)
    record(m, 1, "assign_task", "Assigned T1 to a", True)
    assert "FAILED" not in m._prepare_context(obs(2))


def test_history_format_is_unchanged_when_awareness_is_off():
    m = manager(False)
    record(m, 2, "assign_task", "Failed: x", False)
    text = m._prepare_context(obs(3))
    assert "t=2: assign_task — Result: Failed: x" in text and "[FAILED]" not in text


def _empty_workflow():
    from tests.helpers.stubs import make_empty_workflow
    return make_empty_workflow()


def running(n, name="Negotiation & Redlines", agent="redline_explainer", t=11):
    return RunningTaskInfo(task_id=uuid4(), name=name, agent_id=agent, started_timestep=t) if n == 1 else [
        RunningTaskInfo(task_id=uuid4(), name=f"Task {i}", agent_id="a", started_timestep=i) for i in range(n)
    ]


def test_running_tasks_block_shows_name_worker_and_start_timestep():
    text = manager(True)._prepare_context(obs(12, running=[running(1)]))
    assert "### Running Tasks" in text
    assert "- Negotiation & Redlines (id " in text
    assert "| worker redline_explainer | started t=11" in text


def test_running_tasks_block_is_capped_and_off_without_awareness():
    text = manager(True)._prepare_context(obs(12, running=running(13)))
    assert text.count("| worker a |") == 10 and "(+3 more running)" in text
    assert "### Running Tasks" not in manager(False)._prepare_context(obs(12, running=[running(1)]))
    assert "### Running Tasks" not in manager(True)._prepare_context(obs(12))


def test_observation_lists_running_tasks_with_worker_and_start_timestep_when_aware():
    from manager_agent_gym.schemas.core.base import TaskStatus
    from manager_agent_gym.schemas.core.tasks import Task

    for enabled in (True, False):
        m = manager(enabled)
        w = _empty_workflow()
        t = Task(name="Drafting", description="d", status=TaskStatus.RUNNING, assigned_agent_id="schedules_builder",
                 started_timestep=12)
        w.add_task(t)
        o = asyncio.run(m.create_observation(
            workflow=w, execution_state="running",
            stakeholder_profile=StakeholderPublicProfile(display_name="S", role="Owner"),
            current_timestep=13, running_tasks={t.id: None}, completed_task_ids=set(), failed_task_ids=set()))
        got = [(r.name, r.agent_id, r.started_timestep) for r in o.running_task_info]
        assert got == ([("Drafting", "schedules_builder", 12)] if enabled else [])
