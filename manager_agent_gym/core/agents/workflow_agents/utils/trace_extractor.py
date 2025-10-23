"""
Utility for extracting execution traces from OpenAI Agents SDK RunResult.

This converts the rich RunResult object (with all messages, tool calls, tokens)
into our WorkerExecutionTrace schema for storage and debugging.
"""

from datetime import datetime
from uuid import UUID
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from agents.result import RunResult  # type: ignore
    from agents.items import (  # type: ignore
        ToolCallOutputItem,
        ReasoningItem,
    )
    from openai.types.responses import (  # type: ignore
        ResponseOutputMessage,
        ResponseFunctionToolCall,
        ResponseFileSearchToolCall,
        ResponseFunctionWebSearch,
        ResponseComputerToolCall,
    )

try:
    from agents.result import RunResult  # type: ignore
    from agents.items import (  # type: ignore
        ToolCallOutputItem,
        ReasoningItem,
    )
    from openai.types.responses import (  # type: ignore
        ResponseOutputMessage,
        ResponseFunctionToolCall,
        ResponseFileSearchToolCall,
        ResponseFunctionWebSearch,
        ResponseComputerToolCall,
    )

    AGENTS_SDK_AVAILABLE = True
except ImportError:
    AGENTS_SDK_AVAILABLE = False

from manager_agent_gym.schemas.execution.trace import (
    WorkerExecutionTrace,
    ModelTurnTrace,
    MessageTrace,
    ToolCallTrace,
)


def extract_execution_trace(
    result: "RunResult",
    agent_id: str,
    task_id: UUID,
    started_at: datetime,
    completed_at: datetime | None = None,
) -> WorkerExecutionTrace:
    """
    Extract complete execution trace from OpenAI Agents SDK RunResult.

    Args:
        result: RunResult from Runner.run()
        agent_id: ID of the agent that executed
        task_id: ID of the task that was executed
        started_at: When execution started
        completed_at: When execution completed (defaults to now)

    Returns:
        WorkerExecutionTrace with all execution details
    """
    if not AGENTS_SDK_AVAILABLE:
        raise ImportError(
            "OpenAI Agents SDK not available. Cannot extract execution trace."
        )

    if completed_at is None:
        completed_at = datetime.now()

    duration_seconds = (completed_at - started_at).total_seconds()

    # Extract model turns with token usage
    model_turns: list[ModelTurnTrace] = []
    total_input_tokens = 0
    total_output_tokens = 0
    total_tokens = 0
    total_cached_tokens = 0
    total_cache_creation_tokens = 0

    for turn_idx, raw_response in enumerate(result.raw_responses):
        # Extract usage stats
        input_tokens = raw_response.usage.input_tokens
        output_tokens = raw_response.usage.output_tokens
        response_total_tokens = raw_response.usage.total_tokens

        # Extract cache tokens if available
        cached_tokens = 0
        cache_creation_tokens = 0
        try:
            if hasattr(raw_response.usage, "input_tokens_details"):
                details = raw_response.usage.input_tokens_details
                if details and hasattr(details, "cached_tokens"):
                    cached_tokens = getattr(details, "cached_tokens", 0) or 0
                if details and hasattr(details, "cache_creation_tokens"):
                    cache_creation_tokens = (
                        getattr(details, "cache_creation_tokens", 0) or 0
                    )
        except (AttributeError, TypeError):
            pass

        # Accumulate totals
        total_input_tokens += input_tokens
        total_output_tokens += output_tokens
        total_tokens += response_total_tokens
        total_cached_tokens += cached_tokens
        total_cache_creation_tokens += cache_creation_tokens

        # Extract messages and tool calls from this turn
        turn_messages: list[MessageTrace] = []
        turn_tool_calls: list[ToolCallTrace] = []
        reasoning_text: str | None = None

        for output_item in raw_response.output:
            if isinstance(output_item, ResponseOutputMessage):
                # Extract message content
                content_text = ""
                content = getattr(output_item, "content", "")
                if isinstance(content, list):
                    for part in content:
                        part_type = getattr(part, "type", None)
                        if part_type == "output_text":
                            content_text += getattr(part, "text", "")
                        elif part_type == "refusal":
                            content_text += f"[REFUSAL: {getattr(part, 'refusal', '')}]"
                else:
                    content_text = str(content)

                turn_messages.append(
                    MessageTrace(
                        role=getattr(output_item, "role", "assistant"),
                        content=content_text,
                        message_id=getattr(output_item, "id", None) or "",
                        status=getattr(output_item, "status", "completed"),
                    )
                )

            elif isinstance(output_item, ResponseFunctionToolCall):
                # Function tool call
                turn_tool_calls.append(
                    ToolCallTrace(
                        tool_name=getattr(output_item, "name", "unknown"),
                        arguments=getattr(output_item, "arguments", ""),
                        output=None,  # Will be filled in later if we find the output
                    )
                )

            elif isinstance(
                output_item,
                (
                    ResponseFileSearchToolCall,
                    ResponseFunctionWebSearch,
                    ResponseComputerToolCall,
                ),
            ):
                # Other tool types
                tool_type = type(output_item).__name__
                turn_tool_calls.append(
                    ToolCallTrace(
                        tool_name=tool_type,
                        arguments="",
                        output=None,
                    )
                )

        # Now match tool outputs from result.new_items
        # This helps us correlate tool calls with their outputs
        tool_call_idx = 0
        for item in result.new_items:
            if isinstance(item, ToolCallOutputItem):
                if tool_call_idx < len(turn_tool_calls):
                    output_value = getattr(item, "output", "")
                    turn_tool_calls[tool_call_idx].output = str(output_value)
                    turn_tool_calls[tool_call_idx].succeeded = True
                    tool_call_idx += 1

            elif isinstance(item, ReasoningItem):
                # Extract reasoning (for o1 models)
                if reasoning_text is None:
                    reasoning_text = ""
                # ReasoningItem has a content field directly
                if hasattr(item, "raw_item"):
                    raw_item = getattr(item, "raw_item", None)
                    if raw_item and hasattr(raw_item, "content"):
                        content = getattr(raw_item, "content", "")
                        reasoning_text += str(content)

        model_turns.append(
            ModelTurnTrace(
                response_id=raw_response.response_id or f"turn_{turn_idx}",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=response_total_tokens,
                cached_tokens=cached_tokens,
                cache_creation_tokens=cache_creation_tokens,
                messages=turn_messages,
                tool_calls=turn_tool_calls,
                reasoning=reasoning_text,
                turn_index=turn_idx,
            )
        )

    # Get final output text
    final_output_text = str(result.final_output)

    # Get conversation history for replay
    full_conversation: list[dict] = []
    try:
        conversation_raw = result.to_input_list()
        # Convert to dict format for JSON serialization
        for msg in conversation_raw:
            try:
                msg_any: Any = msg
                if isinstance(msg_any, dict):
                    full_conversation.append(msg_any)  # type: ignore
                elif hasattr(msg_any, "model_dump"):
                    full_conversation.append(msg_any.model_dump())  # type: ignore
                else:
                    # Fallback: try to convert to dict
                    full_conversation.append(
                        {"type": type(msg_any).__name__, "data": str(msg_any)}
                    )  # type: ignore
            except Exception:
                # Skip problematic messages
                continue
    except Exception:
        # If to_input_list fails, create a minimal history
        pass

    # Count errors
    errors_encountered: list[str] = []
    for item in result.new_items:
        if isinstance(item, ToolCallOutputItem):
            # Check for tool errors in the output
            output_value = getattr(item, "output", "")
            output_str = str(output_value)
            if "error" in output_str.lower() or "failed" in output_str.lower():
                errors_encountered.append(f"Tool error: {output_str[:200]}")

    # Count total tool calls
    total_tool_calls = sum(len(turn.tool_calls) for turn in model_turns)

    return WorkerExecutionTrace(
        agent_id=agent_id,
        task_id=task_id,
        started_at=started_at,
        completed_at=completed_at,
        duration_seconds=duration_seconds,
        model_turns=model_turns,
        total_turns=len(model_turns),
        total_input_tokens=total_input_tokens,
        total_output_tokens=total_output_tokens,
        total_tokens=total_tokens,
        total_cached_tokens=total_cached_tokens,
        total_cache_creation_tokens=total_cache_creation_tokens,
        total_tool_calls=total_tool_calls,
        final_output_text=final_output_text,
        full_conversation_history=full_conversation,
        errors_encountered=errors_encountered,
    )
