# CLAUDE.md

## Project: adaptive replanning for manager agents under unexpected external team changes

Direction is set by `research/Project Proposal.pdf`; the specification of record is `research/decisions.md` (D15 to D19). Summary:

- **Question:** when an agent becomes unexpectedly unavailable (outage, rate limit, permanent deprecation), when do rule-based approaches suffice, and when is a
  manager or replanning policy needed? Either outcome is a finding.
- **Sub-questions:** (1) does telling the manager in its prompt suffice, or does an explicit continue/repair/replan policy improve recovery; (2) how does recovery
  change with the share of affected tasks that have an equivalent remaining agent (none to all); (3) at what cost (tokens, time, unnecessary reassignments).
- **Contributions:** a benchmark whose change processes are grounded in public incident and release records; possibly a continue/repair/replan policy manager.
- **Fixed:** task goals and requirements, accurately declared capabilities. **Varied:** change type and duration, substitute availability, what the manager is told
  (unannounced signals; informed as the upper bound), workflow size and depth. **Out of scope:** error recovery, task and preference drift, changing requirements, joins,
  deployment-performance claims. Specialised agents are an assumption, not a claim about industry practice.
- **Benchmarks are grounded in real-world scenarios** (documented deployments, public incident and release records), not MA-Gym's example workflows (`decisions.md` D20). The experiment types are in `research/preregistration.md` (E0 to E7).
- The earlier join/leave "team non-stationarity" direction is **removed**.

Three components, each with one home. Do not create a fourth place for any of them.

| Component | Code | Converted data | Docs | UPDATES.md table |
|---|---|---|---|---|
| **Benchmark**: scenarios, events, workers, checklists | `manager_agent_gym/specialist_loss/` (`events`, `engine`, `worker`, `scenario`, `family`) | `examples/specialist_loss/<workflow>/` | `research/decisions.md` | Benchmark |
| **Metric**: scoring, analysis, validation | `specialist_loss/scoring.py`, `analysis.py`, `thresholds.py`; `tests/specialist_loss/` | n/a | `research/preregistration.md` | Metric |
| **Manager agent**: how it is run, informed, compared | `specialist_loss/managers.py`, `runner.py`, `phase2_stub.py`; the notice block in `structured_manager.py` | n/a | `research/decisions.md` | Manager agent |

Status (2026-10-21): the first Phase 1 implementation (benchmark, metrics, baselines, validation) is **no longer in the working tree**; `decisions.md` and `preregistration.md`
keep its design as the specification, and `decisions.md` D17 lists how it falls short of the proposal. Every path below is the planned layout until it is rebuilt; check that a file
exists before relying on it, and do not write benchmark code unless asked. The LLM diagnostic waits for the
user's "go" (then write `research/diagnostic_report.md` and stop again). Phase 2 (the LLM manager) is a stub until the user confirms the verdict.

## Where things live

- **Benchmarks are saved in `examples/specialist_loss/<workflow>/`**, in the original MA-Gym layout (`workflow.py`, `team.py`,
  `team_change_spec.py`, `preferences.py`, `__init__.py`, `CONVERSION.md`), loaded by `examples.scenarios.get_scenario("<workflow>_team")`.
  Variants are factory arguments: `create_team_change_spec(roster, event_type, timing)`. Nothing converted goes anywhere else.
- Each package's `.conversion/` holds the LLM conversion cache (`family.json`, `llm_cache/`, `log.json`). The package files are **generated** from it
  by `scripts/specialist_loss/generate_packages.py`: never hand-edit them; change the conversion or the generator and regenerate.
- `research/decisions.md` (design decisions and Step 0 findings) and `research/preregistration.md` (thresholds, grid, decision rule) are the only
  docs for this work. **Edit them; do not add new documents.** Record a new decision as a new `D<n>` in `decisions.md`.
- **All project specs and research notes live in `research/`** (the proposal, `decisions.md`, `preregistration.md`, `problem.md`); `docs/` is the original MA-Gym documentation site. `CLAUDE.md` stays at the repo root because Claude Code only loads it from there.
- Commands: `DEV.md`. Running record of changes: `UPDATES.md`. Dashboard features: `dashboard/FEATURES.md`.

## Keep things in step (maintenance)

- **`UPDATES.md`**: whenever you add, change or remove an update (code, scripts, docs, dashboard, a revert), edit it in the same turn, before
  reporting the work done. Three tables: **Manager agent**, **Benchmark**, **Metric** (rows marked "Specialist loss" are the current direction; unmarked
  rows are the shelved join/leave work). Each row: Update, Files (link files that exist), Purpose, Status (`Done` or `Planned`). Removed work: delete the
  row. Built planned work: `Planned` to `Done`. Verify a row against the working tree (`git diff`) before writing it.
- **Thresholds have one source**: `specialist_loss/thresholds.py`, mirrored in `research/preregistration.md`; `tests/specialist_loss/test_preregistration.py`
  fails if they disagree. Change both, and add a dated amendment to the preregistration after the go.
- **Shared MA-Gym code is edited only additively**, with the new path inert by default, so existing managers and benchmarks behave as before.
  Prove it with a test (`test_new_hooks_are_inert_by_default`) and keep the whole suite green: `uv run pytest tests -q`.
- A failing scenario gate (`tests/specialist_loss/test_validation.py`) means the **scenario** is broken, not the manager: fix or drop the scenario.
- Dashboard: `dashboard/` only reads existing files under `dashboard/outputs/` (override `$MAG_OUTPUTS_DIR`). Keep `dashboard/FEATURES.md` in
  sync the same way as `UPDATES.md`.

## Never spend money without an explicit ask in the user's current message

Not `scripts/specialist_loss/run_grid.py --enable-llm`, not `scripts/specialist_loss/convert_workflows.py` (cheap OpenAI calls), not `scripts/run.sh`,
`scripts/run_all.sh` or `examples/run_examples.py`. Scripted and rule-based managers, tests, the analysis script and `estimate_cost.py` are free.
`runner.build_manager` refuses `cot` and `assign_all` unless `allow_llm=True`; tests mock the model.

## Claude skill and agent

- `/create-benchmark <workflow>` (or `scripts/create_benchmark.sh`): converts a workflow into its adaptive-replanning package (dry-run, convert on
  request, generate, validate, `UPDATES.md` row). It never runs an LLM manager and does not edit the preregistered grid
  (`WORKFLOWS` in `specialist_loss/family.py`): adding a workflow changes the preregistration, so the user decides.
- `problem-checker` agent: fact-checks `research/problem.md` against prior work and, if `research/inputs.md` exists, the preregistration and
  diagnostic report. Keep its input paths current if those docs move.
- If you change the skill, the agent, `decisions.md` or `preregistration.md`, say which other files now disagree.

## Removed: team-membership (join/leave) benchmark

The join/leave scenario, its docs, roster-change log, static-roster loader and `create-team-benchmark` tooling were removed (2026-10-21). The code is otherwise upstream MA-Gym plus: the ML-050/052/053 fixes, task checklists
(`TaskRequirement`) with the post-change and disruption metrics, a no-LLM-judge option, a manager context log, and the dashboard and run scripts. Ask before adding back anything join/leave.
