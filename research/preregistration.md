# Preregistration: when do rules suffice, and when is a manager or replanning policy needed?

Written **before any run**. Specification only: no code, scenario or result exists yet. Companion to [`decisions.md`](decisions.md) (design decisions) and
[`Project Proposal.pdf`](Project%20Proposal.pdf) (direction). Frozen when the user gives the "go"; after that, changes are dated amendments at the bottom.
Values marked **(proposed)** are my defaults for you to confirm before the freeze.

## Question

Under unexpected external team changes (an agent becomes unavailable), when do rule-based approaches suffice, and when is a manager or replanning policy
needed? Either outcome is a finding: if rules suffice, builders can avoid the cost of a manager; if a manager wins, the benchmark locates where.

| ID | Sub-question (from the proposal) |
|---|---|
| Q1 | Does telling the manager about the change in its prompt suffice, or does an explicit continue/repair/replan policy improve recovery? |
| Q2 | How does recovery change with the share of affected tasks that have an equivalent remaining agent (none to all)? Where do rules stop being enough? |
| Q3 | At what cost: tokens, time, unnecessary reassignments? |
| Q0 | (Precondition) Is the problem meaningful: do systems lose much when an agent is lost? |

## The benchmark these experiments run on

The benchmark is **grounded in real-world scenarios**, not in MA-Gym's existing workflows. MA-Gym supplies the manager action space and its three baseline
managers (Random, CoT, Assign-All); the workflows, rosters and changes below are new. Every scenario must satisfy:

- **Grounded source.** A documented real deployment or workflow (public engineering write-ups, vendor reference architectures, open task benchmarks) supplies the task graph and
  agent roles; public incident and release records (provider status pages, API deprecation and release notes, rate-limit documentation) supply the change processes. Each scenario records
  its sources (URL, date, what was taken from it). Specialised agent roles are an **explicit assumption**, not a claim about industry practice.
- **Fixed:** task goals and requirements, accurately declared agent capabilities (each description says what the agent can and cannot do), no preference drift, no joins.
- **Change-event schema** (one schema for public records and developer logs): timestamp, agent, event type (outage, rate limit, permanent deprecation), duration, announced or not.
- **Tasks are gated** with deterministic checklists (content present, produced by an eligible agent, dependencies met), scored at every step. Workers have a deterministic mode, so variance comes from the manager.
- **Counterfactual pair:** the same task, workflow and seed run twice, with and without the change. Unaffected tasks are marked as controls; affected tasks are marked in advance, never derived from a run.
- **Documented best action** for each affected task (continue, repair with a substitute, replan or drop), from the declared capabilities.
- **Validity gates (E0).** Scripted managers only, no LLM spend: *do-nothing* scores low on affected tasks and high on the counterfactual; the *oracle* reaches the best achievable score and leaves unaffected tasks untouched;
  a *null* manager (no-op only) scores about zero everywhere. A failing gate means the **scenario** is broken: fix or drop it, and list every failure and fix in the report.

## Factors

| Factor | Levels |
|---|---|
| Substitute share (fraction of affected tasks with an equivalent remaining agent) | 0, 0.25, 0.5, 0.75, 1.0 (`SUBSTITUTE_SHARES`) |
| Change type | outage, rate limit, permanent deprecation |
| Duration and timing | sampled from the empirical distributions in the public records, plus a small fixed grid (early, mid-run) as a control |
| What the manager is told | informed (upper bound) or unannounced signals only (timeouts, errors, degraded outputs) |
| Workflow size and dependency depth | parameters, stratified (small, medium, large; shallow, deep), taken from documented use cases |
| Horizon | a parameter; typical lengths grounded in documented use cases where possible |

## Systems under test

| ID | System | Notes |
|---|---|---|
| S0 | Do nothing (assigned upfront, never reacts) | The floor |
| S1 | Rule-based router with ordered fallbacks; capability-based routing variant | Read the hidden labels and chains the LLM systems never see |
| S2 | MA-Gym Random, CoT and Assign-All managers, unchanged | CoT and Assign-All are the "existing managers" |
| S3 | Prompt-informed manager | A plain LLM manager told in its prompt what changed |
| S4 | Policy manager | S3 plus an explicit continue/repair/replan rule based on which tasks depended on the lost agent. **Same model, prompt and observation otherwise**, so any difference is the policy |

LLM systems get 5 seeds (`SEEDS`); S0 and S1 and the scripted managers are deterministic and run once. S4 does not exist yet; E4 waits for it.

## Experiment types

| ID | Experiment | Varies | Answers | Needs |
|---|---|---|---|---|
| E0 | Validity gates | none (scripted managers) | whether each scenario is fit to use | the benchmark only |
| E1 | Does losing an agent hurt? | systems S0, S1, S2 on every scenario, informed | Q0 | E0 |
| E2 | Substitute-share sweep | substitute share, at fixed change type and timing | Q2 | E0 |
| E3 | Announcement ablation | informed vs unannounced | what happens when the manager must detect the change | E0 |
| E4 | Prompt vs policy | S3 vs S4, matched | Q1 | the policy manager |
| E5 | Change-process sweep | change type, duration, timing (sampled from records) | whether results depend on how the agent is lost | E0 |
| E6 | Scale sweep | workflow size and dependency depth (and horizon) | whether results hold as dependencies accumulate | E0 |
| E7 | Cost accounting | measured in every experiment | Q3 | none |

E1 gates the others: if E1's verdict is **not meaningful**, stop and report that. Order of work: E0, E1, then E2 and E3, then E5 and E6, then E4 once the policy manager is built.
The scenario count is (grounded cases) x (factor levels) and is fixed at the freeze, when the case list exists; this document does not state it because no cases exist yet.

## Measures

- **Post-change score:** mean checklist score of the affected tasks at the end of the run.
- **Drop** of system *m* on a scenario: (mean post-change score on its counterfactual) minus (mean on the change run), over seeds.
- **Recovery** of system *m*: `(P_m - P_S0) / (P_cf - P_S0)`, where `P` is the mean post-change score and `cf` the counterfactual. Reported per substitute share.
- **Disruption cost:** share of unaffected, unfinished tasks needlessly reassigned, restarted or removed after the event.
- **Cost:** tokens, wall time, LLM calls; **partial completion:** the per-step score curve.
- **Failure taxonomy** (per run): assigned to an unavailable agent, stalled, needless restart, over-replanning, under-repair, dependency violation, premature termination.
- A structured trace per run: change events, manager decisions, affected tasks, and why each task passed or failed.

## Thresholds (single source of truth)

To be mirrored in the code's threshold module when it exists, with a test that fails if the two disagree. Change both and add an amendment.

| Constant | Value | Meaning |
|---|---|---|
| `MEANINGFUL_DROP_MIN` | 0.25 | A scenario "hurts" a system when its drop is at least this, with the CI above zero |
| `NOT_MEANINGFUL_DROP_MAX` | 0.10 | Mean drop below this for both existing managers: not meaningful |
| `SCENARIO_SHARE_MIN` | 0.70 | Share of change scenarios that must hurt, for each existing manager |
| `FAILURE_MODE_SHARE_MIN` | 0.30 | One failure mode must account for at least this share of failures |
| `RULES_SUFFICE_RECOVERY` | 0.90 | (proposed) Rules "suffice" at a substitute share when the best S1 variant scores at least this fraction of its counterfactual |
| `POLICY_GAIN_MIN` | 0.10 | (proposed) S4 must beat S3 by at least this post-change score, with the CI above zero |
| `MANAGER_GAIN_MIN` | 0.10 | (proposed) A manager "wins" over the best S1 variant by at least this post-change score, with the CI above zero |
| `COST_RATIO_MAX` | 5 | (proposed) A win is "worth it" only if the manager's tokens are at most this multiple of the best S1 variant's (S1 uses none, so its cost is the scripted overhead; report the raw tokens too) |
| `CI_LEVEL` | 0.95 | Bootstrap confidence level |
| `BOOTSTRAP_RESAMPLES` | 10000 | Bootstrap draws |
| `SEEDS` | 5 | Seeds per LLM system |
| `SUBSTITUTE_SHARES` | 0, 0.25, 0.5, 0.75, 1.0 | Levels of the substitute-share factor |

Validity gates (not decision thresholds): do-nothing at most 0.55 on affected tasks in a change run and at least 0.95 on its counterfactual; oracle at least 0.95 of the achievable maximum with zero disruption;
null at most 0.02 everywhere.

## Decision rules

Statistics: scenario-level paired comparison against the counterfactual; 95% percentile bootstrap, resampling seeds within a scenario and scenarios within a stratum. Every comparison below is pre-specified; all are reported, none dropped.

1. **Q0, is the problem meaningful (E1).**
   - **NOT MEANINGFUL** if the mean drop is below `NOT_MEANINGFUL_DROP_MAX` for both CoT and Assign-All. Checked first.
   - **MEANINGFUL** if, for both, the share of change scenarios that hurt is at least `SCENARIO_SHARE_MIN`, and the top failure mode's share is at least `FAILURE_MODE_SHARE_MIN`.
   - **INCONCLUSIVE** otherwise.
2. **Q2, where do rules stop being enough (E2).** The crossover is the smallest substitute share at which the best S1 variant reaches `RULES_SUFFICE_RECOVERY`. Report: rules suffice at every share; rules suffice from share *s\** upward (a manager is only needed below *s\**); or rules never suffice.
3. **Q1, prompt vs policy (E4).** S4 beats S3 if the gain is at least `POLICY_GAIN_MIN` with the CI above zero; report per substitute share. If it does not, the policy adds nothing over the prompt.
4. **Manager vs rules.** A manager (S3 or S4) wins at a share if it beats the best S1 variant by `MANAGER_GAIN_MIN`; it is worth it if its token cost is within `COST_RATIO_MAX`. (Q3.)
5. **Announcement (E3):** report each system's loss from informed to unannounced, and its detection delay in steps. No threshold: it measures how far the informed results are an upper bound.
6. **Overall finding, one of:** rules suffice (state where); a manager wins (state where and at what cost); a policy is needed beyond the prompt (state where); or none, with the reasons.

## Grounding protocol

- Inclusion criteria for a source scenario are written before selection: a documented deployment with a stated task graph and agent roles, and incident or release records for at least one of its dependencies.
- For each change process: record the source, extract type, start and duration as stated, mark whether the provider announced it, and never invent a record.
- A scenario with an unverifiable source is excluded, and exclusions are listed. Specialised agents, declared capabilities and any invented parts (for example the substitute assignment) are listed as assumptions in the scenario's provenance.

## What would change my mind

- If E1 passes only because of the scoring (for example a credit for dropping work), re-report E1 with that credit removed; if the verdict changes, it depends on my design and is reported so.
- If a system's drop is explained by the horizon or by its own failures in the counterfactual, the counterfactual is the problem: check counterfactual scores before anything else (below 0.9 for a manager is reported first).
- A failure mode that is a scoring artefact is named as one.

## Cost

Fixed at the freeze, when the case list exists. Planning figures from an earlier prototype: a CoT prompt averaged about 6,200 tokens and CoT makes one call per step, so a run costs roughly (steps) x 6,200 prompt tokens plus output;
Assign-All makes one call. Re-measure on the real scenarios (build the real prompts and count tokens without calling a model) and state calls and dollars before the "go".

## Amendments

- 2026-10-21, before any run: redesigned around the Project Proposal. Experiment types E0 to E7 replace the earlier fixed grid; the benchmark is grounded in real-world scenarios instead of MA-Gym's workflows; new thresholds marked (proposed).
