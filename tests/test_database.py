import tempfile
import os
import pytest


@pytest.fixture(autouse=True)
def temp_db():
    from src.config.settings import settings
    old_path = settings.DATABASE_PATH
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_path = f.name
    settings.DATABASE_PATH = temp_path
    from src.data.database import init_db, _db_path
    import src.data.database as db_module
    db_module._db_path = None
    init_db()
    yield
    settings.DATABASE_PATH = old_path
    db_module._db_path = None
    os.unlink(temp_path)


def _insert_message(session_id, role, content, timestamp):
    from src.data.database import get_connection
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO conversations (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
            (session_id, role, content, timestamp),
        )
        conn.commit()


class TestDatabaseCRUD:
    def test_create_and_get_session(self):
        from src.data.database import create_session, get_session
        session = create_session("test-123", "Test Customer")
        assert session["id"] == "test-123"
        assert session["customer_name"] == "Test Customer"
        assert session["status"] == "active"

        retrieved = get_session("test-123")
        assert retrieved is not None
        assert retrieved["id"] == "test-123"

    def test_get_nonexistent_session(self):
        from src.data.database import get_session
        result = get_session("nonexistent")
        assert result is None

    def test_save_and_get_messages(self):
        from src.data.database import create_session, get_conversation_history
        create_session("msg-test", "")
        _insert_message("msg-test", "user", "Hello", "2026-09-03 10:00:00")
        _insert_message("msg-test", "assistant", "Hi there!", "2026-09-03 10:00:01")

        history = get_conversation_history("msg-test")
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Hello"
        assert history[1]["role"] == "assistant"
        assert history[1]["content"] == "Hi there!"

    def test_get_conversation_history_max_messages(self):
        from src.data.database import create_session, get_conversation_history
        create_session("max-test", "")
        for i in range(10):
            ts = f"2026-09-03 10:00:{i:02d}"
            _insert_message("max-test", "user", f"Message {i}", ts)

        history = get_conversation_history("max-test", max_messages=5)
        assert len(history) == 5
        assert history[0]["content"] == "Message 5"
        assert history[4]["content"] == "Message 9"

    def test_search_products_empty_database(self):
        from src.data.database import search_products
        results = search_products("anything")
        assert results == []

    def test_create_quote(self):
        from src.data.database import create_quote
        result = create_quote("Q-001", "session-1", "[]", 100000.0, "2026-12-31")
        assert result["id"] == "Q-001"
        assert result["total_price"] == 100000.0
        assert result["status"] == "pending"
