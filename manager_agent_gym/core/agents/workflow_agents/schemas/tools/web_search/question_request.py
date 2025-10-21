from enum import StrEnum, auto

from pydantic import BaseModel, Field


class SearchDomain(StrEnum):
    company = auto()
    research_paper = auto()
    news = auto()
    pdf = auto()
    github = auto()
    tweet = auto()
    personal_site = auto()
    linkedin_profile = auto()
    financial_report = auto()


class QuestionRequest(BaseModel):
    query: str = Field(..., description="Query to use to search the open web")
    return_results_from: str = Field(
        ...,
        description="the date from which to return results from, in ISO 8601 format, e.g. 2025-02-08T00:00:00.000Z",
    )
    domain: SearchDomain = Field(
        ..., description="The general domain of contents to source the answer from"
    )


class QuestionRequestWithId(QuestionRequest):
    question_id: str
