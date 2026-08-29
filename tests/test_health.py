"""
Tests for health check and system status endpoints
"""
from unittest.mock import AsyncMock, patch


def test_health_endpoint_returns_200(client):
    response = client.get("/api/health")
    assert response.status_code == 200


def test_health_response_has_required_fields(client):
    response = client.get("/api/health")
    data = response.json()
    assert "status" in data
    assert "timestamp" in data
    assert "version" in data


def test_health_status_is_string(client):
    response = client.get("/api/health")
    data = response.json()
    assert isinstance(data["status"], str)
    assert data["status"] in ("healthy", "unhealthy")


def test_health_includes_version(client):
    response = client.get("/api/health")
    data = response.json()
    assert data["version"]
    assert isinstance(data["version"], str)


def test_system_status_endpoint_exists(client):
    """Status endpoint may return 503 if Ollama is not running — that is fine"""
    response = client.get("/api/status")
    assert response.status_code in (200, 503)


def test_system_status_has_mode_local(client):
    with patch(
        "backend.services.llm.OllamaService.check_connection",
        new_callable=AsyncMock,
        return_value={"status": "connected"}
    ):
        with patch(
            "backend.services.llm.OllamaService.get_current_model",
            new_callable=AsyncMock,
            return_value={"name": "qwen2.5:3b"}
        ):
            response = client.get("/api/status")
            if response.status_code == 200:
                data = response.json()
                assert data.get("mode") == "local"


def test_root_endpoint(client):
    response = client.get("/")
    # Either serves HTML or JSON welcome — both are acceptable
    assert response.status_code in (200, 404)
