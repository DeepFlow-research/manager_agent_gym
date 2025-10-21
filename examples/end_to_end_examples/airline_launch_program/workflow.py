"""
Airline Launch Program Demo

Real-world use case: UK airline startup securing AOC and Operating Licence.

Demonstrates:
- Multi-track regulatory certification coordination with critical path dependencies
- Complex aviation safety and security compliance management under CAA oversight
- Resource-constrained project execution with parallel workstream management
- Stakeholder coordination across aviation authorities, lessors, airports, and service providers
- Risk-based decision making in heavily regulated industry with safety-critical requirements
- Escalation management for regulatory findings and compliance gaps
"""

from uuid import uuid4, UUID

from manager_agent_gym.schemas.domain.workflow import Workflow
from manager_agent_gym.schemas.domain.task import Task
from manager_agent_gym.schemas.domain.base import TaskStatus
from manager_agent_gym.schemas.preferences import Constraint
from manager_agent_gym.core.workflow.services import WorkflowMutations


def create_workflow() -> Workflow:
    """Create Airline Launch Program workflow with parallel certification tracks and dependencies."""

    workflow = Workflow(
        name="UK Airline Launch Program - AOC & Operating Licence",
        workflow_goal=(
            """
            Objective: Execute a structured airline launch program in the UK, securing both the Air Operator Certificate
            (AOC) and Operating Licence (OL) from the Civil Aviation Authority (CAA), demonstrating compliance with
            aviation safety, airworthiness, security, economic, and consumer protection requirements, and achieving
            readiness for safe, reliable, and commercially viable operations.

            Primary deliverables:
            - Approved Air Operator Certificate (AOC) with validated Operations Manuals (OM-A/B/C/D), Safety Management
              System (SMS), Compliance Monitoring, and training records meeting UK Reg (EU) 965/2012 and ANO 2016.
            - Granted Operating Licence (OL) with evidence of UK principal place of business, majority ownership/control,
              financial fitness, and binding insurance contracts compliant with Reg (EC) 785/2004.
            - Airworthiness approvals: Part-CAMO and Part-145 arrangements (in-house or contracted), Aircraft
              Registration Certificates, Certificates of Airworthiness (CofA) and Airworthiness Review Certificates (ARC),
              and reliability/maintenance programs.
            - Aviation security package: airline security programme approved under the National Aviation Security Programme
              (NASP), staff vetting and training records, and use of government-approved screening equipment.
            - Dangerous goods (DG) approval (if applicable): CAA Form SRG2807 submission, DG training program approval,
              and Ops Manual DG procedures integrated into compliance monitoring.
            - Insurance & liability package: binding certificates covering passenger, baggage, cargo, and third-party
              liabilities with required minima.
            - Airport and slot access approvals: slot confirmations at coordinated airports (via ACL), handling contracts,
              ground operations arrangements, and disruption management plan compliant with UK261 passenger rights.
            - Governance package: decision logs, proving flight records, CAA inspection findings and closures, executive
              sign-offs, and board-approved readiness evidence.

            Acceptance criteria (high-level):
            - AOC issued with no unresolved CAA findings; proving flights and inspections completed successfully.
            - OL granted on demonstration of financial fitness, ownership/control, and compliant insurance coverage.
            - CAMO/Part-145 arrangements validated; ARC/CofA issued for all fleet aircraft; reliability and MEL/GMEL
              programs approved.
            - Airline security programme accepted by CAA; 100% of relevant staff vetted and trained; compliance with
              NASP evidenced.
            - Dangerous goods approval (where applicable) granted; DG procedures integrated into Ops Manual and training
              records available.
            - Slots confirmed at intended airports; ground handling and disruption management plans signed off.
            - Formal sign-offs present from Accountable Manager, nominated postholders (Flight Ops, Ground Ops,
              Continuing Airworthiness, Crew Training, Safety, Security), and Board of Directors.
            - Governance documentation demonstrates regulatory engagement, escalation handling, and final approval.

            Constraints (soft):
            - Target horizon: complete certification and launch readiness in ≤ 12 weeks of simulated effort; avoid >7-day
              stalls on critical-path milestones (AOC, OL, airworthiness approvals).
            - Budget guardrail: stay within ±20% of projected certification, legal, insurance, and operational setup costs
              absent justified scope changes.
            - Transparency: prefer proactive disclosure of regulatory issues or resource gaps, with remediation and
              mitigation plans, to maximize regulator trust and launch confidence.
            """
        ),
        owner_id=uuid4(),
    )

    # Phase 1: Foundation & Governance Setup
    foundation_setup = Task(
        id=UUID(int=0),
        name="Foundation & Corporate Structure",
        description=(
            "Establish UK corporate structure, appoint nominated postholders, define governance framework, "
            "and secure UK principal place of business to meet CAA requirements."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=8.0,
        estimated_cost=1200.0,
    )
    foundation_setup.subtasks = [
        Task(
            id=UUID(int=100),
            name="Corporate Structure & Postholders",
            description="Establish UK corporate entity and appoint CAA-required nominated postholders for key functions.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=450.0,
        ),
        Task(
            id=UUID(int=101),
            name="UK Principal Place of Business",
            description="Secure and validate UK principal place of business meeting CAA location and control requirements.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=2.0,
            estimated_cost=300.0,
        ),
        Task(
            id=UUID(int=102),
            name="Governance Framework & Policies",
            description="Develop governance framework, decision-making authorities, and corporate policies.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=450.0,
        ),
    ]

    # Phase 2: Operations Manual Development
    operations_manual = Task(
        id=UUID(int=1),
        name="Operations Manual (OM-A/B/C/D) Development",
        description=(
            "Develop comprehensive Operations Manual covering General (OM-A), Aircraft Operating (OM-B), "
            "Route & Aerodrome (OM-C), and Training (OM-D) procedures compliant with UK regulations."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=16.0,
        estimated_cost=2400.0,
        dependency_task_ids=[foundation_setup.id],
    )
    operations_manual.subtasks = [
        Task(
            id=UUID(int=110),
            name="OM-A General Procedures",
            description="Develop OM-A covering general procedures, emergency response, and operational control.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
        Task(
            id=UUID(int=111),
            name="OM-B Aircraft Operating Procedures",
            description="Develop OM-B covering aircraft-specific operating procedures and performance data.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
        Task(
            id=UUID(int=112),
            name="OM-C Route & Aerodrome Information",
            description="Develop OM-C covering route procedures, aerodrome information, and navigation requirements.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
        Task(
            id=UUID(int=113),
            name="OM-D Training Program",
            description="Develop OM-D covering pilot and crew training programs, checking requirements, and competency standards.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
    ]

    # Phase 3: Safety Management System
    safety_management = Task(
        id=UUID(int=2),
        name="Safety Management System (SMS) Implementation",
        description=(
            "Implement comprehensive SMS including safety policy, risk management, safety assurance, "
            "and safety promotion components meeting ICAO Annex 19 and UK requirements."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=12.0,
        estimated_cost=1800.0,
        dependency_task_ids=[foundation_setup.id],
    )
    safety_management.subtasks = [
        Task(
            id=UUID(int=120),
            name="Safety Policy & Objectives",
            description="Develop safety policy, objectives, and accountable manager commitment statements.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=450.0,
        ),
        Task(
            id=UUID(int=121),
            name="Safety Risk Management",
            description="Establish safety risk management processes including hazard identification and risk assessment.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
        Task(
            id=UUID(int=122),
            name="Safety Assurance & Monitoring",
            description="Implement safety assurance processes including monitoring, measurement, and continuous improvement.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=450.0,
        ),
        Task(
            id=UUID(int=123),
            name="Safety Promotion & Training",
            description="Develop safety promotion programs including communication, training, and safety culture initiatives.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=2.0,
            estimated_cost=300.0,
        ),
    ]

    # Phase 4: Airworthiness Management
    airworthiness_management = Task(
        id=UUID(int=3),
        name="Airworthiness & CAMO Arrangements",
        description=(
            "Establish Part-CAMO arrangements, aircraft registration, maintenance programs, "
            "and continuing airworthiness management organization compliance."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=14.0,
        estimated_cost=2100.0,
        dependency_task_ids=[operations_manual.id],
    )
    airworthiness_management.subtasks = [
        Task(
            id=UUID(int=130),
            name="CAMO Approval & Organization",
            description="Establish Part-CAMO organization or contract arrangements for continuing airworthiness management.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
        Task(
            id=UUID(int=131),
            name="Aircraft Registration & Certificates",
            description="Obtain aircraft registration certificates and validate certificates of airworthiness (CofA).",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=450.0,
        ),
        Task(
            id=UUID(int=132),
            name="Maintenance Programs & Reliability",
            description="Develop aircraft maintenance programs, MEL/GMEL, and reliability monitoring systems.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
        Task(
            id=UUID(int=133),
            name="Part-145 Maintenance Arrangements",
            description="Establish Part-145 maintenance organization arrangements and approve maintenance contracts.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=450.0,
        ),
    ]

    # Phase 5: Aviation Security Programme
    aviation_security = Task(
        id=UUID(int=4),
        name="Aviation Security Programme & NASP Compliance",
        description=(
            "Develop airline security programme compliant with NASP, implement staff vetting, "
            "security training, and screening equipment arrangements."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=10.0,
        estimated_cost=1500.0,
        dependency_task_ids=[foundation_setup.id],
    )
    aviation_security.subtasks = [
        Task(
            id=UUID(int=140),
            name="Airline Security Programme",
            description="Develop comprehensive airline security programme meeting NASP requirements and CAA approval.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
        Task(
            id=UUID(int=141),
            name="Staff Vetting & Security Training",
            description="Implement staff security vetting processes and deliver required security training programs.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=450.0,
        ),
        Task(
            id=UUID(int=142),
            name="Security Equipment & Procedures",
            description="Arrange approved screening equipment and establish security operational procedures.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=450.0,
        ),
    ]

    # Phase 6: Financial Fitness & Insurance
    financial_fitness = Task(
        id=UUID(int=5),
        name="Financial Fitness & Insurance Package",
        description=(
            "Demonstrate financial fitness for Operating Licence, secure required insurance coverage, "
            "and establish financial monitoring and reporting systems."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=8.0,
        estimated_cost=1200.0,
        dependency_task_ids=[foundation_setup.id],
    )
    financial_fitness.subtasks = [
        Task(
            id=UUID(int=150),
            name="Financial Fitness Assessment",
            description="Prepare financial fitness documentation including business plan, cash flow projections, and funding evidence.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
        Task(
            id=UUID(int=151),
            name="Insurance Coverage & Binding",
            description="Secure binding insurance certificates for passenger, baggage, cargo, and third-party liabilities.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=2.0,
            estimated_cost=300.0,
        ),
        Task(
            id=UUID(int=152),
            name="Financial Monitoring Systems",
            description="Establish financial monitoring and reporting systems for ongoing compliance demonstration.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=2.0,
            estimated_cost=300.0,
        ),
    ]

    # Phase 7: Airport Operations & Slot Access
    airport_operations = Task(
        id=UUID(int=6),
        name="Airport Operations & Slot Coordination",
        description=(
            "Secure airport slots, establish ground handling contracts, develop disruption management plans, "
            "and ensure compliance with passenger rights regulations."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=10.0,
        estimated_cost=1500.0,
        dependency_task_ids=[operations_manual.id, aviation_security.id],
    )
    airport_operations.subtasks = [
        Task(
            id=UUID(int=160),
            name="Slot Coordination & Confirmations",
            description="Secure slot confirmations at coordinated airports through ACL and airport slot coordinators.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=450.0,
        ),
        Task(
            id=UUID(int=161),
            name="Ground Handling Contracts",
            description="Negotiate and finalize ground handling contracts covering passenger, baggage, cargo, and ramp services.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=450.0,
        ),
        Task(
            id=UUID(int=162),
            name="Disruption Management & Passenger Rights",
            description="Develop disruption management plans and passenger rights compliance procedures under UK261.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=2.0,
            estimated_cost=300.0,
        ),
        Task(
            id=UUID(int=163),
            name="Airport Security & Access Arrangements",
            description="Establish airport security access arrangements and operational coordination protocols.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=2.0,
            estimated_cost=300.0,
        ),
    ]

    # Phase 8: AOC Application & Proving Flights
    aoc_application = Task(
        id=UUID(int=7),
        name="AOC Application & Proving Flights",
        description=(
            "Submit formal AOC application, conduct proving flights, address CAA inspection findings, "
            "and achieve AOC issuance with operational approvals."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=12.0,
        estimated_cost=1800.0,
        dependency_task_ids=[
            safety_management.id,
            airworthiness_management.id,
            aviation_security.id,
        ],
    )
    aoc_application.subtasks = [
        Task(
            id=UUID(int=170),
            name="AOC Application Submission",
            description="Compile and submit comprehensive AOC application package to CAA with all supporting documentation.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
        Task(
            id=UUID(int=171),
            name="CAA Inspections & Findings",
            description="Support CAA inspections, address findings, and implement corrective actions as required.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
        Task(
            id=UUID(int=172),
            name="Proving Flights & Demonstrations",
            description="Conduct proving flights and operational demonstrations to validate readiness and competency.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
    ]

    # Phase 9: Operating Licence & Launch Readiness
    operating_licence = Task(
        id=UUID(int=8),
        name="Operating Licence & Launch Approval",
        description=(
            "Submit Operating Licence application, demonstrate ongoing compliance, "
            "obtain final governance approvals, and achieve launch readiness certification."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=8.0,
        estimated_cost=1200.0,
        dependency_task_ids=[
            financial_fitness.id,
            airport_operations.id,
            aoc_application.id,
        ],
    )
    operating_licence.subtasks = [
        Task(
            id=UUID(int=180),
            name="Operating Licence Application",
            description="Submit Operating Licence application with financial fitness, ownership, and insurance evidence.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=450.0,
        ),
        Task(
            id=UUID(int=181),
            name="Final Governance Approvals",
            description="Obtain final board approvals, postholder sign-offs, and accountable manager certification.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=2.0,
            estimated_cost=300.0,
        ),
        Task(
            id=UUID(int=182),
            name="Launch Readiness Validation",
            description="Conduct final readiness validation, systems testing, and launch go/no-go decision.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=450.0,
        ),
    ]

    for task in [
        foundation_setup,
        operations_manual,
        safety_management,
        airworthiness_management,
        aviation_security,
        financial_fitness,
        airport_operations,
        aoc_application,
        operating_licence,
    ]:
        WorkflowMutations.add_task(workflow, task)

    # Aviation regulatory and safety constraints
    workflow.constraints.extend(
        [
            Constraint(
                name="CAA AOC Compliance",
                description=(
                    "Air Operator Certificate must be issued by CAA with no unresolved findings and successful proving flights."
                ),
                constraint_type="regulatory",
                enforcement_level=1.0,
                applicable_task_types=["AOC Application & Proving Flights"],
                metadata={},
            ),
            Constraint(
                name="Operating Licence Financial Fitness",
                description=(
                    "Operating Licence requires demonstrated financial fitness, UK ownership/control, and compliant insurance."
                ),
                constraint_type="regulatory",
                enforcement_level=1.0,
                applicable_task_types=["Operating Licence & Launch Approval"],
                metadata={},
            ),
            Constraint(
                name="Airworthiness Certification",
                description=(
                    "All aircraft must have valid CofA, ARC, and approved maintenance programs before operations."
                ),
                constraint_type="regulatory",
                enforcement_level=1.0,
                applicable_task_types=["Airworthiness & CAMO Arrangements"],
                metadata={},
            ),
            Constraint(
                name="Safety Management System",
                description=(
                    "SMS must be fully implemented and operational meeting ICAO Annex 19 and UK regulatory requirements."
                ),
                constraint_type="regulatory",
                enforcement_level=0.95,
                applicable_task_types=["Safety Management System (SMS) Implementation"],
                metadata={},
            ),
            Constraint(
                name="Aviation Security Compliance",
                description=(
                    "Aviation security programme must be approved under NASP with 100% staff vetting and training."
                ),
                constraint_type="regulatory",
                enforcement_level=0.95,
                applicable_task_types=["Aviation Security Programme & NASP Compliance"],
                metadata={},
            ),
            Constraint(
                name="Operations Manual Approval",
                description=(
                    "Operations Manual (OM-A/B/C/D) must be approved by CAA and compliant with UK Reg (EU) 965/2012."
                ),
                constraint_type="regulatory",
                enforcement_level=0.9,
                applicable_task_types=["Operations Manual (OM-A/B/C/D) Development"],
                metadata={},
            ),
            Constraint(
                name="Nominated Postholder Requirements",
                description=(
                    "All nominated postholders must be appointed and meet CAA competency and experience requirements."
                ),
                constraint_type="regulatory",
                enforcement_level=0.9,
                applicable_task_types=["Foundation & Corporate Structure"],
                metadata={},
            ),
            Constraint(
                name="Airport Slot Confirmation",
                description=(
                    "Airport slots must be confirmed at coordinated airports with valid handling and access arrangements."
                ),
                constraint_type="operational",
                enforcement_level=0.85,
                applicable_task_types=["Airport Operations & Slot Coordination"],
                metadata={},
            ),
            Constraint(
                name="Insurance Coverage Minima",
                description=(
                    "Insurance coverage must meet regulatory minima for passenger, baggage, cargo, and third-party liabilities."
                ),
                constraint_type="regulatory",
                enforcement_level=0.9,
                applicable_task_types=["Financial Fitness & Insurance Package"],
                metadata={},
            ),
        ]
    )

    return workflow
