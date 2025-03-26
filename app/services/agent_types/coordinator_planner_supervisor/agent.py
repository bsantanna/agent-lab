import logging
from datetime import datetime
from pathlib import Path

import hvac
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.constants import START, END
from langgraph.graph import StateGraph, MessagesState
from langgraph.managed import RemainingSteps
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from typing_extensions import List, Annotated

from app.infrastructure.database.checkpoints import GraphPersistenceFactory
from app.infrastructure.database.vectors import DocumentRepository
from app.interface.api.messages.schema import MessageRequest
from app.services.agent_settings import AgentSettingService
from app.services.agent_types.base import join_messages, WorkflowAgent
from app.services.agent_types.coordinator_planner_supervisor import (
    SUPERVISED_AGENTS,
    SUPERVISED_AGENT_CONFIGURATION,
)
from app.services.agent_types.coordinator_planner_supervisor.schema import (
    SupervisorRouter,
    CoordinatorRouter,
)
from app.services.agents import AgentService
from app.services.integrations import IntegrationService
from app.services.language_model_settings import LanguageModelSettingService
from app.services.language_models import LanguageModelService


class AgentState(MessagesState):
    agent_id: str
    query: str
    generated: str
    collection_name: str
    coordinator_system_prompt: str
    planner_system_prompt: str
    supervisor_system_prompt: str
    researcher_system_prompt: str
    coder_system_prompt: str
    browser_system_prompt: str
    reporter_system_prompt: str
    deep_search_mode: bool
    plan: str
    messages: Annotated[List, join_messages]
    remaining_steps: RemainingSteps


class CoordinatorPlannerSupervisorAgent(WorkflowAgent):
    def __init__(
        self,
        agent_service: AgentService,
        agent_setting_service: AgentSettingService,
        language_model_service: LanguageModelService,
        language_model_setting_service: LanguageModelSettingService,
        integration_service: IntegrationService,
        vault_client: hvac.Client,
        graph_persistence_factory: GraphPersistenceFactory,
        document_repository: DocumentRepository,
    ):
        super().__init__(
            agent_service=agent_service,
            agent_setting_service=agent_setting_service,
            language_model_service=language_model_service,
            language_model_setting_service=language_model_setting_service,
            integration_service=integration_service,
            vault_client=vault_client,
            graph_persistence_factory=graph_persistence_factory,
        )
        self.document_repository = document_repository
        self.logger = logging.getLogger(__name__)

    def create_default_settings(self, agent_id: str):
        current_dir = Path(__file__).parent

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

        supervisor_prompt = self.read_file_content(
            f"{current_dir}/default_supervisor_system_prompt.txt"
        )
        self.agent_setting_service.create_agent_setting(
            agent_id=agent_id,
            setting_key="supervisor_system_prompt",
            setting_value=supervisor_prompt,
        )

        researcher_prompt = self.read_file_content(
            f"{current_dir}/default_researcher_system_prompt.txt"
        )
        self.agent_setting_service.create_agent_setting(
            agent_id=agent_id,
            setting_key="researcher_system_prompt",
            setting_value=researcher_prompt,
        )

        coder_prompt = self.read_file_content(
            f"{current_dir}/default_coder_system_prompt.txt"
        )
        self.agent_setting_service.create_agent_setting(
            agent_id=agent_id,
            setting_key="coder_system_prompt",
            setting_value=coder_prompt,
        )

        browser_prompt = self.read_file_content(
            f"{current_dir}/default_browser_system_prompt.txt"
        )
        self.agent_setting_service.create_agent_setting(
            agent_id=agent_id,
            setting_key="browser_system_prompt",
            setting_value=browser_prompt,
        )

        reporter_prompt = self.read_file_content(
            f"{current_dir}/default_reporter_system_prompt.txt"
        )
        self.agent_setting_service.create_agent_setting(
            agent_id=agent_id,
            setting_key="reporter_system_prompt",
            setting_value=reporter_prompt,
        )

        collection_name = self.read_file_content(
            f"{current_dir}/default_collection_name.txt"
        )
        self.agent_setting_service.create_agent_setting(
            agent_id=agent_id,
            setting_key="collection_name",
            setting_value=collection_name,
        )

        self.agent_setting_service.create_agent_setting(
            agent_id=agent_id,
            setting_key="deep_search_mode",
            setting_value="False",
        )

    def get_workflow_builder(self, agent_id: str):
        workflow_builder = StateGraph(AgentState)
        workflow_builder.add_edge(START, "coordinator")
        workflow_builder.add_node("coordinator", self.get_coordinator)
        workflow_builder.add_node("planner", self.get_planner)
        workflow_builder.add_node("supervisor", self.get_supervisor)
        workflow_builder.add_node("researcher", self.get_researcher)
        workflow_builder.add_node("coder", self.get_coder)
        workflow_builder.add_node("browser", self.get_browser)
        workflow_builder.add_node("reporter", self.get_reporter)
        return workflow_builder

    def get_input_params(self, message_request: MessageRequest):
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
            "query": message_request.message_content,
            "collection_name": settings_dict["collection_name"],
            "deep_search_mode": settings_dict["deep_search_mode"] == "True",
            "coordinator_system_prompt": self.parse_prompt_template(
                settings_dict, "coordinator_system_prompt", template_vars
            ),
            "planner_system_prompt": self.parse_prompt_template(
                settings_dict, "planner_system_prompt", template_vars
            ),
            "supervisor_system_prompt": self.parse_prompt_template(
                settings_dict, "supervisor_system_prompt", template_vars
            ),
            "researcher_system_prompt": self.parse_prompt_template(
                settings_dict, "researcher_system_prompt", template_vars
            ),
            "coder_system_prompt": self.parse_prompt_template(
                settings_dict, "coder_system_prompt", template_vars
            ),
            "browser_system_prompt": self.parse_prompt_template(
                settings_dict, "browser_system_prompt", template_vars
            ),
            "reporter_system_prompt": self.parse_prompt_template(
                settings_dict, "reporter_system_prompt", template_vars
            ),
            "messages": [],
        }

    def get_coordinator_chain(self, llm, coordinator_system_prompt: str):
        structured_llm_generator = llm.with_structured_output(CoordinatorRouter)
        coordinator_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", coordinator_system_prompt),
                ("human", "<query>{query}</query>"),
            ]
        )
        return coordinator_prompt | structured_llm_generator

    def get_coordinator(self, state: AgentState):
        self.logger.info("Coordinator -> Start")
        agent_id = state["agent_id"]
        query = state["query"]
        coordinator_system_prompt = state["coordinator_system_prompt"]
        chat_model = self.get_chat_model(agent_id)

        response = self.get_coordinator_chain(
            chat_model, coordinator_system_prompt
        ).invoke({"query": query})

        self.logger.info(f"Coordinator -> Response -> {response}")
        return Command(
            goto=response["next"], update={"generated": response["generated"]}
        )

    def get_planner(self, state: AgentState):
        deep_search_mode = state["deep_search_mode"]
        if deep_search_mode:
            tools = [
                self.get_web_search_tool(),
                self.create_handoff_tool(agent_name="supervisor"),
            ]
        else:
            tools = [self.create_handoff_tool(agent_name="supervisor")]

        agent_id = state["agent_id"]
        planner_system_prompt = state["planner_system_prompt"]
        chat_model = self.get_chat_model(agent_id)
        planner = create_react_agent(
            model=chat_model,
            tools=tools,
            prompt=planner_system_prompt,
        )
        return planner

    def get_supervisor_chain(self, llm, supervisor_system_prompt: str):
        structured_llm_generator = llm.with_structured_output(SupervisorRouter)
        supervisor_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", supervisor_system_prompt),
                (
                    "human",
                    "{query}",
                ),
            ]
        )
        return supervisor_prompt | structured_llm_generator

    def get_supervisor(self, state: AgentState):
        agent_id = state["agent_id"]
        query = state["query"]
        supervisor_system_prompt = state["supervisor_system_prompt"]
        chat_model = self.get_chat_model(agent_id)

        response = self.get_supervisor_chain(
            chat_model, supervisor_system_prompt
        ).invoke({"query": query})

        goto = response["next"]
        if goto == "FINISH":
            goto = END
        return Command(goto=goto, update={"next": goto})

    def get_researcher(self, state: AgentState):
        agent_id = state["agent_id"]
        researcher_system_prompt = state["researcher_system_prompt"]
        chat_model = self.get_chat_model(agent_id)
        researcher = create_react_agent(
            model=chat_model,
            tools=[
                self.create_handoff_tool(agent_name="supervisor")
            ],  # TODO include retrieval tool
            prompt=researcher_system_prompt,
        )
        return researcher

    def get_coder(self, state: AgentState):
        agent_id = state["agent_id"]
        coder_system_prompt = state["coder_system_prompt"]
        chat_model = self.get_chat_model(agent_id)
        coder = create_react_agent(
            model=chat_model,
            tools=[
                self.create_handoff_tool(agent_name="supervisor")
            ],  # TODO include Python tool
            prompt=coder_system_prompt,
        )
        return coder

    def get_browser(self, state: AgentState):
        # agent_id = state["agent_id"]
        # browser_system_prompt = state["browser_system_prompt"]
        # chat_model = self.get_chat_model(agent_id)

        # TODO call browser use https://medium.com/@sumit.somanchd/browser-use-with-openai-langchain-for-automating-web-browsing-ba6db7439566
        response = "???"
        return Command(
            update={
                "messages": [
                    HumanMessage(
                        content=response,
                        name="coder",
                    )
                ]
            },
            goto="supervisor",
        )

    def get_reporter(self, state: AgentState):
        agent_id = state["agent_id"]
        reporter_system_prompt = state["reporter_system_prompt"]
        chat_model = self.get_chat_model(agent_id)
        reporter = create_react_agent(
            model=chat_model,
            tools=[self.create_handoff_tool(agent_name="supervisor")],
            prompt=reporter_system_prompt,
        )
        return reporter
