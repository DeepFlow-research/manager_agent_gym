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

import argparse
import asyncio
from uuid import uuid4

from manager_agent_gym.schemas.domain.workflow import Workflow
from manager_agent_gym.schemas.domain.task import Task
from manager_agent_gym.schemas.domain.resource import Resource
from manager_agent_gym.schemas.domain.base import TaskStatus
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
)
from manager_agent_gym.core.workflow.phases.rubric_execution_base import (
    RubricExecutionPhaseBase,
)
from manager_agent_gym.core.agents.manager_agent.implementations.rubric_generation_manager.rubric_decomposition_manager import (
    RubricDecompositionManagerAgent,
)
from manager_agent_gym.core.agents.stakeholder_agent.rubric_stakeholder import (
    ClarificationStakeholderAgent,
)
from manager_agent_gym.core.agents.manager_agent.implementations.rubric_generation_manager.rubric_generation import (
    ManagerAgentGeneratedRubricWithMetadata,
    RubricGenerationMetadata,
)


def load_gdpeval_ground_truth():
    """Load first GDPEval sample as ground truth.
    
    Returns:
        Dictionary with task info and gold rubric
    """
    from pathlib import Path
    from manager_agent_gym.core.evaluation.loaders.gdpeval_sample_loader import (
        load_first_gdpeval_sample,
    )
    
    # Load first GDPEval sample
    sample = load_first_gdpeval_sample()
    
    return sample


async def run_multi_agent_ml_example(
    mode: str = "train",
    n_synthetic: int = 2,
    n_variants: int = 10,
):
    """Run a complete multi-agent ML task with rubric generation and evaluation.
    
    Args:
        mode: Execution mode - "train", "best_of_n", "ground_truth", or "trained_policy"
        n_synthetic: Number of synthetic rubrics for training mode
        n_variants: Number of variants for best_of_n baseline
    """

    print("=" * 80)
    if mode == "train":
        print("Multi-Rubric Training Example (GRPO)")
    else:
        print(f"Baseline Evaluation: {mode}")
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
    # 1. Load GDPEval sample and create workflow
    # ============================================================
    print("🔧 Step 1: Loading GDPEval sample and creating workflow...")

    SEED = 42

    # Load first GDPEval sample
    gdpeval_sample = load_gdpeval_ground_truth()
    
    print(f"  ✓ Loaded GDPEval task: {gdpeval_sample['task_id']}")
    print(f"  ✓ Sector: {gdpeval_sample['sector']}")
    print(f"  ✓ Occupation: {gdpeval_sample['occupation']}")
    print(f"  ✓ Reference files: {len(gdpeval_sample['reference_files'])}")

    workflow = Workflow(
        name=gdpeval_sample['task_name'],
        workflow_goal=gdpeval_sample['task_description'],  # Truncate for display
        owner_id=uuid4(),
        seed=SEED,
    )

    # Add reference files as input resources
    from pathlib import Path
    input_resources = []
    for ref_file_path in gdpeval_sample['reference_files']:
        ref_file = Path(ref_file_path)
        if ref_file.exists():
            # Determine MIME type
            suffix = ref_file.suffix.lower()
            mime_type_map = {
                '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                '.pdf': 'application/pdf',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.txt': 'text/plain',
                '.csv': 'text/csv',
                '.json': 'application/json',
            }
            mime_type = mime_type_map.get(suffix, 'application/octet-stream')
            
            resource = Resource(
                name=ref_file.name,
                description=f"Reference file for {gdpeval_sample['occupation']} task",
                file_path=str(ref_file.absolute()),
                mime_type=mime_type,
                size_bytes=ref_file.stat().st_size,
            )
            WorkflowMutations.add_resource(workflow, resource)
            input_resources.append(resource)

    # Create main task from GDPEval prompt
    gdpeval_task = Task(
        name=gdpeval_sample['task_name'],
        description=gdpeval_sample['task_description'],
        status=TaskStatus.PENDING,
        input_resource_ids=[r.id for r in input_resources],
    )
    WorkflowMutations.add_task(workflow, gdpeval_task)

    print(f"  ✓ Created workflow: {workflow.name}")
    print(f"  ✓ Created task: {gdpeval_task.name}")
    print(f"  ✓ Added {len(input_resources)} reference file(s) as inputs")
    for res in input_resources:
        print(f"      - {res.name} ({res.mime_type})")
    print()

    # ============================================================
    # 2. Create communication service
    # ============================================================
    print("🔧 Step 2: Setting up communication service...")

    from manager_agent_gym.core.communication.service import (
        COMMUNICATION_SERVICE_SINGLETON,
    )

    communication_service = COMMUNICATION_SERVICE_SINGLETON

    print("  ✓ Communication service initialized (using singleton)")
    print()

    # ============================================================
    # 3. Prepare ground truth rubric (GDPEval gold standard)
    # ============================================================
    print("🔧 Step 3: Preparing GDPEval gold standard rubric...")

    # Convert GDPEval rubric to executable format
    from manager_agent_gym.core.agents.manager_agent.implementations.rubric_generation_manager.utils import (
        convert_staged_rubric_to_executable,
    )
    from manager_agent_gym.core.agents.manager_agent.implementations.rubric_generation_manager.rubric_generation import (
        ManagerAgentGeneratedStagedRubricWithMetadata,
        RubricGenerationMetadata,
    )
    
    # Wrap GDPEval rubric with metadata (metadata is empty for gold standard)
    gt_rubric_spec_raw = gdpeval_sample['rubric_spec']
    gt_rubric_spec = ManagerAgentGeneratedStagedRubricWithMetadata(
        **gt_rubric_spec_raw.model_dump(),
        metadata=RubricGenerationMetadata(),  # No generation cost for gold standard
    )
    gt_rubric_executable = convert_staged_rubric_to_executable(gt_rubric_spec)
    
    print(f"  ✓ Gold rubric: {gt_rubric_executable.category_name}")
    print(f"  ✓ Max score: {gt_rubric_executable.max_total_score}")
    print(f"  ✓ Stages: {len(gt_rubric_executable.stages)}")
    for stage in gt_rubric_executable.stages:
        gate_marker = "🚪 GATE" if stage.is_required else "  "
        print(f"    {gate_marker} {stage.name}: {len(stage.rules)} rules, {stage.max_points} pts")
    print()

    # ============================================================
    # 4. Create clarification stakeholder (no preference data needed)
    # ============================================================
    print("🔧 Step 4: Creating stakeholder for rubric generation...")

    stakeholder_config = StakeholderConfig(
        agent_id="gdpeval_stakeholder",
        agent_type="stakeholder",
        name=f"{gdpeval_sample['occupation']} Expert",
        role=gdpeval_sample['occupation'],
        persona_description=f"Expert in {gdpeval_sample['sector']} with deep knowledge of {gdpeval_sample['occupation']} best practices.",
        agent_description=f"{gdpeval_sample['occupation']} stakeholder for rubric generation",
        agent_capabilities=[
            "domain expertise",
            "quality evaluation",
            "professional standards",
        ],
        preference_data=None,  # No preference data - using gold rubrics directly
        model_name="gpt-5",
    )

    stakeholder = ClarificationStakeholderAgent(
        config=stakeholder_config,
        seed=SEED,
    )

    print(f"  ✓ Created clarification stakeholder: {stakeholder.config.agent_id}")
    print("  ✓ Role: {stakeholder.config.role}")
    print("  ✓ Note: Stakeholder will help generate rubrics; gold rubric used for evaluation")
    print()

    # ============================================================
    # 5. Create rubric decomposition manager
    # ============================================================
    print("🔧 Step 5: Creating rubric decomposition manager...")

    rubric_manager = RubricDecompositionManagerAgent(
        model_name="gpt-4o-mini",
        max_clarification_budget=3,
        seed=SEED,
    )

    print(f"  ✓ Created rubric manager: {rubric_manager.agent_id}")
    print("  ✓ Max clarification budget: 3 turns")
    print()

    # ============================================================
    # 6. Create agent registry, worker config, and GDPEval tools
    # ============================================================
    print("🔧 Step 6: Setting up agent registry, worker, and tools...")

    agent_registry = AgentRegistry()
    agent_registry.register_agent_class("ai", AIAgent)

    # Create GDPEval toolkit (REAL tools for file creation!)
    from manager_agent_gym.core.agents.workflow_agents.tools.tool_factory import (
        ToolFactory,
    )
    from manager_agent_gym.core.workflow.resource_storage import ResourceFileManager

    resource_manager = ResourceFileManager()
    gdpeval_tools = ToolFactory.create_gdpeval_tools(resource_manager=resource_manager)

    print(f"  ✓ Created GDPEval toolkit with {len(gdpeval_tools)} real tools")

    worker_config = AIAgentConfig(
        agent_id="ml_researcher",
        agent_type="ai",
        # system_prompt removed - now using agent_description (uses proper template)
        model_name="gpt-5",  # Using mini for faster/cheaper execution
        agent_description="an expert ML researcher with deep knowledge of machine learning algorithms, model evaluation, and best practices who develops creative and effective solutions",
        agent_capabilities=[
            "algorithm design",
            "model development",
            "data analysis",
            "evaluation",
            "multimodal deliverable creation",
        ],
        max_turns=20,  # Allow more turns for complex tasks
        enable_execution_tracing=True,  # Capture detailed execution traces
        use_multimodal_resources=True,  # Enable multimodal inputs
    )

    print("  ✓ Registered agent type: ai")
    print(f"  ✓ Created base worker config: {worker_config.agent_id}")
    print()


    # ============================================================
    # 7. Create pre-execution phase based on mode
    # ============================================================
    print(f"🔧 Step 7: Configuring pre-execution phase (mode={mode})...")

    # Create the appropriate phase based on mode
    pre_execution_phase: RubricExecutionPhaseBase
    
    if mode == "train":
        # Create multi-rubric training phase (generates N synthetic + 1 ground truth)
        pre_execution_phase = MultiRubricTrainingPhase(
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
        print(f"  ✓ Training phase configured: {n_synthetic} synthetic rubrics")
        print(f"  ✓ Total workers per task: {n_synthetic}")
        print("  ✓ Evaluation: All workers evaluated with ground truth rubric")
    
    elif mode == "best_of_n":
        # Best-of-N baseline
        pre_execution_phase = create_baseline_phase(
            baseline="best_of_n",
            n=n_variants,
            base_worker_config=worker_config,
            agent_registry=agent_registry,
            rubric_manager=rubric_manager,
            stakeholder=stakeholder,
            communication_service=communication_service,
            additional_tools=gdpeval_tools,
        )
        print(f"  ✓ Best-of-N baseline configured: {n_variants} variants")
    
    elif mode == "ground_truth":
        # Ground truth baseline
        pre_execution_phase = create_baseline_phase(
            baseline="ground_truth",
            ground_truth_rubric=gt_rubric_spec,
            base_worker_config=worker_config,
            agent_registry=agent_registry,
            rubric_manager=rubric_manager,
            stakeholder=stakeholder,
            communication_service=communication_service,
            additional_tools=gdpeval_tools,
        )
        print("  ✓ Ground truth baseline configured: 1 worker with GT rubric")
    
    elif mode == "trained_policy":
        # Trained policy baseline
        pre_execution_phase = create_baseline_phase(
            baseline="trained_policy",
            base_worker_config=worker_config,
            agent_registry=agent_registry,
            rubric_manager=rubric_manager,
            stakeholder=stakeholder,
            communication_service=communication_service,
            additional_tools=gdpeval_tools,
        )
        print("  ✓ Trained policy baseline configured: 1 worker with policy rubric")
    
    else:
        raise ValueError(f"Unknown mode: {mode}")
    
    print()

    # ============================================================
    # 8. Create NoOp manager for main execution
    # ============================================================
    print("🔧 Step 8: Creating NoOp manager for main execution...")

    execution_manager = create_manager_agent(
        preferences=PreferenceSnapshot(preferences=[]),
        manager_mode="noop",
    )

    print("  ✓ Execution manager: NoOp (no intervention)")
    print()

    # ============================================================
    # 9. Create and run engine with pre-execution phase
    # ============================================================
    print("🔧 Step 9: Creating workflow engine...")
    print()

    engine = WorkflowExecutionEngine(
        workflow=workflow,
        agent_registry=agent_registry,
        stakeholder_agent=stakeholder,
        manager_agent=execution_manager,
        communication_service=communication_service,
        seed=SEED,
        pre_execution_phases=[
            pre_execution_phase,  # Selected phase based on mode
        ],
        gold_rubrics=[gt_rubric_executable],  # GDPEval gold standard for evaluation
        max_timesteps=10,
        enable_timestep_logging=False,  # Disable for cleaner output
        enable_final_metrics_logging=True,
    )

    print(
        f"  ✓ Engine configured with {len(engine.pre_execution_phases)} pre-execution phase(s)"
    )
    print()

    print("=" * 80)
    print("🚀 Starting Execution")
    print("=" * 80)
    print()
    if mode == "train":
        print("Multi-Rubric Training Phase...")
    else:
        print(f"Baseline Phase: {mode}...")
    print("-" * 80)

    await engine.run_full_execution()

    print()
    print("=" * 80)
    print("✅ Execution Complete")
    print("=" * 80)
    print()

    # ============================================================
    # 9. Display Gold Standard Evaluation Results
    # ============================================================
    if hasattr(workflow, "metadata") and workflow.metadata and "gold_evaluation_results" in workflow.metadata:
        print("🏆 Gold Standard Evaluation (GDPEval)")
        print("=" * 80)
        print()
        
        gold_results = workflow.metadata["gold_evaluation_results"]
        for category_name, result in gold_results.items():
            print(f"Category: {category_name}")
            print("-" * 80)
            print(f"  Total Score: {result['total_score']:.2f} / {result['max_score']:.2f}")
            print(f"  Normalized: {result['normalized_score']:.2%}")
            print(f"  Stages Evaluated: {result['stages_evaluated']}")
            print(f"  Stages Passed: {result['stages_passed']}")
            
            if result.get('failed_gate'):
                print(f"  ❌ Failed Gate: {result['failed_gate']}")
                print(f"  ⚠️  Evaluation stopped at: {result['stopped_at']}")
            else:
                print(f"  ✅ All required gates passed!")
            
            print()
        
        print("=" * 80)
        print()

    # ============================================================
    # 10. Display results
    # ============================================================
    print("📊 Results Summary")
    print("=" * 80)
    print()

    # Show rubric generation results
    print("Rubric Generation:")
    print("-" * 80)
    if stakeholder.generated_rubrics:
        rubric = stakeholder.generated_rubrics[0]
        print(f"  ✓ Generated rubric: {rubric.name}")
        print(f"  ✓ Number of criteria: {len(rubric.criteria)}")
        print("  ✓ Criteria names:")
        for criterion in rubric.criteria:
            print(f"    - {criterion.name}")
    else:
        print("  ⚠️  No rubric generated")
    print()

    # Show task execution results using new TaskExecution model
    completed_task = workflow.tasks[gdpeval_task.id]
    print("Task Execution:")
    print("-" * 80)
    print(f"  Task: {completed_task.name}")
    print(f"  Status: {completed_task.status.value}")

    # Get all executions for this task
    executions = completed_task.get_executions(workflow)
    if executions:
        completed_executions = [ex for ex in executions if ex.is_completed()]
        print(
            f"  Variants executed: {len(completed_executions)}/{len(executions)}"
        )
    print()

    # Show ranking results using new TaskExecution model
    if executions:
        # Get ranked executions (sorted by rank)
        ranked_executions = [ex for ex in executions if ex.rank is not None]
        ranked_executions.sort(key=lambda ex: ex.rank if ex.rank is not None else float('inf'))
        
        if ranked_executions:
            print("Output Rankings:")
            print("-" * 80)
            print(f"  Total outputs evaluated: {len(ranked_executions)}")
            print()

            for execution in ranked_executions[:3]:  # Show top 3
                print(f"  Rank {execution.rank}:")
                print(f"    Score: {execution.aggregate_score:.2f}/10" if execution.aggregate_score else "    Score: N/A")
                print(f"    Agent: {execution.agent_id}")
                
                # Show all resources produced by this execution
                if execution.output_resource_ids:
                    print(f"    Resources produced: {len(execution.output_resource_ids)}")
                    for resource_id in execution.output_resource_ids[:3]:  # Show first 3
                        resource = workflow.resources.get(resource_id)
                        if resource:
                            print(f"      - {resource.name}")
                            print(f"        Path: {resource.file_path}")
                            print(f"        MIME: {resource.mime_type}")
                            print(f"        Size: {resource.size_bytes} bytes")

                            # Check if file exists and show content type
                            if hasattr(resource, "is_spreadsheet") and resource.is_spreadsheet:
                                print("        Type: Excel file")
                                if resource.file_format_metadata:
                                    print(f"        Metadata: {resource.file_format_metadata}")
                            elif hasattr(resource, "is_text_format") and resource.is_text_format:
                                print("        Type: Text file")
                                # Try to show preview
                                try:
                                    preview = resource.load_text()[:200]
                                    if len(resource.load_text()) > 200:
                                        preview += "..."
                                    print(f"        Preview: {preview}")
                                except Exception as e:
                                    print(f"        (Could not preview: {e})")

                # Show evaluation details
                if execution.evaluation_details and "reasoning" in execution.evaluation_details:
                    print(f"    Evaluation: {execution.evaluation_details['reasoning']}")

                print()

            # Show selection results using best execution
            best_execution = completed_task.get_best_execution(workflow)
            print("Output Selection:")
            print("-" * 80)
            if best_execution:
                print(
                    f"  ✓ Selected: Rank {best_execution.rank} (score: {best_execution.aggregate_score:.2f}/10)"
                )
                print(f"  ✓ Agent: {best_execution.agent_id}")
                print(f"  ✓ Resources: {len(best_execution.output_resource_ids)}")
                print("  ✓ Ready for propagation to downstream tasks")
            else:
                print(f"  ℹ️  All {len(completed_task.output_resource_ids)} outputs selected")
        else:
            print("⚠️  No ranked executions found")
    else:
        print("⚠️  No executions found")

    print()
    print("=" * 80)
    print("✅ Smoke Test Complete!")
    print("=" * 80)
    print()
    print("This example demonstrated:")
    print("  ✓ Rubric generation via manager-stakeholder dialogue")
    print("  ✓ Multi-agent task assignment (N variants)")
    print("  ✓ Parallel execution of N workers")
    print("  ✓ Rubric-based evaluation of outputs")
    print("  ✓ Ranking and selection of best output")
    print("  ✓ Full result serialization")
    print()
    print(
        f"Check output files for detailed results in: {engine.output_writer.output_config.workflow_dir}"
    )
    print("=" * 80)

    # ============================================================
    # 10. Analyze multimodal outputs (Phase 2 validation)
    # ============================================================
    print()
    print("=" * 80)
    print("📁 Phase 2 Multimodal Output Analysis")
    print("=" * 80)
    print()
    print("Analyzing all generated files to validate Phase 2 implementation...")
    print()

    # Collect all output resources
    all_resources = list(workflow.resources.values())
    output_resources = [
        r for r in all_resources if r.id != input_resource.id
    ]  # Exclude input

    print(f"Total resources in workflow: {len(all_resources)}")
    print("Input resources: 1 (customer_data.xlsx)")
    print(f"Output resources: {len(output_resources)}")
    print()

    # Analyze by type
    excel_outputs = [
        r for r in output_resources if hasattr(r, "is_spreadsheet") and r.is_spreadsheet
    ]
    text_outputs = [
        r for r in output_resources if hasattr(r, "is_text_format") and r.is_text_format
    ]

    print("Outputs by type:")
    print(f"  📊 Excel files: {len(excel_outputs)}")
    print(f"  📝 Text/Markdown files: {len(text_outputs)}")
    print()

    # Detailed analysis of each output type
    if excel_outputs:
        print("Excel File Analysis:")
        print("-" * 80)
        for resource in excel_outputs[:3]:  # Show first 3
            print(f"  File: {Path(resource.file_path).name}")
            print(f"    Path: {resource.file_path}")
            print(f"    Size: {resource.size_bytes:,} bytes")
            if resource.file_format_metadata:
                print(
                    f"    Sheets: {resource.file_format_metadata.get('sheet_names', 'N/A')}"
                )
                print(
                    f"    Rows: {resource.file_format_metadata.get('num_rows', 'N/A')}"
                )

            # Verify file exists
            if Path(resource.file_path).exists():
                print("    ✓ File exists on disk")

                # Try to read Excel content
                try:
                    import pandas as pd

                    xls = pd.ExcelFile(resource.file_path)
                    print(f"    ✓ File is valid Excel ({len(xls.sheet_names)} sheets)")
                    for sheet in xls.sheet_names:
                        df = pd.read_excel(xls, sheet_name=sheet)
                        print(
                            f"      - Sheet '{sheet}': {len(df)} rows × {len(df.columns)} columns"
                        )
                except Exception as e:
                    print(f"    ✗ Could not read Excel: {e}")
            else:
                print("    ✗ File does not exist!")
            print()

    if text_outputs:
        print("Text/Markdown File Analysis:")
        print("-" * 80)
        for resource in text_outputs[:3]:  # Show first 3
            print(f"  File: {Path(resource.file_path).name}")
            print(f"    Path: {resource.file_path}")
            print(f"    Size: {resource.size_bytes:,} bytes")

            # Verify file exists
            if Path(resource.file_path).exists():
                print("    ✓ File exists on disk")

                # Try to read text content
                try:
                    text = resource.load_text()
                    print(f"    ✓ File is valid text ({len(text)} characters)")

                    # Show first 200 chars
                    preview = text[:200].replace("\n", " ")
                    if len(text) > 200:
                        preview += "..."
                    print(f"    Preview: {preview}")
                except Exception as e:
                    print(f"    ✗ Could not read text: {e}")
            else:
                print("    ✗ File does not exist!")
            print()

    # Validation summary
    print("=" * 80)
    print("✅ Phase 2 Validation Summary")
    print("=" * 80)

    validation_checks = []

    # Check 1: Workers created file-based outputs
    if len(output_resources) > 0:
        validation_checks.append(("✓", "Workers created file-based outputs"))
    else:
        validation_checks.append(("✗", "No output resources created"))

    # Check 2: Excel files were created
    if len(excel_outputs) > 0:
        validation_checks.append(
            ("✓", f"Excel outputs created ({len(excel_outputs)} files)")
        )
    else:
        validation_checks.append(("✗", "No Excel outputs created"))

    # Check 3: Text/Markdown files were created
    if len(text_outputs) > 0:
        validation_checks.append(
            ("✓", f"Text/Markdown outputs created ({len(text_outputs)} files)")
        )
    else:
        validation_checks.append(("✗", "No text outputs created"))

    # Check 4: Files exist on disk
    existing_files = sum(1 for r in output_resources if Path(r.file_path).exists())
    if existing_files == len(output_resources):
        validation_checks.append(
            ("✓", f"All {existing_files} output files exist on disk")
        )
    else:
        validation_checks.append(
            ("⚠", f"Only {existing_files}/{len(output_resources)} files exist")
        )

    # Check 5: Resources have proper metadata
    with_metadata = sum(1 for r in output_resources if r.file_format_metadata)
    if with_metadata > 0:
        validation_checks.append(
            ("✓", f"{with_metadata}/{len(output_resources)} resources have metadata")
        )
    else:
        validation_checks.append(("✗", "No resources have metadata"))

    print()
    for symbol, message in validation_checks:
        print(f"  {symbol} {message}")

    print()
    print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Multi-agent ML task with rubric generation (training and baselines)"
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["train", "best_of_n", "ground_truth", "trained_policy"],
        default="train",
        help="Execution mode: train (GRPO training), or baseline (best_of_n, ground_truth, trained_policy)"
    )
    parser.add_argument(
        "--n-synthetic",
        type=int,
        default=2,
        help="Number of synthetic rubrics for training mode (default: 2)"
    )
    parser.add_argument(
        "--n",
        type=int,
        default=8,
        help="Number of variants for best_of_n baseline (default: 10)"
    )
    
    args = parser.parse_args()
    
    asyncio.run(run_multi_agent_ml_example(
        mode=args.mode,
        n_synthetic=args.n_synthetic,
        n_variants=args.n,
    ))
