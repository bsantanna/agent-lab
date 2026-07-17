from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from agent_lab import create_app

from {{ cookiecutter.package_name }}.core.container import Container


@pytest.fixture(scope="module")
def client():
    app = create_app(
        container=Container(),
        scan_packages=[
            "{{ cookiecutter.package_name }}.agents",
            "{{ cookiecutter.package_name }}.mcp",
        ],
    )
    yield TestClient(app)


def create_agent(client) -> dict:
    integration = client.post(
        "/integrations/create",
        json={
            "api_endpoint": "https://example.com",
            "api_key": "an_invalid_key",
            "integration_type": "openai_api_v1",
        },
    ).json()
    language_model = client.post(
        "/llms/create",
        json={
            "integration_id": integration["id"],
            "language_model_tag": "an_invalid_tag",
        },
    ).json()
    return client.post(
        "/agents/create",
        json={
            "language_model_id": language_model["id"],
            "agent_type": "{{ cookiecutter.package_name }}_echo",
            "agent_name": f"agent-{uuid4()}",
        },
    ).json()


def test_echo_agent_replies_through_the_api(client):
    agent = create_agent(client)

    response = client.post(
        "/messages/post",
        json={
            "message_role": "human",
            "message_content": "hello",
            "agent_id": agent["id"],
            "attachment_id": None,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["message_role"] == "assistant"
    assert body["message_content"] == "Echo: hello"
