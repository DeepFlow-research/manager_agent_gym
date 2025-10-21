# pyright: reportMissingImports=false, reportMissingTypeStubs=false
"""
Unified example runner that loads workflow, preferences, and team timeline
from per-scenario modules under examples/end_to_end_examples/<workflow_name>/.
"""

# ruff: noqa: E402
import os
import logging
from manager_agent_gym.core.common.logging import configure_library_logging
from manager_agent_gym.core.common.callbacks import default_timestep_callbacks
from manager_agent_gym.core.agents.stakeholder_agent.stakeholder_agent import (
    StakeholderAgent,
)
import litellm  # type: ignore  # noqa: F401

# Silence LiteLLM before it is imported elsewhere and set global flags
os.environ.setdefault("LITELLM_LOG", "ERROR")
os.environ.setdefault("LITELLM_LOGGING", "OFF")

# Configure console logging for this application and route library logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
configure_library_logging(logging.INFO)


import asyncio
from datetime import datetime
import argparse
from manager_agent_gym.core.workflow.engine import WorkflowExecutionEngine
from manager_agent_gym.core.agents.manager_agent.common.factory import create_manager
from manager_agent_gym.core.agents.workflow_agents.tools.registry import AgentRegistry
from manager_agent_gym.core.communication.service import CommunicationService
from manager_agent_gym.schemas.preferences.evaluator import Rubric
from manager_agent_gym.schemas.domain.workflow import Workflow
from manager_agent_gym.schemas.preferences.preference import (
    PreferenceSnapshot,
)
from manager_agent_gym.config import settings
from examples.common_stakeholders import create_stakeholder_agent
from manager_agent_gym.core.evaluation.rules.common_evaluators import (
    build_default_evaluators,
)
from manager_agent_gym.schemas.agents import AgentConfig
from manager_agent_gym.schemas.preferences.rubric import RunCondition

from examples.scenarios import SCENARIOS


def create_workflow(name: str) -> Workflow:
    if name not in SCENARIOS:
        raise ValueError(f"Unknown workflow: {name}")
    return SCENARIOS[name].create_workflow()


def create_preferences(name: str) -> PreferenceSnapshot:
    if name not in SCENARIOS:
        raise ValueError(f"Unknown preferences: {name}")
    return SCENARIOS[name].create_preferences()


def create_team_timeline(name: str) -> dict[int, list]:
    if name not in SCENARIOS:
        raise ValueError(f"Unknown team timeline: {name}")
    return SCENARIOS[name].create_team_timeline()


def create_evaluator_to_measure_goal_achievement(name: str) -> Rubric:
    if name not in SCENARIOS:
        raise ValueError(f"Unknown evaluator: {name}")
    if not SCENARIOS[name].create_evaluator_to_measure_goal_achievement:
        raise ValueError(f"No evaluator to measure goal achievement for {name}")

    return SCENARIOS[name].create_evaluator_to_measure_goal_achievement()  # type: ignore


async def run_demo(
    offline_run_dir: str | None = None,
    workflow_name: str = "icaap",
    max_timesteps: int | None = None,
    model_name: str = "o3",
    base_output_dir: str | None = None,
    manager_agent_mode: str | None = None,
    seed: int = 42,
    restore_from_snapshot: str | None = None,
    restore_timestep: int | None = None,
    rerun_suffix: str = "_rerun",
    use_rubric_decomposition: bool = False,
):
    """Run a workflow end-to-end with shared config."""

    # 1. Create workflow
    print(f"📋 Creating {workflow_name.upper()} workflow...")
    workflow = create_workflow(workflow_name)
    print(f"   ✅ Created workflow with {len(workflow.tasks)} tasks")

    # 2. Agent registry
    print("\n👥 Setting up agent registry...")
    agent_registry = AgentRegistry()

    # 3. Governance validation rules
    print("\n🎛️ Configuring preferences...")
    preferences = create_preferences(workflow_name)
    # Augment with generic agent behavior rubrics
    print("   ✅ Preferences ready")

    # 5. Agent scheduling via registry
    print("\n🤝 Creating team timeline...")

    # If using rubric decomposition mode, create a single generic AI worker for all tasks
    if use_rubric_decomposition:
        from manager_agent_gym.schemas.agents import AIAgentConfig
        from manager_agent_gym.core.agents.workflow_agents import AIAgent

        print("   🎯 Rubric decomposition mode: Creating generic AI worker...")
        generic_worker_config = AIAgentConfig(
            agent_id="generic_ai_worker",
            agent_type="ai",
            system_prompt="You are a skilled AI worker executing tasks in a managed workflow. Follow task requirements carefully and deliver high-quality work.",
            model_name=model_name,
            agent_description="Generic AI worker for rubric decomposition workflow",
            agent_capabilities=[
                "general_task_execution",
                "tool_usage",
                "communication",
            ],
        )
        generic_worker = AIAgent(config=generic_worker_config, tools=[])
        agent_registry.register_agent(generic_worker)

        # Assign all workflow tasks to this generic worker
        for task in workflow.tasks.values():
            if task.is_atomic_task():  # Only assign atomic tasks
                task.assigned_agent_id = "generic_ai_worker"

        print(
            f"   ✅ Generic worker created and assigned to {sum(1 for t in workflow.tasks.values() if t.is_atomic_task())} atomic tasks"
        )
    else:
        # Standard mode: use scenario-specific team timeline
        team_timeline = create_team_timeline(workflow_name)
        # Register timeline directly on the registry
        for t, changes in team_timeline.items():
            for action, payload, reason in changes:
                if action == "add":
                    agent_registry.schedule_agent_add(t, payload, reason)
                elif action == "remove":
                    # Accept either a config object or a string agent_id for removals
                    agent_id = (
                        payload.agent_id
                        if isinstance(payload, AgentConfig)
                        else payload
                    )
                    agent_registry.schedule_agent_remove(t, agent_id, reason)

        print(f"   ✅ Registered team timeline with {len(team_timeline)} timesteps")

    # 6. Manager agent (selectable baseline or CoT)
    print("\n🧠 Initializing manager agent...")
    # For rubric_decomp mode, use assign_all since tasks are pre-assigned
    effective_manager_mode = (
        "assign_all" if use_rubric_decomposition else manager_agent_mode
    )
    manager = create_manager(
        preferences=preferences,
        model_name=model_name,
        manager_mode=effective_manager_mode,
    )
    print("   ✅ Manager ready")

    # 7. Communication system
    print("\n📡 Setting up communication system...")
    communication_service = CommunicationService()

    # 8. Execution engine
    label = workflow_name

    # Modify output directory for re-evaluation runs to avoid overwriting original results
    rerun_base_output_dir = base_output_dir
    if restore_from_snapshot is not None:
        # Add rerun suffix to the base directory
        if base_output_dir is not None:
            rerun_base_output_dir = base_output_dir.rstrip("/") + rerun_suffix
        else:
            # Use default output directory with rerun suffix
            rerun_base_output_dir = f"./simulation_outputs{rerun_suffix}"
        print(f"🔄 Re-evaluation mode: Saving results to {rerun_base_output_dir}")

    import os  # Ensure os is available in local scope

    output_config = settings.build_labeled_output_config(
        label=label,
        base_output_dir=rerun_base_output_dir,
        run_suffix=os.environ.get("MAG_RUN_SUFFIX"),
        label_as_subdir=True,
    )

    # 9. Make a stakeholder agent
    # For rubric decomposition, use specialized clarification stakeholder with TRUE preferences
    if use_rubric_decomposition:
        from manager_agent_gym.core.agents.stakeholder_agent.rubric_stakeholder import (
            ClarificationStakeholderAgent,
        )
        from manager_agent_gym.schemas.agents.stakeholder import (
            StakeholderConfig,
        )
        from manager_agent_gym.schemas.preferences.evaluator import PreferenceExemplar

        stakeholder = ClarificationStakeholderAgent(
            config=StakeholderConfig(
                agent_id="stakeholder",
                model_name=model_name,
                name="Stakeholder",
                role="Project Stakeholder",
                persona_description="Balanced stakeholder focused on preference elicitation",
                preference_data=PreferenceExemplar(
                    exemplar_output="High-quality output that maximizes stakeholder utility across all preferences.",
                ),
                system_prompt="You are a project stakeholder answering clarification questions about preferences.",
                agent_description="Project stakeholder with expertise in preference elicitation",
                agent_capabilities=[
                    "answer_clarifications",
                    "provide_feedback",
                    "evaluate_quality",
                ],
            ),
            seed=seed,
        )
        print(
            f"   🎯 Created ClarificationStakeholderAgent with {len(preferences.preferences)} TRUE preferences"
        )

        # Add stakeholder to workflow so it can be found by AskClarificationQuestionsAction
        workflow.agents[stakeholder.config.agent_id] = stakeholder
        print("   ✅ Added stakeholder to workflow.agents")
    else:
        stakeholder = create_stakeholder_agent(
            persona="balanced", preferences=preferences
        )

    # Apply scenario-defined preference dynamics (if provided)
    spec = SCENARIOS.get(workflow_name)
    if (
        spec
        and spec.create_preference_update_requests
        and isinstance(stakeholder, StakeholderAgent)
    ):
        stakeholder.apply_weight_updates(spec.create_preference_update_requests())  # type: ignore

    max_steps = int(max_timesteps or settings.resolve_max_timesteps(fallback=50))
    print(f"\n⚙️ Building execution engine (max_timesteps={max_steps})...")
    default_evaluators: list[Rubric] = build_default_evaluators(communication_service)
    default_evaluators.append(
        create_evaluator_to_measure_goal_achievement(workflow_name)
    )

    # Inject scenario-specific constraints and milestone rubrics
    from manager_agent_gym.core.evaluation.rules.scenario_constraints import (
        build_constraints_for_scenario,
    )

    # Add scenario hard constraints (if any)
    scenario_constraints = build_constraints_for_scenario(workflow_name)
    if scenario_constraints is not None:
        default_evaluators.append(scenario_constraints)

    # Create pre-execution phase if using rubric decomposition
    pre_execution_phase = None
    if use_rubric_decomposition:
        from manager_agent_gym.core.execution.pre_execution_phase import (
            InitialRubricGenerationPhase,
        )
        from manager_agent_gym.core.agents.manager_agent.implementations.rubric_generation_manager.rubric_decomposition_manager import (
            RubricDecompositionManagerAgent,
        )

        print("   🎯 Creating rubric decomposition pre-execution phase...")

        # Create decomposition manager
        decomp_manager = RubricDecompositionManagerAgent(
            model_name=model_name,
            max_clarification_budget=2,
            seed=seed,
        )

        # Create runner with manager, stakeholder, and communication service
        pre_execution_phase = InitialRubricGenerationPhase(
            manager=decomp_manager,
            stakeholder=stakeholder,  # type: ignore
            communication_service=communication_service,
            max_turns=10,
        )
        print("   ✅ Pre-execution phase configured")

    engine = WorkflowExecutionEngine(
        workflow=workflow,
        agent_registry=agent_registry,
        stakeholder_agent=stakeholder,
        manager_agent=manager,
        communication_service=communication_service,
        output_config=output_config,
        max_timesteps=max_steps,
        enable_timestep_logging=True,
        enable_final_metrics_logging=True,
        timestep_end_callbacks=default_timestep_callbacks(),
        evaluations=default_evaluators,
        seed=seed,
        pre_execution_phases=[pre_execution_phase] if pre_execution_phase else None,
    )
    print("   ✅ Engine configured")

    # Configure preference-based regret calculator with categories/weights via engine API
    # Evaluate only at selected checkpoints (full rubric sets forced there)
    engine.evaluation_cadence = RunCondition.ON_COMPLETION
    # engine.validation_engine.selected_timesteps = [5, 10, 25, 50, 75]

    # 9. Run (either from snapshot or full simulation)
    results = []
    start_time = datetime.now()
    end_time = start_time

    # Check if we should restore from existing snapshot
    if restore_from_snapshot is not None:
        import os

        if os.path.exists(restore_from_snapshot):
            print(f"\n🔄 RESTORING FROM SNAPSHOT: {restore_from_snapshot}")
            print("=" * 60)

            # Use default timestep if not specified
            target_timestep = restore_timestep if restore_timestep is not None else 100

            # Restore state from snapshot into the existing engine
            engine.restore_from_snapshot(
                snapshot_dir=restore_from_snapshot, timestep=target_timestep
            )

            print(f"   ✅ State restored from timestep {target_timestep}")
            print("\n🧪 RUNNING RE-EVALUATION WITH NEW CRITERIA")

            # Run evaluation on the restored state
            start_time = datetime.now()

            evaluation_result = await engine.validation_engine.evaluate_timestep(
                workflow=engine.workflow,
                timestep=engine.current_timestep,
                cadence=RunCondition.ON_COMPLETION,
                communications=engine.communication_service.get_messages_grouped_by_sender(
                    sort_within_group="time", include_broadcasts=True
                ),
                manager_actions=engine.manager_agent.get_action_buffer(),
                preferences=None,  # Preferences now handled by stakeholder.evaluate_for_timestep()
                workflow_evaluators=engine.evaluations,
            )

            # Save the new evaluation results
            engine.validation_engine.evaluation_results.append(evaluation_result)

            end_time = datetime.now()
            # Create a dummy ExecutionResult for consistency with normal simulation
            from manager_agent_gym.core.execution.schemas.results import create_timestep_result

            execution_result = create_timestep_result(
                timestep=target_timestep,
                manager_id="restored_manager",
                tasks_started=[],
                tasks_completed=[],
                tasks_failed=[],
                execution_time=(end_time - start_time).total_seconds(),
                completed_tasks_simulated_hours=0.0,
                evaluation_result=evaluation_result,
            )
            results = [execution_result]

            print("   ✅ Re-evaluation complete")
        else:
            print(f"\n❌ ERROR: Snapshot directory not found: {restore_from_snapshot}")
            print("   Proceeding with normal simulation instead...")
            restore_from_snapshot = None

    # Run normal simulation if no snapshot restore
    if restore_from_snapshot is None:
        print(f"\n🚀 STARTING SIMULATION: {workflow_name}")
        print("=" * 60)
        start_time = datetime.now()
        results = await engine.run_full_execution()
        end_time = datetime.now()

    # 10. Report
    print("\n📊 SIMULATION COMPLETE - REPORT")
    print("=" * 60)
    print(f"⏱️ Execution time: {(end_time - start_time).total_seconds():.1f} seconds")
    print(f"📈 Timesteps completed: {len(results)}")

    # High-level metrics
    decomposed_tasks = len([t for t in workflow.tasks.values() if t.subtasks])
    print(f"   Structure: {decomposed_tasks} tasks with subtasks")

    # Report final per-preference rewards (weighted)
    tracker = engine.validation_engine
    final_eval = tracker.evaluation_results[-1]
    per_pref_rewards = {
        name: ps.score * ps.weight for name, ps in final_eval.preference_scores.items()
    }
    print("   Final rewards per preference (weighted):")
    for name, reward in per_pref_rewards.items():
        print(
            f"     - {name}: {reward:.3f} (score={final_eval.preference_scores[name].score:.3f}, weight={final_eval.preference_scores[name].weight:.3f})"
        )

    # Team change metrics can be derived from outputs/logs if needed

    # Or compute via the engine using its configured categories
    # Performance files are written by engine on completion

    print(f"\n✅ {workflow_name.upper()} DEMO COMPLETE")
    return engine, results


if __name__ == "__main__":
    # Silence noisy debug logs
    logging.getLogger("litellm").setLevel(logging.CRITICAL)
    logging.getLogger("httpx").setLevel(logging.CRITICAL)

    parser = argparse.ArgumentParser(description="Run an end-to-end example workflow")
    parser.add_argument("--workflow_name", required=True)
    parser.add_argument("--offline-run-dir", dest="offline_run_dir", default=None)
    parser.add_argument("--max-timesteps", dest="max_timesteps", type=int, default=None)
    parser.add_argument("--model-name", dest="model_name", default="o3")
    parser.add_argument("--output-dir", dest="output_dir", default=None)
    parser.add_argument("--manager-agent-mode", dest="manager_agent_mode", default=None)
    parser.add_argument("--seed", dest="seed", type=int, default=42)
    parser.add_argument(
        "--restore-from",
        dest="restore_from_snapshot",
        default=None,
        help="Path to existing simulation run directory to restore and re-evaluate",
    )
    parser.add_argument(
        "--restore-timestep",
        dest="restore_timestep",
        type=int,
        default=None,
        help="Specific timestep to restore from (defaults to final timestep)",
    )
    parser.add_argument(
        "--rerun-suffix",
        dest="rerun_suffix",
        default="_rerun",
        help="Suffix to add to output directory for re-evaluation runs (default: _rerun)",
    )
    parser.add_argument(
        "--num-seeds",
        dest="num_seeds",
        type=int,
        default=1,
        help="Number of random seeds to run sequentially (seed, seed+1, ...).",
    )
    args = parser.parse_args()

    async def _run_multi_seed() -> None:
        base_seed = int(args.seed)
        num_seeds = max(1, int(args.num_seeds))
        for i in range(num_seeds):
            current_seed = base_seed + i
            # Encode seed in run_id via environment so outputs land under
            # <output_dir>/<workflow_name>/run_seed_<n>/...
            os.environ["MAG_RUN_SUFFIX"] = f"seed_{current_seed}"
            print(f"\n==== Running seed {current_seed} ====")
            # Check if rubric decomposition mode is enabled
            use_rubric_decomp = (
                args.manager_agent_mode == "rubric_decomp"
                if args.manager_agent_mode
                else False
            )

            await run_demo(
                offline_run_dir=args.offline_run_dir,
                workflow_name=args.workflow_name,
                max_timesteps=args.max_timesteps,
                model_name=args.model_name,
                base_output_dir=args.output_dir,
                manager_agent_mode=args.manager_agent_mode,
                seed=current_seed,
                restore_from_snapshot=args.restore_from_snapshot,
                restore_timestep=args.restore_timestep,
                rerun_suffix=args.rerun_suffix,
                use_rubric_decomposition=use_rubric_decomp,
            )

    asyncio.run(_run_multi_seed())
