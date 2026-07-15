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


class GenerateAnswer(TypedDict):
    """Generate a good answer to user query based on context and previous_messages."""

    connection: Annotated[
        str,
        ...,
        "A brief and solid argument connecting user query and generated answer.",
    ]
    generation: Annotated[str, ..., "A generated good answer to user query."]
