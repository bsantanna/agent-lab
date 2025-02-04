from typing import Literal, TypedDict, Annotated


class GradeDocuments(TypedDict):
    """Binary score for relevance check on retrieved documents."""

    binary_score: Annotated[
        str, ..., "Documents are relevant to the question, 'yes' or 'no'"
    ]


class GradeHallucinations(TypedDict):
    """Binary score for hallucination present in generation answer."""

    binary_score: Annotated[str, ..., "Answer is grounded in the facts, 'yes' or 'no'"]


class RouteQuery(TypedDict):
    """Route user query matching the most relevant knowledge_base."""

    knowledge_base: Annotated[
        Literal["static_data", "structured_data", "temporal_data", "api_data"],
        ...,
        "Given a user query choose a class matching most appropriate knowledge base.",
    ]
