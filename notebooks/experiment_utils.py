import os
from uuid import uuid4
from IPython.display import Image, display
import requests
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain_core.embeddings import Embeddings
from langchain_text_splitters import CharacterTextSplitter
from markitdown import MarkItDown

from app.infrastructure.database.vectors import DocumentRepository


def print_graph(graph):
    display(Image(graph.get_graph(xray=True).draw_mermaid_png()))


def create_static_document(
    embeddings_model: Embeddings,
    document_repository: DocumentRepository,
    file_path: str,
):
    md = MarkItDown()
    result = md.convert(file_path)
    md_file_path = f"{file_path}.md"
    with open(md_file_path, "w") as md_file:
        md_file.write(result.text_content)

    loader = UnstructuredMarkdownLoader(md_file_path)
    documents = loader.load_and_split(
        CharacterTextSplitter(chunk_size=512, chunk_overlap=64)
    )
    document_repository.add(embeddings_model, "static_document_data", documents)

    os.remove(md_file_path)


def create_agent_with_integration(
    llm_tag: str, agent_type: str, agent_lab_endpoint: str, integration_params: dict
):
    integration_response = requests.post(
        f"{agent_lab_endpoint}/integrations/create", json=integration_params
    )
    integration_response.raise_for_status()
    integration_result = integration_response.json()

    llm_params = {
        "integration_id": integration_result["id"],
        "language_model_tag": llm_tag,
    }

    llm_response = requests.post(f"{agent_lab_endpoint}/llms/create", json=llm_params)
    llm_response.raise_for_status()
    llm_result = llm_response.json()

    agent_params = {
        "agent_name": f"agent_{uuid4()}",
        "agent_type": agent_type,
        "language_model_id": llm_result["id"],
    }

    agent_response = requests.post(
        f"{agent_lab_endpoint}/agents/create", json=agent_params
    )
    agent_response.raise_for_status()
    agent_result = agent_response.json()

    return agent_result["id"]


def create_ollama_agent(
    llm_tag: str = "smollm2",
    agent_type: str = "test_echo",
    agent_lab_endpoint: str = "http://localhost:18000",
    ollama_endpoint: str = "http://localhost:11434/v1",
) -> str:
    integration_params = {
        "integration_type": "ollama_api_v1",
        "api_endpoint": ollama_endpoint,
        "api_key": "ollama",
    }

    return create_agent_with_integration(
        llm_tag, agent_type, agent_lab_endpoint, integration_params
    )


def create_xai_agent(
    llm_tag: str = "grok-2-latest",
    agent_type: str = "test_echo",
    agent_lab_endpoint: str = "http://localhost:8000",
    api_key: str = "",
) -> str:
    integration_params = {
        "integration_type": "xai_api_v1",
        "api_endpoint": "https://api.x.ai/v1/",
        "api_key": api_key,
    }

    return create_agent_with_integration(
        llm_tag, agent_type, agent_lab_endpoint, integration_params
    )
