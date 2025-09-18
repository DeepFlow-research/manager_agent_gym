## Mnc Workforce Restructuring

### Workflow Goal

(No goal text found)

### Team Structure

| Agent ID | Type | Name / Role | Capabilities |
|---|---|---|---|
| selection_criteria_ai | ai |  | Builds structured scorecards<br>Pre‑computes eligibility sets<br>Flags bias proxies and edge cases<br>Prepares calibration packets |
| jurisdiction_matrix_ai | ai |  | Maps WARN/collective redundancy rules<br>Builds per‑site dependency timelines<br>Blocks risky sequencing<br>Tracks obligations and SLAs |
| adverse_impact_ai | ai |  | Computes selection rate ratios<br>Bootstraps confidence bands<br>Designs mitigation options<br>Reports risk reductions |
| notice_pack_ai | ai |  | Assembles letters/FAQs/agreements<br>Coordinates translations<br>Aligns with severance matrices<br>Tracks jurisdictional specifics |
| employment_counsel_ic | human_mock | Employment Counsel (IC) (Lead Counsel) | Sets legal strategy and cadence<br>Approves selection documentation<br>Owns consultation posture<br>Signs final notices and defensibility |
| chro_hrbp_lead | human_mock | HRBP Lead (People/HR) | Runs calibration with managers<br>Coordinates redeployment/outplacement<br>Ensures rationale documentation<br>Advises on timeline certainty |
| er_ir_specialist | human_mock | ER/IR Specialist (Employee/Industrial Relations) | Runs works council/union processes<br>Manages minutes and responses<br>Advises on strike risk<br>Coordinates mitigation |
| comp_benefits_lead | human_mock | Comp & Benefits Lead (Total Rewards) | Designs severance/benefits matrices<br>Reconciles statutory overlays<br>Coordinates payroll readiness<br>Ensures accuracy and fairness |
| communications_lead | human_mock | Communications Lead (Internal/External Comms) | Drafts scripts/letters/FAQs<br>Choreographs day‑of sequencing<br>Coordinates HR/Legal reviews<br>Monitors feedback and adjusts |
| chro_stakeholder | stakeholder | CHRO (Stakeholder) (Executive Stakeholder) | Approves criteria and consultation plan<br>Arbitrates adverse‑impact mitigations<br>Monitors humane comms and execution<br>Signs documentation/audit readiness |

### Join/Leave Schedule

| Timestep | Agents / Notes |
|---:|---|
| 0 | **employment_counsel_ic** — Open under privilege; charter program; set cadence<br>**chro_hrbp_lead** — Translate targets into role proposals; launch calibration<br>**selection_criteria_ai** — Materialize criteria into scorecards; prep calibration packets<br>**chro_stakeholder** — Confirm fairness principles and communication posture |
| 5 | **jurisdiction_matrix_ai** — Build per-site consultation/notice timelines and dependencies<br>**er_ir_specialist** — Engage works councils/unions; prep info packs |
| 10 | **adverse_impact_ai** — Run adverse-impact tests; propose mitigations<br>**comp_benefits_lead** — Draft severance matrix and statutory overlays |
| 14 | **selection_criteria_ai** — Criteria stabilized; decisions in documentation flow |
| 18 | **notice_pack_ai** — Generate jurisdictional notice packs and translations<br>**communications_lead** — Draft manager scripts, letters, FAQs |
| 22 | **jurisdiction_matrix_ai** — Timelines locked; tracking in counsel's SSOT |
| 26 | **chro_stakeholder** — Day-of oversight and humane execution checks |
| 30 | **adverse_impact_ai** — Remediation complete; final lists frozen<br>**notice_pack_ai** — Packs finalized; execution underway |
| 34 | **employment_counsel_ic** — Close-out: documentation and audit readiness |

### Preferences & Rubrics

Defined: Yes.

#### Sources

- Workflow: `/Users/charliemasters/Desktop/deepflow/manager_agent_gym/examples/end_to_end_examples/mnc_workforce_restructuring/workflow.py`
- Team: `/Users/charliemasters/Desktop/deepflow/manager_agent_gym/examples/end_to_end_examples/mnc_workforce_restructuring/team.py`
- Preferences: `/Users/charliemasters/Desktop/deepflow/manager_agent_gym/examples/end_to_end_examples/mnc_workforce_restructuring/preferences.py`

