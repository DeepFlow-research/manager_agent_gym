"""Export curated dataset to HuggingFace Hub."""

from typing import TYPE_CHECKING
from pathlib import Path
import json
import pandas as pd
import argparse
import os
from dotenv import load_dotenv

if TYPE_CHECKING:
    import datasets

from datasets import Dataset
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


def prepare_dataset(
    rubrics_file: Path,
    gdpeval_file: Path,
    feedback_file: Path | None = None,
) -> Dataset:
    """Prepare final dataset for HuggingFace.

    Args:
        rubrics_file: Path to final rubrics JSONL
        gdpeval_file: Path to GDPEval parquet
        feedback_file: Optional path to feedback JSONL

    Returns:
        HuggingFace Dataset ready for upload
    """
    logger.info("Loading rubrics...")
    rubrics = []
    with open(rubrics_file, "r") as f:
        for line in f:
            rubrics.append(json.loads(line))
    rubrics_df = pd.DataFrame(rubrics)

    logger.info("Loading GDPEval...")
    gdpeval_df = pd.read_parquet(gdpeval_file)

    # Merge
    logger.info("Merging datasets...")
    merged = gdpeval_df.merge(rubrics_df, on="task_id", how="inner")

    # Add feedback if available
    if feedback_file and feedback_file.exists():
        logger.info("Adding feedback annotations...")
        feedback_df = pd.DataFrame(
            [json.loads(line) for line in open(feedback_file, "r")]
        )
        # Get latest feedback per task
        latest_feedback = feedback_df.sort_values("timestamp").groupby("task_id").last()
        merged = merged.merge(
            latest_feedback[["status", "comments"]],
            on="task_id",
            how="left",
            suffixes=("", "_feedback"),
        )

    logger.info(f"Final dataset size: {len(merged)} tasks")

    # Create HF Dataset
    dataset = Dataset.from_pandas(merged)

    return dataset


def validate_dataset(dataset: Dataset) -> bool:
    """Run quality checks on the dataset.

    Args:
        dataset: Dataset to validate

    Returns:
        True if all checks pass
    """
    logger.info("Running validation checks...")

    # Check size
    assert len(dataset) == 220, f"Expected 220 tasks, got {len(dataset)}"
    logger.info("✓ All 220 tasks present")

    # Check rubric quality
    for row in dataset:
        row_dict: dict = row  # type: ignore
        criteria = row_dict["criteria"]
        assert 3 <= len(criteria) <= 15, (
            f"Task {row_dict['task_id']} has {len(criteria)} criteria"
        )

        total_weight = sum(c["weight"] for c in criteria)
        assert 0.95 <= total_weight <= 1.05, (
            f"Task {row_dict['task_id']} weights sum to {total_weight}"
        )

    logger.info("✓ All rubrics have 3-15 criteria with normalized weights")

    # Check annotation coverage (if feedback exists)
    if "status" in dataset.column_names:
        annotated = sum(1 for row in dataset if dict(row).get("status") is not None)  # type: ignore
        coverage = annotated / len(dataset)
        logger.info(f"✓ Annotation coverage: {coverage:.1%}")

        if coverage < 0.8:
            logger.warning(f"⚠️ Annotation coverage is {coverage:.1%}, recommended >80%")

    logger.info("✅ All validation checks passed!")
    return True


def push_to_hub(
    dataset: "datasets.Dataset",
    repo_id: str,
    token: str,
    private: bool = False,
):
    """Push dataset to HuggingFace Hub.

    Args:
        dataset: Dataset to upload
        repo_id: HuggingFace repo (e.g., username/gdpeval-rubrics)
        token: HuggingFace API token
        private: Whether to make the dataset private
    """
    logger.info(f"Pushing dataset to {repo_id}...")

    dataset.push_to_hub(
        repo_id,
        token=token,
        private=private,
    )

    logger.info(f"✓ Pushed dataset to https://huggingface.co/datasets/{repo_id}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Export curated dataset to HuggingFace Hub"
    )
    parser.add_argument(
        "--rubrics-version",
        default="final",
        help="Rubric version to export (v1, v2, final)",
    )
    parser.add_argument(
        "--repo-id", required=True, help="HF repo (e.g., username/gdpeval-rubrics)"
    )
    parser.add_argument("--private", action="store_true", help="Make dataset private")
    parser.add_argument(
        "--skip-validation", action="store_true", help="Skip validation checks"
    )
    args = parser.parse_args()

    # Paths
    base_dir = Path(__file__).parent.parent
    rubrics_file = (
        base_dir / "data" / "generated" / args.rubrics_version / "rubrics.jsonl"
    )
    gdpeval_file = base_dir / "data" / "raw" / "gdpeval.parquet"
    feedback_file = base_dir / "data" / "feedback" / "feedback.jsonl"

    # Check files exist
    if not rubrics_file.exists():
        logger.error(f"Rubrics file not found: {rubrics_file}")
        exit(1)
    if not gdpeval_file.exists():
        logger.error(f"GDPEval file not found: {gdpeval_file}")
        exit(1)

    # Prepare dataset
    logger.info("Preparing dataset...")
    dataset = prepare_dataset(
        rubrics_file=rubrics_file,
        gdpeval_file=gdpeval_file,
        feedback_file=feedback_file if feedback_file.exists() else None,
    )

    logger.info(f"Dataset columns: {dataset.column_names}")

    # Validate
    if not args.skip_validation:
        validate_dataset(dataset)

    # Push to Hub
    token = os.getenv("HF_TOKEN")
    if not token:
        logger.error("HF_TOKEN not found in environment")
        exit(1)

    push_to_hub(dataset, args.repo_id, token, args.private)
