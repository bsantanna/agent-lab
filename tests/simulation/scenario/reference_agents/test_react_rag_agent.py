import os

import scenario
import pytest
from starlette.testclient import TestClient

from app.main import app
from tests.simulation.common.config import (
    judge_agent_kwargs,
    simulation_model_config,
)
from tests.simulation.common.reference_agents import react_rag_agent


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
async def test_react_rag_agent(client):
    class ReactRagAgent(scenario.AgentAdapter):
        async def call(self, input: scenario.AgentInput) -> scenario.AgentReturnTypes:
            user_message = input.last_new_user_message_str()
            return react_rag_agent(client, user_message)

    result = await scenario.run(
        name="Simulation: react rag question / answer reasoning agent",
        description="Answer user question using react rag pattern, with <thinking> and <response> sections.",
        agents=[
            ReactRagAgent(),
            scenario.UserSimulatorAgent(),
            scenario.JudgeAgent(
                **judge_agent_kwargs(),
                temperature=1.0,
                criteria=[
                    "Agent should answer user question. ",
                    "Agent must use knowledge base to answer the question. "
                    "Generated response must contain <thinking> and <response> sections. ",
                ],
            ),
        ],
        script=[
            scenario.user("What is the pinnacle of excellence?"),
            scenario.agent(),
            scenario.judge(),
        ],
    )

    assert result.success
