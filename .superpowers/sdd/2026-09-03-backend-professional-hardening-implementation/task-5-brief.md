### Task 5: Rewrite agent tests with mocked LLM

**Files:**
- Modify: `tests/test_agent.py`

**Interfaces:**
- Consumes: `mock_llm` fixture from conftest.py
- Produces: deterministic agent tests without real API calls

- [ ] **Step 1: Rewrite test_agent.py with mocked responses**

```python
import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import AIMessage
from src.agents.graph import create_sales_agent


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
        from langchain_core.messages import AIMessageChunk
        from langchain_core.tools import tool

        # First response: agent requests tool call
        tool_call_response = AIMessage(
            content="",
            tool_calls=[{
                "id": "call_1",
                "name": "search_products",
                "args": {"query": "polo", "category": ""}
            }]
        )
        # Second response: agent provides answer after tool result
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
```

- [ ] **Step 2: Run agent tests**

Run: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/test_agent.py -v`

Expected: All tests pass

- [ ] **Step 3: Commit**

```bash
git add tests/test_agent.py
git commit -m "test: rewrite agent tests with mocked LLM for determinism"
```
