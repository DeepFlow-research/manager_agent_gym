"""
Example: Multi-rubric training for GRPO with TaskExecution architecture.

Demonstrates the complete GRPO training pipeline:
1. Generate N synthetic rubrics + 1 ground truth rubric (unified pre-execution phase)
2. Create N+1 workers, each guided by a different rubric
3. Execute task with all workers in parallel
4. Evaluate each output using the rubric that guided it
5. Rank outputs by score
6. Store all metadata (costs, cognitive burden) for GRPO loss computation

This is the GRPO training pipeline: multi-rubric generation → N+1-way execution →
evaluation → ranking → metadata collection

Train/Eval Split:
=================
The script automatically uses the appropriate data split from GDPEval:
- Training mode (--mode train): Uses TRAINING SPLIT (175 rubrics, 80%)
- Baseline modes (best_of_n, ground_truth, trained_policy): Use EVAL SPLIT (44 rubrics, 20%)
- Each workflow in a batch gets a different random sample (based on workflow_id seed)
- Split files: curation/gdpeval/data/generated/staged_v1/{train,eval}_rubrics.jsonl

Command-Line Arguments:
========================

--mode <MODE>
    Execution mode for the workflow. Choices: train, best_of_n, ground_truth, trained_policy
    Default: train

    - train: GRPO training mode
        * Generates N synthetic rubrics via manager-stakeholder dialogue
        * Uses 1 hardcoded ground truth rubric (for evaluation only)
        * Creates N workers (one per synthetic rubric)
        * Each worker is guided by its assigned synthetic rubric during execution
        * ALL workers evaluated with ground truth rubric (not their guiding rubrics)
        * Tracks generation costs, cognitive burden for GRPO loss computation

    - best_of_n: Best-of-N baseline
        * Creates N worker variants with NO rubric guidance
        * Workers use only base task description
        * Tests whether rubric guidance improves quality beyond sampling diversity
        * Use with --n to specify number of variants

    - ground_truth: Ground truth rubric baseline
        * Creates 1 worker guided by the hardcoded ground truth rubric
        * Represents best-case scenario with perfect rubric
        * Useful for evaluating upper bound of rubric-guided performance

    - trained_policy: Trained policy rubric baseline
        * Generates 1 synthetic rubric using the trained policy
        * Creates 1 worker guided by that rubric
        * Tests the trained policy's ability to generate useful rubrics
        * Requires a trained rubric generation model

--n-synthetic <N>
    Number of synthetic rubrics to generate in training mode
    Default: 2
    Only applies to --mode train

    Examples:
        --n-synthetic 2  → Generate 2 synthetic rubrics, create 2 workers
        --n-synthetic 5  → Generate 5 synthetic rubrics, create 5 workers

    Note: Ground truth rubric is NOT used to create a worker - it's only used
    for evaluation after all workers complete.

--n <N>
    Number of worker variants for best_of_n baseline
    Default: 10
    Only applies to --mode best_of_n

    Examples:
        --n 10 → Create 10 worker variants (no rubric guidance)
        --n 50 → Create 50 worker variants (no rubric guidance)

--batch-size <N>
    Number of workflows to run concurrently (for concurrency testing and training)
    Default: 1 (sequential execution)

    Examples:
        --batch-size 1 → Run single workflow sequentially (default)
        --batch-size 4 → Run 4 workflows concurrently with shared LLM generator
        --batch-size 8 → Run 8 workflows concurrently (stress test concurrency)

    Note: When batch-size > 1, each workflow gets its own isolated state (communication
    service, agent registry, stakeholder, etc.) but ALL workflows share the SAME
    LLM generator instance. This tests concurrency-safety and prepares for GRPO
    training where a shared policy (manager agent) needs to accumulate gradients
    across multiple episodes.

Usage Examples:
===============

# Training mode with 2 synthetic rubrics (default)
python -m examples.research.multi_agent_ml_task

# Training mode with custom number of synthetic rubrics
python -m examples.research.multi_agent_ml_task --mode train --n-synthetic 5

# Best-of-N baseline with 10 variants (default)
python -m examples.research.multi_agent_ml_task --mode best_of_n

# Best-of-N baseline with custom number of variants
python -m examples.research.multi_agent_ml_task --mode best_of_n --n 50

# Ground truth rubric baseline (1 worker with GT rubric)
python -m examples.research.multi_agent_ml_task --mode ground_truth

# Trained policy rubric baseline (1 worker with trained policy rubric)
python -m examples.research.multi_agent_ml_task --mode trained_policy

# Test concurrency with 4 parallel workflows (shared LLM generator)
python -m examples.research.multi_agent_ml_task --batch-size 4

# Stress test with 8 parallel workflows
python -m examples.research.multi_agent_ml_task --mode train --n-synthetic 2 --batch-size 8

GRPO Training Context:
======================

This example supports the complete GRPO workflow where:
1. A policy (manager agent) generates N synthetic rubrics through stakeholder dialogue
2. N workers execute tasks, each guided by a different synthetic rubric
3. ALL worker outputs are evaluated using the ground truth rubric (NOT their guiding rubrics)
4. Advantage is computed for each worker: GT_score(output_i) - baseline
5. GRPO loss is computed using:
   - Advantage: measures how well each synthetic rubric guided the worker
   - Log probability: policy's likelihood of generating that rubric
   - Cost regularization: LLM API costs for rubric generation
   - Cognitive burden: difficulty of clarification questions asked

Key Insight: The quality of a rubric is measured by how well a worker performs
when GUIDED by that rubric, as evaluated by the ground truth standard.

The training mode generates multiple rollouts with different rubrics to compute
policy gradients. Baselines provide comparison points for evaluating the trained
policy's performance.
"""

import traceback

import argparse
import asyncio
from uuid import uuid4

from manager_agent_gym.schemas.domain.workflow import Workflow
from manager_agent_gym.schemas.domain.task import Task
from manager_agent_gym.schemas.domain.resource import Resource
from manager_agent_gym.schemas.agents import AIAgentConfig
from manager_agent_gym.schemas.preferences.preference import PreferenceSnapshot
from manager_agent_gym.schemas.agents.stakeholder import StakeholderConfig
from manager_agent_gym.core.workflow.services import WorkflowMutations
from manager_agent_gym.core.workflow.engine import WorkflowExecutionEngine
from manager_agent_gym.core.agents.workflow_agents.tools.registry import AgentRegistry
from manager_agent_gym.core.agents.workflow_agents.workers.ai_agent import AIAgent
from manager_agent_gym.core.agents.manager_agent.common.factory import (
    create_manager_agent,
)

# Rubric generation imports
from manager_agent_gym.core.workflow.phases.multi_rubric_training import (
    MultiRubricTrainingPhase,
)
from manager_agent_gym.core.workflow.phases.baseline_phases import (
    create_baseline_phase,
    RubricExecutionPhaseBase,
)
from manager_agent_gym.core.agents.manager_agent.implementations.rubric_generation_manager.rubric_decomposition_manager import (
    RubricDecompositionManagerAgent,
)
from manager_agent_gym.core.agents.stakeholder_agent.rubric_stakeholder import (
    ClarificationStakeholderAgent,
)

import logging
from manager_agent_gym.core.common.logging import configure_library_logging

# Configure root logger to output to console
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
# Enable library logging
configure_library_logging(level=logging.INFO)


async def run_single_workflow_instance(
    workflow_id: int,
    mode: str,
    n_synthetic: int,
    n_variants: int,
    fast_llm_generator,  # CloudLLMGenerator for clarification/rubric gen
    quality_llm_generator,  # CloudLLMGenerator for workers
    batch_name: str,  # Batch-level timestamp directory
) -> dict:
    """Run a single workflow execution instance with isolated state.

    Each workflow gets its own:
    - CommunicationService
    - Stakeholder agent
    - Rubric decomposition manager
    - Agent registry
    - Worker configs
    - Execution manager
    - Workflow engine

    All workflows SHARE the same generators (for GRPO gradient accumulation).

    Args:
        workflow_id: Unique identifier for this workflow instance (for logging)
        mode: Execution mode
        n_synthetic: Number of synthetic rubrics for training mode
        n_variants: Number of variants for best_of_n baseline
        fast_llm_generator: SHARED fast generator for clarification/rubric gen
        quality_llm_generator: SHARED quality generator for workers

    Returns:
        Dictionary with workflow results (status, metrics, etc.)
    """
    print(f"\n[Workflow {workflow_id}] 🚀 Starting workflow execution...")

    from manager_agent_gym.core.communication.service import CommunicationService
    from manager_agent_gym.core.evaluation.loaders.gdpeval_sample_loader import (
        load_gdpeval_sample,
    )
    from manager_agent_gym.schemas.domain.task import TaskStatus
    from pathlib import Path
    from manager_agent_gym.core.agents.manager_agent.implementations.rubric_generation_manager.utils import (
        convert_staged_rubric_to_executable,
    )
    from manager_agent_gym.core.agents.manager_agent.implementations.rubric_generation_manager.rubric_generation import (
        ManagerAgentGeneratedStagedRubricWithMetadata,
    )
    from manager_agent_gym.core.agents.workflow_agents.tools.tool_factory import (
        ToolFactory,
    )
    from manager_agent_gym.core.workflow.resource_storage import ResourceFileManager

    SEED = 42 + workflow_id  # Different seed per workflow

    # ============================================================
    # 1. Create isolated communication service
    # ============================================================
    communication_service = CommunicationService()
    print(f"[Workflow {workflow_id}]   ✓ Created fresh CommunicationService")

    # ============================================================
    # 2. Load GDPEval sample with train/eval split
    # ============================================================
    # Training mode: Use training split with random sampling for diversity
    # Baseline modes: Use eval split with random sampling
    if mode == "train":
        use_train_split = True
        split_label = "TRAIN"
    else:
        use_train_split = False
        split_label = "EVAL"
    
    # Use workflow_id-based random seed for diverse sampling across batch
    gdpeval_sample = load_gdpeval_sample(
        use_train_split=use_train_split,
        random_seed=SEED,
    )
    
    print(
        f"[Workflow {workflow_id}]   ✓ Loaded {split_label} sample "
        f"({gdpeval_sample['sample_index']}/{gdpeval_sample['total_samples_in_split']-1}): "
        f"{gdpeval_sample['task_id'][:8]}..."
    )

    workflow = Workflow(
        name=f"{gdpeval_sample['task_name']} (W{workflow_id})",
        workflow_goal=gdpeval_sample["task_description"],
        owner_id=uuid4(),
        seed=SEED,
    )

    # Add reference files as input resources
    input_resources = []
    for ref_file_path in gdpeval_sample["reference_files"]:
        ref_file = Path(ref_file_path)
        if ref_file.exists():
            suffix = ref_file.suffix.lower()
            mime_type_map = {
                ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                ".pdf": "application/pdf",
                ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                ".txt": "text/plain",
                ".csv": "text/csv",
                ".json": "application/json",
            }
            mime_type = mime_type_map.get(suffix, "application/octet-stream")

            resource = Resource(
                name=ref_file.name,
                description=f"Reference file for {gdpeval_sample['occupation']} task",
                file_path=str(ref_file.absolute()),
                mime_type=mime_type,
                size_bytes=ref_file.stat().st_size,
            )
            WorkflowMutations.add_resource(workflow, resource)
            input_resources.append(resource)

    # Create main task
    gdpeval_task = Task(
        name=gdpeval_sample["task_name"],
        description=gdpeval_sample["task_description"],
        status=TaskStatus.PENDING,
        input_resource_ids=[r.id for r in input_resources],
    )
    WorkflowMutations.add_task(workflow, gdpeval_task)

    print(
        f"[Workflow {workflow_id}]   ✓ Created workflow with {len(input_resources)} input(s)"
    )

    # ============================================================
    # 3. Prepare ground truth rubric
    # ============================================================
    gt_rubric_spec_raw = gdpeval_sample["rubric_spec"]
    gt_rubric_spec = ManagerAgentGeneratedStagedRubricWithMetadata(
        **gt_rubric_spec_raw.model_dump(),
    )
    gt_rubric_executable = convert_staged_rubric_to_executable(gt_rubric_spec)

    print(
        f"[Workflow {workflow_id}]   ✓ Gold rubric: {gt_rubric_executable.category_name}"
    )

    # ============================================================
    # 4. Create clarification stakeholder (isolated)
    # ============================================================
    stakeholder_config = StakeholderConfig(
        agent_id=f"gdpeval_stakeholder_w{workflow_id}",
        agent_type="stakeholder",
        name=f"{gdpeval_sample['occupation']} Expert",
        role=gdpeval_sample["occupation"],
        persona_description=f"Expert in {gdpeval_sample['sector']}",
        agent_description=f"{gdpeval_sample['occupation']} stakeholder",
        agent_capabilities=["domain expertise", "quality evaluation"],
        preference_data=gt_rubric_executable,
        model_name="gpt-4.1-mini",  # not used rn note!
    )

    stakeholder = ClarificationStakeholderAgent(
        config=stakeholder_config,
        llm_generator=fast_llm_generator,  # FAST generator for clarification
        seed=SEED,
    )

    print(
        f"[Workflow {workflow_id}]   ✓ Created stakeholder (uses FAST LLM for clarification)"
    )

    # ============================================================
    # 5. Create rubric decomposition manager (isolated)
    # ============================================================
    rubric_manager = RubricDecompositionManagerAgent(
        llm_generator=fast_llm_generator,  # FAST generator for rubric generation
        model_name="gpt-4.1-mini",  # not used rn note!
        max_clarification_budget=2,
        seed=SEED,
    )

    print(f"[Workflow {workflow_id}]   ✓ Created rubric manager (uses FAST LLM)")

    # ============================================================
    # 6. Create agent registry and tools (isolated)
    # ============================================================
    # ⚠️ CRITICAL: AgentRegistry MUST use quality_llm_generator!
    # All AI workers (AIAgent instances) created via registry.register_ai_agent()
    # will use this generator for task execution. If you use fast_llm_generator here,
    # the simulation will fail with structured output errors when using Claude models.
    agent_registry = AgentRegistry(
        llm_generator=quality_llm_generator  # ✅ QUALITY generator for workers (Claude Haiku 4.5)
    )
    agent_registry.register_agent_class("ai", AIAgent)

    resource_manager = ResourceFileManager()
    gdpeval_tools = ToolFactory.create_gdpeval_tools(resource_manager=resource_manager)

    worker_config = AIAgentConfig(
        agent_id=f"ml_researcher_w{workflow_id}",
        agent_type="ai",
        model_name="gpt-5",
        agent_description="expert ML researcher",
        agent_capabilities=["algorithm design", "model development", "evaluation"],
        max_turns=20,
        enable_execution_tracing=True,
        use_multimodal_resources=True,
    )

    print(f"[Workflow {workflow_id}]   ✓ Created agent registry & tools")

    # ============================================================
    # 7. Create pre-execution phase based on mode
    # ============================================================
    pre_execution_phase: MultiRubricTrainingPhase | RubricExecutionPhaseBase
    if mode == "train":
        pre_execution_phase = MultiRubricTrainingPhase(
            llm_generator=fast_llm_generator,
            n_synthetic_rubrics=n_synthetic,
            ground_truth_rubric=gt_rubric_spec,
            base_worker_config=worker_config,
            agent_registry=agent_registry,
            rubric_manager=rubric_manager,
            stakeholder=stakeholder,
            communication_service=communication_service,
            additional_tools=gdpeval_tools,
            max_turns=5,
        )
        print(
            f"[Workflow {workflow_id}]   ✓ Training phase: {n_synthetic} synthetic rubrics"
        )

    elif mode == "best_of_n":
        pre_execution_phase = create_baseline_phase(
            baseline="best_of_n",
            n=n_variants,
            base_worker_config=worker_config,
            agent_registry=agent_registry,
            rubric_manager=rubric_manager,
            stakeholder=stakeholder,
            communication_service=communication_service,
            llm_generator=fast_llm_generator,
            additional_tools=gdpeval_tools,
        )
        print(f"[Workflow {workflow_id}]   ✓ Best-of-N: {n_variants} variants")

    elif mode == "ground_truth":
        pre_execution_phase = create_baseline_phase(
            baseline="ground_truth",
            ground_truth_rubric=gt_rubric_spec,
            base_worker_config=worker_config,
            agent_registry=agent_registry,
            rubric_manager=rubric_manager,
            stakeholder=stakeholder,
            communication_service=communication_service,
            llm_generator=fast_llm_generator,
            additional_tools=gdpeval_tools,
        )
        print(f"[Workflow {workflow_id}]   ✓ Ground truth baseline")

    elif mode == "trained_policy":
        pre_execution_phase = create_baseline_phase(
            baseline="trained_policy",
            base_worker_config=worker_config,
            agent_registry=agent_registry,
            rubric_manager=rubric_manager,
            stakeholder=stakeholder,
            communication_service=communication_service,
            llm_generator=fast_llm_generator,
            additional_tools=gdpeval_tools,
        )
        print(f"[Workflow {workflow_id}]   ✓ Trained policy baseline")
    else:
        raise ValueError(f"Unknown mode: {mode}")

    # ============================================================
    # 8. Create NoOp execution manager (isolated)
    # ============================================================
    execution_manager = create_manager_agent(
        llm_generator=quality_llm_generator,  # QUALITY generator (though NoOp doesn't use it)
        preferences=PreferenceSnapshot(preferences=[]),
        manager_mode="noop",
    )

    print(f"[Workflow {workflow_id}]   ✓ Created NoOp execution manager")

    # ============================================================
    # 9. Create and run workflow engine
    # ============================================================
    
    # Create output config with batch-level timestamp + GDP task ID structure
    from manager_agent_gym.core.workflow.schemas.config import OutputConfig
    from pathlib import Path
    
    output_config = OutputConfig(
        base_output_dir=Path("./simulation_outputs") / batch_name,  # Batch timestamp directory
        run_id=gdpeval_sample["task_id"],  # GDP task ID for this run
        create_run_subdirectory=True,
    )
    print(f"[Workflow {workflow_id}]   ✓ Output directory: {batch_name}/run_{gdpeval_sample['task_id']}")
    
    engine = WorkflowExecutionEngine(
        workflow=workflow,
        llm_generator=quality_llm_generator,
        agent_registry=agent_registry,
        stakeholder_agent=stakeholder,
        manager_agent=execution_manager,
        communication_service=communication_service,
        seed=SEED,
        output_config=output_config,  # Pass custom output config with batch + task structure
        pre_execution_phases=[pre_execution_phase],
        gold_rubrics=[gt_rubric_executable],
        max_timesteps=10,
        enable_timestep_logging=True,
        enable_final_metrics_logging=True,
        log_preference_evaluation_progress=False,  # Disable inner progress bars for parallel eval
    )

    # Enable ignore_gates mode for GRPO training (provides continuous reward signal)
    if mode == "train":
        engine.validation_engine._ignore_gates = True
        print(f"[Workflow {workflow_id}]   ✓ Training mode: ignore_gates enabled")
        print(
            f"[Workflow {workflow_id}]     → All rubric stages will run for continuous reward signal"
        )

    print(f"[Workflow {workflow_id}]   ✓ Created workflow engine")
    print(f"[Workflow {workflow_id}] ▶ Running execution...\n")

    # Run the workflow
    try:
        final_state = await engine.run_full_execution()

        print(f"\n[Workflow {workflow_id}] ✅ Execution complete!")

        return {
            "workflow_id": workflow_id,
            "status": "completed",
            "task_id": gdpeval_sample["task_id"],
            "workflow_name": workflow.name,
            "final_state": final_state,
            "message": f"Workflow {workflow_id} completed successfully",
        }
    except Exception as e:
        print(
            f"\n[Workflow {workflow_id}] ❌ Execution failed: {e, traceback.format_exc()}"
        )
        return {
            "workflow_id": workflow_id,
            "status": "failed",
            "workflow_name": workflow.name,
            "error": str(e),
            "message": f"Workflow {workflow_id} failed",
        }


async def run_multi_agent_ml_example(
    mode: str = "train",
    n_synthetic: int = 2,
    n_variants: int = 10,
    batch_size: int = 1,
):
    """Run multi-agent ML task with optional batch processing for concurrency testing.

    The script automatically uses the appropriate train/eval split:
    - Training mode (mode="train"): Uses training split (175 rubrics, 80%)
    - Baseline modes (best_of_n, ground_truth, trained_policy): Use eval split (44 rubrics, 20%)
    - Each workflow in a batch gets a different random sample from the split (based on workflow_id seed)

    Args:
        mode: Execution mode - "train", "best_of_n", "ground_truth", or "trained_policy"
        n_synthetic: Number of synthetic rubrics for training mode
        n_variants: Number of variants for best_of_n baseline
        batch_size: Number of workflows to run concurrently (1 = sequential, >1 = parallel)
    """
    
    # Create batch-level timestamp for all runs in this session
    from datetime import datetime
    batch_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    batch_name = f"batch_{batch_timestamp}"

    print("=" * 80)
    if mode == "train":
        print("Multi-Rubric Training Example (GRPO)")
        print("📊 Data Split: TRAINING SET (175 rubrics, 80%)")
    else:
        print(f"Baseline Evaluation: {mode}")
        print("📊 Data Split: EVAL SET (44 rubrics, 20%)")

    print(f"📁 Batch Directory: simulation_outputs/{batch_name}/")
    if batch_size > 1:
        print(f"🔀 BATCH MODE: Running {batch_size} workflows concurrently")
        print("   Testing concurrency-safety with shared LLM generator")
        print("   Each workflow samples a different task (seed = 42 + workflow_id)")
    print("=" * 80)
    print()

    if mode == "train":
        print("This example demonstrates the GRPO training pipeline:")
        print("  1. Generate N synthetic rubrics")
        print("  2. Create N workers, each guided by a synthetic rubric")
        print("  3. Execute task with all workers in parallel")
        print("  4. Evaluate ALL outputs with ground truth rubric")
        print("  5. Rank outputs and collect metadata for GRPO")
    else:
        print(f"Running baseline: {mode}")
        if mode == "best_of_n":
            print(f"  - {n_variants} workers with no rubric guidance")
        elif mode == "ground_truth":
            print("  - 1 worker with ground truth rubric")
        elif mode == "trained_policy":
            print("  - 1 worker with trained policy rubric")
    print("=" * 80)
    print()

    # ============================================================
    # CREATE DUAL LLM GENERATORS (fast for rubric gen, quality for workers)
    # ============================================================
    print("🔧 Creating dual LLM generators...")
    print("")
    print("  📋 Generator Architecture:")
    print("     • fast_llm_generator → clarification dialogue, rubric generation")
    print("     • quality_llm_generator → worker task execution (via AgentRegistry)")
    print("")
    print("  ⚠️  CRITICAL: AgentRegistry MUST use quality_llm_generator!")
    print("     Claude models don't support native structured outputs, so we use")
    print("     a two-step process: Claude executes → GPT-4.1-mini parses to JSON")
    print("")

    from manager_agent_gym.core.common.llm_generator import CloudLLMGenerator

    fast_llm_generator = CloudLLMGenerator(model_name="gpt-4.1-mini")
    quality_llm_generator = CloudLLMGenerator(model_name="claude-haiku-4-5")

    print("  ✓ Fast generator (gpt-4.1-mini) for clarification & rubric generation")
    print("  ✓ Quality generator (claude-haiku-4-5) for worker task execution")
    print("    → Claude Haiku 4.5: Fast, cost-effective, excellent tool calling!")
    print(f"  ✓ Generators will be SHARED across all {batch_size} workflow(s)")
    print()

    # ============================================================
    # RUN WORKFLOWS (sequential or parallel based on batch_size)
    # ============================================================
    if batch_size == 1:
        print("🔧 Running single workflow (sequential mode)...")
        result = await run_single_workflow_instance(
            workflow_id=0,
            mode=mode,
            n_synthetic=n_synthetic,
            n_variants=n_variants,
            fast_llm_generator=fast_llm_generator,
            quality_llm_generator=quality_llm_generator,
            batch_name=batch_name,
        )
        results = [result]
    else:
        print(f"🔧 Running {batch_size} workflows concurrently...")
        print("  ⚡ Testing concurrency-safety of workflow engine")
        print("  🔗 All workflows share the same LLM generators")
        print("  📁 Each workflow saves outputs immediately upon completion")
        print()

        # Track completions for progress reporting
        completed_count = 0
        completed_tasks: list[tuple[int, dict[str, object] | Exception, float]] = []
        start_time = asyncio.get_event_loop().time()
        
        # Wrapper to track completion and report progress
        async def run_with_progress_tracking(workflow_id: int):
            nonlocal completed_count
            try:
                result = await run_single_workflow_instance(
                    workflow_id=workflow_id,
                    mode=mode,
                    n_synthetic=n_synthetic,
                    n_variants=n_variants,
                    fast_llm_generator=fast_llm_generator,
                    quality_llm_generator=quality_llm_generator,
                    batch_name=batch_name,
                )
                completed_count += 1
                elapsed = asyncio.get_event_loop().time() - start_time
                
                # Report completion immediately
                if isinstance(result, dict) and result.get('status') == 'completed':
                    task_id = result.get('task_id', 'unknown')
                    task_name = result.get('workflow_name', 'unknown')
                    print("\n" + "=" * 80)
                    print(f"✅ EPISODE {completed_count}/{batch_size} COMPLETE")
                    print("=" * 80)
                    print(f"  Workflow ID: {workflow_id}")
                    print(f"  GDP Task ID: {task_id}")
                    print(f"  Task: {task_name}")
                    print(f"  Elapsed Time: {elapsed:.1f}s")
                    print(f"  Output Directory: simulation_outputs/run_{task_id}/")
                    print(f"  Progress: {completed_count}/{batch_size} episodes ({completed_count/batch_size*100:.1f}%)")
                    
                    # Estimate time remaining
                    if completed_count < batch_size:
                        avg_time = elapsed / completed_count
                        remaining_time = avg_time * (batch_size - completed_count)
                        print(f"  Estimated Time Remaining: {remaining_time:.1f}s ({remaining_time/60:.1f}m)")
                    print("=" * 80 + "\n")
                
                completed_tasks.append((workflow_id, result, elapsed))
                return result
            except Exception as e:
                completed_count += 1
                elapsed = asyncio.get_event_loop().time() - start_time
                print("\n" + "=" * 80)
                print(f"❌ EPISODE {completed_count}/{batch_size} FAILED")
                print("=" * 80)
                print(f"  Workflow ID: {workflow_id}")
                print(f"  Error: {type(e).__name__}: {e}")
                print(f"  Elapsed Time: {elapsed:.1f}s")
                print(f"  Progress: {completed_count}/{batch_size} episodes ({completed_count/batch_size*100:.1f}%)")
                print("=" * 80 + "\n")
                completed_tasks.append((workflow_id, e, elapsed))
                return e

        # Create batch of workflows with progress tracking
        workflow_tasks = [
            run_with_progress_tracking(i)
            for i in range(batch_size)
        ]

        # Run all workflows concurrently with incremental reporting
        print(f"🚀 Starting {batch_size} parallel episodes...\n")
        results = await asyncio.gather(*workflow_tasks, return_exceptions=False)  # type: ignore[assignment]

        # Final summary
        total_elapsed = asyncio.get_event_loop().time() - start_time
        failures = [r for r in results if isinstance(r, Exception)]
        successes = [r for r in results if isinstance(r, dict) and r.get('status') == 'completed']
        
        print(f"\n{'='*80}")
        print("📊 BATCH EXECUTION SUMMARY")
        print(f"{'='*80}")
        print(f"  Total Episodes: {batch_size}")
        print(f"  Successful: {len(successes)}")
        print(f"  Failed: {len(failures)}")
        print(f"  Total Time: {total_elapsed:.1f}s ({total_elapsed/60:.1f}m)")
        print(f"  Average Time per Episode: {total_elapsed/batch_size:.1f}s")
        print(f"{'='*80}")
        
        if failures:
            print(f"\n❌ {len(failures)} episode(s) failed:")
            for i, exc in enumerate(failures):
                print(f"  • Workflow {i}: {type(exc).__name__}: {exc}")
        
        # List all output directories
        print("\n📁 Output Directories (all saved incrementally):")
        for result in successes:
            if isinstance(result, dict):
                task_id = result.get('task_id', 'unknown')
                print(f"  • simulation_outputs/run_{task_id}/")
        print()

    print("✅ Batch execution complete!")
    print()

    # Note: All workflow execution is now handled by run_single_workflow_instance
    # The legacy single-workflow code below has been removed since each workflow
    # in the batch gets its own complete execution environment

    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Multi-agent ML task with rubric generation (training and baselines)"
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["train", "best_of_n", "ground_truth", "trained_policy"],
        default="train",
        help="Execution mode: train (GRPO training), or baseline (best_of_n, ground_truth, trained_policy)",
    )
    parser.add_argument(
        "--n-synthetic",
        type=int,
        default=2,
        help="Number of synthetic rubrics for training mode (default: 2)",
    )
    parser.add_argument(
        "--n",
        type=int,
        default=8,
        help="Number of variants for best_of_n baseline (default: 10)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1,
        help="Number of workflows to run concurrently (tests concurrency-safety, default: 1)",
    )

    args = parser.parse_args()

    asyncio.run(
        run_multi_agent_ml_example(
            mode=args.mode,
            n_synthetic=args.n_synthetic,
            n_variants=args.n,
            batch_size=args.batch_size,
        )
    )
