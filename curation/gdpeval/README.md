# GDPEval Rubric Curation

Generate and curate high-quality evaluation rubrics for GDPEval's 220 real-world professional tasks.

## Overview

This module creates a curated rubric dataset by:
1. Downloading GDPEval from HuggingFace
2. Generating evaluation rubrics using LLMs
3. Providing a Streamlit labeling interface for human review
4. Iteratively refining rubrics based on feedback
5. Exporting the final dataset to HuggingFace Hub

## Quick Start

```bash
# 0. Install curation dependencies
uv sync --group curation

# 1. Download GDPEval dataset
python -m curation.gdpeval.src.download

# 2. Generate rubrics for all 220 tasks
python -m curation.gdpeval.src.generate_rubrics --model gpt-4o

# 3. Start annotation app
streamlit run curation/gdpeval/src/streamlit_app.py

# 4. After annotation, refine rubrics
python -m curation.gdpeval.src.refine_rubrics --original-version v1 --output-version v2

# 5. Export to HuggingFace Hub
python curation/gdpeval/scripts/export_to_hf.py --repo-id yourusername/gdpeval-rubrics
```

## Features

The Streamlit annotation app includes:
- **PDF Preview**: Renders PDF pages inline (first 3 pages)
- **Excel Preview**: Interactive dataframe viewer with sheet selection
- **Word Document Preview**: Extracts and displays text content
- **Image Preview**: Direct display of PNG, JPG, GIF, etc.
- **Local File Links**: Click to open files in your default application
- **Progress Tracking**: See generation and annotation progress
- **Advanced Filtering**: By sector, occupation, and annotation status

## Structure

```
curation/gdpeval/
├── src/
│   ├── download.py              # Download GDPEval
│   ├── rubric_generator.py      # Core generation logic
│   ├── generate_rubrics.py      # Batch generation
│   ├── streamlit_app.py         # Labeling interface
│   └── refine_rubrics.py        # Iterative refinement
├── scripts/
│   └── export_to_hf.py          # Push to HuggingFace
└── data/
    ├── raw/                     # Downloaded GDPEval data
    ├── generated/               # Generated rubrics (v1, v2, final)
    └── feedback/                # Human annotations
```

## Workflow

1. **Download** (~5 min): Fetch GDPEval dataset and reference files
2. **Generate** (~30-60 min): LLM generates rubrics for all tasks
3. **Annotate** (~20-40 hours): Human review and feedback
4. **Refine** (~30-60 min): Regenerate based on feedback
5. **Export** (~5 min): Publish to HuggingFace Hub

## Cost

- Initial generation: ~$22 (220 tasks @ $0.10/task)
- Refinement: ~$11 (50% need revision)
- Total: ~$35 in LLM API costs

## Configuration

Set environment variables:
```bash
export OPENAI_API_KEY=your_key
export HF_TOKEN=your_token
```

Or use `.env` file in the project root.

