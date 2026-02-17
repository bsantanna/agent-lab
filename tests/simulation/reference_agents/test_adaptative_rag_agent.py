import os
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


@scenario.cache()
def adaptive_rag_agent(client, message_content) -> scenario.AgentReturnTypes:
    # create integration
    response = client.post(
        headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
        url="/integrations/create",
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
            "language_model_tag": "grok-code-fast",
        },
    )
    language_model_id = response_2.json()["id"]

    # create agent
    response_3 = client.post(
        headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
        url="/agents/create",
        json={
            "language_model_id": language_model_id,
            "agent_type": "adaptive_rag",
            "agent_name": f"agent-{uuid4()}",
        },
    )
    agent_id = response_3.json()["id"]

    # update collection_name to match pgvector dump
    client.post(
        url="/agents/update_setting",
        headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
        json={
            "agent_id": agent_id,
            "setting_key": "collection_name",
            "setting_value": "static_document_data_ollama_embeddings",
        },
    )

    # post message
    response_4 = client.post(
        "/messages/post",
        headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
        json={
            "message_role": "human",
            "message_content": message_content,
            "agent_id": agent_id,
        },
    )

    return response_4.json()["message_content"]
