import os

import pytest


@pytest.fixture
def langwatch_configured():
    if not (os.getenv("LANGWATCH_ENDPOINT") and os.getenv("LANGWATCH_API_KEY")):
        pytest.skip("LangWatch credentials are not configured.")
