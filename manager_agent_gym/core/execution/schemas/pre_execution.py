"""
Schemas for pre-execution phase (clarification dialogue and rubric generation).

This module defines the logging and tracking structures for the pre-execution
phase where the manager agent interacts with stakeholder to generate rubrics.
"""

from datetime import datetime
from pydantic import BaseModel, Field

from manager_agent_gym.core.agents.manager_agent.implementations.rubric_generation_manager.rubric_generation import (
    ManagerAgentGeneratedRubric,
)


class ClarificationTurn(BaseModel):
    """A single question-answer exchange in the clarification dialogue.

    Represents one turn where the manager asks a question and (optionally)
    receives a response from the stakeholder.
    """

    turn: int = Field(description="Turn number (0-indexed)")
    timestep: int = Field(description="Simulation timestep when turn occurred")
    manager_question: str = Field(description="Question asked by manager agent")
    stakeholder_response: str | None = Field(
        default=None, description="Response from stakeholder (None if no response yet)"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now, description="When this turn occurred"
    )
    question_message_id: str | None = Field(
        default=None, description="Message ID of the question for tracking"
    )
    response_message_id: str | None = Field(
        default=None, description="Message ID of the response for tracking"
    )


class PreExecutionLog(BaseModel):
    """Complete log of pre-execution clarification phase.

    Captures the entire interaction between manager and stakeholder during
    the rubric generation phase, including all questions, answers, and
    generated rubrics.

    This is saved to workflow.metadata['pre_execution_logs'] after completion.
    """

    clarification_turns: list[ClarificationTurn] = Field(
        default_factory=list, description="All question-answer exchanges"
    )
    generated_rubrics: list[ManagerAgentGeneratedRubric] = Field(
        default_factory=list, description="All rubrics generated during this phase"
    )
    completion_reason: str = Field(
        description="Why the phase ended: 'all_rubrics_generated', 'max_turns_reached', 'error', 'manual_stop'"
    )
    total_turns: int = Field(description="Total number of turns executed")
    max_turns_reached: bool = Field(
        default=False, description="Whether the phase ended due to max turns limit"
    )
    started_at: datetime = Field(description="When pre-execution phase started")
    completed_at: datetime = Field(description="When pre-execution phase completed")
    stakeholder_id: str = Field(description="ID of stakeholder agent")
    manager_id: str = Field(description="ID of manager agent")

    # Optional metadata
    exemplar_output: str | None = Field(
        default=None,
        description="Exemplar output used by stakeholder (for RL training context)",
    )
    max_turns_budget: int | None = Field(
        default=None, description="Maximum turns allowed for this phase"
    )

    def get_turn_by_index(self, turn: int) -> ClarificationTurn | None:
        """Get a specific turn by index."""
        for t in self.clarification_turns:
            if t.turn == turn:
                return t
        return None

    @property
    def duration_seconds(self) -> float:
        """Total duration of pre-execution phase in seconds."""
        return (self.completed_at - self.started_at).total_seconds()

    @property
    def questions_asked(self) -> int:
        """Total number of questions asked."""
        return len(self.clarification_turns)

    @property
    def questions_answered(self) -> int:
        """Number of questions that received responses."""
        return sum(
            1 for t in self.clarification_turns if t.stakeholder_response is not None
        )

    @property
    def rubrics_generated_count(self) -> int:
        """Number of rubrics generated."""
        return len(self.generated_rubrics)
