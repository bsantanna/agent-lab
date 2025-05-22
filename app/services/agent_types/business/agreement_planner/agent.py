import base64
import json
import mimetypes
from datetime import datetime
from pathlib import Path

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.constants import START
from langgraph.prebuilt import create_react_agent
from typing_extensions import Literal

from langgraph.graph import MessagesState, StateGraph
from langgraph.types import Command

from app.interface.api.messages.schema import MessageRequest
from app.services.agent_types.base import SupervisedWorkflowAgentBase, AgentUtils
from app.services.agent_types.business.agreement_planner import (
    SUPERVISED_AGENTS,
    SUPERVISED_AGENT_CONFIGURATION,
)
from app.services.agent_types.business.agreement_planner.schema import (
    SupervisorRouter,
    StructuredReport,
    ImpedimentAnalysis,
    FinancialExpertAnalysis,
    CustomerServiceExpertAnalysis,
    CoordinatorRouter,
)
from app.services.agent_types.schema import SolutionPlan


class AgentState(MessagesState):
    agent_id: str
    attachment_id: str
    query: str
    next: str
    coordinator_system_prompt: str
    planner_system_prompt: str
    supervisor_system_prompt: str
    reporter_system_prompt: str
    financial_struggle_system_prompt: str
    customer_complaint_system_prompt: str
    impediment_checker_system_prompt: str
    structured_report: dict
    execution_plan: dict
    agreement_plan: dict
    agreement_impediment: dict


class AgreementPlanner(SupervisedWorkflowAgentBase):
    def __init__(self, agent_utils: AgentUtils):
        super().__init__(agent_utils)

    def format_response(self, workflow_state: AgentState) -> (str, dict):
        response_data = {
            "agent_id": workflow_state.get("agent_id"),
            "query": workflow_state.get("query"),
            "structured_report": workflow_state.get("structured_report"),
            "execution_plan": workflow_state.get("execution_plan"),
            "agreement_plan": workflow_state.get("agreement_plan"),
            "agreement_impediment": workflow_state.get("agreement_impediment"),
        }
        return workflow_state["messages"][-1].content, response_data

    def get_coordinator(
        self, state: AgentState
    ) -> Command[Literal["planner", "impediment_checker", "__end__"]]:
        agent_id = state["agent_id"]
        attachment_id = state["attachment_id"]

        if attachment_id is None:
            query = state["query"]
            self.logger.info(f"Agent[{agent_id}] -> Coordinator -> Query -> {query}")
            coordinator = create_react_agent(
                model=self.get_chat_model(agent_id),
                tools=self.get_coordinator_tools(),
                prompt=state["coordinator_system_prompt"],
                response_format=CoordinatorRouter,
            )
            response = coordinator.invoke(state)
            self.logger.info(
                f"Agent[{agent_id}] -> Coordinator -> Response -> {response}"
            )
            return Command(
                goto=response["structured_response"]["next"],
                update={"messages": response["messages"]},
            )
        else:
            self.logger.info(
                f"Agent[{agent_id}] -> Coordinator -> Attachment -> {attachment_id}"
            )
            return Command(goto="impediment_checker")

    def get_planner(self, state: AgentState) -> Command[Literal["supervisor"]]:
        agent_id = state["agent_id"]
        query = state["query"]
        planner_system_prompt = state["planner_system_prompt"]
        self.logger.info(f"Agent[{agent_id}] -> Planner -> Query -> {query}")
        chat_model = (
            self.get_chat_model(agent_id)
            .bind_tools(self.get_planner_tools())
            .with_structured_output(SolutionPlan)
        )
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
        messages = self.get_last_interaction_messages(state["messages"])
        agent_id = state["agent_id"]
        self.logger.info(f"Agent[{agent_id}] -> Supervisor -> Messages -> {messages}")
        supervisor_system_prompt = state.get("supervisor_system_prompt")
        structured_report = state.get("structured_report")
        agreement_plan = state.get("agreement_plan")
        agreement_impediment = state.get("agreement_impediment")
        chat_model = self.get_chat_model(agent_id).bind_tools(
            self.get_supervisor_tools()
        )
        chat_model_with_structured_output = chat_model.with_structured_output(
            SupervisorRouter
        )

        if agreement_plan is not None and structured_report is not None:
            self.logger.info(
                f"Agent[{agent_id}] -> Supervisor -> Agreement Plan -> {agreement_plan}"
            )
            return Command(goto="__end__")
        if agreement_impediment is not None and structured_report is not None:
            self.logger.info(
                f"Agent[{agent_id}] -> Supervisor -> Claim Support Request -> {agreement_impediment}"
            )
            return Command(goto="__end__")

        response = self.get_supervisor_chain(
            llm=chat_model_with_structured_output,
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
            response_format=StructuredReport,
        )
        response = reporter.invoke(state)
        self.logger.info(f"Agent[{agent_id}] -> Reporter -> Response -> {response}")
        return Command(
            update={
                "messages": response["messages"],
                "structured_report": response["structured_response"],
            },
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
            response_format=FinancialExpertAnalysis,
        )
        response = financial_struggle_analyst.invoke(state)
        self.logger.info(
            f"Agent[{agent_id}] -> Financial Struggle Analyst -> Response -> {response}"
        )
        return Command(
            update={
                "messages": response["messages"],
                "agreement_plan": response["structured_response"]["agreement_plan"],
                "agreement_impediment": response["structured_response"][
                    "agreement_impediment"
                ],
            },
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
            response_format=CustomerServiceExpertAnalysis,
        )
        response = customer_complaint_analyst.invoke(state)
        self.logger.info(
            f"Agent[{agent_id}] -> Customer Complaint Analyst -> Response -> {response}"
        )
        return Command(
            update={
                "messages": response["messages"],
                "agreement_plan": response["structured_response"]["agreement_plan"],
                "agreement_impediment": response["structured_response"][
                    "agreement_impediment"
                ],
            },
            goto="supervisor",
        )

    def get_customer_complaint_analyst_tools(self) -> list:
        return []

    def get_impediment_checker(
        self, state: AgentState
    ) -> Command[Literal["planner", "__end__"]]:
        agent_id = state["agent_id"]
        query = state["query"]
        attachment_id = state["attachment_id"]
        impediment_checker_system_prompt = state["impediment_checker_system_prompt"]
        attachment = self.attachment_service.get_attachment_by_id(attachment_id)
        image_base64 = base64.b64encode(attachment.raw_content).decode("utf-8")
        image_content_type = mimetypes.guess_type(attachment.file_name)[0]
        chat_model_with_structured_output = (
            self.get_chat_model(agent_id)
            .bind_tools(self.get_impediment_checker_tools())
            .with_structured_output(ImpedimentAnalysis)
        )
        self.logger.info(f"Agent[{agent_id}] -> Claim Support Analyst")
        response = self.get_image_analysis_chain(
            chat_model_with_structured_output,
            impediment_checker_system_prompt,
            image_content_type,
        ).invoke({"query": query, "image_base64": image_base64})
        self.logger.info(
            f"Agent[{agent_id}] -> Claim Support Analyst -> Response -> {response}"
        )
        return Command(
            update={
                "messages": [
                    AIMessage(content=response["analysis"], name="impediment_checker")
                ],
            },
            goto=response["next"],
        )

    def get_workflow_builder(self, agent_id: str):
        workflow_builder = StateGraph(AgentState)
        workflow_builder.add_edge(START, "coordinator")
        workflow_builder.add_node("coordinator", self.get_coordinator)
        workflow_builder.add_node("planner", self.get_planner)
        workflow_builder.add_node("supervisor", self.get_supervisor)
        workflow_builder.add_node("impediment_checker", self.get_impediment_checker)
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

        impediment_checker_prompt = self.read_file_content(
            f"{current_dir}/default_impediment_checker_system_prompt.txt"
        )
        self.agent_setting_service.create_agent_setting(
            agent_id=agent_id,
            setting_key="impediment_checker_system_prompt",
            setting_value=impediment_checker_prompt,
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
            "FINANCIAL_STRUGGLE_ANALYST_TOOLS": [],
            "FINANCIAL_STRUGGLE_ANALYST_TOOLS_CONFIGURATION": {},
            "CUSTOMER_COMPLAINT_ANALYST_TOOLS": [],
            "CUSTOMER_COMPLAINT_ANALYST_TOOLS_CONFIGURATION": {},
        }

        return {
            "agent_id": message_request.agent_id,
            "query": message_request.message_content,
            "attachment_id": message_request.attachment_id,
            "structured_report": None,
            "agreement_plan": None,
            "agreement_impediment": None,
            "impediment_checker_system_prompt": self.parse_prompt_template(
                settings_dict, "impediment_checker_system_prompt", template_vars
            ),
            "coordinator_system_prompt": self.parse_prompt_template(
                settings_dict, "coordinator_system_prompt", template_vars
            ),
            "financial_struggle_system_prompt": self.parse_prompt_template(
                settings_dict, "financial_struggle_system_prompt", template_vars
            ),
            "planner_system_prompt": self.parse_prompt_template(
                settings_dict, "planner_system_prompt", template_vars
            ),
            "customer_complaint_system_prompt": self.parse_prompt_template(
                settings_dict, "customer_complaint_system_prompt", template_vars
            ),
            "supervisor_system_prompt": self.parse_prompt_template(
                settings_dict, "supervisor_system_prompt", template_vars
            ),
            "reporter_system_prompt": self.parse_prompt_template(
                settings_dict, "reporter_system_prompt", template_vars
            ),
            "messages": [HumanMessage(content=message_request.message_content)],
        }
