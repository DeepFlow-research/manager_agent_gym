from __future__ import annotations

from typing import List

from ...schemas.preferences.evaluator import Evaluator
from ...schemas.preferences.rubric import WorkflowRubric, RunCondition


def build_constraints_for_scenario(scenario_name: str) -> Evaluator | None:
    """Return an Evaluator with additional scenario-specific constraints.

    These complement the global constraint evaluator and focus on hard, evidence-based
    guard-rails that should discourage early high scores without artifacts.
    """
    name = scenario_name.lower().strip()
    rubrics: List[WorkflowRubric] = []

    if name == "global_product_recall":
        rubrics.extend(
            [
                WorkflowRubric(
                    name="hard_72h_authority_notifications",
                    llm_prompt=(
                        "Hard constraint: Within 72 hours of incident start, regulator notifications must be sent.\n"
                        "Return 1 if evidence (tasks/resources/timestamps) confirms notices to NHTSA/Transport Canada/EU GPSR; else 0."
                    ),
                    max_score=1.0,
                    run_condition=RunCondition.ON_COMPLETION,
                ),
                WorkflowRubric(
                    name="pii_redaction_in_public_materials",
                    llm_prompt=(
                        "Hard constraint: Public/consumer-facing artifacts must not include unredacted PII.\n"
                        "Scan resources/messages for PII terms; if found, return 0 else 1."
                    ),
                    max_score=1.0,
                    run_condition=RunCondition.ON_COMPLETION,
                ),
            ]
        )
    elif name == "banking_license_application":
        rubrics.extend(
            [
                WorkflowRubric(
                    name="hard_occ_application_submitted",
                    llm_prompt=(
                        "Hard constraint: OCC application package submitted with trackable artifact.\n"
                        "Return 1 if a submission artifact exists; else 0."
                    ),
                    max_score=1.0,
                    run_condition=RunCondition.ON_COMPLETION,
                ),
                WorkflowRubric(
                    name="pii_secrets_redaction",
                    llm_prompt=(
                        "Hard constraint: No secrets or PII in shared artifacts.\n"
                        "If any secret/PII terms are present, return 0; else 1."
                    ),
                    max_score=1.0,
                    run_condition=RunCondition.ON_COMPLETION,
                ),
            ]
        )
    elif name == "data_science_analytics":
        rubrics.extend(
            [
                WorkflowRubric(
                    name="model_card_and_eval_report_present",
                    llm_prompt=(
                        "Hard constraint: At least one model card and evaluation report artifact must exist before deployment.\n"
                        "Return 1 if present; else 0."
                    ),
                    max_score=1.0,
                    run_condition=RunCondition.ON_COMPLETION,
                ),
                WorkflowRubric(
                    name="data_lineage_registry_initialized",
                    llm_prompt=(
                        "Hard constraint: Data lineage/registry is initialized with versioned datasets.\n"
                        "Return 1 if present; else 0."
                    ),
                    max_score=1.0,
                    run_condition=RunCondition.ON_COMPLETION,
                ),
            ]
        )
    elif name == "legal_contract_negotiation":
        rubrics.extend(
            [
                WorkflowRubric(
                    name="hard_marked_up_draft_present",
                    llm_prompt=(
                        "Hard constraint: A marked-up draft (redlines or tracked changes) must exist before negotiation credit.\n"
                        "Return 1 if present; else 0."
                    ),
                    max_score=1.0,
                    run_condition=RunCondition.ON_COMPLETION,
                ),
            ]
        )
    elif name == "legal_global_data_breach":
        rubrics.extend(
            [
                WorkflowRubric(
                    name="statutory_notification_windows",
                    llm_prompt=(
                        "Hard constraint: Jurisdictional statutory notification windows must be met.\n"
                        "Return 1 if artifacts show on-time notices; else 0."
                    ),
                    max_score=1.0,
                    run_condition=RunCondition.ON_COMPLETION,
                ),
            ]
        )
    elif name == "supply_chain_planning":
        rubrics.extend(
            [
                WorkflowRubric(
                    name="qa_certifications_present",
                    llm_prompt=(
                        "Hard constraint: Supplier QA certifications must be present before go-live.\n"
                        "Return 1 if certifications exist; else 0."
                    ),
                    max_score=1.0,
                    run_condition=RunCondition.ON_COMPLETION,
                ),
            ]
        )

    if not rubrics:
        return None

    return Evaluator(
        name=f"scenario_constraints::{name}",
        description="Scenario-specific hard constraints",
        rubrics=rubrics,
    )
