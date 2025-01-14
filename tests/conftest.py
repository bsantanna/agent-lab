import os

import pytest
from testcontainers.core.waiting_utils import wait_for_logs
from testcontainers.redis import RedisContainer
from testcontainers.vault import VaultContainer

redis = RedisContainer("redis:alpine").with_bind_ports(container=6379, host=16379)

vault = (
    VaultContainer("hashicorp/vault:1.18.1")
    .with_bind_ports(container=8200, host=18200)
    .with_env("VAULT_DEV_ROOT_TOKEN_ID", "dev-only-token")
    .with_env("VAULT_DEV_LISTEN_ADDRESS", "0.0.0.0:8200")
)

os.environ["TESTING"] = "1"


@pytest.fixture(scope="session", autouse=True)
def test_config(request):
    redis.start()
    vault.start()

    def remove_container():
        redis.stop()
        vault.stop()

    request.addfinalizer(remove_container)
    wait_for_logs(redis, "Ready to accept connections")
    wait_for_logs(
        vault, "Development mode should NOT be used in production installations!"
    )
    yield
