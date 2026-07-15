import os

import scenario
import pytest
from starlette.testclient import TestClient

from agent_lab.main import app
from tests.simulation.common.config import (
    judge_agent_kwargs,
    simulation_model_config,
)
from tests.simulation.common.reference_agents import adaptive_rag_agent


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
async def test_adaptive_rag_agent(client):
    class AdaptiveRagAgent(scenario.AgentAdapter):
        async def call(self, input: scenario.AgentInput) -> scenario.AgentReturnTypes:
            user_message = input.last_new_user_message_str()
            return adaptive_rag_agent(client, user_message)

    result = await scenario.run(
        name="Simulation: adaptive rag question / answer",
        description="Answer user question using adaptive rag pattern.",
        agents=[
            AdaptiveRagAgent(),
            scenario.UserSimulatorAgent(),
            scenario.JudgeAgent(
                **judge_agent_kwargs(),
                temperature=1.0,
                criteria=[
                    "Agent should answer user question",
                    "Answer should meet given criteria in the query",
                ],
            ),
        ],
        script=[
            scenario.user(
                "You have access to this book 'The Art of War - Sun Tzu' "
                "available at static_document_data, "
                "I want to ask you to summarize in one sentence "
                "what is the pinnacle of excellence."
            ),
            scenario.agent(),
            scenario.judge(),
        ],
    )

    assert result.success
