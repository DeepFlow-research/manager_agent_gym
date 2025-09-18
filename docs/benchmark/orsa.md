## Orsa

`tasks: 30` `constraints: 4` `team: 22` `timesteps: 50`

### Workflow Goal

!!! info "Objective"
    Objective: Produce a Board‑approved, supervisory‑ready internal risk and solvency assessment for the
                co‑operative bank/credit union. Align capital adequacy with risk profile under baseline and stressed
                conditions, demonstrate robust risk governance and model controls, and document recovery options.

??? note "Primary deliverables"
    - Risk appetite statement with quantitative limits and early‑warning indicators
    - Material risk inventory and qualitative assessment (inherent, controls, residual) with owners
    - Scenario suite and stress testing results (credit, IRRBB, liquidity, operational, climate overlay)
    - Capital plan with buffers vs NCUA RBC or CCULR leverage, plus management buffer policy
    - Model risk framework evidence (inventory, validation, challenger outcomes) per SR 11‑7
    - Liquidity adequacy analysis and contingency funding plan
    - Board package: exec summary, key findings, capital decisions, and remediation actions

### Team Structure

| Agent ID | Type | Name / Role | Capabilities |
|---|---|---|---|
| project_coordinator_ai | ai |  | Maintains assessment calendar and RAID<br>Tracks dependencies and owners<br>Manages documentation index/versioning<br>Publishes status and blocker lists |
| model_inventory_ai | ai |  | Compiles model inventory<br>Maps inputs/outputs/controls<br>Drafts validation/challenger plans<br>Prepares governance‑ready summaries |
| scenario_designer_ai | ai |  | Drafts macro paths and shocks<br>Builds climate/idiosyncratic overlays<br>Prepares variable books<br>Aligns with governance reviewers |
| credit_modeler_ai | ai |  | Builds PD/LGD/EAD projections<br>Designs overlays and sensitivities<br>Prepares challenger comparisons<br>Runs backtests and attribution |
| irrbb_modeler_ai | ai |  | Computes NII/EVE sensitivities<br>Builds laddered reports<br>Performs attribution analysis<br>Checks behavioral assumptions |
| liquidity_stress_ai | ai |  | Builds liquidity stress profiles<br>Drafts contingency funding triggers<br>Computes survival horizons<br>Publishes funding playbooks |
| operational_risk_ai | ai |  | Summarizes OR exposures and loss data<br>Builds scenario add‑ons<br>Links control gaps to remediation<br>Quantifies capital impacts |
| validator_ai | ai |  | Runs conceptual soundness checks<br>Performs outcomes analysis<br>Designs ongoing monitoring<br>Captures effective challenge evidence |
| documentation_ai | ai |  | Assembles report with citations<br>Ensures reproducibility<br>Maintains audit trail completeness<br>Coordinates approvals |
| dashboard_ai | ai |  | Builds executive dashboards<br>Prepares board materials<br>Summarizes key findings and decisions<br>Tracks remediation owners and ETAs |
| cro | human_mock | Chief Risk Officer (Risk Leadership) | Owns risk framework and appetite<br>Approves scenario selection<br>Engages board and executives<br>Signs final decisions |
| cfo | human_mock | Chief Financial Officer (Finance Leadership) | Aligns with budget/plan<br>Approves buffer policy<br>Chairs finance reviews<br>Owns financial disclosures |
| treasurer | human_mock | Treasurer (Treasury/ALM) | Owns ALM/IRRBB modeling<br>Coordinates funding strategy<br>Confirms ownership and data feeds<br>Presents treasury actions |
| head_credit_risk | human_mock | Head of Credit Risk (Credit Risk) | Oversees credit models/overlays<br>Leads segmentation and loss drivers<br>Approves assumptions<br>Presents results to governance |
| liquidity_risk_manager | human_mock | Liquidity Risk Manager (Liquidity Risk) | Runs liquidity stress tests<br>Maintains CFP triggers<br>Coordinates with Treasurer<br>Reports survival horizons |
| operational_risk_lead | human_mock | Operational Risk Lead (Operational Risk) | Owns OR taxonomy and KRIs<br>Manages loss data and scenarios<br>Coordinates third‑party/fraud posture<br>Presents OR add‑ons |
| model_risk_lead | human_mock | Model Risk/Validation Lead (Model Risk) | Owns SR 11‑7 inventory<br>Plans validations/challengers<br>Documents effective challenge<br>Sets monitoring requirements |
| internal_audit | human_mock | Internal Audit (Assurance) | Audits process and controls<br>Checks documentation and evidence<br>Issues findings and follow‑ups<br>Confirms remediation |
| board_risk_committee | human_mock | Board Risk Committee (Board Oversight) | Challenges methods and results<br>Approves buffer and action choices<br>Signs governance approvals<br>Tracks management actions |
| regulatory_liaison | human_mock | Regulatory Liaison (Regulatory Affairs) | Coordinates with supervisors<br>Preps exam‑ready packages<br>Manages communications<br>Tracks commitments and responses |
| data_governance_lead | human_mock | Data Governance Lead (Data Governance) | Owns data lineage and QC<br>Runs change management<br>Ensures risk data governance<br>Preps data audit evidence |
| cro_stakeholder | stakeholder | CRO Stakeholder (Executive Stakeholder) | Sets priorities across phases<br>Approves scenario and validation scope<br>Demands reproducible evidence<br>Grants final approvals |

### Join/Leave Schedule

| Timestep | Agents / Notes |
|---:|---|
| 0 | **cro** — Launch assessment; approve scope and proportionality<br>**project_coordinator_ai** — Stand up calendar, RAID, and evidence index<br>**data_governance_lead** — Establish data lineage and QC policy<br>**cfo** — Align with budget/plan and board calendar |
| 5 | **model_inventory_ai** — Compile SR 11‑7 model inventory and plan validations<br>**model_risk_lead** — Define validation and challenger scope<br>**treasurer** — Confirm ALM/IRRBB model ownership and data feeds |
| 10 | **head_credit_risk** — Portfolio segmentation and loss-drivers<br>**operational_risk_lead** — Operational risk taxonomy and KRIs |
| 14 | **scenario_designer_ai** — Draft macro paths and idiosyncratic/climate overlays<br>**regulatory_liaison** — Sanity-check scenario plausibility for supervisors |
| 20 | **credit_modeler_ai** — Project credit losses and overlays<br>**irrbb_modeler_ai** — NII/EVE sensitivity and attribution<br>**liquidity_stress_ai** — Liquidity survival horizon and CFP |
| 26 | **dashboard_ai** — Build executive views for interim results |
| 30 | **validator_ai** — Run validation/challenger testing and monitoring design<br>**model_inventory_ai** — Inventory stabilized; handoff to validation |
| 35 | **cfo** — Review capital buffer options vs RBC/CCULR<br>**cro** — Set management buffer; finalize decisions |
| 40 | **documentation_ai** — Compile report with evidence links<br>**internal_audit** — Independent assurance on controls and audit trail |
| 45 | **board_risk_committee** — Board challenge and approval<br>**scenario_designer_ai** — Scenario set finalized; quant complete |
| 50 | **regulatory_liaison** — Package for exam; coordinate communications<br>**validator_ai** — Validation complete; monitoring plan handed off |

### Workflow Diagram

[![Workflow DAG](assets/orsa.svg){ width=1200 }](assets/orsa.svg){ target=_blank }

### Preferences & Rubrics

Defined: Yes.

#### Sources

- Workflow: `/Users/charliemasters/Desktop/deepflow/manager_agent_gym/examples/end_to_end_examples/orsa/workflow.py`
- Team: `/Users/charliemasters/Desktop/deepflow/manager_agent_gym/examples/end_to_end_examples/orsa/team.py`
- Preferences: `/Users/charliemasters/Desktop/deepflow/manager_agent_gym/examples/end_to_end_examples/orsa/preferences.py`

