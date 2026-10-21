#!/usr/bin/env bash
# Run one workflow with one manager mode, then analyse the run. One place for the settings, so
# the run and its analysis always point at the same folder.
#
#   scripts/run.sh [all|run|eval]
#
#   scripts/run.sh                 run then analyse (default)
#   scripts/run.sh eval            analyse an existing run only (free: reads files, no API calls)
#   scripts/run.sh run             run only (no analysis)
#   NUM_SEEDS=5 scripts/run.sh     5 seeds (SEED, SEED+1, ...); `eval` scores every seed
#   STAGE=eval scripts/run.sh      same, from the environment
#   EVAL_MODES="cot random" scripts/run.sh eval   compare several modes that were already run
#
# Stages: `run` calls the OpenAI API (manager gpt-5-mini). `eval` only reads and writes files:
# run summaries (analyze_runs.py). `all` runs `run` and then `eval`, and skips `eval` if `run` fails.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# EDIT THESE
STAGE="${STAGE:-all}"          # all, run, eval

for arg in "$@"; do
  case "$arg" in
    all|run|eval) STAGE="$arg" ;;
    *) echo "usage: scripts/run.sh [all|run|eval]" >&2; exit 1 ;;
  esac
done
case "$STAGE" in all|run|eval) ;; *) echo "STAGE must be 'all', 'run' or 'eval', got '$STAGE'" >&2; exit 1 ;; esac

# EDIT THESE
WORKFLOWS="legal_m_and_a" # legal_m_and_a, marketing_campaign, orsa
MODE=cot                  # random, cot, assign_all
SEED=42
NUM_SEEDS="${NUM_SEEDS:-1}"       # seeds run: SEED, SEED+1, ...
EVAL_MODES="${EVAL_MODES:-$MODE}" # modes to analyse; defaults to the mode that was run
LABELS="$WORKFLOWS"

if [ "$STAGE" = "all" ] || [ "$STAGE" = "run" ]; then
  uv run python examples/run_examples.py \
    --num-seeds "$NUM_SEEDS" \
    --workflow_name $WORKFLOWS \
    --manager-agent-mode "$MODE" \
    --model-name gpt-5-mini \
    --output-dir "dashboard/outputs/$MODE" \
    --seed "$SEED"
fi

if [ "$STAGE" = "all" ] || [ "$STAGE" = "eval" ]; then
  for ((i = 0; i < NUM_SEEDS; i++)); do
    seed=$((SEED + i))
    uv run python dashboard/analysis/analyze_runs.py \
      --workflow $LABELS \
      --mode $EVAL_MODES \
      --seed "$seed"
  done
fi
