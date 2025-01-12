import os

import pytest
from testcontainers.core.waiting_utils import wait_for_logs
from testcontainers.redis import RedisContainer
from testcontainers.vault import VaultContainer

redis = RedisContainer("redis:alpine").with_exposed_ports(16379)
vault = VaultContainer("hashicorp/vault:1.18.1").with_exposed_ports(18200)

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

    yield
