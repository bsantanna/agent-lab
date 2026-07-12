import os
from pathlib import Path
from uuid import uuid4

import scenario

from tests.simulation.common.llm_factory import LanguageModelBuilder


def react_rag_agent(client, message_content) -> scenario.AgentReturnTypes:
    language_model_id = LanguageModelBuilder(client).build()

    # create agent
    response_3 = client.post(
        url="/agents/create",
        headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
        json={
            "language_model_id": language_model_id,
            "agent_type": "react_rag",
            "agent_name": f"agent-{uuid4()}",
        },
    )
    agent_id = response_3.json()["id"]

    # update collection_name to match pgvector dump
    client.post(
        url="/agents/update_setting",
        headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
        json={
            "agent_id": agent_id,
            "setting_key": "collection_name",
            "setting_value": "static_document_data_ollama_embeddings",
        },
    )

    # post message
    response_4 = client.post(
        "/messages/post",
        headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
        json={
            "message_role": "human",
            "message_content": message_content,
            "agent_id": agent_id,
        },
    )
    return response_4.json()["message_content"]


def adaptive_rag_agent(client, message_content) -> scenario.AgentReturnTypes:
    language_model_id = LanguageModelBuilder(client).build()

    # create agent
    response_3 = client.post(
        headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
        url="/agents/create",
        json={
            "language_model_id": language_model_id,
            "agent_type": "adaptive_rag",
            "agent_name": f"agent-{uuid4()}",
        },
    )
    agent_id = response_3.json()["id"]

    # update collection_name to match pgvector dump
    client.post(
        url="/agents/update_setting",
        headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
        json={
            "agent_id": agent_id,
            "setting_key": "collection_name",
            "setting_value": "static_document_data_ollama_embeddings",
        },
    )

    # post message
    response_4 = client.post(
        "/messages/post",
        headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
        json={
            "message_role": "human",
            "message_content": message_content,
            "agent_id": agent_id,
        },
    )
    return response_4.json()["message_content"]


def supervised_agent(client, message_content) -> scenario.AgentReturnTypes:
    language_model_id = LanguageModelBuilder(client).build()

    # create agent
    response_3 = client.post(
        url="/agents/create",
        headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
        json={
            "language_model_id": language_model_id,
            "agent_type": "coordinator_planner_supervisor",
            "agent_name": f"agent-{uuid4()}",
        },
    )
    agent_id = response_3.json()["id"]

    # update collection_name to match pgvector dump
    client.post(
        url="/agents/update_setting",
        headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
        json={
            "agent_id": agent_id,
            "setting_key": "collection_name",
            "setting_value": "static_document_data_ollama_embeddings",
        },
    )

    # post message
    response_4 = client.post(
        "/messages/post",
        headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
        json={
            "message_role": "human",
            "message_content": message_content,
            "agent_id": agent_id,
        },
    )

    return response_4.json()["message_content"]


def web_browser_agent(client, message_content) -> scenario.AgentReturnTypes:
    language_model_id = LanguageModelBuilder(client).build()

    # create agent
    response_3 = client.post(
        url="/agents/create",
        headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
        json={
            "language_model_id": language_model_id,
            "agent_type": "coordinator_planner_supervisor",
            "agent_name": f"agent-{uuid4()}",
        },
    )
    agent_id = response_3.json()["id"]

    # post message
    response_4 = client.post(
        "/messages/post",
        headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
        json={
            "message_role": "human",
            "message_content": message_content,
            "agent_id": agent_id,
        },
    )

    return response_4.json()["message_content"]


def audio_voice_memos_agent(
    client, message_content, agent_type="fast_voice_memos"
) -> scenario.AgentReturnTypes:
    # audio chat input needs openai (LAN model has no audio support)
    language_model_id = (
        LanguageModelBuilder(client)
        .with_integration(
            api_endpoint="https://api.openai.com/v1/",
            api_key=os.environ["OPENAI_API_KEY"],
            integration_type="openai_api_v1",
        )
        .with_model_tag("gpt-5-nano")
        .build()
    )

    # create agent
    response_3 = client.post(
        url="/agents/create",
        headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
        json={
            "language_model_id": language_model_id,
            "agent_type": agent_type,
            "agent_name": f"agent-{uuid4()}",
        },
    )
    agent_id = response_3.json()["id"]

    filename = "voice_memos_01_pt_BR.mp3"
    content_type = "audio/mp3"
    tests_dir = Path(__file__).parent.parent.parent
    file_path = f"{tests_dir}/integration/{filename}"

    # create attachment
    response_4 = None
    with open(file_path, "rb") as file:
        response_4 = client.post(
            url="/attachments/upload",
            headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
            files={"file": (filename, file, content_type)},
        )
    attachment_id = response_4.json()["id"]

    # post message
    response_5 = client.post(
        "/messages/post",
        headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
        json={
            "message_role": "human",
            "message_content": message_content,
            "agent_id": agent_id,
            "attachment_id": attachment_id,
        },
    )

    return response_5.json()["message_content"]


def image_vision_document_agent(client, message_content) -> scenario.AgentReturnTypes:
    language_model_id = LanguageModelBuilder(client).build()

    # create agent
    response_3 = client.post(
        url="/agents/create",
        headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
        json={
            "language_model_id": language_model_id,
            "agent_type": "vision_document",
            "agent_name": f"agent-{uuid4()}",
        },
    )
    agent_id = response_3.json()["id"]
    filename = "vision_document_01.jpg"
    content_type = "image/jpeg"
    tests_dir = Path(__file__).parent.parent.parent
    file_path = f"{tests_dir}/integration/{filename}"

    # create attachment
    response_4 = None
    with open(file_path, "rb") as file:
        response_4 = client.post(
            url="/attachments/upload",
            headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
            files={"file": (filename, file, content_type)},
        )
    attachment_id = response_4.json()["id"]

    # post message
    response_5 = client.post(
        "/messages/post",
        headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
        json={
            "message_role": "human",
            "message_content": message_content,
            "agent_id": agent_id,
            "attachment_id": attachment_id,
        },
    )

    return response_5.json()["message_content"]
