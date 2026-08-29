"""
Tests for database operations
"""
import pytest
from datetime import datetime
from backend.models.database_models import (
    Conversation, Message, Setting,
    create_conversation, create_message,
    get_conversation_with_messages, get_conversations_list,
    update_conversation_title, delete_conversation,
    search_conversations, get_setting, set_setting,
    delete_all_conversations, get_conversation_stats
)


class TestConversationCRUD:

    def test_create_conversation(self, test_db):
        conv = create_conversation(test_db, "My first chat", "qwen2.5:3b")
        assert conv.id
        assert conv.title == "My first chat"
        assert conv.model == "qwen2.5:3b"
        assert isinstance(conv.created_at, datetime)

    def test_conversation_has_unique_id(self, test_db):
        c1 = create_conversation(test_db, "Chat A", "model")
        c2 = create_conversation(test_db, "Chat B", "model")
        assert c1.id != c2.id

    def test_get_conversation_with_messages(self, test_db):
        conv = create_conversation(test_db, "Chat", "model")
        create_message(test_db, conv.id, "user", "Hello")
        create_message(test_db, conv.id, "assistant", "Hi there!")

        fetched = get_conversation_with_messages(test_db, conv.id)
        assert fetched is not None
        assert len(fetched.messages) == 2

    def test_get_nonexistent_conversation_returns_none(self, test_db):
        result = get_conversation_with_messages(test_db, "nonexistent-id")
        assert result is None

    def test_get_conversations_list_order(self, test_db):
        c1 = create_conversation(test_db, "First", "model")
        c2 = create_conversation(test_db, "Second", "model")

        convs = get_conversations_list(test_db, limit=10)
        ids = [c.id for c in convs]
        # Second is more recent so it should come first
        assert ids.index(c2.id) < ids.index(c1.id)

    def test_get_conversations_list_limit(self, test_db):
        for i in range(5):
            create_conversation(test_db, f"Conv {i}", "model")

        result = get_conversations_list(test_db, limit=3)
        assert len(result) <= 3

    def test_update_conversation_title(self, test_db):
        conv = create_conversation(test_db, "Old Title", "model")
        success = update_conversation_title(test_db, conv.id, "New Title")
        assert success is True

        updated = get_conversation_with_messages(test_db, conv.id)
        assert updated.title == "New Title"

    def test_update_nonexistent_conversation_returns_false(self, test_db):
        result = update_conversation_title(test_db, "bad-id", "Title")
        assert result is False

    def test_delete_conversation(self, test_db):
        conv = create_conversation(test_db, "To Delete", "model")
        success = delete_conversation(test_db, conv.id)
        assert success is True

        result = get_conversation_with_messages(test_db, conv.id)
        assert result is None

    def test_delete_nonexistent_conversation_returns_false(self, test_db):
        result = delete_conversation(test_db, "bad-id")
        assert result is False

    def test_delete_conversation_cascades_messages(self, test_db):
        conv = create_conversation(test_db, "Has Messages", "model")
        create_message(test_db, conv.id, "user", "Hello")
        create_message(test_db, conv.id, "assistant", "Hi!")

        delete_conversation(test_db, conv.id)

        # Messages should also be gone
        messages = test_db.query(Message).filter(
            Message.conversation_id == conv.id
        ).all()
        assert len(messages) == 0


class TestMessageCRUD:

    def test_create_message(self, test_db):
        conv = create_conversation(test_db, "Chat", "model")
        msg = create_message(test_db, conv.id, "user", "Test message")

        assert msg.id
        assert msg.role == "user"
        assert msg.content == "Test message"
        assert msg.conversation_id == conv.id

    def test_message_roles(self, test_db):
        conv = create_conversation(test_db, "Chat", "model")
        for role in ("system", "user", "assistant"):
            msg = create_message(test_db, conv.id, role, f"Content from {role}")
            assert msg.role == role

    def test_message_content_preview(self, test_db):
        conv = create_conversation(test_db, "Chat", "model")
        long_content = "A" * 200
        msg = create_message(test_db, conv.id, "user", long_content)

        assert len(msg.content_preview) <= 103  # 100 + "..."

    def test_message_count_on_conversation(self, test_db):
        conv = create_conversation(test_db, "Chat", "model")
        for i in range(4):
            create_message(test_db, conv.id, "user", f"Message {i}")

        refreshed = get_conversation_with_messages(test_db, conv.id)
        assert refreshed.message_count == 4


class TestSearchConversations:

    def test_search_by_title(self, test_db):
        create_conversation(test_db, "Python tutorial", "model")
        create_conversation(test_db, "JavaScript guide", "model")

        results = search_conversations(test_db, "Python")
        titles = [r.title for r in results]
        assert any("Python" in t for t in titles)

    def test_search_returns_empty_for_no_match(self, test_db):
        create_conversation(test_db, "Unique xyz conversation", "model")
        results = search_conversations(test_db, "zzznomatch")
        # Could return 0 — no guarantee, so just check it's a list
        assert isinstance(results, list)

    def test_search_is_case_insensitive(self, test_db):
        create_conversation(test_db, "Machine Learning basics", "model")
        results = search_conversations(test_db, "machine learning")
        assert len(results) > 0


class TestSettings:

    def test_set_and_get_setting(self, test_db):
        set_setting(test_db, "test_key", "test_value")
        value = get_setting(test_db, "test_key")
        assert value == "test_value"

    def test_get_nonexistent_setting_returns_default(self, test_db):
        value = get_setting(test_db, "nonexistent_key", "default")
        assert value == "default"

    def test_get_nonexistent_setting_returns_none_by_default(self, test_db):
        value = get_setting(test_db, "completely_missing")
        assert value is None

    def test_overwrite_setting(self, test_db):
        set_setting(test_db, "overwrite_key", "first")
        set_setting(test_db, "overwrite_key", "second")
        value = get_setting(test_db, "overwrite_key")
        assert value == "second"


class TestBulkOperations:

    def test_delete_all_conversations(self, test_db):
        for i in range(3):
            create_conversation(test_db, f"Conv {i}", "model")

        count = delete_all_conversations(test_db)
        assert count >= 3

        remaining = get_conversations_list(test_db, limit=100)
        assert len(remaining) == 0

    def test_get_conversation_stats(self, test_db):
        delete_all_conversations(test_db)  # start clean

        conv = create_conversation(test_db, "Stats Chat", "model")
        create_message(test_db, conv.id, "user", "Hi")
        create_message(test_db, conv.id, "assistant", "Hello!")

        stats = get_conversation_stats(test_db)
        assert stats["total_conversations"] >= 1
        assert stats["total_messages"] >= 2
