from uuid import uuid4
from IPython.display import Image, display
import requests


def print_graph(graph):
    display(Image(graph.get_graph(xray=True).draw_mermaid_png()))


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
