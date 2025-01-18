import os
from pathlib import Path

import pytest
from testcontainers.core.waiting_utils import wait_for_logs
from testcontainers.ollama import OllamaContainer
from testcontainers.vault import VaultContainer

os.environ["TESTING"] = "1"

llm_tag = "smollm2"

ollama = OllamaContainer(ollama_home=f"{Path.home()}/.ollama").with_bind_ports(
    container=11434, host=21434
)


vault = (
    VaultContainer("hashicorp/vault:1.18.1")
    .with_bind_ports(container=8200, host=18200)
    .with_env("VAULT_DEV_ROOT_TOKEN_ID", "dev-only-token")
    .with_env("VAULT_DEV_LISTEN_ADDRESS", "0.0.0.0:8200")
)


@pytest.fixture(scope="session", autouse=True)
def test_config(request):
    ollama.start()
    vault.start()

    def remove_container():
        ollama.stop()
        vault.stop()

    request.addfinalizer(remove_container)
    wait_for_logs(ollama, "Listening on")
    wait_for_logs(
        vault, "Development mode should NOT be used in production installations!"
    )

    if llm_tag not in [e["name"] for e in ollama.list_models()]:
        print(f"Pulling {llm_tag} model")
        ollama.pull_model(llm_tag)

    yield
