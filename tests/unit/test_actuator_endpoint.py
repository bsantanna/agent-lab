import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    yield TestClient(app)

def test_health_check(client):
    response = client.get("/actuator/health")
    assert response.status_code == 200
    assert response.json() == {"msg": "success"}

def test_metrics(client):
    response = client.get("/actuator/metrics")
    assert response.status_code == 200, "The /metrics endpoint should return 200"
    data = response.json()

    assert "application" in data, "The response should contain the 'application' key"
    assert "uptime_seconds" in data["application"], "It should contain 'uptime_seconds'"
    assert "startup_time" in data["application"], "It should contain 'startup_time'"

    assert "system" in data, "The response should contain the 'system' key"
    assert "cpu_usage_percent" in data["system"], "It should contain 'cpu_usage_percent'"
    assert "memory" in data["system"], "It should contain memory information"
    assert "disk" in data["system"], "It should contain disk information"

    assert "threads" in data, "The response should contain the 'threads' key"
    assert "active_count" in data["threads"], "It should contain 'active_count'"


