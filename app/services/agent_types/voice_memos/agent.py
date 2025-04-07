import base64
import json
from datetime import datetime
from pathlib import Path

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.constants import START, END
from langgraph.graph import MessagesState, StateGraph
from langgraph.managed import RemainingSteps
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from typing_extensions import Annotated, List, Literal

from app.interface.api.messages.schema import MessageRequest
from app.services.agent_types.base import (
    join_messages,
    SupervisedWorkflowAgentBase,
    AgentUtils,
)
from app.services.agent_types.voice_memos import (
    SUPERVISED_AGENTS,
    SUPERVISED_AGENT_CONFIGURATION,
)
from app.services.agent_types.voice_memos.schema import (
    SupervisorRouter,
    VoiceCoordinatorRouter,
)


class AgentState(MessagesState):
    agent_id: str
    attachment_id: str
    query: str
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


class VoiceMemosAgent(SupervisedWorkflowAgentBase):
    def __init__(self, agent_utils: AgentUtils):
        super().__init__(agent_utils)

    def format_response(self, workflow_state: AgentState) -> (str, dict):
        response_data = {
            "agent_id": workflow_state["agent_id"],
            "attachment_id": workflow_state["attachment_id"],
            "query": workflow_state["query"],
            "transcription": workflow_state["transcription"],
            "execution_plan": workflow_state["execution_plan"],
            "messages": [
                json.loads(message.model_dump_json())
                for message in workflow_state["messages"]
            ],
        }
        return response_data["messages"][-1]["content"], response_data

    def get_workflow_builder(self, agent_id: str):
        workflow_builder = StateGraph(AgentState)
        workflow_builder.add_edge(START, "coordinator")
        workflow_builder.add_node("coordinator", self.get_coordinator)
        workflow_builder.add_node("planner", self.get_planner)
        workflow_builder.add_node("supervisor", self.get_supervisor)
        workflow_builder.add_node("reporter", self.get_reporter)
        workflow_builder.add_node("content_analyst", self.get_content_analyst)
        return workflow_builder

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

        coordinator_prompt = self.read_file_content(
            f"{current_dir}/default_coordinator_system_prompt.txt"
        )
        self.agent_setting_service.create_agent_setting(
            agent_id=agent_id,
            setting_key="coordinator_system_prompt",
            setting_value=coordinator_prompt,
        )

        content_analyst_prompt = self.read_file_content(
            f"{current_dir}/default_content_analyst_system_prompt.txt"
        )
        self.agent_setting_service.create_agent_setting(
            agent_id=agent_id,
            setting_key="content_analyst_system_prompt",
            setting_value=content_analyst_prompt,
        )

        planner_prompt = self.read_file_content(
            f"{current_dir}/default_planner_system_prompt.txt"
        )
        self.agent_setting_service.create_agent_setting(
            agent_id=agent_id,
            setting_key="planner_system_prompt",
            setting_value=planner_prompt,
        )

        reporter_prompt = self.read_file_content(
            f"{current_dir}/default_reporter_system_prompt.txt"
        )
        self.agent_setting_service.create_agent_setting(
            agent_id=agent_id,
            setting_key="reporter_system_prompt",
            setting_value=reporter_prompt,
        )

    def get_input_params(self, message_request: MessageRequest) -> dict:
        settings = self.agent_setting_service.get_agent_settings(
            message_request.agent_id
        )
        settings_dict = {
            setting.setting_key: setting.setting_value for setting in settings
        }

        template_vars = {
            "CURRENT_TIME": datetime.now().strftime("%a %b %d %Y %H:%M:%S %z"),
            "SUPERVISED_AGENTS": SUPERVISED_AGENTS,
            "SUPERVISED_AGENT_CONFIGURATION": SUPERVISED_AGENT_CONFIGURATION,
        }

        return {
            "agent_id": message_request.agent_id,
            "attachment_id": message_request.attachment_id,
            "query": message_request.message_content,
            "content_analyst_system_prompt": self.parse_prompt_template(
                settings_dict, "content_analyst_system_prompt", template_vars
            ),
            "coordinator_system_prompt": self.parse_prompt_template(
                settings_dict, "coordinator_system_prompt", template_vars
            ),
            "planner_system_prompt": self.parse_prompt_template(
                settings_dict, "planner_system_prompt", template_vars
            ),
            "supervisor_system_prompt": self.parse_prompt_template(
                settings_dict, "supervisor_system_prompt", template_vars
            ),
            "reporter_system_prompt": self.parse_prompt_template(
                settings_dict, "reporter_system_prompt", template_vars
            ),
            "messages": [HumanMessage(content=message_request.message_content)],
        }

    def get_voice_coordinator_chain(
        self,
        llm:BaseChatModel,
        coordinator_system_prompt: str,
        audio_format:str="wav"
    ):
        structured_llm_generator = llm.with_structured_output(VoiceCoordinatorRouter)
        coordinator_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", coordinator_system_prompt),
                ("human", [
                    {
                        "type": "text",
                        "text": "<query>{query}</query>",
                    },
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": "{audio_base64}",
                            "format": audio_format,
                        }
                    }
                ]),
            ]
        )
        return coordinator_prompt | structured_llm_generator

    def get_coordinator(
        self, state: AgentState
    ) -> Command[Literal["planner", "__end__"]]:
        agent_id = state["agent_id"]
        attachment_id = state["attachment_id"]
        query = state["query"]
        coordinator_system_prompt = state["coordinator_system_prompt"]

        self.logger.info(
            f"Agent[{agent_id}] -> Coordinator -> Query -> {query} -> Attachment[{attachment_id}]"
        )

        chat_model = self.get_chat_model(agent_id)
        attachment = self.attachment_service.get_attachment_by_id(
            attachment_id
        )
        audio_base64 = base64.b64encode(attachment.raw_content).decode()

        response = self.get_voice_coordinator_chain(
            chat_model, coordinator_system_prompt
        ).invoke({
            "query": f"{query}",
            "audio_base64": audio_base64
        })

        self.logger.info(f"Agent[{agent_id}] -> Coordinator -> Response -> {response}")

        return Command(
            goto=response["next"],
            update={"transcription": response["transcription"]},
        )

    def get_planner(self, state: MessagesState) -> Command[Literal["supervisor"]]:
        agent_id = state["agent_id"]
        query = state["query"]
        transcription = state["transcription"]
        planner_system_prompt = state["planner_system_prompt"]
        self.logger.info(
            f"Agent[{agent_id}] -> Planner -> Query -> {query} -> Transcription -> {transcription}"
        )
        chat_model = self.get_chat_model(agent_id)

        response = self.get_planner_chain(
            llm=chat_model, planner_system_prompt=planner_system_prompt
        ).invoke(
            {
                "query": f"User instructions: {query}\n\nAudio transcription: {transcription}"
            }
        )

        self.logger.info(f"Agent[{agent_id}] -> Planner -> Response -> {response}")
        plain_response = json.dumps(response)

        return Command(
            update={
                "messages": [AIMessage(content=plain_response, name="planner")],
                "execution_plan": response,
            },
            goto="supervisor",
        )

    def get_supervisor_chain(self, llm, supervisor_system_prompt: str):
        structured_llm_generator = llm.with_structured_output(SupervisorRouter)
        supervisor_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", supervisor_system_prompt),
                ("human", "<messages>{messages}</messages>"),
            ]
        )
        return supervisor_prompt | structured_llm_generator

    def get_supervisor(
        self, state: AgentState
    ) -> Command[Literal[*SUPERVISED_AGENTS, "__end__"]]:
        messages = self.get_last_interaction_messages(state["messages"])
        agent_id = state["agent_id"]
        self.logger.info(f"Agent[{agent_id}] -> Supervisor -> Messages -> {messages}")
        supervisor_system_prompt = state["supervisor_system_prompt"]
        response = self.get_supervisor_chain(
            llm=self.get_chat_model(agent_id),
            supervisor_system_prompt=supervisor_system_prompt,
        ).invoke({"messages": messages})
        self.logger.info(f"Agent[{agent_id}] -> Supervisor -> Response -> {response}")
        return Command(goto=response["next"], update={"next": response["next"]})

    def get_reporter(self, state: AgentState) -> Command[Literal["supervisor"]]:
        agent_id = state["agent_id"]
        self.logger.info(f"Agent[{agent_id}] -> Reporter")
        reporter_system_prompt = state["reporter_system_prompt"]
        reporter = create_react_agent(
            model=self.get_chat_model(agent_id),
            tools=[],
            prompt=reporter_system_prompt,
        )
        response = reporter.invoke(state)
        self.logger.info(f"Agent[{agent_id}] -> Reporter -> Response -> {response}")
        return Command(
            update={"messages": response["messages"]},
            goto="supervisor",
        )

    def get_content_analyst(self, state: AgentState) -> Command[Literal["supervisor"]]:
        agent_id = state["agent_id"]
        self.logger.info(f"Agent[{agent_id}] -> Content Analyst")
        content_analyst_system_prompt = state["content_analyst_system_prompt"]
        reporter = create_react_agent(
            model=self.get_chat_model(agent_id),
            tools=[],
            prompt=content_analyst_system_prompt,
        )
        response = reporter.invoke(state)
        self.logger.info(
            f"Agent[{agent_id}] -> Content Analyst -> Response -> {response}"
        )
        return Command(
            update={"messages": response["messages"]},
            goto="supervisor",
        )
