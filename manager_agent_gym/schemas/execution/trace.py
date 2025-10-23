"""
Execution trace schemas for debugging worker task execution.

These models capture the complete execution history from OpenAI Agents SDK,
including all LLM generations, tool calls, token usage, and conversation flow.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ToolCallTrace(BaseModel):
    """Record of a single tool invocation during execution."""

    tool_name: str = Field(..., description="Name of the tool that was called")
    arguments: str = Field(..., description="JSON string of tool arguments")
    output: str | None = Field(default=None, description="Tool output/result")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="When the tool was called"
    )
    error: str | None = Field(default=None, description="Error message if tool failed")
    succeeded: bool = Field(default=True, description="Whether the tool call succeeded")


class MessageTrace(BaseModel):
    """Record of a message in the conversation."""

    role: str = Field(..., description="Message role: user, assistant, etc.")
    content: str = Field(..., description="Simplified text content of the message")
    message_id: str = Field(..., description="Unique message identifier")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="When the message was created"
    )
    status: str | None = Field(default=None, description="Message status")


class ModelTurnTrace(BaseModel):
    """Record of a single model inference turn."""

    response_id: str = Field(..., description="Unique response identifier")
    input_tokens: int = Field(..., description="Number of input tokens")
    output_tokens: int = Field(..., description="Number of output tokens")
    total_tokens: int = Field(..., description="Total tokens for this turn")
    cached_tokens: int = Field(
        default=0, description="Number of cached tokens (if available)"
    )
    cache_creation_tokens: int = Field(
        default=0, description="Tokens used to create cache (if available)"
    )
    messages: list[MessageTrace] = Field(
        default_factory=list, description="Messages generated in this turn"
    )
    tool_calls: list[ToolCallTrace] = Field(
        default_factory=list, description="Tool calls made in this turn"
    )
    reasoning: str | None = Field(
        default=None, description="Reasoning content (for o1 models)"
    )
    turn_index: int = Field(..., description="Turn number in the conversation")


class WorkerExecutionTrace(BaseModel):
    """
    Complete execution trace for a worker completing a task.

    This captures all the internal execution details from the OpenAI Agents SDK,
    including every LLM call, tool invocation, and token usage. Useful for
    debugging, analysis, and understanding how workers complete tasks.
    """

    # High-level info
    agent_id: str = Field(..., description="ID of the agent that executed")
    task_id: UUID = Field(..., description="ID of the task that was executed")
    started_at: datetime = Field(..., description="When execution started")
    completed_at: datetime = Field(..., description="When execution completed")
    duration_seconds: float = Field(..., description="Total execution time in seconds")

    # Conversation flow - the key data!
    model_turns: list[ModelTurnTrace] = Field(
        default_factory=list,
        description="Each LLM inference call with its inputs/outputs/tool calls",
    )

    # Aggregate metrics
    total_turns: int = Field(default=0, description="Total number of LLM turns")
    total_input_tokens: int = Field(default=0, description="Total input tokens used")
    total_output_tokens: int = Field(default=0, description="Total output tokens used")
    total_tokens: int = Field(default=0, description="Total tokens used")
    total_tool_calls: int = Field(default=0, description="Total tool calls made")
    total_cached_tokens: int = Field(
        default=0, description="Total cached tokens (if available)"
    )
    total_cache_creation_tokens: int = Field(
        default=0, description="Total cache creation tokens (if available)"
    )

    # Final output
    final_output_text: str = Field(
        ..., description="Final output text from the execution"
    )

    # Conversation history (for replay/debugging)
    full_conversation_history: list[dict] = Field(
        default_factory=list,
        description="Complete conversation in OpenAI format for replay/debugging",
    )

    # Error tracking
    errors_encountered: list[str] = Field(
        default_factory=list, description="List of errors encountered during execution"
    )

    model_config = {"json_schema_extra": {"title": "Worker Execution Trace"}}
