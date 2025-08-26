from __future__ import annotations


from ...schemas.preferences.evaluator import Evaluator
from ..communication.service import CommunicationService
from .stakeholder_evaluator import build_stakeholder_evaluator
from .constraint_evaluator import build_constraint_evaluator
from .operational_efficiency_evaluator import build_operational_efficiency_evaluator


def build_default_evaluators(
    communication_service: CommunicationService | None,
) -> list[Evaluator]:
    """Return the default evaluator sets to run on every workflow.

    Args:
        communication_service: Optional communication service for stakeholder metrics.
    """
    constraint_eval = build_constraint_evaluator()
    stakeholder_eval = build_stakeholder_evaluator()
    operational_eval = build_operational_efficiency_evaluator()
    return [constraint_eval, stakeholder_eval, operational_eval]
