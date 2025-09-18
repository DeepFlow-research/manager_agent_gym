## Global Product Recall

`tasks: 49` `constraints: 6` `team: 24` `timesteps: 40`

### Workflow Goal

!!! info "Objective"
    Objective: Execute comprehensive global product recall for automotive safety component affecting 2M vehicles 
                across 15 countries, implement effective remediation measures, and achieve successful market re-entry with 
                restored consumer confidence and regulatory compliance.

??? note "Primary deliverables"
    - Global regulatory notification package: NHTSA, Transport Canada, EU GPSR, and national authority filings
    - with defect characterization, risk assessment, and coordinated timeline across all jurisdictions.
    - Crisis management coordination: cross-functional recall team activation, executive communication protocols,
    - regulatory liaison management, and 24/7 incident response capability with documented decision-making authority.
    - Consumer communication campaign: multi-channel safety notifications (mail, electronic, dealer networks),
    - customer service hotline deployment, media relations strategy, and social media crisis management with
    - regulatory-compliant messaging.
    - Product retrieval logistics: reverse supply chain activation, dealer network coordination, customer return
    - processing, affected inventory identification and quarantine, and disposal/recycling protocols across
    - global markets.
    - Root cause analysis and remediation: technical failure investigation, design modification development,
    - enhanced testing protocols, supplier quality improvements, and manufacturing process corrections with
    - validation evidence.
    - Regulatory compliance documentation: recall effectiveness monitoring, consumer response tracking
    - (targeting >95% completion), regulatory status reporting, and audit trail maintenance across all markets.
    - Market re-entry strategy: product redesign validation, regulatory approval for resumed sales, enhanced
    - quality assurance protocols, customer confidence rebuilding campaign, and competitive repositioning plan.
    - Legal and financial coordination: liability management across jurisdictions, insurance claims processing,
    - litigation strategy development, and financial impact mitigation with stakeholder communication.

??? success "Acceptance criteria (high-level)"
    - Recall completion rate >95% across all 15 markets with regulatory sign-offs obtained; no outstanding
    - critical safety findings.
    - Consumer safety incidents eliminated with zero additional injuries/fatalities post-recall announcement;
    - product hazard fully contained.
    - Regulatory approvals secured for market re-entry in all jurisdictions; enhanced quality protocols
    - validated and operational.
    - Customer confidence metrics restored to >80% of pre-recall levels within 12 months; brand reputation
    - recovery demonstrated through independent surveys.
    - Financial impact contained within crisis management budget parameters; insurance coverage maximized
    - and litigation exposure minimized.
    - Supply chain partners retained with enhanced quality agreements; dealer network confidence maintained
    - throughout process.

### Team Structure

| Agent ID | Type | Name / Role | Capabilities |
|---|---|---|---|
| crisis_coordinator | ai |  | Runs crisis operations cadence<br>Coordinates emergency response<br>Manages executive escalations<br>Maintains decision/owner/ETA logs |
| safety_engineer | ai |  | Performs safety assessments<br>Investigates failure modes<br>Analyzes risk and mitigations<br>Reports safety findings |
| quality_assurance_specialist | ai |  | Runs root cause analysis<br>Implements design modifications<br>Enhances testing protocols<br>Improves supplier quality |
| regulatory_affairs_manager | ai |  | Coordinates multi‑jurisdiction filings<br>Tracks timelines and dependencies<br>Aligns with authorities<br>Prepares regulator communications |
| compliance_coordinator | ai |  | Monitors recall effectiveness<br>Tracks consumer responses<br>Produces status reports<br>Targets >95% completion |
| communications_director | ai |  | Runs crisis comms strategy<br>Drafts consumer safety notifications<br>Handles media relations<br>Coordinates stakeholder communication |
| customer_service_manager | ai |  | Deploys hotlines and portals<br>Runs return processing systems<br>Tracks SLAs and satisfaction<br>Feeds learnings to ops |
| logistics_coordinator | ai |  | Manages reverse logistics<br>Coordinates dealer networks<br>Plans retrieval across countries<br>Resolves operational bottlenecks |
| supply_chain_manager | ai |  | Implements quarantine/disposal<br>Coordinates suppliers<br>Maintains partner relationships<br>Audits process compliance |
| legal_counsel | ai |  | Assesses multi‑jurisdiction liability<br>Guides litigation strategy<br>Drafts legal communications<br>Balances risk vs action |
| financial_analyst | ai |  | Manages crisis budget<br>Processes insurance claims<br>Tracks financial KPIs<br>Models impact scenarios |
| brand_manager | ai |  | Designs confidence rebuilding campaigns<br>Plans competitive repositioning<br>Coordinates recovery communications<br>Measures trust restoration |
| market_reentry_strategist | ai |  | Coordinates redesign validation<br>Secures approvals for resumption<br>Enhances QA protocols<br>Stages re‑entry by market |
| nhtsa_examiner | human_mock | NHTSA Safety Examiner (US Safety Regulator) | Reviews defect reports<br>Assesses recall effectiveness<br>Issues findings/requirements<br>Coordinates with manufacturer |
| transport_canada_official | human_mock | Transport Canada Official (Canadian Safety Regulator) | Coordinates Canadian approvals<br>Monitors compliance<br>Communicates updates<br>Engages with stakeholders |
| eu_gpsr_coordinator | human_mock | EU GPSR Coordinator (European Safety Regulator) | Oversees EU coordination<br>Validates compliance<br>Tracks status across markets<br>Aligns messaging and actions |
| ceo | human_mock | Chief Executive Officer (Executive Leadership) | Sets crisis priorities<br>Communicates to stakeholders<br>Approves major decisions<br>Allocates resources |
| chief_safety_officer | human_mock | Chief Safety Officer (Safety Leadership) | Oversees safety protocols<br>Validates corrective actions<br>Tracks incidents<br>Approves safety sign‑offs |
| general_counsel | human_mock | General Counsel (Legal Leadership) | Approves legal strategy<br>Manages liability exposure<br>Coordinates multi‑jurisdiction issues<br>Oversees documentation |
| chief_financial_officer | human_mock | Chief Financial Officer (Financial Leadership) | Approves crisis budget<br>Tracks financial impact<br>Optimizes insurance/claims<br>Reports to board and regulators |
| independent_safety_auditor | human_mock | Independent Safety Auditor (Independent Validation) | Validates remediation effectiveness<br>Runs independent checks<br>Issues findings<br>Recommends improvements |
| insurance_adjuster | human_mock | Insurance Adjuster (Insurance Representative) | Processes claims<br>Coordinates with insurers<br>Documents coverage decisions<br>Advises finance on recovery |
| consumer_advocacy_representative | human_mock | Consumer Advocacy Representative (Consumer Protection) | Represents consumer interests<br>Validates effectiveness measures<br>Provides feedback to improve<br>Monitors outreach quality |
| board_chair | human_mock | Board Chair (Board Governance) | Chairs crisis board sessions<br>Approves major crisis actions<br>Ensures governance documentation<br>Holds executives accountable |

### Join/Leave Schedule

| Timestep | Agents / Notes |
|---:|---|
| 0 | **crisis_coordinator** — Crisis management coordination<br>**safety_engineer** — Immediate safety assessment<br>**regulatory_affairs_manager** — Emergency regulatory notifications<br>**ceo** — Executive crisis authority |
| 1 | **communications_director** — Crisis communication strategy<br>**legal_counsel** — Legal risk assessment<br>**chief_safety_officer** — Safety oversight authority |
| 3 | **customer_service_manager** — Customer service infrastructure<br>**compliance_coordinator** — Regulatory compliance monitoring<br>**general_counsel** — Legal strategy approval |
| 5 | **nhtsa_examiner** — US regulatory review<br>**transport_canada_official** — Canadian regulatory coordination<br>**eu_gpsr_coordinator** — European regulatory oversight |
| 8 | **logistics_coordinator** — Global logistics coordination<br>**supply_chain_manager** — Supply chain operations<br>**financial_analyst** — Financial impact management |
| 12 | **quality_assurance_specialist** — Root cause analysis<br>**chief_financial_officer** — Financial oversight |
| 20 | **independent_safety_auditor** — Independent safety validation<br>**insurance_adjuster** — Insurance claims processing<br>**consumer_advocacy_representative** — Consumer protection oversight |
| 30 | **brand_manager** — Brand recovery strategy<br>**market_reentry_strategist** — Market re-entry planning |
| 40 | **board_chair** — Board governance and final approvals |

### Workflow Diagram

[![Workflow DAG](assets/global_product_recall.svg){ width=1200 }](assets/global_product_recall.svg){ target=_blank }

### Preferences & Rubrics

Defined: Yes.

#### Sources

- Workflow: `/Users/charliemasters/Desktop/deepflow/manager_agent_gym/examples/end_to_end_examples/global_product_recall/workflow.py`
- Team: `/Users/charliemasters/Desktop/deepflow/manager_agent_gym/examples/end_to_end_examples/global_product_recall/team.py`
- Preferences: `/Users/charliemasters/Desktop/deepflow/manager_agent_gym/examples/end_to_end_examples/global_product_recall/preferences.py`

