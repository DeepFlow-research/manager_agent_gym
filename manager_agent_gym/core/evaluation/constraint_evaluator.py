from __future__ import annotations

from datetime import datetime
from statistics import mean
from typing import List, Tuple

from ...schemas.core.workflow import Workflow
from ...schemas.evaluation.success_criteria import ValidationContext
from ...schemas.preferences.evaluator import Evaluator
from ...schemas.preferences.rubric import (
    WorkflowRubric,
    RunCondition,
    AdditionalContextItem,
)


def _is_hard(constraint) -> bool:
    try:
        return (constraint.constraint_type or "").lower() == "hard"
    except Exception:
        return False


def _get_prohibited_keywords(constraint) -> List[str]:
    try:
        meta = constraint.metadata or {}
        value = meta.get("prohibited_keywords", [])
        return [str(x).lower() for x in value] if isinstance(value, list) else []
    except Exception:
        return []


def _get_applicable_task_types(constraint) -> List[str]:
    try:
        return list(constraint.applicable_task_types or [])
    except Exception:
        return []


def _parse_deadline(constraint) -> datetime | None:
    try:
        meta = constraint.metadata or {}
        raw = meta.get("deadline")
        if not raw:
            return None
        return datetime.fromisoformat(str(raw))
    except Exception:
        return None


def hard_constraints_enforced(
    workflow: Workflow, context: ValidationContext
) -> Tuple[float, str]:
    """Return 1.0 if no hard constraint is violated; else 0.0.

    Violation heuristics:
      - prohibited_keywords not present in resources/messages
      - when applicable_task_types provided, at least one matching task exists and is completed
    """
    violations: List[str] = []

    # Build message texts if provided
    messages_text: List[str] = []
    if context.communications_by_sender is not None:
        for group in context.communications_by_sender:
            for m in group.messages:
                messages_text.append((m.content or "").lower())

    # Scan constraints
    for c in workflow.constraints:
        if not _is_hard(c):
            continue
        # 1) prohibited keywords
        prohibited = _get_prohibited_keywords(c)
        if prohibited:
            # resources
            for r in workflow.resources.values():
                text = (
                    str(r.name)
                    + "\n"
                    + str(r.description or "")
                    + "\n"
                    + str(r.content or "")
                ).lower()
                if any(k in text for k in prohibited):
                    violations.append(f"prohibited resource content: {c.name}")
                    break
            # messages (if available)
            if not violations and messages_text:
                if any(any(k in msg for k in prohibited) for msg in messages_text):
                    violations.append(f"prohibited message content: {c.name}")

        # 2) applicable tasks present and completed
        types_ = _get_applicable_task_types(c)
        if types_:
            matches = [
                t
                for t in workflow.tasks.values()
                if any(tp.lower() in t.name.lower() for tp in types_)
            ]
            if not matches or not any(t.completed_at is not None for t in matches):
                violations.append(f"missing/unfinished tasks for: {c.name}")

    score = 1.0 if not violations else 0.0
    detail = "; ".join(violations) if violations else "all hard constraints satisfied"
    return score, detail


def constraint_coverage_mapping(
    workflow: Workflow, context: ValidationContext
) -> Tuple[float, str]:
    """Fraction of constraints that show handling artifacts (tasks or resources)."""
    total = len(workflow.constraints)
    if total == 0:
        return 1.0, "no constraints"
    covered = 0
    for c in workflow.constraints:
        types_ = _get_applicable_task_types(c)
        name_l = c.name.lower() if c.name else ""
        tasks_match = any(
            (name_l in t.name.lower())
            or any(tp.lower() in t.name.lower() for tp in types_)
            for t in workflow.tasks.values()
        )
        resources_match = any(
            (name_l in (r.name or "").lower()) for r in workflow.resources.values()
        )
        if tasks_match or resources_match:
            covered += 1
    score = covered / float(total)
    return score, f"covered={covered}/{total}"


def deadline_guardrails(
    workflow: Workflow, context: ValidationContext
) -> Tuple[float, str]:
    """Fraction of deadline-tagged tasks that met the deadline."""
    num_with_deadline = 0
    num_met = 0
    for c in workflow.constraints:
        deadline = _parse_deadline(c)
        if deadline is None:
            continue
        types_ = _get_applicable_task_types(c)
        for t in workflow.tasks.values():
            if types_ and not any(tp.lower() in t.name.lower() for tp in types_):
                continue
            num_with_deadline += 1
            if t.completed_at is not None and t.completed_at <= deadline:
                num_met += 1
    if num_with_deadline == 0:
        return 1.0, "no deadline-tagged tasks"
    score = num_met / float(num_with_deadline)
    return score, f"met={num_met}/{num_with_deadline}"


def prohibited_actions_avoidance(
    workflow: Workflow, context: ValidationContext
) -> Tuple[float, str]:
    """1.0 if no prohibited keywords appear in resources/messages; else 0.0."""
    prohibited: List[str] = []
    for c in workflow.constraints:
        prohibited.extend(_get_prohibited_keywords(c))
    prohibited = [p for p in set(prohibited) if p]
    if not prohibited:
        return 1.0, "no prohibited keywords configured"

    # resources
    for r in workflow.resources.values():
        text = (
            str(r.name) + "\n" + str(r.description or "") + "\n" + str(r.content or "")
        ).lower()
        if any(k in text for k in prohibited):
            return 0.0, "prohibited keyword in resources"

    # messages (optional)
    if context.communications_by_sender is not None:
        for group in context.communications_by_sender:
            for m in group.messages:
                if any(k in (m.content or "").lower() for k in prohibited):
                    return 0.0, "prohibited keyword in messages"

    return 1.0, "no prohibited usage found"


def hard_zero_agg(
    scores: list[float],
    rubrics: list,
    workflow: Workflow | None = None,
    context: ValidationContext | None = None,
) -> float:
    """If hard_constraints_enforced == 0, return 0; else mean of scores."""
    gate = 1.0
    for r in rubrics or []:
        if r.name == "hard_constraints_enforced":
            gate = float(r.normalized_score)
            break
    if gate == 0.0:
        return 0.0
    return mean(scores) if scores else 0.0


def build_constraint_evaluator() -> Evaluator:
    rubrics: list[WorkflowRubric] = [
        WorkflowRubric(
            name="hard_constraints_enforced",
            description=(
                "LLM check: 1 if all hard constraints satisfied; 0 if any violation."
            ),
            llm_prompt=(
                """
You are evaluating enforcement of HARD constraints for this workflow at completion.

Instructions:
- Read the workflow tasks, their completion status, and produced resources.
- For each constraint with constraint_type == "hard":
  - If metadata.prohibited_keywords are specified, ensure none appear in artifacts (names, descriptions, or contents) provided in the workflow context.
  - If applicable_task_types are specified, ensure at least one matching task exists and is COMPLETED.
  - If deadlines are specified (metadata.deadline ISO timestamp), ensure relevant tasks completed on/before the deadline.
- If ANY hard constraint shows a violation, return score = 0; otherwise return score = 1.

Output:
- reasoning: brief bullet points referencing the specific constraints checked and evidence found.
- score: 0 or 1
"""
            ),
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="constraint_coverage_mapping",
            description="Fraction of constraints with handling artifacts (tasks/resources).",
            evaluator_function=constraint_coverage_mapping,  # type: ignore[arg-type]
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="deadline_guardrails",
            description="Fraction of deadline-tagged tasks that met deadlines.",
            evaluator_function=deadline_guardrails,  # type: ignore[arg-type]
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="prohibited_actions_avoidance",
            description="1 if no prohibited keywords found in resources/messages; 0 otherwise.",
            evaluator_function=prohibited_actions_avoidance,  # type: ignore[arg-type]
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
            required_context={AdditionalContextItem.COMMS_BY_SENDER},
        ),
        # LLM-based evidence checks (prompts only; no extra context needed)
        WorkflowRubric(
            name="access_control_pii_evidence",
            llm_prompt=(
                "Evaluate access control and PII handling evidence: redactions, RBAC documentation, and access logs."
                " Provide partial credit and cite artifacts. Output numeric score [0, 10]."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="formal_signoffs_present",
            llm_prompt=(
                "Assess presence and completeness of formal sign-offs (names, dates, scope, references)."
                " Provide partial credit and cite artifacts. Output numeric score [0, 10]."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="data_lineage_controls_evidence",
            llm_prompt=(
                "Evaluate data lineage and controls: registry, reconciliations, reproducibility, and remediation logs."
                " Provide partial credit and cite artifacts. Output numeric score [0, 10]."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        WorkflowRubric(
            name="soft_constraints_tradeoff_documentation",
            llm_prompt=(
                "When soft constraints are not strictly met, assess whether rationale/trade-offs are documented"
                " in artifacts and communications. Provide partial credit and cite. Output numeric score [0, 6]."
            ),
            max_score=6.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    return Evaluator(
        name="constraint_adherence",
        description="Constraint adherence at completion (hard zeroing + soft evidence).",
        aggregation=hard_zero_agg,
        rubrics=rubrics,
    )
