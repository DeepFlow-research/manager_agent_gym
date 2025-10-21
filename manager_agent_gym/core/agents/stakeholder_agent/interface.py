from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from manager_agent_gym.schemas.agents import StakeholderConfig
from manager_agent_gym.schemas.agents.stakeholder import (
    StakeholderPublicProfile,
)
from manager_agent_gym.core.agents.workflow_agents.common import AgentInterface

if TYPE_CHECKING:
    from manager_agent_gym.core.evaluation.engine.validation_engine import (
        ValidationEngine,
    )
    from manager_agent_gym.schemas.domain.workflow import Workflow
    from manager_agent_gym.schemas.domain.communication import SenderMessagesView
    from manager_agent_gym.core.agents.manager_agent.actions import ActionResult


class StakeholderBase(AgentInterface[StakeholderConfig], ABC):
    """Abstract base for stakeholder agents.

    Stakeholders own three responsibilities:
    1. Evaluation: Decide what rubrics to run and trigger evaluation
    2. Serialization: Provide state for logging/checkpoints
    3. Communication: Respond to messages and interact with manager

    Different stakeholder types (PreferenceSnapshot-based vs Exemplar-based)
    implement these hooks differently while presenting a unified interface.
    """

    def __init__(self, config: StakeholderConfig):
        super().__init__(config)
        self.public_profile: StakeholderPublicProfile = self._build_public_profile()

    @abstractmethod
    def _build_public_profile(self) -> StakeholderPublicProfile:
        """Build public profile for manager visibility.

        Implementations provide appropriate summaries based on their data model.

        Returns:
            StakeholderPublicProfile with display name, role, and preference summary
        """
        ...

    # ========================================================================
    # EVALUATION HOOK
    # ========================================================================

    @abstractmethod
    async def evaluate_for_timestep(
        self,
        timestep: int,
        validation_engine: "ValidationEngine",
        workflow: "Workflow",
        communications: list["SenderMessagesView"],
        manager_actions: list["ActionResult"],
    ) -> None:
        """Trigger evaluation for this timestep.

        The stakeholder decides what to evaluate and how:
        - Traditional stakeholder: evaluates using PreferenceSnapshot preferences
        - Clarification stakeholder: evaluates using generated Rubrics

        Args:
            timestep: Current timestep
            validation_engine: Engine to submit evaluations to
            workflow: Current workflow state
            communications: Communication history for evaluation
            manager_actions: Manager action buffer for evaluation
        """
        ...

    # ========================================================================
    # SERIALIZATION HOOK
    # ========================================================================

    @abstractmethod
    def get_serializable_state(self, timestep: int) -> dict:
        """Get serializable state for logging/checkpoints.

        Returns a dict that can be JSON-serialized for outputs.
        Different stakeholder types return different structures:

        Traditional stakeholder returns:
        {
            "type": "preference_snapshot",
            "timestep": 5,
            "weights": {"quality": 0.5, "speed": 0.3, ...},
            "preference_names": ["quality", "speed", ...],
        }

        Clarification stakeholder returns:
        {
            "type": "exemplar",
            "timestep": 5,
            "exemplar_output": "...",
            "rubric_count": 12,
            "rubric_names": ["clarity", "completeness", ...],
        }

        Args:
            timestep: Timestep to serialize state for

        Returns:
            JSON-serializable dictionary with stakeholder state
        """
        ...

    @abstractmethod
    def restore_from_state(self, state_dict: dict) -> None:
        """Restore stakeholder state from serialized checkpoint.

        Args:
            state_dict: Dictionary from get_serializable_state()
        """
        ...

    # ========================================================================
    # COMMUNICATION HOOK
    # ========================================================================

    @abstractmethod
    async def policy_step(self, current_timestep: int) -> None:
        """Run timestep communication/behavior.

        Handle messages, send responses, proactive suggestions, etc.
        This is called AFTER evaluation.

        Args:
            current_timestep: Current timestep number
        """
        ...
