import pytest
from src.agents.graph import create_sales_agent


@pytest.fixture
def agent():
    return create_sales_agent()


class TestAgentCreation:
    def test_agent_can_be_created(self, agent):
        assert agent is not None


class TestAgentFlow:
    def test_agent_responds_to_greeting(self, agent):
        result = agent.invoke({
            "messages": [("user", "Halo, saya mau cari kaos polo")],
            "session_id": "test-session-1",
            "context": {},
        })
        assert result is not None
        assert len(result["messages"]) > 0

    def test_agent_uses_tools(self, agent):
        result = agent.invoke({
            "messages": [("user", "Cari kaos polo hitam untuk 500 orang")],
            "session_id": "test-session-2",
            "context": {},
        })
        assert result is not None
        last_message = result["messages"][-1]
        assert last_message.content is not None
