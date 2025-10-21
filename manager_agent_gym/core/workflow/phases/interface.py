from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from manager_agent_gym.schemas.domain.workflow import Workflow


class PreExecutionPhase(ABC):
    """Abstract pre-execution component that updates workflow before execution.

    Implementations can perform upfront manager reasoning such as:
    - Rubric decomposition with stakeholder clarification
    - Preference elicitation
    - Workflow structure optimization
    - Resource pre-allocation

    The phase is given access to workflow and preferences, and can mutate them
    before the main execution loop starts. Any metrics or state should be stored
    in workflow.metadata for later retrieval.
    """

    @abstractmethod
    async def run(
        self,
        workflow: Workflow,
    ) -> None:
        """Execute pre-execution phase, updating workflow/preferences in place.

        Args:
            workflow: Workflow to prepare (can be mutated)
            preferences: Preference weights (can be mutated)

        Note:
            Store any metrics or state in workflow.metadata for tracking.
            Example: workflow.metadata['pre_execution_metrics'] = {...}
        """
