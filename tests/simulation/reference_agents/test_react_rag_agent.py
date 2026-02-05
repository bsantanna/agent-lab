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
# scenario.configure(default_model="anthropic/claude-sonnet-4-5")
scenario.configure(default_model="openai/o3")

@pytest.mark.agent_test
@pytest.mark.asyncio
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
            scenario.JudgeAgent(criteria=[
                "Agent should answer user question. ",
                "Documents containing excerpts of a book is available for agent as knowledge base, "
                "agent must use knowledge base to answer the question."
                "Answer must contain <thinking>...</thinking> with reasoning."
                "Answer must contain <response>...</response> with conclusions."
            ])
        ],
        script=[
            scenario.user(
                "What is the pinnacle of excellence?"
            ),
            scenario.agent(),
            scenario.judge(),
        ],
    )

    assert result.success



@scenario.cache()
def react_rag_agent(client, message_content) -> scenario.AgentReturnTypes:
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
            "language_model_tag": "grok-code-fast",
        },
    )
    language_model_id = response_2.json()["id"]

    # create agent
    response_3 = client.post(
        url="/agents/create",
        headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
        json={
            "language_model_id": language_model_id,
            "agent_type": "react_rag",
            "agent_name": f"agent-{uuid4()}",
        },
    )

    agent_id = response_3.json()["id"]

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
