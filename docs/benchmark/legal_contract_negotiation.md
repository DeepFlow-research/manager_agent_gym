## Legal Contract Negotiation

### Workflow Goal

(No goal text found)

### Team Structure

| Agent ID | Type | Name / Role | Capabilities |
|---|---|---|---|
| inhouse_counsel | ai |  | Drafts/redlines MSA/DPA/Security schedules<br>Maintains issue table and deviation register<br>Aligns cross‑document definitions and scope<br>Prepares crisp escalation briefs with recommendations |
| privacy_counsel | ai |  | Validates Art. 28(3) terms and TOMs<br>Confirms transfer instruments and DPAs<br>Checks records/notice/sub‑processor flows<br>Produces clause‑level guidance and fallbacks |
| security_risk | ai |  | Assesses SOC2/ISO scope and gaps<br>Maps controls to ISO/NCSC frameworks<br>Synthesizes pen‑test and BCP/DR evidence<br>Recommends compensating controls and timelines |
| procurement_lead | ai |  | Validates price/indexation/payment terms<br>Designs SLA/SLO service‑credit structures<br>Tracks concessions vs mitigations<br>Ensures practical change/renewal mechanics |
| finance_partner | ai |  | Builds TCO/NPV sensitivity models<br>Tests credit/cap structures vs SLOs<br>Identifies hidden and lifecycle costs<br>Produces decision‑ready financial briefs |
| business_owner | ai |  | Defines use cases and non‑functionals<br>Sets acceptance criteria and priorities<br>Makes rapid trade‑off decisions<br>Escalates blockers with context |
| vendor_counsel | ai |  | Drafts reasoned responses and trade packages<br>Shares current assurance evidence<br>Maintains cross‑doc consistency<br>Tracks exceptions and approvals |
| general_counsel | human_mock | General Counsel (GC) | Sets approval thresholds and carve‑outs<br>Assesses liability/indemnity posture<br>Balances audit rights vs feasibility<br>Signs off escalations with rationale |
| ciso | human_mock | Chief Information Security Officer (CISO) | Validates assurance scope and exceptions<br>Approves control mappings and targets<br>Sets remediation owners and timelines<br>Reviews incident/BCP readiness |
| dpo | human_mock | Data Protection Officer (DPO) | Reviews DPA/transfer mechanisms<br>Checks DSAR/support obligations<br>Audits sub‑processor regimes<br>Approves privacy notices and UX |
| cfo | human_mock | Finance Approval (Finance) | Validates TCO and cash‑flow impacts<br>Sets budget guardrails and approvals<br>Assesses service‑credit economics<br>Balances cost with risk mitigations |

### Join/Leave Schedule

| Timestep | Agents / Notes |
|---:|---|
| 0 | **inhouse_counsel** — Lead drafting and redlines<br>**business_owner** — Provide use case and timelines<br>**procurement_lead** — Align commercial policy<br>**privacy_counsel** — DPA requirements<br>**security_risk** — Security questionnaire & evidence |
| 5 | **finance_partner** — Commercial modeling |
| 10 | **vendor_counsel** — Begin negotiation rounds |
| 15 | **general_counsel** — Final legal approvals<br>**ciso** — Security approvals<br>**dpo** — Privacy approvals<br>**cfo** — Commercial approvals |

### Preferences & Rubrics

Defined: Yes.

#### Sources

- Workflow: `/Users/charliemasters/Desktop/deepflow/manager_agent_gym/examples/end_to_end_examples/legal_contract_negotiation/workflow.py`
- Team: `/Users/charliemasters/Desktop/deepflow/manager_agent_gym/examples/end_to_end_examples/legal_contract_negotiation/team.py`
- Preferences: `/Users/charliemasters/Desktop/deepflow/manager_agent_gym/examples/end_to_end_examples/legal_contract_negotiation/preferences.py`

