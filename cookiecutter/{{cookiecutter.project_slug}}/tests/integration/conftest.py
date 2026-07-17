import os

import pytest
from testcontainers.core.wait_strategies import LogMessageWaitStrategy
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer
from testcontainers.vault import VaultContainer

os.environ["TESTING"] = "1"

postgres = (
    PostgresContainer(
        image="pgvector/pgvector:pg16", username="postgres", password="postgres"
    )
    .with_bind_ports(container=5432, host=15432)
    .waiting_for(
        LogMessageWaitStrategy("database system is ready to accept connections")
    )
)

redis = (
    RedisContainer(image="redis:alpine")
    .with_bind_ports(container=6379, host=16379)
    .waiting_for(LogMessageWaitStrategy("Ready to accept connections"))
)

vault = (
    VaultContainer("hashicorp/vault:1.18.1")
    .with_bind_ports(container=8200, host=18200)
    .with_env("VAULT_DEV_ROOT_TOKEN_ID", "dev-only-token")
    .with_env("VAULT_DEV_LISTEN_ADDRESS", "0.0.0.0:8200")
    .waiting_for(
        LogMessageWaitStrategy(
            "Development mode should NOT be used in production installations!"
        )
    )
)


def setup_postgres():
    psql = "PGPASSWORD='postgres' psql --username postgres --host 127.0.0.1"
    for database in (
        "{{ cookiecutter.package_name }}",
        "{{ cookiecutter.package_name }}_checkpoints",
        "{{ cookiecutter.package_name }}_vectors",
    ):
        postgres.exec(["sh", "-c", f"{psql} -c 'create database {database};'"])


@pytest.fixture(scope="session", autouse=True)
def test_containers(request):
    postgres.start()
    redis.start()
    vault.start()

    def stop():
        postgres.stop()
        redis.stop()
        vault.stop()

    request.addfinalizer(stop)
    setup_postgres()
    yield
