# Task 5: LangGraph Agent (State, Prompts, Graph, Nodes)

## Files to Create
- `src/agents/__init__.py`
- `src/agents/state.py`
- `src/agents/prompts.py`
- `src/agents/nodes.py`
- `src/agents/graph.py`
- `tests/test_agent.py`

## Prerequisites
- Task 4 completed: 6 tools exist at `src/tools/*.py`
- `src/config/settings.py` exists with `settings.GROQ_API_KEY` and `settings.GROQ_MODEL`

## What to Do

### 1. Create `src/agents/state.py`

```python
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    session_id: str
    context: dict
```

### 2. Create `src/agents/prompts.py`

```python
SALES_AGENT_PROMPT = """Anda adalah AI Sales Assistant untuk PT Lemone Surya Indonesia, perusahaan fashion grosir B2B terbesar di Asia Tenggara yang berlokasi di Pusat Grosir Metro Tanah Abang, Jakarta Pusat.

Tugas Anda:
1. Membantu customer menemukan produk fashion grosir yang sesuai kebutuhan
2. Cek ketersediaan stok secara real-time
3. Hitung harga berdasarkan quantity (ada tier harga untuk order besar)
4. Buat penawaran/quote untuk customer
5. Sarankan produk alternatif jika stok tidak cukup atau budget tidak sesuai

Aturan:
- Selalu cek stok sebelum memberikan harga
- Jika stok tidak cukup, tawarkan alternatif
- Jika budget customer tidak sesuai, sarankan produk lain yang lebih sesuai
- Gunakan Bahasa Indonesia yang profesional dan ramah
- Jangan janji sesuatu yang tidak bisa dipenuhi
- Jika pertanyaan di luar kemampuan Anda (pembayaran, klaim), sarankan hubungi sales langsung

Anda memiliki akses ke tools untuk:
- Mencari produk (search_products)
- Melihat detail produk (get_product_detail)
- Mengecek stok (check_stock)
- Menghitung harga (calculate_price)
- Membuat penawaran (create_quote)
- Mencari alternatif (get_alternatives)

Gunakan tools yang tepat untuk setiap permintaan customer."""
```

### 3. Create `src/agents/nodes.py`

```python
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq
from src.agents.state import AgentState
from src.agents.prompts import SALES_AGENT_PROMPT
from src.tools.search_products import search_products
from src.tools.get_product_detail import get_product_detail
from src.tools.check_stock import check_stock
from src.tools.calculate_price import calculate_price
from src.tools.create_quote import create_quote
from src.tools.get_alternatives import get_alternatives
from src.config.settings import settings

tools = [search_products, get_product_detail, check_stock, calculate_price, create_quote, get_alternatives]


def create_llm():
    return ChatGroq(
        model=settings.GROQ_MODEL,
        api_key=settings.GROQ_API_KEY,
        temperature=0.3,
    ).bind_tools(tools)


def llm_node(state: AgentState) -> dict:
    llm = create_llm()
    messages = list(state["messages"])
    # Prepend system prompt if not already present
    if not messages or not (isinstance(messages[0], HumanMessage) and SALES_AGENT_PROMPT in messages[0].content):
        messages = [HumanMessage(content=SALES_AGENT_PROMPT)] + messages
    response = llm.invoke(messages)
    return {"messages": [response]}


def tool_node(state: AgentState) -> dict:
    last_message = state["messages"][-1]
    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        return {"messages": []}

    tool_map = {
        "search_products": search_products,
        "get_product_detail": get_product_detail,
        "check_stock": check_stock,
        "calculate_price": calculate_price,
        "create_quote": create_quote,
        "get_alternatives": get_alternatives,
    }

    results = []
    for tool_call in last_message.tool_calls:
        tool_func = tool_map.get(tool_call["name"])
        if tool_func:
            result = tool_func.invoke(tool_call["args"])
            results.append(
                {"role": "tool", "content": str(result), "tool_call_id": tool_call["id"]}
            )

    return {"messages": results}
```

### 4. Create `src/agents/graph.py`

```python
from langgraph.graph import StateGraph, END
from src.agents.state import AgentState
from src.agents.nodes import llm_node, tool_node


def should_continue(state: AgentState) -> str:
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END


def create_sales_agent():
    graph = StateGraph(AgentState)
    graph.add_node("llm", llm_node)
    graph.add_node("tools", tool_node)
    graph.set_entry_point("llm")
    graph.add_conditional_edges("llm", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "llm")
    return graph.compile()
```

### 5. Create `tests/test_agent.py`

```python
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
```

## Verification
1. Seed DB: `D:\Jeli\myenv\Scripts\python.exe -m src.data.seed.seed`
2. Run tests: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/test_agent.py -v`
Note: Tests require GROQ_API_KEY in .env

## Report
Write your report to: `.superpowers/sdd/2026-09-02-sales-order-agent-implementation/task-5-report.md`
