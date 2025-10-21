"""
US Co‑op Bank — Internal Risk & Solvency Assessment (ORSA‑style / ICAAP‑aligned)
Note: ORSA is an insurance construct (NAIC Model 505). For a US co‑op bank/credit union,
this workflow mirrors ORSA principles while aligning with banking capital planning practices
(e.g., NCUA RBC/CCULR and Federal Reserve/OCC guidance on model risk and capital adequacy).

Demonstrates:
- Enterprise risk assessment across credit, market/IRRBB, liquidity, operational, and climate risk
- Capital planning under baseline/adverse/severe scenarios with management buffers
- Governance and model risk controls per SR 11‑7, proportional to firm size/complexity
- Board engagement and supervisory‑ready documentation
"""

from uuid import UUID
from manager_agent_gym.schemas.domain.workflow import Workflow
from manager_agent_gym.schemas.domain.task import Task
from manager_agent_gym.schemas.domain.base import TaskStatus
from manager_agent_gym.schemas.preferences import Constraint
from manager_agent_gym.core.workflow.services import WorkflowMutations


def create_workflow() -> Workflow:
    """Create an internal risk & solvency assessment workflow for a US co‑op bank."""
    workflow = Workflow(
        owner_id=UUID(int=626),
        name="US Co‑op Bank — Internal Risk & Solvency Assessment",
        workflow_goal=(
            """
            Objective: Produce a Board‑approved, supervisory‑ready internal risk and solvency assessment for the
            co‑operative bank/credit union. Align capital adequacy with risk profile under baseline and stressed
            conditions, demonstrate robust risk governance and model controls, and document recovery options.
            Primary deliverables:
            - Risk appetite statement with quantitative limits and early‑warning indicators
            - Material risk inventory and qualitative assessment (inherent, controls, residual) with owners
            - Scenario suite and stress testing results (credit, IRRBB, liquidity, operational, climate overlay)
            - Capital plan with buffers vs NCUA RBC or CCULR leverage, plus management buffer policy
            - Model risk framework evidence (inventory, validation, challenger outcomes) per SR 11‑7
            - Liquidity adequacy analysis and contingency funding plan
            - Board package: exec summary, key findings, capital decisions, and remediation actions
            """
        ),
    )

    # ---------------------------
    # PHASE 1 — Governance, Scope, and Data Foundations
    # ---------------------------
    governance_scope = Task(
        name="Governance & Scope",
        description=(
            "Define purpose, scope, proportionality (credit union scale), roles, and calendar. Confirm linkages to strategic plan "
            "and budget cycle; define documentation standards and audit trail requirements."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=10.0,
        estimated_cost=2500.0,
    )
    governance_scope.subtasks = [
        Task(
            name="Charter & Roles",
            description="Draft RACI (Board/Risk Committee, Management, Risk, Finance, Internal Audit).",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=700.0,
        ),
        Task(
            name="Proportionality Assessment",
            description="Scale methods, scenario granularity, and documentation to size/complexity.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=700.0,
        ),
        Task(
            name="Calendar & Milestones",
            description="Publish milestones and dependencies aligned to board meetings and budget.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=1100.0,
        ),
    ]

    data_model_inventory = Task(
        name="Data & Model Inventory (SR 11‑7)",
        description=(
            "Compile data lineage and model inventory for risk measurement and capital planning (PD/LGD/EAD, ALM/IRRBB, "
            "liquidity metrics). Identify model owners, use cases, and limitations; define validation plan."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=16.0,
        estimated_cost=5000.0,
        dependency_task_ids=[governance_scope.task_id],
    )
    data_model_inventory.subtasks = [
        Task(
            name="Model Inventory & Ratings Map",
            description="List models/tools by risk, inputs/outputs, and decisions influenced.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=1800.0,
        ),
        Task(
            name="Data Lineage & Controls",
            description="Source‑to‑report lineage, QC checks, and change‑management hooks.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=1800.0,
        ),
        Task(
            name="Validation & Challenger Plan",
            description="Prioritize validations; define challenger tests and backtesting cadence.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=1400.0,
        ),
    ]

    risk_appetite = Task(
        name="Risk Appetite & Materiality",
        description=(
            "Define risk appetite statement and limits by risk type (credit, IRRBB, liquidity, operational), with metrics, "
            "triggers, and escalation. Identify material risks and control effectiveness to derive residual risk."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=14.0,
        estimated_cost=4200.0,
        dependency_task_ids=[governance_scope.task_id],
    )
    risk_appetite.subtasks = [
        Task(
            name="Metrics & Limits",
            description="Quantify limit structure (e.g., NIM sensitivity, NPL ratio, LCR/NSFR proxy, operational loss thresholds).",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=1800.0,
        ),
        Task(
            name="Early‑Warning Indicators",
            description="Define EWIs and playbooks (breach management and communications).",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=1200.0,
        ),
        Task(
            name="Material Risk Register",
            description="Score inherent/control/residual risk; assign owners and test plans.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=1200.0,
        ),
    ]

    # ---------------------------
    # PHASE 2 — Risk Identification & Scenario Design
    # ---------------------------
    risk_identification = Task(
        name="Risk Identification Workshops",
        description=(
            "Cross‑functional workshops to confirm risk taxonomy: credit (retail/commercial), IRRBB, liquidity, operational, "
            "compliance, strategic, reputational, and climate risk overlay."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=12.0,
        estimated_cost=3000.0,
        dependency_task_ids=[risk_appetite.task_id],
    )
    risk_identification.subtasks = [
        Task(
            name="Portfolio Deep‑Dive",
            description="Segmented views by product, vintage, collateral, geography, and industry.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=1500.0,
        ),
        Task(
            name="Operational & Cyber Risk Scan",
            description="Key risk indicators, losses, near‑misses; third‑party and fraud posture.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=1500.0,
        ),
    ]

    scenario_suite = Task(
        name="Scenario Suite Design",
        description=(
            "Design baseline, adverse, and severe scenarios; include idiosyncratic shocks and climate scenarios "
            "appropriate to size/complexity. Define variable paths and narrative."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=14.0,
        estimated_cost=4200.0,
        dependency_task_ids=[risk_identification.task_id, data_model_inventory.task_id],
    )
    scenario_suite.subtasks = [
        Task(
            name="Macro & Rate Paths",
            description="GDP, unemployment, CPI, policy/term rates; deposit beta assumptions.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=1800.0,
        ),
        Task(
            name="Idiosyncratic & Climate Overlays",
            description="Local industry downturn; physical/transition risk overlays for credit & collateral.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=1200.0,
        ),
        Task(
            name="Severe but Plausible Calibration",
            description="Tail calibration with management buffer considerations.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=1200.0,
        ),
    ]

    # ---------------------------
    # PHASE 3 — Quantification & Capital/Liquidity Planning
    # ---------------------------
    credit_loss_projection = Task(
        name="Credit Loss Projection",
        description=(
            "Project lifetime and 1‑yr losses under scenarios using PD/LGD/EAD or proxy methods; "
            "assess overlays and qualitative adjustments."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=16.0,
        estimated_cost=4800.0,
        dependency_task_ids=[scenario_suite.task_id],
    )
    irrbb_projection = Task(
        name="IRRBB & NII/EVE Sensitivity",
        description="ALM modeling of net interest income and economic value under rate shocks and ramps.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=14.0,
        estimated_cost=4200.0,
        dependency_task_ids=[scenario_suite.task_id],
    )
    liquidity_profile = Task(
        name="Liquidity Profile & Contingency Funding Plan",
        description=(
            "Assess liquidity survival horizon and funding sources; build contingency funding triggers and actions."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=12.0,
        estimated_cost=3600.0,
        dependency_task_ids=[scenario_suite.task_id],
    )
    operational_risk_assessment = Task(
        name="Operational Risk Assessment",
        description="Score operational risk exposures; scenario‑based capital add‑ons and control remediation plan.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=12.0,
        estimated_cost=3600.0,
        dependency_task_ids=[risk_identification.task_id],
    )

    capital_adequacy = Task(
        name="Capital Adequacy & Buffer Policy",
        description=(
            "Reconcile capital under scenarios to NCUA RBC or CCULR leverage options; define management buffer and "
            "dividend/member distribution constraints."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=16.0,
        estimated_cost=4800.0,
        dependency_task_ids=[
            credit_loss_projection.task_id,
            irrbb_projection.task_id,
            operational_risk_assessment.task_id,
        ],
    )

    # ---------------------------
    # PHASE 4 — Controls, Documentation, and Governance
    # ---------------------------
    model_validation = Task(
        name="Model Validation & Use‑Test (SR 11‑7)",
        description=(
            "Execute validation/challenger tests; assess conceptual soundness, outcomes analysis, and ongoing monitoring; "
            "evidence 'effective challenge' and use‑test."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=14.0,
        estimated_cost=4200.0,
        dependency_task_ids=[
            data_model_inventory.task_id,
            credit_loss_projection.task_id,
            irrbb_projection.task_id,
        ],
    )
    control_testing = Task(
        name="Control Testing & Audit Trail",
        description="Key controls walkthroughs; documentation QA; audit trail and reproducibility checks.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=10.0,
        estimated_cost=2800.0,
        dependency_task_ids=[model_validation.task_id],
    )
    recovery_options = Task(
        name="Management Actions & Recovery Options",
        description="Catalog credible actions (pricing, expense, asset sales, dividend policy) with execution playbooks.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=8.0,
        estimated_cost=2400.0,
        dependency_task_ids=[capital_adequacy.task_id, liquidity_profile.task_id],
    )
    orsa_report = Task(
        name="Internal Risk & Solvency Assessment Report",
        description=(
            "Draft the assessment report: methodology, scenarios, results, governance, limitations, and conclusions; "
            "include evidence index for supervisory review."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=18.0,
        estimated_cost=5400.0,
        dependency_task_ids=[
            capital_adequacy.task_id,
            control_testing.task_id,
            recovery_options.task_id,
        ],
    )
    board_approval = Task(
        name="Board Review & Approval",
        description="Deliver executive summary; capture decisions; record approvals and follow‑up actions.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=6.0,
        estimated_cost=1500.0,
        dependency_task_ids=[orsa_report.task_id],
    )
    disclosure_communication = Task(
        name="Stakeholder Communication & Filing Readiness",
        description="Prepare internal/external communications; package for supervisory exam; schedule refresh cadence.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=6.0,
        estimated_cost=1500.0,
        dependency_task_ids=[board_approval.task_id],
    )

    # ---------------------------
    # REGISTER TASKS
    # ---------------------------
    for task in [
        governance_scope,
        data_model_inventory,
        risk_appetite,
        risk_identification,
        scenario_suite,
        credit_loss_projection,
        irrbb_projection,
        liquidity_profile,
        operational_risk_assessment,
        capital_adequacy,
        model_validation,
        control_testing,
        recovery_options,
        orsa_report,
        board_approval,
        disclosure_communication,
    ]:
        WorkflowMutations.add_task(workflow, task)

    # ---------------------------
    # CONSTRAINTS (Regulatory & Governance)
    # ---------------------------
    workflow.constraints.extend(
        [
            Constraint(
                name="Model Risk Management (SR 11‑7)",
                description="Models used for capital planning and risk quantification must follow SR 11‑7: inventory, validation, and ongoing monitoring.",
                constraint_type="regulatory",
                enforcement_level=0.95,
                applicable_task_types=[
                    "Data & Model Inventory (SR 11‑7)",
                    "Model Validation & Use‑Test (SR 11‑7)",
                    "Credit Loss Projection",
                    "IRRBB & NII/EVE Sensitivity",
                ],
                metadata={
                    "evidence_required": [
                        "inventory",
                        "validation_reports",
                        "monitoring_metrics",
                    ]
                },
            ),
            Constraint(
                name="Capital Adequacy vs NCUA RBC/CCULR",
                description="Capital plan must satisfy NCUA RBC or CCULR leverage requirements with documented management buffer.",
                constraint_type="regulatory",
                enforcement_level=0.9,
                applicable_task_types=["Capital Adequacy & Buffer Policy"],
                metadata={"references": ["NCUA RBC", "CCULR"]},
            ),
            Constraint(
                name="Board Oversight & Approval",
                description="Assessment must be reviewed and approved by the Board/Risk Committee with minutes and decisions recorded.",
                constraint_type="organizational",
                enforcement_level=1.0,
                applicable_task_types=["Board Review & Approval"],
                metadata={
                    "approval_artifacts": ["minutes", "resolution", "decision_log"]
                },
            ),
            Constraint(
                name="Documentation & Auditability",
                description="All results must be reproducible with audit trails and versioned artifacts.",
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=[
                    "Control Testing & Audit Trail",
                    "Internal Risk & Solvency Assessment Report",
                ],
                metadata={"requirements": ["reproducibility", "evidence_index"]},
            ),
        ]
    )

    return workflow
