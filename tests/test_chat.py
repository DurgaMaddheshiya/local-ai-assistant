"""
Tests for the chat endpoint with mocked Ollama service
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

MOCK_STREAM_CHUNKS = [
    {"content": "Hello", "done": False},
    {"content": " there!", "done": False},
    {"content": "", "done": True}
]


async def mock_stream_generator(*args, **kwargs):
    """Async generator that yields fake LLM chunks"""
    for chunk in MOCK_STREAM_CHUNKS:
        yield chunk


def mock_ollama_connected():
    return {"status": "connected", "url": "http://127.0.0.1:11434"}


def mock_ollama_disconnected():
    return {"status": "disconnected", "error": "Connection refused"}


# ------------------------------------------------------------------
# Chat request validation
# ------------------------------------------------------------------

class TestChatRequestValidation:

    def test_empty_message_rejected(self, client):
        with patch(
            "backend.services.llm.OllamaService.check_connection",
            new_callable=AsyncMock,
            return_value=mock_ollama_connected()
        ):
            response = client.post("/api/chat", json={"message": "", "stream": False})
            assert response.status_code == 422

    def test_missing_message_field_rejected(self, client):
        response = client.post("/api/chat", json={"stream": False})
        assert response.status_code == 422

    def test_invalid_temperature_rejected(self, client):
        response = client.post(
            "/api/chat",
            json={"message": "Hi", "temperature": 5.0, "stream": False}
        )
        assert response.status_code == 422


# ------------------------------------------------------------------
# Ollama unavailable
# ------------------------------------------------------------------

class TestChatOllamaUnavailable:

    def test_returns_503_when_ollama_down(self, client):
        with patch(
            "backend.services.llm.OllamaService.check_connection",
            new_callable=AsyncMock,
            return_value=mock_ollama_disconnected()
        ):
            response = client.post(
                "/api/chat",
                json={"message": "Hello", "stream": False}
            )
            assert response.status_code == 503

    def test_503_response_has_error_field(self, client):
        with patch(
            "backend.services.llm.OllamaService.check_connection",
            new_callable=AsyncMock,
            return_value=mock_ollama_disconnected()
        ):
            response = client.post(
                "/api/chat",
                json={"message": "Hello", "stream": False}
            )
            data = response.json()
            assert "error" in data


# ------------------------------------------------------------------
# Non-streaming chat
# ------------------------------------------------------------------

class TestChatNonStreaming:

    def test_non_streaming_response_has_conversation_id(self, client):
        with patch(
            "backend.services.llm.OllamaService.check_connection",
            new_callable=AsyncMock,
            return_value=mock_ollama_connected()
        ):
            with patch(
                "backend.services.llm.OllamaService.set_model",
                new_callable=AsyncMock,
                return_value=True
            ):
                with patch(
                    "backend.services.llm.OllamaService.generate_single_response",
                    new_callable=AsyncMock,
                    return_value={"content": "Hello there!", "model": "qwen2.5:3b"}
                ):
                    response = client.post(
                        "/api/chat",
                        json={"message": "Hi", "stream": False}
                    )
                    assert response.status_code == 200
                    data = response.json()
                    assert "conversation_id" in data

    def test_non_streaming_response_has_content(self, client):
        with patch(
            "backend.services.llm.OllamaService.check_connection",
            new_callable=AsyncMock,
            return_value=mock_ollama_connected()
        ):
            with patch(
                "backend.services.llm.OllamaService.set_model",
                new_callable=AsyncMock,
                return_value=True
            ):
                with patch(
                    "backend.services.llm.OllamaService.generate_single_response",
                    new_callable=AsyncMock,
                    return_value={"content": "The answer is 42.", "model": "qwen2.5:3b"}
                ):
                    response = client.post(
                        "/api/chat",
                        json={"message": "What is 42?", "stream": False}
                    )
                    data = response.json()
                    assert data.get("content") == "The answer is 42."

    def test_non_streaming_creates_new_conversation(self, client):
        with patch(
            "backend.services.llm.OllamaService.check_connection",
            new_callable=AsyncMock,
            return_value=mock_ollama_connected()
        ):
            with patch(
                "backend.services.llm.OllamaService.set_model",
                new_callable=AsyncMock,
                return_value=True
            ):
                with patch(
                    "backend.services.llm.OllamaService.generate_single_response",
                    new_callable=AsyncMock,
                    return_value={"content": "Sure!", "model": "qwen2.5:3b"}
                ):
                    response = client.post(
                        "/api/chat",
                        json={"message": "Create a new conversation", "stream": False}
                    )
                    assert response.status_code == 200
                    data = response.json()
                    conv_id = data["conversation_id"]
                    assert conv_id

                    # Verify conversation exists
                    conv_response = client.get(f"/api/conversations/{conv_id}")
                    assert conv_response.status_code == 200

    def test_non_streaming_continues_existing_conversation(self, client, sample_conversation):
        with patch(
            "backend.services.llm.OllamaService.check_connection",
            new_callable=AsyncMock,
            return_value=mock_ollama_connected()
        ):
            with patch(
                "backend.services.llm.OllamaService.set_model",
                new_callable=AsyncMock,
                return_value=True
            ):
                with patch(
                    "backend.services.llm.OllamaService.generate_single_response",
                    new_callable=AsyncMock,
                    return_value={"content": "Continuing...", "model": "qwen2.5:3b"}
                ):
                    response = client.post(
                        "/api/chat",
                        json={
                            "message": "Continue please",
                            "conversation_id": sample_conversation.id,
                            "stream": False
                        }
                    )
                    assert response.status_code == 200
                    data = response.json()
                    assert data["conversation_id"] == sample_conversation.id

    def test_invalid_conversation_id_returns_404(self, client):
        with patch(
            "backend.services.llm.OllamaService.check_connection",
            new_callable=AsyncMock,
            return_value=mock_ollama_connected()
        ):
            response = client.post(
                "/api/chat",
                json={
                    "message": "Hello",
                    "conversation_id": "nonexistent-id",
                    "stream": False
                }
            )
            assert response.status_code == 404


# ------------------------------------------------------------------
# Message persistence
# ------------------------------------------------------------------

class TestChatPersistence:

    def test_user_message_saved_to_db(self, client):
        with patch(
            "backend.services.llm.OllamaService.check_connection",
            new_callable=AsyncMock,
            return_value=mock_ollama_connected()
        ):
            with patch(
                "backend.services.llm.OllamaService.set_model",
                new_callable=AsyncMock,
                return_value=True
            ):
                with patch(
                    "backend.services.llm.OllamaService.generate_single_response",
                    new_callable=AsyncMock,
                    return_value={"content": "Got it.", "model": "qwen2.5:3b"}
                ):
                    response = client.post(
                        "/api/chat",
                        json={"message": "Save this message", "stream": False}
                    )
                    assert response.status_code == 200
                    conv_id = response.json()["conversation_id"]

                    # Retrieve conversation and verify message was stored
                    conv_response = client.get(f"/api/conversations/{conv_id}")
                    messages = conv_response.json()["messages"]
                    user_messages = [m for m in messages if m["role"] == "user"]
                    assert any("Save this message" in m["content"] for m in user_messages)

    def test_assistant_response_saved_to_db(self, client):
        with patch(
            "backend.services.llm.OllamaService.check_connection",
            new_callable=AsyncMock,
            return_value=mock_ollama_connected()
        ):
            with patch(
                "backend.services.llm.OllamaService.set_model",
                new_callable=AsyncMock,
                return_value=True
            ):
                with patch(
                    "backend.services.llm.OllamaService.generate_single_response",
                    new_callable=AsyncMock,
                    return_value={"content": "I am the AI response.", "model": "qwen2.5:3b"}
                ):
                    response = client.post(
                        "/api/chat",
                        json={"message": "Tell me something", "stream": False}
                    )
                    conv_id = response.json()["conversation_id"]

                    conv_response = client.get(f"/api/conversations/{conv_id}")
                    messages = conv_response.json()["messages"]
                    assistant_messages = [m for m in messages if m["role"] == "assistant"]
                    assert any("I am the AI response." in m["content"] for m in assistant_messages)
