import os

import pytest
from starlette.testclient import TestClient

from app.main import app
from tests.simulation.common.reference_agents import supervised_agent
from tests.simulation.langfuse.runner import run_simulation


@pytest.fixture
def client():
    yield TestClient(app)


@pytest.mark.agent_test
@pytest.mark.skipif(
    condition=os.getenv("BUILD_WORKFLOW") == "True", reason="Skip Github CI."
)
def test_supervisor_agent(client, langfuse_client):
    results = run_simulation(langfuse_client, client, "supervisor", supervised_agent)

    failed = [result for result in results if not result["passed"]]
    assert not failed, f"LLM judge rejected items: {failed}"
