from pathlib import Path
from typing import Annotated, List, TypedDict

import hvac
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
    GradeHallucinations,
)
from app.services.agent_types.base import WorkflowAgent
from app.services.agents import AgentService
from app.services.integrations import IntegrationService
from app.services.language_model_settings import LanguageModelSettingService
from app.services.language_models import LanguageModelService


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
            You a question re-writer that converts an input question to a better version that is
            optimized for vectorstore retrieval. Look at the input and try to reason about the underlying
            semantic intent / meaning."""
        re_write_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system),
                (
                    "human",
                    "Here is the initial question: \n\n {query} \n Formulate an improved question.",
                ),
            ]
        )

        return re_write_prompt | chat_model | StrOutputParser()

    def get_query_router(self, llm, preparation_system_prompt):
        structured_llm_router = llm.with_structured_output(RouteQuery)
        route_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", preparation_system_prompt),
                ("human", "{question}"),
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
        return {knowledge_base: knowledge_base}

    def get_hallucination_grader(self, llm):
        # LLM with function call
        structured_llm_grader = llm.with_structured_output(GradeHallucinations)

        # Prompt
        system = """
        You are a grader assessing whether an LLM generation is grounded in / supported by one or
        more retrieved facts. \n
        Give a binary score 'yes' or 'no'. 'Yes' means that the answer is grounded in / supported by
        facts."""
        hallucination_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system),
                (
                    "human",
                    "Set of facts: \n\n {documents} \n\n LLM generation: {generation}",
                ),
            ]
        )

        return hallucination_prompt | structured_llm_grader

    def grade_generation_v_documents_and_question(self, state: AgentState):
        agent_id = state["agent_id"]
        query = state["query"]
        chat_model = self.get_chat_model(agent_id)
        documents = state["documents"]
        generation = state["generation"]

        score = self.get_hallucination_grader(chat_model).invoke(
            {"documents": documents, "generation": generation}
        )
        grade = score.binary_score

        # Check hallucination
        if grade == "yes":
            # Check question-answering
            score = self.get_answer_grader(chat_model).invoke(
                {"query": query, "generation": generation}
            )
            grade = score.binary_score
            if grade == "yes":
                return "useful"
            else:
                return "not useful"
        else:
            return "not supported"

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
        workflow_builder.add_edge("transform_query", "retrieve")
        workflow_builder.add_conditional_edges(
            "generate",
            self.grade_generation_v_documents_and_question,
            {
                "not supported": "generate",
                "useful": END,
                "not useful": "transform_query",
            },
        )

        return workflow_builder

    def get_rag_chain(self, chat_model):
        system = """
        You are an assistant for question-answering tasks. Use the following pieces of retrieved
        context to answer the question. If you don't know the answer, just say that you don't know.
        Use three sentences maximum and keep the answer concise.
        """
        generate_prompt = ChatPromptTemplate.from_messages(
            [("system", system), ("human", "Question: {query}\n Context: {context}")]
        )
        return generate_prompt | chat_model | StrOutputParser()

    def generate(self, state: AgentState):
        agent_id = state["agent_id"]
        query = state["query"]
        documents = state["documents"]
        chat_model = self.get_chat_model(agent_id)
        generation = self.get_rag_chain(chat_model).invoke(
            {"context": documents, "query": query}
        )
        return {generation: generation}

    def get_retrieval_grader(self, chat_model):
        # LLM with function call
        structured_llm_grader = chat_model.with_structured_output(GradeDocuments)

        # Prompt
        system = """You are a grader assessing relevance of a retrieved document to a user question. \n
            If the document contains keyword(s) or semantic meaning related to the user question,
            grade it as relevant. \n
            It does not need to be a stringent test. The goal is to filter out erroneous retrievals. \n
            Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to
            the question."""
        grade_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system),
                (
                    "human",
                    "Retrieved document: \n\n {document} \n\n User question: {question}",
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
            grade = score.binary_score
            if grade == "yes":
                filtered_docs.append(d)
            else:
                continue
        return {"documents": filtered_docs}

    def retrieve(self, state: AgentState):
        agent_id = state["agent_id"]
        query = state["query"]
        knowledge_base = state["knowledge_base"]
        embeddings = self.get_embeddings_model(agent_id)
        documents = self.document_repository.search(
            embeddings_model=embeddings, collection_name=knowledge_base, query=query
        )
        return {"documents": documents}

    def transform_query(self, state: AgentState):
        agent_id = state["agent_id"]
        query = state["query"]
        chat_model = self.get_chat_model(agent_id)
        better_query = self.get_query_rewriter(chat_model).invoke({"query": query})
        return {query: better_query}

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
        return {}
