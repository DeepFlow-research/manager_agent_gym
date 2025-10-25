"""
Loader for GDPEval sample data (task + rubric + reference files).

This module provides utilities to load a single GDPEval sample for development
and testing, including the task description, reference files, and ground truth rubric.

The loader supports train/eval splits:
- use_train_split=True: Load from train_rubrics.jsonl (175 rubrics, 80%)
- use_train_split=False: Load from eval_rubrics.jsonl (44 rubrics, 20%)
- use_train_split=None: Load from full staged_rubrics.jsonl (219 rubrics)
"""

import json
import random
from pathlib import Path
from typing import Any

import pandas as pd

from manager_agent_gym.core.agents.manager_agent.implementations.rubric_generation_manager.rubric_generation import (
    ManagerAgentGeneratedStagedRubric,
)


def load_gdpeval_sample(
    gdpeval_data_dir: Path | None = None,
    use_train_split: bool | None = None,
    sample_index: int | None = None,
    random_seed: int | None = None,
) -> dict[str, Any]:
    """Load a GDPEval sample for development or training.

    Returns task description, reference files, and ground truth rubric for a
    task in the GDPEval dataset.

    Args:
        gdpeval_data_dir: Path to curation/gdpeval/data directory.
                         If None, attempts to find it relative to this file.
        use_train_split: Which data split to use:
                         - True: Load from train_rubrics.jsonl (175 rubrics, 80%)
                         - False: Load from eval_rubrics.jsonl (44 rubrics, 20%)
                         - None: Load from full staged_rubrics.jsonl (219 rubrics)
        sample_index: Index of sample to load (0-based). If None and random_seed is None,
                     loads first sample. If None and random_seed is set, loads random sample.
        random_seed: Random seed for reproducible random sampling. If set, ignores sample_index
                    and selects a random sample from the chosen split.

    Returns:
        Dictionary with keys:
            - task_id: str
            - task_name: str
            - task_description: str
            - reference_files: list[Path] (paths to input files)
            - rubric_spec: ManagerAgentGeneratedStagedRubric (gold standard)
            - category_name: str
            - max_score: float
            - split: str ("train", "eval", or "full")
            - sample_index: int (actual index used)

    Example:
        >>> # Load first sample from training set
        >>> sample = load_gdpeval_sample(use_train_split=True)
        
        >>> # Load random sample from eval set with fixed seed
        >>> sample = load_gdpeval_sample(use_train_split=False, random_seed=42)
        
        >>> # Load specific sample from full dataset
        >>> sample = load_gdpeval_sample(use_train_split=None, sample_index=10)
    """
    # Find data directory
    if gdpeval_data_dir is None:
        # Try to find it relative to this file
        this_file = Path(__file__)
        repo_root = this_file.parent.parent.parent.parent.parent
        gdpeval_data_dir = repo_root / "curation" / "gdpeval" / "data"

    if not gdpeval_data_dir.exists():
        raise FileNotFoundError(
            f"GDPEval data directory not found: {gdpeval_data_dir}\n"
            "Please provide the path to curation/gdpeval/data"
        )

    # Determine which rubrics file to load based on split
    if use_train_split is True:
        rubrics_filename = "train_rubrics.jsonl"
        split_name = "train"
    elif use_train_split is False:
        rubrics_filename = "eval_rubrics.jsonl"
        split_name = "eval"
    else:  # None - use full dataset
        rubrics_filename = "staged_rubrics.jsonl"
        split_name = "full"

    rubrics_path = gdpeval_data_dir / "generated" / "staged_v1" / rubrics_filename
    if not rubrics_path.exists():
        raise FileNotFoundError(
            f"Rubrics file not found: {rubrics_path}\n"
            f"Expected split: {split_name}"
        )

    # Load tasks parquet
    tasks_path = gdpeval_data_dir / "raw" / "gdpeval.parquet"
    if not tasks_path.exists():
        raise FileNotFoundError(f"Tasks file not found: {tasks_path}")

    # Load all rubrics from the chosen split
    rubrics = []
    with open(rubrics_path, "r") as f:
        for line in f:
            rubrics.append(json.loads(line.strip()))

    total_samples = len(rubrics)

    # Determine which sample to load
    if random_seed is not None:
        # Random sampling with fixed seed
        rng = random.Random(random_seed)
        actual_index = rng.randint(0, total_samples - 1)
    elif sample_index is not None:
        # Specific index
        if sample_index < 0 or sample_index >= total_samples:
            raise ValueError(
                f"sample_index {sample_index} out of range for {split_name} split "
                f"(0-{total_samples-1})"
            )
        actual_index = sample_index
    else:
        # Default to first sample
        actual_index = 0

    # Load the selected rubric
    rubric_data = rubrics[actual_index]
    task_id = rubric_data["task_id"]
    rubric_spec = ManagerAgentGeneratedStagedRubric(**rubric_data["rubric"])

    # Load tasks dataframe
    tasks_df = pd.read_parquet(tasks_path)

    # Find matching task
    task_row = tasks_df[tasks_df["task_id"] == task_id]
    if task_row.empty:
        raise ValueError(f"Task {task_id} not found in tasks dataset")

    task_row = task_row.iloc[0]

    # Get reference files
    reference_files = []
    ref_files_base_dir = gdpeval_data_dir / "raw"

    if "reference_files" in task_row and task_row["reference_files"] is not None:
        for ref_file in task_row["reference_files"]:
            # Reference files may be stored in several ways due to data evolution
            # Try multiple strategies to find the file

            # Strategy 1: Use path exactly as recorded in parquet
            file_path = ref_files_base_dir / ref_file
            if file_path.exists():
                reference_files.append(file_path)
                continue

            # Strategy 2: Replace any hash directory with task_id
            # Example: 'reference_files/HASH/file.xlsx' -> 'reference_files/task_id/file.xlsx'
            ref_file_path = Path(ref_file)
            if (
                len(ref_file_path.parts) >= 3
                and ref_file_path.parts[0] == "reference_files"
            ):
                # Path has format: reference_files/some_dir/filename
                file_path = (
                    ref_files_base_dir
                    / "reference_files"
                    / task_id
                    / ref_file_path.name
                )
                if file_path.exists():
                    reference_files.append(file_path)
                    continue

            # Strategy 3: Try with task_id prefix (legacy format)
            file_path = (
                ref_files_base_dir
                / "reference_files"
                / f"{task_id}_{ref_file_path.name}"
            )
            if file_path.exists():
                reference_files.append(file_path)
                continue

            # Strategy 4: Try just the filename in reference_files root
            file_path = ref_files_base_dir / "reference_files" / ref_file_path.name
            if file_path.exists():
                reference_files.append(file_path)
                continue

    return {
        "task_id": task_id,
        "task_name": f"{task_row.get('sector', 'Unknown')} - {task_row.get('occupation', 'Unknown')}",
        "task_description": task_row.get("prompt", "No description provided"),
        "sector": task_row.get("sector", "Unknown"),
        "occupation": task_row.get("occupation", "Unknown"),
        "reference_files": reference_files,
        "rubric_spec": rubric_spec,
        "category_name": rubric_spec.category_name,
        "max_score": rubric_spec.max_total_score,
        "num_stages": len(rubric_spec.stages),
        "split": split_name,
        "sample_index": actual_index,
        "total_samples_in_split": total_samples,
        # Store full row for any additional metadata
        "_raw_task_data": task_row.to_dict(),
    }


def load_first_gdpeval_sample(
    gdpeval_data_dir: Path | None = None,
) -> dict[str, Any]:
    """Load the first GDPEval sample (backward compatibility wrapper).
    
    This function maintains backward compatibility with existing code.
    For new code, use load_gdpeval_sample() with explicit split parameters.
    
    Args:
        gdpeval_data_dir: Path to curation/gdpeval/data directory
        
    Returns:
        Dictionary with sample data (loads from full dataset, first sample)
    """
    return load_gdpeval_sample(
        gdpeval_data_dir=gdpeval_data_dir,
        use_train_split=None,
        sample_index=0,
    )


def print_sample_summary(sample: dict[str, Any]) -> None:
    """Print a summary of a loaded GDPEval sample.

    Args:
        sample: Dictionary returned from load_gdpeval_sample()
    """
    print("=" * 80)
    print("GDPEval Sample Loaded")
    print("=" * 80)
    print()
    print(f"Task ID: {sample['task_id']}")
    print(f"Task Name: {sample['task_name']}")
    print(f"Split: {sample.get('split', 'unknown')} ({sample.get('sample_index', 0)}/{sample.get('total_samples_in_split', '?')-1})")
    print()
    print("Task Description:")
    print("-" * 80)
    desc = sample["task_description"]
    if len(desc) > 300:
        desc = desc[:300] + "..."
    print(desc)
    print()
    print(f"Reference Files: {len(sample['reference_files'])} files")
    for ref_file in sample["reference_files"]:
        print(f"  - {ref_file.name}")
    print()
    print(f"Gold Rubric: {sample['category_name']}")
    print(f"  Max Score: {sample['max_score']}")
    print(f"  Stages: {sample['num_stages']}")

    rubric = sample["rubric_spec"]
    for i, stage in enumerate(rubric.stages, 1):
        gate_marker = "🚪 GATE" if stage.is_required else "  "
        print(f"    {gate_marker} Stage {i}: {stage.name}")
        print(f"         {len(stage.rules)} rules, max {stage.max_points} pts")
        if stage.is_required:
            print(f"         Must score {stage.min_score_to_pass:.0%} to continue")

    print()
    print("=" * 80)


if __name__ == "__main__":
    # Test the loader with different split configurations
    print("\n🧪 Testing GDPEval Sample Loader\n")
    
    # Test 1: Load from training split (first sample)
    print("TEST 1: Load first sample from training split")
    print("-" * 80)
    sample = load_gdpeval_sample(use_train_split=True, sample_index=0)
    print_sample_summary(sample)
    
    # Test 2: Load random sample from eval split
    print("\n\nTEST 2: Load random sample from eval split (seed=42)")
    print("-" * 80)
    sample = load_gdpeval_sample(use_train_split=False, random_seed=42)
    print_sample_summary(sample)
    
    # Test 3: Backward compatibility - load first from full dataset
    print("\n\nTEST 3: Backward compatibility test (load_first_gdpeval_sample)")
    print("-" * 80)
    sample = load_first_gdpeval_sample()
    print_sample_summary(sample)
