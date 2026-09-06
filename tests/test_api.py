import pytest
from unittest.mock import patch, MagicMock
from langchain_core.messages import AIMessage


class TestHealth:
    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestSession:
    def test_create_session(self, client):
        response = client.post("/session", json={"customer_name": "Test User"})
        assert response.status_code == 200
        assert "session_id" in response.json()


class TestChat:
    @patch("src.agents.nodes.get_llm")
    def test_chat_without_session(self, mock_get_llm, client):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = AIMessage(content="Halo! Ada yang bisa dibantu?")
        mock_get_llm.return_value = mock_llm
        response = client.post("/chat", json={"message": "Halo"})
        assert response.status_code == 200
        assert "response" in response.json()
        assert "session_id" in response.json()


class TestChatStream:
    def _make_mock_agent(self, content="Halo!"):
        mock_agent = MagicMock()
        mock_msg = MagicMock()
        mock_msg.content = content
        mock_agent.invoke.return_value = {"messages": [mock_msg]}
        return mock_agent

    @patch("src.api.stream.create_sales_agent")
    @patch("src.api.stream.asyncio")
    def test_chat_stream_endpoint(self, mock_asyncio, mock_create, client):
        mock_agent = self._make_mock_agent()
        mock_create.return_value = mock_agent
        mock_asyncio.to_thread.side_effect = lambda fn, *a, **kw: fn(*a, **kw)
        response = client.post("/chat/stream", json={"message": "Halo"})
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

    @patch("src.api.stream.create_sales_agent")
    @patch("src.api.stream.asyncio")
    def test_chat_stream_with_session(self, mock_asyncio, mock_create, client):
        mock_agent = self._make_mock_agent()
        mock_create.return_value = mock_agent
        mock_asyncio.to_thread.side_effect = lambda fn, *a, **kw: fn(*a, **kw)
        response = client.post("/chat/stream", json={"message": "Halo", "session_id": ""})
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]


class TestInputValidation:
    def test_chat_empty_message(self, client):
        response = client.post("/chat", json={"message": ""})
        assert response.status_code == 422

    def test_chat_missing_message(self, client):
        response = client.post("/chat", json={})
        assert response.status_code == 422

    def test_chat_message_too_long(self, client):
        response = client.post("/chat", json={"message": "x" * 2001})
        assert response.status_code == 422

    def test_chat_invalid_session_id_format(self, client):
        response = client.post("/chat", json={"message": "test", "session_id": "invalid!"})
        assert response.status_code == 422

    def test_get_session_not_found(self, client):
        response = client.get("/session/nonexistent-uuid")
        assert response.status_code == 404

    def test_chat_wrong_content_type(self, client):
        response = client.post("/chat", content="not json", headers={"Content-Type": "text/plain"})
        assert response.status_code == 422