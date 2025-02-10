from pathlib import Path

from langchain_core.messages import AIMessage, HumanMessage
from langchain_text_splitters import CharacterTextSplitter
from langgraph.managed import RemainingSteps
from typing_extensions import Annotated, List, TypedDict, Literal

import hvac
from langchain_core.documents import Document
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
    GenerateAnswer,
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
    messages: Annotated[List, add_messages]
    remaining_steps: RemainingSteps
    preparation_system_prompt: str
    execution_system_prompt: str
    query_rewriter_system_prompt: str
    answer_grader_system_prompt: str
    retrieval_grader_system_prompt: str


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

        query_rewriter_prompt = self.read_file_content(
            f"{current_dir}/default_query_rewriter_system_prompt.txt"
        )
        self.agent_setting_service.create_agent_setting(
            agent_id=agent_id,
            setting_key="query_rewriter_system_prompt",
            setting_value=query_rewriter_prompt,
        )

        answer_grader_prompt = self.read_file_content(
            f"{current_dir}/default_answer_grader_system_prompt.txt"
        )
        self.agent_setting_service.create_agent_setting(
            agent_id=agent_id,
            setting_key="answer_grader_system_prompt",
            setting_value=answer_grader_prompt,
        )

        retrieval_grader_prompt = self.read_file_content(
            f"{current_dir}/default_retrieval_grader_system_prompt.txt"
        )
        self.agent_setting_service.create_agent_setting(
            agent_id=agent_id,
            setting_key="retrieval_grader_system_prompt",
            setting_value=retrieval_grader_prompt,
        )

    def get_query_rewriter(self, chat_model, query_rewriter_system_prompt):
        re_write_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", query_rewriter_system_prompt),
                (
                    "human",
                    "Here is the initial query: <query>{query}</query> \n Formulate an improved query.",
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
                ("human", "<query>{query}</query>"),
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

    def get_answer_grader(self, llm, answer_grader_system_prompt):
        # LLM with function call
        structured_llm_grader = llm.with_structured_output(GradeAnswer)

        answer_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", answer_grader_system_prompt),
                ("human", "<query>{query}</query>\n<answer>{generation}</answer>"),
            ]
        )

        return answer_prompt | structured_llm_grader

    def grade_generation_v_documents_and_question(
        self, state: AgentState
    ) -> Literal["complete_answer", "incomplete_answer"]:
        agent_id = state["agent_id"]
        query = state["query"]
        chat_model = self.get_chat_model(agent_id)
        generation = state["generation"]
        remaining_steps = state["remaining_steps"]
        answer_grader_system_prompt = state["answer_grader_system_prompt"]
        limit_remaining_steps = 5
        # Check question-answering
        score = self.get_answer_grader(chat_model, answer_grader_system_prompt).invoke(
            {"query": query, "generation": generation}
        )

        grade = None
        if score is not None:
            grade = score["binary_score"]

        if grade == "yes" or remaining_steps <= limit_remaining_steps:
            return "complete_answer"

        return "incomplete_answer"

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
                "complete_answer": END,
                "incomplete_answer": "transform_query",
            },
        )

        return workflow_builder

    def get_rag_chain(self, llm, execution_system_prompt):
        structured_llm_generator = llm.with_structured_output(GenerateAnswer)
        generate_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", execution_system_prompt),
                (
                    "human",
                    "<query>{query}</query>\n<context>{context}</context>\n<knowledge_base>{knowledge_base}</knowledge_base>",
                ),
            ]
        )
        return generate_prompt | structured_llm_generator

    def generate(self, state: AgentState):
        agent_id = state["agent_id"]
        query = state["query"]
        documents = state["documents"]
        execution_system_prompt = state["execution_system_prompt"]
        knowledge_base = state["knowledge_base"]
        chat_model = self.get_chat_model(agent_id)
        generation = self.get_rag_chain(chat_model, execution_system_prompt).invoke(
            {"context": documents, "query": query, "knowledge_base": knowledge_base}
        )
        generation["messages"] = [
            HumanMessage(content=query),
            AIMessage(content=generation["generation"]),
        ]
        return generation

    def get_retrieval_grader(self, chat_model, retrieval_grader_system_prompt):
        # LLM with function call
        structured_llm_grader = chat_model.with_structured_output(GradeDocuments)

        grade_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", retrieval_grader_system_prompt),
                (
                    "human",
                    "<document>{document}</document>\n<query>{query}</query>",
                ),
            ]
        )

        return grade_prompt | structured_llm_grader

    def grade_documents(self, state: AgentState):
        agent_id = state["agent_id"]
        query = state["query"]
        documents = state["documents"]
        chat_model = self.get_chat_model(agent_id)
        retrieval_grader_system_prompt = state["retrieval_grader_system_prompt"]
        knowledge_base = state["knowledge_base"]

        if knowledge_base == "previous_conversations":
            return {"documents": documents}

        filtered_docs = []
        for d in documents:
            score = self.get_retrieval_grader(
                chat_model, retrieval_grader_system_prompt
            ).invoke({"query": query, "document": d.page_content})

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
        messages = state["messages"]

        if knowledge_base == "previous_conversations":
            text_splitter = CharacterTextSplitter()
            history = ""
            for message in messages:
                history = f"{history}\n{message.type}: {message.content}"
            chunks = text_splitter.split_text(history)
            documents = [Document(page_content=chunk) for chunk in chunks]

        else:
            embeddings = self.get_embeddings_model(agent_id)
            documents = self.document_repository.search(
                embeddings_model=embeddings,
                collection_name=knowledge_base,
                query=query,
                size=3,
            )

        return {"documents": documents}

    def transform_query(
        self, state: AgentState
    ) -> Literal["transform_query", "generate"]:
        agent_id = state["agent_id"]
        query = state["query"]
        chat_model = self.get_chat_model(agent_id)
        query_rewriter_system_prompt = state["query_rewriter_system_prompt"]
        transformed_query = self.get_query_rewriter(
            chat_model, query_rewriter_system_prompt
        ).invoke({"query": query})
        messages = [AIMessage(content=f"Transformed query: {transformed_query}")]
        return {"query": transformed_query, "messages": messages}

    def decide_to_generate(self, state: AgentState):
        filtered_documents = state["documents"]
        remaining_steps = state["remaining_steps"]
        if not filtered_documents and remaining_steps > 1:
            # All documents have been filtered check_relevance and there are still attempts left
            # We will re-generate a new query
            return "transform_query"
        else:
            # We have relevant documents or no attempts left, so generate answer
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
            "query_rewriter_system_prompt": settings_dict[
                "query_rewriter_system_prompt"
            ],
            "answer_grader_system_prompt": settings_dict["answer_grader_system_prompt"],
            "retrieval_grader_system_prompt": settings_dict[
                "retrieval_grader_system_prompt"
            ],
            "messages": [],
        }
