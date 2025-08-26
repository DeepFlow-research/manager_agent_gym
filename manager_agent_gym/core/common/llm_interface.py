"""
Centralized LLM interface for validation rules and other components.
"""

from openai import AsyncOpenAI
import asyncio

from typing import TypeVar, Type, Any, cast
import os
from pydantic import BaseModel
from .logging import logger

T = TypeVar("T", bound=BaseModel)


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


def _get_openai_client() -> AsyncOpenAI:
    """Get configured OpenAI async client."""
    return AsyncOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        timeout=300.0,  # 5 minute timeout for long responses
    )


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


def _resolve_max_prompt_tokens() -> int:
    """Resolve max prompt tokens from env (MAG_MAX_PROMPT_TOKENS) or default 100k."""
    try:
        env_val = os.environ.get("MAG_MAX_PROMPT_TOKENS")
        if env_val is not None:
            return max(1, int(env_val))
    except Exception:
        pass
    return 100_000


def _truncate_text_budget(text: str, max_tokens: int) -> str:
    """Approximate truncation using 4 chars/token; keep head and tail context."""
    chars_per_token = 4
    max_chars = max(2_000, max_tokens * chars_per_token)
    if len(text) <= max_chars:
        return text
    head_chars = int(max_chars * 0.6)
    tail_chars = max_chars - head_chars
    return (
        text[:head_chars] + "\n\n...[TRUNCATED FOR LENGTH]...\n\n" + text[-tail_chars:]
    )


def _apply_truncation_to_messages(
    messages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    max_tokens = _resolve_max_prompt_tokens()
    out: list[dict[str, Any]] = []
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content")
        if isinstance(content, str):
            out.append(
                {"role": role, "content": _truncate_text_budget(content, max_tokens)}
            )
        else:
            out.append(m)
    return out


async def generate_structured_response(
    system_prompt: str,
    user_prompt: str | None,
    response_type: Type[T],
    seed: int,
    model: str = "gpt-4o",
    temperature: float = 1,
    max_completion_tokens: int = 0,
    max_retries: int = 0,
    retry_delay_seconds: float = 0.5,
) -> T:
    """
    Generate a structured response using OpenAI with structured outputs and Pydantic model validation.

    Args:
        system_prompt: System prompt for the LLM
        user_prompt: User prompt for the LLM
        response_type: Pydantic model class for response validation
        seed: Random seed for reproducible outputs
        model: The OpenAI model to use for generation (must support structured outputs)
        temperature: Temperature for generation (0-2)
        max_completion_tokens: Maximum tokens to generate
        max_retries: Number of retry attempts on failure
        retry_delay_seconds: Base delay between retries (exponential backoff)

    Returns:
        Instance of response_type populated with LLM response

    Raises:
        LLMInferenceTruncationError: If no valid response is received from LLM
        ValueError: If model is not supported for structured outputs
    """
    # Validate model supports structured outputs

    # Build messages array
    messages = [{"role": "system", "content": system_prompt}]
    if user_prompt:
        messages.append({"role": "user", "content": user_prompt})

    # Apply truncation to avoid token limits
    truncated_messages = _apply_truncation_to_messages(messages)

    # Get OpenAI client
    client = _get_openai_client()

    async def _attempt() -> T:
        try:
            response = await client.beta.chat.completions.parse(
                model=model,
                messages=cast(Any, truncated_messages),  # OpenAI typing is restrictive
                response_format=response_type,
                temperature=temperature,
                seed=seed,
                # max_completion_tokens=max_completion_tokens,
            )

            # Check for refusal
            if response.choices[0].message.refusal:
                error = LLMInferenceTruncationError(
                    f"LLM refused to generate {response_type.__name__}",
                    refusal_text=response.choices[0].message.refusal,
                    model=model,
                    response_id=response.id,
                    finish_reason=response.choices[0].finish_reason,
                    provider_fields={
                        "seed": seed,
                        "max_completion_tokens": max_completion_tokens,
                        "temperature": temperature,
                        "messages": truncated_messages,
                        "response_type": response_type,
                    },
                )
                logger.error(
                    f"LLM refused to generate {response_type.__name__}: {error}"
                )
                raise error

            # Check for content
            if not response.choices[0].message.parsed:
                error = LLMInferenceTruncationError(
                    f"LLM failed to generate structured {response_type.__name__}",
                    model=model,
                    response_id=response.id,
                    finish_reason=response.choices[0].finish_reason,
                    provider_fields={
                        "seed": seed,
                        "max_completion_tokens": max_completion_tokens,
                        "temperature": temperature,
                        "messages": truncated_messages,
                        "response": response,
                        "response_type": response_type,
                    },
                )
                logger.error(
                    f"LLM failed to generate {response_type.__name__}: {error}"
                )
                raise error

            # Return the parsed structured response
            return response.choices[0].message.parsed

        except Exception as e:
            if isinstance(e, LLMInferenceTruncationError):
                raise

            # Wrap other exceptions in our error type
            error = LLMInferenceTruncationError(
                f"LLM request failed for {response_type.__name__}: {str(e)}",
                model=model,
                provider_fields={
                    "seed": seed,
                    "max_completion_tokens": max_completion_tokens,
                    "temperature": temperature,
                    "messages": truncated_messages,
                    "response_type": response_type,
                    "original_error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            logger.error(f"LLM request failed for {response_type.__name__}: {error}")
            raise error

    attempts = max(1, max_retries + 1)
    for attempt_index in range(attempts):
        try:
            return await _attempt()
        except LLMInferenceTruncationError as e:
            if attempt_index == attempts - 1:
                raise e
            delay = retry_delay_seconds * (2**attempt_index)
            logger.warning(
                f"Retrying structured response generation due to error (attempt {attempt_index + 1}/{attempts}); sleeping {delay:.2f}s"
            )
            await asyncio.sleep(delay)

    # Unreachable: either returned a valid response or raised on final attempt
    raise LLMInferenceTruncationError(
        f"LLM failed to generate {response_type.__name__} after {attempts} attempts",
        model=model,
        provider_fields={
            "seed": seed,
            "max_completion_tokens": max_completion_tokens,
            "temperature": temperature,
            "messages": truncated_messages,
            "max_retries": max_retries,
        },
    )
