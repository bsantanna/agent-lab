import os

import pytest
from starlette.testclient import TestClient

from agent_lab.main import app
from tests.simulation.common.reference_agents import react_rag_agent
from tests.simulation.langwatch.runner import run_simulation


@pytest.fixture
def client():
    yield TestClient(app)


@pytest.mark.agent_test
@pytest.mark.skipif(
    condition=os.getenv("BUILD_WORKFLOW") == "True", reason="Skip Github CI."
)
def test_react_rag_agent(client, langwatch_configured):
    results = run_simulation(client, "react_rag", react_rag_agent)

    failed = [result for result in results if not result["passed"]]
    assert not failed, f"LLM judge rejected items: {failed}"
