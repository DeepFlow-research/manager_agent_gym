"""Web search tools - two-layer architecture.

Layer 1: Core functions (_*) - pure business logic, testable, returns typed results
Layer 2: OpenAI tool wrappers - thin adapters for OpenAI SDK, handle JSON serialization
"""

import asyncio
import traceback
from typing import Any

from agents import function_tool, RunContextWrapper

from manager_agent_gym.core.agents.workflow_agents.tools.web_search_core import (
    search,
)
from manager_agent_gym.core.common.logging import logger
from manager_agent_gym.core.agents.workflow_agents.schemas.tools.web_search import (
    QuestionRequest,
    SearchResult,
    SearchDomain,
    TimeoutMessage,
)
from manager_agent_gym.core.workflow.context import AgentExecutionContext
from manager_agent_gym.core.agents.workflow_agents.schemas.telemetry import (
    AgentToolUseEvent,
)

SEARCH_TIMEOUT = 20
SEARCH_SEMAPHORE = asyncio.Semaphore(5)


# ============================================================================
# LAYER 1: WEB SEARCH OPERATIONS (Core Business Logic)
# ============================================================================


async def _perform_web_search(
    query: str,
    return_results_from: str | None = None,
    domain: str | None = None,
    num_results: int = 5,
) -> dict[str, Any]:
    """Perform a web search and return results."""
    try:
        # Provide defaults and convert types
        date_filter = return_results_from or "2025-01-01T00:00:00.000Z"

        # Convert string domain to SearchDomain enum, default to company
        search_domain: SearchDomain
        if domain:
            try:
                search_domain = SearchDomain(domain)
            except ValueError:
                search_domain = SearchDomain.company
        else:
            search_domain = SearchDomain.company

        async with SEARCH_SEMAPHORE:
            search_results: SearchResult = await search(
                query=query,
                num_results=num_results,
                return_results_from=date_filter,
                domain=search_domain,
            )

            return {
                "success": True,
                "result": search_results,
            }

    except Exception as e:
        logger.error(f"Web search failed: {traceback.format_exc()}")
        return {"success": False, "error": str(e)}


# ============================================================================
# LAYER 2: OPENAI TOOL WRAPPERS
# ============================================================================


@function_tool
async def get_search_context(
    wrapper: RunContextWrapper,
    question: QuestionRequest,
) -> SearchResult | TimeoutMessage:
    """
    Perform a real-time web search to answer a user's question with up-to-date information and citations.

    This asynchronous function takes a user's search question, queries the web for recent and relevant results,
    synthesizes the findings, and returns a structured answer that includes inline citations to the sources.

    Note: Before calling this tool, make sure you tell the user you are going to do a web search.
    Parameters:
        question (QuestionRequest):
            The search request containing:
                - query (str): The user's search query.
                - return_results_from (str): ISO 8601 date string specifying the earliest date for search results.
                - domain (SearchDomain): The content domain to restrict the search (e.g., news, academic, general).

    Returns:
        SearchResult:
            An object containing a comprehensive answer to the query, with inline citations referencing the sources used.

    Usage:
        Call this tool when you need context from the web to complete a user task.
    """

    try:
        result_dict = await asyncio.wait_for(
            _perform_web_search(
                query=question.query,
                return_results_from=question.return_results_from,
                domain=question.domain,
                num_results=5,
            ),
            timeout=SEARCH_TIMEOUT,
        )

        if not result_dict["success"]:
            raise Exception(result_dict["error"])

        result = result_dict["result"]

        # Telemetry
        ctx_exc: AgentExecutionContext = wrapper.context  # type: ignore[attr-defined]
        ctx_exc.record_tool_event(
            AgentToolUseEvent(
                agent_id=ctx_exc.agent_id,
                task_id=ctx_exc.current_task_id,
                tool_name="web_search.get_search_context",
                succeeded=True,
            )
        )
        return result

    except TimeoutError:
        # Telemetry
        try:
            ctx_timeout: AgentExecutionContext = wrapper.context  # type: ignore[attr-defined]
            ctx_timeout.record_tool_event(
                AgentToolUseEvent(
                    agent_id=ctx_timeout.agent_id,
                    task_id=ctx_timeout.current_task_id,
                    tool_name="web_search.get_search_context",
                    succeeded=False,
                    error_type="TimeoutError",
                    error_message="search timeout",
                )
            )
        except Exception:
            pass
        return TimeoutMessage()
    except Exception:
        logger.error(f"Search context failed: {traceback.format_exc()}")
        # Telemetry
        try:
            ctx_err: AgentExecutionContext = wrapper.context  # type: ignore[attr-defined]
            ctx_err.record_tool_event(
                AgentToolUseEvent(
                    agent_id=ctx_err.agent_id,
                    task_id=ctx_err.current_task_id,
                    tool_name="web_search.get_search_context",
                    succeeded=False,
                    error_type="Exception",
                    error_message="search failure",
                )
            )
        except Exception:
            pass
        raise
