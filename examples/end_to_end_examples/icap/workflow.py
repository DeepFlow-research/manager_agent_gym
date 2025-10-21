"""
ICAAP (Internal Capital Adequacy Assessment Process) Demo

Real-world use case: Mid-size EU retail bank annual ICAAP cycle.

Demonstrates:
- Hierarchical task decomposition for ICAAP phases
- Preference dynamics emphasizing compliance near submission
- Ad hoc team coordination with human sign-offs
- Governance-by-design validation rules (LLM-based rubrics)
"""

from uuid import uuid4, UUID

from manager_agent_gym.schemas.domain.workflow import Workflow
from manager_agent_gym.schemas.domain.task import Task
from manager_agent_gym.schemas.domain.base import TaskStatus
from manager_agent_gym.schemas.preferences import Constraint
from manager_agent_gym.core.workflow.services import WorkflowMutations


def create_workflow() -> Workflow:
    """Create ICAAP workflow with hierarchical phases and dependencies."""

    workflow = Workflow(
        name="Annual ICAAP - EU Retail Bank",
        workflow_goal=(
            """
            Objective: Execute the annual ICAAP to provide a coherent, well‑governed, and evidence‑backed assessment of
            capital adequacy across economic and normative perspectives for a mid‑size EU retail bank.

            Primary deliverables:
            - Comprehensive risk inventory and materiality assessment (credit, market/CVA/IRRBB, liquidity, operational,
              concentration, model risk) with quantification methods and owners.
            - Economic capital computation with sensitivity analysis and consistency checks across models.
            - Institution‑wide stress testing (baseline/adverse/severe) and reverse stress testing with severity rationale.
            - 3‑year normative capital plan (CET1 vs OCR+CBR, P2R/P2G, MDA) and management buffer sizing.
            - Management actions catalog with feasibility, triggers, timelines, and quantified impacts.
            - Governance package: decision logs, committee materials, sign‑offs, and escalation evidence.
            - Regulatory mapping (PRA/ECB/CRD/CRR, Basel) with proportionality rationale and explicit gaps.
            - Data lineage registry and reproducibility notes for all key figures and workpapers.

            Acceptance criteria (high‑level):
            - Evidenced scenario coverage incl. reverse stress; decision‑impact analysis documented.
            - Sign‑offs present for validation, compliance, internal audit, and board pack.
            - Consistency between economic/normative perspectives with reconciliations where required.
            - Confidential information redacted with documented access controls; no unresolved high‑risk issues pending.


            """
        ),
        owner_id=uuid4(),
    )

    # Phase 1: Governance and Scope
    governance_scope = Task(
        id=UUID(int=0),
        name="Governance & Scope Setup",
        description=(
            "Define ICAAP scope and proportionality; update RAF/limits; map committees, "
            "decision rights, and escalation procedures; document ICAAP architecture."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=8.0,
        estimated_cost=1200.0,
    )
    governance_scope.subtasks = [
        Task(
            id=UUID(int=100),
            name="Risk Appetite & Limits",
            description="Refresh risk appetite statement and hierarchical limit system with breach escalation.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=450.0,
        ),
        Task(
            id=UUID(int=101),
            name="ICAAP Architecture Doc",
            description="Document ICAAP architecture and integration with planning and governance.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=2.0,
            estimated_cost=300.0,
        ),
        Task(
            id=UUID(int=102),
            name="Governance Roles & Approvals",
            description="Define committees, roles, responsibilities, sign-off workflow and escalation.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=450.0,
        ),
    ]

    risk_inventory = Task(
        id=UUID(int=1),
        name="Risk Inventory & Materiality",
        description=(
            "Compile risk inventory (credit, market/CVA, IRRBB, operational, concentration, model risk). "
            "Assess materiality using gross approach; map methods and owners."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=10.0,
        estimated_cost=1500.0,
        dependency_task_ids=[governance_scope.id],
    )

    # Phase 2: Risk Quantification (Economic Perspective)
    credit_risk = Task(
        id=UUID(int=2),
        name="Credit Risk Economic Capital",
        description=(
            "Estimate PD/LGD/EAD, portfolio concentrations; compute economic capital with sensitivity analysis."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=16.0,
        estimated_cost=2400.0,
    )
    credit_risk.subtasks = [
        Task(
            id=UUID(int=110),
            name="Data Preparation (Wholesale/Retail)",
            description="Assemble and reconcile PD/LGD/EAD inputs; handle defaults, cures, downturn adjustments.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=5.0,
            estimated_cost=750.0,
        ),
        Task(
            id=UUID(int=111),
            name="Model Estimation & Calibration",
            description="Estimate/validate PD/LGD/EAD segments; concentration add‑on; downturn calibration.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=6.0,
            estimated_cost=900.0,
        ),
        Task(
            id=UUID(int=112),
            name="Sensitivity & Consistency Checks",
            description="Run multi‑parameter sweeps; reconcile against inventory and management overlays.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=5.0,
            estimated_cost=750.0,
        ),
    ]
    irrbb = Task(
        id=UUID(int=3),
        name="IRRBB (EVE/NII)",
        description=(
            "Measure EVE and NII under EBA standard shocks; justify behavioral assumptions; check limits."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=14.0,
        estimated_cost=2100.0,
        dependency_task_ids=[risk_inventory.id],
    )
    irrbb.subtasks = [
        Task(
            id=UUID(int=120),
            name="Behavioral Assumptions",
            description="Document and justify pass‑through, core deposits, prepayment; approvals captured.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
        Task(
            id=UUID(int=121),
            name="Shock Application & Limits Check",
            description="Apply EBA shocks, compute EVE/NII; check policy limits and flag breaches.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=5.0,
            estimated_cost=750.0,
        ),
        Task(
            id=UUID(int=122),
            name="Reconciliation & Reporting",
            description="Reconcile results with prior runs and budget plan; produce summary tables.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=5.0,
            estimated_cost=750.0,
        ),
    ]
    op_risk = Task(
        id=UUID(int=4),
        name="Operational Risk Scenarios",
        description=(
            "Scenario-based OpRisk assessment with internal loss data; model risk overlay and parameter uncertainty."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=12.0,
        estimated_cost=1800.0,
        dependency_task_ids=[risk_inventory.id],
    )
    op_risk.subtasks = [
        Task(
            id=UUID(int=130),
            name="Loss Data Analysis",
            description="Analyze internal losses; categorize by event type; severity/frequency exploration.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
        Task(
            id=UUID(int=131),
            name="Scenario Workshop",
            description="Conduct scenario workshop; document narratives and parameter rationale.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
        Task(
            id=UUID(int=132),
            name="Quantification & Overlay",
            description="Quantify scenarios; apply model risk overlay; produce distribution summaries.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
    ]

    # Phase 3: Stress Testing & Reverse Stress
    stress_design = Task(
        id=UUID(int=5),
        name="Stress Testing Design",
        description=(
            "Design baseline, adverse, and severe scenarios; calibrate macro and idiosyncratic drivers; define attributions."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=10.0,
        estimated_cost=1500.0,
        dependency_task_ids=[op_risk.id],
    )
    stress_design.subtasks = [
        Task(
            id=UUID(int=140),
            name="Scenario Definitions",
            description="Define baseline/adverse/severe with coherent macro paths and sectoral stresses.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
        Task(
            id=UUID(int=141),
            name="Severity Calibration",
            description="Calibrate severities vs history and supervisory guidance; justify plausibility.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=450.0,
        ),
        Task(
            id=UUID(int=142),
            name="Attribution & Reporting",
            description="Define attribution methodology; prepare templates for consolidated reporting.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=450.0,
        ),
    ]
    reverse_stress = Task(
        id=UUID(int=6),
        name="Reverse Stress Test",
        description=(
            "Define non-viability conditions and pathways; parameterize; link to remediation actions."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=8.0,
        estimated_cost=1200.0,
        dependency_task_ids=[],
    )

    # Phase 4: Normative Perspective & Capital Planning
    capital_planning = Task(
        id=UUID(int=7),
        name="3-Year Capital Planning (Normative)",
        description=(
            "Project earnings, RWAs, CET1 vs OCR+CBR; integrate P2R/P2G; MDA checks; size management buffer."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=12.0,
        estimated_cost=1800.0,
        dependency_task_ids=[stress_design.task_id, reverse_stress.task_id],
    )
    capital_planning.subtasks = [
        Task(
            id=UUID(int=150),
            name="Projection Engine Setup",
            description="Set up 3‑year projection with scenarios and management actions toggles.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
        Task(
            id=UUID(int=151),
            name="Buffer & MDA Checks",
            description="Assess CET1 vs OCR+CBR; integrate P2R/P2G; run MDA triggers and remedies.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
        Task(
            id=UUID(int=152),
            name="Reconciliation (Economic↔Normative)",
            description="Reconcile material differences between EC and normative; document drivers.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=4.0,
            estimated_cost=600.0,
        ),
    ]
    mgmt_actions = Task(
        id=UUID(int=8),
        name="Management Actions Catalog",
        description=(
            "Define feasible, timely, quantified actions (issuance, dividend, RWA optimization) with triggers."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=8.0,
        estimated_cost=1200.0,
        dependency_task_ids=[capital_planning.task_id],
    )
    mgmt_actions.subtasks = [
        Task(
            id=UUID(int=160),
            name="Feasibility & Governance",
            description="Assess feasibility and governance routes for issuance/dividend/RWA optimization.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=450.0,
        ),
        Task(
            id=UUID(int=161),
            name="Triggers & Quantification",
            description="Define triggers and quantify impacts; timeline and execution constraints.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=450.0,
        ),
    ]

    # Phase 5: Consolidation & Sign-offs
    validation_pack = Task(
        id=UUID(int=9),
        name="Independent Validation Pack",
        description="Compile methodology and data validation evidence for independent review.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=6.0,
        estimated_cost=900.0,
        dependency_task_ids=[credit_risk.task_id, irrbb.task_id, op_risk.task_id],
    )
    validation_pack.subtasks = [
        Task(
            id=UUID(int=170),
            name="Methodology Summary",
            description="Summarize methods, assumptions, limitations, and backtesting evidence.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=450.0,
        ),
        Task(
            id=UUID(int=171),
            name="Data Validation & Lineage",
            description="Compile data lineage, reconciliations, and validation checks for reviewers.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=450.0,
        ),
    ]
    board_pack = Task(
        id=UUID(int=10),
        name="Board Pack & Approvals",
        description=(
            "Assemble CAS, risk coverage, stress results, capital plan, management actions; obtain approvals."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=6.0,
        estimated_cost=900.0,
        dependency_task_ids=[mgmt_actions.task_id, validation_pack.task_id],
    )
    board_pack.subtasks = [
        Task(
            id=UUID(int=180),
            name="Materials & Minutes",
            description="Prepare committee/board materials and record minutes with decisions.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=450.0,
        ),
        Task(
            id=UUID(int=181),
            name="Approvals & Sign‑offs",
            description="Collect sign‑offs (Validation, Compliance, IA, Board) with scope and dates.",
            status=TaskStatus.PENDING,
            estimated_duration_hours=3.0,
            estimated_cost=450.0,
        ),
    ]

    # Additional cross‑cutting tasks to increase initial complexity
    data_lineage = Task(
        id=UUID(int=11),
        name="Data Lineage Registry & Controls",
        description=(
            "Create registry of data sources, transformations, reconciliations; define control checks and owners."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=6.0,
        estimated_cost=900.0,
        dependency_task_ids=[],
    )
    regulatory_mapping = Task(
        id=UUID(int=12),
        name="Regulatory Mapping & Assurance Coordination",
        description=(
            "Map ICAAP sections to PRA/ECB/CRD/CRR and Basel principles; plan assurance scope with authorities."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=6.0,
        estimated_cost=900.0,
        dependency_task_ids=[],
    )
    model_inventory = Task(
        id=UUID(int=13),
        name="Model Inventory & Backtesting Summary",
        description=(
            "Update model inventory entries; summarize backtesting/monitoring results and limitations."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=5.0,
        estimated_cost=750.0,
        dependency_task_ids=[],
    )
    pii_controls = Task(
        id=UUID(int=14),
        name="Confidentiality & Access Controls",
        description=(
            "Implement/redact PII/secret content; document access roles, approvals, and evidence of controls."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=4.0,
        estimated_cost=600.0,
        dependency_task_ids=[],
    )

    for task in [
        governance_scope,
        risk_inventory,
        credit_risk,
        irrbb,
        op_risk,
        stress_design,
        reverse_stress,
        capital_planning,
        mgmt_actions,
        validation_pack,
        board_pack,
        data_lineage,
        regulatory_mapping,
        model_inventory,
        pii_controls,
    ]:
        WorkflowMutations.add_task(workflow, task)

    # Governance and compliance constraints for ICAAP
    workflow.constraints.extend(
        [
            Constraint(
                name="Independent Validation Required",
                description=(
                    "Independent validation artifacts must be produced and completed before submission."
                ),
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=["Independent Validation Pack"],
                metadata={},
            ),
            Constraint(
                name="Board Approvals Required",
                description=(
                    "Board/C-level approvals and minutes must be assembled and finalized."
                ),
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=["Board Pack & Approvals"],
                metadata={},
            ),
            Constraint(
                name="Reverse Stress Coverage",
                description=(
                    "A reverse stress test must be defined with clear non-viability conditions and linkages to actions."
                ),
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=["Reverse Stress"],
                metadata={},
            ),
            Constraint(
                name="PII and Secrets Redaction",
                description=(
                    "Confidential information must be redacted or access-controlled across artifacts and communications."
                ),
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=[
                    "Confidentiality & Access Controls",
                    "Independent Validation Pack",
                    "Board Pack",
                ],
                metadata={
                    "prohibited_keywords": [
                        "ssn",
                        "passport",
                        "password",
                        "api key",
                        "secret key",
                        "private key",
                        "account_number",
                    ]
                },
            ),
            Constraint(
                name="Regulatory Mapping Completeness",
                description=(
                    "ICAAP sections must be mapped to PRA/ECB/CRD/CRR and Basel principles with proportionality rationale."
                ),
                constraint_type="regulatory",
                enforcement_level=0.9,
                applicable_task_types=["Regulatory Mapping"],
                metadata={},
            ),
            Constraint(
                name="Data Lineage and Controls",
                description=(
                    "Data lineage registry, reconciliations, and control checks must be documented."
                ),
                constraint_type="organizational",
                enforcement_level=0.9,
                applicable_task_types=["Data Lineage"],
                metadata={},
            ),
            Constraint(
                name="Model Inventory & Backtesting",
                description=(
                    "Model inventory entries and backtesting/monitoring summaries must be updated."
                ),
                constraint_type="regulatory",
                enforcement_level=0.8,
                applicable_task_types=["Model Inventory"],
                metadata={},
            ),
            Constraint(
                name="MDA and Buffer Checks",
                description=(
                    "CET1 vs OCR+CBR with P2R/P2G must be assessed and MDA triggers/remedies evaluated."
                ),
                constraint_type="regulatory",
                enforcement_level=0.85,
                applicable_task_types=["Capital Planning"],
                metadata={},
            ),
            Constraint(
                name="Economic–Normative Reconciliation",
                description=(
                    "Material differences between economic and normative perspectives must be reconciled and documented."
                ),
                constraint_type="organizational",
                enforcement_level=0.8,
                applicable_task_types=["Capital Planning"],
                metadata={},
            ),
        ]
    )

    return workflow
