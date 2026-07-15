import os

import scenario
import pytest
from starlette.testclient import TestClient

from agent_lab.main import app
from tests.simulation.common.config import (
    judge_agent_kwargs,
    simulation_model_config,
)
from tests.simulation.common.reference_agents import supervised_agent


@pytest.fixture
def client():
    yield TestClient(app)


# Configure the default model for simulation
scenario.configure(default_model=simulation_model_config())


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
                **judge_agent_kwargs(),
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
                "With coder, generate a simple hello world with FastAPI in Python. "
                "No need to setup libraries, just generate the code as a text report that makes use of markdown "
                "formatting for reading. Make sure to include code examples in the final report."
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
                **judge_agent_kwargs(),
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
