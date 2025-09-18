## Supply Chain Planning

### Workflow Goal

(No goal text found)

### Team Structure

| Agent ID | Type | Name / Role | Capabilities |
|---|---|---|---|
| forecaster_ai | ai |  | Builds multi‑horizon forecasts with CIs<br>Detects change‑points and fragility<br>Documents assumptions and data quality<br>Feeds scenarios to capacity planning |
| convoy_planner_ai | ai |  | Plans convoy/slot utilization<br>Simulates ETA and routing impacts<br>Coordinates port rotations<br>Maintains auditable schedules |
| trade_compliance_ai | ai |  | Validates HS coding and manifests<br>Automates advance filings<br>Screens DG and permits<br>Keeps audit trails for decisions |
| ops_copilot_ai | ai |  | Monitors telemetry and events<br>Suggests reroute/hold/advance plays<br>Triage by SLA/impact<br>Generates concise status updates |
| head_ops | human_mock | Head of Logistics Operations (Operations Leadership) | Sets service targets and escalation rules<br>Arbitrates capacity trade‑offs<br>Owns disruption response<br>Drives continuous improvement |
| network_planning_mgr | human_mock | Network Planning Manager (Network & Capacity Planning) | Slots vessels/rail/road and yards<br>Sets buffers for priority customers<br>Manages resource constraints<br>Signs off weekly plans and reroutes |
| customs_manager | human_mock | Customs & Compliance Manager (Trade Compliance) | Owns HS/manifest/permit accuracy<br>Runs DG declarations and stowage checks<br>Preps pre‑arrival documentation<br>Clears exceptions with authorities |
| control_tower_lead | human_mock | Control Tower Lead (Execution & Exceptions) | Runs ops room and owner assignment<br>Maintains dashboards vs reality<br>Coordinates incident response<br>Approves deliberate deviations |
| port_liaison | human_mock | Port & Canal Liaison (External Coordination) | Confirms convoys/pilotage/tugs<br>Expedites documentation issues<br>Maintains rotation constraints view<br>Propagates schedule changes |
| coo_stakeholder | stakeholder | COO Stakeholder (Executive Stakeholder) | Sets priorities and customer guardrails<br>Approves buffers and reroute strategies<br>Holds teams to OTIF targets<br>Chairs post‑mortems and improvements |

### Join/Leave Schedule

| Timestep | Agents / Notes |
|---:|---|
| 0 | **head_ops** — Kick off; set service targets and escalation rules<br>**network_planning_mgr** — Translate goals into capacity planning assumptions<br>**forecaster_ai** — Generate baseline + scenario bands for volumes<br>**coo_stakeholder** — Confirm priorities and customer guardrails |
| 5 | **convoy_planner_ai** — Reserve convoy slots and align rotations/ETAs<br>**port_liaison** — Coordinate with SCA and port agents on constraints |
| 8 | **customs_manager** — Stand up pre‑arrival filings and DG process<br>**trade_compliance_ai** — Automate HS validation and documentation checks |
| 12 | **forecaster_ai** — Forecast stabilized; hand off to planning |
| 16 | **control_tower_lead** — Stand up control tower, dashboards, and comms<br>**ops_copilot_ai** — Exception triage and playbook suggestions |
| 22 | **convoy_planner_ai** — Rotation fixed; ops in steady‑state |
| 30 | **coo_stakeholder** — Review OTIF/dwell and sign off on learnings<br>**trade_compliance_ai** — Documentation flow stable; audits ongoing |

### Preferences & Rubrics

Defined: Yes.

#### Sources

- Workflow: `/Users/charliemasters/Desktop/deepflow/manager_agent_gym/examples/end_to_end_examples/supply_chain_planning/workflow.py`
- Team: `/Users/charliemasters/Desktop/deepflow/manager_agent_gym/examples/end_to_end_examples/supply_chain_planning/team.py`
- Preferences: `/Users/charliemasters/Desktop/deepflow/manager_agent_gym/examples/end_to_end_examples/supply_chain_planning/preferences.py`

