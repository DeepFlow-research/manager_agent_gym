"""
Loader for GDPEval sample data (task + rubric + reference files).

This module provides utilities to load a single GDPEval sample for development
and testing, including the task description, reference files, and ground truth rubric.
"""

import json
from pathlib import Path
from typing import Any

import pandas as pd

from manager_agent_gym.core.agents.manager_agent.implementations.rubric_generation_manager.rubric_generation import (
    ManagerAgentGeneratedStagedRubric,
)


def load_first_gdpeval_sample(
    gdpeval_data_dir: Path | None = None,
) -> dict[str, Any]:
    """Load the first GDPEval sample for development.
    
    Returns task description, reference files, and ground truth rubric for the
    first task in the GDPEval dataset.
    
    Args:
        gdpeval_data_dir: Path to curation/gdpeval/data directory.
                         If None, attempts to find it relative to this file.
    
    Returns:
        Dictionary with keys:
            - task_id: str
            - task_name: str
            - task_description: str
            - reference_files: list[Path] (paths to input files)
            - rubric_spec: ManagerAgentGeneratedStagedRubric (gold standard)
            - category_name: str
            - max_score: float
    
    Example:
        >>> sample = load_first_gdpeval_sample()
        >>> print(sample["task_name"])
        >>> rubric = sample["rubric_spec"]
        >>> print(f"Evaluating: {rubric.category_name}")
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
    
    # Load rubrics JSONL
    rubrics_path = gdpeval_data_dir / "generated" / "staged_v4" / "staged_rubrics.jsonl"
    if not rubrics_path.exists():
        raise FileNotFoundError(f"Rubrics file not found: {rubrics_path}")
    
    # Load tasks parquet
    tasks_path = gdpeval_data_dir / "raw" / "gdpeval.parquet"
    if not tasks_path.exists():
        raise FileNotFoundError(f"Tasks file not found: {tasks_path}")
    
    # Load first rubric
    with open(rubrics_path, "r") as f:
        first_line = f.readline()
        rubric_data = json.loads(first_line)
    
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
    ref_files_dir = gdpeval_data_dir / "raw" / "reference_files"
    
    if "reference_files" in task_row and isinstance(task_row["reference_files"], list):
        for ref_file in task_row["reference_files"]:
            # Reference files are stored with task_id prefix
            file_path = ref_files_dir / f"{task_id}_{ref_file}"
            if file_path.exists():
                reference_files.append(file_path)
            else:
                # Try without prefix (some files may not have it)
                file_path = ref_files_dir / ref_file
                if file_path.exists():
                    reference_files.append(file_path)
    
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
        # Store full row for any additional metadata
        "_raw_task_data": task_row.to_dict(),
    }


def print_sample_summary(sample: dict[str, Any]) -> None:
    """Print a summary of a loaded GDPEval sample.
    
    Args:
        sample: Dictionary returned from load_first_gdpeval_sample()
    """
    print("=" * 80)
    print("GDPEval Sample Loaded")
    print("=" * 80)
    print()
    print(f"Task ID: {sample['task_id']}")
    print(f"Task Name: {sample['task_name']}")
    print()
    print("Task Description:")
    print("-" * 80)
    desc = sample['task_description']
    if len(desc) > 300:
        desc = desc[:300] + "..."
    print(desc)
    print()
    print(f"Reference Files: {len(sample['reference_files'])} files")
    for ref_file in sample['reference_files']:
        print(f"  - {ref_file.name}")
    print()
    print(f"Gold Rubric: {sample['category_name']}")
    print(f"  Max Score: {sample['max_score']}")
    print(f"  Stages: {sample['num_stages']}")
    
    rubric = sample['rubric_spec']
    for i, stage in enumerate(rubric.stages, 1):
        gate_marker = "🚪 GATE" if stage.is_required else "  "
        print(f"    {gate_marker} Stage {i}: {stage.name}")
        print(f"         {len(stage.rules)} rules, max {stage.max_points} pts")
        if stage.is_required:
            print(f"         Must score {stage.min_score_to_pass:.0%} to continue")
    
    print()
    print("=" * 80)


if __name__ == "__main__":
    # Test the loader
    sample = load_first_gdpeval_sample()
    print_sample_summary(sample)

