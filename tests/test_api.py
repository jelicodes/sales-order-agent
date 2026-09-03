import pytest


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
    def test_chat_without_session(self, client):
        response = client.post("/chat", json={"message": "Halo"})
        assert response.status_code == 200
        assert "response" in response.json()
        assert "session_id" in response.json()