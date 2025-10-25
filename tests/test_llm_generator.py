"""
Tests for LLMGenerator interface and implementations.

Validates both CloudLLMGenerator and LocalLLMGenerator behavior.
"""

import pytest
from pydantic import BaseModel

from manager_agent_gym.core.common.llm_generator import (
    CloudLLMGenerator,
    LocalLLMGenerator,
    LLMGenerator,
)
from agents.agent_output import AgentOutputSchema
from agents.model_settings import ModelSettings
from agents.models.interface import ModelTracing


class SimpleResponse(BaseModel):
    """Test response schema."""

    message: str
    success: bool


@pytest.mark.asyncio
async def test_cloud_generator_instantiation():
    """Test CloudLLMGenerator can be instantiated."""
    generator = CloudLLMGenerator(model_name="gpt-4o-mini")
    assert generator.model_name == "gpt-4o-mini"
    assert isinstance(generator, LLMGenerator)


@pytest.mark.asyncio
async def test_cloud_generator_freeform_response():
    """Test CloudLLMGenerator can generate freeform text."""
    generator = CloudLLMGenerator(model_name="gpt-4o-mini")

    response = await generator.get_response(
        system_instructions="You are a helpful assistant.",
        input="Say hello!",
        model_settings=ModelSettings(seed=42, temperature=0.7),
        tools=[],
        output_schema=None,  # Freeform
        handoffs=[],
        tracing=ModelTracing.ENABLED,
        previous_response_id=None,
        prompt=None,
    )

    assert response.output
    assert len(response.output) > 0
    assert response.output[0].content
    assert response.usage.total_tokens > 0


@pytest.mark.asyncio
async def test_cloud_generator_structured_response():
    """Test CloudLLMGenerator can generate structured output."""
    generator = CloudLLMGenerator(model_name="gpt-4o-mini")

    response = await generator.get_response(
        system_instructions="You are a helpful assistant.",
        input='Respond with a JSON object: {"message": "Hello", "success": true}',
        model_settings=ModelSettings(seed=42, temperature=0.7),
        tools=[],
        output_schema=AgentOutputSchema(SimpleResponse),
        handoffs=[],
        tracing=ModelTracing.ENABLED,
        previous_response_id=None,
        prompt=None,
    )

    assert response.output
    # Validate the output is valid JSON that matches our schema
    output_text = response.output[0].content[0].text  # type: ignore
    parsed = SimpleResponse.model_validate_json(output_text)
    assert isinstance(parsed, SimpleResponse)
    assert parsed.message
    assert isinstance(parsed.success, bool)


@pytest.mark.asyncio
async def test_cloud_generator_stream_response():
    """Test CloudLLMGenerator streaming (currently yields complete response)."""
    generator = CloudLLMGenerator(model_name="gpt-4o-mini")

    chunks = []
    async for chunk in generator.stream_response(
        system_instructions="You are a helpful assistant.",
        input="Say hello!",
        model_settings=ModelSettings(seed=42, temperature=0.7),
        tools=[],
        output_schema=None,
        handoffs=[],
        tracing=ModelTracing.ENABLED,
        previous_response_id=None,
        prompt=None,
    ):
        chunks.append(chunk)

    # Current implementation yields complete response as single chunk
    assert len(chunks) == 1
    assert chunks[0].output


def test_cloud_generator_training_methods_noop():
    """Test that training methods are no-ops for CloudLLMGenerator."""
    generator = CloudLLMGenerator(model_name="gpt-4o-mini")

    # These should not raise errors, just be no-ops
    generator.store_generation_metadata({"test": "data"})
    result = generator.compute_loss([1.0, 2.0, 3.0])
    assert result is None

    generator.backpropagate(None)


def test_local_generator_instantiation():
    """Test LocalLLMGenerator can be instantiated."""
    generator = LocalLLMGenerator(model_path="meta-llama/Llama-3.1-8B", device="cpu")
    assert generator.model_path == "meta-llama/Llama-3.1-8B"
    assert generator.device == "cpu"
    assert isinstance(generator, LLMGenerator)


@pytest.mark.asyncio
async def test_local_generator_not_implemented():
    """Test LocalLLMGenerator raises NotImplementedError for inference."""
    generator = LocalLLMGenerator(model_path="meta-llama/Llama-3.1-8B")

    with pytest.raises(
        NotImplementedError, match="Local inference not yet implemented"
    ):
        await generator.get_response(
            system_instructions="Test",
            input="Test",
            model_settings=ModelSettings(seed=42),
            tools=[],
            output_schema=None,
            handoffs=[],
            tracing=ModelTracing.ENABLED,
            previous_response_id=None,
            prompt=None,
        )


def test_local_generator_stores_metadata():
    """Test LocalLLMGenerator can store generation metadata."""
    generator = LocalLLMGenerator(model_path="meta-llama/Llama-3.1-8B")

    generator.store_generation_metadata({"logits": [1, 2, 3], "tokens": [4, 5, 6]})
    assert len(generator.generation_metadata) == 1
    assert generator.generation_metadata[0]["logits"] == [1, 2, 3]


def test_local_generator_training_not_implemented():
    """Test LocalLLMGenerator training methods raise NotImplementedError."""
    generator = LocalLLMGenerator(model_path="meta-llama/Llama-3.1-8B")

    with pytest.raises(
        NotImplementedError, match="Loss computation not yet implemented"
    ):
        generator.compute_loss([1.0, 2.0])

    with pytest.raises(NotImplementedError, match="Backprop not yet implemented"):
        generator.backpropagate(None)


if __name__ == "__main__":
    # Run tests with: pytest tests/test_llm_generator.py -v
    pytest.main([__file__, "-v"])
