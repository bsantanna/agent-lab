import os
from uuid import uuid4
from IPython.display import Image, display
import requests
from langchain_core.runnables.graph import MermaidDrawMethod


def print_graph(graph):
    display(
        Image(
            graph.get_graph(xray=True).draw_mermaid_png(
                draw_method=MermaidDrawMethod.PYPPETEER
            )
        )
    )


def create_llm_with_integration(
    llm_tag: str,
    integration_params: dict,
    agent_lab_endpoint: str = "http://localhost:18000",
):
    integration_response = requests.post(
        f"{agent_lab_endpoint}/integrations/create",
        json=integration_params,
        headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
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
        headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
    )
    llm_response.raise_for_status()
    return llm_response.json()


def create_agent_with_integration(
    llm_tag: str,
    agent_type: str,
    integration_params: dict,
    agent_lab_endpoint: str = "http://localhost:18000",
):
    llm_result = create_llm_with_integration(
        llm_tag=llm_tag,
        integration_params=integration_params,
        agent_lab_endpoint=agent_lab_endpoint,
    )

    agent_params = {
        "agent_name": f"agent_{uuid4()}",
        "agent_type": agent_type,
        "language_model_id": llm_result["id"],
    }

    agent_response = requests.post(
        f"{agent_lab_endpoint}/agents/create",
        json=agent_params,
        headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
    )
    agent_response.raise_for_status()
    agent_result = agent_response.json()

    return agent_result


def create_ollama_agent(
    llm_tag: str = "smollm2",
    agent_type: str = "test_echo",
    agent_lab_endpoint: str = "http://localhost:18000",
    ollama_endpoint: str = "http://localhost:11434",
) -> str:
    integration_params = {
        "integration_type": "ollama_api_v1",
        "api_endpoint": ollama_endpoint,
        "api_key": "ollama",
    }

    return create_agent_with_integration(
        llm_tag,
        agent_type,
        integration_params,
        agent_lab_endpoint,
    )


def create_openai_agent(
    llm_tag: str = "o1-mini",
    agent_type: str = "test_echo",
    agent_lab_endpoint: str = "http://localhost:18000",
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
    llm_tag: str = "grok-2-latest",
    agent_type: str = "test_echo",
    agent_lab_endpoint: str = "http://localhost:18000",
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


def create_attachment(
    file_path: str,
    content_type: str,
    agent_lab_endpoint: str = "http://localhost:18000",
) -> str:
    with open(file_path, "rb") as file:
        attachment_response = requests.post(
            f"{agent_lab_endpoint}/attachments/upload",
            files={"file": (file_path, file, content_type)},
            headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
        )
        return attachment_response.json()["id"]


def create_embeddings(
    attachment_id: str,
    language_model_id: str,
    collection_name: str,
    agent_lab_endpoint: str = "http://localhost:18000",
) -> dict:
    embeddings_response = requests.post(
        f"{agent_lab_endpoint}/attachments/embeddings",
        json={
            "attachment_id": attachment_id,
            "language_model_id": language_model_id,
            "collection_name": collection_name,
        },
        headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
    )
    return embeddings_response.json()


def update_agent_setting(
    agent_id: str,
    setting_key: str,
    setting_value: str,
    agent_lab_endpoint: str = "http://localhost:18000",
) -> dict:
    update_setting_response = requests.post(
        f"{agent_lab_endpoint}/agents/update_setting",
        json={
            "agent_id": agent_id,
            "setting_key": setting_key,
            "setting_value": setting_value,
        },
        headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
    )
    return update_setting_response.json()
