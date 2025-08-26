from manager_agent_gym.schemas.core.workflow import Workflow
from manager_agent_gym.schemas.core.tasks import Task
from manager_agent_gym.schemas.core.base import TaskStatus
from uuid import uuid4
from examples.common_stakeholders import create_stakeholder_agent
from .preferences import create_preferences
from manager_agent_gym.schemas.preferences import Constraint


def create_workflow() -> Workflow:
    wf = Workflow(
        name="Suez Logistics – End-to-End Supply Chain Planning",
        workflow_goal=(
            "Integrated S&OP for a Suez-based logistics operator covering demand forecasting, "
            "vessel/convoy planning, capacity & intermodal allocation, customs/DG compliance, "
            "and execution control with risk contingencies."
        ),
        owner_id=uuid4(),
    )

    # ---------------------------
    # PHASE 1 — Forecasting & Strategy
    # ---------------------------
    demand_forecast = Task(
        name="Demand & Volume Forecast",
        description=(
            "Build multi-horizon demand forecast combining customer bookings pipeline, seasonality, "
            "and disruption signals; publish volume bands with confidence intervals."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=10.0,
        estimated_cost=1200.0,
    )
    demand_forecast.subtasks = [
        Task(
            name="Historical & Seasonality Analysis",
            description="Analyze 24–36 months of lanes/commodities to capture seasonal effects.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=450.0,
        ),
        Task(
            name="Bookings Pipeline & Cancellations",
            description="Integrate CRM pipeline, historical no-show/cancel rates into forecast.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=350.0,
        ),
        Task(
            name="Disruption & Weather Signals",
            description="Overlay disruption indicators (weather, port congestion) into scenario bands.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=400.0,
        ),
    ]

    network_capacity = Task(
        name="Network & Capacity Plan",
        description=(
            "Allocate vessel slots, rail/road capacity, yard space, and warehouse throughput; "
            "establish tactical plan for the planning window with buffers."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=12.0,
        estimated_cost=1600.0,
        dependency_task_ids=[demand_forecast.task_id],
    )
    network_capacity.subtasks = [
        Task(
            name="Vessel Slot Allocation",
            description="Match capacity by lane; hold safety stock for priority customers.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=500.0,
        ),
        Task(
            name="Yard/Warehouse Throughput",
            description="Balance yard slots and warehouse shifts to forecasted volumes.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=500.0,
        ),
        Task(
            name="Rail/Road Allocation",
            description="Reserve drayage/rail capacity with carriers and set SLAs.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
    ]

    # ---------------------------
    # PHASE 2 — Suez Transit, Rotation & Compliance
    # ---------------------------
    transit_slot_planning = Task(
        name="Suez Transit Slot & Convoy Planning",
        description=(
            "Coordinate canal convoy/slot planning and align with departure/arrival rotations; "
            "build alternatives in case of delays."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=8.0,
        estimated_cost=1000.0,
        dependency_task_ids=[network_capacity.task_id],
    )
    rotation_alignment = Task(
        name="Vessel ETA & Rotation Alignment",
        description="Align rotations and turnaround times across ports; publish ETA commitments.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=8.0,
        estimated_cost=900.0,
        dependency_task_ids=[transit_slot_planning.task_id],
    )

    customs_docs = Task(
        name="Customs & Documentation",
        description=(
            "Prepare export/import documentation (manifests, certificates) with data validation and "
            "pre-arrival filing where applicable."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=10.0,
        estimated_cost=900.0,
        dependency_task_ids=[network_capacity.task_id],
    )
    customs_docs.subtasks = [
        Task(
            name="Data Validation & HS Codes",
            description="Validate shipper/consignee and HS codes; correct common data quality issues.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=250.0,
        ),
        Task(
            name="Pre-Arrival/Advance Filing",
            description="Submit mandatory filings per lane; track acknowledgements.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=300.0,
        ),
        Task(
            name="Certificates & Permits",
            description="Collect certificates of origin, phytosanitary, and other permits as needed.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=350.0,
        ),
    ]

    dangerous_goods = Task(
        name="Dangerous Goods (DG) Screening",
        description="Screen for DG classes; prepare declarations and stowage restrictions.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=6.0,
        estimated_cost=600.0,
        dependency_task_ids=[customs_docs.task_id],
    )

    # ---------------------------
    # PHASE 3 — Execution Enablement
    # ---------------------------
    equipment_reposition = Task(
        name="Equipment & Container Repositioning",
        description="Plan empty container repositioning and chassis allocation across depots.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=8.0,
        estimated_cost=800.0,
        dependency_task_ids=[network_capacity.task_id],
    )
    intermodal_allocation = Task(
        name="Intermodal & Drayage Allocation",
        description="Confirm trucking/rail bookings and dispatch windows for gate moves.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=8.0,
        estimated_cost=900.0,
        dependency_task_ids=[network_capacity.task_id, rotation_alignment.task_id],
    )
    yard_warehouse = Task(
        name="Yard & Warehouse Plan",
        description="Set yard slotting, warehouse shift plans, and labor rosters for inbound/outbound.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=8.0,
        estimated_cost=900.0,
        dependency_task_ids=[network_capacity.task_id],
    )

    bunker_emissions = Task(
        name="Bunker Fuel & Emissions Plan",
        description="Estimate bunker needs and compile emissions reporting requirements for voyages.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=6.0,
        estimated_cost=700.0,
        dependency_task_ids=[network_capacity.task_id],
    )

    customer_bookings = Task(
        name="Customer Bookings & SLA Matrix",
        description="Confirm allocations, service levels, and cutoffs with priority/routed customers.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=6.0,
        estimated_cost=500.0,
        dependency_task_ids=[network_capacity.task_id],
    )

    risk_contingency = Task(
        name="Risk & Contingency Planning",
        description="Define reroute/hold/advance options with triggers for weather/security/port events.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=6.0,
        estimated_cost=600.0,
        dependency_task_ids=[transit_slot_planning.task_id, network_capacity.task_id],
    )

    control_tower = Task(
        name="Execution Control Tower Setup",
        description="Stand up daily ops room with dashboards, exception queues, and comms protocol.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=10.0,
        estimated_cost=1000.0,
        dependency_task_ids=[
            customer_bookings.task_id,
            intermodal_allocation.task_id,
            yard_warehouse.task_id,
        ],
    )

    gate_cutoffs = Task(
        name="Gate-In & Cutoff Management",
        description="Publish/document cutoffs (docs, gate-in, VGM) and enforce exceptions policy.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=4.0,
        estimated_cost=300.0,
        dependency_task_ids=[customs_docs.task_id, customer_bookings.task_id],
    )

    daily_ops = Task(
        name="Daily Operations & Exception Handling",
        description="Run the plan; resolve exceptions via playbooks; escalate per SLA matrix.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=24.0,
        estimated_cost=2400.0,
        dependency_task_ids=[
            control_tower.task_id,
            gate_cutoffs.task_id,
            dangerous_goods.task_id,
        ],
    )

    kpi_review = Task(
        name="KPI Review & Post-Mortem",
        description="Analyze OTIF, dwell time, utilization, and cost variance; publish learnings.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=6.0,
        estimated_cost=400.0,
        dependency_task_ids=[daily_ops.task_id],
    )

    # Register tasks
    for t in [
        demand_forecast,
        network_capacity,
        transit_slot_planning,
        rotation_alignment,
        customs_docs,
        dangerous_goods,
        equipment_reposition,
        intermodal_allocation,
        yard_warehouse,
        bunker_emissions,
        customer_bookings,
        risk_contingency,
        control_tower,
        gate_cutoffs,
        daily_ops,
        kpi_review,
    ]:
        wf.add_task(t)

    # Constraints for Suez logistics flow and confidentiality
    wf.constraints.extend(
        [
            Constraint(
                name="Forecast Completed",
                description="Demand & volume forecast must be produced as basis for planning.",
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=["Demand & Volume Forecast"],
                metadata={},
            ),
            Constraint(
                name="Suez Transit Slot Confirmed",
                description="Transit slot/convoy plan must be confirmed before vessel departure.",
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=[
                    "Suez Transit Slot & Convoy Planning",
                    "Vessel ETA & Rotation Alignment",
                ],
                metadata={},
            ),
            Constraint(
                name="Customs Documents Complete Before Gate-In",
                description="Customs documentation must be completed and validated before gate-in cutoffs.",
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=[
                    "Customs & Documentation",
                    "Gate-In & Cutoff Management",
                ],
                metadata={},
            ),
            Constraint(
                name="Dangerous Goods Cleared Before Load",
                description="DG screening/declaration must be approved prior to load planning.",
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=[
                    "Dangerous Goods (DG) Screening",
                    "Daily Operations & Exception Handling",
                ],
                metadata={},
            ),
            Constraint(
                name="Customer SLA Acknowledged",
                description="Customers must acknowledge SLA matrix and cutoffs before dispatch.",
                constraint_type="organizational",
                enforcement_level=0.9,
                applicable_task_types=[
                    "Customer Bookings & SLA Matrix",
                    "Execution Control Tower Setup",
                ],
                metadata={},
            ),
            Constraint(
                name="Emissions Reporting Integrity",
                description="Emissions reporting must be compiled per voyage as required by operators/regulators.",
                constraint_type="organizational",
                enforcement_level=0.85,
                applicable_task_types=["Bunker Fuel & Emissions Plan"],
                metadata={},
            ),
            Constraint(
                name="PII and Secrets Redaction",
                description="Confidential info must be redacted or access-controlled in artifacts and comms.",
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=[
                    "Customs & Documentation",
                    "Execution Control Tower Setup",
                    "Daily Operations & Exception Handling",
                ],
                metadata={
                    "prohibited_keywords": [
                        "password",
                        "api key",
                        "secret key",
                        "private key",
                        "account_number",
                    ]
                },
            ),
        ]
    )

    # Stakeholder (optional – tolerant to absence)
    try:
        prefs = create_preferences()
        stakeholder = create_stakeholder_agent(persona="balanced", preferences=prefs)
        wf.add_agent(stakeholder)
    except Exception:
        pass

    return wf
