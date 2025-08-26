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

from uuid import uuid4, UUID

from manager_agent_gym.schemas.core.workflow import Workflow
from manager_agent_gym.schemas.core.tasks import Task
from manager_agent_gym.schemas.core.base import TaskStatus
from manager_agent_gym.schemas.preferences import Constraint


def create_workflow() -> Workflow:
    """Create Gen-AI Feature Launch workflow with safety-first governance and compliance focus."""

    workflow = Workflow(
        name="Gen-AI Feature Launch - Safety & Compliance",
        workflow_goal=(
            """
            Objective: Launch a user-facing GenAI feature with built-in safety gates to deliver useful assistance
            (e.g., drafting/search/summarization) while meeting privacy, security, and transparency expectations,
            and establishing governance evidence suitable for internal and external scrutiny.

            Primary deliverables:
            - Product definition pack: intended use and misuse, task boundaries, user journeys, success metrics, and
              out-of-scope behaviors (what the feature must refuse or route).
            - Data protection & DPIA bundle: data-flow maps, lawful basis/consent model, retention/minimization rules,
              DSR handling paths, third-party/model disclosures, and residual-risk register.
            - Threat model & control plan: risks across prompt injection, data exfiltration via tools, unsafe function
              calling, secrets exposure, rate/credit abuse; mapped controls incl. sandboxing, least privilege, filters.
            - Safety evaluation suite: red-team scenarios and abuse tests, hallucination/jailbreak metrics, benchmark
              results with failure analysis and a remediation log to "fix or fence" issues before launch.
            - Transparency & provenance assets: user-facing AI disclosures and capability limits, content labeling/
              watermarking or provenance where feasible, model/system cards, and policy copy for Help/ToS/Privacy.
            - Observability & guardrails: runtime moderation checks, PII/unsafe-content filters, event logging, alerting
              thresholds, and dashboards for safety/quality/cost; rollback and kill-switch procedures.
            - Pilot & rollout plan: design-partner cohort, A/B experiment design, acceptance gates, rollback criteria,
              staged exposure (internal → limited external → GA) with entry/exit criteria.
            - Governance package: decision logs, launch-gate materials, approvals (Product, Security, Privacy/Compliance,
              Legal), and audit-ready links to evidence and artifacts.

            Acceptance criteria (high-level):
            - Red-team coverage demonstrated across injection/exfiltration/unsafe tool use; all critical issues remediated
              or explicitly risk-accepted by the accountable owner with compensating controls.
            - DPIA completed with privacy controls validated in staging and production paths; residual risks documented
              and accepted; no unresolved high-risk privacy issues at launch gate.
            - Clear, testable transparency: disclosures present; labeling/provenance applied where applicable; telemetry
              shows safety checks executed in ≥99% of eligible events with alerting for misses.
            - Formal sign-offs captured for Security, Privacy/Compliance, Legal, and Product; launch-gate minutes and
              evidence stored and linkable for audit.
            """
        ),
        owner_id=uuid4(),
    )

    # Phase 1: Product Definition & Risk Assessment
    product_definition = Task(
        id=UUID(int=0),
        name="Product Definition & Use Case Specification",
        description=(
            "Define intended use cases, task boundaries, user journeys, success metrics, and "
            "explicit out-of-scope behaviors the AI feature must refuse or route."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=12.0,
        estimated_cost=1800.0,
    )
    product_definition.subtasks = [
        Task(
            id=UUID(int=100),
            name="Use Case & Boundary Definition",
            description="Document intended use cases, task boundaries, and explicit rejection criteria for unsafe/inappropriate requests.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=450.0,
        ),
        Task(
            id=UUID(int=101),
            name="User Journey & Success Metrics",
            description="Design user interaction flows, define success metrics, and establish baseline performance expectations.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=450.0,
        ),
        Task(
            id=UUID(int=102),
            name="Misuse Pattern & Rejection Framework",
            description="Catalog known misuse patterns, define rejection strategies, and create routing mechanisms for inappropriate requests.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=450.0,
        ),
        Task(
            id=UUID(int=103),
            name="Competitive Analysis & Feature Differentiation",
            description="Analyze competitive AI features, identify differentiation opportunities, and define unique value propositions.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=450.0,
        ),
    ]

    threat_modeling = Task(
        id=UUID(int=1),
        name="Threat Model & Security Control Planning",
        description=(
            "Comprehensive threat assessment covering prompt injection, data exfiltration, unsafe function "
            "calling, secrets exposure, and rate abuse with mapped security controls."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=16.0,
        estimated_cost=2400.0,
        dependency_task_ids=[product_definition.id],
    )
    threat_modeling.subtasks = [
        Task(
            id=UUID(int=110),
            name="Prompt Injection & Jailbreak Analysis",
            description="Catalog prompt injection techniques, jailbreak scenarios, and adversarial input patterns.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
        Task(
            id=UUID(int=111),
            name="Data Exfiltration & Function Calling Risks",
            description="Assess data leakage vectors, unsafe function calling scenarios, and tool misuse patterns.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
        Task(
            id=UUID(int=112),
            name="Secrets Exposure & Rate Abuse Scenarios",
            description="Model secrets leakage, API key exposure, and rate/credit abuse attack patterns.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=450.0,
        ),
        Task(
            id=UUID(int=113),
            name="Security Control Architecture",
            description="Design sandboxing, least privilege, input/output filtering, and rate limiting control systems.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=450.0,
        ),
        Task(
            id=UUID(int=114),
            name="PII Protection & Data Minimization",
            description="Implement PII detection, data minimization controls, and validation procedures for privacy protection.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=2.0,
            estimated_cost=300.0,
        ),
    ]

    # Phase 2: Privacy & Compliance Framework
    dpia_framework = Task(
        id=UUID(int=2),
        name="Data Protection Impact Assessment (DPIA)",
        description=(
            "Complete DPIA with data flow mapping, lawful basis determination, retention policies, "
            "and third-party disclosure analysis."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=14.0,
        estimated_cost=2100.0,
        dependency_task_ids=[threat_modeling.id],
    )
    dpia_framework.subtasks = [
        Task(
            id=UUID(int=120),
            name="Data Flow & Lawful Basis Mapping",
            description="Map all data flows, determine lawful basis for processing, and document consent mechanisms.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=5.0,
            estimated_cost=750.0,
        ),
        Task(
            id=UUID(int=121),
            name="Retention & Minimization Rules",
            description="Define data retention periods, minimization procedures, and automated deletion policies.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
        Task(
            id=UUID(int=122),
            name="Third-Party & Model Disclosure Analysis",
            description="Document third-party data sharing, model training implications, and disclosure requirements.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=5.0,
            estimated_cost=750.0,
        ),
    ]

    transparency_framework = Task(
        id=UUID(int=3),
        name="Transparency & Provenance System",
        description=(
            "Develop AI disclosures, capability documentation, content labeling, and model/system cards "
            "for user transparency and regulatory compliance."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=10.0,
        estimated_cost=1500.0,
        dependency_task_ids=[dpia_framework.id],
    )
    transparency_framework.subtasks = [
        Task(
            id=UUID(int=130),
            name="AI Disclosure & Capability Documentation",
            description="Create user-facing AI disclosures, capability limits, and interaction guidelines.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=5.0,
            estimated_cost=750.0,
        ),
        Task(
            id=UUID(int=131),
            name="Model Cards & System Documentation",
            description="Prepare comprehensive model/system cards with training data, capabilities, and limitations.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=5.0,
            estimated_cost=750.0,
        ),
    ]

    # Phase 3: Safety Evaluation & Red Team Testing
    safety_evaluation = Task(
        id=UUID(int=4),
        name="Safety Evaluation & Red Team Testing",
        description=(
            "Comprehensive safety testing including red team scenarios, abuse testing, hallucination metrics, "
            "and jailbreak resistance with remediation tracking."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=18.0,
        estimated_cost=2700.0,
        dependency_task_ids=[transparency_framework.id],
    )
    safety_evaluation.subtasks = [
        Task(
            id=UUID(int=140),
            name="Red Team Scenario Development",
            description="Design adversarial test scenarios for prompt injection, jailbreaking, and misuse attempts.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=5.0,
            estimated_cost=750.0,
        ),
        Task(
            id=UUID(int=141),
            name="Automated Safety Testing Infrastructure",
            description="Build automated test suites for safety violations, bias detection, and harmful output classification.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
        Task(
            id=UUID(int=142),
            name="Hallucination & Factual Accuracy Evaluation",
            description="Implement hallucination detection, factual accuracy benchmarks, and knowledge boundary testing.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
        Task(
            id=UUID(int=143),
            name="Human Adversarial Testing",
            description="Conduct manual red team exercises with security researchers and domain experts.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=450.0,
        ),
        Task(
            id=UUID(int=144),
            name="Failure Analysis & Remediation Planning",
            description="Analyze test failures, document remediation strategies, and track fix implementation progress.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=2.0,
            estimated_cost=300.0,
        ),
    ]

    observability_system = Task(
        id=UUID(int=5),
        name="Observability & Runtime Guardrails",
        description=(
            "Implement runtime monitoring, moderation checks, event logging, alerting, and kill-switch procedures "
            "for production safety and quality assurance."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=16.0,
        estimated_cost=2400.0,
        dependency_task_ids=[safety_evaluation.id],
    )
    observability_system.subtasks = [
        Task(
            id=UUID(int=150),
            name="Runtime Moderation & Filtering",
            description="Deploy real-time content moderation, PII detection, and unsafe content filtering systems.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=900.0,
        ),
        Task(
            id=UUID(int=151),
            name="Monitoring & Alerting Infrastructure",
            description="Set up dashboards, alerting thresholds, and automated monitoring for safety, quality, and cost metrics.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=5.0,
            estimated_cost=750.0,
        ),
        Task(
            id=UUID(int=152),
            name="Incident Response & Kill Switch Procedures",
            description="Implement emergency rollback procedures, kill switches, and incident response playbooks.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=5.0,
            estimated_cost=750.0,
        ),
    ]

    # Phase 4: Pilot & Rollout Strategy
    pilot_design = Task(
        id=UUID(int=6),
        name="Pilot & Controlled Rollout Design",
        description=(
            "Design staged rollout with design partners, A/B testing framework, acceptance gates, "
            "and progressive exposure controls from internal to general availability."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=12.0,
        estimated_cost=1800.0,
        dependency_task_ids=[observability_system.id],
    )
    pilot_design.subtasks = [
        Task(
            id=UUID(int=160),
            name="Design Partner Selection & Onboarding",
            description="Select trusted design partners, establish NDAs, and create feedback collection frameworks.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=900.0,
        ),
        Task(
            id=UUID(int=161),
            name="Staged Rollout Architecture",
            description="Design internal → limited external → GA progression with feature flags and circuit breakers.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=900.0,
        ),
    ]

    # Phase 5: Governance & Documentation
    governance_package = Task(
        id=UUID(int=7),
        name="Governance & Audit Documentation Package",
        description=(
            "Assemble comprehensive governance documentation including decision logs, approvals, "
            "audit trails, and evidence linkage for regulatory scrutiny."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=10.0,
        estimated_cost=1500.0,
        dependency_task_ids=[pilot_design.id],
    )
    governance_package.subtasks = [
        Task(
            id=UUID(int=170),
            name="Decision Logs & Launch Gate Materials",
            description="Document all governance decisions, risk acceptance, and launch gate approval materials.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
        Task(
            id=UUID(int=171),
            name="Cross-Functional Approvals & Sign-offs",
            description="Obtain formal approvals from Product, Security, Privacy/Compliance, and Legal stakeholders.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=450.0,
        ),
        Task(
            id=UUID(int=172),
            name="Audit Trail & Evidence Linkage",
            description="Create comprehensive audit trails linking all evidence, decisions, and approval artifacts.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=450.0,
        ),
    ]

    reproducibility_docs = Task(
        id=UUID(int=8),
        name="Documentation & Reproducibility Package",
        description=(
            "Complete technical documentation including prompt configurations, evaluation harnesses, "
            "data lineage, and operational playbooks for incident response."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=8.0,
        estimated_cost=1200.0,
        dependency_task_ids=[governance_package.id],
    )
    reproducibility_docs.subtasks = [
        Task(
            id=UUID(int=180),
            name="Technical Configuration Documentation",
            description="Document prompts, model configurations, versioned datasets, and evaluation seeds for reproducibility.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
        Task(
            id=UUID(int=181),
            name="Operational Playbooks & Incident Response",
            description="Create incident response procedures, on-call escalation guides, and operational runbooks.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
    ]

    # Phase 6: Post-Launch Monitoring Plan
    post_launch_plan = Task(
        id=UUID(int=9),
        name="Post-Launch Monitoring & Maintenance Plan",
        description=(
            "Establish ongoing monitoring SLAs, periodic re-evaluation procedures, drift detection, "
            "and controlled update processes for models and policies."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=8.0,
        estimated_cost=1200.0,
        dependency_task_ids=[reproducibility_docs.id],
    )
    post_launch_plan.subtasks = [
        Task(
            id=UUID(int=190),
            name="Continuous Monitoring SLA Definition",
            description="Define monitoring SLAs for safety, quality, latency, and cost with escalation procedures.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=450.0,
        ),
        Task(
            id=UUID(int=191),
            name="Model Drift Detection & Re-evaluation",
            description="Implement drift detection systems and periodic re-evaluation processes for model performance.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=450.0,
        ),
        Task(
            id=UUID(int=192),
            name="Controlled Update & Rollback Procedures",
            description="Establish controlled processes for model updates, policy changes, and emergency rollbacks.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=2.0,
            estimated_cost=300.0,
        ),
    ]

    for task in [
        product_definition,
        threat_modeling,
        dpia_framework,
        transparency_framework,
        safety_evaluation,
        observability_system,
        pilot_design,
        governance_package,
        reproducibility_docs,
        post_launch_plan,
    ]:
        workflow.add_task(task)

    # AI Safety and Compliance constraints for Gen-AI Feature Launch
    workflow.constraints.extend(
        [
            Constraint(
                name="Red Team Testing Required",
                description=(
                    "Comprehensive red team testing must be completed with all critical vulnerabilities remediated before launch."
                ),
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=["Safety Evaluation & Red Team Testing"],
                metadata={},
            ),
            Constraint(
                name="DPIA Completion Mandatory",
                description=(
                    "Data Protection Impact Assessment must be completed with documented risk acceptance before production deployment."
                ),
                constraint_type="regulatory",
                enforcement_level=1.0,
                applicable_task_types=["Data Protection Impact Assessment (DPIA)"],
                metadata={},
            ),
            Constraint(
                name="Multi-Stakeholder Approval Required",
                description=(
                    "Formal sign-offs from Product, Security, Privacy/Compliance, and Legal must be obtained before launch."
                ),
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=["Governance & Audit Documentation Package"],
                metadata={},
            ),
            Constraint(
                name="Safety Monitoring Infrastructure",
                description=(
                    "Runtime safety monitoring, kill switches, and incident response procedures must be operational before rollout."
                ),
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=["Observability & Runtime Guardrails"],
                metadata={},
            ),
            Constraint(
                name="Transparency Disclosure Requirements",
                description=(
                    "AI disclosures, capability limitations, and content labeling must be implemented for user transparency."
                ),
                constraint_type="regulatory",
                enforcement_level=0.9,
                applicable_task_types=["Transparency & Provenance System"],
                metadata={},
            ),
            Constraint(
                name="Threat Model Coverage",
                description=(
                    "Threat model must address prompt injection, data exfiltration, unsafe function calling, and rate abuse vectors."
                ),
                constraint_type="organizational",
                enforcement_level=0.9,
                applicable_task_types=["Threat Model & Security Control Planning"],
                metadata={
                    "required_threat_categories": [
                        "prompt_injection",
                        "data_exfiltration",
                        "unsafe_function_calling",
                        "secrets_exposure",
                        "rate_abuse",
                    ]
                },
            ),
            Constraint(
                name="Staged Rollout Controls",
                description=(
                    "Controlled rollout must progress through internal → limited external → GA stages with defined gates."
                ),
                constraint_type="organizational",
                enforcement_level=0.8,
                applicable_task_types=["Pilot & Controlled Rollout Design"],
                metadata={},
            ),
            Constraint(
                name="Audit Trail Completeness",
                description=(
                    "Complete audit trail with linked evidence and decision documentation must be maintained for regulatory scrutiny."
                ),
                constraint_type="regulatory",
                enforcement_level=0.9,
                applicable_task_types=["Governance & Audit Documentation Package"],
                metadata={},
            ),
            Constraint(
                name="Safety Threshold Compliance",
                description=(
                    "Safety checks must execute in ≥99% of eligible events with automated alerting for misses."
                ),
                constraint_type="hard",
                enforcement_level=0.95,
                applicable_task_types=["Observability & Runtime Guardrails"],
                metadata={"minimum_safety_check_rate": 0.99, "alerting_required": True},
            ),
        ]
    )

    return workflow
