import os
from uuid import uuid4
from IPython.display import Image, display
import requests
from langchain_core.runnables.graph import MermaidDrawMethod

from agent_lab.app_factory import bind_agent_registry
from agent_lab.core.config import default_config_source, load_config
from agent_lab.core.container import Container
from agent_lab.services.agent_types import discovery

DEFAULT_AGENT_LAB_ENDPOINT = "http://localhost:18000"
DEFAULT_SCAN_PACKAGES = ("agent_lab.services.agent_types",)


def bootstrap_container(modules, scan_packages=DEFAULT_SCAN_PACKAGES):
    # mirrors create_app()'s composition root for use outside the app factory;
    # config-*.yml paths are relative, so call this after chdir to the repo root
    discovery.scan_packages(scan_packages)
    discovery.load_entry_point_agents()
    container = Container()
    load_config(container, default_config_source())
    bind_agent_registry(container)
    container.init_resources()
    container.wire(modules=modules)
    return container


def print_graph(graph):
    display(
        Image(
            graph.get_graph(xray=True).draw_mermaid_png(
                draw_method=MermaidDrawMethod.API
            )
        )
    )


def create_llm_with_integration(
    llm_tag: str,
    integration_params: dict,
    agent_lab_endpoint: str = DEFAULT_AGENT_LAB_ENDPOINT,
    embeddings_tag: str = None,
):
    # pin embeddings to the model served by EMBEDDINGS_ENDPOINT (openai_api_v1
    # integrations default to text-embedding-3-large, which Ollama lacks)
    if embeddings_tag is None and os.getenv("EMBEDDINGS_ENDPOINT"):
        embeddings_tag = "bge-m3"

    integration_response = requests.post(
        f"{agent_lab_endpoint}/integrations/create",
        json=integration_params,
        headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN', 'x')}"},
    )
    integration_response.raise_for_status()
    integration_result = integration_response.json()

    llm_params = {
        "integration_id": integration_result["id"],
        "language_model_tag": llm_tag,
    }

    llm_response = requests.post(
        f"{agent_lab_endpoint}/llms/create",
        json=llm_params,
        headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN', 'x')}"},
    )
    llm_response.raise_for_status()
    llm_result = llm_response.json()

    if embeddings_tag is not None:
        update_response = requests.post(
            f"{agent_lab_endpoint}/llms/update_setting",
            json={
                "language_model_id": llm_result["id"],
                "setting_key": "embeddings",
                "setting_value": embeddings_tag,
            },
            headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN', 'x')}"},
        )
        update_response.raise_for_status()

    return llm_result


def create_agent_with_integration(
    llm_tag: str,
    agent_type: str,
    integration_params: dict,
    agent_lab_endpoint: str = DEFAULT_AGENT_LAB_ENDPOINT,
    embeddings_tag: str = None,
    rag_collection: str = None,
):
    llm_result = create_llm_with_integration(
        llm_tag=llm_tag,
        integration_params=integration_params,
        agent_lab_endpoint=agent_lab_endpoint,
        embeddings_tag=embeddings_tag,
    )

    agent_params = {
        "agent_name": f"agent_{uuid4()}",
        "agent_type": agent_type,
        "language_model_id": llm_result["id"],
    }

    agent_response = requests.post(
        f"{agent_lab_endpoint}/agents/create",
        json=agent_params,
        headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN', 'x')}"},
    )
    agent_response.raise_for_status()
    agent_result = agent_response.json()

    rag_agent_types = ["adaptive_rag", "react_rag", "coordinator_planner_supervisor"]
    if agent_type in rag_agent_types:
        if rag_collection is not None:
            collection = rag_collection
        else:
            collection = "static_document_data_ollama_embeddings"
        update_agent_setting(
            agent_id=agent_result["id"],
            setting_key="collection_name",
            setting_value=collection,
            agent_lab_endpoint=agent_lab_endpoint,
        )

    return agent_result


def create_local_agent(
    llm_tag: str = "phi4-mini:latest",
    agent_type: str = "test_echo",
    agent_lab_endpoint: str = DEFAULT_AGENT_LAB_ENDPOINT,
    local_endpoint: str = "http://localhost:11434/v1",
) -> str:
    # local openai-compatible server (e.g. ollama) mocking the openai api
    integration_params = {
        "integration_type": "openai_api_v1",
        "api_endpoint": local_endpoint,
        "api_key": "ollama",
    }

    return create_agent_with_integration(
        llm_tag,
        agent_type,
        integration_params,
        agent_lab_endpoint,
        embeddings_tag="bge-m3",
        rag_collection="static_document_data_ollama_embeddings",
    )


def create_openai_agent(
    llm_tag: str = "gpt-5-nano",
    agent_type: str = "test_echo",
    agent_lab_endpoint: str = DEFAULT_AGENT_LAB_ENDPOINT,
    api_key: str = "",
) -> str:
    integration_params = {
        "integration_type": "openai_api_v1",
        "api_endpoint": "https://api.openai.com/v1/",
        "api_key": api_key,
    }

    return create_agent_with_integration(
        llm_tag,
        agent_type,
        integration_params,
        agent_lab_endpoint,
    )


def create_xai_agent(
    llm_tag: str = "grok-4.5",
    agent_type: str = "test_echo",
    agent_lab_endpoint: str = DEFAULT_AGENT_LAB_ENDPOINT,
    api_key: str = "",
) -> str:
    integration_params = {
        "integration_type": "xai_api_v1",
        "api_endpoint": "https://api.x.ai/v1/",
        "api_key": api_key,
    }

    return create_agent_with_integration(
        llm_tag,
        agent_type,
        integration_params,
        agent_lab_endpoint,
    )


def create_anthropic_agent(
    llm_tag: str = "claude-haiku-4-5-20251001",
    agent_type: str = "test_echo",
    agent_lab_endpoint: str = DEFAULT_AGENT_LAB_ENDPOINT,
    api_key: str = "",
) -> str:
    integration_params = {
        "integration_type": "anthropic_api_v1",
        "api_endpoint": "https://api.anthropic.com",
        "api_key": api_key,
    }

    return create_agent_with_integration(
        llm_tag,
        agent_type,
        integration_params,
        agent_lab_endpoint,
    )


def create_attachment(
    file_path: str,
    content_type: str,
    agent_lab_endpoint: str = DEFAULT_AGENT_LAB_ENDPOINT,
) -> str:
    with open(file_path, "rb") as file:
        attachment_response = requests.post(
            f"{agent_lab_endpoint}/attachments/upload",
            files={"file": (file_path, file, content_type)},
            headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN', 'x')}"},
        )
        return attachment_response.json()["id"]


def create_embeddings(
    attachment_id: str,
    language_model_id: str,
    collection_name: str,
    agent_lab_endpoint: str = DEFAULT_AGENT_LAB_ENDPOINT,
) -> dict:
    embeddings_response = requests.post(
        f"{agent_lab_endpoint}/attachments/embeddings",
        json={
            "attachment_id": attachment_id,
            "language_model_id": language_model_id,
            "collection_name": collection_name,
        },
        headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN', 'x')}"},
    )
    return embeddings_response.json()


def update_agent_setting(
    agent_id: str,
    setting_key: str,
    setting_value: str,
    agent_lab_endpoint: str = DEFAULT_AGENT_LAB_ENDPOINT,
) -> dict:
    update_setting_response = requests.post(
        f"{agent_lab_endpoint}/agents/update_setting",
        json={
            "agent_id": agent_id,
            "setting_key": setting_key,
            "setting_value": setting_value,
        },
        headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN', 'x')}"},
    )
    return update_setting_response.json()


def openai_responses_api_mcp_tool_request(
    query: str,
    mcp_server: dict,
    model: str = "gpt-5-nano",
    reasoning: dict = {"effort": "low", "summary": "auto"},
) -> dict:
    response = requests.post(
        url="https://api.openai.com/v1/responses",
        headers={
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "tools": [mcp_server],
            "reasoning": reasoning,
            "input": query,
        },
    )

    return response.json()
