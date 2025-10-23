from pydantic import BaseModel, Field


class EvaluatedScore(BaseModel):
    reasoning: str = Field(..., description="Reasoning for the evaluated score")
    score: float = Field(..., description="Evaluated score")
