---
name: create-benchmark
description: Convert a workflow in examples/end_to_end_examples into an adaptive-replanning benchmark (exogenous outage and rate-limit scenarios) in examples/specialist_loss/<workflow>/, validate it with scripted managers, and keep UPDATES.md and the docs in step. Never runs an LLM manager.
argument-hint: <workflow-name> [--dry-run]
allowed-tools: Read Edit Glob Grep Bash(uv run python scripts/specialist_loss/*) Bash(uv run pytest tests/specialist_loss*)
---

# Create benchmark: $ARGUMENTS

> **Under revision (decisions.md D20):** benchmarks are now grounded in real-world scenarios and public change records, not converted MA-Gym workflows, so the conversion steps below describe the earlier prototype. Do not run them on `examples/end_to_end_examples` workflows; ask the user how a grounded scenario should be built.
>
> Specification only for now: the `scripts/specialist_loss/` tools and `manager_agent_gym/specialist_loss/` package this skill drives are not in the working tree. If they are missing, stop and say so; do not write them unless asked.

Direction (`research/Project Proposal.pdf`): when an agent becomes unexpectedly unavailable, when do rules suffice and when is a manager or replanning policy
needed. The rules live in `research/decisions.md` (design; D15 to D19 are the proposal's scope and gaps) and `research/preregistration.md` (thresholds, grid); read
the sections you need fresh, refer to them by heading, and if this file and the docs disagree the docs win and you say so.

## Ground rules

- **Never** run `scripts/specialist_loss/run_grid.py --enable-llm`, `scripts/run.sh`, `scripts/run_all.sh` or
  `examples/run_examples.py`. They spend money and need an explicit ask in the user's current message.
- The conversion script makes cheap OpenAI calls (a few cents per workflow). Run it for real only if the user's
  message asks for the conversion; otherwise stop after `--dry-run`.
- Never hand-edit the generated package files (`workflow.py`, `team.py`, `team_change_spec.py`, `preferences.py`,
  `__init__.py`, `CONVERSION.md`, `.generated.json`). Change the conversion or the generator and regenerate.
- Write only inside `examples/specialist_loss/<workflow>/`, plus the `UPDATES.md` row (last step).

## Target spec (from the proposal; the tools do not all implement it yet)

A converted benchmark should support, and the skill must **report as a gap, never fake**, any of these that the tools lack (`decisions.md` D17):
a change-event schema (timestamp, agent, event type, duration, announced) that serves public records and developer logs; change type and duration
(outage, rate limit, permanent deprecation) taken from public records; a substitute share swept from none to all; announced and unannounced conditions
(timeouts, errors, degraded outputs; informed is the upper bound); workflow size and dependency depth as parameters; gated tasks with deterministic
checklists; counterfactual runs (same task, workflow and seed with and without the change); a deterministic worker mode; a structured trace of change events,
decisions, affected tasks and why each task passed or failed; extensibility to new disruption types. Task goals, requirements and declared capabilities stay fixed.

## Steps

1. **Check the source.** `<workflow>` must be a folder in `examples/end_to_end_examples/`. A workflow needs a task at depth 3
   or more with a later dependent that has something downstream (`manager_agent_gym/specialist_loss/graph.py`,
   `target_candidates`); if it has none, say so and stop.
2. **Preview.** `uv run python scripts/specialist_loss/convert_workflows.py --workflows <workflow> --dry-run` prints the
   first prompt and spends nothing. With `--dry-run` in the arguments, stop here.
3. **Convert** (only if asked): `uv run python scripts/specialist_loss/convert_workflows.py --workflows <workflow>`. It writes
   `examples/specialist_loss/<workflow>/.conversion/` (`family.json`, `llm_cache/`, `log.json`) and reports the LLM calls.
4. **Generate the package:** `uv run python scripts/specialist_loss/generate_packages.py --workflows <workflow>` (no LLM).
5. **Skim** `team.py` and `workflow.py`: each description states what the agent can and cannot do, and no two agents are
   interchangeable. Report anything odd; do not edit it.
6. **Validate.** `uv run pytest tests/specialist_loss -q`. A new workflow is not in the preregistered grid
   (`WORKFLOWS` in `manager_agent_gym/specialist_loss/family.py`), so also run the gates on it:
   `uv run python scripts/specialist_loss/run_grid.py --workflows <workflow> --out <scratch dir>` then check ignore-change, oracle and
   null against the `GATE_*` thresholds in `manager_agent_gym/specialist_loss/thresholds.py`. A failing gate means the scenario is
   broken, not the manager: fix or drop the workflow.
7. **Record.** Add or update the Benchmark row in `UPDATES.md`. Adding the workflow to the grid changes the preregistration (scenario
   count, cost): tell the user and let them decide; do not edit `WORKFLOWS` or `research/preregistration.md` yourself.

## Report

The workflow, LLM calls and cost, gate results (numbers), anything skimmed that looked wrong, and what the user must decide.
