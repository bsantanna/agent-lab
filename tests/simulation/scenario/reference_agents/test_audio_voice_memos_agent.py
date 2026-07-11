import os

import scenario
import pytest
from starlette.testclient import TestClient

from app.main import app
from tests.simulation.common.config import (
    judge_agent_kwargs,
    simulation_model_config,
)
from tests.simulation.common.reference_agents import audio_voice_memos_agent


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
                **judge_agent_kwargs(),
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
