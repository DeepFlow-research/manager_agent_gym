import pytest
from pydantic import BaseModel
from unittest.mock import AsyncMock, Mock
from typing import Any
import os


class _MockAsyncOpenAI:
    def __init__(self) -> None:
        self.chat = Mock()
        self.chat.completions = Mock()
        self.chat.completions.create = AsyncMock()


class _ToyModel(BaseModel):
    foo: str


@pytest.mark.asyncio
async def test_generate_structured_response_happy_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Create toy model instance for structured response
    toy_instance = _ToyModel(foo="bar")

    # Set up mock OpenAI client (Instructor-patched style)
    mock_client = _MockAsyncOpenAI()
    mock_client.chat.completions.create.return_value = toy_instance

    # Import and patch the interface
    import importlib

    llm_iface = importlib.import_module("manager_agent_gym.core.common.llm_interface")

    # Patch the _get_openai_client function to return our mock
    monkeypatch.setattr(llm_iface, "_get_openai_client", lambda: mock_client)

    result = await llm_iface.generate_structured_response(
        system_prompt="sys",
        user_prompt="user",
        response_type=_ToyModel,
        seed=123,
        model="gpt-4o",
        temperature=0,
    )

    assert isinstance(result, _ToyModel)
    assert result.foo == "bar"


@pytest.mark.asyncio
async def test_generate_structured_response_error_wrapping(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Set up mock OpenAI client that raises during structured creation
    mock_client = _MockAsyncOpenAI()
    mock_client.chat.completions.create.side_effect = RuntimeError(
        "Content policy refusal"
    )

    # Import and patch the interface
    import importlib

    llm_iface = importlib.import_module("manager_agent_gym.core.common.llm_interface")

    # Patch the _get_openai_client function to return our mock
    monkeypatch.setattr(llm_iface, "_get_openai_client", lambda: mock_client)

    with pytest.raises(llm_iface.LLMInferenceTruncationError) as exc_info:
        await llm_iface.generate_structured_response(
            system_prompt="sys",
            user_prompt="user",
            response_type=_ToyModel,
            seed=456,
            model="gpt-4o",
            temperature=0,
        )

    err = exc_info.value
    # Ensure context is populated minimally under Instructor path
    assert err.refusal_text is None
    assert err.response_id is None
    assert err.model == "gpt-4o"
    assert err.provider_fields.get("original_error") == "Content policy refusal"


@pytest.mark.asyncio
async def test_generate_structured_response_exception_propagates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Set up mock OpenAI client that raises a generic error (e.g., no parsed content)
    mock_client = _MockAsyncOpenAI()
    mock_client.chat.completions.create.side_effect = ValueError("resp_no_parse")

    # Import and patch the interface
    import importlib

    llm_iface = importlib.import_module("manager_agent_gym.core.common.llm_interface")

    # Patch the _get_openai_client function to return our mock
    monkeypatch.setattr(llm_iface, "_get_openai_client", lambda: mock_client)

    with pytest.raises(llm_iface.LLMInferenceTruncationError) as exc_info:
        await llm_iface.generate_structured_response(
            system_prompt="sys",
            user_prompt="user",
            response_type=_ToyModel,
            seed=789,
            model="gpt-4o",
            temperature=0,
        )

    err = exc_info.value
    assert err.refusal_text is None
    assert err.model == "gpt-4o"
    assert err.response_id is None
    assert err.provider_fields.get("original_error") == "resp_no_parse"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "model_name",
    [
        "gpt-5",  # OpenAI latest
        "gpt-4.1",  # OpenAI 4.x
        "claude-3-7-sonnet",  # Anthropic (provider-specific, but mocked)
    ],
)
async def test_generate_structured_response_across_providers(
    monkeypatch: pytest.MonkeyPatch, model_name: str
) -> None:
    # Create toy model instance for structured response
    toy_instance = _ToyModel(foo=f"ok:{model_name}")

    # Set up mock OpenAI client (Instructor-patched style)
    mock_client = _MockAsyncOpenAI()

    async def _fake_create(**kwargs: Any) -> _ToyModel:
        # Ensure our code passes through the requested model and response schema
        assert kwargs.get("model") == model_name
        assert kwargs.get("response_model") is _ToyModel
        # messages must exist and be a list
        assert isinstance(kwargs.get("messages"), list)
        return toy_instance

    mock_client.chat.completions.create.side_effect = _fake_create

    # Import and patch the interface
    import importlib

    llm_iface = importlib.import_module("manager_agent_gym.core.common.llm_interface")

    # Patch the _get_openai_client function to return our mock
    monkeypatch.setattr(llm_iface, "_get_openai_client", lambda: mock_client)

    result = await llm_iface.generate_structured_response(
        system_prompt="sys",
        user_prompt="user",
        response_type=_ToyModel,
        seed=42,
        model=model_name,
        temperature=0,
    )

    assert isinstance(result, _ToyModel)
    assert result.foo == f"ok:{model_name}"


@pytest.mark.asyncio
@pytest.mark.live_llm
@pytest.mark.parametrize("model_name", ["gpt-5", "gpt-4.1"])  # OpenAI live
async def test_live_openai_models_return_pydantic(
    model_name: str,
) -> None:
    from manager_agent_gym.core.common.llm_interface import generate_structured_response

    class _LiveModel(BaseModel):
        foo: str

    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    # Some models (e.g., gpt-5) only support temperature=1
    temp = 1 if model_name.startswith("gpt-5") else 0
    result = await generate_structured_response(
        system_prompt="Return JSON with field foo set to 'live'",
        user_prompt=None,
        response_type=_LiveModel,
        seed=1,
        model=model_name,
        temperature=temp,
        max_retries=2,
    )
    assert isinstance(result, _LiveModel)
    assert isinstance(result.foo, str)
    assert len(result.foo) > 0


@pytest.mark.asyncio
@pytest.mark.live_llm
async def test_live_anthropic_returns_pydantic() -> None:
    """Use Instructor provider wrapper for Anthropic live call when available."""
    try:
        import instructor  # type: ignore
    except Exception:
        pytest.skip("instructor package not available for Anthropic provider")
    from pydantic import BaseModel

    if not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set")

    class _AnthModel(BaseModel):
        foo: str

    # Build provider client per Instructor docs using chat.completions API
    # Note: We avoid touching our OpenAI async client path here to keep the provider test isolated.
    # If anthropic package is missing, gracefully skip
    try:
        # Allow overriding model via env to match account availability
        anthropic_model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet")
        client = instructor.from_provider(f"anthropic/{anthropic_model}")
    except Exception as e:
        if "anthropic package is required" in str(e).lower():
            pytest.skip("anthropic package not installed")
        raise
    try:
        user = client.chat.completions.create(
            response_model=_AnthModel,
            messages=[
                {
                    "role": "user",
                    "content": "Reply strictly with a JSON object matching schema {foo: string}, set foo='live'",
                }
            ],
            max_retries=2,
        )
    except Exception as e:
        # Gracefully skip when model is unavailable in the account/region
        if "not_found_error" in str(e).lower() or "model:" in str(e).lower():
            pytest.skip(f"Anthropic model not available: {e}")
        raise
    assert isinstance(user, _AnthModel)
    assert isinstance(user.foo, str)
    assert len(user.foo) > 0
