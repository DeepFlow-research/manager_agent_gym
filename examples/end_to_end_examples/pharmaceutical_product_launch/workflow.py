"""
Pharmaceutical Product Launch Demo

Real-world use case: Global pharmaceutical company launching new drug product.

Demonstrates:
- Sequential dependency management across 9 interconnected regulatory and manufacturing phases
- Safety-critical decision prioritization when regulatory compliance conflicts with commercial timelines
- Multi-stakeholder coordination across highly specialized domains (regulatory, quality, manufacturing, commercial)
- Long-horizon strategic planning with 10+ week critical path and complex approval gates
- Risk escalation and mitigation when patient safety signals or manufacturing deficiencies emerge
- Resource reallocation under strict regulatory constraints and budget pressures
"""

from uuid import uuid4, UUID

from manager_agent_gym.schemas.core.workflow import Workflow
from manager_agent_gym.schemas.core.tasks import Task
from manager_agent_gym.schemas.core.base import TaskStatus
from manager_agent_gym.schemas.preferences import Constraint


def create_workflow() -> Workflow:
    """Create pharmaceutical product launch workflow with regulatory and manufacturing phases."""

    workflow = Workflow(
        name="Pharmaceutical Product Launch - Global Registration",
        workflow_goal=(
            """
            Objective: Execute the launch of a new pharmaceutical product by securing regulatory approval, validating
            manufacturing and quality systems, and ensuring commercial, compliance, and supply readiness to deliver
            a safe, effective, and well-governed market entry across initial launch geographies.

            Primary deliverables:
            - Regulatory dossier (eCTD format) covering all required modules (quality, safety, nonclinical, clinical)
              submitted to FDA/EMA and aligned with ICH guidelines (Q8–Q11, M4).
            - Good Manufacturing Practice (cGMP) audit reports with validated processes, equipment qualification
              (IQ/OQ/PQ), and lot release readiness.
            - Quality by Design (QbD) and risk management package including critical quality attributes (CQAs),
              critical process parameters (CPPs), control strategy, and lifecycle monitoring plan.
            - Pre-Launch Activities Importation Request (PLAIR) or equivalent documentation to stage product for
              commercial release in compliance with FDA/EMA requirements.
            - Market access strategy including payer dossiers, HTA submissions, pricing models, and early access
              or compassionate use program approvals.
            - Distribution and supply chain readiness plan: validated logistics partners, cold-chain testing,
              serialization/track-and-trace compliance, and inventory ramp-up.
            - Pharmacovigilance system: safety management plan, adverse event reporting pathways, signal detection
              protocols, and risk minimization measures.
            - Governance package: decision logs, launch readiness reviews, regulatory correspondence, and board
              sign-offs evidencing accountability at each gate.

            Acceptance criteria (high-level):
            - Regulatory agencies (FDA/EMA or local authorities) formally accept submission with no critical
              deficiencies; first cycle review proceeds without major gaps in modules.
            - cGMP compliance confirmed by external inspection reports; no unresolved major observations.
            - QbD framework documented with linkages between CQAs, CPPs, and control strategy; reproducibility
              demonstrated across at least three validation batches.
            - Market access plans approved by internal governance and validated by payer/HTA feedback where
              available; launch pricing strategy documented and authorized.
            - Supply chain stress-tested with distribution partners; serialization and cold-chain controls verified.
            - Pharmacovigilance system tested with mock case processing and validated by safety/compliance team.
            - Formal sign-offs secured from Regulatory Affairs, Quality, Pharmacovigilance, Commercial, and
              Executive Board prior to commercial release.

            Constraints (soft):
            - Target horizon: complete launch readiness within ≤ 10 weeks of simulated effort; avoid critical path
              stalls >5 days on regulatory or manufacturing deliverables.
            - Budget guardrail: stay within ±20% of projected regulatory, manufacturing validation, and launch
              marketing costs absent justified scope changes.
            - Transparency: prefer proactive disclosure of known risks (e.g., supply constraints, safety signals)
              with mitigation plans over concealment to maximize regulator and stakeholder confidence.

            """
        ),
        owner_id=uuid4(),
    )

    # Phase 1: Regulatory Dossier Preparation
    regulatory_dossier = Task(
        id=UUID(int=0),
        name="Regulatory Dossier Preparation",
        description=(
            "Compile comprehensive eCTD dossier covering quality, safety, nonclinical, and clinical modules "
            "aligned with ICH guidelines for FDA/EMA submission."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=120.0,
        estimated_cost=18000.0,
    )
    regulatory_dossier.subtasks = [
        Task(
            id=UUID(int=100),
            name="Quality Module (M3)",
            description="Compile pharmaceutical quality data including drug substance/product specifications, manufacturing info, and analytical validation.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=40.0,
            estimated_cost=6000.0,
        ),
        Task(
            id=UUID(int=101),
            name="Nonclinical Module (M4)",
            description="Assemble nonclinical safety data including pharmacology, toxicology, and ADME studies per ICH guidelines.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=30.0,
            estimated_cost=4500.0,
        ),
        Task(
            id=UUID(int=102),
            name="Clinical Module (M5)",
            description="Compile clinical study reports, integrated summaries of safety/efficacy, and risk-benefit analysis.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=50.0,
            estimated_cost=7500.0,
        ),
    ]

    # Phase 2: Manufacturing Validation & cGMP Compliance
    manufacturing_validation = Task(
        id=UUID(int=1),
        name="Manufacturing Validation & cGMP Compliance",
        description=(
            "Execute cGMP validation including process qualification, equipment validation (IQ/OQ/PQ), "
            "and demonstrate manufacturing readiness for commercial production."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=100.0,
        estimated_cost=15000.0,
        dependency_task_ids=[regulatory_dossier.id],
    )
    manufacturing_validation.subtasks = [
        Task(
            id=UUID(int=200),
            name="Equipment Qualification (IQ/OQ/PQ)",
            description="Execute installation, operational, and performance qualification for manufacturing equipment.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=35.0,
            estimated_cost=5250.0,
        ),
        Task(
            id=UUID(int=201),
            name="Process Validation Batches",
            description="Manufacture and test three consecutive validation batches demonstrating process consistency.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=40.0,
            estimated_cost=6000.0,
        ),
        Task(
            id=UUID(int=202),
            name="Analytical Method Validation",
            description="Validate analytical methods for release testing and stability monitoring per ICH Q2(R1).",
            status=TaskStatus.PENDING,
            estimated_duration_hours=25.0,
            estimated_cost=3750.0,
        ),
    ]

    # Phase 3: Quality by Design (QbD) Framework
    qbd_framework = Task(
        id=UUID(int=2),
        name="Quality by Design (QbD) Framework",
        description=(
            "Establish QbD framework with critical quality attributes (CQAs), critical process parameters (CPPs), "
            "and control strategy for lifecycle management."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=80.0,
        estimated_cost=12000.0,
        dependency_task_ids=[manufacturing_validation.id],
    )
    qbd_framework.subtasks = [
        Task(
            id=UUID(int=300),
            name="Critical Quality Attributes (CQAs)",
            description="Define and justify CQAs linked to safety and efficacy with acceptance criteria.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=20.0,
            estimated_cost=3000.0,
        ),
        Task(
            id=UUID(int=301),
            name="Design Space Definition",
            description="Establish proven acceptable ranges for critical process parameters through experimental design.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=25.0,
            estimated_cost=3750.0,
        ),
        Task(
            id=UUID(int=302),
            name="Control Strategy",
            description="Develop comprehensive control strategy linking CQAs, CPPs, and monitoring throughout lifecycle.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=20.0,
            estimated_cost=3000.0,
        ),
        Task(
            id=UUID(int=303),
            name="Lifecycle Management Plan",
            description="Establish continued process verification and lifecycle management protocols for post-approval changes.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=15.0,
            estimated_cost=2250.0,
        ),
    ]

    # Phase 4: Pharmacovigilance System Setup
    pharmacovigilance = Task(
        id=UUID(int=3),
        name="Pharmacovigilance System Setup",
        description=(
            "Establish pharmacovigilance system with safety management plan, adverse event reporting, "
            "and signal detection protocols for post-market surveillance."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=70.0,
        estimated_cost=10500.0,
    )
    pharmacovigilance.subtasks = [
        Task(
            id=UUID(int=400),
            name="Risk Management Plan (RMP)",
            description="Develop comprehensive risk management plan with risk minimization measures and safety concerns.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=40.0,
            estimated_cost=6000.0,
        ),
        Task(
            id=UUID(int=401),
            name="Safety Database & Reporting System",
            description="Setup global adverse event collection, assessment, regulatory reporting, and signal detection infrastructure.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=30.0,
            estimated_cost=4500.0,
        ),
    ]

    # Phase 5: Supply Chain & Distribution Readiness
    supply_chain = Task(
        id=UUID(int=4),
        name="Supply Chain & Distribution Readiness",
        description=(
            "Validate distribution network with serialization compliance, cold-chain controls, "
            "and logistics partner qualification for global launch."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=90.0,
        estimated_cost=13500.0,
        dependency_task_ids=[manufacturing_validation.id],
    )
    supply_chain.subtasks = [
        Task(
            id=UUID(int=500),
            name="Serialization & Track-and-Trace",
            description="Implement serialization systems and track-and-trace compliance for anti-counterfeiting.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=35.0,
            estimated_cost=5250.0,
        ),
        Task(
            id=UUID(int=501),
            name="Cold-Chain Validation",
            description="Validate temperature-controlled distribution and storage capabilities with logistics partners.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=30.0,
            estimated_cost=4500.0,
        ),
        Task(
            id=UUID(int=502),
            name="Distribution Partner Qualification",
            description="Qualify and audit distribution partners for cGMP compliance and service capability.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=25.0,
            estimated_cost=3750.0,
        ),
    ]

    # Phase 6: Market Access Strategy
    market_access = Task(
        id=UUID(int=5),
        name="Market Access Strategy",
        description=(
            "Develop market access strategy with payer dossiers, HTA submissions, "
            "and pricing strategy for successful commercial launch."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=60.0,
        estimated_cost=9000.0,
        dependency_task_ids=[pharmacovigilance.id],
    )
    market_access.subtasks = [
        Task(
            id=UUID(int=600),
            name="Health Technology Assessment (HTA)",
            description="Prepare HTA submissions with health economic evidence and budget impact models.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=20.0,
            estimated_cost=3000.0,
        ),
        Task(
            id=UUID(int=601),
            name="Payer Value Dossiers",
            description="Develop payer-specific value dossiers with clinical and economic evidence packages.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=15.0,
            estimated_cost=2250.0,
        ),
        Task(
            id=UUID(int=602),
            name="Pricing Strategy & Models",
            description="Establish global pricing strategy with market-specific pricing models and access strategies.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=15.0,
            estimated_cost=2250.0,
        ),
        Task(
            id=UUID(int=603),
            name="Early Access Programs",
            description="Develop compassionate use and expanded access programs for pre-approval patient access.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=10.0,
            estimated_cost=1500.0,
        ),
    ]

    # Phase 7: Regulatory Submission & Review Management
    regulatory_submission = Task(
        id=UUID(int=6),
        name="Regulatory Submission & Review Management",
        description=(
            "Submit regulatory applications to FDA/EMA and manage review process "
            "including responses to regulatory questions and inspections."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=50.0,
        estimated_cost=7500.0,
        dependency_task_ids=[qbd_framework.id, market_access.id],
    )

    # Phase 8: Pre-Launch Readiness & Commercial Preparation
    prelaunch_readiness = Task(
        id=UUID(int=7),
        name="Pre-Launch Readiness & Commercial Preparation",
        description=(
            "Execute final launch readiness activities including commercial team training, "
            "inventory staging, and launch governance approvals."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=70.0,
        estimated_cost=10500.0,
        dependency_task_ids=[supply_chain.id, regulatory_submission.id],
    )
    prelaunch_readiness.subtasks = [
        Task(
            id=UUID(int=700),
            name="Commercial Team Training & Certification",
            description="Train and certify commercial teams on product profile, safety information, and regulatory compliance requirements.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=35.0,
            estimated_cost=5250.0,
        ),
        Task(
            id=UUID(int=701),
            name="Launch Inventory & Distribution Staging",
            description="Stage commercial inventory and finalize distribution readiness with validated supply chain partners.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=35.0,
            estimated_cost=5250.0,
        ),
    ]

    # Phase 9: Final Governance & Launch Authorization
    launch_authorization = Task(
        id=UUID(int=8),
        name="Final Governance & Launch Authorization",
        description=(
            "Secure final governance approvals from executive committee and regulatory authorities "
            "for commercial product release."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=30.0,
        estimated_cost=4500.0,
        dependency_task_ids=[prelaunch_readiness.id],
    )

    for task in [
        regulatory_dossier,
        manufacturing_validation,
        qbd_framework,
        pharmacovigilance,
        supply_chain,
        market_access,
        regulatory_submission,
        prelaunch_readiness,
        launch_authorization,
    ]:
        workflow.add_task(task)

    # Pharmaceutical regulatory and safety constraints
    workflow.constraints.extend(
        [
            Constraint(
                name="cGMP Compliance Required",
                description=(
                    "All manufacturing activities must comply with current Good Manufacturing Practice regulations."
                ),
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=["Manufacturing Validation & cGMP Compliance"],
                metadata={},
            ),
            Constraint(
                name="ICH Guideline Compliance",
                description=(
                    "Regulatory dossier must comply with ICH guidelines Q8-Q11 and M4 formatting requirements."
                ),
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=["Regulatory Dossier Preparation"],
                metadata={},
            ),
            Constraint(
                name="Patient Safety Paramount",
                description=(
                    "Patient safety considerations must take precedence over commercial timeline pressures."
                ),
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=[
                    "Pharmacovigilance System Setup",
                    "Risk Management Plan",
                ],
                metadata={},
            ),
            Constraint(
                name="Quality by Design Implementation",
                description=(
                    "QbD principles must be implemented with documented CQAs, CPPs, and control strategy."
                ),
                constraint_type="regulatory",
                enforcement_level=0.95,
                applicable_task_types=["Quality by Design (QbD) Framework"],
                metadata={},
            ),
            Constraint(
                name="Serialization Compliance",
                description=(
                    "Supply chain must implement serialization and track-and-trace per regulatory requirements."
                ),
                constraint_type="regulatory",
                enforcement_level=0.9,
                applicable_task_types=["Serialization & Track-and-Trace"],
                metadata={},
            ),
            Constraint(
                name="Cold-Chain Integrity",
                description=(
                    "Temperature-sensitive products must maintain cold-chain integrity throughout distribution."
                ),
                constraint_type="regulatory",
                enforcement_level=0.9,
                applicable_task_types=["Cold-Chain Validation"],
                metadata={},
            ),
            Constraint(
                name="Regulatory Inspection Readiness",
                description=(
                    "Manufacturing facilities must be inspection-ready with complete documentation."
                ),
                constraint_type="organizational",
                enforcement_level=0.85,
                applicable_task_types=[
                    "Equipment Qualification (IQ/OQ/PQ)",
                    "Process Validation Batches",
                ],
                metadata={},
            ),
            Constraint(
                name="Market Access Evidence Requirements",
                description=(
                    "Market access materials must include robust clinical and economic evidence packages."
                ),
                constraint_type="organizational",
                enforcement_level=0.8,
                applicable_task_types=[
                    "Health Technology Assessment (HTA)",
                    "Payer Value Dossiers",
                ],
                metadata={},
            ),
            Constraint(
                name="Cross-Functional Governance",
                description=(
                    "Major decisions must involve cross-functional input from regulatory, quality, safety, and commercial teams."
                ),
                constraint_type="organizational",
                enforcement_level=0.85,
                applicable_task_types=[
                    "Launch Readiness Review",
                    "Final Governance & Launch Authorization",
                ],
                metadata={},
            ),
        ]
    )

    return workflow
