from __future__ import annotations

from typing import TYPE_CHECKING

from manager_agent_gym.core.workflow.phases.interface import PreExecutionPhase

if TYPE_CHECKING:
    from manager_agent_gym.schemas.domain.workflow import Workflow
    from manager_agent_gym.core.common.llm_generator import LLMGenerator


class NoOpPreExecutionPhase(PreExecutionPhase):
    """Default implementation that does nothing."""

    async def run(
        self,
        workflow: Workflow,
        llm_generator: "LLMGenerator",
    ) -> None:
        """No-op: workflow proceeds as-is."""
        pass
