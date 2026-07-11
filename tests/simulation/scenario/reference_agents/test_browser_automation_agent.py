import os

import scenario
import pytest
from starlette.testclient import TestClient

from app.main import app
from tests.simulation.common.config import (
    judge_agent_kwargs,
    simulation_model_config,
)
from tests.simulation.common.reference_agents import web_browser_agent


@pytest.fixture
def client():
    yield TestClient(app)


# Configure the default model for simulation
scenario.configure(default_model=simulation_model_config())


@pytest.mark.agent_test
@pytest.mark.asyncio
@pytest.mark.skipif(
    condition=os.getenv("BUILD_WORKFLOW") == "True", reason="Skip Github CI."
)
async def test_browser_automation_agent(client):
    class BrowserAgent(scenario.AgentAdapter):
        async def call(self, input: scenario.AgentInput) -> scenario.AgentReturnTypes:
            user_message = input.last_new_user_message_str()
            return web_browser_agent(client, user_message)

    result = await scenario.run(
        name="Simulation: web browser automation",
        description="Summarize a wikipedia article using web browser.",
        agents=[
            BrowserAgent(),
            scenario.UserSimulatorAgent(),
            scenario.JudgeAgent(
                **judge_agent_kwargs(),
                temperature=1.0,
                criteria=[
                    "Agent should not ask follow-up questions. ",
                    "Agent should match the given acceptance criteria in the query.",
                ],
            ),
        ],
        script=[
            scenario.user(
                "Using the web browser, explain the first paragraph of "
                "https://en.wikipedia.org/wiki/Mathematical_finance. "
                "Acceptance criteria: a 12 year old would understand."
            ),
            scenario.agent(),
            scenario.judge(),
        ],
    )

    assert result.success
