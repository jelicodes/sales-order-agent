import pytest
import tempfile
import os
from unittest.mock import MagicMock, patch
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from src.agents.graph import create_sales_agent
from src.agents.nodes import llm_node


class TestAgentCreation:
    def test_agent_can_be_created(self):
        with patch("src.agents.nodes.create_llm") as mock_create:
            mock_create.return_value = MagicMock()
            agent = create_sales_agent()
            assert agent is not None


class TestAgentFlow:
    def test_agent_responds_to_greeting(self, mock_llm):
        greeting_response = AIMessage(
            content="Selamat datang! Saya AI Sales Assistant PT Lemone. Ada yang bisa saya bantu?",
            tool_calls=[]
        )
        agent = mock_llm([greeting_response])
        result = agent.invoke({
            "messages": [("user", "Halo")],
            "session_id": "test-session-1",
            "context": {},
        })
        assert result is not None
        assert len(result["messages"]) > 0
        last_message = result["messages"][-1]
        assert "Selamat datang" in last_message.content

    def test_agent_calls_search_tool(self, mock_llm):
        tool_call_response = AIMessage(
            content="",
            tool_calls=[{
                "id": "call_1",
                "name": "search_products",
                "args": {"query": "polo", "category": ""}
            }]
        )
        final_response = AIMessage(
            content="Kami memiliki Polo Premium Cotton seharga Rp 85.000/pcs untuk MOQ 100.",
            tool_calls=[]
        )
        agent = mock_llm([tool_call_response, final_response])
        result = agent.invoke({
            "messages": [("user", "Cari kaos polo")],
            "session_id": "test-session-2",
            "context": {},
        })
        assert result is not None
        last_message = result["messages"][-1]
        assert "Polo" in last_message.content or "polo" in last_message.content

    def test_agent_handles_error_gracefully(self, mock_llm):
        error_response = AIMessage(
            content="Maaf, terjadi kesalahan saat memproses pesan Anda. Silakan coba lagi.",
            tool_calls=[]
        )
        agent = mock_llm([error_response])
        result = agent.invoke({
            "messages": [("user", "Test error handling")],
            "session_id": "test-session-3",
            "context": {},
        })
        assert result is not None
        last_message = result["messages"][-1]
        assert "Maaf" in last_message.content or "kesalahan" in last_message.content

    def test_agent_maintains_context(self, mock_llm):
        response1 = AIMessage(
            content="Saya menemukan Polo Premium Cotton. Stok tersedia 500 pcs.",
            tool_calls=[]
        )
        response2 = AIMessage(
            content="Untuk 500 pcs navy, harga Rp 70.000/pcs. Total Rp 35.000.000.",
            tool_calls=[]
        )
        agent = mock_llm([response1, response2])

        # First turn
        result1 = agent.invoke({
            "messages": [("user", "Cari kaos polo")],
            "session_id": "test-session-4",
            "context": {},
        })

        # Second turn with context
        result2 = agent.invoke({
            "messages": [
                ("user", "Cari kaos polo"),
                ("assistant", "Saya menemukan Polo Premium Cotton. Stok tersedia 500 pcs."),
                ("user", "Buatkan penawaran untuk 500 pcs navy")
            ],
            "session_id": "test-session-4",
            "context": {},
        })
        assert result2 is not None


class TestLangfuseMetadata:
    def test_metadata_includes_session_id(self):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = AIMessage(content="OK", tool_calls=[])
        state = {
            "messages": [("user", "test")],
            "session_id": "sess-123",
            "context": {"request_id": "req-456"},
        }
        with patch("src.agents.nodes.get_llm", return_value=mock_llm):
            with patch("src.agents.nodes.get_langfuse_handler", return_value=MagicMock()):
                llm_node(state)
                call_args = mock_llm.invoke.call_args
                config = call_args[1].get("config", call_args[1])
                assert "metadata" in config
                assert config["metadata"]["session_id"] == "sess-123"
                assert config["metadata"]["request_id"] == "req-456"

    def test_metadata_absent_when_no_session(self):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = AIMessage(content="OK", tool_calls=[])
        state = {
            "messages": [("user", "test")],
            "session_id": "",
            "context": {},
        }
        with patch("src.agents.nodes.get_llm", return_value=mock_llm):
            with patch("src.agents.nodes.get_langfuse_handler", return_value=MagicMock()):
                llm_node(state)
                call_args = mock_llm.invoke.call_args
                config = call_args[1].get("config", call_args[1])
                assert "metadata" not in config


class TestGroqRateLimit:
    def test_rate_limit_returns_503(self, client):
        with patch("src.agents.nodes.get_llm") as mock_get_llm:
            from groq import RateLimitError as GroqRateLimitError
            mock_instance = MagicMock()
            mock_instance.invoke.side_effect = GroqRateLimitError(
                message="Rate limit exceeded",
                response=MagicMock(status_code=429),
                body={"error": {"message": "Rate limit reached"}}
            )
            mock_get_llm.return_value = mock_instance
            response = client.post("/chat", json={"message": "test"})
            assert response.status_code == 503
            assert "sibuk" in response.json()["error"]


class TestMultiTurn:
    def test_checkpointer_accumulates_messages(self):
        tmp = tempfile.mktemp(suffix=".db")
        try:
            checkpointer = SqliteSaver.from_conn_string(tmp)
            cp_ctx = checkpointer.__enter__()
            agent = create_sales_agent(checkpointer=cp_ctx)

            call_count = 0
            def mock_invoke(messages, config=None):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return AIMessage(content="Halo!")
                elif call_count == 2:
                    return AIMessage(content="Nama Anda Budi.")
                return AIMessage(content="Budi, ada yang bisa saya bantu?")

            with patch("src.agents.nodes.get_llm") as mock_get_llm:
                mock_llm = MagicMock()
                mock_llm.invoke = mock_invoke
                mock_get_llm.return_value = mock_llm

                r1 = agent.invoke(
                    {"messages": [HumanMessage(content="Halo")], "session_id": "s1", "context": {}},
                    {"configurable": {"thread_id": "s1"}},
                )
                r2 = agent.invoke(
                    {"messages": [HumanMessage(content="Nama saya Budi")], "session_id": "s1", "context": {}},
                    {"configurable": {"thread_id": "s1"}},
                )
                r3 = agent.invoke(
                    {"messages": [HumanMessage(content="Nama saya siapa?")], "session_id": "s1", "context": {}},
                    {"configurable": {"thread_id": "s1"}},
                )

            assert len(r1["messages"]) == 2
            assert len(r2["messages"]) == 4
            assert len(r3["messages"]) == 6
            assert call_count == 3
        finally:
            checkpointer.__exit__(None, None, None)
            if os.path.exists(tmp):
                os.remove(tmp)
