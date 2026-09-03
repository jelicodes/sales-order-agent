# Backend Hardening Design Spec

**Tanggal:** 2026-09-03
**Status:** Approved
**Approach:** Modular (phase by phase)

## Ringkasan

Backend hardening untuk Sales Order Agent — meningkatkan reliability, type safety, dan testability. Berdasarkan analisis codebase dan dokumentasi LangChain/LangGraph terbaru.

## Problem Statement

Codebase saat ini memiliki:
- **Critical:** No error handling di agent nodes (LLM/tool invoke)
- **Critical:** Synchronous blocking di async context
- **Critical:** No input validation, inconsistent error responses
- **High:** No Pydantic response models, no rate limiting
- **High:** No message history truncation
- **High:** No shared test fixtures, no mock LLM

## Solution: 4-Phase Modular Approach

### Phase 1: Error Handling & Resilience

#### 1.1 Agent Error Handling (`src/agents/nodes.py`)

**Tool errors** — return error sebagai ToolMessage (LLM-recoverable pattern dari LangGraph docs):

```python
def tool_node(state: AgentState) -> dict:
    last_message = state["messages"][-1]
    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        return {"messages": []}

    results = []
    for tool_call in last_message.tool_calls:
        tool_func = TOOL_REGISTRY.get(tool_call["name"])
        if tool_func:
            try:
                result = tool_func.invoke(tool_call["args"])
            except Exception as e:
                result = f"Tool error: {str(e)}"
        else:
            result = f"Unknown tool: {tool_call['name']}"
        results.append({"role": "tool", "content": str(result), "tool_call_id": tool_call["id"]})

    return {"messages": results}
```

**LLM errors** — try/except + RetryPolicy untuk transient errors:

```python
from langgraph.types import RetryPolicy

graph.add_node(
    "llm",
    llm_node,
    retry_policy=RetryPolicy(max_attempts=3, retry_on=ConnectionError)
)
```

#### 1.2 Unified Error Response (`src/api/models.py`)

```python
from pydantic import BaseModel, Field

class ErrorResponse(BaseModel):
    """Response error unified."""
    success: bool = Field(default=False, description="Status sukses")
    error: str = Field(description="Pesan error")
    detail: str | None = Field(default=None, description="Detail error")
    request_id: str | None = Field(default=None, description="ID request")
```

#### 1.3 Input Validation (`src/api/chat.py`)

```python
from pydantic import BaseModel, Field, field_validator

class ChatRequest(BaseModel):
    """Request chat ke agent."""
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Pesan ke agent"
    )
    session_id: str = Field(
        default="",
        pattern=r"^[a-f0-9-]{0,36}$",
        description="Session ID (UUID format)"
    )
    customer_name: str = Field(default="", max_length=100)

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Message tidak boleh kosong atau spasi saja")
        return v.strip()
```

#### 1.4 Rate Limiting (`src/main.py`)

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/chat", response_model=ChatResponse)
@limiter.limit("10/minute")
async def chat_endpoint(req: ChatRequest):
    ...
```

#### 1.5 Session 404 (`src/api/session.py`)

```python
from fastapi import HTTPException

if not session:
    raise HTTPException(status_code=404, detail="Session not found")
```

### Phase 2: Async & Performance

#### 2.1 Async Chat Endpoint (`src/api/chat.py`)

```python
import asyncio

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    result = await asyncio.to_thread(
        agent.invoke,
        {"messages": messages, "session_id": session_id, "context": {"request_id": request_id}}
    )
```

**Why:** `agent.invoke()` synchronous. `asyncio.to_thread()` adalah official approach untuk sync code di async context.

#### 2.2 Message Truncation (Official `trim_messages`)

```python
from langchain_core.messages.utils import trim_messages, count_tokens_approximately

def get_trimmed_history(session_id: str, max_tokens: int = 4000) -> list:
    all_messages = get_conversation_history(session_id)
    return trim_messages(
        all_messages,
        strategy="last",
        token_counter=count_tokens_approximately,
        max_tokens=max_tokens,
        start_on="human",
        end_on=("human", "tool"),
    )
```

**Why:** Official LangChain utility — token counting, boundary detection, strategy.

#### 2.3 System Prompt (Official `SystemMessage`)

```python
from langchain_core.messages import SystemMessage

def llm_node(state: AgentState) -> dict:
    messages = [SystemMessage(content=SALES_AGENT_PROMPT)] + list(state["messages"])
    response = llm.invoke(messages, config=config)
    return {"messages": [response]}
```

**Why:** `SystemMessage` adalah official LangChain type untuk system prompts.

#### 2.4 Quote-Session Link

```python
@tool
def create_quote(items: list[dict], session_id: str = "") -> dict:
    # gunakan session_id dari agent state
    ...
```

### Phase 3: Type Safety & Code Quality

#### 3.1 Pydantic Response Models (`src/api/models.py`)

```python
from pydantic import BaseModel, Field

class ChatResponse(BaseModel):
    """Response dari chat endpoint."""
    response: str = Field(description="Respons dari agent")
    session_id: str = Field(description="ID sesi percakapan")
    request_id: str = Field(description="ID unik request")

class SessionResponse(BaseModel):
    """Response session."""
    id: str = Field(description="Session ID")
    customer_name: str = Field(description="Nama customer")
    status: str = Field(description="Status session")

class HealthResponse(BaseModel):
    """Response health check."""
    status: str = Field(description="Status overall")
    service: str = Field(description="Nama service")
    version: str = Field(description="Versi aplikasi")
    checks: dict = Field(description="Detail checks")
```

#### 3.2 Tool Input Schemas (Official Pydantic Pattern)

```python
from pydantic import BaseModel, Field
from langchain_core.tools import tool

class SearchInput(BaseModel):
    """Input untuk pencarian produk."""
    query: str = Field(description="Kata kunci pencarian produk")
    category: str | None = Field(default=None, description="Filter kategori produk")

@tool(args_schema=SearchInput)
def search_products(query: str, category: str | None = None) -> list[dict]:
    """Cari produk berdasarkan kata kunci dan kategori."""
    ...
```

**Why:** Official LangChain pattern — Pydantic models provide field validation, descriptions, auto-generated JSON schema.

#### 3.3 Unified Tool Registry

```python
TOOL_REGISTRY: dict[str, tool] = {
    "search_products": search_products,
    "get_product_detail": get_product_detail,
    "check_stock": check_stock,
    "calculate_price": calculate_price,
    "create_quote": create_quote,
    "get_alternatives": get_alternatives,
}

tools = list(TOOL_REGISTRY.values())
```

#### 3.4 Version Constant

```python
# src/config/settings.py
APP_VERSION = "0.1.0"

# src/main.py
from src.config.settings import APP_VERSION
app = FastAPI(version=APP_VERSION, ...)
```

### Phase 4: Test Infrastructure

#### 4.1 Official Mock Chat Model (`GenericFakeChatModel`)

```python
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, ToolCall

simple_model = GenericFakeChatModel(messages=iter([
    "Halo! Ada yang bisa saya bantu?",
    "Produk Polo Premium tersedia dalam 3 warna."
]))

tool_model = GenericFakeChatModel(messages=iter([
    AIMessage(content="", tool_calls=[
        ToolCall(name="search_products", args={"query": "polo"}, id="call_1")
    ]),
    "Saya menemukan 3 produk polo untuk Anda."
]))
```

**Why:** Official LangChain utility — extends `BaseChatModel`.

#### 4.2 Test Strategy

| Level | What | Speed | Flakiness |
|-------|------|-------|-----------|
| Unit tests | Tools, database, config | Fast (<1s) | Low |
| Integration tests | Agent + real Groq API | Slow (30s+) | High |
| Evals | LLM-as-judge quality | Slow | Medium |

#### 4.3 Assert on Structure, Not Content

```python
# ❌ Bad — nondeterministic
assert response == "Saya menemukan 3 produk polo"

# ✅ Good — deterministic
assert response.status_code == 200
assert "session_id" in response.json()
assert len(response.json()["response"]) > 0
```

#### 4.4 `conftest.py`

```python
import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.data.database import init_db

@pytest.fixture(scope="session")
def client():
    init_db()
    with TestClient(app) as c:
        yield c

@pytest.fixture
def sample_session(client):
    response = client.post("/session", json={"customer_name": "Test User"})
    return response.json()
```

#### 4.5 Test Structure

```
tests/
├── conftest.py           # Shared fixtures
├── test_tools.py         # 52 unit tests (existing)
├── test_agent.py         # Agent tests (mock + integration)
├── test_api.py           # API tests (error handling)
├── test_database.py      # Database unit tests (NEW)
└── test_integration.py   # Integration tests (skip by default)
```

## Implementation Order

1. **Phase 1** — Error handling & resilience (Critical)
2. **Phase 2** — Async & performance (High)
3. **Phase 3** — Type safety & code quality (High)
4. **Phase 4** — Test infrastructure (High)

## References

- LangGraph error handling: https://docs.langchain.com/oss/python/langgraph/fault-tolerance
- LangGraph tool errors: https://docs.langchain.com/oss/python/langchain/tools#error-handling
- trim_messages: https://docs.langchain.com/oss/python/langchain/short-term-memory#trim-messages
- GenericFakeChatModel: https://docs.langchain.com/oss/python/langchain/test/unit-testing#mock-chat-model
- Pydantic tool schemas: https://docs.langchain.com/oss/python/langchain/tools#advanced-schema-definition
