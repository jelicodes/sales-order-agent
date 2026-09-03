# Backend Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Meningkatkan reliability, type safety, dan testability backend Sales Order Agent

**Architecture:** 4-phase modular approach — error handling, async, type safety, test infrastructure. Setiap phase bisa di-commit dan di-test secara independent.

**Tech Stack:** FastAPI, LangChain/LangGraph, Pydantic, SQLite, Langfuse, pytest

## Global Constraints

- Python 3.13.1 (D:\Jeli\myenv)
- Test command: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/test_tools.py tests/test_api.py -v`
- Run server: `D:\Jeli\myenv\Scripts\python.exe -m src.main`
- Commit format: conventional commits (`feat:`, `fix:`, `docs:`)
- Language: Bahasa Indonesia untuk user-facing text, English untuk code

---

## Phase 1: Error Handling & Resilience

### Task 1: Add slowapi rate limiting

**Files:**
- Modify: `requirements.txt`
- Modify: `src/main.py`

**Interfaces:**
- Consumes: existing FastAPI app
- Produces: rate-limited `/chat` endpoint

- [ ] **Step 1: Add slowapi to requirements.txt**

```txt
slowapi>=0.1.9
```

- [ ] **Step 2: Install slowapi**

Run: `D:\Jeli\myenv\Scripts\pip.exe install slowapi`

- [ ] **Step 3: Add rate limiter to main.py**

```python
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={"success": False, "error": "Terlalu banyak request. Silakan coba lagi nanti."}
    )
```

- [ ] **Step 4: Add @limiter.limit to /chat endpoint**

```python
@router.post("/chat", response_model=ChatResponse)
@limiter.limit("10/minute")
async def chat_endpoint(req: ChatRequest):
    ...
```

- [ ] **Step 5: Run existing tests to verify no regression**

Run: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/test_tools.py tests/test_api.py -v`

- [ ] **Step 6: Commit**

```bash
git add requirements.txt src/main.py src/api/chat.py
git commit -m "feat: add rate limiting with slowapi (10 req/min per IP)"
```

### Task 2: Add Pydantic response models and input validation

**Files:**
- Create: `src/api/models.py`
- Modify: `src/api/chat.py`
- Modify: `src/api/session.py`
- Modify: `src/api/health.py`
- Modify: `src/main.py`

**Interfaces:**
- Consumes: existing API endpoints
- Produces: typed response models, input validation

- [ ] **Step 1: Create src/api/models.py with all response models**

```python
from pydantic import BaseModel, Field


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

    model_config = {"json_schema_extra": {"examples": [{"message": "Cari produk polo"}]}}


class ChatResponse(BaseModel):
    """Response dari chat endpoint."""
    response: str = Field(description="Respons dari agent")
    session_id: str = Field(description="ID sesi percakapan")
    request_id: str = Field(description="ID unik request")


class CreateSessionRequest(BaseModel):
    """Request buat session baru."""
    customer_name: str = Field(default="", max_length=100)


class SessionResponse(BaseModel):
    """Response session."""
    id: str = Field(description="Session ID")
    customer_name: str = Field(description="Nama customer")
    status: str = Field(description="Status session")


class CreateSessionResponse(BaseModel):
    """Response buat session baru."""
    session_id: str = Field(description="Session ID baru")
    status: str = Field(description="Status session")


class ErrorResponse(BaseModel):
    """Response error unified."""
    success: bool = Field(default=False, description="Status sukses")
    error: str = Field(description="Pesan error")
    detail: str | None = Field(default=None, description="Detail error")
    request_id: str | None = Field(default=None, description="ID request")


class HealthCheckResult(BaseModel):
    """Result dari health check."""
    status: str = Field(description="Status check")
    message: str | None = Field(default=None, description="Pesan tambahan")
    enabled: bool | None = Field(default=None, description="Status enabled")
    model: str | None = Field(default=None, description="Model name")
    products_count: int | None = Field(default=None, description="Jumlah produk")


class HealthResponse(BaseModel):
    """Response health check."""
    status: str = Field(description="Status overall")
    service: str = Field(description="Nama service")
    version: str = Field(description="Versi aplikasi")
    checks: dict[str, HealthCheckResult] = Field(description="Detail checks")
```

- [ ] **Step 2: Update chat.py to use typed models**

```python
from src.api.models import ChatRequest, ChatResponse
from fastapi import HTTPException

@router.post("/chat", response_model=ChatResponse)
@limiter.limit("10/minute")
async def chat_endpoint(req: ChatRequest):
    ...
    return ChatResponse(
        response=response_content,
        session_id=session_id,
        request_id=request_id,
    )
```

- [ ] **Step 3: Update session.py to use typed models and HTTPException**

```python
from fastapi import HTTPException
from src.api.models import CreateSessionRequest, CreateSessionResponse, SessionResponse

@router.post("/session", response_model=CreateSessionResponse)
async def create_session_endpoint(req: CreateSessionRequest):
    session_id = str(uuid.uuid4())
    session = create_session(session_id, req.customer_name)
    return CreateSessionResponse(session_id=session_id, status=session["status"])

@router.get("/session/{session_id}", response_model=SessionResponse)
async def get_session_endpoint(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionResponse(**session)
```

- [ ] **Step 4: Update health.py to use typed model**

```python
from src.api.models import HealthResponse, HealthCheckResult

@router.get("/health", response_model=HealthResponse)
async def health_check():
    ...
    return HealthResponse(
        status=overall_status,
        service="sales-order-agent",
        version=APP_VERSION,
        checks={
            "database": HealthCheckResult(**db_status),
            "chromadb": HealthCheckResult(**chromadb_status),
            "groq": HealthCheckResult(**groq_status),
            "langfuse": HealthCheckResult(**langfuse_status),
        }
    )
```

- [ ] **Step 5: Update main.py global exception handler to use ErrorResponse**

```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Terjadi kesalahan internal server",
            detail=str(exc)
        ).model_dump()
    )
```

- [ ] **Step 6: Run tests**

Run: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/test_tools.py tests/test_api.py -v`

- [ ] **Step 7: Commit**

```bash
git add src/api/models.py src/api/chat.py src/api/session.py src/api/health.py src/main.py
git commit -m "feat: add Pydantic response models, input validation, unified error response"
```

### Task 3: Add agent error handling with LangGraph best practices

**Files:**
- Modify: `src/agents/nodes.py`
- Modify: `src/agents/graph.py`

**Interfaces:**
- Consumes: existing agent state, tools
- Produces: error-resilient llm_node and tool_node

- [ ] **Step 1: Update nodes.py with error handling and unified tool registry**

```python
import logging
from typing import Optional
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
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
from src.config.langfuse import get_langfuse_handler

logger = logging.getLogger(__name__)

# Single source of truth for tool registry
TOOL_REGISTRY = {
    "search_products": search_products,
    "get_product_detail": get_product_detail,
    "check_stock": check_stock,
    "calculate_price": calculate_price,
    "create_quote": create_quote,
    "get_alternatives": get_alternatives,
}

tools = list(TOOL_REGISTRY.values())


def create_llm():
    return ChatGroq(
        model=settings.GROQ_MODEL,
        api_key=settings.GROQ_API_KEY,
        temperature=0.3,
    ).bind_tools(tools)


def llm_node(state: AgentState) -> dict:
    llm = create_llm()
    messages = [SystemMessage(content=SALES_AGENT_PROMPT)] + list(state["messages"])

    langfuse_handler = get_langfuse_handler()
    config = {"callbacks": [langfuse_handler]} if langfuse_handler else {}

    try:
        response = llm.invoke(messages, config=config)
        return {"messages": [response]}
    except Exception as e:
        logger.error(f"LLM invocation failed: {e}")
        error_msg = AIMessage(content="Maaf, terjadi kesalahan saat memproses pesan Anda. Silakan coba lagi.")
        return {"messages": [error_msg]}


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
                logger.error(f"Tool {tool_call['name']} failed: {e}")
                result = f"Tool error: {str(e)}"
        else:
            result = f"Unknown tool: {tool_call['name']}"
            logger.warning(f"Unknown tool called: {tool_call['name']}")
        results.append(
            {"role": "tool", "content": str(result), "tool_call_id": tool_call["id"]}
        )

    return {"messages": results}
```

- [ ] **Step 2: Update graph.py with RetryPolicy for LLM node**

```python
from langgraph.graph import StateGraph, END
from langgraph.types import RetryPolicy
from src.agents.state import AgentState
from src.agents.nodes import llm_node, tool_node


def should_continue(state: AgentState) -> str:
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END


def create_sales_agent():
    graph = StateGraph(AgentState)
    graph.add_node(
        "llm",
        llm_node,
        retry_policy=RetryPolicy(max_attempts=3, retry_on=ConnectionError)
    )
    graph.add_node("tools", tool_node)
    graph.set_entry_point("llm")
    graph.add_conditional_edges("llm", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "llm")
    return graph.compile()
```

- [ ] **Step 3: Run tests**

Run: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/test_tools.py tests/test_api.py -v`

- [ ] **Step 4: Commit**

```bash
git add src/agents/nodes.py src/agents/graph.py
git commit -m "feat: add error handling to agent nodes, RetryPolicy for LLM, unified tool registry"
```

### Task 4: Add version constant

**Files:**
- Modify: `src/config/settings.py`
- Modify: `src/main.py`
- Modify: `src/api/health.py`

**Interfaces:**
- Consumes: existing settings
- Produces: single APP_VERSION constant

- [ ] **Step 1: Add APP_VERSION to settings.py**

```python
APP_VERSION = "0.1.0"
```

- [ ] **Step 2: Update main.py to use APP_VERSION**

```python
from src.config.settings import settings, APP_VERSION
app = FastAPI(
    title="Sales Order Agent - PT Lemone",
    description="AI Agent untuk membantu proses order fashion grosir B2B",
    version=APP_VERSION,
    lifespan=lifespan,
)
```

- [ ] **Step 3: Update health.py to use APP_VERSION**

```python
from src.config.settings import APP_VERSION

@router.get("/health", response_model=HealthResponse)
async def health_check():
    ...
    return HealthResponse(
        status=overall_status,
        service="sales-order-agent",
        version=APP_VERSION,
        ...
    )
```

- [ ] **Step 4: Run tests**

Run: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/test_tools.py tests/test_api.py -v`

- [ ] **Step 5: Commit**

```bash
git add src/config/settings.py src/main.py src/api/health.py
git commit -m "feat: add APP_VERSION constant, single source of truth"
```

---

## Phase 2: Async & Performance

### Task 5: Add async wrapping for agent.invoke

**Files:**
- Modify: `src/api/chat.py`

**Interfaces:**
- Consumes: existing agent.invoke
- Produces: async-compatible chat endpoint

- [ ] **Step 1: Update chat.py with asyncio.to_thread**

```python
import asyncio

@router.post("/chat", response_model=ChatResponse)
@limiter.limit("10/minute")
async def chat_endpoint(req: ChatRequest):
    request_id = str(uuid.uuid4())
    logger.info(f"[{request_id}] Chat request received: session={req.session_id}")

    session_id = req.session_id
    if not session_id:
        session_id = str(uuid.uuid4())
        create_session(session_id, req.customer_name)
        logger.info(f"[{request_id}] New session created: {session_id}")

    history = get_conversation_history(session_id)
    messages = []
    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=req.message))

    result = await asyncio.to_thread(
        agent.invoke,
        {
            "messages": messages,
            "session_id": session_id,
            "context": {"request_id": request_id},
        }
    )

    save_message(session_id, "user", req.message)
    response_content = result["messages"][-1].content
    save_message(session_id, "assistant", response_content)

    logger.info(f"[{request_id}] Response sent successfully")

    return ChatResponse(
        response=response_content,
        session_id=session_id,
        request_id=request_id,
    )
```

- [ ] **Step 2: Run tests**

Run: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/test_tools.py tests/test_api.py -v`

- [ ] **Step 3: Commit**

```bash
git add src/api/chat.py
git commit -m "feat: wrap agent.invoke with asyncio.to_thread for non-blocking async"
```

### Task 6: Add message history truncation

**Files:**
- Modify: `src/api/chat.py`
- Modify: `src/data/database.py`

**Interfaces:**
- Consumes: existing get_conversation_history
- Produces: truncated message history

- [ ] **Step 1: Add max_messages parameter to get_conversation_history in database.py**

```python
def get_conversation_history(session_id: str, max_messages: int = 20) -> list[dict]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM conversations WHERE session_id = ? ORDER BY timestamp",
            (session_id,),
        )
        results = [dict(row) for row in cursor.fetchall()]
        if len(results) > max_messages:
            return results[-max_messages:]
        return results
```

- [ ] **Step 2: Run tests**

Run: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/test_tools.py tests/test_api.py -v`

- [ ] **Step 3: Commit**

```bash
git add src/data/database.py
git commit -m "feat: add message history truncation (max 20 messages)"
```

### Task 7: Fix system prompt handling with SystemMessage

**Files:**
- Modify: `src/agents/nodes.py`

**Interfaces:**
- Consumes: existing SALES_AGENT_PROMPT
- Produces: proper SystemMessage usage

- [ ] **Step 1: Verify nodes.py already uses SystemMessage (from Task 3)**

This was already done in Task 3. The current implementation uses:
```python
messages = [SystemMessage(content=SALES_AGENT_PROMPT)] + list(state["messages"])
```

- [ ] **Step 2: Commit (no changes needed)**

This is already implemented in Task 3.

---

## Phase 3: Type Safety & Code Quality

### Task 8: Add Pydantic input schemas to all tools

**Files:**
- Modify: `src/tools/search_products.py`
- Modify: `src/tools/get_product_detail.py`
- Modify: `src/tools/check_stock.py`
- Modify: `src/tools/calculate_price.py`
- Modify: `src/tools/create_quote.py`
- Modify: `src/tools/get_alternatives.py`

**Interfaces:**
- Consumes: existing tool functions
- Produces: tools with Pydantic args_schema

- [ ] **Step 1: Update search_products.py with Pydantic schema**

```python
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from src.data.vector_store import search_products_semantic
from src.data.database import search_products as db_search


class SearchProductsInput(BaseModel):
    """Input untuk pencarian produk."""
    query: str = Field(description="Kata kunci pencarian produk")
    category: str = Field(default="", description="Filter kategori produk (opsional)")


@tool(args_schema=SearchProductsInput)
def search_products(query: str, category: str = "") -> list[dict]:
    """Cari produk fashion grosir berdasarkan query. Gunakan untuk mencari produk berdasarkan nama, kategori, atau deskripsi."""
    if query and query.strip():
        results = search_products_semantic(query, n_results=5)
        if results:
            return results
    return db_search(query if query else "", category if category else None)
```

- [ ] **Step 2: Update get_product_detail.py with Pydantic schema**

```python
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from src.data.database import get_product_by_id, get_product_variants


class GetProductDetailInput(BaseModel):
    """Input untuk detail produk."""
    product_id: int = Field(description="ID produk")


@tool(args_schema=GetProductDetailInput)
def get_product_detail(product_id: int) -> dict | None:
    """Ambil detail lengkap produk berdasarkan ID, termasuk varian warna dan spesifikasi."""
    product = get_product_by_id(product_id)
    if not product:
        return None
    variants = get_product_variants(product_id)
    return {**product, "variants": variants}
```

- [ ] **Step 3: Update check_stock.py with Pydantic schema**

```python
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from src.data.database import get_stock_by_product


class CheckStockInput(BaseModel):
    """Input untuk cek stok."""
    product_id: int = Field(description="ID produk")
    quantity: int = Field(description="Jumlah yang dibutuhkan")


@tool(args_schema=CheckStockInput)
def check_stock(product_id: int, quantity: int) -> dict:
    """Cek ketersediaan stok produk untuk jumlah tertentu."""
    variants = get_stock_by_product(product_id)
    total_stock = sum(v["quantity"] for v in variants)
    available = total_stock >= quantity
    return {
        "product_id": product_id,
        "requested": quantity,
        "total_stock": total_stock,
        "available": available,
        "variants": [
            {
                "variant_id": v["variant_id"],
                "color": v["color"],
                "quantity": v["quantity"],
                "warehouse": v["warehouse_location"],
            }
            for v in variants
        ],
    }
```

- [ ] **Step 4: Update calculate_price.py with Pydantic schema**

```python
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from src.data.database import get_price_tier, get_discount


class CalculatePriceInput(BaseModel):
    """Input untuk kalkulasi harga."""
    product_id: int = Field(description="ID produk")
    quantity: int = Field(description="Jumlah barang")
    discount_code: str = Field(default="", description="Kode diskon (opsional)")


@tool(args_schema=CalculatePriceInput)
def calculate_price(product_id: int, quantity: int, discount_code: str = "") -> dict:
    """Hitung harga total berdasarkan quantity tier dan diskon yang tersedia."""
    tier = get_price_tier(product_id, quantity)
    if not tier:
        return {"error": "Price tier not found"}

    price_per_unit = tier["price_per_unit"]
    subtotal = price_per_unit * quantity

    discount = None
    discount_amount = 0
    if discount_code:
        discount = get_discount(discount_code)
        if discount:
            if discount["type"] == "percentage":
                discount_amount = subtotal * (discount["value"] / 100)
            elif discount["type"] == "fixed":
                discount_amount = discount["value"]

    total = subtotal - discount_amount

    return {
        "product_id": product_id,
        "quantity": quantity,
        "price_per_unit": price_per_unit,
        "subtotal": subtotal,
        "discount": discount,
        "discount_amount": discount_amount,
        "total": total,
        "tier": {"min_qty": tier["min_qty"], "max_qty": tier["max_qty"], "pcs": f"{tier['min_qty']}+ pcs"},
    }
```

- [ ] **Step 5: Update create_quote.py with Pydantic schema**

```python
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from src.data.database import create_quote as db_create_quote
from src.tools.calculate_price import calculate_price
import uuid
from datetime import datetime, timedelta


class QuoteItem(BaseModel):
    """Item dalam penawaran."""
    product_id: int = Field(description="ID produk")
    quantity: int = Field(description="Jumlah barang")
    color: str = Field(description="Warna produk")


class CreateQuoteInput(BaseModel):
    """Input untuk buat penawaran."""
    items: list[QuoteItem] = Field(description="Daftar item penawaran")
    customer_info: dict = Field(description="Informasi customer")


@tool(args_schema=CreateQuoteInput)
def create_quote(items: list[dict], customer_info: dict, session_id: str = "") -> dict:
    """Buat penawaran harga (quote) untuk customer berdasarkan item yang dipilih."""
    quote_id = f"Q-{datetime.now().strftime('%Y-%m-%d')}-{str(uuid.uuid4())[:8]}"
    valid_until = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

    total_price = 0
    items_with_pricing = []
    for item in items:
        pricing = calculate_price.invoke({
            "product_id": item["product_id"],
            "quantity": item["quantity"]
        })
        item_total = pricing.get("total", 0)
        total_price += item_total
        items_with_pricing.append({
            **item,
            "price_per_unit": pricing.get("price_per_unit", 0),
            "subtotal": item_total,
        })

    import json
    db_create_quote(quote_id, session_id, json.dumps(items_with_pricing), total_price, valid_until)

    return {
        "quote_id": quote_id,
        "items": items_with_pricing,
        "total_price": total_price,
        "formatted_total": f"Rp {total_price:,.0f}".replace(",", "."),
        "valid_until": valid_until,
        "customer_info": customer_info,
    }
```

- [ ] **Step 6: Update get_alternatives.py with Pydantic schema**

```python
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from src.data.database import get_product_by_id, search_products


class GetAlternativesInput(BaseModel):
    """Input untuk cari alternatif."""
    product_id: int = Field(description="ID produk yang ingin dicari alternatifnya")
    reason: str = Field(description="Alasan mencari alternatif: 'budget' atau 'stock'")


@tool(args_schema=GetAlternativesInput)
def get_alternatives(product_id: int, reason: str) -> list[dict]:
    """Cari produk alternatif berdasarkan alasan (budget/stock)."""
    product = get_product_by_id(product_id)
    if not product:
        return []

    all_products = search_products("", product["category"])

    alternatives = []
    for p in all_products:
        if p["id"] == product_id:
            continue
        price_diff = p["base_price"] - product["base_price"]
        price_diff_pct = (price_diff / product["base_price"]) * 100 if product["base_price"] else 0

        alternatives.append({
            "product_id": p["id"],
            "name": p["name"],
            "category": p["category"],
            "base_price": p["base_price"],
            "price_diff": price_diff,
            "price_diff_pct": round(price_diff_pct, 1),
        })

    if reason == "budget":
        alternatives.sort(key=lambda x: x["base_price"])
    elif reason == "stock":
        alternatives.sort(key=lambda x: x["base_price"], reverse=True)

    return alternatives[:3]
```

- [ ] **Step 7: Run tests**

Run: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/test_tools.py tests/test_api.py -v`

- [ ] **Step 8: Commit**

```bash
git add src/tools/*.py
git commit -m "feat: add Pydantic input schemas to all 6 tools"
```

---

## Phase 4: Test Infrastructure

### Task 9: Add conftest.py with shared fixtures

**Files:**
- Create: `tests/conftest.py`

**Interfaces:**
- Consumes: existing FastAPI app, database
- Produces: shared test fixtures

- [ ] **Step 1: Create tests/conftest.py**

```python
import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.data.database import init_db


@pytest.fixture(scope="session")
def client():
    """Test client untuk semua tests."""
    init_db()
    with TestClient(app) as c:
        yield c


@pytest.fixture
def sample_session(client):
    """Buat session baru untuk testing."""
    response = client.post("/session", json={"customer_name": "Test User"})
    return response.json()
```

- [ ] **Step 2: Run tests to verify fixtures work**

Run: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/test_tools.py tests/test_api.py -v`

- [ ] **Step 3: Commit**

```bash
git add tests/conftest.py
git commit -m "test: add conftest.py with shared fixtures"
```

### Task 10: Add API error handling tests

**Files:**
- Modify: `tests/test_api.py`

**Interfaces:**
- Consumes: shared client fixture from conftest.py
- Produces: error handling tests

- [ ] **Step 1: Update test_api.py with error handling tests**

```python
import pytest


class TestHealth:
    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["ok", "degraded"]
        assert data["service"] == "sales-order-agent"
        assert "checks" in data


class TestSession:
    def test_create_session(self, client):
        response = client.post("/session", json={"customer_name": "Test User"})
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["status"] == "active"

    def test_get_session_not_found(self, client):
        response = client.get("/session/nonexistent-session-id")
        assert response.status_code == 404
        assert "Session not found" in response.json()["detail"]

    def test_get_session_success(self, client, sample_session):
        session_id = sample_session["session_id"]
        response = client.get(f"/session/{session_id}")
        assert response.status_code == 200
        assert response.json()["id"] == session_id


class TestChat:
    def test_chat_without_session(self, client):
        response = client.post("/chat", json={"message": "Halo"})
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "session_id" in data
        assert "request_id" in data

    def test_chat_empty_message(self, client):
        response = client.post("/chat", json={"message": ""})
        assert response.status_code == 422

    def test_chat_message_too_long(self, client):
        response = client.post("/chat", json={"message": "x" * 2001})
        assert response.status_code == 422

    def test_chat_invalid_session_id(self, client):
        response = client.post("/chat", json={"message": "Halo", "session_id": "invalid!@#"})
        assert response.status_code == 422
```

- [ ] **Step 2: Run tests**

Run: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/test_api.py -v`

- [ ] **Step 3: Commit**

```bash
git add tests/test_api.py
git commit -m "test: add API error handling tests (404, validation)"
```

### Task 11: Add database unit tests

**Files:**
- Create: `tests/test_database.py`

**Interfaces:**
- Consumes: existing database functions
- Produces: database unit tests

- [ ] **Step 1: Create tests/test_database.py**

```python
import pytest
from src.data.database import (
    init_db, search_products, get_product_by_id,
    get_product_variants, get_price_tier, get_stock_by_product,
    create_session, get_session, save_message, get_conversation_history,
    create_quote
)


class TestDatabaseProducts:
    def test_search_products_returns_results(self):
        results = search_products("polo")
        assert len(results) > 0

    def test_search_products_by_category(self):
        results = search_products("", "Kaos")
        assert len(results) > 0
        assert all(r["category"] == "Kaos" for r in results)

    def test_get_product_by_id(self):
        product = get_product_by_id(1)
        assert product is not None
        assert product["name"] == "Polo Premium Cotton"

    def test_get_product_by_invalid_id(self):
        product = get_product_by_id(9999)
        assert product is None

    def test_get_product_variants(self):
        variants = get_product_variants(1)
        assert len(variants) > 0
        assert "color" in variants[0]


class TestDatabasePricing:
    def test_get_price_tier(self):
        tier = get_price_tier(1, 100)
        assert tier is not None
        assert tier["price_per_unit"] == 80000

    def test_get_price_tier_invalid(self):
        tier = get_price_tier(9999, 100)
        assert tier is None


class TestDatabaseStock:
    def test_get_stock_by_product(self):
        stock = get_stock_by_product(1)
        assert len(stock) > 0
        assert "quantity" in stock[0]


class TestDatabaseSession:
    def test_create_and_get_session(self):
        session = create_session("test-session-123", "Test User")
        assert session["id"] == "test-session-123"

        retrieved = get_session("test-session-123")
        assert retrieved is not None
        assert retrieved["customer_name"] == "Test User"

    def test_get_invalid_session(self):
        session = get_session("nonexistent")
        assert session is None


class TestDatabaseConversation:
    def test_save_and_get_history(self):
        create_session("test-conv-123", "Test")
        save_message("test-conv-123", "user", "Halo")
        save_message("test-conv-123", "assistant", "Halo! Ada yang bisa saya bantu?")

        history = get_conversation_history("test-conv-123")
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"
```

- [ ] **Step 2: Run tests**

Run: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/test_database.py -v`

- [ ] **Step 3: Commit**

```bash
git add tests/test_database.py
git commit -m "test: add database unit tests"
```

---

## Final Verification

### Task 12: Run all tests and verify

**Files:**
- None (verification only)

- [ ] **Step 1: Run all tests**

Run: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/test_tools.py tests/test_api.py tests/test_database.py -v`

- [ ] **Step 2: Verify all tests pass**

Expected: All tests should pass. If any fail, fix them.

- [ ] **Step 3: Run syntax check on all modified files**

```powershell
D:\Jeli\myenv\Scripts\python.exe -m py_compile src/api/models.py
D:\Jeli\myenv\Scripts\python.exe -m py_compile src/api/chat.py
D:\Jeli\myenv\Scripts\python.exe -m py_compile src/api/session.py
D:\Jeli\myenv\Scripts\python.exe -m py_compile src/api/health.py
D:\Jeli\myenv\Scripts\python.exe -m py_compile src/agents/nodes.py
D:\Jeli\myenv\Scripts\python.exe -m py_compile src/agents/graph.py
D:\Jeli\myenv\Scripts\python.exe -m py_compile src/config/settings.py
D:\Jeli\myenv\Scripts\python.exe -m py_compile src/main.py
```

- [ ] **Step 4: Final commit with all changes**

```bash
git add -A
git commit -m "feat: complete backend hardening (error handling, async, type safety, tests)"
```

- [ ] **Step 5: Push to GitHub**

```bash
git push origin main
```
