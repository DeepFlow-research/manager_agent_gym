from manager_agent_gym.schemas.domain.workflow import Workflow
from manager_agent_gym.schemas.domain.task import Task
from manager_agent_gym.schemas.domain.base import TaskStatus
from manager_agent_gym.schemas.preferences import Constraint
from uuid import uuid4
from examples.common_stakeholders import create_stakeholder_agent
from examples.end_to_end_examples.data_science_analytics.preferences import (
    create_preferences,
)
from manager_agent_gym.core.workflow.services import WorkflowMutations


def create_workflow() -> Workflow:
    workflow = Workflow(
        name="Enterprise Data Science Analytics",
        workflow_goal=(
            """
            Objective: Deliver a production‑ready analytics/modeling solution for a business problem with
            high data quality, responsible‑AI controls, and reproducible results.

            Primary deliverables:
            - Curated and governed dataset with documented lineage and quality checks
            - Feature pipeline and model artifacts with experiment tracking and seeds
            - Model card, bias/fairness analysis, and explainability report
            - Deployment package (CI/CD) with monitoring and rollback plan
            - Executive readout with business impact, risks, and next steps

            Acceptance criteria (high‑level):
            - Data privacy/PII policy compliance; secrets not present in artifacts
            - Reproducible training runs (fixed seeds, environment captured)
            - Minimum evaluation thresholds met (e.g., AUC/accuracy and calibration)
            - Bias/fairness metrics within policy thresholds and mitigations documented
            - Deployment readiness gate passed (security review + monitoring plan)
            """
        ),
        owner_id=uuid4(),
    )

    # Phase 1: Project Setup & Governance
    charter = Task(
        name="Project Charter & Scope",
        description=(
            "Define business objective, success metrics, assumptions, stakeholders, and risks."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=6.0,
        estimated_cost=600.0,
    )
    access_governance = Task(
        name="Data Access & Privacy Review",
        description=(
            "Obtain data access approvals; review PII/PHI handling; document privacy controls."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=4.0,
        estimated_cost=500.0,
        dependency_task_ids=[charter.task_id],
    )
    env_setup = Task(
        name="Environment & Reproducibility Setup",
        description=(
            "Create project repo; pin dependencies; set seeds; enable experiment tracking; set up CI."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=5.0,
        estimated_cost=550.0,
        dependency_task_ids=[charter.task_id],
    )

    # Phase 2: Data Ingestion & Understanding
    ingestion = Task(
        name="Data Ingestion",
        description="Ingest raw sources; define schemas; persist raw zone; baseline profiling.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=8.0,
        estimated_cost=900.0,
        dependency_task_ids=[access_governance.task_id, env_setup.task_id],
    )
    understanding = Task(
        name="Data Understanding & Profiling",
        description=(
            "Explore distributions, drift, missingness, outliers; identify leakage risks; create data summary."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=6.0,
        estimated_cost=700.0,
        dependency_task_ids=[ingestion.task_id],
    )
    data_quality = Task(
        name="Data Quality & Cleaning",
        description=(
            "Implement checks (completeness, validity, uniqueness); remediate issues; create quality report."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=7.0,
        estimated_cost=800.0,
        dependency_task_ids=[understanding.task_id],
    )

    # Phase 3: Feature Engineering
    # Define feature engineering atomic subtasks first for dependency wiring
    feat_baseline = Task(
        name="Baseline Feature Set",
        description="Create minimal viable features and validate against target leakage.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=4.0,
        estimated_cost=400.0,
    )
    feat_store_reg = Task(
        name="Feature Store Registration",
        description="Register reusable features with metadata and ownership.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=3.0,
        estimated_cost=350.0,
    )
    feat_validation = Task(
        name="Feature Validation",
        description="Backtest features; assess stability and drift; document caveats.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=3.0,
        estimated_cost=450.0,
    )

    feature_pipeline = Task(
        name="Feature Engineering Pipeline",
        description="Design/implement feature transformations; register in feature store if applicable.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=10.0,
        estimated_cost=1200.0,
        dependency_task_ids=[data_quality.task_id],
    )
    feature_pipeline.subtasks = [feat_baseline, feat_store_reg, feat_validation]

    # Phase 4: Modeling & Evaluation
    baseline_model = Task(
        name="Baseline Modeling",
        description="Train a simple baseline; establish metrics and calibration; log experiments.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=6.0,
        estimated_cost=800.0,
        dependency_task_ids=[feat_validation.task_id],
    )
    experimentation = Task(
        name="Experimentation & Tuning",
        description="Iterate on models/hyperparameters; cross‑validation; model selection with seeds.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=12.0,
        estimated_cost=1600.0,
        dependency_task_ids=[baseline_model.task_id],
    )
    model_eval = Task(
        name="Model Evaluation & Validation",
        description=(
            "Holdout evaluation; calibration; thresholding; error analysis; compare against acceptance targets."
        ),
        status=TaskStatus.PENDING,
        estimated_duration_hours=8.0,
        estimated_cost=1100.0,
        dependency_task_ids=[experimentation.task_id],
    )

    # Phase 5: Responsible AI Controls
    # Define RAI atomic subtasks first for dependency wiring
    fairness = Task(
        name="Bias & Fairness Assessment",
        description="Compute fairness metrics vs policy thresholds; propose mitigations if breached.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=3.0,
        estimated_cost=450.0,
    )
    xai_report = Task(
        name="Explainability Report",
        description="Generate SHAP/feature importance; create narrative for business stakeholders.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=3.0,
        estimated_cost=450.0,
    )

    rai_checks = Task(
        name="Responsible AI Checks",
        description="Bias/fairness metrics, explainability, performance across cohorts; mitigations if needed.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=6.0,
        estimated_cost=900.0,
        dependency_task_ids=[model_eval.task_id],
    )
    rai_checks.subtasks = [fairness, xai_report]

    # Phase 6: Packaging & Deployment Readiness
    packaging = Task(
        name="Model Packaging & Registry",
        description="Package model; save artifacts; register in model registry with version and metadata.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=5.0,
        estimated_cost=700.0,
        dependency_task_ids=[fairness.task_id, xai_report.task_id],
    )
    model_card = Task(
        name="Model Card & Documentation",
        description="Document training data, metrics, risks, intended use, and limitations.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=4.0,
        estimated_cost=500.0,
        dependency_task_ids=[packaging.task_id],
    )
    cicd = Task(
        name="CI/CD & Security Review",
        description="Implement CI/CD for training/inference; conduct security review and dependency scan.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=6.0,
        estimated_cost=900.0,
        dependency_task_ids=[model_card.task_id],
    )
    monitoring = Task(
        name="Monitoring & Rollback Plan",
        description="Define performance/drift monitors, alerting, and rollback strategy with ownership.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=4.0,
        estimated_cost=600.0,
        dependency_task_ids=[cicd.task_id],
    )

    # Phase 7: Reporting & Sign‑offs
    exec_readout = Task(
        name="Executive Readout & Sign‑offs",
        description="Summarize outcomes, business impact, risks; collect approvals for launch/pilot.",
        status=TaskStatus.PENDING,
        estimated_duration_hours=4.0,
        estimated_cost=600.0,
        dependency_task_ids=[monitoring.task_id],
    )

    # Register tasks in the workflow
    for task in [
        charter,
        access_governance,
        env_setup,
        ingestion,
        understanding,
        data_quality,
        feature_pipeline,
        baseline_model,
        experimentation,
        model_eval,
        rai_checks,
        packaging,
        model_card,
        cicd,
        monitoring,
        exec_readout,
    ]:
        WorkflowMutations.add_task(workflow, task)

    # Governance and organizational constraints for DS analytics
    workflow.constraints.extend(
        [
            Constraint(
                name="Data Privacy & PII Compliance",
                description=(
                    "PII/PHI must be handled per policy; sensitive fields redacted or access‑controlled in artifacts."
                ),
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=[
                    "Data Access & Privacy Review",
                    "Data Ingestion",
                    "Data Quality & Cleaning",
                    "Model Card & Documentation",
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
                name="Reproducible Training Runs",
                description=(
                    "Seeds and environment must be captured; experiments tracked; runs re‑executable end‑to‑end."
                ),
                constraint_type="organizational",
                enforcement_level=0.9,
                applicable_task_types=[
                    "Environment & Reproducibility Setup",
                    "Baseline Modeling",
                    "Experimentation & Tuning",
                ],
                metadata={"requires_seed": True, "experiment_tracking": True},
            ),
            Constraint(
                name="Model Card Required",
                description=(
                    "A model card documenting data, metrics, risks, intended use, and limitations must be produced."
                ),
                constraint_type="organizational",
                enforcement_level=0.95,
                applicable_task_types=["Model Card & Documentation"],
                metadata={},
            ),
            Constraint(
                name="Bias/Fairness Thresholds",
                description=(
                    "Fairness metrics must meet policy thresholds or mitigations documented and signed off."
                ),
                constraint_type="organizational",
                enforcement_level=0.9,
                applicable_task_types=[
                    "Responsible AI Checks",
                    "Bias & Fairness Assessment",
                ],
                metadata={"policy": "org_fairness_v1"},
            ),
            Constraint(
                name="Security Review Gate",
                description="Security review and dependency scan must pass before deployment.",
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=["CI/CD & Security Review"],
                metadata={"requires_approval": True},
            ),
            Constraint(
                name="Monitoring Plan Required",
                description=(
                    "Monitoring and rollback strategy with owners must be defined prior to launch/pilot."
                ),
                constraint_type="organizational",
                enforcement_level=0.9,
                applicable_task_types=["Monitoring & Rollback Plan"],
                metadata={},
            ),
            Constraint(
                name="Executive Sign‑off",
                description="Executive stakeholder sign‑off required prior to production launch.",
                constraint_type="hard",
                enforcement_level=1.0,
                applicable_task_types=["Executive Readout & Sign‑offs"],
                metadata={"roles": ["Product", "Risk", "Security"]},
            ),
        ]
    )

    prefs = create_preferences()
    stakeholder = create_stakeholder_agent(persona="balanced", preferences=prefs)
    WorkflowMutations.add_agent(workflow, stakeholder)

    return workflow
