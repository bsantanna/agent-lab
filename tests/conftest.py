import os
from pathlib import Path

import pytest
from testcontainers.core.waiting_utils import wait_for_logs
from testcontainers.postgres import PostgresContainer
from testcontainers.vault import VaultContainer

os.environ["TESTING"] = "1"
os.environ["OLLAMA_ENDPOINT"] = "http://localhost:11434"
os.environ["OLLAMA_MODEL"] = "mistral-small:24b"

postgres = (
    PostgresContainer(
        image="pgvector/pgvector:pg16", username="postgres", password="postgres"
    )
    .with_bind_ports(container=5432, host=15432)
    .with_volume_mapping(f"{Path.cwd()}/tests/integration", "/mnt/integration")
)
vault = (
    VaultContainer("hashicorp/vault:1.18.1")
    .with_bind_ports(container=8200, host=18200)
    .with_env("VAULT_DEV_ROOT_TOKEN_ID", "dev-only-token")
    .with_env("VAULT_DEV_LISTEN_ADDRESS", "0.0.0.0:8200")
)


@pytest.fixture(scope="session", autouse=True)
def test_config(request):
    postgres.start()
    vault.start()

    def remove_container():
        postgres.stop()
        vault.stop()

    request.addfinalizer(remove_container)
    wait_for_logs(postgres, "database system is ready to accept connections")
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

    yield
