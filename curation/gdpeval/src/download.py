"""Download GDPEval dataset and reference files from HuggingFace."""

from pathlib import Path
from datasets import load_dataset
import requests
from tqdm import tqdm
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def download_gdpeval(output_dir: Path | None = None):
    """Download GDPEval dataset from HuggingFace.

    Downloads:
    - Main dataset (220 tasks)
    - Reference files for each task
    - Saves metadata as JSON

    Args:
        output_dir: Output directory (default: datasets/gdpeval/data/raw)
    """
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "data" / "raw"

    output_dir.mkdir(parents=True, exist_ok=True)

    # Load dataset
    logger.info("Loading GDPEval dataset from HuggingFace...")
    dataset = load_dataset("openai/gdpval", split="train")

    # Save as parquet
    dataset.to_parquet(str(output_dir / "gdpeval.parquet"))  # type: ignore
    logger.info(f"✓ Saved dataset to {output_dir / 'gdpeval.parquet'}")

    # Download reference files
    ref_dir = output_dir / "reference_files"
    ref_dir.mkdir(exist_ok=True)

    logger.info("Downloading reference files...")
    for idx, row in enumerate(tqdm(dataset, desc="Downloading files")):
        row_dict: dict = row  # type: ignore
        task_id = row_dict["task_id"]
        task_dir = ref_dir / task_id
        task_dir.mkdir(exist_ok=True)

        # Download each reference file
        for file_url in row_dict.get("reference_file_urls", []):
            if not file_url:
                continue
            try:
                filename = Path(file_url).name
                file_path = task_dir / filename

                # Skip if already downloaded
                if file_path.exists():
                    continue

                response = requests.get(file_url, timeout=30)
                response.raise_for_status()

                with open(file_path, "wb") as f:
                    f.write(response.content)
            except Exception as e:
                logger.warning(f"Failed to download {file_url}: {e}")

    # Save metadata
    metadata = []
    for row in dataset:
        row_dict: dict = row  # type: ignore
        metadata.append(
            {
                "task_id": row_dict["task_id"],
                "sector": row_dict["sector"],
                "occupation": row_dict["occupation"],
                "prompt": row_dict["prompt"],
                "num_reference_files": len(row_dict.get("reference_file_urls", [])),
            }
        )

    with open(output_dir / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"✓ Downloaded {len(metadata)} tasks")
    logger.info(f"✓ Metadata saved to {output_dir / 'metadata.json'}")

    return dataset


if __name__ == "__main__":
    download_gdpeval()
