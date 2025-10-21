from __future__ import annotations

from typing import TYPE_CHECKING

from manager_agent_gym.core.workflow.phases.interface import PreExecutionPhase

if TYPE_CHECKING:
    from manager_agent_gym.schemas.domain.workflow import Workflow


class NoOpPreExecutionPhase(PreExecutionPhase):
    """Default implementation that does nothing."""

    async def run(
        self,
        workflow: Workflow,
    ) -> None:
        """No-op: workflow proceeds as-is."""
        pass
