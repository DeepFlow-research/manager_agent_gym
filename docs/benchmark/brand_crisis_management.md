## Brand Crisis Management

`tasks: 40` `constraints: 6` `team: 16` `timesteps: 10`

### Workflow Goal

!!! info "Objective"
    Objective: Execute comprehensive brand crisis management response to social media-driven reputation incident affecting mid-market consumer goods company, coordinate multi-stakeholder communications, implement reputation recovery strategy, and restore customer trust to pre-crisis levels within 4-month timeline.

??? note "Primary deliverables"
    - Crisis assessment and stakeholder impact analysis with comprehensive situation evaluation, stakeholder mapping, sentiment analysis across digital platforms, and financial impact quantification with real-time monitoring dashboard.
    - Multi-channel crisis communication strategy with coordinated messaging framework across social media, traditional media, internal communications, and customer service channels with platform-specific content and media relations protocols.
    - Executive crisis team activation with cross-functional team deployment including executive leadership, PR specialists, legal counsel, HR representatives, and customer service leads with defined roles and 24/7 response capability.
    - Customer communication and engagement program with direct customer outreach campaigns, social media response protocols, customer service enhancement, compensation program development, and community management strategy.
    - Internal stakeholder management with employee communication plan, leadership messaging alignment, partner notifications, investor relations updates, and board reporting with morale monitoring.
    - Media relations and narrative control with press release development, interview preparation, journalist relationship management, and proactive media engagement with message consistency.
    - Digital reputation recovery campaign with SEO optimization, positive content creation, influencer engagement, customer testimonial programs, and online review management.
    - Legal and regulatory coordination with legal risk assessment, regulatory notification requirements, litigation preparedness, compliance verification, and documentation preservation.

??? success "Acceptance criteria (high‑level)"
    - Customer sentiment recovery to >75% of pre-crisis levels within 4 months; social media sentiment shifted from negative to neutral/positive across all platforms.
    - Media coverage balance achieved with 60% neutral-to-positive articles within 6 weeks; no unresolved factual inaccuracies in major media coverage.
    - Internal stakeholder confidence maintained with <5% employee turnover during crisis period; investor confidence preserved with transparent communication.
    - Legal and compliance requirements met with zero regulatory violations; all documentation properly maintained for potential legal proceedings.
    - Customer retention rate >90% among existing customer base; customer service resolution time <24 hours for crisis-related inquiries.
    - Brand trust metrics restored to within 80% of pre-crisis baseline through independent third-party measurement.

### Team Structure

| Agent ID | Type | Name / Role | Capabilities |
|---|---|---|---|
| crisis_communications_lead | ai |  | Develops messaging framework<br>Develops multi-channel communication strategy<br>Preserves brand voice during crisis |
| social_media_manager | ai |  | Handles real-time social media response<br>Monitors sentiment<br>Maintains platform consistency |
| stakeholder_relations_manager | ai |  | Manages customer retention<br>Manages employee communications<br>Manages investor relations<br>Manages partner notifications |
| media_relations_specialist | ai |  | Handles traditional media relations<br>Manages journalist relationships<br>Coordinates spokesperson activities<br>Controls narrative during crisis |
| crisis_analyst | ai |  | Conducts situation assessment<br>Analyzes stakeholder impact<br>Quantifies financial impact<br>Evaluates competitive landscape |
| customer_service_coordinator | ai |  | Enhances customer service<br>Develops crisis-specific scripts<br>Implements customer retention and compensation programs |
| digital_reputation_manager | ai |  | Manages digital reputation recovery<br>Optimizes SEO<br>Creates positive content<br>Manages online review management<br>Engages influencers |
| crisis_legal_counsel | ai |  | Provides legal guidance during crisis<br>Assesses risk<br>Ensures regulatory compliance<br>Prepares litigation |
| chief_executive_officer | human_mock | Chief Executive Officer (Executive Leadership) | Provides executive leadership<br>Makes final decisions<br>Represents the company externally |
| chief_marketing_officer | human_mock | Chief Marketing Officer (Brand Leadership) | Oversees brand protection<br>Adjusts marketing strategy<br>Manages reputation recovery efforts |
| chief_legal_officer | human_mock | Chief Legal Officer (Legal Leadership) | Ensures legal compliance<br>Mitigates risk<br>Meets regulatory requirements |
| public_relations_director | human_mock | Public Relations Director (External Communications) | Leads external communications<br>Manages media strategy<br>Coordinates spokesperson activities |
| human_resources_director | human_mock | Human Resources Director (Internal Stakeholder Management) | Manages internal communications<br>Manages employee morale<br>Manages workforce retention |
| investor_relations_director | human_mock | Investor Relations Director (Financial Communications) | Maintains investor confidence<br>Provides transparent updates<br>Manages financial communications |
| operations_director | human_mock | Operations Director (Business Continuity) | Ensures business continuity<br>Manages supply chain stability<br>Responds to operational crises |
| external_brand_consultant | human_mock | External Brand Consultant (Strategic Advisory) | Provides independent perspective<br>Validates crisis strategy<br>Expertise in reputation recovery |

### Join/Leave Schedule

| Timestep | Agents / Notes |
|---:|---|
| 0 | **crisis_communications_lead** — Crisis communications strategy<br>**crisis_analyst** — Situation assessment and impact analysis<br>**chief_executive_officer** — Executive crisis leadership<br>**chief_marketing_officer** — Brand protection oversight |
| 2 | **social_media_manager** — Real-time social media response<br>**media_relations_specialist** — Media relations and press response<br>**public_relations_director** — External communications leadership |
| 4 | **stakeholder_relations_manager** — Multi-stakeholder coordination<br>**customer_service_coordinator** — Customer service enhancement<br>**crisis_legal_counsel** — Legal risk assessment<br>**chief_legal_officer** — Legal compliance oversight |
| 6 | **human_resources_director** — Internal communications and employee relations<br>**investor_relations_director** — Investor confidence management<br>**operations_director** — Business continuity assurance |
| 10 | **digital_reputation_manager** — Digital reputation recovery<br>**external_brand_consultant** — Strategic crisis advisory |

### Workflow Diagram

[![Workflow DAG](assets/brand_crisis_management.svg){ width=1200 }](assets/brand_crisis_management.svg){ target=_blank }

### Preferences & Rubrics

Defined: Yes.

#### Sources

- Workflow: `/Users/charliemasters/Desktop/deepflow/manager_agent_gym/examples/end_to_end_examples/brand_crisis_management/workflow.py`
- Team: `/Users/charliemasters/Desktop/deepflow/manager_agent_gym/examples/end_to_end_examples/brand_crisis_management/team.py`
- Preferences: `/Users/charliemasters/Desktop/deepflow/manager_agent_gym/examples/end_to_end_examples/brand_crisis_management/preferences.py`

