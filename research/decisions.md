# Decisions: adaptive replanning for manager agents under unexpected external team changes

Status: the implementation described in Step 0 and the decisions below is no longer in the working tree; read them as the specification.
Source of direction: [`Project Proposal.pdf`](Project%20Proposal.pdf) (FYP plan). Phase 1 of it: prove the problem is meaningful
before building a manager. Branch `adaptive-replanning-specialist-loss`. Code:
`manager_agent_gym/specialist_loss/`; scenarios:
`examples/specialist_loss/<workflow>/`; scripts: `scripts/specialist_loss/`;
tests: `tests/specialist_loss/`. Thresholds and the decision rule:
[`preregistration.md`](preregistration.md). Labels: **Verified** (I read the code), **Inferred** (reasoned from it).

## Alignment with the Project Proposal

Updated 2026-10-21 from [`Project Proposal.pdf`](Project%20Proposal.pdf). Specifications only: nothing below changes code.

**D15. Research question, scope, contributions.**
- *Question*: under unexpected external team changes (an agent becomes unavailable), when do rule-based approaches suffice, and when is a manager or replanning policy needed? Either outcome is a finding.
- *Sub-questions*: (1) does telling the manager about the change in its prompt suffice, or does an explicit continue/repair/replan **policy** improve recovery; (2) how does recovery change with the **share of affected tasks that have an equivalent remaining agent** (none to all); (3) at what cost (tokens, time, unnecessary reassignments).
- *Contributions*: (1) a benchmark whose change processes are grounded in public incident and release records, gated tasks, recovery measured directly; (2) potentially, an explicit continue/repair/replan policy manager.
- *Fixed*: task goals and requirements, accurately declared capabilities. *Varied*: change type and duration (outage, rate limit, permanent deprecation), substitute availability, what the manager is told, workflow size and dependency depth.
- *Out of scope*: error recovery, task and preference drift, changing requirements, joins, deployment-performance claims. Specialised agents are an explicit assumption (realistic, but their prevalence in production is unproven), not a claim about industry practice.
- *Hypothesis*: without an explicit policy a manager stalls on the change (under-reacts) or restarts work it did not need to (over-reacts); the right decision is structural, since what to keep, repair or redo depends on which tasks depend on the lost agent.

**D16. Systems under test** (target): do nothing (`ignore_change`); rule-based router with ordered fallbacks (`chain`, `routing`); MA-Gym `random`, `cot`, `assign_all`; **prompt-informed** manager (a plain LLM manager told what changed); **policy-based** manager (explicit continue/repair/replan rule over the dependency structure). Measures: post-change score on affected tasks, disruption cost, tokens and time, partial completion.

**D17. What the first Phase 1 build covered against that target.** Its code, scripts, tests and converted workflows are no longer in the working tree (2026-10-21); this table is what a rebuild must at least match, and the gaps it must close.

| Proposal element | Current build | Status |
|---|---|---|
| Post-change score, disruption cost, deterministic checklists, counterfactual runs (the controls) | Built (D7, D12) | Covered |
| Do nothing, rule-based router, `cot`, `assign_all` | Was built (`ignore_change`, `chain`, `routing`, `reassign_all`, `cot`, `assign_all`) | Covered |
| MA-Gym `random` manager | Not in the grid | Gap |
| Prompt-informed vs policy manager | `cot` with the availability notice is the prompt-informed manager; the policy manager is the Phase 2 stub | Policy: not built |
| Share of affected tasks with a substitute, swept from none to all | Two points only: no substitute, and one substitute that covers 3 of 4 items of both affected tasks (D4) | Gap |
| Unannounced changes (timeouts, errors, degraded outputs), informed condition as an upper bound | Only the informed condition (D5): the manager is told | Gap |
| Change type and duration sampled from public incident and release records | Hand-authored: outage for the rest of the run, rate limit resetting on the last step | Gap |
| Workflow size and dependency depth as parameters | Three fixed workflows (9, 9 and 16 tasks, depth 5 to 8) | Gap |
| Time and partial completion as measures | Per-step score exists (partial completion); wall time is not scored; tokens and cost are | Partial |
| Structured trace of change events, decisions, affected tasks, why each task passed or failed | The run record holds actions and per-task state; no explanation per task | Partial |
| Change-event schema (timestamp, agent, event type, duration, announced) serving public records and developer logs | `AvailabilityEvent` has agent, kind, start, duration; no `announced` field, no import path | Gap |
| Deterministic worker mode for core tests | Built (D6) | Covered |
| Long horizon only as a parameter | Horizon is derived from the task count (D5) | Partial |
| Log import (replay mode) | Not planned; a later stretch | Out for now |

**D18. Order of the remaining specification work** (from the proposal's Dev Work): the change-event schema first (add `announced`; one schema for public records and developer logs), then the grounded-benchmark research (SWE-bench, VitaBench, MCPEvol-Bench as models for turning real data into test cases), then the substitute-share sweep and the unannounced condition, then the policy manager. Each is a `Planned` row in `UPDATES.md`. Until they exist, the Phase 1 diagnostic, once rebuilt, answers sub-question 3 and a coarse version of sub-question 2, and **does not** answer sub-question 1 or the unannounced-change question; reports must say so.

**D19. Open concerns the proposal records** (carry into the report, do not resolve by wording): demand for manager-style solutions is unclear, and AWS guidance both lists hard-coded orchestration as a common problem and recommends deterministic capability routing and ordered fallbacks (so rules may suffice where a substitute exists); how often no fallback exists in real systems is unevidenced; the benchmark must treat changes as unannounced or a reviewer will ask how it differs from MA-Gym's scripted leaves.

**D20. Benchmarks are grounded in real-world scenarios, not MA-Gym's workflows** (2026-10-21, user decision). MA-Gym stays as the engine, action space and source of the Random, CoT and
Assign-All managers; its example workflows are no longer converted. Scenarios come from documented deployments and public incident and release records, as `preregistration.md` specifies, and
the experiment types there (E0 to E7) replace the fixed grid. This **supersedes D3** (the three converted workflows), **D12** (the 30-scenario grid) and **D14** (conversion of MA-Gym workflows by an LLM);
D4, D5, D7 and D8 describe the earlier prototype's mechanics and remain useful design notes (event semantics, checklist scoring, scripted managers and gates) until the grounded build restates them.

## Step 0: what the existing code does

### Fixes the study depends on

| Fix | Status in the tree | Gap |
|---|---|---|
| ML-050: a completed task is not marked FAILED with score 0 | Present. `AIAgent._calculate_accurate_cost` ([`ai_agent.py:216`](../manager_agent_gym/core/workflow_agents/ai_agent.py)) catches any pricing failure and returns 0.0. Test: `tests/test_ai_agent_cost.py`, and `test_a_completed_task_is_not_marked_failed...` | None. Not exercised here: workers are scripted, so no LLM call prices a task. |
| ML-052: reassignments are applied properly | Present but **opt-in**. `apply_assignment` ([`manager_actions.py:114`](../manager_agent_gym/schemas/execution/manager_actions.py)) cancels and restarts a RUNNING task and rejects COMPLETED, FAILED and composite tasks only when `Workflow.strict_assignment` is on (engine arg `restart_on_reassign`, off by default). The runner turns it on. | `AssignAllPendingTasksAction` still bypasses `apply_assignment` (it only skips composites in strict mode). With strict mode off the original benchmark keeps the legacy behaviour, as intended. |
| ML-053: the manager is told when an action is rejected | Present but **only for `cot`, and only with `team_awareness=True`**. The engine puts the failure cause in the `ActionResult`, and `ChainOfThoughtManagerAgent._prepare_context` ([`structured_manager.py:262`](../manager_agent_gym/core/manager_agent/structured_manager.py)) renders `[FAILED] - Cause: ...`. The runner turns it on. Test: `test_cot_is_told_of_the_event_the_reset_time_and_why_its_assignment_was_rejected`. | `assign_all` never reads its action history, so it is not told. It acts once, so there is nothing to learn from. |

I fixed nothing in Step 0: all three exist. I did not widen them to the original benchmark, because the brief says not to alter existing managers.

### Worker join and leave events

Verified. `AgentRegistry.schedule_agent_add/remove(timestep, ...)` ([`registry.py:192`](../manager_agent_gym/core/workflow_agents/registry.py))
store changes by timestep. `WorkflowExecutionEngine._check_and_apply_agent_changes`
([`engine.py:1085`](../manager_agent_gym/core/execution/engine.py)) runs at the start of `execute_timestep`, before the manager acts, calls
`apply_scheduled_changes_for_timestep` once per timestep, mirrors the registry into `workflow.agents`, and prunes mirrored agents that left.
A join creates a new `AIAgent` (an LLM agent). A leave deletes the agent from the registry and the workflow; its running task is not
cancelled, and a task still assigned to it never starts (the engine looks the agent up and skips the task when it is gone). Every change is
appended to `registry.change_log`, which the manager sees only with `team_awareness=True`.
**Neither is an outage or a rate limit**: a leaver is gone for good and nothing returns. The study therefore adds its own availability events
(D5) and keeps the worker on the roster, flagged unavailable. Joins and leaves are out of scope.

### Is `_seed` used?

Verified, by call site:

| Component | Uses the seed? |
|---|---|
| `cot` manager | Yes. `generate_structured_response(seed=self._seed)` sends it as the OpenAI `seed`, which is best-effort. `temperature` is the function default **1**, so runs still vary. |
| `assign_all` manager | Same call, same seed. |
| Worker LLM calls (`AIAgent.execute_task`) | **No.** `_seed` is stored by `configure_seed` and never passed to `Runner.run` (ML-092 confirmed). |
| Stakeholder | Its `random.Random` is seeded and drives reply latency and pushes. Its one LLM call (`execute_task`) is unseeded. `policy_step` makes no LLM call. |
| Judge / rubrics | Yes, `ValidationEngine(seed=...)` passes it. |
| Decomposition | **Mismatch.** `decompose_task` passes `workflow.seed` ([`manager_actions.py:1050`](../manager_agent_gym/schemas/execution/manager_actions.py)). The field's comment says the engine sets it, but nothing does, so it is always 42 and ignores the run seed. |

Consequence: the only run-to-run variance in this study is the manager's, as the brief wants, because workers are scripted (D6) and the
stakeholder is static. Seeds affect only the LLM managers, and only weakly. Scripted and rule-based runs are deterministic, so they run once.

### How scoring is done in MA-Gym

Verified. The original benchmark scores a run with `ValidationEngine.evaluate_timestep`
([`validation_engine.py`](../manager_agent_gym/core/evaluation/validation_engine.py)): preference rubrics and workflow evaluators, some
LLM-judged and some code, aggregated per timestep into a reward vector by a `BaseRewardAggregator`. `skip_llm_judge` drops the LLM-judged
rubrics. This study needs none of it. Its metrics are deterministic checklists computed post hoc from the run record
(`specialist_loss/scoring.py`), as the existing team-membership metrics are (`team_change_metrics.py`, which I reuse the idea of, not the code).

### Documentation versus behaviour

1. `Workflow.seed`: documented as set by the engine; it is never set (above).
2. `create_manager_agent(..., manager_mode="assign_all")` ignores `model_name`; `OneShotDelegateManagerAgent` always uses its default, `o3`.
   The study's cost estimate prices `assign_all` at o3 accordingly.
3. `AIAgent`'s "seed" plumbing (`configure_seed`) reads as if it makes workers deterministic. It does not.
4. `CreateTaskAction` and `RemoveTaskAction` mutate `workflow.tasks` without fixing dependants: removing a task leaves its dependants waiting
   forever. The engine here prunes such dependencies (D5); the standard engine does not.

## Decisions

**D1. Scope.** Phase 1 only. No manager is built, no LLM diagnostic is run. Existing managers, the original benchmark and the team-membership
benchmark are unchanged; every engine hook I added is inert unless a specialist-loss scenario turns it on (tests:
`test_new_hooks_are_inert_by_default`, `test_other_managers_get_no_availability_notices`, and the full existing suite, 172 tests, still passes).

**D2. Where things live.** Each workflow is a scenario package in the original layout, `examples/specialist_loss/<workflow>/` (`workflow.py`,
`team.py`, `team_change_spec.py`, `preferences.py`, `__init__.py`, `CONVERSION.md`, as the original MA-Gym scenarios have), loaded by `get_scenario("<workflow>_team")`.
Variants are factory arguments: `create_team_change_spec(roster, event_type, timing)` returns the scenario (events, affected tasks, hidden labels and chains,
oracle actions); no event type is the control. The packages are generated from the conversion output by `scripts/specialist_loss/generate_packages.py` and
are what runs read (`Family.load`); `examples/specialist_loss/<workflow>/.conversion/` (`family.json`, `llm_cache/`, `log.json`) is only the conversion cache. Under `run_examples.py` a package loads as a
static LLM roster with no events; events and scripted workers run only through `scripts/specialist_loss/run_grid.py`. The library is a new package,
`manager_agent_gym/specialist_loss/`, not edits to the team benchmark. Additive edits to shared code, each defaulting to off:
`Workflow.unavailable_agents` (empty), a rejection branch in `apply_assignment` and `AssignAllPendingTasksAction`, a `_can_start` hook in the engine
(always True), `AvailabilityNotice` and `ManagerObservation.availability_notices` (empty), a notice block in the `cot` prompt (renders only when
non-empty), and an optional `UsageTracker` around `generate_structured_response`.

**D3. Workflows.** *Superseded by D20.* `airline_launch_program` (9 tasks, depth 5, 13 dependencies: dense convergence), `ipo_readiness_program` (9 tasks, depth 6: two
branches joining at the end) and `supply_chain_planning` (16 tasks, depth 8: a wide fan-out then a chain). Chosen for different graph shapes and
modest size, since an LLM manager gets one action per step (ML-049) and cost scales with steps. I **flatten** each to its top-level tasks (each
becomes one atomic task, dependencies kept): the sources nest several subtasks per task, which would triple the steps and make assignment, not
replanning, the bottleneck. The target pair must be a task at depth 3 or more and a later task that depends on it, with something downstream.

**D4. No exact equivalent; partial substitution.** Every task has exactly one worker that can produce all of its four checklist items (tests:
`test_no_agent_has_an_equivalent`). In the *partial* roster one adjacent worker (chosen by the LLM as nearest in expertise) can produce the first
three, the basic ones, of each target task. In the *none* roster it can produce none. "Splitting" a task is not credited as more than the
substitute can do: a scripted worker can only deliver items its labels cover, so splitting between workers yields their union, which is still
three items. LLM managers that `decompose_task` are scored by rolling up their leaf subtasks. Consequence for the verdict: even a perfect repair
scores (3 + 2) / 6 = 0.83 on a target task, an unavoidable drop of 0.17. The preregistered drop is the brief's; I also report the oracle's.

**D5. Events.** Applied at the start of timestep `start`, before the manager acts.
- *Outage*: unavailable from `start` for the rest of the run. Running tasks are lost: they return to READY (`restart_count` + 1) and start fresh if run again.
- *Rate limit*: no new work until it resets at `start + duration`. In-flight tasks complete. **My reading**: "accepts no new assignments" also holds
  tasks that are assigned but not started, otherwise an upfront-assigning manager is never affected and the event does nothing.
- The manager is told by an `AvailabilityNotice` in its observation (the `cot` prompt renders it), by the worker leaving the available-agents list,
  and by a rejection that names the cause. A rate limit notice states the reset step. Notices name the worker and the effect, never a task or a substitute.
- *Timing*: early = step 1, before the target's first task starts. Mid = the step that task is in flight (its depth, 3 or more). These are set from the
  nominal schedule (assign everything at t=0, one step per dependency level), so for slower LLM managers "mid" may arrive before the task has started.
- *Reset step*: the **last** step of the horizon. With any earlier reset, doing nothing passes (test `test_a_rate_limit_that_resets_in_time_is_cleared_by_waiting`),
  which fails the gating requirement. So in this grid a rate limit is, for pending tasks, indistinguishable from an outage except that it is announced with a reset
  time and spares in-flight work. Waiting is the correct action only for the in-flight task of a mid rate limit. A regime where a short rate limit should
  simply be waited out is **not covered**; it is the natural extension.
- Removing a task detaches its dependants (the engine prunes dependencies on missing tasks), see Step 0 mismatch 4.
- Horizon = tasks + critical-path depth + 6 (20, 21 and 30 steps).

**D6. Deterministic workers, static stakeholder, no judge.** `ScriptedWorker` writes a templated deliverable: a `PRODUCED_BY` line and one plain sentence per
checklist item its hidden labels cover. No LLM, no randomness. Deliverables use plain sentences, not tags, because the `cot` prompt shows completed
deliverables and a tag would leak the hidden label names (found by a test, fixed). The stakeholder never speaks and its preferences never change; it is
unassignable. No LLM judge runs. The study's worker (GPT-4.1), stakeholder (o3) and judge (o3) models are therefore unused by design (`config.py`).

**D7. Metrics.** Per task, `ITEMS_PER_TASK + 2` = 6 binary checks on the state at a timestep: each of 4 content items present; the producer is on the task's
hidden eligibility chain; every dependency finished before the task did. Score = passed / total; an uncompleted task scores 0. An infeasible task (no worker can
do any of it) that the manager removed scores `DROP_CREDIT`.
- *Post-change score*: mean over the two affected tasks at the end of the run. *Per-step score*: mean over all tasks, and over the affected tasks, at every step.
- *Disruption cost*: of the unaffected tasks unfinished at the event, the share that were moved to another worker, restarted, or removed afterwards. A first
  assignment, or a move before the event, is not disruption.
- *Failure taxonomy*, per run: `assigned_to_unavailable` (a rejected assignment), `stalled` (an affected task left unfinished), `needless_restart` (an unaffected task
  restarted), `over_replanning` (an unaffected task moved or removed, or a repairable affected task removed), `under_repair` (an affected task finished below the
  best achievable score), `dependency_violation` (a task finished before a dependency still in the plan), `premature_termination` (the manager ended the run with work left).
- **`DROP_CREDIT = 1.0` is a judgement, not a measurement.** It says removing work nobody can do, and carrying on, is fully correct. It decides every *none*
  scenario, so the analysis reports the verdict again with `DROP_CREDIT = 0`. Change it in `thresholds.py`.
- Tokens and cost per run come from `UsageTracker` and are stored in each record.

**D8. Scripted managers and gates.** `ignore_change` (assign every task to its nominal worker at t=0, then noop), `oracle` (that, then the documented action per
affected task, one per step), `null` (noop only). Validation (`tests/specialist_loss/test_validation.py`) asserts, for all 30 scenarios: ignore-change <= 0.55 on affected tasks in
every change scenario and >= 0.95 on controls; the starting roster's best cover of an affected task is below full; the oracle reaches >= 95% of the achievable maximum with zero
disruption; the null manager scores <= 0.02 everywhere, controls included. The *mid rate-limit* scenarios sit at 0.50 for ignore-change (the in-flight task completes), under the 0.55
limit; that margin is thin by construction.

**D9. No LLM spend without an explicit flag.** `runner.build_manager` raises `PermissionError` for `cot` and `assign_all` unless `allow_llm=True`; `run_grid.py` needs
`--enable-llm`. No test runs an LLM manager. The conversion script (D14) made 16 cheap calls, as Step 1 asked. `estimate_cost.py` builds the real prompts without calling a model.

**D10. Models.** `config.py`: development default `gpt-5-mini`, preregistered manager `gpt-5`, overridable with `MAG_MODEL_NAME` or `--model`. Conversion model `gpt-4o-mini`
(the account has no `gpt-4.1-mini`, checked with a free model listing); `gpt-5-mini` for the two calls `gpt-4o-mini` failed three times on the 16-task workflow.

**D11. Rule-based baselines** read the hidden labels and chains. `routing`: each unfinished task to the available worker with the best label match, re-checked every step,
running tasks included (so it restarts an in-flight task on a rate limit). `chain`: the first available worker on the task's predefined chain, re-checked every step, but running tasks are left alone.
`reassign_all`: when who is available changes, one bulk assignment of every unfinished task over the remaining roster. None has a "drop" action, so none recovers a *none* scenario.
In this synthetic world the three largely coincide; the differences are running-task handling and latency. Say so if they are reported as three independent baselines.

**D12. Grid.** *Superseded by D20.* Controls are per roster, because the roster differs between partial and none (the substitute's description and labels): 3 workflows x (2 controls + 2 rosters x 2 event types x
2 timings) = 30 scenarios. A control is scored on the same affected pair as the change scenarios of its roster.

**D13. Phase 2** is a stub only (`phase2_stub.py`): an interface and the planned behaviour.

**D14. Conversion.** *Superseded by D20.* `scripts/specialist_loss/convert_workflows.py`: three cached calls per workflow (roster and target/substitute choice, 4-item checklists, can/cannot descriptions), each validated and
retried with the rejection reasons. Event configs, labels, chains, affected tasks and oracle actions are code, not LLM output. The substitute's description in each roster is composed by code from the checklist,
so it says exactly what it can and cannot do of the target's work. After the conversion, `generate_packages.py` (no LLM) writes the packages. Result: **16 LLM calls, 18,372 prompt and 13,531 completion tokens, about $0.02** (each package's `.conversion/log.json`),
including 7 rejected attempts. Every response is cached in `examples/specialist_loss/<workflow>/.conversion/llm_cache/`.

## Limitations to carry into the report

- The build is the informed, hand-authored, two-point-substitute slice of the proposal; see D17 for the gaps.

- A task is one step long, and a manager gets one action per step (ML-049); the horizon is sized for that, and "mid" timing is defined on the scripted schedule.
- The partial-roster drop floor (0.17) and the none-roster `DROP_CREDIT` both come from my design.
- The rate-limit grid is the late-reset regime only (D5).
- Descriptions and checklists are LLM-written by a small model; a manager might not read "can also produce a basic version" as I intend. The family files should be skimmed before the diagnostic.
- `assign_all` runs on o3 whatever the manager model setting.
