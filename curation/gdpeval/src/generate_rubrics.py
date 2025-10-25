"""Batch generate staged rubrics for GDPEval tasks."""

import asyncio
import json
from pathlib import Path
from tqdm.asyncio import tqdm_asyncio
import pandas as pd
from staged_rubric_generator import (
    generate_staged_rubric_v3 as generate_staged_rubric,
)
from dotenv import load_dotenv
import argparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


async def generate_all_staged_rubrics(
    dataset_path: Path | None = None,
    output_dir: Path | None = None,
    model: str = "gpt-5",
    seed: int = 42,
    max_concurrent: int = 10,
    limit: int | None = None,
):
    """Generate staged rubrics for all tasks with concurrency control."""

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
        return 0

    # Semaphore for concurrency control
    semaphore = asyncio.Semaphore(max_concurrent)

    async def generate_with_semaphore(row):
        """Generate rubric with concurrency limiting."""
        async with semaphore:
            try:
                # Get reference file URLs
                reference_file_urls = row.get("reference_file_urls", [])
                if not isinstance(reference_file_urls, list):
                    reference_file_urls = []

                rubric = await generate_staged_rubric(
                    task_id=row["task_id"],
                    sector=row["sector"],
                    occupation=row["occupation"],
                    prompt=row["prompt"],
                    reference_file_urls=reference_file_urls,
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
    parser.add_argument("--version", default="staged_v4", help="Output version")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of tasks")
    args = parser.parse_args()

    output_dir = Path(__file__).parent.parent / "data" / "generated" / args.version

    asyncio.run(
        generate_all_staged_rubrics(
            output_dir=output_dir,
            model=args.model,
            seed=args.seed,
            max_concurrent=args.max_concurrent,
            limit=args.limit,
        )
    )
