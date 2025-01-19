from pathlib import Path

from app.infrastructure.database.checkpoints import GraphPersistenceFactory
from app.interface.api.messages.schema import MessageRequest
from app.services.agent_settings import AgentSettingService
from app.services.agent_types.base import WorkflowAgent


class ThreePhaseReactAgent(WorkflowAgent):
    def __init__(
        self,
        agent_setting_service: AgentSettingService,
        graph_persistence_factory: GraphPersistenceFactory,
    ):
        super().__init__(agent_setting_service, graph_persistence_factory)

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

    def get_workflow_builder(self):
        pass

    def get_input_params(self, message_request: MessageRequest):
        pass
