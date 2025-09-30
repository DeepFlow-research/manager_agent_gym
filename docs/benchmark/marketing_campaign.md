## Marketing Campaign

`tasks: 51` `constraints: 5` `team: 26` `timesteps: 55`

### Workflow Goal

!!! info "Objective"
    Objective: Launch a national integrated campaign for Acme Renewables to drive brand awareness,
                qualified pipeline for B2B (utilities, municipalities, C&I), and sign-ups for B2C community energy.

??? note "Primary deliverables"
    - Messaging house & claims playbook (substantiated, privacy-safe), brand & creative toolkit Channel plan & budget (paid/owned/earned), flighting calendar, and experimentation plan Web conversion flows (accessibility & consent), CRM and lead-routing with scoring PR & analyst program, events/field marketing kit, partner co-marketing assets Measurement framework (brand lift, funnel KPIs, CAC/LTV), MMM/MTA-compatible UTM governance

??? success "Acceptance criteria (high‑level)"
    - Brand lift ≥ +6% aided awareness within target segments; ≥ 15% MoM web organic uplift during flight ≥ 1,000 MQLs (B2B+B2C) with <= target CAC thresholds; ≥ 25 qualified opportunities for B2B Claims substantiation log maintained; no greenwashing guideline violations WCAG 2.1 AA compliance for key web assets; consent opt‑in rates ≥ 85% Experimentation cadence established; weekly executive dashboard live

### Team Structure

| Agent ID | Type | Name / Role | Capabilities |
|---|---|---|---|
| campaign_planner_ai | ai |  | Translates research to channel plan<br>Maintains risk/dependency register<br>Proposes weekly reallocations<br>Tracks performance signals and trade‑offs |
| creative_director_ai | ai |  | Generates territories and briefs<br>Enforces brand voice and inclusion<br>Curates variant matrices<br>Reviews creative for coherence |
| copy_optimizer_ai | ai |  | Drafts channel‑specific variants<br>Runs A/B tests with hypotheses<br>Checks claims against substantiation<br>Feeds learnings back to creative |
| seo_analyst_ai | ai |  | Creates keyword clusters and pillars<br>Plans internal links and schema<br>Builds content backlog<br>Aligns with ICP pain points |
| media_buyer_ai | ai |  | Configures platforms and budgets<br>Sets frequency caps and audiences<br>Runs canary rollouts<br>Scales winners and prunes waste |
| analytics_ai | ai |  | Defines KPIs and event schemas<br>Implements dashboards and alerts<br>Designs experiments<br>Publishes weekly readouts |
| consent_compliance_ai | ai |  | Configures CMP and opt‑ins<br>Enforces minimization and audit trails<br>Monitors compliance for green claims<br>Coordinates with legal marketing |
| accessibility_checker_ai | ai |  | Checks contrast/alt/captions<br>Flags plain‑language fixes<br>Tracks WCAG 2.1 AA compliance<br>Coordinates remediation |
| crm_ops_ai | ai |  | Configures scoring and routing<br>Deduplicates and enriches<br>Tracks SLAs<br>Closes feedback loops |
| social_listener_ai | ai |  | Monitors sentiment and competitor moves<br>Summarizes insights<br>Triggers budget/creative pivots<br>Feeds learning back to planners |
| cmo | human_mock | Chief Marketing Officer (Executive Stakeholder) | Sets objectives and KPIs<br>Approves budgets and trade‑offs<br>Chairs reviews and sign‑offs<br>Balances speed/brand/compliance |
| vp_marketing | human_mock | VP Marketing (LT Member) | Owns channel staffing and cadence<br>Publishes weekly readouts<br>Aligns pipeline and brand goals<br>Escalates risks and decisions |
| brand_creative_director | human_mock | Brand Creative Director (Creative Lead) | Approves territories and assets<br>Enforces brand and inclusive tone<br>Partners with Legal on approvals<br>Curates design quality |
| performance_media_manager | human_mock | Performance Media Manager (Paid Media) | Owns platform setup and pacing<br>Enforces brand safety<br>Optimizes budgets<br>Manages flighting |
| web_lead | human_mock | Web Experience Lead (Web/Conversion) | Builds LPs and analytics<br>Integrates CMP/accessibility<br>Coordinates QA and releases<br>Tracks conversion and fixes |
| crm_lifecycle_manager | human_mock | CRM & Lifecycle Manager (Lifecycle/Email) | Designs lifecycle journeys<br>Maintains deliverability<br>Runs preference center<br>Aligns with Sales/Community |
| pr_lead | human_mock | PR Lead (PR/AR) | Builds press kit and briefings<br>Runs interviews/analyst relations<br>Monitors coverage<br>Coordinates with legal marketing |
| events_manager | human_mock | Events & Field Manager (Events) | Runs event/webinar production<br>Staffs and equips teams<br>Ensures compliant capture<br>Closes loop with sales |
| partnerships_manager | human_mock | Partnerships Manager (Alliances/Partners) | Leads co‑marketing and MDF<br>Coordinates partner approvals<br>Aligns claims and assets<br>Reports partner impact |
| data_analyst | human_mock | Marketing Data Analyst (Analytics) | Builds dashboards<br>Runs attribution/experiments<br>QA’s analytics<br>Provides insights and guardrails |
| legal_marketing_counsel | human_mock | Legal Marketing Counsel (Legal (Marketing)) | Reviews claims and disclosures<br>Approves co‑branding and PR<br>Advises on privacy/consent<br>Tracks approvals and exceptions |
| accessibility_specialist | human_mock | Accessibility Specialist (Accessibility) | Conducts manual WCAG audits<br>Guides remediation<br>Validates alt/captions/contrast<br>Documents conformance |
| sustainability_officer | human_mock | Sustainability Officer (Sustainability) | Validates REC/LCA references<br>Approves green claims<br>Maintains evidence register<br>Advises messaging house |
| sales_director | human_mock | Sales Director (B2B) (Sales) | Aligns MQL/SQL definitions<br>Sets routing SLAs<br>Closes sales feedback loop<br>Tracks velocity |
| community_ops_manager | human_mock | Community Ops Manager (Community/B2C Ops) | Designs support flows<br>Ensures compliance notices<br>Coordinates with partners<br>Reports enrollment KPIs |
| cmo_stakeholder | stakeholder | CMO Stakeholder (Executive) | Sets pace and quality bars<br>Approves budgets and exceptions<br>Chairs weekly decision forums<br>Holds teams to measurement discipline |

### Join/Leave Schedule

| Timestep | Agents / Notes |
|---:|---|
| 0 | **cmo** — Set objectives, budget guardrails, and KPIs<br>**vp_marketing** — Stand up cadence and org plan<br>**campaign_planner_ai** — Translate research to initial channel plan<br>**analytics_ai** — Define KPIs, UTM, dashboards<br>**consent_compliance_ai** — Embed privacy-by-design up front<br>**social_listener_ai** — Baseline sentiment and competitor activity |
| 5 | **seo_analyst_ai** — SEO roadmap; inform content pillars<br>**brand_creative_director** — Approve messaging territories<br>**legal_marketing_counsel** — Review green claims substantiation approach |
| 10 | **creative_director_ai** — Creative territories + briefs<br>**copy_optimizer_ai** — Variant copy and A/B hypotheses<br>**web_lead** — LP build plan and analytics mapping |
| 14 | **accessibility_checker_ai** — WCAG checks for assets and LPs<br>**crm_ops_ai** — Scoring/routing/dedup config<br>**sustainability_officer** — Validate metrics for claims |
| 18 | **pr_lead** — Press/analyst briefing program<br>**events_manager** — Event/webinar plan and kits<br>**partnerships_manager** — Partner co-marketing planning |
| 20 | **performance_media_manager** — Platform setup and pacing<br>**media_buyer_ai** — Automate budgets, caps, and QA<br>**brand_creative_director** — Final creative approvals |
| 22 | **crm_lifecycle_manager** — Nurture sequences and deliverability<br>**sales_director** — B2B pipeline SLA alignment<br>**community_ops_manager** — B2C enrollment support alignment |
| 28 | **data_analyst** — Executive dashboard & analysis cadence<br>**seo_analyst_ai** — Initial roadmap delivered; ongoing items via planner |
| 35 | **analytics_ai** — Experiment design reviews and MMM/MTA alignment<br>**campaign_planner_ai** — Weekly reallocation proposals based on results |
| 45 | **accessibility_specialist** — Manual AA audit during scale-up<br>**copy_optimizer_ai** — Creative variants stabilized; focus on scaling |
| 55 | **media_buyer_ai** — Automation steady-state; human pacing sufficient<br>**vp_marketing** — Transition to wrap-up and learnings |

### Workflow Diagram

[![Workflow DAG](assets/marketing_campaign.svg){ width=1200 }](assets/marketing_campaign.svg){ target=_blank }

### Preferences & Rubrics

Defined: Yes.

#### Sources

- Workflow: `/Users/charliemasters/Desktop/deepflow/manager_agent_gym/examples/end_to_end_examples/marketing_campaign/workflow.py`
- Team: `/Users/charliemasters/Desktop/deepflow/manager_agent_gym/examples/end_to_end_examples/marketing_campaign/team.py`
- Preferences: `/Users/charliemasters/Desktop/deepflow/manager_agent_gym/examples/end_to_end_examples/marketing_campaign/preferences.py`

