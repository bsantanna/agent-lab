import json
from datetime import datetime
from pathlib import Path

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool, BaseTool
from langgraph.constants import START, END
from langgraph.graph import StateGraph, MessagesState
from langgraph.managed import RemainingSteps
from langgraph.prebuilt import create_react_agent, InjectedState
from langgraph.types import Command
from typing_extensions import List, Annotated, Literal

from app.interface.api.messages.schema import MessageRequest
from app.services.agent_types.base import (
    SupervisedWorkflowAgentBase,
    AgentUtils,
    join_messages,
)
from app.services.agent_types.coordinator_planner_supervisor import (
    SUPERVISED_AGENTS,
    SUPERVISED_AGENT_CONFIGURATION,
)
from app.services.agent_types.coordinator_planner_supervisor.schema import (
    SupervisorRouter,
)


class AgentState(MessagesState):
    agent_id: str
    query: str
    next: str
    collection_name: str
    coordinator_system_prompt: str
    planner_system_prompt: str
    supervisor_system_prompt: str
    researcher_system_prompt: str
    coder_system_prompt: str
    browser_system_prompt: str
    reporter_system_prompt: str
    deep_search_mode: bool
    execution_plan: str
    messages: Annotated[List, join_messages]
    remaining_steps: RemainingSteps


class CoordinatorPlannerSupervisorAgent(SupervisedWorkflowAgentBase):
    def __init__(self, agent_utils: AgentUtils):
        super().__init__(agent_utils)

    def format_response(self, workflow_state: AgentState) -> (str, dict):
        response_data = {
            "agent_id": workflow_state.get("agent_id"),
            "query": workflow_state.get("query"),
            "collection_name": workflow_state.get("collection_name"),
            "deep_search_mode": workflow_state.get("deep_search_mode"),
            "execution_plan": workflow_state.get("execution_plan"),
        }
        return workflow_state["messages"][-1].content, response_data

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

        deep_search_mode = settings_dict["deep_search_mode"] == "True"

        template_vars = {
            "CURRENT_TIME": datetime.now().strftime("%a %b %d %Y %H:%M:%S %z"),
            "DEEP_SEARCH_MODE": deep_search_mode,
            "SUPERVISED_AGENTS": SUPERVISED_AGENTS,
            "SUPERVISED_AGENT_CONFIGURATION": SUPERVISED_AGENT_CONFIGURATION,
        }

        return {
            "agent_id": message_request.agent_id,
            "query": message_request.message_content,
            "collection_name": settings_dict["collection_name"],
            "deep_search_mode": deep_search_mode,
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
            "messages": [HumanMessage(content=message_request.message_content)],
        }

    def get_coordinator(
        self, state: AgentState
    ) -> Command[Literal["planner", "__end__"]]:
        agent_id = state["agent_id"]
        query = state["query"]
        coordinator_system_prompt = state["coordinator_system_prompt"]

        self.logger.info(f"Agent[{agent_id}] -> Coordinator -> Query -> {query}")
        chat_model = self.get_chat_model(agent_id)
        response = self.get_coordinator_chain(
            chat_model, coordinator_system_prompt
        ).invoke({"query": query})
        self.logger.info(f"Agent[{agent_id}] -> Coordinator -> Response -> {response}")
        if response["next"] == END:
            return Command(
                goto=response["next"],
                update={"messages": [AIMessage(content=response["generated"])]},
            )
        else:
            return Command(goto=response["next"])

    def get_planner(self, state: AgentState) -> Command[Literal["supervisor"]]:
        agent_id = state["agent_id"]
        query = state["query"]
        planner_system_prompt = state["planner_system_prompt"]
        deep_search_mode = state["deep_search_mode"]
        self.logger.info(
            f"Agent[{agent_id}] -> Planner -> Query -> {query} -> Deep Search Mode -> {deep_search_mode}"
        )
        chat_model = self.get_chat_model(agent_id)

        if deep_search_mode:
            search_response = self.get_web_search_tool().invoke({"query": query})
            search_results = f"{json.dumps([{'title': elem['title'], 'content': elem['content']} for elem in search_response['results']], ensure_ascii=False)}"
            response = self.get_planner_chain(
                llm=chat_model,
                planner_system_prompt=planner_system_prompt,
                search_results=search_results,
            ).invoke({"query": query, "search_results": search_results})
        else:
            response = self.get_planner_chain(
                llm=chat_model, planner_system_prompt=planner_system_prompt
            ).invoke({"query": query})

        self.logger.info(f"Agent[{agent_id}] -> Planner -> Response -> {response}")
        plain_response = json.dumps(response)

        return Command(
            update={
                "messages": [AIMessage(content=plain_response, name="planner")],
                "execution_plan": response,
            },
            goto="supervisor",
        )

    def get_supervisor(
        self, state: AgentState
    ) -> Command[Literal[*SUPERVISED_AGENTS, "__end__"]]:
        agent_id = state["agent_id"]
        messages = self.get_last_interaction_messages(state["messages"])

        self.logger.info(f"Agent[{agent_id}] -> Supervisor -> Messages -> {messages}")
        supervisor_system_prompt = state["supervisor_system_prompt"]
        chat_model = self.get_chat_model(agent_id).bind_tools(
            self.get_supervisor_tools()
        )
        chat_model_with_structured_output = chat_model.with_structured_output(
            SupervisorRouter
        )
        response = self.get_supervisor_chain(
            llm=chat_model_with_structured_output,
            supervisor_system_prompt=supervisor_system_prompt,
        ).invoke({"messages": messages})
        self.logger.info(f"Agent[{agent_id}] -> Supervisor -> Response -> {response}")
        return Command(goto=response["next"], update={"next": response["next"]})

    def get_research_knowledge_base_tool(
        self, state: Annotated[dict, InjectedState]
    ) -> BaseTool:
        @tool("research_knowledge_base")
        def retrieve_tool_call():
            """
            Consult the knowledge base. Use this to perform research on known knowledge bases.

            Returns:
                str: Documents retrieved from knowledge base separated by line breaks.
            """
            agent_id = state["agent_id"]
            collection_name = state["collection_name"]
            execution_plan = state["execution_plan"]
            embeddings_model = self.get_embeddings_model(agent_id)
            thought_docs = self.document_repository.search(
                embeddings_model=embeddings_model,
                collection_name=collection_name,
                query=execution_plan["thought"],
                size=3,
            )
            return "\n\n".join([doc.page_content for doc in thought_docs])

        return retrieve_tool_call

    def get_researcher(self, state: AgentState) -> Command[Literal["supervisor"]]:
        agent_id = state["agent_id"]
        deep_search_mode = state["deep_search_mode"]
        researcher_system_prompt = state["researcher_system_prompt"]

        self.logger.info(
            f"Agent[{agent_id}] -> Researcher -> Deep Search Mode -> {deep_search_mode}"
        )
        if deep_search_mode:
            tools = [self.get_web_search_tool(), self.get_web_crawl_tool()]
        else:
            tools = [self.get_research_knowledge_base_tool(state)]

        chat_model = self.get_chat_model(agent_id)
        researcher = create_react_agent(
            model=chat_model,
            tools=tools,
            prompt=researcher_system_prompt,
        )
        response = researcher.invoke(state)
        self.logger.info(f"Agent[{agent_id}] -> Researcher -> Response -> {response}")
        return Command(
            update={"messages": response["messages"]},
            goto="supervisor",
        )

    def get_coder(self, state: AgentState) -> Command[Literal["supervisor"]]:
        agent_id = state["agent_id"]
        coder_system_prompt = state["coder_system_prompt"]

        self.logger.info(f"Agent[{agent_id}] -> Coder")
        chat_model = self.get_chat_model(agent_id)
        coder = create_react_agent(
            model=chat_model,
            tools=[self.get_bash_tool(), self.get_python_tool()],
            prompt=coder_system_prompt,
        )

        response = coder.invoke(state)
        self.logger.info(f"Agent[{agent_id}] -> Coder -> Response -> {response}")
        return Command(
            update={"messages": response["messages"]},
            goto="supervisor",
        )

    def get_browser(self, state: AgentState) -> Command[Literal["supervisor"]]:
        agent_id = state["agent_id"]
        browser_system_prompt = state["browser_system_prompt"]

        self.logger.info(f"Agent[{agent_id}] -> Browser")
        chat_model = self.get_chat_model(agent_id)
        browser = create_react_agent(
            model=chat_model,
            tools=[self.get_web_browser_tool(agent_id)],
            prompt=browser_system_prompt,
        )

        response = browser.invoke(state)
        self.logger.info(f"Agent[{agent_id}] -> Browser -> Response -> {response}")
        return Command(
            update={"messages": response["messages"]},
            goto="supervisor",
        )

    def get_reporter(self, state: AgentState) -> Command[Literal["supervisor"]]:
        agent_id = state["agent_id"]
        self.logger.info(f"Agent[{agent_id}] -> Reporter")
        reporter_system_prompt = state["reporter_system_prompt"]
        chat_model = self.get_chat_model(agent_id)
        reporter = create_react_agent(
            model=chat_model,
            tools=self.get_reporter_tools(),
            prompt=reporter_system_prompt,
        )
        response = reporter.invoke(state)
        self.logger.info(f"Agent[{agent_id}] -> Reporter -> Response -> {response}")
        return Command(
            update={"messages": response["messages"]},
            goto="supervisor",
        )
