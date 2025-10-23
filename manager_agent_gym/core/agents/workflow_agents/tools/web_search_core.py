import asyncio
import functools
from typing import Literal

import cohere

from manager_agent_gym.core.clients import EXA_CLIENT
from manager_agent_gym.core.agents.workflow_agents.schemas.tools.web_search import (
    SearchDomain,
    SearchItem,
    SearchResult,
)
from manager_agent_gym.config import settings


async def search(
    query: str,
    domain: SearchDomain,
    num_results: int = 5,
    maximum_length_search_result: int = 25000,
    return_results_from: str = "2025-01-01T00:00:00.000Z",
    rerank_model: Literal["rerank-v3.5", "rerank-v3.0"] | None = "rerank-v3.5",
) -> SearchResult:
    """
    Search the web to get a series of ranked search results based on relevance to the query.

    Args:
        query: The query the agent needs open-web context to be able to answer effectively.
        return_results_from: The date to start searching from.
        domain: The domain to search.
        maximum_length_search_result: The maximum length of the search result.
        rerank_model: The rerank model to use.
    """
    loop = asyncio.get_event_loop()
    fut = loop.run_in_executor(
        None,
        functools.partial(
            _search,
            query=query,
            domain=domain,
            maximum_length_search_result=maximum_length_search_result,
            return_results_from=return_results_from,
        ),
    )
    items: list[SearchItem] = await fut
    if rerank_model:
        # Create a new Cohere client for each request to avoid event loop issues
        # This ensures the client uses the current event loop and properly cleans up
        async with cohere.AsyncClientV2(
            api_key=settings.COHERE_API_KEY
        ) as cohere_client:
            reranked_indices = await cohere_client.rerank(
                model=rerank_model,
                query=query,
                documents=[item.truncated_contents for item in items],
                top_n=num_results,
            )
            # Explicitly cast to avoid type checker issue with list comprehension
            items = [items[result.index] for result in reranked_indices.results]  # type: ignore[assignment]

    return SearchResult(results=items, original_query=query)


def _search(
    query: str,
    domain: SearchDomain,
    maximum_length_search_result: int = 2048,
    num_results_to_return: int = 5,
    return_results_from: str = "2025-01-01T00:00:00.000Z",
) -> list[SearchItem]:
    results = EXA_CLIENT.search_and_contents(
        query,
        type="auto",
        text=True,
        start_published_date=return_results_from,
        category=domain.value,
        num_results=num_results_to_return,
        summary=True,
    ).results

    return [
        SearchItem(
            truncated_contents=" ".join(
                result.text.split()[:maximum_length_search_result]
            ),
            author=result.author if result.author else "unknown",
            domain=domain,
            content_summary=result.summary,
            published_date=result.published_date
            if result.published_date
            else "unknown",
        )
        for result in results
    ]
