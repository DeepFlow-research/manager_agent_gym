"""
Centralized LLM interface using Instructor for structured outputs.
"""

from typing import TypeVar, Any, NamedTuple
from pydantic import BaseModel

from manager_agent_gym.core.common.logging import logger

from litellm.cost_calculator import cost_per_token

T = TypeVar("T", bound=BaseModel)


class LLMUsage(NamedTuple):
    """Token usage information from LLM response."""

    input_tokens: int
    output_tokens: int
    cached_tokens: int = 0
    cache_creation_tokens: int = 0


class StructuredLLMResponse(NamedTuple):
    """Response from generate_structured_response including usage metadata."""

    result: Any  # The validated Pydantic object
    usage: LLMUsage | None  # Token usage (None if unavailable)


def calculate_llm_cost(usage: LLMUsage, model: str) -> float:
    """Calculate LLM cost in USD using litellm's cost_per_token.

    Args:
        usage: Token usage information
        model: Model name (e.g., "gpt-4o", "gpt-4o-mini")

    Returns:
        Total cost in USD
    """
    if cost_per_token is None:
        logger.warning("litellm not installed, cannot calculate cost")
        return 0.0

    try:
        prompt_cost, completion_cost = cost_per_token(
            model=model,
            prompt_tokens=usage.input_tokens,
            completion_tokens=usage.output_tokens,
            cache_read_input_tokens=usage.cached_tokens,
            cache_creation_input_tokens=usage.cache_creation_tokens,
        )
        return prompt_cost + completion_cost
    except Exception as e:
        logger.warning(f"Failed to calculate LLM cost for {model}: {e}")
        return 0.0


class LLMInferenceTruncationError(Exception):
    """Raised when the LLM provider indicates a truncation/content block.

    Carries provider and message context for better logging and graceful fallbacks.
    """

    def __init__(
        self,
        message: str,
        *,
        refusal_text: str | None = None,
        model: str | None = None,
        response_id: str | None = None,
        finish_reason: str | None = None,
        message_content_preview: str | None = None,
        provider_fields: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.refusal_text = refusal_text
        self.model = model
        self.response_id = response_id
        self.finish_reason = finish_reason
        self.provider_fields = provider_fields or {}

    def __str__(self) -> str:  # pragma: no cover - formatting helper
        base = super().__str__()
        details: list[str] = []
        if self.model:
            details.append(f"model={self.model}")
        if self.finish_reason:
            details.append(f"finish_reason={self.finish_reason}")
        if self.response_id:
            details.append(f"response_id={self.response_id}")
        if self.refusal_text:
            # Trim to avoid log spam
            trimmed = (
                self.refusal_text
                if len(self.refusal_text) <= 2048
                else self.refusal_text[:2048] + "…"
            )
            details.append(f"refusal={trimmed}")

        return base + (" [" + ", ".join(details) + "]" if details else "")


# DEPRECATED: _get_openai_client removed - use CloudLLMGenerator instead


def build_litellm_model_id(model_id: str) -> str:
    """Build the litellm model ID by prepending the appropriate provider prefix.

    NOTE: This function is kept for backward compatibility with other parts of the codebase
    that still use LiteLLM directly. The structured generation functionality now uses
    OpenAI's native client.
    """
    # OpenAI models
    if model_id.startswith(("gpt-", "o")):
        return f"openai/{model_id}"
    # Anthropic models
    elif model_id.startswith("claude-"):
        return f"anthropic/{model_id}"
    # Google models
    elif model_id.startswith("gemini-"):
        return f"google/{model_id}"
    # Bedrock models (already have provider prefix)
    elif model_id.startswith(("eu.anthropic.", "eu.openai.", "eu.google.", "bedrock/")):
        return model_id
    # Default case - return as is
    else:
        return model_id


# DEPRECATED: generate_structured_response removed
# Use CloudLLMGenerator + OpenAI Agents SDK instead:
#
# from manager_agent_gym.core.common.llm_generator import CloudLLMGenerator
# from agents import Agent
# from agents.run import Runner
#
# generator = CloudLLMGenerator(model_name="gpt-4o")
# agent = Agent(
#     name="my_agent",
#     model=generator,
#     instructions=system_prompt,
#     output_type=YourPydanticModel,
# )
# result = await Runner.run(agent, user_prompt)
# response = result.final_output
