from typing_extensions import TypedDict, Annotated


class ImageAnalysis(TypedDict):
    """Structured Image Analysis based on the image provided and user query."""

    short_description: Annotated[
        str, ..., "A short description with image key features"
    ]
    detailed_analysis: Annotated[
        str, ..., "Your best effort to solve user intent delimited by <query></query> "
    ]
    lessons_learned: Annotated[
        str, ..., "What you learned from this image that improved your understanding"
    ]
    detected_languages: Annotated[
        str, ..., "Detected languages in image using ISO 639-3"
    ]
    business_value: Annotated[
        str,
        ...,
        "Detected business value according to context delimited by <context></context>",
    ]
    number_of_words: Annotated[str, ..., "Detected number of words"]
    document_format: Annotated[
        str,
        ...,
        "Detected document format between text/word, presentation, sheet, photo, etc.",
    ]
