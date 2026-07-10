import os

import pytest
from langfuse import Langfuse


@pytest.fixture
def langfuse_client():
    if not (
        (os.getenv("LANGFUSE_BASE_URL") or os.getenv("LANGFUSE_HOST"))
        and os.getenv("LANGFUSE_PUBLIC_KEY")
        and os.getenv("LANGFUSE_SECRET_KEY")
    ):
        pytest.skip("Langfuse credentials are not configured.")
    client = Langfuse()
    yield client
    client.flush()
