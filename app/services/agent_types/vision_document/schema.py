from typing_extensions import TypedDict, Annotated, List


class ImageAnalysis(TypedDict):
    """Structured Image Analysis based on the image provided and user query."""

    description: Annotated[str, ..., "A detailed description about the image"]
    brands: Annotated[List[str], ..., "A list of identified brands"]
    products: Annotated[List[str], ..., "A list of identified products"]
    useful_information: Annotated[
        str, ..., "Useful information extracted from the image"
    ]
