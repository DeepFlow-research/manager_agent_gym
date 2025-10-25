"""
Unified LLM generator interface compatible with OpenAI Agents SDK.

This module provides a common interface for both cloud (OpenAI API) and local
(HuggingFace) LLM inference, enabling seamless switching between inference modes
and supporting gradient accumulation for RL training.

Supports both OpenAI (GPT-4o, GPT-4o-mini) and Anthropic (Claude Sonnet, Haiku).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any, TYPE_CHECKING

from openai import NOT_GIVEN, AsyncOpenAI
from openai.types.responses.response_prompt_param import ResponsePromptParam

from anthropic import AsyncAnthropic
from anthropic.types import (
    MessageParam,
    ToolParam,
    ToolUseBlock,
    TextBlock,
)


from agents.models.interface import Model, ModelTracing
from agents.models.chatcmpl_converter import Converter
from agents.items import ModelResponse, TResponseInputItem, TResponseStreamEvent
from agents.usage import Usage
from agents.agent_output import AgentOutputSchemaBase
from agents.handoffs import Handoff
from agents.tool import Tool
from agents.tracing import generation_span

if TYPE_CHECKING:
    from agents.model_settings import ModelSettings


# ============================================================================
# Anthropic ↔ OpenAI Conversion Helpers
# ============================================================================


def _convert_messages_to_anthropic(
    messages: list[dict[str, Any]] | list[Any],
) -> tuple[str | None, list[MessageParam]]:
    """Convert OpenAI-style messages to Anthropic format.

    Returns:
        (system_prompt, anthropic_messages)
    """
    system_prompt: str | None = None
    anthropic_messages: list[MessageParam] = []

    for msg in messages:
        role = msg.get("role")
        content = msg.get("content", "")

        # Extract system message (Anthropic handles it separately)
        if role == "system":
            if system_prompt:
                system_prompt += f"\n\n{content}"
            else:
                system_prompt = content
            continue

        # Convert tool calls from OpenAI to Anthropic format
        if role == "assistant" and "tool_calls" in msg:
            import json

            # Assistant message with tool calls
            anthropic_content: list[dict[str, Any]] = []

            # Add text content if present
            if content:
                anthropic_content.append({"type": "text", "text": content})

            # Add tool use blocks
            for tool_call in msg.get("tool_calls", []):
                # OpenAI's arguments field is a JSON string, parse it to dict
                arguments_str = tool_call.get("function", {}).get("arguments", "{}")
                try:
                    arguments_dict = (
                        json.loads(arguments_str)
                        if isinstance(arguments_str, str)
                        else arguments_str
                    )
                except json.JSONDecodeError:
                    arguments_dict = {}

                anthropic_content.append(
                    {
                        "type": "tool_use",
                        "id": tool_call.get("id", ""),
                        "name": tool_call.get("function", {}).get("name", ""),
                        "input": arguments_dict,
                    }
                )

            msg_param: MessageParam = {
                "role": "assistant",
                "content": anthropic_content,
            }
            anthropic_messages.append(msg_param)
            continue

        # Convert tool results from OpenAI to Anthropic format
        if role == "tool":
            anthropic_messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": msg.get("tool_call_id", ""),
                            "content": content,
                        }
                    ],
                }
            )
            continue

        # Regular user/assistant messages
        if role in ("user", "assistant"):
            # Handle multimodal content (images, etc.)
            if isinstance(content, list):
                anthropic_content_list = []
                for item in content:
                    if isinstance(item, dict):
                        if item.get("type") == "text":
                            anthropic_content_list.append(
                                {
                                    "type": "text",
                                    "text": item.get("text", ""),
                                }
                            )
                        elif item.get("type") == "image_url":
                            # Anthropic uses base64 image format
                            image_url = item.get("image_url", {}).get("url", "")
                            if image_url.startswith("data:image"):
                                # Extract base64 data
                                parts = image_url.split(",", 1)
                                if len(parts) == 2:
                                    media_type = parts[0].split(":")[1].split(";")[0]
                                    base64_data = parts[1]
                                    anthropic_content_list.append(
                                        {
                                            "type": "image",
                                            "source": {
                                                "type": "base64",
                                                "media_type": media_type,
                                                "data": base64_data,
                                            },
                                        }
                                    )
                    else:
                        anthropic_content_list.append(
                            {
                                "type": "text",
                                "text": str(item),
                            }
                        )

                anthropic_messages.append(
                    {
                        "role": role,
                        "content": anthropic_content_list,
                    }
                )
            else:
                anthropic_messages.append(
                    {
                        "role": role,
                        "content": str(content),
                    }
                )

    return system_prompt, anthropic_messages


def _convert_tools_to_anthropic(tools: list[dict[str, Any]] | list[Any]) -> list[ToolParam]:
    """Convert OpenAI-style tools to Anthropic format."""
    anthropic_tools: list[ToolParam] = []

    for tool in tools:
        if tool.get("type") == "function":
            func = tool.get("function", {})
            anthropic_tools.append(
                {
                    "name": func.get("name", ""),
                    "description": func.get("description", ""),
                    "input_schema": func.get("parameters", {}),
                }
            )

    return anthropic_tools


def _convert_anthropic_response_to_openai(
    anthropic_response: Any,
) -> dict[str, Any]:
    """Convert Anthropic response to OpenAI chat completion format."""
    # Extract content blocks
    content_blocks = anthropic_response.content

    # Build OpenAI-style message
    openai_message: dict[str, Any] = {
        "role": "assistant",
        "content": "",
    }

    tool_calls = []
    text_parts = []

    for block in content_blocks:
        if isinstance(block, TextBlock) or (
            isinstance(block, dict) and block.get("type") == "text"
        ):
            text_content = (
                block.text if isinstance(block, TextBlock) else block.get("text", "")
            )
            text_parts.append(text_content)

        elif isinstance(block, ToolUseBlock) or (
            isinstance(block, dict) and block.get("type") == "tool_use"
        ):
            import json

            tool_id = (
                block.id if isinstance(block, ToolUseBlock) else block.get("id", "")
            )
            tool_name = (
                block.name if isinstance(block, ToolUseBlock) else block.get("name", "")
            )
            tool_input = (
                block.input
                if isinstance(block, ToolUseBlock)
                else block.get("input", {})
            )

            # Convert tool input to JSON string (OpenAI format)
            tool_args_str = (
                json.dumps(tool_input)
                if isinstance(tool_input, dict)
                else str(tool_input)
            )

            tool_calls.append(
                {
                    "id": tool_id,
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "arguments": tool_args_str,
                    },
                }
            )

    # Combine text parts
    if text_parts:
        openai_message["content"] = "\n".join(text_parts)

    # Add tool calls if present
    if tool_calls:
        openai_message["tool_calls"] = tool_calls

    return openai_message


# ============================================================================
# LLM Generator Classes
# ============================================================================


class LLMGenerator(Model, ABC):
    """Base interface for LLM inference (cloud or local).

    Implements OpenAI Agents SDK Model interface for compatibility with
    the agents library, while adding training-specific methods for
    gradient accumulation and backpropagation.

    Subclasses must implement:
    - get_response(): Generate complete response
    - stream_response(): Stream response chunks

    Optional training methods:
    - store_generation_metadata(): Store generation data for training
    - compute_loss(): Compute loss from advantages
    - backpropagate(): Perform gradient update
    """

    @abstractmethod
    async def get_response(
        self,
        system_instructions: str | None,
        input: str | list[TResponseInputItem],
        model_settings: "ModelSettings",
        tools: list[Tool],
        output_schema: AgentOutputSchemaBase | None,
        handoffs: list[Handoff],
        tracing: ModelTracing,
        *,
        previous_response_id: str | None,
        prompt: ResponsePromptParam | None = None,
    ) -> ModelResponse:
        """Get a response from the model."""
        pass

    @abstractmethod
    def stream_response(
        self,
        system_instructions: str | None,
        input: str | list[TResponseInputItem],
        model_settings: "ModelSettings",
        tools: list[Tool],
        output_schema: AgentOutputSchemaBase | None,
        handoffs: list[Handoff],
        tracing: ModelTracing,
        *,
        previous_response_id: str | None,
        prompt: ResponsePromptParam | None = None,
    ) -> AsyncIterator[TResponseStreamEvent]:
        """Stream a response from the model."""
        pass

    # Training-specific methods (no-ops for cloud, implemented for local)

    def store_generation_metadata(self, metadata: dict[str, Any]) -> None:
        """Store generation metadata for training."""
        pass

    def compute_loss(self, advantages: list[float]) -> Any:
        """Compute loss for backpropagation."""
        pass

    def backpropagate(self, loss: Any) -> None:
        """Perform backpropagation and parameter update."""
        pass


class CloudLLMGenerator(LLMGenerator):
    """Multi-provider cloud inference (OpenAI GPT + Anthropic Claude).

    Supports:
    - OpenAI: gpt-4o, gpt-4o-mini, gpt-5, etc.
    - Anthropic: claude-3-5-sonnet-20241022, claude-3-5-haiku-20241022, etc.

    Auto-detects provider from model name and uses official SDKs for maximum
    reliability with tool calling.
    """

    def __init__(self, model_name: str = "gpt-4o"):
        """Initialize cloud generator.

        Args:
            model_name: Model identifier
                - OpenAI: "gpt-4o", "gpt-4o-mini", "gpt-5"
                - Anthropic: "claude-sonnet-4-5", "claude-haiku-4-5", "claude-3-5-sonnet-20241022", etc.
        """
        self.model_name = model_name
        self._openai_client: AsyncOpenAI | None = None
        self._anthropic_client: AsyncAnthropic | None = None

        # Detect provider
        self.provider = self._detect_provider(model_name)

    @staticmethod
    def _detect_provider(model_name: str) -> str:
        """Detect provider from model name."""
        model_lower = model_name.lower()
        if model_lower.startswith("gpt-") or model_lower.startswith("o1-"):
            return "openai"
        elif "claude" in model_lower:
            return "anthropic"
        else:
            # Default to OpenAI for unknown models
            return "openai"

    def _get_openai_client(self) -> AsyncOpenAI:
        """Get or create OpenAI client."""
        if self._openai_client is None:
            import os

            api_key = os.environ.get("OPENAI_API_KEY", "")
            if not api_key or api_key == "na":
                raise ValueError("OpenAI API key not found in environment")

            self._openai_client = AsyncOpenAI(api_key=api_key)
        return self._openai_client

    def _get_anthropic_client(self) -> AsyncAnthropic:
        """Get or create Anthropic client."""
        if self._anthropic_client is None:
            import os

            api_key = os.environ.get("ANTHROPIC_API_KEY", "")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not found in environment")

            self._anthropic_client = AsyncAnthropic(api_key=api_key)
        return self._anthropic_client

    async def get_response(
        self,
        system_instructions: str | None,
        input: str | list[TResponseInputItem],
        model_settings: "ModelSettings",
        tools: list[Tool],
        output_schema: AgentOutputSchemaBase | None,
        handoffs: list[Handoff],
        tracing: ModelTracing,
        *,
        previous_response_id: str | None,
        prompt: ResponsePromptParam | None = None,
    ) -> ModelResponse:
        """Generate response using OpenAI or Anthropic API."""

        if self.provider == "openai":
            return await self._get_response_openai(
                system_instructions=system_instructions,
                input=input,
                model_settings=model_settings,
                tools=tools,
                output_schema=output_schema,
                handoffs=handoffs,
                tracing=tracing,
                previous_response_id=previous_response_id,
                prompt=prompt,
            )
        elif self.provider == "anthropic":
            return await self._get_response_anthropic(
                system_instructions=system_instructions,
                input=input,
                model_settings=model_settings,
                tools=tools,
                output_schema=output_schema,
                handoffs=handoffs,
                tracing=tracing,
                previous_response_id=previous_response_id,
                prompt=prompt,
            )
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    async def _get_response_openai(
        self,
        system_instructions: str | None,
        input: str | list[TResponseInputItem],
        model_settings: "ModelSettings",
        tools: list[Tool],
        output_schema: AgentOutputSchemaBase | None,
        handoffs: list[Handoff],
        tracing: ModelTracing,
        *,
        previous_response_id: str | None,
        prompt: ResponsePromptParam | None = None,
    ) -> ModelResponse:
        """OpenAI-specific implementation."""

        with generation_span(
            model=str(self.model_name),
            model_config=model_settings.to_json_dict()
            | {"base_url": str(self._get_openai_client().base_url)},
            disabled=tracing.is_disabled(),
        ) as span_generation:
            # Convert input items to messages using SDK's Converter
            converted_messages = Converter.items_to_messages(input)

            # Add system instructions
            if system_instructions:
                converted_messages.insert(
                    0,
                    {
                        "content": system_instructions,
                        "role": "system",
                    },
                )

            if tracing.include_data():
                span_generation.span_data.input = converted_messages

            # Convert tools using SDK's Converter
            converted_tools = (
                [Converter.tool_to_openai(tool) for tool in tools] if tools else []
            )

            # Add handoffs as tools
            for handoff in handoffs:
                converted_tools.append(Converter.convert_handoff_tool(handoff))

            # Convert response format for structured output
            response_format = Converter.convert_response_format(output_schema)

            # Build API parameters
            api_params: dict[str, Any] = {
                "model": self.model_name,
                "messages": converted_messages,
                "temperature": model_settings.temperature
                if model_settings.temperature is not None
                else 1.0,
            }

            # Add tools if present
            if converted_tools:
                api_params["tools"] = converted_tools
                tool_choice = Converter.convert_tool_choice(model_settings.tool_choice)
                if tool_choice is not NOT_GIVEN:
                    api_params["tool_choice"] = tool_choice

            # Add response format for structured output
            if response_format is not NOT_GIVEN:
                api_params["response_format"] = response_format

            # Add other settings
            if model_settings.max_tokens is not None:
                api_params["max_tokens"] = model_settings.max_tokens
            if model_settings.top_p is not None:
                api_params["top_p"] = model_settings.top_p
            if model_settings.frequency_penalty is not None:
                api_params["frequency_penalty"] = model_settings.frequency_penalty
            if model_settings.presence_penalty is not None:
                api_params["presence_penalty"] = model_settings.presence_penalty

            # Call OpenAI API
            completion = await self._get_openai_client().chat.completions.create(
                **api_params
            )

            if tracing.include_data():
                span_generation.span_data.output = [
                    completion.choices[0].message.model_dump()
                ]

            span_generation.span_data.usage = {
                "input_tokens": completion.usage.prompt_tokens
                if completion.usage
                else 0,
                "output_tokens": completion.usage.completion_tokens
                if completion.usage
                else 0,
            }

            # Convert response back to SDK format using Converter
            items = Converter.message_to_output_items(completion.choices[0].message)

            usage = Usage(
                requests=1,
                input_tokens=completion.usage.prompt_tokens if completion.usage else 0,
                output_tokens=completion.usage.completion_tokens
                if completion.usage
                else 0,
                total_tokens=completion.usage.total_tokens if completion.usage else 0,
            )

            return ModelResponse(
                output=items,
                usage=usage,
                response_id=completion.id,
            )

    async def _get_response_anthropic(
        self,
        system_instructions: str | None,
        input: str | list[TResponseInputItem],
        model_settings: "ModelSettings",
        tools: list[Tool],
        output_schema: AgentOutputSchemaBase | None,
        handoffs: list[Handoff],
        tracing: ModelTracing,
        *,
        previous_response_id: str | None,
        prompt: ResponsePromptParam | None = None,
    ) -> ModelResponse:
        """Anthropic-specific implementation with proper conversion."""

        with generation_span(
            model=str(self.model_name),
            model_config=model_settings.to_json_dict() | {"provider": "anthropic"},
            disabled=tracing.is_disabled(),
        ) as span_generation:
            # Step 1: Convert input to OpenAI format (using SDK's Converter)
            converted_messages = Converter.items_to_messages(input)

            # Add system instructions to messages (will be extracted later)
            if system_instructions:
                converted_messages.insert(
                    0,
                    {
                        "content": system_instructions,
                        "role": "system",
                    },
                )

            if tracing.include_data():
                span_generation.span_data.input = converted_messages

            # Step 2: Convert OpenAI format to Anthropic format
            system_prompt, anthropic_messages = _convert_messages_to_anthropic(
                converted_messages
            )

            # Step 3: Convert tools to Anthropic format
            converted_tools = (
                [Converter.tool_to_openai(tool) for tool in tools] if tools else []
            )

            # Add handoffs as tools
            for handoff in handoffs:
                converted_tools.append(Converter.convert_handoff_tool(handoff))

            anthropic_tools = _convert_tools_to_anthropic(converted_tools)

            # Step 4: Build Anthropic API parameters
            api_params: dict[str, Any] = {
                "model": self.model_name,
                "messages": anthropic_messages,
                "max_tokens": model_settings.max_tokens
                or 4096,  # Required by Anthropic
            }

            # Add system prompt if present
            if system_prompt:
                api_params["system"] = system_prompt

            # Add tools if present
            if anthropic_tools:
                api_params["tools"] = anthropic_tools

                # Handle tool choice
                if model_settings.tool_choice:
                    if model_settings.tool_choice == "auto":
                        api_params["tool_choice"] = {"type": "auto"}
                    elif model_settings.tool_choice == "required":
                        api_params["tool_choice"] = {"type": "any"}
                    elif isinstance(model_settings.tool_choice, dict):
                        # Specific tool choice
                        tool_name = model_settings.tool_choice.get("function", {}).get(
                            "name"
                        )
                        if tool_name:
                            api_params["tool_choice"] = {
                                "type": "tool",
                                "name": tool_name,
                            }

            # Add temperature
            if model_settings.temperature is not None:
                api_params["temperature"] = model_settings.temperature

            # Add top_p
            if model_settings.top_p is not None:
                api_params["top_p"] = model_settings.top_p

            # Note: Anthropic doesn't support frequency_penalty or presence_penalty

            # Step 5: Call Anthropic API
            anthropic_response = await self._get_anthropic_client().messages.create(
                **api_params
            )

            # Step 6: Convert Anthropic response to OpenAI format
            openai_message = _convert_anthropic_response_to_openai(anthropic_response)

            if tracing.include_data():
                span_generation.span_data.output = [openai_message]

            span_generation.span_data.usage = {
                "input_tokens": anthropic_response.usage.input_tokens,
                "output_tokens": anthropic_response.usage.output_tokens,
            }

            # Step 7: Convert OpenAI message to SDK output items using Converter
            # Create a mock OpenAI message object
            from openai.types.chat import ChatCompletionMessage

            mock_message = ChatCompletionMessage(
                role=openai_message["role"],
                content=openai_message.get("content"),
                tool_calls=openai_message.get("tool_calls"),
            )

            items = Converter.message_to_output_items(mock_message)

            usage = Usage(
                requests=1,
                input_tokens=anthropic_response.usage.input_tokens,
                output_tokens=anthropic_response.usage.output_tokens,
                total_tokens=(
                    anthropic_response.usage.input_tokens
                    + anthropic_response.usage.output_tokens
                ),
            )

            return ModelResponse(
                output=items,
                usage=usage,
                response_id=anthropic_response.id,
            )

    async def stream_response(
        self,
        system_instructions: str | None,
        input: str | list[TResponseInputItem],
        model_settings: "ModelSettings",
        tools: list[Tool],
        output_schema: AgentOutputSchemaBase | None,
        handoffs: list[Handoff],
        tracing: ModelTracing,
        *,
        previous_response_id: str | None,
        prompt: ResponsePromptParam | None = None,
    ) -> AsyncIterator[TResponseStreamEvent]:
        """Stream response (simplified: get complete then yield)."""
        response = await self.get_response(
            system_instructions=system_instructions,
            input=input,
            model_settings=model_settings,
            tools=tools,
            output_schema=output_schema,
            handoffs=handoffs,
            tracing=tracing,
            previous_response_id=previous_response_id,
            prompt=prompt,
        )
        yield response  # type: ignore


class LocalLLMGenerator(LLMGenerator):
    """Local HuggingFace model inference (for training).

    Skeleton implementation for future local inference support.
    All methods raise NotImplementedError.
    """

    def __init__(self, model_path: str, device: str = "cuda"):
        """Initialize local generator."""
        self.model_path = model_path
        self.device = device
        self.generation_metadata: list[dict[str, Any]] = []

    async def get_response(
        self,
        system_instructions: str | None,
        input: str | list[TResponseInputItem],
        model_settings: "ModelSettings",
        tools: list[Tool],
        output_schema: AgentOutputSchemaBase | None,
        handoffs: list[Handoff],
        tracing: ModelTracing,
        *,
        previous_response_id: str | None,
        prompt: ResponsePromptParam | None = None,
    ) -> ModelResponse:
        """Not yet implemented."""
        raise NotImplementedError(
            "Local inference not yet implemented. Use CloudLLMGenerator for now."
        )

    def stream_response(
        self,
        system_instructions: str | None,
        input: str | list[TResponseInputItem],
        model_settings: "ModelSettings",
        tools: list[Tool],
        output_schema: AgentOutputSchemaBase | None,
        handoffs: list[Handoff],
        tracing: ModelTracing,
        *,
        previous_response_id: str | None,
        prompt: ResponsePromptParam | None = None,
    ) -> AsyncIterator[TResponseStreamEvent]:
        """Not yet implemented."""
        raise NotImplementedError(
            "Local streaming not yet implemented. Use CloudLLMGenerator for now."
        )

    def store_generation_metadata(self, metadata: dict[str, Any]) -> None:
        """Store generation metadata for training."""
        self.generation_metadata.append(metadata)

    def compute_loss(self, advantages: list[float]) -> Any:
        """Not yet implemented."""
        raise NotImplementedError(
            "Loss computation not yet implemented. "
            "Will be added when local inference is implemented."
        )

    def backpropagate(self, loss: Any) -> None:
        """Not yet implemented."""
        raise NotImplementedError(
            "Backpropagation not yet implemented. "
            "Will be added when local inference is implemented."
        )


# ============================================================================
# Structured Output Fix for Anthropic Models
# ============================================================================


async def fix_structured_output_with_openai(
    raw_text_output: str,
    output_schema: type,
    model: str = "gpt-4.1-mini",
) -> Any:
    """Parse unstructured text into structured format using a fast OpenAI model.

    This is a workaround for Anthropic models which don't support native structured
    outputs. We use a fast OpenAI model (gpt-4o-mini) to parse Claude's natural
    language response into the required Pydantic schema.

    Args:
        raw_text_output: The unstructured text response from Claude
        output_schema: The Pydantic model class to parse into
        model: OpenAI model to use for parsing (default: gpt-4o-mini)

    Returns:
        Validated instance of output_schema

    Example:
        ```python
        # Claude returned natural language
        raw_response = "I'll start by analyzing... [long text]"

        # Parse it into structured format
        structured = await fix_structured_output_with_openai(
            raw_text_output=raw_response,
            output_schema=AITaskOutput,
        )
        # Now structured.answer, structured.confidence, etc. are properly populated
        ```
    """
    from agents import Agent
    from agents.run import Runner

    # Create a fast OpenAI generator for parsing
    parser_generator = CloudLLMGenerator(model_name=model)

    system_prompt = """You are a precise JSON parser. Your ONLY job is to:
1. Read the provided text response
2. Extract the relevant information
3. Format it into a valid JSON object matching the exact schema

CRITICAL RULES:
- Output ONLY valid JSON
- Match the schema EXACTLY
- If information is missing, use reasonable defaults
- Do NOT add commentary or explanations
- Do NOT wrap in markdown code blocks"""

    user_prompt = f"""Parse this text response into the required JSON schema:

TEXT RESPONSE:
{raw_text_output}

Convert the above text into valid JSON matching the required schema. Extract the key information and structure it properly."""

    # Use Agents SDK to get structured output with strict schema
    agent = Agent(
        name="json_parser",
        model=parser_generator,
        instructions=system_prompt,
        output_type=output_schema,
    )

    result = await Runner.run(agent, user_prompt)
    return result.final_output
