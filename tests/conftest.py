import os
from pathlib import Path

import pytest
from testcontainers.core.waiting_utils import wait_for_logs
from testcontainers.ollama import OllamaContainer
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer
from testcontainers.vault import VaultContainer

os.environ["TESTING"] = "1"
os.environ["OLLAMA_ENDPOINT"] = "http://localhost:21434"

llm_tag = "bge-m3"

ollama = OllamaContainer(
    ollama_home=f"{Path.home()}/.ollama", image="ollama/ollama:latest"
).with_bind_ports(container=11434, host=21434)

postgres = (
    PostgresContainer(
        image="pgvector/pgvector:pg16", username="postgres", password="postgres"
    )
    .with_bind_ports(container=5432, host=15432)
    .with_volume_mapping(f"{Path.cwd()}/tests/integration", "/mnt/integration")
)

redis = RedisContainer(image="redis:alpine").with_bind_ports(container=6379, host=16379)

vault = (
    VaultContainer("hashicorp/vault:1.18.1")
    .with_bind_ports(container=8200, host=18200)
    .with_env("VAULT_DEV_ROOT_TOKEN_ID", "dev-only-token")
    .with_env("VAULT_DEV_LISTEN_ADDRESS", "0.0.0.0:8200")
)


@pytest.fixture(scope="session", autouse=True)
def test_config(request):
    ollama.start()
    postgres.start()
    redis.start()
    vault.start()

    def remove_container():
        ollama.stop()
        postgres.stop()
        redis.stop()
        vault.stop()

    request.addfinalizer(remove_container)
    wait_for_logs(ollama, "Listening on")
    wait_for_logs(postgres, "database system is ready to accept connections")
    wait_for_logs(redis, "Ready to accept connections")
    wait_for_logs(
        vault, "Development mode should NOT be used in production installations!"
    )

    # setup databases
    psql_command = "PGPASSWORD='postgres' psql --username postgres --host 127.0.0.1"
    create_database_command = f"{psql_command} -c 'create database ?;'"
    main_db_command = create_database_command.replace("?", "agent_lab")
    checkpoints_db_command = create_database_command.replace(
        "?", "agent_lab_checkpoints"
    )
    vectors_db_command = create_database_command.replace("?", "agent_lab_vectors")
    copy_dump_command = "cp /mnt/integration/pgvector_dump.sql.gz /tmp/ && gunzip /tmp/pgvector_dump.sql.gz"
    restore_dump_command = (
        f"{psql_command} -d agent_lab_vectors < /tmp/pgvector_dump.sql"
    )

    postgres.exec(
        [
            "sh",
            "-c",
            f"""
            {main_db_command} &&
            {checkpoints_db_command} &&
            {vectors_db_command} &&
            {copy_dump_command} &&
            {restore_dump_command}
            """,
        ]
    )

    # pull llm from registry
    if llm_tag not in [e["name"] for e in ollama.list_models()]:
        print(f"Pulling {llm_tag} model")
        ollama.pull_model(llm_tag)

    yield
