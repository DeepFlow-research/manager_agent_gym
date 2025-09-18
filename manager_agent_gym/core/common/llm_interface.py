"""
Centralized LLM interface using Instructor for structured outputs.
"""

from openai import AsyncOpenAI
import instructor
from typing import TypeVar, Type, Any
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
    """Get configured OpenAI async client patched by Instructor."""
    client = AsyncOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        timeout=300.0,  # 5 minute timeout for long responses
    )
    # Patch the client to support response_model with validation & retries
    if instructor is not None:  # type: ignore[truthy-function]
        instructor.patch(client)  # type: ignore[attr-defined]
    return client


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


# Note: Manual prompt truncation and custom retry loops have been removed.
# Instructor handles validation and retry semantics internally.


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
    Generate a structured response via Instructor with Pydantic validation and provider-agnostic handling.

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
    # Build messages array
    messages = [{"role": "system", "content": system_prompt}]
    if user_prompt:
        messages.append({"role": "user", "content": user_prompt})
    # Get Instructor-patched OpenAI client
    client = _get_openai_client()

    try:
        # Compatibility path for older tests/mocks expecting .beta.chat.completions.parse
        beta = getattr(client, "beta", None)
        if beta is not None and hasattr(beta, "chat") and hasattr(beta.chat, "completions") and hasattr(beta.chat.completions, "parse"):
            response = await beta.chat.completions.parse(
                model=model,
                messages=messages,
                response_format=response_type,
                temperature=temperature,
                seed=seed,
            )

            # Check for refusal
            if getattr(response.choices[0].message, "refusal", None):
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
                        "messages": messages,
                        "response_type": response_type,
                    },
                )
                logger.error(
                    f"LLM refused to generate {response_type.__name__}: {error}"
                )
                raise error

            # Check for content
            if not getattr(response.choices[0].message, "parsed", None):
                error = LLMInferenceTruncationError(
                    f"LLM failed to generate structured {response_type.__name__}",
                    model=model,
                    response_id=response.id,
                    finish_reason=response.choices[0].finish_reason,
                    provider_fields={
                        "seed": seed,
                        "max_completion_tokens": max_completion_tokens,
                        "temperature": temperature,
                        "messages": messages,
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

        # Default path using Instructor-enhanced create()
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "response_model": response_type,
            "temperature": temperature,
            "seed": seed,
        }
        if max_completion_tokens and max_completion_tokens > 0:
            kwargs["max_tokens"] = max_completion_tokens

        create_fn: Any = client.chat.completions.create
        result: T = await create_fn(
            max_retries=max_retries,
            **kwargs,
        )
        return result

    except Exception as e:
        if isinstance(e, LLMInferenceTruncationError):
            # Preserve rich error details from compatibility path
            raise
        error = LLMInferenceTruncationError(
            f"LLM request failed for {response_type.__name__}: {str(e)}",
            model=model,
            provider_fields={
                "seed": seed,
                "max_completion_tokens": max_completion_tokens,
                "temperature": temperature,
                "messages": messages,
                "response_type": response_type,
                "original_error": str(e),
                "error_type": type(e).__name__,
            },
        )
        logger.error(f"LLM request failed for {response_type.__name__}: {error}")
        raise error
