import pytest
from fastapi.testclient import TestClient
from src.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def session_id(client):
    response = client.post("/session", json={"customer_name": "Test Customer"})
    return response.json()["session_id"]
