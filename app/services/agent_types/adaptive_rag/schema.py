from typing import Literal

from pydantic import BaseModel, Field


class GradeDocuments(BaseModel):
    """Binary score for relevance check on retrieved documents."""

    binary_score: str = Field(
        description="Documents are relevant to the question, 'yes' or 'no'"
    )


class GradeHallucinations(BaseModel):
    """Binary score for hallucination present in generation answer."""

    binary_score: str = Field(
        description="Answer is grounded in the facts, 'yes' or 'no'"
    )


class RouteQuery(BaseModel):
    """Route user query matching the most relevant knowledge_base."""

    knowledge_base: Literal["??", "?"] = Field(
        ...,
        description="Given a user query choose a class matching most appropriate knowledge base.",
    )
