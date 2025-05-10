import json
from pathlib import Path

from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.constants import START, END
from langgraph.managed import RemainingSteps
from langgraph.prebuilt import create_react_agent
from typing_extensions import Literal

from langgraph.graph import MessagesState, StateGraph
from langgraph.types import Command

from app.interface.api.messages.schema import MessageRequest
from app.services.agent_types.base import SupervisedWorkflowAgentBase, AgentUtils
from app.services.agent_types.business.agreement_planner import SUPERVISED_AGENTS
from app.services.agent_types.business.agreement_planner.schema import SupervisorRouter


class AgentState(MessagesState):
    agent_id: str
    query: str
    structured_report: dict
    coordinator_system_prompt: str
    planner_system_prompt: str
    supervisor_system_prompt: str
    reporter_system_prompt: str
    financial_struggle_system_prompt: str
    customer_complaint_system_prompt: str
    customer_profile: dict
    execution_plan: str
    agreement_plan: str
    claim_support_request: str
    remaining_steps: RemainingSteps


class AgreementPlanner(SupervisedWorkflowAgentBase):
    def __init__(self, agent_utils: AgentUtils):
        super().__init__(agent_utils)

    def get_coordinator(
        self, state: AgentState
    ) -> Command[Literal["planner", "__end__"]]:
        agent_id = state["agent_id"]
        query = state["query"]

        self.logger.info(f"Agent[{agent_id}] -> Coordinator -> Query -> {query}")
        chat_model = self.get_chat_model(agent_id)
        response = self.get_coordinator_chain(
            chat_model, state["coordinator_system_prompt"]
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
        self.logger.info(f"Agent[{agent_id}] -> Planner -> Query -> {query}")
        chat_model = self.get_chat_model(agent_id)
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

    def get_supervisor_chain(self, llm, supervisor_system_prompt: str):
        structured_llm_generator = llm.bind_tools(
            self.get_supervisor_tools()
        ).with_structured_output(SupervisorRouter)
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
        agreement_plan = state["agreement_plan"]
        claim_support_request = state["claim_support_request"]
        if agreement_plan:
            self.logger.info(
                f"Agent[{agent_id}] -> Supervisor -> Agreement Plan -> {agreement_plan}"
            )
            return Command(goto="__end__")
        if claim_support_request:
            self.logger.info(
                f"Agent[{agent_id}] -> Supervisor -> Claim Support Request -> {claim_support_request}"
            )
            return Command(goto="__end__")

        response = self.get_supervisor_chain(
            llm=self.get_chat_model(agent_id),
            supervisor_system_prompt=supervisor_system_prompt,
        ).invoke({"messages": messages})
        self.logger.info(f"Agent[{agent_id}] -> Supervisor -> Response -> {response}")
        return Command(goto=response["next"], update={"next": response["next"]})

    def get_reporter(self, state: AgentState) -> Command[Literal["supervisor"]]:
        agent_id = state["agent_id"]
        self.logger.info(f"Agent[{agent_id}] -> Reporter")
        reporter = create_react_agent(
            model=self.get_chat_model(agent_id),
            tools=self.get_reporter_tools(),
            prompt=state["reporter_system_prompt"],
        )
        response = reporter.invoke(state)
        self.logger.info(f"Agent[{agent_id}] -> Reporter -> Response -> {response}")
        return Command(
            update={"messages": response["messages"]},
            goto="supervisor",
        )

    def get_financial_struggle_analyst(
        self, state: AgentState
    ) -> Command[Literal["supervisor"]]:
        agent_id = state["agent_id"]
        self.logger.info(f"Agent[{agent_id}] -> Financial Struggle Analyst")
        financial_struggle_system_prompt = state["financial_struggle_system_prompt"]
        financial_struggle_analyst = create_react_agent(
            model=self.get_chat_model(agent_id),
            tools=self.get_financial_struggle_analyst_tools(),
            prompt=financial_struggle_system_prompt,
        )
        response = financial_struggle_analyst.invoke(state)
        self.logger.info(
            f"Agent[{agent_id}] -> Financial Struggle Analyst -> Response -> {response}"
        )
        return Command(
            update={"messages": response["messages"]},
            goto="supervisor",
        )

    def get_financial_struggle_analyst_tools(self) -> list:
        return []

    def get_customer_complaint_analyst(
        self, state: AgentState
    ) -> Command[Literal["supervisor"]]:
        agent_id = state["agent_id"]
        self.logger.info(f"Agent[{agent_id}] -> Customer Complaint Analyst")
        customer_complaint_system_prompt = state["customer_complaint_system_prompt"]
        customer_complaint_analyst = create_react_agent(
            model=self.get_chat_model(agent_id),
            tools=self.get_customer_complaint_analyst_tools(),
            prompt=customer_complaint_system_prompt,
        )
        response = customer_complaint_analyst.invoke(state)
        self.logger.info(
            f"Agent[{agent_id}] -> Customer Complaint Analyst -> Response -> {response}"
        )
        return Command(
            update={"messages": response["messages"]},
            goto="supervisor",
        )

    def get_customer_complaint_analyst_tools(self) -> list:
        return []

    def get_workflow_builder(self, agent_id: str):
        workflow_builder = StateGraph(AgentState)
        workflow_builder.add_edge(START, "coordinator")
        workflow_builder.add_node("coordinator", self.get_coordinator)
        workflow_builder.add_node("planner", self.get_planner)
        workflow_builder.add_node("supervisor", self.get_supervisor)
        workflow_builder.add_node(
            "financial_struggle_analyst", self.get_financial_struggle_analyst
        )
        workflow_builder.add_node(
            "customer_complaint_analyst", self.get_customer_complaint_analyst
        )
        workflow_builder.add_node("reporter", self.get_reporter)
        return workflow_builder

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

        financial_struggle_prompt = self.read_file_content(
            f"{current_dir}/default_financial_struggle_system_prompt.txt"
        )
        self.agent_setting_service.create_agent_setting(
            agent_id=agent_id,
            setting_key="financial_struggle_system_prompt",
            setting_value=financial_struggle_prompt,
        )

        supervisor_prompt = self.read_file_content(
            f"{current_dir}/default_supervisor_system_prompt.txt"
        )
        self.agent_setting_service.create_agent_setting(
            agent_id=agent_id,
            setting_key="supervisor_system_prompt",
            setting_value=supervisor_prompt,
        )

        customer_complaint_prompt = self.read_file_content(
            f"{current_dir}/default_customer_complaint_system_prompt.txt"
        )
        self.agent_setting_service.create_agent_setting(
            agent_id=agent_id,
            setting_key="customer_complaint_system_prompt",
            setting_value=customer_complaint_prompt,
        )

        reporter_prompt = self.read_file_content(
            f"{current_dir}/default_reporter_system_prompt.txt"
        )
        self.agent_setting_service.create_agent_setting(
            agent_id=agent_id,
            setting_key="reporter_system_prompt",
            setting_value=reporter_prompt,
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
