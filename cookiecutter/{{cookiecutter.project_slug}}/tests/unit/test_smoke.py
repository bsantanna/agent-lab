"""Boots the app without any live infrastructure.

tests/conftest.py sets TESTING=1, so create_app() reads config-test.yml.
Database/vault/redis connections are created lazily from its syntactically
valid URLs — these tests run in seconds with no containers.
"""

from fastapi.testclient import TestClient

from agent_lab.interface.mcp import prompt_registration, tool_registration
from agent_lab.services.agent_types import registration

from {{ cookiecutter.package_name }}.main import app

client = TestClient(app)


def test_app_boots_and_status_route_present():
    response = client.get("/status/liveness")
    assert response.status_code == 200


def test_example_agents_are_registered():
    assert registration.is_registered("{{ cookiecutter.package_name }}_echo")


def test_agent_types_endpoint_resolves_dependency_injection():
    # Exercises a DI-injected endpoint (no database needed): fails if the
    # framework endpoint modules are not wired to this project's Container.
    response = client.get("/agents/types", headers={"Authorization": "Bearer dummy"})
    assert response.status_code == 200
    assert "{{ cookiecutter.package_name }}_echo" in response.json()


def test_example_mcp_tool_is_registered():
    tool_names = {tool.name for tool in tool_registration.registered_tools()}
    assert "{{ cookiecutter.package_name }}_hello_tool" in tool_names


def test_example_mcp_prompt_is_registered():
    prompt_names = {prompt.name for prompt in prompt_registration.registered_prompts()}
    assert "{{ cookiecutter.package_name }}_greeting_prompt" in prompt_names
