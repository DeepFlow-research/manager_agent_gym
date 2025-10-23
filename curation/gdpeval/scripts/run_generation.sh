#!/bin/bash
set -e

echo "🚀 Starting GDPEval rubric generation pipeline"

cd "$(dirname "$0")/.."

# 1. Download data if not exists
if [ ! -f "data/raw/gdpeval.parquet" ]; then
    echo "📥 Downloading GDPEval dataset..."
    python -m curation.gdpeval.src.download
fi

# 2. Generate rubrics
echo "🎯 Generating rubrics for all tasks..."
python -m curation.gdpeval.src.generate_rubrics --model gpt-4o --seed 42 --max-concurrent 10

echo ""
echo "✅ Generation complete!"
echo "📊 Review rubrics at: data/generated/staged_v1/staged_rubrics.jsonl"
echo "👉 Next step: ./scripts/run_app.sh"

