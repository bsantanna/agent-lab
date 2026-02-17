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
# scenario.configure(default_model="anthropic/claude-haiku-4-5")
scenario.configure(default_model="openai/gpt-5-nano")


@pytest.mark.agent_test
@pytest.mark.asyncio
@pytest.mark.skipif(
    condition=os.getenv("BUILD_WORKFLOW") == "True", reason="Skip Github CI."
)
async def test_audio_voice_memos_agent(client):
    class AudioVoiceMemosAgent(scenario.AgentAdapter):
        async def call(self, input: scenario.AgentInput) -> scenario.AgentReturnTypes:
            user_message = input.last_new_user_message_str()
            return audio_voice_memos_agent(client, user_message)

    result = await scenario.run(
        name="Simulation: analyse and answer questions about given audio document",
        description="Answer questions about given audio document.",
        agents=[
            AudioVoiceMemosAgent(),
            scenario.UserSimulatorAgent(),
            scenario.JudgeAgent(
                temperature=1.0,
                criteria=[
                    "Agent should not ask further questions.",
                    "Agent should answer user question about given audio document. ",
                    "Agent answer format is a detailed report with remarks of the audio and follow up actions."
                    "Audio document contains a first person voice memo about a meeting and a fictional character responsible for marketing team. "
                    "Audio document is recorded in portuguese. "
                    "The fictional character is concerned about delivery date of project, agent should mention this in report.",
                ],
            ),
        ],
        script=[
            scenario.user(
                "Can you describe the voice memo recording? Please identify stakeholders involved."
            ),
            scenario.agent(),
            scenario.judge(),
        ],
    )

    assert result.success


@scenario.cache()
def audio_voice_memos_agent(
    client, message_content, agent_type="fast_voice_memos"
) -> scenario.AgentReturnTypes:
    # create integration (audio transcription needs openai)
    response = client.post(
        url="/integrations/create",
        headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
        json={
            "api_endpoint": "https://api.openai.com/v1/",
            "api_key": os.environ["OPENAI_API_KEY"],
            "integration_type": "openai_api_v1",
        },
    )
    integration_id = response.json()["id"]

    # create llm
    response_2 = client.post(
        url="/llms/create",
        headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
        json={
            "integration_id": integration_id,
            "language_model_tag": "gpt-5-nano",
        },
    )
    language_model_id = response_2.json()["id"]

    # create agent
    response_3 = client.post(
        url="/agents/create",
        headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
        json={
            "language_model_id": language_model_id,
            "agent_type": agent_type,
            "agent_name": f"agent-{uuid4()}",
        },
    )
    agent_id = response_3.json()["id"]

    filename = "voice_memos_01_pt_BR.mp3"
    content_type = "audio/mp3"
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
