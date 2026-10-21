#!/usr/bin/env bash
# Run the create-benchmark skill from the terminal (headless Claude Code).
#
#   scripts/create_benchmark.sh orsa --dry-run   preview the conversion prompt, spend nothing
#   scripts/create_benchmark.sh orsa             convert (cheap OpenAI calls), generate the package, validate
#
# Env: CLAUDE_MODEL=<alias or id>. Never runs an LLM manager. Inside an interactive Claude Code
# session you can run /create-benchmark <workflow> instead.
set -euo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ $# -eq 0 ]; then
  sed -n '2,8p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
  exit 1
fi

# Headless mode does not expand /slash commands, so ask for the skill in words.
claude -p "Use the create-benchmark skill with these arguments: $*. Follow it exactly and end with its report." \
  --permission-mode acceptEdits \
  --allowedTools "Read Edit Glob Grep Bash(uv run python scripts/specialist_loss/*) Bash(uv run pytest tests/specialist_loss*)" \
  ${CLAUDE_MODEL:+--model "$CLAUDE_MODEL"}
