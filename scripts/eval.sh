#!/usr/bin/env bash
# Analyse existing runs only (reads files, no simulation, no API calls). Same as
# `scripts/run.sh eval`; the settings live in run.sh.
#
#   scripts/eval.sh
#   NUM_SEEDS=5 scripts/eval.sh               score every seed
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/run.sh" "$@" eval
