import os
from pathlib import Path
from uuid import uuid4

import scenario
import pytest
from starlette.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    yield TestClient(app)


# Configure the default model for simulation
scenario.configure(default_model="anthropic/claude-sonnet-4-5") # Rate limit error with claude-haiku-4-5


@pytest.mark.agent_test
@pytest.mark.asyncio
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
            scenario.JudgeAgent(criteria=[
                "Agent should answer user question about given image document. ",
                "Image document contains a fisherman sit on a bench adjusting his net. "
                "There is a philosophical quote in the image evoking preparation and readiness, agent must describe this."
            ])
        ],
        script=[
            scenario.user(
                "Can you describe the following image in details?"
            ),
            scenario.agent(),
            scenario.judge(),
        ],
    )

    assert result.success


@scenario.cache()
def image_vision_document_agent(client, message_content) -> scenario.AgentReturnTypes:
    # create integration
    response = client.post(
        url="/integrations/create",
        headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
        json={
            "api_endpoint": "https://api.x.ai/v1/",
            "api_key": os.environ["XAI_API_KEY"],
            "integration_type": "xai_api_v1",
        },
    )
    integration_id = response.json()["id"]

    # create llm
    response_2 = client.post(
        url="/llms/create",
        headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
        json={
            "integration_id": integration_id,
            "language_model_tag": "grok-4-1-fast-non-reasoning",
        },
    )
    language_model_id = response_2.json()["id"]

    # create agent
    response_3 = client.post(
        url="/agents/create",
        headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
        json={
            "language_model_id": language_model_id,
            "agent_type": "vision_document",
            "agent_name": f"agent-{uuid4()}",
        },
    )
    agent_id = response_3.json()["id"]
    filename = "vision_document_01.jpg"
    content_type = "image/jpeg"
    tests_dir = Path(__file__).parent.parent.parent
    file_path = f"{tests_dir}/integration/{filename}"

    # create attachment
    response_4 = None
    with open(file_path, "rb") as file:
        response_4 = client.post(
            url="/attachments/upload",
            headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
            files={"file": (filename, file, content_type)},
        )
    attachment_id = response_4.json()["id"]

    # post message
    response_5 = client.post(
        "/messages/post",
        headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
        json={
            "message_role": "human",
            "message_content": message_content,
            "agent_id": agent_id,
            "attachment_id": attachment_id,
        },
    )

    return response_5.json()["message_content"]
