from pathlib import Path

from app.interface.api.messages.schema import MessageRequest, MessageBase
from app.services.agent_settings import AgentSettingService
from app.services.agent_types.base import AgentBase


class ThreePhaseReactAgent(AgentBase):
    def __init__(self, agent_setting_service: AgentSettingService):
        super().__init__(agent_setting_service)

    def create_default_settings(self, agent_id: str):
        current_dir = Path(__file__).parent

        preparation_prompt = self.read_file_content(
            f"{current_dir}/default_preparation_system_prompt.txt"
        )
        self.setting_service.create_agent_setting(
            agent_id=agent_id,
            setting_key="preparation_system_prompt",
            setting_value=preparation_prompt,
        )

        execution_prompt = self.read_file_content(
            f"{current_dir}/default_execution_system_prompt.txt"
        )
        self.setting_service.create_agent_setting(
            agent_id=agent_id,
            setting_key="execution_system_prompt",
            setting_value=execution_prompt,
        )

        conclusion_prompt = self.read_file_content(
            f"{current_dir}/default_conclusion_system_prompt.txt"
        )
        self.setting_service.create_agent_setting(
            agent_id=agent_id,
            setting_key="conclusion_system_prompt",
            setting_value=conclusion_prompt,
        )

    def process_message(self, message_request: MessageRequest) -> MessageBase:
        pass  # todo
