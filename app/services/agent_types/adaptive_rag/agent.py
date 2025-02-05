from pathlib import Path
from typing import Annotated, List, TypedDict

import hvac
from langchain_core.documents import Document
from langchain_core.messages import AnyMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langgraph.constants import START, END
from langgraph.graph import add_messages, StateGraph

from app.infrastructure.database.checkpoints import GraphPersistenceFactory
from app.infrastructure.database.vectors import DocumentRepository
from app.interface.api.messages.schema import MessageRequest
from app.services.agent_settings import AgentSettingService
from app.services.agent_types.adaptive_rag.schema import (
    GradeDocuments,
    RouteQuery,
    GradeAnswer,
)
from app.services.agent_types.base import WorkflowAgent
from app.services.agents import AgentService
from app.services.integrations import IntegrationService
from app.services.language_model_settings import LanguageModelSettingService
from app.services.language_models import LanguageModelService
from app.services.messages import MessageService


class AgentState(TypedDict):
    agent_id: str
    query: str
    knowledge_base: str
    generation: str
    documents: List[str]
    messages: Annotated[List[AnyMessage], add_messages]
    preparation_system_prompt: str
    execution_system_prompt: str


class AdaptiveRagAgent(WorkflowAgent):
    def __init__(
        self,
        agent_service: AgentService,
        agent_setting_service: AgentSettingService,
        language_model_service: LanguageModelService,
        language_model_setting_service: LanguageModelSettingService,
        integration_service: IntegrationService,
        vault_client: hvac.Client,
        graph_persistence_factory: GraphPersistenceFactory,
        message_service: MessageService,
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
        self.message_service = message_service
        self.document_repository = document_repository

    def create_default_settings(self, agent_id: str):
        current_dir = Path(__file__).parent

        preparation_prompt = self.read_file_content(
            f"{current_dir}/default_preparation_system_prompt.txt"
        )
        self.agent_setting_service.create_agent_setting(
            agent_id=agent_id,
            setting_key="preparation_system_prompt",
            setting_value=preparation_prompt,
        )

        execution_prompt = self.read_file_content(
            f"{current_dir}/default_execution_system_prompt.txt"
        )
        self.agent_setting_service.create_agent_setting(
            agent_id=agent_id,
            setting_key="execution_system_prompt",
            setting_value=execution_prompt,
        )

    def get_query_rewriter(self, chat_model):
        system = """
        You a query re-writer that converts an input query to a better version that is
        optimized for vectorstore retrieval. Look at the input and try to reason about the underlying
        semantic intent / meaning.
        No explanation necessary, answer only with adapted version.
        """

        re_write_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system),
                (
                    "human",
                    "Here is the initial query: \n\n {query} \n Formulate an improved query.",
                ),
            ]
        )

        return re_write_prompt | chat_model | StrOutputParser()

    def get_query_router(self, llm, preparation_system_prompt):
        structured_llm_router = llm.with_structured_output(RouteQuery)
        route_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    f"{preparation_system_prompt}",
                ),
                ("human", "{query}"),
            ]
        )
        return route_prompt | structured_llm_router

    def determine_knowledge_base(self, state: AgentState):
        agent_id = state["agent_id"]
        query = state["query"]
        preparation_system_prompt = state["preparation_system_prompt"]
        chat_model = self.get_chat_model(agent_id)
        knowledge_base = self.get_query_router(
            chat_model, preparation_system_prompt
        ).invoke({"query": query})
        return knowledge_base

    def get_answer_grader(self, llm):
        # LLM with function call
        structured_llm_grader = llm.with_structured_output(GradeAnswer)

        # Prompt
        system = """
        You are a grader assessing whether an answer addresses or resolves the given query \n
        No explanation necessary. Give a binary score 'yes' or 'no'.
        'yes' means that the answer is helpful.
        Answer must be *exactly one* of the values 'yes' or 'no'.
        """
        answer_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system),
                ("human", "User query: \n\n {query} \n\n LLM generation: {generation}"),
            ]
        )

        return answer_prompt | structured_llm_grader

    def grade_generation_v_documents_and_question(self, state: AgentState):
        agent_id = state["agent_id"]
        query = state["query"]
        chat_model = self.get_chat_model(agent_id)
        generation = state["generation"]

        # Check question-answering
        score = self.get_answer_grader(chat_model).invoke(
            {"query": query, "generation": generation}
        )

        grade = None
        if score is not None:
            grade = score["binary_score"]

        if grade == "yes":
            return "useful"

        return "not useful"

    def get_workflow_builder(self, agent_id: str):
        workflow_builder = StateGraph(AgentState)

        # node definitions
        workflow_builder.add_node(
            "determine_knowledge_base", self.determine_knowledge_base
        )
        workflow_builder.add_node("retrieve", self.retrieve)
        workflow_builder.add_node("grade_documents", self.grade_documents)
        workflow_builder.add_node("generate", self.generate)
        workflow_builder.add_node("transform_query", self.transform_query)

        # edge definitions
        workflow_builder.add_edge(START, "determine_knowledge_base")
        workflow_builder.add_edge("determine_knowledge_base", "retrieve")
        workflow_builder.add_edge("retrieve", "grade_documents")
        workflow_builder.add_conditional_edges(
            "grade_documents",
            self.decide_to_generate,
            {
                "transform_query": "transform_query",
                "generate": "generate",
            },
        )
        workflow_builder.add_edge("transform_query", "determine_knowledge_base")
        workflow_builder.add_conditional_edges(
            "generate",
            self.grade_generation_v_documents_and_question,
            {
                "useful": END,
                "not useful": "transform_query",
            },
        )

        return workflow_builder

    def get_rag_chain(self, chat_model, execution_system_prompt):
        generate_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", execution_system_prompt),
                ("human", "Query: {query}\n Context: {context}"),
            ]
        )
        return generate_prompt | chat_model | StrOutputParser()

    def generate(self, state: AgentState):
        agent_id = state["agent_id"]
        query = state["query"]
        documents = state["documents"]
        execution_system_prompt = state["execution_system_prompt"]
        chat_model = self.get_chat_model(agent_id)
        generation = self.get_rag_chain(chat_model, execution_system_prompt).invoke(
            {"context": documents, "query": query}
        )
        return {"generation": generation}

    def get_retrieval_grader(self, chat_model):
        # LLM with function call
        structured_llm_grader = chat_model.with_structured_output(GradeDocuments)

        # Prompt
        system = """
        You are a grader assessing relevance of a retrieved document to a user query. \n
        Document can be of general nature like books, presentations, structural data, backend api data, etc.
        If the document can support a solution to the user query, grade it as relevant. \n
        It does not need to be a stringent test. The goal is to filter out erroneous retrievals. \n
        You are not supposed to answer user query, only filter documents for further analysis.
        Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the query.
        Answer must be *exactly one* of the values 'yes' or 'no'.
        """

        grade_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system),
                (
                    "human",
                    "Retrieved document: \n\n {document} \n\n User query: {query}",
                ),
            ]
        )

        return grade_prompt | structured_llm_grader

    def grade_documents(self, state: AgentState):
        agent_id = state["agent_id"]
        query = state["query"]
        documents = state["documents"]
        chat_model = self.get_chat_model(agent_id)

        filtered_docs = []
        for d in documents:
            score = self.get_retrieval_grader(chat_model).invoke(
                {"query": query, "document": d.page_content}
            )

            grade = None
            if score is not None:
                grade = score["binary_score"]

            if grade == "yes":
                filtered_docs.append(d)
            else:
                continue
        return {"documents": filtered_docs}

    def retrieve(self, state: AgentState):
        agent_id = state["agent_id"]
        query = state["query"]
        knowledge_base = state["knowledge_base"]

        if knowledge_base == "previous_conversations":
            messages = self.message_service.get_messages(agent_id)
            documents = [
                Document(page_content=message.message_content) for message in messages
            ]

        else:
            embeddings = self.get_embeddings_model(agent_id)
            documents = self.document_repository.search(
                embeddings_model=embeddings,
                collection_name=knowledge_base,
                query=query,
                size=3,
            )

        return {"documents": documents}

    def transform_query(self, state: AgentState):
        agent_id = state["agent_id"]
        query = state["query"]
        chat_model = self.get_chat_model(agent_id)
        better_query = self.get_query_rewriter(chat_model).invoke({"query": query})
        return {"query": better_query}

    def decide_to_generate(self, state: AgentState):
        filtered_documents = state["documents"]
        if not filtered_documents:
            # All documents have been filtered check_relevance
            # We will re-generate a new query
            return "transform_query"
        else:
            # We have relevant documents, so generate answer
            return "generate"

    def get_input_params(self, message_request: MessageRequest):
        settings = self.agent_setting_service.get_agent_settings(
            message_request.agent_id
        )
        settings_dict = {
            setting.setting_key: setting.setting_value for setting in settings
        }

        return {
            "agent_id": message_request.agent_id,
            "query": message_request.message_content,
            "preparation_system_prompt": settings_dict["preparation_system_prompt"],
            "execution_system_prompt": settings_dict["execution_system_prompt"],
        }
