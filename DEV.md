# Main commands for developer

> The specialist-loss scripts and tests below are the planned commands; that implementation is not in the working tree (see `CLAUDE.md`). Only the shelved and dashboard commands currently exist.

Run from the repo root with `uv run`. Everything under "Free" makes no LLM call.

## Free

```
uv run pytest tests -q                  # whole suite (tests/specialist_loss is the pre-merge validation of the scenarios)
uv run pytest tests/specialist_loss -q  # just the adaptive-replanning benchmark
```

```
uv run python scripts/specialist_loss/run_grid.py                 # scripted + rule-based managers on all 30 scenarios
uv run python scripts/specialist_loss/analyze.py <runs dir>       # tables, verdict, failure taxonomy (reads records only)
uv run python scripts/specialist_loss/estimate_cost.py --manager-model gpt-5   # LLM calls and cost of the diagnostic, no LLM call
```

## Convert a workflow into a benchmark

```
/create-benchmark <workflow>            # in Claude Code; or: bash scripts/create_benchmark.sh <workflow> [--dry-run]
```

or by hand (the conversion step makes cheap OpenAI calls):

```
uv run python scripts/specialist_loss/convert_workflows.py --workflows <workflow> [--dry-run]
uv run python scripts/specialist_loss/generate_packages.py --workflows <workflow>
```

Output: `examples/specialist_loss/<workflow>/`. Never hand-edit the generated files.

## Run the LLM diagnostic (costs money; only after the user's "go")

```
uv run python scripts/specialist_loss/run_grid.py --managers cot assign_all --enable-llm --preregistered --dry-run   # plan only
uv run python scripts/specialist_loss/run_grid.py --managers cot assign_all --enable-llm --preregistered
```

## Run app

```
bash scripts/launch_dashboard.sh
```

## Original MA-Gym benchmark (calls the OpenAI API; the join/leave team scenario was removed)

```
bash scripts/run.sh                     # run and evaluate the original benchmark
bash scripts/eval.sh                    # evaluate only
```
