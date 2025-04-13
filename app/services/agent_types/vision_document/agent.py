import base64
import mimetypes
from datetime import datetime
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate
from langgraph.constants import START, END
from langgraph.graph import StateGraph, MessagesState

from app.interface.api.messages.schema import MessageRequest
from app.services.agent_types.base import WorkflowAgentBase, AgentUtils


class AgentState(MessagesState):
    agent_id: str
    query: str
    generation: dict
    image_base64: str
    image_content_type: str
    execution_system_prompt: str


class VisionDocumentAgent(WorkflowAgentBase):
    def __init__(self, agent_utils: AgentUtils):
        super().__init__(agent_utils)

    def format_response(self, workflow_state: AgentState) -> (str, dict):
        return workflow_state["generation"], {
            "agent_id": workflow_state["agent_id"],
            "query": workflow_state["query"],
            "generation": workflow_state["generation"],
        }

    def get_image_analysis_chain(
        self, llm, execution_system_prompt, image_content_type
    ):
        generate_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", execution_system_prompt),
                (
                    "human",
                    [
                        {
                            "type": "text",
                            "text": "<query>{query}</query>",
                        },
                        {
                            "type": "image_url",
                            "image_url": f"data:{image_content_type};base64,"
                            + "{image_base64}",
                        },
                    ],
                ),
            ]
        )
        return generate_prompt | llm

    def generate(self, state: AgentState):
        agent_id = state["agent_id"]
        query = state["query"]
        execution_system_prompt = state["execution_system_prompt"]
        image_base64 = state["image_base64"]
        image_content_type = state["image_content_type"]
        chat_model = self.get_chat_model(agent_id)
        generation = self.get_image_analysis_chain(
            chat_model, execution_system_prompt, image_content_type
        ).invoke({"query": query, "image_base64": image_base64})
        return {"generation": generation.content}

    def get_workflow_builder(self, agent_id: str):
        workflow_builder = StateGraph(AgentState)

        # node definitions
        workflow_builder.add_node("generate", self.generate)

        # edge definitions
        workflow_builder.add_edge(START, "generate")
        workflow_builder.add_edge("generate", END)

        return workflow_builder

    def get_input_params(self, message_request: MessageRequest):
        settings = self.agent_setting_service.get_agent_settings(
            message_request.agent_id
        )
        settings_dict = {
            setting.setting_key: setting.setting_value for setting in settings
        }

        attachment = self.attachment_service.get_attachment_by_id(
            message_request.attachment_id
        )

        image_base64 = base64.b64encode(attachment.raw_content).decode("utf-8")
        image_content_type = mimetypes.guess_type(attachment.file_name)[0]

        template_vars = {
            "CURRENT_TIME": datetime.now().strftime("%a %b %d %Y %H:%M:%S %z"),
        }

        return {
            "agent_id": message_request.agent_id,
            "query": message_request.message_content,
            "execution_system_prompt": self.parse_prompt_template(
                settings_dict, "execution_system_prompt", template_vars
            ),
            "image_base64": image_base64,
            "image_content_type": image_content_type,
        }

    def create_default_settings(self, agent_id: str):
        current_dir = Path(__file__).parent

        execution_prompt = self.read_file_content(
            f"{current_dir}/default_execution_system_prompt.txt"
        )
        self.agent_setting_service.create_agent_setting(
            agent_id=agent_id,
            setting_key="execution_system_prompt",
            setting_value=execution_prompt,
        )
