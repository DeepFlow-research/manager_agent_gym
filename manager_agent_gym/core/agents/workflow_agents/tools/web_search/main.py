import asyncio
import traceback
from uuid import uuid4

from agents import function_tool, RunContextWrapper

from manager_agent_gym.core.agents.workflow_agents.tools.web_search.search import search
from manager_agent_gym.core.common.logging import logger
from manager_agent_gym.core.agents.workflow_agents.schemas.tools.web_search import (
    QuestionRequest,
    QuestionRequestWithId,
    SearchResult,
    TimeoutMessage,
)
from manager_agent_gym.core.workflow.context import AgentExecutionContext
from manager_agent_gym.core.agents.workflow_agents.schemas.telemetry import AgentToolUseEvent

SEARCH_TIMEOUT = 20
SEARCH_SEMAPHORE = asyncio.Semaphore(5)


async def _answer_single_question(
    question: QuestionRequestWithId,
) -> SearchResult:
    """
    Answer a single web search question using up-to-date search results.

    This tool performs a web search for the given question, synthesizes the results,
    and returns a comprehensive answer with citations.

    Args:
        question (QuestionRequestWithId): The question to answer, including:
            - query (str): The search query string.
            - return_results_from (str): The date (ISO 8601 format) from which to return results, e.g. "2025-02-08T00:00:00.000Z".
            - domain (SearchDomain): The general domain of contents to source the answer from.
            - question_id (str): A unique identifier for the question.

    Returns:
        Answer: A comprehensive answer to the query, with inline citations referencing the sources of the information.

    Example:
        Use this tool when you need to answer a single question using recent web search results,
        and require a detailed answer with sources.

    """
    # Our key has a ratelimit of 5 concurrent requests, so we ratelimit
    async with SEARCH_SEMAPHORE:
        try:
            search_results: SearchResult = await search(
                query=question.query,
                num_results=5,
                return_results_from=question.return_results_from,
                domain=question.domain,
            )
        except Exception as e:
            logger.error(f"Web search failed: {traceback.format_exc()}")
            raise e

        return search_results


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
        result = await asyncio.wait_for(
            _answer_single_question(
                QuestionRequestWithId(
                    query=question.query,
                    return_results_from=question.return_results_from,
                    domain=question.domain,
                    question_id=uuid4().hex,
                )
            ),
            timeout=SEARCH_TIMEOUT,
        )
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
