import pytest
from pydantic import BaseModel
from unittest.mock import AsyncMock, Mock
from typing import Any


class _DummyMessage:
    def __init__(
        self,
        *,
        content: str | None = None,
        refusal: str | None = None,
        parsed: Any = None,
    ) -> None:
        self.content = content
        self.refusal = refusal
        self.parsed = parsed


class _DummyChoice:
    def __init__(
        self, *, message: _DummyMessage, finish_reason: str | None = None
    ) -> None:
        self.message = message
        self.finish_reason = finish_reason


class _DummyResponse:
    def __init__(self, *, _id: str, choices: list[_DummyChoice]) -> None:
        self.id = _id
        self.choices = choices


class _MockAsyncOpenAI:
    def __init__(self) -> None:
        self.beta = Mock()
        self.beta.chat = Mock()
        self.beta.chat.completions = Mock()
        self.beta.chat.completions.parse = AsyncMock()


class _ToyModel(BaseModel):
    foo: str


@pytest.mark.asyncio
async def test_generate_structured_response_happy_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Create toy model instance for parsed response
    toy_instance = _ToyModel(foo="bar")

    # Set up mock OpenAI client
    mock_client = _MockAsyncOpenAI()
    msg = _DummyMessage(parsed=toy_instance)
    choice = _DummyChoice(message=msg, finish_reason="stop")
    mock_response = _DummyResponse(_id="resp_ok", choices=[choice])
    mock_client.beta.chat.completions.parse.return_value = mock_response

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
async def test_generate_structured_response_refusal_attr(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    refusal_text = "Content policy refusal"

    # Set up mock OpenAI client with refusal
    mock_client = _MockAsyncOpenAI()
    msg = _DummyMessage(refusal=refusal_text, parsed=None)
    choice = _DummyChoice(message=msg, finish_reason="content_filter")
    mock_response = _DummyResponse(_id="resp_refuse_attr", choices=[choice])
    mock_client.beta.chat.completions.parse.return_value = mock_response

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
    # Ensure rich context is populated
    assert err.refusal_text == refusal_text
    assert (
        err.model == "gpt-4o"
    )  # no longer transformed since we validate OpenAI models directly
    assert err.response_id == "resp_refuse_attr"
    assert err.finish_reason == "content_filter"


@pytest.mark.asyncio
async def test_generate_structured_response_no_parsed_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Set up mock OpenAI client with no parsed content (parsing failed)
    mock_client = _MockAsyncOpenAI()
    msg = _DummyMessage(refusal=None, parsed=None)
    choice = _DummyChoice(message=msg, finish_reason="stop")
    mock_response = _DummyResponse(_id="resp_no_parse", choices=[choice])
    mock_client.beta.chat.completions.parse.return_value = mock_response

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
    assert err.response_id == "resp_no_parse"
