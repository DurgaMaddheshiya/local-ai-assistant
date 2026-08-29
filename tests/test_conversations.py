"""
Tests for the conversations REST API
"""
import pytest


class TestListConversations:

    def test_get_conversations_returns_200(self, client):
        response = client.get("/api/conversations")
        assert response.status_code == 200

    def test_get_conversations_returns_list(self, client):
        response = client.get("/api/conversations")
        assert isinstance(response.json(), list)

    def test_get_conversations_limit(self, client):
        response = client.get("/api/conversations?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 5

    def test_search_conversations(self, client, sample_conversation):
        response = client.get("/api/conversations?search=Test")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestCreateConversation:

    def test_create_conversation_returns_201_or_200(self, client):
        response = client.post("/api/conversations", json={"title": "New Chat"})
        assert response.status_code in (200, 201)

    def test_create_conversation_returns_id(self, client):
        response = client.post("/api/conversations", json={"title": "Test"})
        data = response.json()
        assert "id" in data
        assert data["id"]

    def test_create_conversation_stores_title(self, client):
        response = client.post("/api/conversations", json={"title": "My Conversation"})
        data = response.json()
        assert data["title"] == "My Conversation"

    def test_create_conversation_with_model(self, client):
        response = client.post(
            "/api/conversations",
            json={"title": "With Model", "model": "qwen2.5:3b"}
        )
        assert response.status_code in (200, 201)
        data = response.json()
        assert data["model"] == "qwen2.5:3b"

    def test_create_conversation_missing_title_fails(self, client):
        response = client.post("/api/conversations", json={})
        assert response.status_code == 422


class TestGetConversation:

    def test_get_conversation_by_id(self, client, sample_conversation):
        response = client.get(f"/api/conversations/{sample_conversation.id}")
        assert response.status_code == 200

    def test_get_conversation_has_messages(self, client, sample_conversation):
        response = client.get(f"/api/conversations/{sample_conversation.id}")
        data = response.json()
        assert "messages" in data
        assert isinstance(data["messages"], list)
        assert len(data["messages"]) > 0

    def test_get_conversation_message_fields(self, client, sample_conversation):
        response = client.get(f"/api/conversations/{sample_conversation.id}")
        messages = response.json()["messages"]
        for msg in messages:
            assert "id" in msg
            assert "role" in msg
            assert "content" in msg
            assert "created_at" in msg

    def test_get_nonexistent_conversation_returns_404(self, client):
        response = client.get("/api/conversations/does-not-exist")
        assert response.status_code == 404


class TestUpdateConversation:

    def test_rename_conversation(self, client, sample_conversation):
        response = client.patch(
            f"/api/conversations/{sample_conversation.id}",
            json={"title": "Renamed Title"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Renamed Title"

    def test_rename_nonexistent_conversation_returns_404(self, client):
        response = client.patch(
            "/api/conversations/nonexistent",
            json={"title": "New Title"}
        )
        assert response.status_code == 404


class TestDeleteConversation:

    def test_delete_conversation(self, client):
        # Create a conversation to delete
        create_resp = client.post("/api/conversations", json={"title": "To Delete"})
        conv_id = create_resp.json()["id"]

        # Delete it
        delete_resp = client.delete(f"/api/conversations/{conv_id}")
        assert delete_resp.status_code == 200

        # Verify it's gone
        get_resp = client.get(f"/api/conversations/{conv_id}")
        assert get_resp.status_code == 404

    def test_delete_nonexistent_conversation_returns_404(self, client):
        response = client.delete("/api/conversations/does-not-exist")
        assert response.status_code == 404

    def test_delete_all_requires_confirm_param(self, client):
        # Without confirm=true it should fail
        response = client.delete("/api/conversations")
        assert response.status_code == 400

    def test_delete_all_with_confirm(self, client):
        response = client.delete("/api/conversations?confirm=true")
        assert response.status_code == 200
        data = response.json()
        assert "deleted_count" in data
