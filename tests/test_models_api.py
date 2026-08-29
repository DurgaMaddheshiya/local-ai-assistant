"""
Tests for the models API with mocked Ollama
"""
from unittest.mock import AsyncMock, patch

MOCK_MODELS = [
    {
        "name": "qwen2.5:3b",
        "size": "2.0 GB",
        "modified_at": "2024-01-01T00:00:00",
        "digest": "abc123",
        "details": {}
    },
    {
        "name": "llama3.2:3b",
        "size": "1.9 GB",
        "modified_at": "2024-01-02T00:00:00",
        "digest": "def456",
        "details": {}
    }
]


def patch_ollama_available(models=MOCK_MODELS):
    """Helper to patch Ollama as connected with models"""
    return [
        patch(
            "backend.services.llm.OllamaService.check_connection",
            new_callable=AsyncMock,
            return_value={"status": "connected"}
        ),
        patch(
            "backend.services.llm.OllamaService.get_models",
            new_callable=AsyncMock,
            return_value=models
        )
    ]


class TestGetModels:

    def test_get_models_when_ollama_connected(self, client):
        with patch(
            "backend.services.llm.OllamaService.check_connection",
            new_callable=AsyncMock,
            return_value={"status": "connected"}
        ):
            with patch(
                "backend.services.llm.OllamaService.get_models",
                new_callable=AsyncMock,
                return_value=MOCK_MODELS
            ):
                response = client.get("/api/models")
                assert response.status_code == 200

    def test_get_models_returns_models_list(self, client):
        with patch(
            "backend.services.llm.OllamaService.check_connection",
            new_callable=AsyncMock,
            return_value={"status": "connected"}
        ):
            with patch(
                "backend.services.llm.OllamaService.get_models",
                new_callable=AsyncMock,
                return_value=MOCK_MODELS
            ):
                response = client.get("/api/models")
                data = response.json()
                assert "models" in data
                assert len(data["models"]) == 2

    def test_get_models_returns_503_when_ollama_down(self, client):
        with patch(
            "backend.services.llm.OllamaService.check_connection",
            new_callable=AsyncMock,
            return_value={"status": "disconnected", "error": "Refused"}
        ):
            response = client.get("/api/models")
            assert response.status_code == 503

    def test_model_has_name_field(self, client):
        with patch(
            "backend.services.llm.OllamaService.check_connection",
            new_callable=AsyncMock,
            return_value={"status": "connected"}
        ):
            with patch(
                "backend.services.llm.OllamaService.get_models",
                new_callable=AsyncMock,
                return_value=MOCK_MODELS
            ):
                response = client.get("/api/models")
                models = response.json()["models"]
                for model in models:
                    assert "name" in model


class TestSelectModel:

    def test_select_existing_model(self, client):
        with patch(
            "backend.services.llm.OllamaService.set_model",
            new_callable=AsyncMock,
            return_value=True
        ):
            response = client.post(
                "/api/models/select",
                json={"model": "qwen2.5:3b"}
            )
            assert response.status_code == 200

    def test_select_model_returns_model_name(self, client):
        with patch(
            "backend.services.llm.OllamaService.set_model",
            new_callable=AsyncMock,
            return_value=True
        ):
            response = client.post(
                "/api/models/select",
                json={"model": "qwen2.5:3b"}
            )
            data = response.json()
            assert data["model"] == "qwen2.5:3b"

    def test_select_nonexistent_model_returns_404(self, client):
        with patch(
            "backend.services.llm.OllamaService.set_model",
            new_callable=AsyncMock,
            return_value=False
        ):
            with patch(
                "backend.services.llm.OllamaService.get_models",
                new_callable=AsyncMock,
                return_value=MOCK_MODELS
            ):
                response = client.post(
                    "/api/models/select",
                    json={"model": "nonexistent:model"}
                )
                assert response.status_code == 404

    def test_select_model_missing_field_rejected(self, client):
        response = client.post("/api/models/select", json={})
        assert response.status_code == 422
