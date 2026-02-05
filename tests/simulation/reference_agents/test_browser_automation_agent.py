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
# scenario.configure(default_model="anthropic/claude-sonnet-4-5") # Required for improved evaluation of output.
scenario.configure(default_model="openai/gpt-5-nano")

@pytest.mark.agent_test
@pytest.mark.asyncio
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
            scenario.JudgeAgent(temperature=1.0, criteria=[
                "Agent should not ask follow-up questions",
                "Agent should generate a report",
                "Report should match the given criteria in the query."
            ])
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

@scenario.cache()
def web_browser_agent(client, message_content) -> scenario.AgentReturnTypes:
    # create integration
    response = client.post(
        url="/integrations/create",
        headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
        json={
            "api_endpoint": "https://api.anthropic.com",
            "api_key": os.environ["ANTHROPIC_API_KEY"],
            "integration_type": "anthropic_api_v1",
        },
    )
    integration_id = response.json()["id"]

    # create llm
    response_2 = client.post(
        url="/llms/create",
        headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
        json={
            "integration_id": integration_id,
            "language_model_tag": "claude-sonnet-4-5",
        },
    )
    language_model_id = response_2.json()["id"]

    # create agent
    response_3 = client.post(
        url="/agents/create",
        headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
        json={
            "language_model_id": language_model_id,
            "agent_type": "coordinator_planner_supervisor",
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
