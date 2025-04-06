import asyncio
import json
import logging
import os
import subprocess
import uuid
from abc import ABC, abstractmethod

import hvac
from browser_use.agent.service import Agent
from browser_use.agent.views import AgentHistoryList
from browser_use.browser.browser import BrowserConfig, Browser
from jinja2 import Environment, DictLoader, select_autoescape
from langchain_anthropic import ChatAnthropic
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool, BaseTool
from langchain_experimental.utilities import PythonREPL
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_tavily import TavilySearch, TavilyExtract
from langgraph.graph import MessagesState
from langgraph.types import Command
from typing_extensions import List, Annotated, Literal

from app.domain.exceptions.base import ResourceNotFoundError, ConfigurationError
from app.infrastructure.database.checkpoints import GraphPersistenceFactory
from app.infrastructure.database.vectors import DocumentRepository
from app.interface.api.messages.schema import MessageRequest, MessageResponse
from app.services.agent_settings import AgentSettingService
from app.services.agent_types.schema import CoordinatorRouter, SolutionPlan
from app.services.agents import AgentService
from app.services.attachments import AttachmentService
from app.services.integrations import IntegrationService
from app.services.language_model_settings import LanguageModelSettingService
from app.services.language_models import LanguageModelService


def join_messages(left: List, right: List) -> List:
    if not isinstance(left, list):
        left = [left]
    if not isinstance(right, list):
        right = [right]

    combined = left + right

    unique_messages = []
    for msg in combined:
        if msg not in unique_messages:
            unique_messages.append(msg)

    return unique_messages


class AgentUtils:
    def __init__(
        self,
        agent_service: AgentService,
        agent_setting_service: AgentSettingService,
        attachment_service: AttachmentService,
        language_model_service: LanguageModelService,
        language_model_setting_service: LanguageModelSettingService,
        integration_service: IntegrationService,
        vault_client: hvac.Client,
        graph_persistence_factory: GraphPersistenceFactory,
        document_repository: DocumentRepository,
    ):
        self.agent_service = agent_service
        self.agent_setting_service = agent_setting_service
        self.attachment_service = attachment_service
        self.language_model_service = language_model_service
        self.language_model_setting_service = language_model_setting_service
        self.integration_service = integration_service
        self.vault_client = vault_client
        self.graph_persistence_factory = graph_persistence_factory
        self.document_repository = document_repository


class AgentBase(ABC):
    def __init__(self, agent_utils: AgentUtils):
        self.agent_service = agent_utils.agent_service
        self.agent_setting_service = agent_utils.agent_setting_service
        self.language_model_service = agent_utils.language_model_service
        self.language_model_setting_service = agent_utils.language_model_setting_service
        self.integration_service = agent_utils.integration_service
        self.vault_client = agent_utils.vault_client
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    def create_default_settings(self, agent_id: str):
        pass

    @abstractmethod
    def get_input_params(self, message_request: MessageRequest) -> dict:
        pass

    @abstractmethod
    def process_message(self, message_request: MessageRequest) -> MessageResponse:
        pass

    def format_response(self, workflow_state: MessagesState) -> (str, dict):
        response_data = {
            "messages": [
                json.loads(message.model_dump_json())
                for message in workflow_state["messages"]
            ]
        }
        return response_data["messages"][-1]["content"], response_data

    def get_embeddings_model(self, agent_id) -> Embeddings:
        agent = self.agent_service.get_agent_by_id(agent_id)
        language_model = self.language_model_service.get_language_model_by_id(
            agent.language_model_id
        )
        integration = self.integration_service.get_integration_by_id(
            language_model.integration_id
        )
        secrets = self.vault_client.secrets.kv.read_secret_version(
            path=f"integration_{integration.id}", raise_on_deleted_version=False
        )
        api_endpoint = secrets["data"]["data"]["api_endpoint"]
        api_key = secrets["data"]["data"]["api_key"]

        lm_settings = self.language_model_setting_service.get_language_model_settings(
            agent.language_model_id
        )

        lm_settings_dict = {
            setting.setting_key: setting.setting_value for setting in lm_settings
        }

        if integration.integration_type == "openai_api_v1":
            return OpenAIEmbeddings(
                model=lm_settings_dict["embeddings"],
                openai_api_base=api_endpoint,
                openai_api_key=api_key,
            )
        elif integration.integration_type == "ollama_api_v1":
            return OllamaEmbeddings(
                model=lm_settings_dict["embeddings"], base_url=api_endpoint
            )
        else:
            return OllamaEmbeddings(
                model=lm_settings_dict["embeddings"],
                base_url=f"{os.getenv('OLLAMA_ENDPOINT')}",
            )

    def get_chat_model(self, agent_id) -> BaseChatModel:
        agent = self.agent_service.get_agent_by_id(agent_id)
        language_model = self.language_model_service.get_language_model_by_id(
            agent.language_model_id
        )
        integration = self.integration_service.get_integration_by_id(
            language_model.integration_id
        )
        secrets = self.vault_client.secrets.kv.read_secret_version(
            raise_on_deleted_version=False, path=f"integration_{integration.id}"
        )
        api_endpoint = secrets["data"]["data"]["api_endpoint"]
        api_key = secrets["data"]["data"]["api_key"]

        if (
            integration.integration_type == "openai_api_v1"
            or integration.integration_type == "xai_api_v1"
        ):
            return ChatOpenAI(
                model_name=language_model.language_model_tag,
                openai_api_base=api_endpoint,
                openai_api_key=api_key,
            )
        elif integration.integration_type == "anthropic_api_v1":
            return ChatAnthropic(
                model=language_model.language_model_tag,
                anthropic_api_url=api_endpoint,
                anthropic_api_key=api_key,
            )
        else:
            return ChatOllama(
                model=language_model.language_model_tag,
                base_url=api_endpoint,
            )

    def read_file_content(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            raise ResourceNotFoundError(file_path)

        with open(file_path, "r") as file:
            return file.read().strip()

    def parse_prompt_template(
        self, settings_dict: dict, prompt_key: str, template_vars: dict
    ) -> str:
        env = Environment(
            loader=DictLoader(settings_dict),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        template = env.get_template(prompt_key)
        return template.render(template_vars)


class WorkflowAgentBase(AgentBase, ABC):
    def __init__(self, agent_utils: AgentUtils):
        super().__init__(agent_utils)
        self.graph_persistence_factory = agent_utils.graph_persistence_factory

    @abstractmethod
    def get_workflow_builder(self, agent_id: str):
        pass

    def get_config(self, agent_id: str) -> dict:
        return {
            "configurable": {
                "thread_id": agent_id,
            },
            "recursion_limit": 30,
        }

    def create_thought_chain(
        self,
        human_input: str,
        ai_response: str,
        connection: str = None,
        llm: BaseChatModel = None,
        token_limit: int = 1024,
    ):
        # Build the chain of thought
        if llm is not None:
            prompt = (
                f"Summarize the text delimited by <ai_resp></ai_resp> using at most {token_limit} tokens.\n"
                f"<ai_resp>{ai_response}</ai_resp>"
            )
            processed_response = llm.invoke(prompt).content
        else:
            processed_response = ai_response

        thought_chain = (
            f"First: The human asked or stated - {human_input}\n"
            f"Then: The AI responded with - {processed_response}\n"
        )

        if connection is not None:
            thought_chain += f"Connection: {connection}"

        return thought_chain

    def process_message(self, message_request: MessageRequest) -> MessageResponse:
        agent_id = message_request.agent_id
        checkpointer = self.graph_persistence_factory.build_checkpoint_saver()
        workflow = self.get_workflow_builder(agent_id).compile(
            checkpointer=checkpointer
        )

        config = self.get_config(agent_id)
        self.logger.info(f"Agent[{agent_id}] -> Config -> {config}")

        inputs = self.get_input_params(message_request)
        self.logger.info(f"Agent[{agent_id}] -> Input -> {inputs}")

        workflow_result = workflow.invoke(inputs, config)
        self.logger.info(f"Agent[{agent_id}] -> Result -> {workflow_result}")
        message_content, response_data = self.format_response(workflow_result)
        return MessageResponse(
            message_role="assistant",
            message_content=message_content,
            response_data=response_data,
            agent_id=agent_id,
        )

    def get_bash_tool(self) -> BaseTool:
        @tool("bash_tool")
        def bash_tool_call(
            cmd: Annotated[str, "The bash command to be executed."],
            timeout: Annotated[
                int, "Maximum time in seconds for the command to complete."
            ] = 120,
        ):
            """Use this to execute bash command and do necessary operations."""
            self.logger.info(f"Executing Bash Command: {cmd} with timeout {timeout}s")
            try:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    check=True,
                    text=True,
                    capture_output=True,
                    timeout=timeout,
                )
                return result.stdout
            except subprocess.CalledProcessError as e:
                error_message = f"Command failed with exit code {e.returncode}.\nStdout: {e.stdout}\nStderr: {e.stderr}"
            except subprocess.TimeoutExpired:
                error_message = f"Command '{cmd}' timed out after {timeout}s."
            except Exception as e:
                error_message = f"Error executing command: {str(e)}"

            self.logger.error(error_message)
            return error_message

        return bash_tool_call

    def get_python_tool(self) -> BaseTool:
        @tool("python_tool")
        def python_tool_call(
            code: Annotated[
                str, "The python code to execute to do further analysis or calculation."
            ],
        ):
            """Use this to execute python3 code and do data analysis or calculation. If you want to see the output of a value,
            you should print it out with `print(...)`. This is visible to the user."""

            repl = PythonREPL()

            if not isinstance(code, str):
                error_msg = f"Invalid input: code must be a string, got {type(code)}"
                self.logger.error(error_msg)
                return (
                    f"Error executing code:\n```python\n{code}\n```\nError: {error_msg}"
                )

            self.logger.info("Executing Python code")
            try:
                result = repl.run(code)
                if isinstance(result, str) and (
                    "Error" in result or "Exception" in result
                ):
                    raise ValueError(result)
                self.logger.info("Code execution successful")
                return (
                    f"Successfully executed:\n```python\n{code}\n```\nStdout: {result}"
                )
            except ValueError as e:
                error_msg = repr(e)
                self.logger.error(error_msg)
                return (
                    f"Error executing code:\n```python\n{code}\n```\nError: {error_msg}"
                )

        return python_tool_call

    def get_last_interaction_messages(self, messages):
        subarray = []
        found_human_message = False

        for message in reversed(messages):
            subarray.insert(0, message)
            if isinstance(message, HumanMessage):
                found_human_message = True
                break

        return subarray if found_human_message else []


class WebAgentBase(WorkflowAgentBase, ABC):
    def __init__(self, agent_utils: AgentUtils):
        super().__init__(agent_utils)
        self.document_repository = agent_utils.document_repository
        if not os.environ.get("TAVILY_API_KEY"):
            raise ConfigurationError("TAVILY_API_KEY environment variable not set")

    def get_web_browser_tool(
        self,
        agent_id: str,
        cache_dir: str = None,
        headless: bool = True,
    ) -> BaseTool:
        if cache_dir is None:
            temp_dir = f"{os.getcwd()}/tmp/"  # NOSONAR used inside container
            os.makedirs(temp_dir, exist_ok=True)
            cache_dir = temp_dir

        chat_model = self.get_chat_model(agent_id)

        def get_browser_result(result_content: str, generated_gif_path: str) -> dict:
            return {
                "result_content": result_content,
                "generated_gif_path": generated_gif_path,
            }

        @tool("browser_tool")
        def browser_tool_call(
            instruction: Annotated[str, "The instruction to use browser."],
        ):
            """
            "Use this tool to interact with web browsers. Input should be a natural language description of
            what you want to do with the browser, such as 'Go to google.com and search for browser-use', or 'Navigate
            to Reddit and find the top post about AI'."
            """
            generated_gif_path = f"{cache_dir}/{uuid.uuid4()}.gif"
            browser_config = BrowserConfig(headless=headless)
            browser = Browser(config=browser_config)
            browser_agent = Agent(
                task=instruction,  # Will be set per request
                llm=chat_model,
                browser=browser,
                generate_gif=generated_gif_path,
            )
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(browser_agent.run())

                    if isinstance(result, AgentHistoryList):
                        json_result = json.dumps(
                            get_browser_result(
                                result.final_result(), generated_gif_path
                            )
                        )
                    else:
                        json_result = json.dumps(
                            get_browser_result(result, generated_gif_path)
                        )

                    self.logger.info(
                        f"Browser tool completed successfully, result: {json_result}"
                    )
                    return json_result

                finally:
                    loop.run_until_complete(browser_agent.browser.close())

            except Exception as e:
                return f"Error executing browser task: {str(e)}"
            finally:
                loop.close()

        return browser_tool_call

    def get_web_crawl_tool(self, extract_depth="basic") -> BaseTool:
        return TavilyExtract(extract_depth=extract_depth)

    def get_web_search_tool(self, max_results=5, topic="general") -> BaseTool:
        return TavilySearch(max_results=max_results, topic=topic)


class SupervisedWorkflowAgentBase(WebAgentBase, ABC):
    def __init__(self, agent_utils: AgentUtils):
        super().__init__(agent_utils)
        self.document_repository = agent_utils.document_repository
        if not os.environ.get("TAVILY_API_KEY"):
            raise ConfigurationError("TAVILY_API_KEY environment variable not set")

    @abstractmethod
    def get_coordinator(
        self, state: MessagesState
    ) -> Command[Literal["planner", "__end__"]]:
        pass

    def get_coordinator_chain(self, llm, coordinator_system_prompt: str):
        structured_llm_generator = llm.with_structured_output(CoordinatorRouter)
        coordinator_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", coordinator_system_prompt),
                ("human", "<query>{query}</query>"),
            ]
        )
        return coordinator_prompt | structured_llm_generator

    @abstractmethod
    def get_planner(self, state: MessagesState) -> Command[Literal["supervisor"]]:
        pass

    def get_planner_chain(
        self, llm, planner_system_prompt: str, search_results: str = None
    ):
        structured_llm_generator = llm.with_structured_output(SolutionPlan)
        if search_results is not None:
            planner_input = "<query>{query}</query>\n\n<search_results>{search_results}</search_results>"
        else:
            planner_input = "<query>{query}</query>"
        planner_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", planner_system_prompt),
                ("human", planner_input),
            ]
        )
        return planner_prompt | structured_llm_generator

    @abstractmethod
    def get_supervisor(self, state: MessagesState) -> Command:
        pass

    @abstractmethod
    def get_reporter(self, state: MessagesState) -> Command[Literal["supervisor"]]:
        pass
