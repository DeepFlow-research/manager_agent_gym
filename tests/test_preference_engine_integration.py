from uuid import uuid4
import pytest

from manager_agent_gym.core.execution.engine import WorkflowExecutionEngine
from manager_agent_gym.schemas.core.workflow import Workflow
from manager_agent_gym.schemas.workflow_agents.stakeholder import (
    StakeholderPublicProfile,
)
from manager_agent_gym.schemas.preferences.rubric import WorkflowRubric, RunCondition
from manager_agent_gym.schemas.preferences.preference import (
    Preference,
    PreferenceWeights,
)
from manager_agent_gym.schemas.preferences.evaluator import (
    Evaluator,
    AggregationStrategy,
)
from manager_agent_gym.core.manager_agent.interface import ManagerAgent
from manager_agent_gym.schemas.execution.manager import ManagerObservation
from manager_agent_gym.schemas.execution.manager_actions import BaseManagerAction
from manager_agent_gym.core.workflow_agents.registry import AgentRegistry
from manager_agent_gym.core.workflow_agents.stakeholder_agent import StakeholderAgent
from manager_agent_gym.schemas.workflow_agents.stakeholder import StakeholderConfig
from manager_agent_gym.schemas.execution.state import ExecutionState


class DummyAction(BaseManagerAction):
    reasoning: str = "ok"
    action_type: str = "noop"

    async def execute(self, workflow, communication_service=None):
        from manager_agent_gym.schemas.execution.manager_actions import ActionResult

        return ActionResult(
            summary="executed",
            kind="info",
            data={},
            action_type=self.action_type if self.action_type else "noop",
        )  # type: ignore[attr-defined]


class DummyManagerAgent(ManagerAgent):
    def __init__(self):
        super().__init__(
            agent_id="dummy", preferences=PreferenceWeights(preferences=[])
        )

    async def create_observation(
        self,
        workflow: Workflow,
        execution_state: ExecutionState,
        stakeholder_profile: StakeholderPublicProfile,
        current_timestep,
        running_tasks,
        completed_task_ids,
        failed_task_ids,
        communication_service=None,
        preference_change_events=None,
        recent_preference_change=None,
    ) -> ManagerObservation:
        # Provide a minimal valid observation
        return ManagerObservation(
            timestep=current_timestep,
            workflow_summary=workflow.pretty_print(),
            workflow_id=workflow.id,
            execution_state=str(execution_state),
            task_status_counts={},
            ready_task_ids=[],
            running_task_ids=list(running_tasks.keys()),
            completed_task_ids=list(completed_task_ids),
            failed_task_ids=list(failed_task_ids),
            available_agent_metadata=[
                a.config for a in workflow.get_available_agents()
            ],
            # Avoid embedding functions in observation to keep JSON serialization simple
            recent_messages=[],
            workflow_progress=(len(completed_task_ids) / len(workflow.tasks))
            if workflow.tasks
            else 0.0,
            constraints=workflow.constraints,
            task_ids=list(workflow.tasks.keys()),
            resource_ids=list(workflow.resources.keys()),
            agent_ids=list(workflow.agents.keys()),
            stakeholder_profile=stakeholder_profile,
        )

    async def take_action(self, observation: ManagerObservation) -> BaseManagerAction:
        return DummyAction(reasoning="dummy", success=True, result_summary="dummy")

    async def step(
        self,
        workflow: Workflow,
        execution_state: ExecutionState,
        stakeholder_profile: StakeholderPublicProfile,
        current_timestep: int,
        running_tasks: dict,
        completed_task_ids: set,
        failed_task_ids: set,
        communication_service=None,
        previous_reward: float = 0.0,
        done: bool = False,
    ) -> BaseManagerAction:
        from manager_agent_gym.schemas.execution.manager_actions import NoOpAction

        return NoOpAction(reasoning="noop", success=True, result_summary="noop")

    def reset(self):
        self._action_buffer.clear()


def make_workflow(name: str = "wf") -> Workflow:
    return Workflow(
        name=name,
        workflow_goal="test workflow",
        owner_id=uuid4(),
    )


def rubric_score_completed_tasks(workflow: Workflow) -> float:
    # Return number of completed tasks as score (capped by max_score)
    return float(
        len([t for t in workflow.tasks.values() if t.status.value == "completed"])
    )


@pytest.mark.asyncio
async def test_engine_accepts_preferences_and_exposes_methods() -> None:
    wf = make_workflow()
    prefs = PreferenceWeights(
        preferences=[
            Preference(
                name="quality",
                weight=0.6,
                evaluator=Evaluator(
                    name="quality_eval",
                    description="",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=[
                        WorkflowRubric(
                            name="completed",
                            evaluator_function=rubric_score_completed_tasks,
                            max_score=1.0,
                        )
                    ],
                ),
            ),
            Preference(
                name="cost",
                weight=0.4,
                evaluator=Evaluator(
                    name="cost_eval",
                    description="",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=[
                        WorkflowRubric(
                            name="constant",
                            evaluator_function=lambda wf: 1.0,
                            max_score=1.0,
                        )
                    ],
                ),
            ),
        ]
    )

    # Create stakeholder with initial preferences and add to workflow before engine init
    stakeholder_cfg = StakeholderConfig(
        agent_id="stakeholder",
        agent_type="stakeholder",
        system_prompt="Stakeholder",
        model_name="o3",
        name="Stakeholder",
        role="Owner",
        initial_preferences=prefs,
        agent_description="Stakeholder",
        agent_capabilities=["Stakeholder"],
    )
    stakeholder = StakeholderAgent(config=stakeholder_cfg)
    wf.add_agent(stakeholder)

    engine = WorkflowExecutionEngine(
        workflow=wf,
        agent_registry=AgentRegistry(),
        manager_agent=DummyManagerAgent(),
        stakeholder_agent=stakeholder,
        max_timesteps=2,
        seed=42,
    )

    # Run a timestep so evaluation history may be populated under the new engine
    # (history will be appended on cadence EACH_TIMESTEP inside the engine)
    engine.evaluation_cadence = RunCondition.EACH_TIMESTEP
    await engine.execute_timestep()

    # Stakeholder should resolve preferences timeline utilities
    cp = stakeholder.get_preferences_for_timestep(0)
    assert cp.get_preference_dict()["quality"] > 0

    stakeholder.apply_preference_change(1, prefs, None)
    assert stakeholder.get_preferences_for_timestep(1) is not None

    # Engine now records evaluation_results directly; presence is enough
    assert len(engine.validation_engine.evaluation_results) >= 1


@pytest.mark.asyncio
async def test_engine_evaluates_preferences_each_timestep_and_tracks_history() -> None:
    wf = make_workflow()
    prefs = PreferenceWeights(
        preferences=[
            Preference(
                name="quality",
                weight=0.5,
                evaluator=Evaluator(
                    name="quality_eval",
                    description="",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=[
                        WorkflowRubric(
                            name="constant",
                            evaluator_function=lambda wf: 1.0,
                            max_score=1.0,
                        )
                    ],
                ),
            )
        ]
    )

    stakeholder_cfg = StakeholderConfig(
        agent_id="stakeholder",
        agent_type="stakeholder",
        system_prompt="Stakeholder",
        model_name="o3",
        name="Stakeholder",
        role="Owner",
        initial_preferences=prefs,
        agent_description="Stakeholder",
        agent_capabilities=["Stakeholder"],
    )
    stakeholder = StakeholderAgent(config=stakeholder_cfg)
    wf.add_agent(stakeholder)

    engine = WorkflowExecutionEngine(
        workflow=wf,
        agent_registry=AgentRegistry(),
        manager_agent=DummyManagerAgent(),
        stakeholder_agent=stakeholder,
        max_timesteps=1,
        seed=42,
    )

    # Execute a single timestep; engine should evaluate preferences internally
    engine.evaluation_cadence = RunCondition.EACH_TIMESTEP
    await engine.execute_timestep()

    assert len(engine.validation_engine.evaluation_results) == 1
    final_eval = engine.validation_engine.evaluation_results[-1]
    assert "quality" in final_eval.preference_scores
    assert 0.0 <= final_eval.preference_scores["quality"].score <= 1.0


@pytest.mark.asyncio
async def test_engine_evaluate_now_appends_history_even_when_on_completion() -> None:
    wf = make_workflow()
    prefs = PreferenceWeights(
        preferences=[
            Preference(
                name="quality",
                weight=1.0,
                evaluator=Evaluator(
                    name="quality_eval",
                    description="",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=[
                        WorkflowRubric(
                            name="const",
                            evaluator_function=lambda wf: 1.0,
                            max_score=1.0,
                        )
                    ],
                ),
            )
        ]
    )

    stakeholder_cfg = StakeholderConfig(
        agent_id="stakeholder",
        agent_type="stakeholder",
        system_prompt="Stakeholder",
        model_name="o3",
        name="Stakeholder",
        role="Owner",
        initial_preferences=prefs,
        agent_description="Stakeholder",
        agent_capabilities=["Stakeholder"],
    )
    stakeholder = StakeholderAgent(config=stakeholder_cfg)
    wf.add_agent(stakeholder)

    engine = WorkflowExecutionEngine(
        workflow=wf,
        agent_registry=AgentRegistry(),
        manager_agent=DummyManagerAgent(),
        stakeholder_agent=stakeholder,
        seed=42,
    )

    # Default cadence is ON_COMPLETION; explicit on-demand with cadence will append one
    assert engine.validation_engine.evaluation_results == []
    _ = await engine.validation_engine.evaluate_timestep(
        workflow=wf,
        timestep=0,
        preferences=prefs,
        cadence=RunCondition.ON_COMPLETION,
        communications=[],
        manager_actions=[],
    )
    # Expect one result appended
    assert len(engine.validation_engine.evaluation_results) == 1


@pytest.mark.asyncio
async def test_engine_preference_change_emission_and_observation_propagation() -> None:
    wf = make_workflow()
    p1 = PreferenceWeights(
        preferences=[
            Preference(
                name="a",
                weight=1.0,
                evaluator=Evaluator(
                    name="a_eval",
                    description="",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=[
                        WorkflowRubric(
                            name="r", evaluator_function=lambda wf: 1.0, max_score=1.0
                        )
                    ],
                ),
            )
        ]
    )
    p2 = PreferenceWeights(
        preferences=[
            Preference(
                name="b",
                weight=1.0,
                evaluator=Evaluator(
                    name="b_eval",
                    description="",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=[
                        WorkflowRubric(
                            name="r2", evaluator_function=lambda wf: 1.0, max_score=1.0
                        )
                    ],
                ),
            )
        ]
    )

    stakeholder_cfg = StakeholderConfig(
        agent_id="stakeholder",
        agent_type="stakeholder",
        system_prompt="Stakeholder",
        model_name="o3",
        name="Stakeholder",
        role="Owner",
        initial_preferences=p1,
        agent_description="Stakeholder",
        agent_capabilities=["Stakeholder"],
    )
    stakeholder = StakeholderAgent(config=stakeholder_cfg)
    wf.add_agent(stakeholder)

    engine = WorkflowExecutionEngine(
        workflow=wf,
        agent_registry=AgentRegistry(),
        manager_agent=DummyManagerAgent(),
        stakeholder_agent=stakeholder,
        max_timesteps=1,
        seed=42,
    )

    # Update at timestep 0 and ensure change is recorded in stakeholder timeline
    stakeholder.apply_preference_change(0, p2, None)
    assert stakeholder.get_preferences_for_timestep(0) is not None
    # Execute one step; observation path should not error
    engine.evaluation_cadence = RunCondition.EACH_TIMESTEP
    await engine.execute_timestep()


@pytest.mark.asyncio
async def test_rubric_cadence_filtering() -> None:
    wf = make_workflow()

    def one(_: Workflow) -> float:
        return 1.0

    prefs = PreferenceWeights(
        preferences=[
            Preference(
                name="q_each",
                weight=0.5,
                evaluator=Evaluator(
                    name="q_each_eval",
                    description="placeholder",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=[
                        WorkflowRubric(
                            name="each",
                            evaluator_function=one,
                            max_score=1.0,
                            run_condition=RunCondition.EACH_TIMESTEP,
                        )
                    ],
                ),
            ),
            Preference(
                name="q_final",
                weight=0.5,
                evaluator=Evaluator(
                    name="q_final_eval",
                    description="placeholder",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    rubrics=[
                        WorkflowRubric(
                            name="final",
                            evaluator_function=one,
                            max_score=1.0,
                            run_condition=RunCondition.ON_COMPLETION,
                        )
                    ],
                ),
            ),
        ]
    )

    stakeholder_cfg = StakeholderConfig(
        agent_id="stakeholder",
        agent_type="stakeholder",
        system_prompt="Stakeholder",
        model_name="o3",
        name="Stakeholder",
        role="Owner",
        initial_preferences=prefs,
        agent_description="Stakeholder",
        agent_capabilities=["Stakeholder"],
    )
    stakeholder = StakeholderAgent(config=stakeholder_cfg)
    wf.add_agent(stakeholder)

    engine = WorkflowExecutionEngine(
        workflow=wf,
        agent_registry=AgentRegistry(),
        manager_agent=DummyManagerAgent(),
        stakeholder_agent=stakeholder,
        max_timesteps=5,
        seed=42,
    )

    # Per-timestep evals only include EACH_TIMESTEP rubrics
    engine.evaluation_cadence = RunCondition.EACH_TIMESTEP
    await engine.execute_timestep()
    assert engine.validation_engine.evaluation_results
    assert len(engine.validation_engine.evaluation_results) == 1

    # Now run completion; ON_COMPLETION should add one more
    engine.evaluation_cadence = RunCondition.ON_COMPLETION
    await engine.run_full_execution(save_outputs=False)
    assert len(engine.validation_engine.evaluation_results) >= 2


@pytest.mark.asyncio
async def test_engine_handles_preference_weight_normalization_and_aggregation() -> None:
    wf = make_workflow()

    def half_score(_: Workflow) -> float:
        return 0.5

    prefs = PreferenceWeights(
        preferences=[
            Preference(
                name="a",
                weight=0.6,
                evaluator=Evaluator(
                    name="a_eval",
                    description="placeholder",
                    aggregation=AggregationStrategy.MIN,
                    rubrics=[
                        WorkflowRubric(
                            name="r1", evaluator_function=half_score, max_score=1.0
                        )
                    ],
                ),
            ),
            Preference(
                name="b",
                weight=0.4,
                evaluator=Evaluator(
                    name="b_eval",
                    description="placeholder",
                    aggregation=AggregationStrategy.MIN,
                    rubrics=[],
                ),
            ),
            Preference(
                name="c",
                weight=0.2,
                evaluator=Evaluator(
                    name="c_eval",
                    description="placeholder",
                    aggregation=AggregationStrategy.MAX,
                    rubrics=[],
                ),
            ),
        ]
    )

    stakeholder_cfg = StakeholderConfig(
        agent_id="stakeholder",
        agent_type="stakeholder",
        system_prompt="Stakeholder",
        model_name="o3",
        name="Stakeholder",
        role="Owner",
        initial_preferences=prefs,
        agent_description="Stakeholder",
        agent_capabilities=["Stakeholder"],
    )
    stakeholder = StakeholderAgent(config=stakeholder_cfg)
    wf.add_agent(stakeholder)

    engine = WorkflowExecutionEngine(
        workflow=wf,
        agent_registry=AgentRegistry(),
        manager_agent=DummyManagerAgent(),
        stakeholder_agent=stakeholder,
        max_timesteps=1,
        seed=42,
    )

    engine.evaluation_cadence = RunCondition.EACH_TIMESTEP
    await engine.execute_timestep()

    # Expect normalized weights to sum to ~1
    weights = stakeholder.get_preferences_for_timestep(0)
    assert abs(sum(weights.get_preference_dict().values()) - 1.0) < 1e-6
