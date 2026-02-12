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
# @pytest.mark.skipif(
#     condition=os.getenv("BUILD_WORKFLOW") == "True", reason="Skip Github CI."
# )
async def test_supervised_coder_agent_python_specialist(client):
    class SupervisedCoderAgent(scenario.AgentAdapter):
        async def call(self, input: scenario.AgentInput) -> scenario.AgentReturnTypes:
            user_message = input.last_new_user_message_str()
            return supervised_agent(client, user_message)

    result = await scenario.run(
        name="Simulation: Python coder agent",
        description="Generate Python code",
        agents=[
            SupervisedCoderAgent(),
            scenario.UserSimulatorAgent(),
            scenario.JudgeAgent(
                temperature=1.0,
                criteria=[
                    "Agent should not ask follow-up questions.",
                    "Agent should generate a solution containing code implementation example in Python."
                    "Solution should match the given criteria in the query.",
                ],
            ),
        ],
        script=[
            scenario.user(
                "Generate a hello world using FastAPI, it should accept 'name' as a query parameter."
            ),
            scenario.agent(),
            scenario.judge(),
        ],
    )

    assert result.success


@pytest.mark.agent_test
@pytest.mark.asyncio
@pytest.mark.skipif(
    condition=os.getenv("BUILD_WORKFLOW") == "True", reason="Skip Github CI."
)
async def test_supervised_researcher_agent(client):
    class SupervisedResearcherAgent(scenario.AgentAdapter):
        async def call(self, input: scenario.AgentInput) -> scenario.AgentReturnTypes:
            user_message = input.last_new_user_message_str()
            return supervised_agent(client, user_message)

    result = await scenario.run(
        name="Simulation: knowledge base researcher agent",
        description="Answer questions using knowledge base researcher",
        agents=[
            SupervisedResearcherAgent(),
            scenario.UserSimulatorAgent(),
            scenario.JudgeAgent(
                temperature=1.0,
                criteria=[
                    "Agent should not ask follow-up questions.",
                    "Agent should generate a comprehensive report containing answer to given question."
                    "Test dataset contains the book 'Sun-Tzu: Art of War', answer must contain be in this context. ",
                ],
            ),
        ],
        script=[
            scenario.user("According to Sun-Tzu, what is the pinnacle of excellence?"),
            scenario.agent(),
            scenario.judge(),
        ],
    )

    assert result.success


@pytest.mark.agent_test
@pytest.mark.asyncio
# @pytest.mark.skipif(
#     condition=os.getenv("BUILD_WORKFLOW") == "True", reason="Skip Github CI."
# )
async def test_supervised_coder_agent_bash_specialist(client):
    class SupervisedCoderAgent(scenario.AgentAdapter):
        async def call(self, input: scenario.AgentInput) -> scenario.AgentReturnTypes:
            user_message = input.last_new_user_message_str()
            return supervised_agent(client, user_message)

    result = await scenario.run(
        name="Simulation: Bash coder agent",
        description="Generate Bash script",
        agents=[
            SupervisedCoderAgent(),
            scenario.UserSimulatorAgent(),
            scenario.JudgeAgent(
                temperature=1.0,
                criteria=[
                    "Agent should not ask follow-up questions.",
                    "Agent should generate a solution containing a bash script implementation."
                    "Solution should match the given criteria in the query.",
                ],
            ),
        ],
        script=[
            scenario.user(
                "Generate a bash script that backs up a directory to a tar.gz archive, "
                "accepting source and destination paths as arguments."
            ),
            scenario.agent(),
            scenario.judge(),
        ],
    )

    assert result.success


@scenario.cache()
def supervised_agent(client, message_content) -> scenario.AgentReturnTypes:
    # create integration
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
