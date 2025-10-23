"""
Tests for web search tools.

Tests the two-layer architecture:
- Layer 1: Core _* functions with real web search operations
- Layer 2: OpenAI tool wrappers (integration tested via tool_factory)

Note: These tests require EXA_API_KEY and COHERE_API_KEY environment variables.
"""

import pytest

from manager_agent_gym.core.agents.workflow_agents.tools.web_search import (
    _perform_web_search,
)


# ============================================================================
# WEB SEARCH TESTS
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.requires_exa
@pytest.mark.requires_cohere
async def test_perform_web_search_basic(exa_api_key: str, cohere_api_key: str) -> None:
    """Test basic web search."""
    result = await _perform_web_search(
        query="Python programming language", num_results=3
    )

    assert result["success"] is True
    assert "result" in result


@pytest.mark.asyncio
@pytest.mark.requires_exa
@pytest.mark.requires_cohere
async def test_perform_web_search_with_date_filter(
    exa_api_key: str, cohere_api_key: str
) -> None:
    """Test web search with date filtering."""
    result = await _perform_web_search(
        query="latest AI developments",
        return_results_from="2024-01-01T00:00:00.000Z",
        num_results=3,
    )

    assert result["success"] is True
    assert "result" in result


@pytest.mark.asyncio
@pytest.mark.requires_exa
@pytest.mark.requires_cohere
async def test_perform_web_search_with_domain(
    exa_api_key: str, cohere_api_key: str
) -> None:
    """Test web search with domain filtering."""
    result = await _perform_web_search(
        query="machine learning research",
        domain="academic",
        num_results=3,
    )

    assert result["success"] is True
    assert "result" in result


@pytest.mark.asyncio
@pytest.mark.requires_exa
@pytest.mark.requires_cohere
async def test_perform_web_search_empty_query(
    exa_api_key: str, cohere_api_key: str
) -> None:
    """Test web search with empty query."""
    result = await _perform_web_search(query="", num_results=3)

    # Should either fail or return minimal results
    assert "success" in result


@pytest.mark.asyncio
@pytest.mark.requires_exa
@pytest.mark.requires_cohere
async def test_perform_web_search_many_results(
    exa_api_key: str, cohere_api_key: str
) -> None:
    """Test web search with many results."""
    result = await _perform_web_search(query="Python web frameworks", num_results=10)

    assert result["success"] is True
    assert "result" in result


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_perform_web_search_without_api_keys() -> None:
    """Test web search fails gracefully without API keys."""
    # This test should fail if API keys are not configured
    # but shouldn't crash - it should return an error
    result = await _perform_web_search(query="test", num_results=1)

    # Should have success key regardless of outcome
    assert "success" in result
