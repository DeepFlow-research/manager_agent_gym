## Tech Company Acquisition

`tasks: 43` `constraints: 6` `team: 16` `timesteps: 25`

### Workflow Goal

!!! info "Objective"
    Objective: Execute comprehensive acquisition of $150M SaaS platform company serving 50K+ enterprise customers across North America and Europe, conduct thorough technology and business due diligence, manage regulatory compliance, and achieve successful integration with retained talent and customer base within 6-month timeline.

??? note "Primary deliverables"
    - Technology due diligence package: software architecture assessment, code quality analysis, cybersecurity audit, IP ownership verification, infrastructure scalability evaluation, and technical debt quantification with integration complexity mapping.
    - Business and financial due diligence: SaaS metrics validation (ARR, churn, CAC, LTV), customer contract analysis, recurring revenue sustainability, operational workflow assessment, and competitive positioning evaluation.
    - Regulatory compliance framework: antitrust clearance coordination, HSR filing preparation, data privacy compliance verification (GDPR/CCPA), software licensing validation, and cross-border regulatory requirements.
    - Integration management office establishment: executive steering committee formation, cross-functional integration teams, governance structure definition, and project management infrastructure.
    - Technology systems integration strategy: platform compatibility roadmap, data migration planning, API integration design, security infrastructure harmonization, and service continuity protocols.
    - Human capital integration program: talent retention strategies, cultural assessment, organizational design, compensation harmonization, and leadership transition planning.
    - Customer relationship preservation: customer notification strategy, service continuity assurance, account management transition, and value proposition enhancement.
    - Market positioning and synergy realization: competitive advantage articulation, product roadmap integration, cross-selling opportunities, and revenue enhancement strategies.

??? success "Acceptance criteria (high‑level)"
    - Technology integration completed with >99.5% service uptime maintained; zero customer data loss or security incidents.
    - Key talent retention >85% for technical leadership; customer churn <5% during integration period.
    - All regulatory approvals secured without conditions; IP ownership fully validated and transferred.
    - Integration budget variance <10% of approved allocation; synergy targets achieved within 12 months.
    - Cultural integration success with unified values and collaborative workflows.
    - Post-integration revenue growth trajectory maintained or improved.
    - Constraints (soft):
    - Integration timeline: critical systems integration within 90 days, complete operational integration within 6 months.
    - Regulatory dependencies: adapt to HSR review timeline variability; maintain compliance readiness.
    - Business continuity: prioritize customer-facing system stability; maintain competitive market position.

### Team Structure

| Agent ID | Type | Name / Role | Capabilities |
|---|---|---|---|
| tech_due_diligence_lead | ai |  | Assesses architecture and code quality<br>Evaluates cybersecurity posture<br>Quantifies technical debt and risks<br>Drafts integration complexity map |
| business_analyst | ai |  | Validates ARR/churn/CAC/LTV metrics<br>Analyzes contracts and cohorts<br>Assesses revenue durability<br>Summarizes operational workflows |
| financial_analyst | ai |  | Builds projection cross‑checks<br>Sizes market and competition<br>Analyzes valuation sensitivities<br>Flags key model risks |
| systems_integration_architect | ai |  | Designs platform compatibility plans<br>Plans data migration and cutovers<br>Defines API/integration patterns<br>Aligns security infrastructure |
| cybersecurity_specialist | ai |  | Runs security audits and gap analysis<br>Verifies privacy/compliance posture<br>Designs integration security controls<br>Tracks remediation owners and SLAs |
| hr_integration_manager | ai |  | Designs retention and comms plans<br>Runs cultural/organizational assessments<br>Coordinates comp/benefit harmonization<br>Guides change management and onboarding |
| customer_success_manager | ai |  | Plans account transitions<br>Ensures service continuity<br>Coordinates comms and SLAs<br>Monitors satisfaction and risks |
| project_coordination_lead | ai |  | Establishes governance and cadence<br>Maintains trackers and status<br>Surfaces risks/decisions with owners<br>Keeps artifacts consistent |
| regulatory_counsel | human_mock | Regulatory Counsel (Legal & Regulatory) | Advises on HSR and remedies<br>Coordinates filings and timelines<br>Interfaces with regulators<br>Mitigates antitrust risks |
| data_privacy_officer | human_mock | Data Privacy Officer (Privacy & Compliance) | Reviews DPAs and data flows<br>Sets transfer and minimization rules<br>Approves integration controls<br>Tracks remediation and notices |
| ip_legal_specialist | human_mock | IP Legal Specialist (Intellectual Property) | Validates IP ownership and OSS<br>Drafts IP/OSS schedules<br>Advises on assignment/consents<br>Mitigates IP litigation risks |
| financial_controller | human_mock | Financial Controller (Financial Integration) | Oversees acquisition accounting<br>Runs budget and synergy tracking<br>Aligns reporting and controls<br>Approves financial integration steps |
| chief_technology_officer | human_mock | Chief Technology Officer (Technology Leadership) | Approves architecture decisions<br>Allocates technical resources<br>Chairs integration design reviews<br>Resolves high‑impact technical risks |
| executive_sponsor | human_mock | Executive Sponsor (Executive Leadership) | Sets success criteria and guardrails<br>Resolves cross‑functional conflicts<br>Approves scope and timelines<br>Communicates status to leadership |
| target_company_ceo | human_mock | Target Company CEO (Target Leadership) | Coordinates employee communications<br>Supports customer continuity<br>Aligns leadership transition<br>Approves disclosure schedule accuracy |
| integration_steering_committee | human_mock | Integration Steering Committee (Governance & Oversight) | Sets governance and decision rights<br>Approves milestones and exceptions<br>Allocates resources to unblock work<br>Monitors integration KPIs |

### Join/Leave Schedule

| Timestep | Agents / Notes |
|---:|---|
| 0 | **tech_due_diligence_lead** — Technology architecture and security assessment<br>**business_analyst** — SaaS metrics and customer contract validation<br>**financial_analyst** — Financial projection and valuation verification<br>**project_coordination_lead** — Integration management office establishment<br>**regulatory_counsel** — Regulatory framework and compliance planning |
| 6 | **cybersecurity_specialist** — Deep security audit and compliance verification<br>**data_privacy_officer** — GDPR/CCPA compliance and privacy framework assessment<br>**ip_legal_specialist** — Intellectual property validation and licensing review |
| 12 | **systems_integration_architect** — Platform integration and migration planning<br>**hr_integration_manager** — Talent retention and cultural integration strategy<br>**financial_controller** — Financial integration and budget management |
| 18 | **customer_success_manager** — Customer relationship preservation and transition<br>**target_company_ceo** — Employee communication and cultural integration leadership<br>**chief_technology_officer** — Technology leadership transition and architecture approval |
| 25 | **executive_sponsor** — Strategic oversight and stakeholder communication<br>**integration_steering_committee** — Governance, decision-making, and milestone approval |

### Workflow Diagram

[![Workflow DAG](assets/tech_company_acquisition.svg){ width=1200 }](assets/tech_company_acquisition.svg){ target=_blank }

### Preferences & Rubrics

Defined: Unknown.

#### Sources

- Workflow: `/Users/charliemasters/Desktop/deepflow/manager_agent_gym/examples/end_to_end_examples/tech_company_acquisition/workflow.py`
- Team: `/Users/charliemasters/Desktop/deepflow/manager_agent_gym/examples/end_to_end_examples/tech_company_acquisition/team.py`
- Preferences: `/Users/charliemasters/Desktop/deepflow/manager_agent_gym/examples/end_to_end_examples/tech_company_acquisition/preferences.py`

