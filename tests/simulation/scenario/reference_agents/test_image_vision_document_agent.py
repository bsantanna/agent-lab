import os

import scenario
import pytest
from starlette.testclient import TestClient

from app.main import app
from tests.simulation.common.config import judge_model_config
from tests.simulation.common.reference_agents import image_vision_document_agent


@pytest.fixture
def client():
    yield TestClient(app)


# Configure the default model for simulation
scenario.configure(default_model=judge_model_config())


@pytest.mark.agent_test
@pytest.mark.asyncio
@pytest.mark.skipif(
    condition=os.getenv("BUILD_WORKFLOW") == "True", reason="Skip Github CI."
)
async def test_image_vision_document_agent(client):
    class ImageVisionDocumentAgent(scenario.AgentAdapter):
        async def call(self, input: scenario.AgentInput) -> scenario.AgentReturnTypes:
            user_message = input.last_new_user_message_str()
            return image_vision_document_agent(client, user_message)

    result = await scenario.run(
        name="Simulation: analyse and answer questions about given image document",
        description="Answer questions about given image document.",
        agents=[
            ImageVisionDocumentAgent(),
            scenario.UserSimulatorAgent(),
            scenario.JudgeAgent(
                temperature=1.0,
                criteria=[
                    "Agent should answer user question about given image document. ",
                    "Image document contains a fisherman sit and adjusting his net. "
                    "There is a philosophical quote in the image evoking preparation and readiness, agent must describe this.",
                ],
            ),
        ],
        script=[
            scenario.user("Can you describe the following image in details?"),
            scenario.agent(),
            scenario.judge(),
        ],
    )

    assert result.success
