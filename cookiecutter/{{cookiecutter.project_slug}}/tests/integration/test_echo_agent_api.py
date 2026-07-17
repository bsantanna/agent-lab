from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from {{ cookiecutter.package_name }}.main import app

# Every route carries an HTTPBearer dependency even with auth disabled, so
# any bearer value satisfies it.
AUTH_HEADERS = {"Authorization": "Bearer dummy"}


@pytest.fixture(scope="module")
def client():
    yield TestClient(app)


def create_agent(client) -> dict:
    integration = client.post(
        "/integrations/create",
        headers=AUTH_HEADERS,
        json={
            "api_endpoint": "https://example.com",
            "api_key": "an_invalid_key",
            "integration_type": "openai_api_v1",
        },
    ).json()
    language_model = client.post(
        "/llms/create",
        headers=AUTH_HEADERS,
        json={
            "integration_id": integration["id"],
            "language_model_tag": "an_invalid_tag",
        },
    ).json()
    return client.post(
        "/agents/create",
        headers=AUTH_HEADERS,
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
        headers=AUTH_HEADERS,
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
