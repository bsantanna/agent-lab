from typing_extensions import TypedDict, Annotated


class GradeAnswer(TypedDict):
    """Binary score to assess answer addresses question."""

    binary_score: Annotated[str, ..., "Answer addresses the question, 'yes' or 'no'"]


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
        str, ..., "Given a user query choose a most appropriate knowledge base."
    ]


class GenerateAnswer(TypedDict):
    """Generate a good answer to user query based on context and previous_messages."""

    generation: Annotated[str, ..., "A generated good answer to user query."]
