## Legal Global Data Breach

### Workflow Goal

(No goal text found)

### Team Structure

| Agent ID | Type | Name / Role | Capabilities |
|---|---|---|---|
| forensic_triage_ai | ai |  | Guides secure evidence collection<br>Maintains chain‑of‑custody ledger<br>Flags spoliation risk and hygiene<br>Produces time‑stamped incident bulletins |
| regulatory_matrix_ai | ai |  | Maps jurisdictional triggers/timelines<br>Builds regulator/individual/partner checklists<br>Tracks SLA clocks and late‑notice risk<br>Aligns with counsel on strategy |
| comms_drafter_ai | ai |  | Drafts regulator and customer notices<br>Maintains consistent multi‑audience tone<br>Coordinates approvals with Legal/Comms<br>Keeps templates jurisdiction‑specific |
| timeline_reconstructor_ai | ai |  | Ingests logs/EDR/tickets/interviews<br>Builds living incident chronology<br>Identifies exfil indicators and gaps<br>Keeps teams aligned on the facts |
| incident_commander_legal | human_mock | Incident Commander (Legal) (Lead Counsel) | Sets objectives and cadence<br>Issues legal holds; preserves evidence<br>Arbitrates speed vs regulatory risk<br>Authors privileged final report |
| privacy_counsel_global | human_mock | Global Privacy Counsel (Privacy Legal) | Interprets DP obligations across regions<br>Reviews external notices for compliance<br>Guides DPIA/ROPA updates<br>Coordinates with regulators/outside counsel |
| security_forensics_lead | human_mock | Security Forensics Lead (Security/IR) | Directs investigation and containment<br>Coordinates rotations/patching/hardening<br>Hunts persistence and lateral movement<br>Aligns actions with Legal to avoid spoliation |
| communications_lead | human_mock | Communications Lead (External & Internal Comms) | Owns internal/external messaging<br>Preps Q&A and spokespersons<br>Monitors feedback and adjusts<br>Aligns filings with Legal/PR |
| vendor_risk_manager | human_mock | Vendor Risk Manager (Third‑Party Risk) | Engages processors/sub‑processors<br>Validates investigation/remediation<br>Tracks SLAs and obligations<br>Maintains vendor evidence dossier |
| gc_stakeholder | stakeholder | General Counsel (Stakeholder) (Executive Stakeholder) | Sets decision thresholds and posture<br>Approves notification strategy<br>Demands consistent facts across channels<br>Signs off on lessons‑learned and fixes |

### Join/Leave Schedule

| Timestep | Agents / Notes |
|---:|---|
| 0 | **incident_commander_legal** — Open under privilege; establish cadence; issue legal holds<br>**security_forensics_lead** — Kick off secure triage and initial containment hygiene<br>**forensic_triage_ai** — Guide evidentiary snapshots; maintain chain‑of‑custody ledger<br>**gc_stakeholder** — Set risk posture and decision thresholds |
| 4 | **timeline_reconstructor_ai** — Build living chronology from logs and notes<br>**privacy_counsel_global** — Begin jurisdictional analysis; align on facts framing |
| 8 | **regulatory_matrix_ai** — Construct obligations matrix and notification timers<br>**vendor_risk_manager** — Engage implicated processors/sub‑processors and track SLAs |
| 12 | **comms_drafter_ai** — Draft regulator and customer/partner notices; internal FAQs |
| 16 | **communications_lead** — Coordinate filings and external messaging with counsel |
| 20 | **forensic_triage_ai** — Evidence collection stabilized; handoff to forensics lead |
| 24 | **timeline_reconstructor_ai** — Timeline stable; minor updates via IC Legal |
| 28 | **regulatory_matrix_ai** — Obligations executed; residual tracking remains in legal<br>**privacy_counsel_global** — Finalize recordkeeping/DPIA/ROPA updates and lessons learned |
| 32 | **comms_drafter_ai** — Notices sent; PR steady‑state<br>**gc_stakeholder** — Review final report and board brief; close out |

### Preferences & Rubrics

Defined: Yes.

#### Sources

- Workflow: `/Users/charliemasters/Desktop/deepflow/manager_agent_gym/examples/end_to_end_examples/legal_global_data_breach/workflow.py`
- Team: `/Users/charliemasters/Desktop/deepflow/manager_agent_gym/examples/end_to_end_examples/legal_global_data_breach/team.py`
- Preferences: `/Users/charliemasters/Desktop/deepflow/manager_agent_gym/examples/end_to_end_examples/legal_global_data_breach/preferences.py`

