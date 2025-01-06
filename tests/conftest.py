import os
import pytest

from testcontainers.core.waiting_utils import wait_for_logs
from testcontainers.redis import RedisContainer

redis = RedisContainer("redis:latest").with_exposed_ports(16379)
os.environ["TESTING"] = "1"

@pytest.fixture(scope="session", autouse=True)
def test_config(request):

    redis.start()

    def remove_container():
        redis.stop()

    request.addfinalizer(remove_container)
    wait_for_logs(redis, "Ready to accept connections")

    yield
