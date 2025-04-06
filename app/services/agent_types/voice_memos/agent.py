import json
from pathlib import Path

from langgraph.graph import MessagesState
from langgraph.managed import RemainingSteps
from typing_extensions import Annotated, List

from app.interface.api.messages.schema import MessageRequest
from app.services.agent_types.base import join_messages, WebAgentBase, AgentUtils


class AgentState(MessagesState):
    agent_id: str
    attachment_id: str
    transcription: str
    next: str
    coordinator_system_prompt: str
    planner_system_prompt: str
    supervisor_system_prompt: str
    content_analyst_system_prompt: str
    reporter_system_prompt: str
    execution_plan: str
    messages: Annotated[List, join_messages]
    remaining_steps: RemainingSteps


class VoiceMemosAgent(WebAgentBase):
    def __init__(self, agent_utils: AgentUtils):
        super().__init__(agent_utils)

    def format_response(self, workflow_state: AgentState) -> (str, dict):
        response_data = {
            "agent_id": workflow_state["agent_id"],
            "attachment_id": workflow_state["attachment_id"],
            "transcription": workflow_state["transcription"],
            "execution_plan": workflow_state["execution_plan"],
            "messages": [
                json.loads(message.model_dump_json())
                for message in workflow_state["messages"]
            ],
        }
        return response_data["messages"][-1]["content"], response_data

    def get_workflow_builder(self, agent_id: str):
        pass

    def create_default_settings(self, agent_id: str):
        current_dir = Path(__file__).parent

        supervisor_prompt = self.read_file_content(
            f"{current_dir}/default_supervisor_system_prompt.txt"
        )
        self.agent_setting_service.create_agent_setting(
            agent_id=agent_id,
            setting_key="supervisor_system_prompt",
            setting_value=supervisor_prompt,
        )

        content_analyst_prompt = self.read_file_content(
            f"{current_dir}/default_content_analyst_system_prompt.txt"
        )
        self.agent_setting_service.create_agent_setting(
            agent_id=agent_id,
            setting_key="content_analyst_system_prompt",
            setting_value=content_analyst_prompt,
        )

        coordinator_prompt = self.read_file_content(
            f"{current_dir}/default_coordinator_system_prompt.txt"
        )
        self.agent_setting_service.create_agent_setting(
            agent_id=agent_id,
            setting_key="coordinator_system_prompt",
            setting_value=coordinator_prompt,
        )

        planner_prompt = self.read_file_content(
            f"{current_dir}/default_planner_system_prompt.txt"
        )
        self.agent_setting_service.create_agent_setting(
            agent_id=agent_id,
            setting_key="planner_system_prompt",
            setting_value=planner_prompt,
        )

    def get_input_params(self, message_request: MessageRequest) -> dict:
        pass
