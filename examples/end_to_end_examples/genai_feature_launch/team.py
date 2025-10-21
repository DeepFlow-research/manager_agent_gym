"""
Gen-AI Feature Launch Demo

Real-world use case: User-facing generative AI feature launch with safety gates and governance.

Demonstrates:
- Complex multi-stakeholder coordination across AI safety, privacy, security, and regulatory compliance domains
- Risk-driven project management with safety-first prioritization and gate-based approval workflows
- High-stakes decision making under regulatory scrutiny with audit-ready documentation requirements
- Crisis-ready deployment planning with real-time monitoring, kill switches, and incident response capabilities
- Cross-functional team leadership managing technical specialists, legal counsel, and executive stakeholders
- Regulatory compliance management across data protection, AI transparency, and safety disclosure requirements
- Timeline-critical delivery under 6-week constraint with safety-first scope management and controlled rollout strategies
"""

from manager_agent_gym.schemas.agents import (
    AIAgentConfig,
    HumanAgentConfig,
    StakeholderConfig,
)
from manager_agent_gym.schemas.preferences.preference import (
    PreferenceSnapshot,
    Preference,
)


def create_team_configs():
    """Create AI and human mock agent configurations for Gen-AI Feature Launch."""

    # AI Safety & Testing Specialists
    ai_safety_engineer = AIAgentConfig(
        agent_id="ai_safety_engineer",
        agent_type="ai",
        system_prompt=(
            "You are an AI Safety Engineer focusing on red team testing, prompt injection detection, "
            "jailbreak resistance, and adversarial robustness evaluation with automated testing frameworks."
        ),
        agent_description=(
            "Safety engineer who pressure‑tests models under realistic adversarial conditions, "
            "builds guardrails that fail safely, and translates findings into actionable fixes."
        ),
        agent_capabilities=[
            "Designs and runs automated red‑team campaigns",
            "Detects prompt‑injection and data‑exfiltration attempts",
            "Builds refusal/containment guardrails and tests kill‑switches",
            "Summarizes risks with reproducible evidence and metrics",
        ],
    )
    red_team_specialist = AIAgentConfig(
        agent_id="red_team_specialist",
        agent_type="ai",
        system_prompt=(
            "You are a Red Team Specialist conducting adversarial testing, prompt injection attacks, "
            "data exfiltration attempts, and safety violation probes with comprehensive attack scenario design."
        ),
        agent_description=(
            "Offensive safety tester who thinks like an attacker, enumerates failure modes, and stress‑tests end‑to‑end systems."
        ),
        agent_capabilities=[
            "Designs diverse attack scenarios and playbooks",
            "Executes prompt‑injection and tool‑abuse tests",
            "Measures exploit success rates and coverage",
            "Produces prioritized remediation guidance",
        ],
    )
    ml_safety_researcher = AIAgentConfig(
        agent_id="ml_safety_researcher",
        agent_type="ai",
        system_prompt=(
            "You design hallucination detection systems, factual accuracy benchmarks, bias evaluation frameworks, "
            "and safety threshold calibration with research-backed methodologies."
        ),
        agent_description=(
            "Research‑minded evaluator who operationalizes accuracy, bias, and robustness metrics and calibrates thresholds to policy."
        ),
        agent_capabilities=[
            "Builds hallucination/factuality benchmarks",
            "Implements bias/fairness metrics and cohort tests",
            "Calibrates thresholds and acceptance gates",
            "Publishes replicable evaluation suites",
        ],
    )

    # Privacy & Compliance Team
    privacy_engineer = AIAgentConfig(
        agent_id="privacy_engineer",
        agent_type="ai",
        system_prompt=(
            "You are a Privacy Engineer implementing data minimization, PII detection, consent management, "
            "and GDPR/CCPA compliance with privacy-by-design architecture."
        ),
        agent_description=(
            "Engineer who bakes privacy into data flows, proving compliance with practical controls and auditable evidence."
        ),
        agent_capabilities=[
            "Designs privacy‑by‑design architectures",
            "Implements PII detection and minimization",
            "Sets consent/retention policies and audits",
            "Prepares DPIA inputs and evidence bundles",
        ],
    )
    compliance_analyst = AIAgentConfig(
        agent_id="compliance_analyst",
        agent_type="ai",
        system_prompt=(
            "You conduct DPIA assessments, regulatory mapping, data flow analysis, and AI transparency "
            "disclosure preparation with cross-jurisdictional compliance expertise."
        ),
        agent_description=(
            "Compliance navigator who maps obligations to system reality and keeps disclosures accurate and actionable."
        ),
        agent_capabilities=[
            "Drafts and reviews DPIA/TRA artifacts",
            "Maps cross‑jurisdictional obligations",
            "Prepares AI transparency disclosures",
            "Tracks gaps and remediation owners/ETAs",
        ],
    )

    # Security & Infrastructure
    security_architect = AIAgentConfig(
        agent_id="security_architect",
        agent_type="ai",
        system_prompt=(
            "You design threat models, implement sandboxing controls, secrets detection systems, "
            "and runtime security monitoring with defense-in-depth strategies."
        ),
        agent_description=(
            "Pragmatic architect who hardens the system against realistic threat models and proves it with telemetry."
        ),
        agent_capabilities=[
            "Authoring system threat models",
            "Designing sandboxing and isolation controls",
            "Integrating secrets/leak detection",
            "Standing up runtime monitoring and alerts",
        ],
    )
    devops_engineer = AIAgentConfig(
        agent_id="devops_engineer",
        agent_type="ai",
        system_prompt=(
            "You build monitoring infrastructure, alerting systems, kill switches, circuit breakers, "
            "and automated deployment pipelines with observability and incident response capabilities."
        ),
        agent_description=(
            "Operations‑first engineer who ships reliable pipelines, rich observability, and crisp incident playbooks."
        ),
        agent_capabilities=[
            "Implements CI/CD and staged rollouts",
            "Configures SLOs, dashboards, and alerts",
            "Builds kill‑switches and circuit breakers",
            "Automates incident response runbooks",
        ],
    )

    # Product & Documentation
    product_manager = AIAgentConfig(
        agent_id="product_manager",
        agent_type="ai",
        system_prompt=(
            "You define product requirements, user journeys, success metrics, feature boundaries, "
            "and launch strategies with stakeholder coordination and market analysis."
        ),
        agent_description=(
            "Outcome‑oriented PM who balances user value with safety and scope, keeping the team decision‑ready."
        ),
        agent_capabilities=[
            "Writes crisp PRDs and success metrics",
            "Defines safe/unsafe feature boundaries",
            "Facilitates cross‑functional decision forums",
            "Plans staged launch and comms",
        ],
    )
    documentation_specialist = AIAgentConfig(
        agent_id="documentation_specialist",
        agent_type="ai",
        system_prompt=(
            "You create model cards, system documentation, user guidelines, API documentation, "
            "and audit-ready evidence packages with traceability and reproducibility focus."
        ),
        agent_description=(
            "Documentation owner who turns complex systems into clear, auditable artifacts others can trust."
        ),
        agent_capabilities=[
            "Authors model/system cards and user guides",
            "Maintains traceability and evidence links",
            "Curates API and operations references",
            "Prepares audit‑ready documentation bundles",
        ],
    )

    # Human Approvals & Oversight
    chief_ai_officer = HumanAgentConfig(
        agent_id="chief_ai_officer",
        agent_type="human_mock",
        system_prompt="Chief AI Officer providing strategic AI governance, safety oversight, and ethical AI compliance.",
        name="Chief AI Officer",
        role="AI Strategy & Ethics",
        experience_years=12,
        background="AI governance and ethics",
        agent_description=(
            "Executive sponsor for responsible AI who sets guardrails, unblocks decisions, and signs off on risk posture."
        ),
        agent_capabilities=[
            "Defines governance and approval gates",
            "Balances safety, compliance, and speed",
            "Chairs cross‑functional reviews",
            "Owns final go/no‑go for AI launches",
        ],
    )
    security_officer = HumanAgentConfig(
        agent_id="chief_security_officer",
        agent_type="human_mock",
        system_prompt="Chief Security Officer ensuring cybersecurity controls, threat mitigation, and incident response readiness.",
        name="Chief Security Officer",
        role="Security Leadership",
        experience_years=15,
        background="Cybersecurity and risk management",
        agent_description=(
            "Security leader who insists on practical controls, measurable risk reduction, and crisp incident readiness."
        ),
        agent_capabilities=[
            "Approves security architectures and controls",
            "Validates threat models and mitigations",
            "Oversees incident response preparedness",
            "Signs off on launch security gates",
        ],
    )
    privacy_officer = HumanAgentConfig(
        agent_id="data_protection_officer",
        agent_type="human_mock",
        system_prompt="Data Protection Officer ensuring GDPR/CCPA compliance, privacy impact assessments, and data subject rights.",
        name="Data Protection Officer",
        role="Privacy & Data Protection",
        experience_years=10,
        background="Data protection law and privacy",
        agent_description=(
            "DPO who ensures lawful, proportionate data use and that user rights are respected in practice, not just on paper."
        ),
        agent_capabilities=[
            "Reviews DPIA/consent/retention models",
            "Assesses cross‑border transfer posture",
            "Approves privacy disclosures and UX",
            "Tracks remediation on privacy risks",
        ],
    )
    legal_counsel = HumanAgentConfig(
        agent_id="legal_counsel",
        agent_type="human_mock",
        system_prompt="Legal Counsel providing regulatory compliance guidance, liability assessment, and AI transparency requirements.",
        name="Legal Counsel",
        role="Legal & Regulatory",
        experience_years=13,
        background="Technology law and AI regulation",
        agent_description=(
            "Practical lawyer who keeps the team inside the lines while enabling speed, with crisp, defensible positions."
        ),
        agent_capabilities=[
            "Drafts/approves regulatory disclosures",
            "Assesses liability and risk trade‑offs",
            "Coordinates with regulators when needed",
            "Ensures documentation defensibility",
        ],
    )
    product_executive = HumanAgentConfig(
        agent_id="product_executive",
        agent_type="human_mock",
        system_prompt="Product Executive responsible for launch decisions, market strategy, and business risk acceptance.",
        name="Product Executive",
        role="Product Leadership",
        experience_years=11,
        background="Product management and AI products",
        agent_description=(
            "Accountable owner for launch outcomes who reconciles value, risk, and timing and commits to decisions."
        ),
        agent_capabilities=[
            "Owns launch criteria and exceptions",
            "Balances scope, schedule, and risk",
            "Communicates plan and status to leadership",
            "Allocates resources to unblock delivery",
        ],
    )
    external_auditor = HumanAgentConfig(
        agent_id="external_ai_auditor",
        agent_type="human_mock",
        system_prompt="External AI Auditor providing independent safety assessment, compliance validation, and audit certification.",
        name="External AI Auditor",
        role="Independent Audit",
        experience_years=8,
        background="AI auditing and safety assessment",
        agent_description=(
            "Independent assessor who pressure‑tests claims and certifies readiness with clear, reproducible checks."
        ),
        agent_capabilities=[
            "Runs impartial conformance checks",
            "Validates evidence and metrics",
            "Issues findings and certification",
            "Recommends remediations and retests",
        ],
    )
    board_ethics_committee = HumanAgentConfig(
        agent_id="ai_ethics_board",
        agent_type="human_mock",
        system_prompt="AI Ethics Board providing ethical oversight, bias assessment, and responsible AI deployment approval.",
        name="AI Ethics Board",
        role="Ethics & Governance",
        experience_years=16,
        background="AI ethics and governance",
        agent_description=(
            "Oversight body that challenges assumptions, protects users, and authorizes responsible deployment."
        ),
        agent_capabilities=[
            "Reviews ethical risks and mitigations",
            "Interrogates bias and cohort impacts",
            "Sets responsible use guardrails",
            "Grants or withholds ethical approval",
        ],
    )

    # Stakeholder (Chief Product Officer) for AI launch priorities
    stakeholder = StakeholderConfig(
        agent_id="chief_product_officer",
        agent_type="stakeholder",
        system_prompt=(
            "You are the Chief Product Officer balancing AI safety, regulatory compliance, launch speed, and market competitiveness."
        ),
        model_name="o3",
        name="Chief Product Officer",
        role="Executive Stakeholder",
        persona_description="Innovation-focused, safety-conscious, values responsible AI deployment with competitive advantage.",
        agent_description=(
            "Executive decision‑maker who integrates product strategy with safety and compliance, and owns the launch call."
        ),
        agent_capabilities=[
            "Prioritizes roadmap vs risk posture",
            "Arbitrates cross‑functional trade‑offs",
            "Approves staged rollout plans",
            "Holds teams to evidence‑based gates",
        ],
        response_latency_steps_min=1,
        response_latency_steps_max=2,
        push_probability_per_timestep=0.15,
        suggestion_rate=0.6,
        clarification_reply_rate=0.8,
        strictness=0.7,
        verbosity=2,
        preference_data=PreferenceSnapshot(
            preferences=[
                Preference(name="quality", weight=0.4),
                Preference(name="compliance", weight=0.3),
                Preference(name="speed", weight=0.2),
                Preference(name="cost", weight=0.1),
            ]
        ),
    )

    return {
        "ai_safety_engineer": ai_safety_engineer,
        "red_team_specialist": red_team_specialist,
        "ml_safety_researcher": ml_safety_researcher,
        "privacy_engineer": privacy_engineer,
        "compliance_analyst": compliance_analyst,
        "security_architect": security_architect,
        "devops_engineer": devops_engineer,
        "product_manager": product_manager,
        "documentation_specialist": documentation_specialist,
        "chief_ai_officer": chief_ai_officer,
        "security_officer": security_officer,
        "privacy_officer": privacy_officer,
        "legal_counsel": legal_counsel,
        "product_executive": product_executive,
        "external_auditor": external_auditor,
        "board_ethics_committee": board_ethics_committee,
        "stakeholder": stakeholder,
    }


def create_team_timeline():
    """Create safety-first coordination timeline for Gen-AI Feature Launch."""

    cfg = create_team_configs()
    return {
        0: [
            # Phase 1: Core Safety & Product Team
            (
                "add",
                cfg["ai_safety_engineer"],
                "AI safety framework and testing infrastructure",
            ),
            ("add", cfg["product_manager"], "Product definition and requirements"),
            (
                "add",
                cfg["security_architect"],
                "Threat modeling and security architecture",
            ),
            ("add", cfg["privacy_engineer"], "Privacy by design and data protection"),
        ],
        5: [
            # Phase 2: Threat Assessment & Red Team
            (
                "add",
                cfg["red_team_specialist"],
                "Adversarial testing and attack scenarios",
            ),
            (
                "add",
                cfg["ml_safety_researcher"],
                "Hallucination detection and bias evaluation",
            ),
            (
                "add",
                cfg["compliance_analyst"],
                "DPIA and regulatory compliance mapping",
            ),
        ],
        12: [
            # Phase 3: Infrastructure & Documentation
            (
                "add",
                cfg["devops_engineer"],
                "Monitoring infrastructure and observability",
            ),
            (
                "add",
                cfg["documentation_specialist"],
                "Model cards and audit documentation",
            ),
        ],
        18: [
            # Phase 4: Executive Review & Approvals
            ("add", cfg["chief_ai_officer"], "AI governance and ethics oversight"),
            ("add", cfg["privacy_officer"], "Privacy impact assessment approval"),
            ("add", cfg["security_officer"], "Security controls validation"),
        ],
        25: [
            # Phase 5: Final Approvals & Launch Readiness
            ("add", cfg["legal_counsel"], "Legal compliance and transparency review"),
            ("add", cfg["product_executive"], "Launch decision and business approval"),
            (
                "add",
                cfg["external_auditor"],
                "Independent safety audit and certification",
            ),
        ],
        28: [
            # Phase 6: Ethics Board Final Approval
            (
                "add",
                cfg["board_ethics_committee"],
                "Final ethics and responsible AI approval",
            ),
        ],
    }
