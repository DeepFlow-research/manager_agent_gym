from typing import Literal

from pydantic import BaseModel, Field

from manager_agent_gym.core.agents.workflow_agents.schemas.tools.web_search.question_request import (
    SearchDomain,
)


class SearchItem(BaseModel):
    published_date: str = Field(
        ...,
        description="The date of the search, in ISO 8601 format, e.g. 2025-02-08T09:55:17.235Z",
    )
    author: str
    domain: SearchDomain
    content_summary: str
    truncated_contents: str


class SearchResult(BaseModel):
    type: Literal["search_result"] = Field(
        default="search_result", description="Type discriminator for this schema"
    )
    original_query: str
    results: list[SearchItem]


class TimeoutMessage(BaseModel):
    type: Literal["timeout_message"] = Field(
        default="timeout_message", description="Type discriminator for this schema"
    )
    contents: str = "I'm sorry, the web search took too long and timed out. Please try again later or refine your query."
