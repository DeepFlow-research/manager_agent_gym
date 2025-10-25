"""Batch generate staged rubrics for GDPEval tasks."""

import asyncio
import json
from pathlib import Path
from tqdm.asyncio import tqdm_asyncio
import pandas as pd
from curation.gdpeval.src.staged_rubric_generator import (
    generate_staged_rubric_v3 as generate_staged_rubric,
)
from dotenv import load_dotenv
import argparse
import logging
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


def create_train_test_split(
    input_file: Path,
    output_dir: Path,
    train_ratio: float = 0.8,
    seed: int = 42,
):
    """Split rubrics into train and test sets.
    
    Args:
        input_file: Path to the full staged_rubrics.jsonl file
        output_dir: Directory to write train/test splits
        train_ratio: Ratio of data to use for training (default 0.8 = 80%)
        seed: Random seed for reproducibility
    """
    logger.info(f"Creating train/test split from {input_file}")
    
    # Load all rubrics
    rubrics = []
    with open(input_file, "r") as f:
        for line in f:
            rubrics.append(json.loads(line))
    
    total_count = len(rubrics)
    logger.info(f"Loaded {total_count} rubrics")
    
    # Shuffle with fixed seed for reproducibility
    random.seed(seed)
    random.shuffle(rubrics)
    
    # Split
    train_count = int(total_count * train_ratio)
    train_rubrics = rubrics[:train_count]
    eval_rubrics = rubrics[train_count:]
    
    # Write splits
    train_file = output_dir / "train_rubrics.jsonl"
    eval_file = output_dir / "eval_rubrics.jsonl"
    
    with open(train_file, "w") as f:
        for rubric in train_rubrics:
            f.write(json.dumps(rubric) + "\n")
    
    with open(eval_file, "w") as f:
        for rubric in eval_rubrics:
            f.write(json.dumps(rubric) + "\n")
    
    # Write metadata
    metadata = {
        "total_rubrics": total_count,
        "train_count": len(train_rubrics),
        "eval_count": len(eval_rubrics),
        "train_ratio": train_ratio,
        "eval_ratio": len(eval_rubrics) / total_count,
        "seed": seed,
        "source_file": str(input_file.absolute()),
        "train_file": str(train_file.absolute()),
        "eval_file": str(eval_file.absolute()),
    }
    
    metadata_file = output_dir / "split_metadata.json"
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"✓ Train set: {len(train_rubrics)} rubrics → {train_file}")
    logger.info(f"✓ Eval set: {len(eval_rubrics)} rubrics → {eval_file}")
    logger.info(f"✓ Metadata: {metadata_file}")
    
    return metadata


async def generate_all_staged_rubrics(
    dataset_path: Path | None = None,
    output_dir: Path | None = None,
    model: str = "gpt-5",
    seed: int = 42,
    max_concurrent: int = 10,
    limit: int | None = None,
    create_splits: bool = True,
    train_ratio: float = 0.8,
):
    """Generate staged rubrics for all tasks with concurrency control.
    
    Args:
        dataset_path: Path to GDPEval dataset
        output_dir: Directory to save rubrics
        model: LLM model to use
        seed: Random seed for generation and splitting
        max_concurrent: Maximum concurrent API requests
        limit: Limit number of tasks to generate (for debugging)
        create_splits: If True, automatically create train/test splits after generation
        train_ratio: Ratio of data to use for training (default 0.8)
    """

    # Default paths
    if dataset_path is None:
        dataset_path = Path(__file__).parent.parent / "data" / "raw" / "gdpeval.parquet"
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "data" / "generated" / "staged_v1"

    output_dir.mkdir(parents=True, exist_ok=True)

    # Load dataset
    logger.info(f"Loading dataset from {dataset_path}")
    df = pd.read_parquet(dataset_path)
    logger.info(f"Loaded {len(df)} tasks")

    # Check for existing rubrics
    output_file = output_dir / "staged_rubrics.jsonl"
    existing_task_ids = set()
    if output_file.exists():
        with open(output_file, "r") as f:
            for line in f:
                rubric = json.loads(line)
                existing_task_ids.add(rubric["task_id"])
        logger.info(f"Found {len(existing_task_ids)} existing rubrics, skipping...")

    # Filter to unprocessed tasks
    df_todo = df[~df["task_id"].isin(list(existing_task_ids))]

    # Apply limit if specified
    if limit is not None and limit > 0:
        df_todo = df_todo.head(limit)
        logger.info(f"Limiting to first {limit} tasks (for debugging)")

    logger.info(f"Generating staged rubrics for {len(df_todo)} tasks...")

    if len(df_todo) == 0:
        logger.info("All tasks already processed!")
        
        # If no new generation but splits requested, create splits from existing file
        if create_splits and output_file.exists():
            logger.info("Creating train/test splits from existing rubrics...")
            create_train_test_split(
                input_file=output_file,
                output_dir=output_dir,
                train_ratio=train_ratio,
                seed=seed,
            )
        
        return 0

    # Semaphore for concurrency control
    semaphore = asyncio.Semaphore(max_concurrent)

    async def generate_with_semaphore(row):
        """Generate rubric with concurrency limiting."""
        async with semaphore:
            try:
                # Get reference files as list
                reference_files = row.get("reference_files", [])
                if not isinstance(reference_files, list):
                    reference_files = []

                rubric = await generate_staged_rubric(
                    task_id=row["task_id"],
                    sector=row["sector"],
                    occupation=row["occupation"],
                    prompt=row["prompt"],
                    reference_file_urls=reference_files,
                    model=model,
                    seed=seed,
                )

                return rubric
            except Exception as e:
                logger.error(f"Error generating rubric for {row['task_id']}: {e}")
                return None

    # Generate with progress bar
    tasks = [generate_with_semaphore(row) for _, row in df_todo.iterrows()]
    rubrics = await tqdm_asyncio.gather(*tasks, desc="Generating staged rubrics")

    # Save results
    successful = 0
    with open(output_file, "a") as f:
        for rubric in rubrics:
            if rubric:
                f.write(rubric.model_dump_json() + "\n")
                successful += 1

    logger.info(f"✓ Generated {successful}/{len(df_todo)} staged rubrics")
    logger.info(f"✓ Saved to {output_file}")
    
    # Create train/test splits if requested
    if create_splits and output_file.exists():
        logger.info("\nCreating train/test splits...")
        create_train_test_split(
            input_file=output_file,
            output_dir=output_dir,
            train_ratio=train_ratio,
            seed=seed,
        )

    return successful


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate staged rubrics for GDPEval tasks"
    )
    parser.add_argument("--model", default="gpt-5", help="LLM model to use")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument(
        "--max-concurrent", type=int, default=10, help="Max concurrent requests"
    )
    parser.add_argument("--version", default="staged_v1", help="Output version")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of tasks")
    parser.add_argument(
        "--no-splits", 
        action="store_true", 
        help="Skip creating train/test splits"
    )
    parser.add_argument(
        "--train-ratio",
        type=float,
        default=0.8,
        help="Train set ratio (default 0.8 = 80%% train, 20%% test)"
    )
    args = parser.parse_args()

    output_dir = Path(__file__).parent.parent / "data" / "generated" / args.version

    asyncio.run(
        generate_all_staged_rubrics(
            output_dir=output_dir,
            model=args.model,
            seed=args.seed,
            max_concurrent=args.max_concurrent,
            limit=args.limit,
            create_splits=not args.no_splits,
            train_ratio=args.train_ratio,
        )
    )
