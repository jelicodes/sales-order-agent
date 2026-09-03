import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from src.main import app
from src.agents.graph import create_sales_agent


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def session_id(client):
    response = client.post("/session", json={"customer_name": "Test Customer"})
    return response.json()["session_id"]


@pytest.fixture
def mock_llm():
    """Fixture to mock LLM with scripted responses."""
    def _make_agent(responses):
        """
        Create agent with mocked LLM.

        Args:
            responses: List of AIMessage objects the mock LLM will return in sequence.
        """
        with patch("src.agents.nodes.create_llm") as mock_create:
            mock_instance = MagicMock()
            mock_instance.invoke.side_effect = responses
            mock_create.return_value = mock_instance
            agent = create_sales_agent()
            yield agent
    return _make_agent
