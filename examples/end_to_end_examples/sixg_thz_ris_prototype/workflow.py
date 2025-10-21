"""
6G THz + RIS Field Prototype Demo

Scenario: University-led consortium delivers a time-bounded research prototype to
empirically evaluate a reconfigurable intelligent surface (RIS)-assisted THz link
(140–300 GHz) in an indoor lab testbed. Scope includes RF bring-up, RIS control,
beam training, channel sounding, security telemetry, and reproducibility.

This example is tightly scoped for running a research project with:
- Clear milestones and acceptance criteria
- Concrete dependencies across hardware, algorithms, and experiments
- Soft deadline guardrails to encourage timely delivery
- References to foundational standards and surveys for grounding
"""

from uuid import uuid4

from manager_agent_gym.schemas.domain.workflow import Workflow
from manager_agent_gym.schemas.domain.task import Task
from manager_agent_gym.schemas.domain.base import TaskStatus
from manager_agent_gym.schemas.preferences import Constraint
from manager_agent_gym.core.workflow.services import WorkflowMutations


def create_workflow() -> Workflow:
    """Create a well-scoped 6G THz+RIS research workflow with dependencies and deadlines."""

    workflow = Workflow(
        name="6G THz + RIS Field Prototype (Indoor Lab Testbed)",
        workflow_goal=(
            """
            Objective: Build and demonstrate a reproducible RIS-assisted THz link (≥10 Gbps PHY throughput over ≥10 m NLOS)
            in an indoor lab setting with security telemetry and compliance checks.

            Primary deliverables:
            - Working THz RF front-ends and baseband chain integrated with a programmable RIS tile (≥64 elements)
            - Beam training algorithm and control loop achieving stable NLOS link with measured SNR/throughput targets
            - Channel sounding dataset (≥200 room poses) with metadata and open reproducibility package
            - Security instrumentation with threat model and at least one adversarial drill (e.g., basic jamming/spoofing)
            - Compliance review: indoor use and EIRP guardrails aligned to local policy; safety/ethics approvals recorded
            - Final technical report: methodology, baseline comparisons, and limitations

            Supporting references (non-exhaustive anchors):
            - 3GPP TR 38.900 (channel models); IEEE 802.15.3d (THz WPAN); RIS surveys (Di Renzo et al.)
            - ITU-R focus on THz bands and measurement best-practices; open-source SDR/beam training repos

            Acceptance criteria (high-level):
            - Indoor NLOS demo with RIS-on vs RIS-off delta ≥ 8 dB SNR or ≥ 2× throughput improvement
            - Channel sounding dataset and code release reproducible on a pinned environment
            - Security telemetry active during demo; documented red-team drill and observed signals
            - Final report submitted by the deadline, with assumptions and limitations disclosed
            """
        ),
        owner_id=uuid4(),
    )

    # Phase 0: Foundations
    literature_survey = Task(
        name="Literature Survey & Baselines",
        description=(
            "Survey THz links, RIS-assisted propagation, beam training baselines; define evaluation metrics and targets."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=8.0,
        estimated_cost=0.0,
    )

    testbed_setup = Task(
        name="Testbed Setup & Spectrum Planning",
        description=(
            "Secure lab allocation, power/RF safety checks, indoor spectrum/EIRP guardrails, and fixture layout."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=10.0,
        estimated_cost=500.0,
        dependency_task_ids=[literature_survey.task_id],
    )

    # Phase 1: Hardware & Control
    thz_rf_bringup = Task(
        name="THz RF Front-End Bring-up",
        description=(
            "Assemble and validate RF front-ends (mixers, LO, antennas), baseband link, and calibration routines."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=14.0,
        estimated_cost=3000.0,
        dependency_task_ids=[testbed_setup.task_id],
    )

    ris_control = Task(
        name="RIS Control Plane Development",
        description=(
            "Develop API/firmware for RIS phase control, timing, and state management; integrate with host software."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=12.0,
        estimated_cost=1500.0,
        dependency_task_ids=[testbed_setup.task_id],
    )

    # Phase 2: Algorithms & Integration
    beam_training = Task(
        name="Beam Training Algorithm",
        description=(
            "Implement hierarchical/compressive beam search and control loop; baseline vs RIS-off; log SNR/throughput."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=12.0,
        estimated_cost=1000.0,
        dependency_task_ids=[thz_rf_bringup.task_id, ris_control.task_id],
    )

    phy_mac_integration = Task(
        name="PHY/MAC Prototype Integration",
        description=(
            "Integrate baseband, beam control, and scheduling; ensure stable operation for ≥10 m NLOS track."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=12.0,
        estimated_cost=1500.0,
        dependency_task_ids=[beam_training.task_id],
    )

    # Phase 3: Measurement & Security
    channel_sounding = Task(
        name="Channel Sounding Campaign",
        description=(
            "Run sounding across ≥200 poses; capture metadata (poses, RIS config) and produce dataset artifacts."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=16.0,
        estimated_cost=800.0,
        dependency_task_ids=[beam_training.task_id],
    )

    security_telemetry = Task(
        name="Security Telemetry & Threat Model",
        description=(
            "Instrument logs/alerts for spoofing/jamming; draft threat model and controls; run at least one drill."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=10.0,
        estimated_cost=400.0,
        dependency_task_ids=[phy_mac_integration.task_id],
    )

    compliance_review = Task(
        name="Compliance & EIRP Review",
        description=(
            "Validate indoor operation plan and EIRP guardrails; record lab safety/ethics approvals and signage."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=6.0,
        estimated_cost=0.0,
        dependency_task_ids=[testbed_setup.task_id],
    )

    # Phase 4: Reproducibility & Reporting
    reproducibility = Task(
        name="Reproducibility Package",
        description=(
            "Pin environment, scripts, and configs; dataset release notes; how-to-run; license and citation file."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=8.0,
        estimated_cost=0.0,
        dependency_task_ids=[channel_sounding.task_id],
    )

    final_report = Task(
        name="Final Report & Demo",
        description=(
            "Compile results, baselines, RIS-on vs off deltas, security drill evidence; record demo video; submit."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=10.0,
        estimated_cost=0.0,
        dependency_task_ids=[
            reproducibility.task_id,
            security_telemetry.task_id,
            compliance_review.task_id,
        ],
    )

    for task in [
        literature_survey,
        testbed_setup,
        thz_rf_bringup,
        ris_control,
        beam_training,
        phy_mac_integration,
        channel_sounding,
        security_telemetry,
        compliance_review,
        reproducibility,
        final_report,
    ]:
        WorkflowMutations.add_task(workflow, task)

    # Scenario constraints and deadline guardrails
    workflow.constraints.extend(
        [
            Constraint(
                name="RIS-THz Integrated Demo",
                description="Beam training and PHY/MAC must be integrated and demonstrated on NLOS track.",
                constraint_type="milestone",
                enforcement_level=0.95,
                applicable_task_types=["PHY/MAC Prototype Integration"],
                metadata={},
            ),
            Constraint(
                name="Reproducibility Package",
                description="Environment pinned and dataset/code release prepared with basic README and license.",
                constraint_type="research",
                enforcement_level=0.9,
                applicable_task_types=["Reproducibility Package"],
                metadata={},
            ),
            Constraint(
                name="Security Telemetry Active",
                description="Security telemetry instrumentation must be enabled during demo; drill evidence recorded.",
                constraint_type="security",
                enforcement_level=0.9,
                applicable_task_types=["Security Telemetry & Threat Model"],
                metadata={},
            ),
            Constraint(
                name="Indoor Compliance",
                description="Indoor spectrum/EIRP guardrails documented; lab safety/ethics sign-offs attached.",
                constraint_type="compliance",
                enforcement_level=0.9,
                applicable_task_types=["Compliance & EIRP Review"],
                metadata={},
            ),
            Constraint(
                name="Deadline",
                description="All primary deliverables locked by project deadline; avoid >5-day stalls on critical path.",
                constraint_type="deadline",
                enforcement_level=0.85,
                applicable_task_types=["Final Report & Demo"],
                metadata={"target_weeks": 8},
            ),
        ]
    )

    return workflow
