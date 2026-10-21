#!/usr/bin/env bash
# Diagnostic suite: team-based non-stationarity / open ad-hoc teamwork.
#
# Runs the 3 churn-heavy scenarios (legal_m_and_a, marketing_campaign, orsa) 
# against the 3 baseline manager modes (cot, random, assign_all) using gpt-5-mini via 
# OpenAI, with a fixed seed for cross-condition comparability.
#
# All team timelines already exist in the scenario modules
# (examples/end_to_end_examples/<scenario>/team.py) via create_team_timeline(),
# so no new team-composition code is required — this script only drives
# examples/run_examples.py, which already wires create_team_timeline() output
# into AgentRegistry.schedule_agent_add/remove().
#
# Benchmark choice (first argument or BENCHMARK=...):
#   original (default): the 3 scenarios above x cot, random, assign_all, from examples/end_to_end_examples
#
# Usage:
#   OPENAI_API_KEY=sk-... ./scripts/run_all.sh [original]
# or populate .env at repo root with OPENAI_API_KEY=... beforehand.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

BENCHMARK="${1:-${BENCHMARK:-original}}"
case "$BENCHMARK" in
  original) WORKFLOWS=(legal_m_and_a marketing_campaign orsa); MODES=(cot random assign_all); LABEL_SUFFIX="" ;;
  *) echo "BENCHMARK must be 'original' (no team scenarios remain), got '$BENCHMARK'" >&2; exit 1 ;;
esac
MODEL_NAME="gpt-5-mini"
SEED=42
MAX_TIMESTEPS="${MAX_TIMESTEPS:-}"   # leave empty to use each scenario's natural length / default (50)
OUT_ROOT="dashboard/outputs"

if [[ -z "${OPENAI_API_KEY:-}" ]] && ! grep -q '^OPENAI_API_KEY=.\+' .env 2>/dev/null; then
  echo "ERROR: OPENAI_API_KEY is not set (env var) and .env has no non-empty OPENAI_API_KEY=... entry." >&2
  echo "Set it before running, e.g.: export OPENAI_API_KEY=sk-..." >&2
  exit 1
fi

mkdir -p "$OUT_ROOT/logs"

TIMESTEP_ARGS=()
if [[ -n "$MAX_TIMESTEPS" ]]; then
  TIMESTEP_ARGS=(--max-timesteps "$MAX_TIMESTEPS")
fi

for mode in "${MODES[@]}"; do
  for wf in "${WORKFLOWS[@]}"; do
    echo "==== workflow=$wf manager_mode=$mode model=$MODEL_NAME seed=$SEED ===="
    RUN_DIR="$OUT_ROOT/$mode/${wf}${LABEL_SUFFIX}/run_seed_$SEED"
    if [[ -d "$RUN_DIR" ]]; then
      echo "Clearing existing run directory: $RUN_DIR"
      rm -rf "$RUN_DIR"
    fi
    LOG_FILE="$OUT_ROOT/logs/${wf}${LABEL_SUFFIX}__${mode}.log"
    uv run python examples/run_examples.py \
      --workflow_name "$wf" \
      --manager-agent-mode "$mode" \
      --model-name "$MODEL_NAME" \
      --output-dir "$OUT_ROOT/$mode" \
      --seed "$SEED" \
      "${TIMESTEP_ARGS[@]+"${TIMESTEP_ARGS[@]}"}" \
      2>&1 | tee "$LOG_FILE"
  done
done

echo
echo "All $(( ${#WORKFLOWS[@]} * ${#MODES[@]} )) runs complete. Outputs under: $OUT_ROOT/<manager_mode>/<workflow_name>/run_<timestamp>/"
echo "Next: scripts/eval.sh"
