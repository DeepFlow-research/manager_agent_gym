"""
Batch evaluate worker outputs with synthetic rubrics for calibration analysis.

This script:
1. Loads saved rubrics and worker outputs from a training run
2. Re-evaluates each output with its guiding synthetic rubric
3. Computes calibration metrics (correlation between synthetic and ground truth scores)
4. Generates calibration matrix for plotting

Usage:
    # Single run
    python -m examples.research.batch_evaluate_calibration simulation_outputs/run_20251025_124534/
    
    # Multiple runs (batch)
    python -m examples.research.batch_evaluate_calibration simulation_outputs/run_*/
    
    # With visualization
    python -m examples.research.batch_evaluate_calibration simulation_outputs/run_*/ --plot
"""

import argparse
import asyncio
import json
import logging
from pathlib import Path
from typing import Any
import numpy as np
from scipy.stats import pearsonr, spearmanr  # type: ignore[import-untyped]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def load_run_data(run_dir: Path) -> dict[str, Any]:
    """Load all data needed for re-evaluation from a training run."""
    
    manifest_path = run_dir / "evaluation_outputs/calibration_data/re_evaluation_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    # Load rubrics
    rubrics = {}
    for rubric_type, rel_path in manifest["rubric_paths"].items():
        rubric_path = run_dir / rel_path
        with open(rubric_path) as f:
            rubrics[rubric_type] = json.load(f)
    
    # Load ground truth evaluations
    eval_results_path = run_dir / f"evaluation_outputs/evaluation_results_{manifest['run_id']}.json"
    with open(eval_results_path) as f:
        eval_results = json.load(f)
    
    return {
        "manifest": manifest,
        "rubrics": rubrics,
        "ground_truth_evaluations": eval_results.get("grpo_training_data", {}),
        "run_dir": run_dir,
    }


async def evaluate_with_synthetic_rubric(
    run_data: dict,
    execution_id: str,
    rubric_type: str,
) -> dict:
    """
    Re-evaluate a worker output using a synthetic rubric.
    
    This recreates the ValidationEngine context and runs evaluation.
    """
    from manager_agent_gym.core.evaluation.engine.validation_engine import ValidationEngine
    from manager_agent_gym.schemas.preferences.evaluation import StagedRubric
    from manager_agent_gym.schemas.domain.workflow import Workflow
    from manager_agent_gym.schemas.domain.task_execution import TaskExecution
    from manager_agent_gym.schemas.domain.resource import Resource
    
    # Load rubric
    rubric_data = run_data["rubrics"][rubric_type]
    rubric = StagedRubric(**rubric_data["full_rubric"])
    
    # Load execution metadata
    exec_metadata_path = run_data["run_dir"] / f"evaluation_outputs/worker_outputs/execution_{execution_id}/metadata.json"
    with open(exec_metadata_path) as f:
        exec_metadata = json.load(f)
    
    # Reconstruct resources
    resources = []
    exec_dir = exec_metadata_path.parent
    for res_data in exec_metadata["resources"]:
        resource_path = exec_dir / res_data["local_path"]
        resources.append(Resource(
            id=res_data["resource_id"],
            name=res_data["name"],
            description="",  # Not needed for evaluation
            file_path=str(resource_path),
            mime_type=res_data["mime_type"],
            size_bytes=res_data["size_bytes"],
            resource_role=res_data["role"],
        ))
    
    # Create minimal workflow context for evaluation
    # Note: This is simplified - in production you'd reconstruct full workflow
    from manager_agent_gym.schemas.domain.task import Task
    from uuid import UUID
    
    task = Task(
        id=UUID(exec_metadata["task_id"]),
        name=exec_metadata["task_name"],
        description="",  # Not needed for evaluation
    )
    
    execution = TaskExecution(
        id=UUID(execution_id),
        task_id=task.id,
        agent_id=exec_metadata["agent_id"],
        variant_index=exec_metadata["variant_index"],
    )
    
    # Create minimal workflow
    from uuid import uuid4
    workflow = Workflow(
        id=UUID(run_data["manifest"]["workflow_id"]),
        name=run_data["manifest"]["workflow_name"],
        workflow_goal="",  # Not needed
        owner_id=uuid4(),  # Not needed for evaluation
    )
    workflow.tasks[task.id] = task
    
    # Add resources to workflow
    for resource in resources:
        workflow.resources[resource.id] = resource
    
    # Run evaluation
    validation_engine = ValidationEngine(seed=42)
    
    # Evaluate with synthetic rubric
    result = await validation_engine.evaluate_execution_with_staged_rubrics(
        workflow=workflow,
        execution=execution,
        timestep=0,
        staged_rubrics=[rubric],
        communications=None,
        manager_actions=None,
    )
    
    return {
        "execution_id": execution_id,
        "rubric_type": rubric_type,
        "result": result[rubric.category_name].model_dump(mode="json"),
    }


async def compute_calibration_matrix(run_dir: Path) -> dict:
    """
    Compute full calibration matrix for a training run.
    
    For each execution:
    - Load ground truth evaluation (already computed)
    - Re-evaluate with its guiding synthetic rubric
    - Compute calibration metrics
    """
    logger.info(f"Loading run data from {run_dir}")
    run_data = await load_run_data(run_dir)
    
    manifest = run_data["manifest"]
    gt_evals = run_data["ground_truth_evaluations"]
    
    evaluation_matrix = []
    synthetic_scores = []
    ground_truth_scores = []
    
    # Process each execution
    for exec_id, exec_meta in manifest["execution_metadata"].items():
        rubric_type = exec_meta["guided_by_rubric_type"]
        
        # Get ground truth evaluation
        gt_eval = None
        for task_data in gt_evals.get("per_task_metrics", {}).values():
            for execution in task_data.get("executions", []):
                if execution["execution_id"] == exec_id:
                    gt_eval = execution
                    break
        
        if not gt_eval:
            logger.warning(f"No ground truth evaluation found for {exec_id}")
            continue
        
        # Re-evaluate with synthetic rubric
        logger.info(f"Evaluating {exec_id} with {rubric_type}")
        synthetic_eval = await evaluate_with_synthetic_rubric(
            run_data, exec_id, rubric_type
        )
        
        # Extract scores
        gt_score = gt_eval["aggregate_score"]
        synthetic_score = synthetic_eval["result"]["normalized_score"]
        
        synthetic_scores.append(synthetic_score)
        ground_truth_scores.append(gt_score)
        
        evaluation_matrix.append({
            "execution_id": exec_id,
            "variant_index": exec_meta["variant_index"],
            "guided_by_rubric": {
                "rubric_type": rubric_type,
                "generation_seed": exec_meta["generation_seed"],
            },
            "ground_truth_evaluation": {
                "aggregate_score": gt_score,
                "full_result": gt_eval,
            },
            "synthetic_rubric_evaluation": {
                "aggregate_score": synthetic_score,
                "full_result": synthetic_eval["result"],
            },
        })
    
    # Compute calibration metrics
    synthetic_arr = np.array(synthetic_scores)
    gt_arr = np.array(ground_truth_scores)
    
    pearson_r, pearson_p = pearsonr(synthetic_arr, gt_arr)
    spearman_r, spearman_p = spearmanr(synthetic_arr, gt_arr)
    
    mae = np.mean(np.abs(synthetic_arr - gt_arr))
    mse = np.mean((synthetic_arr - gt_arr) ** 2)
    bias = np.mean(synthetic_arr - gt_arr)
    
    calibration_matrix = {
        "run_id": manifest["run_id"],
        "timestamp": manifest["timestamp"],
        "workflow_id": manifest["workflow_id"],
        "evaluation_matrix": evaluation_matrix,
        "calibration_metrics": {
            "pearson_correlation": float(pearson_r),
            "pearson_p_value": float(pearson_p),
            "spearman_correlation": float(spearman_r),
            "spearman_p_value": float(spearman_p),
            "mean_absolute_error": float(mae),
            "mean_squared_error": float(mse),
            "synthetic_overestimation_bias": float(bias),
            "num_samples": len(synthetic_scores),
        },
        "score_pairs": {
            "synthetic": synthetic_scores,
            "ground_truth": ground_truth_scores,
        },
    }
    
    # Save calibration matrix
    output_path = run_dir / "evaluation_outputs/calibration_data/calibration_matrix.json"
    with open(output_path, "w") as f:
        json.dump(calibration_matrix, f, indent=2, default=str)
    
    logger.info(f"✅ Saved calibration matrix: {output_path}")
    logger.info(f"   Pearson r = {pearson_r:.3f} (p={pearson_p:.4f})")
    logger.info(f"   Spearman r = {spearman_r:.3f} (p={spearman_p:.4f})")
    logger.info(f"   MAE = {mae:.3f}, Bias = {bias:.3f}")
    
    return calibration_matrix


def plot_calibration(calibration_matrices: list[dict], output_path: Path):
    """Generate calibration scatter plot."""
    import matplotlib.pyplot as plt
    
    fig, ax = plt.subplots(figsize=(8, 8))
    
    # Aggregate all score pairs
    all_synthetic = []
    all_ground_truth = []
    
    for matrix in calibration_matrices:
        all_synthetic.extend(matrix["score_pairs"]["synthetic"])
        all_ground_truth.extend(matrix["score_pairs"]["ground_truth"])
    
    # Scatter plot
    ax.scatter(all_ground_truth, all_synthetic, alpha=0.6, s=50)
    
    # Perfect calibration line
    ax.plot([0, 1], [0, 1], 'r--', label='Perfect Calibration', linewidth=2)
    
    # Compute overall correlation
    pearson_r, _ = pearsonr(all_synthetic, all_ground_truth)
    
    ax.set_xlabel('Ground Truth Score', fontsize=12)
    ax.set_ylabel('Synthetic Rubric Score', fontsize=12)
    ax.set_title(f'Rubric Calibration (r={pearson_r:.3f}, n={len(all_synthetic)})', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    logger.info(f"✅ Saved calibration plot: {output_path}")


async def main():
    parser = argparse.ArgumentParser(description="Batch evaluate calibration")
    parser.add_argument("run_dirs", nargs="+", help="Training run directories")
    parser.add_argument("--plot", action="store_true", help="Generate calibration plot")
    parser.add_argument("--output", default="calibration_scatter.png", help="Plot output path")
    
    args = parser.parse_args()
    
    # Process all runs
    calibration_matrices = []
    for run_pattern in args.run_dirs:
        run_paths = list(Path(".").glob(run_pattern))
        
        for run_dir in run_paths:
            if not run_dir.is_dir():
                continue
            
            try:
                matrix = await compute_calibration_matrix(run_dir)
                calibration_matrices.append(matrix)
            except Exception as e:
                logger.error(f"Failed to process {run_dir}: {e}")
    
    logger.info(f"\n✅ Processed {len(calibration_matrices)} runs")
    
    # Generate plot if requested
    if args.plot and calibration_matrices:
        plot_calibration(calibration_matrices, Path(args.output))


if __name__ == "__main__":
    asyncio.run(main())

