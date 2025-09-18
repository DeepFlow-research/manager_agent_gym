## Legal Litigation Ediscovery

### Workflow Goal

(No goal text found)

### Team Structure

| Agent ID | Type | Name / Role | Capabilities |
|---|---|---|---|
| ediscovery_engineer | ai |  | Plans and executes forensic collection<br>Implements processing and culling<br>Maintains chain‑of‑custody tracking<br>Documents tools, versions, and parameters |
| review_analyst | ai |  | Runs ECA and custodian/topic scoping<br>Builds seed sets and trains TAR<br>Performs QC sampling and metrics<br>Produces defensibility memos |
| production_specialist | ai |  | Prepares Bates and load files<br>Validates metadata and redactions<br>Runs privilege and confidentiality checks<br>Tracks production logs and errata |
| supervising_attorney | human_mock | Supervising Attorney (Legal Oversight) | Approves protocols and workflows<br>Resolves privilege and confidentiality<br>Chairs QC/exception reviews<br>Signs off on productions |
| records_manager | human_mock | Records Manager (Legal Hold) | Issues and tracks legal holds<br>Monitors acknowledgments and releases<br>Coordinates custodian communications<br>Maintains preservation documentation |
| lead_counsel | stakeholder | Lead Counsel (Executive Stakeholder) | Sets defensibility and privilege guardrails<br>Approves protocol and exception handling<br>Arbitrates speed vs. risk trade‑offs<br>Grants final production approvals |

### Join/Leave Schedule

| Timestep | Agents / Notes |
|---:|---|
| 0 | **records_manager** — Issue legal hold & track acknowledgments<br>**ediscovery_engineer** — Forensic collection & processing |
| 6 | **review_analyst** — ECA, seed sets, TAR & QC |
| 12 | **production_specialist** — Prepare productions per protocol |
| 14 | **supervising_attorney** — Approve protocols & privilege decisions |

### Preferences & Rubrics

Defined: Yes.

#### Sources

- Workflow: `/Users/charliemasters/Desktop/deepflow/manager_agent_gym/examples/end_to_end_examples/legal_litigation_ediscovery/workflow.py`
- Team: `/Users/charliemasters/Desktop/deepflow/manager_agent_gym/examples/end_to_end_examples/legal_litigation_ediscovery/team.py`
- Preferences: `/Users/charliemasters/Desktop/deepflow/manager_agent_gym/examples/end_to_end_examples/legal_litigation_ediscovery/preferences.py`

