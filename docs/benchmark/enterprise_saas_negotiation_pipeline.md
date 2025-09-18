## Enterprise Saas Negotiation Pipeline

### Workflow Goal

(No goal text found)

### Team Structure

| Agent ID | Type | Name / Role | Capabilities |
|---|---|---|---|
| playbook_selector_ai | ai |  | Drafting a contract playbook with the right clauses and fallback positions |
| clause_librarian_ai | ai |  | Detecting missing or risky provisions in the counterparty paper<br>Proposing alternative language for missing or risky provisions with rationale citations |
| redline_assistant_ai | ai |  | Applying and explaining redlines consistent with the playbook<br>Providing a short justification for each edit<br>Linking to the approval path when the edit exceeds negotiator discretion<br>Keeping an issues list synchronized with CLM metadata |
| obligations_tracker_ai | ai |  | Generating an obligations matrix from the near-final contract<br>Pushing these to RevOps/Success and setting alerts for time-bound obligations<br>Closing the loop by logging playbook learnings to improve future cycles |
| deal_desk_lead | human_mock | Deal Desk Lead (Legal Operations) | Defines intake, tiering, and approval topology<br>Balances speed vs risk and arbitrates escalations<br>Owns cycle‑time metrics and bottleneck removal<br>Maintains playbook hygiene and change control |
| commercial_counsel | human_mock | Commercial Counsel (Legal (Commercial)) | Runs pragmatic negotiations within guardrails<br>Explains risk in plain language and escalates wisely<br>Ensures paper matches product/service reality<br>Maintains issues list and approval links |
| privacy_counsel | human_mock | Privacy & Data Protection Counsel (Legal (Privacy)) | Owns DPA/transfer mechanisms and notices<br>Aligns definitions across MSA/DPA stack<br>Validates claims vs actual data flows<br>Advises on public sector/regulated overlays |
| security_architect | human_mock | Security Architect (Security/Trust) | Reviews SIG/CAIQ and maps to controls exhibits<br>Checks feasibility of audit/LoL/security terms<br>Coordinates mitigations with Engineering<br>Signs off on security language and exceptions |
| revops_clm_admin | human_mock | RevOps & CLM Admin (Revenue Operations) | Ingests executed docs and extracts metadata<br>Sets alerts for time‑bound obligations<br>Translates obligations to GTM workflows<br>Maintains data accuracy in CLM/CRM |
| cro_stakeholder | stakeholder | Chief Revenue Officer (Stakeholder) (Executive Stakeholder) | Sets revenue‑first priorities and guardrails<br>Approves escalations and trade‑offs<br>Demands cycle‑time and quality accountability<br>Champions factory improvements post‑mortem |

### Join/Leave Schedule

| Timestep | Agents / Notes |
|---:|---|
| 0 | **deal_desk_lead** — Stand up intake, SLAs, and approval topology<br>**playbook_selector_ai** — Auto‑select playbook; initialize deviation register<br>**cro_stakeholder** — Confirm revenue priorities and close plan |
| 4 | **commercial_counsel** — Begin redlines and counterpart engagement<br>**clause_librarian_ai** — Normalize templates; ensure clause coverage |
| 8 | **privacy_counsel** — Own DPA/transfers and privacy definitions alignment<br>**security_architect** — Own security questionnaire and controls feasibility<br>**redline_assistant_ai** — Apply guided redlines with justification and fallbacks |
| 14 | **playbook_selector_ai** — Playbook locked; deviations tracked |
| 18 | **deal_desk_lead** — Drive approvals/escalations; clear blockers |
| 22 | **clause_librarian_ai** — Clause normalization complete |
| 26 | **revops_clm_admin** — Ingest executed docs; extract metadata; set alerts<br>**obligations_tracker_ai** — Publish obligations matrix and alerts to GTM teams |
| 32 | **cro_stakeholder** — Review cycle‑time KPIs; approve factory improvements<br>**redline_assistant_ai** — Negotiation complete; closing |

### Preferences & Rubrics

Defined: Yes.

#### Sources

- Workflow: `/Users/charliemasters/Desktop/deepflow/manager_agent_gym/examples/end_to_end_examples/enterprise_saas_negotiation_pipeline/workflow.py`
- Team: `/Users/charliemasters/Desktop/deepflow/manager_agent_gym/examples/end_to_end_examples/enterprise_saas_negotiation_pipeline/team.py`
- Preferences: `/Users/charliemasters/Desktop/deepflow/manager_agent_gym/examples/end_to_end_examples/enterprise_saas_negotiation_pipeline/preferences.py`

