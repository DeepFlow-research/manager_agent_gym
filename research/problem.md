# Problem statement (draft v1, from research/Project Proposal.pdf)

## Problem
Adaptive Replanning for Manager Agents under Unexpected External Team Changes. We study the manager agent's role in resilient multi-agent workflows: how it should repair a plan after an unexpected agent loss (outage, rate limit, permanent deprecation), evaluated against rule-based and prompt-only baselines on a benchmark whose change processes come from public incident and release records.

## Question
Under unexpected external team changes (an agent becomes unavailable), when do rule-based approaches suffice, and when is a manager or replanning policy needed? Either outcome is a finding: if rules suffice, builders can avoid the cost of a manager; if a manager wins, the benchmark locates where.

## Sub-questions
1. Does telling the manager about the change in its prompt suffice, or does an explicit continue/repair/replan policy improve recovery?
2. How does recovery change with the share of affected tasks that have an equivalent remaining agent (none to all)?
3. At what cost (tokens, time, unnecessary reassignments)?

## Contributions
1. A grounded benchmark for disturbances, starting with team-based change. Gap: many benchmarks use scripted or invented disruptions not derived from real change records.
2. Potentially, an explicit continue/repair/replan policy for a manager handling external team changes.
To our knowledge no existing work combines adaptive replanning, unexpected external agent unavailability, and a manager that delegates to specialised sub-agents.

## Hypothesis
Without an explicit continue/repair/replan policy, a manager either stalls on the change or restarts work it did not need to; the right decision is structural, since it depends on which tasks depend on the lost agent.

## Scope
- Fixed: task goals and requirements, accurately declared agent capabilities.
- Varied: change type and duration (sampled from public records), substitute availability, what the manager is told (unannounced signals; informed as an upper bound), workflow size and dependency depth.
- Out of scope: error recovery, task and preference drift, changing requirements, joins, deployment-performance claims.
- Assumption, not claim: specialised agents are realistic and widely advocated, but their prevalence in production is unproven.

## Open concerns
- Demand for manager-style solutions is unclear; AWS guidance recommends deterministic routing and ordered fallbacks where a substitute exists.
- No evidence on how often no fallback exists in real systems.
- The benchmark must treat changes as unannounced, or it does not differ from MA-Gym's scripted leaves.

## Evaluation
Post-change score on affected tasks (deterministic checklist); disruption cost (unnecessary reassignments, unaffected tasks as control); tokens, time and partial completion. Systems: do nothing, rule-based router with ordered fallbacks, MA-Gym Random, CoT and Assign-All, a prompt-informed manager, a policy-based manager.
