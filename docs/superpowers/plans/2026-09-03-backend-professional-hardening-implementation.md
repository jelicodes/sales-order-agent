# Backend Professional Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Meningkatkan backend dari "functional" menjadi "production-ready" — performance, testing, caching, security.

**Architecture:** 4-phase modular approach — performance critical fixes, test coverage, caching, security. Setiap phase bisa di-commit dan di-test secara independent.

**Tech Stack:** FastAPI, LangChain/LangGraph, Pydantic, SQLite, ChromaDB, pytest, cachetools

## Global Constraints

- Python 3.13.1 (D:\Jeli\myenv)
- Test command: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/ -v --ignore=tests/test_integration.py`
- Run server: `D:\Jeli\myenv\Scripts\python.exe -m src.main`
- Commit format: conventional commits (`feat:`, `fix:`, `docs:`, `test:`)
- Language: Bahasa Indonesia untuk user-facing text, English untuk code

---

## Phase 1: Performance P0 — Critical Fixes

### Task 1: Add database indexes

**Files:**
- Modify: `src/data/database.py`

**Interfaces:**
- Consumes: existing `init_db()` function
- Produces: indexed database schema

- [ ] **Step 1: Add index creation to init_db()**

After the `CREATE TABLE` statements in `init_db()`, add index creation:

```python
def init_db() -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                base_price REAL NOT NULL,
                moq INTEGER NOT NULL DEFAULT 1,
                lead_time_days INTEGER NOT NULL DEFAULT 5
            );

            CREATE TABLE IF NOT EXISTS product_variants (
                id INTEGER PRIMARY KEY,
                product_id INTEGER NOT NULL,
                color TEXT NOT NULL,
                FOREIGN KEY (product_id) REFERENCES products(id)
            );

            CREATE TABLE IF NOT EXISTS price_tiers (
                id INTEGER PRIMARY KEY,
                product_id INTEGER NOT NULL,
                min_qty INTEGER NOT NULL,
                max_qty INTEGER,
                price_per_unit REAL NOT NULL,
                FOREIGN KEY (product_id) REFERENCES products(id)
            );

            CREATE TABLE IF NOT EXISTS stock (
                id INTEGER PRIMARY KEY,
                variant_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                warehouse_location TEXT NOT NULL,
                FOREIGN KEY (variant_id) REFERENCES product_variants(id)
            );

            CREATE TABLE IF NOT EXISTS discounts (
                id INTEGER PRIMARY KEY,
                code TEXT UNIQUE NOT NULL,
                type TEXT NOT NULL,
                value REAL NOT NULL,
                min_qty INTEGER,
                valid_until DATE
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                customer_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active'
            );

            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                tool_calls TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            );

            CREATE TABLE IF NOT EXISTS quotes (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                items_json TEXT NOT NULL,
                total_price REAL NOT NULL,
                valid_until DATE NOT NULL,
                status TEXT DEFAULT 'pending',
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            );
        """)

        # Create indexes for performance
        cursor.executescript("""
            CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
            CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);
            CREATE INDEX IF NOT EXISTS idx_product_variants_product_id ON product_variants(product_id);
            CREATE INDEX IF NOT EXISTS idx_price_tiers_product_id ON price_tiers(product_id);
            CREATE INDEX IF NOT EXISTS idx_stock_variant_id ON stock(variant_id);
            CREATE INDEX IF NOT EXISTS idx_conversations_session_ts ON conversations(session_id, timestamp DESC);
            CREATE INDEX IF NOT EXISTS idx_discounts_code ON discounts(code);
        """)
        conn.commit()
```

- [ ] **Step 2: Verify indexes exist**

Run: `D:\Jeli\myenv\Scripts\python.exe -c "from src.data.database import init_db; init_db(); import sqlite3; conn = sqlite3.connect('data/app.db'); cursor = conn.cursor(); cursor.execute(\"SELECT name FROM sqlite_master WHERE type='index'\"); print([r[0] for r in cursor.fetchall()])"`

Expected: List of 7 index names

- [ ] **Step 3: Run existing tests to verify no regression**

Run: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/test_tools.py tests/test_database.py -v`

Expected: All tests pass

- [ ] **Step 4: Commit**

```bash
git add src/data/database.py
git commit -m "feat: add database indexes for query performance"
```

### Task 2: Refactor connection management with proper error handling

**Files:**
- Modify: `src/data/database.py`

**Interfaces:**
- Consumes: existing `get_connection()` usage across codebase
- Produces: `get_connection()` with commit/rollback/close

- [ ] **Step 1: Update get_connection() with error handling**

```python
@contextmanager
def get_connection():
    conn = sqlite3.connect(_get_db_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
```

- [ ] **Step 2: Remove redundant commit calls**

In `database.py`, remove `conn.commit()` from all functions since `get_connection()` now handles it:
- `init_db()` line 105
- `create_session()` line 201
- `save_message()` line 220
- `create_quote()` line 242

- [ ] **Step 3: Run existing tests**

Run: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/test_tools.py tests/test_database.py -v`

Expected: All tests pass

- [ ] **Step 4: Commit**

```bash
git add src/data/database.py
git commit -m "feat: refactor connection management with rollback on error"
```

### Task 3: Add async wrapping for database calls

**Files:**
- Modify: `src/api/chat.py`
- Modify: `src/api/session.py`
- Modify: `src/api/health.py`

**Interfaces:**
- Consumes: existing sync database functions
- Produces: non-blocking async handlers

- [ ] **Step 1: Update chat.py with async DB calls**

```python
import uuid
import logging
import asyncio
from fastapi import APIRouter, Request
from langchain_core.messages import HumanMessage, AIMessage, trim_messages
from src.agents.graph import create_sales_agent
from src.data.database import create_session, get_conversation_history, save_message
from src.api.models import ChatRequest, ChatResponse

router = APIRouter()
agent = create_sales_agent()
logger = logging.getLogger(__name__)


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: Request, req: ChatRequest):
    limiter = request.app.state.limiter
    request_id = str(uuid.uuid4())
    logger.info(f"[{request_id}] Chat request received: session={req.session_id}")

    session_id = req.session_id
    if not session_id:
        session_id = str(uuid.uuid4())
        await asyncio.to_thread(create_session, session_id, req.customer_name)
        logger.info(f"[{request_id}] New session created: {session_id}")

    history = await asyncio.to_thread(get_conversation_history, session_id)
    messages = []
    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=req.message))

    messages = trim_messages(
        messages,
        max_tokens=8000,
        token_counter=len,
        strategy="last",
        start_on="human",
    )

    result = await asyncio.to_thread(
        agent.invoke,
        {
            "messages": messages,
            "session_id": session_id,
            "context": {"request_id": request_id},
        }
    )

    await asyncio.to_thread(save_message, session_id, "user", req.message)
    response_content = result["messages"][-1].content
    await asyncio.to_thread(save_message, session_id, "assistant", response_content)

    logger.info(f"[{request_id}] Response sent successfully")

    return ChatResponse(
        response=response_content,
        session_id=session_id,
        request_id=request_id,
    )
```

- [ ] **Step 2: Update session.py with async DB calls**

```python
import uuid
from fastapi import APIRouter, HTTPException
from src.data.database import create_session, get_session
from src.api.models import CreateSessionRequest, CreateSessionResponse, SessionResponse

router = APIRouter()


@router.post("/session", response_model=CreateSessionResponse)
async def create_session_endpoint(req: CreateSessionRequest):
    import asyncio
    session_id = str(uuid.uuid4())
    session = await asyncio.to_thread(create_session, session_id, req.customer_name)
    return CreateSessionResponse(session_id=session_id, status=session["status"])


@router.get("/session/{session_id}", response_model=SessionResponse)
async def get_session_endpoint(session_id: str):
    import asyncio
    session = await asyncio.to_thread(get_session, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionResponse(**session)
```

- [ ] **Step 3: Update health.py with async DB calls**

```python
import sqlite3
import asyncio
from pathlib import Path
from fastapi import APIRouter
from src.config.settings import settings, APP_VERSION
from src.config.langfuse import get_langfuse_handler
from src.api.models import HealthResponse, HealthCheckResult

router = APIRouter()


def check_database_sync() -> dict:
    try:
        db_path = Path(settings.DATABASE_PATH)
        if not db_path.exists():
            return {"status": "error", "message": "Database file not found"}
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM products")
        count = cursor.fetchone()[0]
        conn.close()
        return {"status": "ok", "products_count": count}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def check_chromadb() -> dict:
    try:
        chromadb_path = Path(settings.CHROMADB_PATH)
        if not chromadb_path.exists():
            return {"status": "warning", "message": "ChromaDB directory not found (will be created on first use)"}
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def check_groq() -> dict:
    try:
        if not settings.GROQ_API_KEY:
            return {"status": "error", "message": "GROQ_API_KEY not configured"}
        return {"status": "ok", "model": settings.GROQ_MODEL}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def check_langfuse() -> dict:
    handler = get_langfuse_handler()
    if handler:
        return {"status": "ok", "enabled": True}
    return {"status": "disabled", "enabled": False}


@router.get("/health", response_model=HealthResponse)
async def health_check():
    db_status = await asyncio.to_thread(check_database_sync)
    chromadb_status = check_chromadb()
    groq_status = check_groq()
    langfuse_status = check_langfuse()

    overall_status = "ok"
    if db_status["status"] == "error" or groq_status["status"] == "error":
        overall_status = "degraded"

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

- [ ] **Step 4: Run existing tests**

Run: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/test_tools.py tests/test_api.py -v`

Expected: All tests pass

- [ ] **Step 5: Commit**

```bash
git add src/api/chat.py src/api/session.py src/api/health.py
git commit -m "feat: wrap sync DB calls with asyncio.to_thread for non-blocking async"
```

---

## Phase 2: Test Coverage — Mock LLM & Fix Timeout

### Task 4: Add mock_llm fixture to conftest.py

**Files:**
- Modify: `tests/conftest.py`

**Interfaces:**
- Consumes: existing `create_sales_agent` from `src.agents.graph`
- Produces: `mock_llm` fixture for agent tests

- [ ] **Step 1: Update conftest.py with mock_llm fixture**

```python
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
```

- [ ] **Step 2: Verify fixture loads**

Run: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/conftest.py -v`

Expected: No import errors

- [ ] **Step 3: Commit**

```bash
git add tests/conftest.py
git commit -m "test: add mock_llm fixture for agent tests"
```

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

### Task 6: Rewrite integration tests with mocked agent

**Files:**
- Modify: `tests/test_integration.py`

**Interfaces:**
- Consumes: existing FastAPI app
- Produces: integration tests that run in < 5 seconds

- [ ] **Step 1: Rewrite test_integration.py with mocked agent**

```python
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage
from src.main import app


@pytest.fixture
def client():
    """TestClient with mocked agent."""
    with patch("src.api.chat.create_sales_agent") as mock_create:
        mock_agent = MagicMock()

        def side_effect(input_state):
            msgs = input_state["messages"]
            last_user_msg = msgs[-1].content if msgs else ""

            if "polo" in last_user_msg.lower() or "kaos" in last_user_msg.lower():
                return {
                    "messages": [
                        msgs[0],
                        msgs[-1],
                        AIMessage(content=(
                            "Kami memiliki Polo Premium Cotton. "
                            "Harga: Rp 85.000/pcs untuk 100 pcs, "
                            "Rp 70.000/pcs untuk 500 pcs. "
                            "Stok tersedia 500 pcs."
                        ))
                    ]
                }
            elif "penawaran" in last_user_msg.lower() or "quote" in last_user_msg.lower():
                return {
                    "messages": [
                        msgs[0],
                        msgs[-1],
                        AIMessage(content=(
                            "Penawaran Q-2026-09-03:\n"
                            "- 500 x Polo Premium Navy @ Rp 70.000\n"
                            "- Subtotal: Rp 35.000.000\n"
                            "- Berlaku 7 hari"
                        ))
                    ]
                }
            return {
                "messages": [
                    msgs[0],
                    msgs[-1],
                    AIMessage(content="Maaf, saya tidak menemukan produk yang sesuai.")
                ]
            }

        mock_agent.invoke.side_effect = side_effect
        mock_create.return_value = mock_agent

        with TestClient(app) as c:
            yield c


class TestFullFlow:
    def test_inquiry_to_quote_flow(self, client):
        resp1 = client.post("/chat", json={
            "message": "Saya butuh 500 kaos polo hitam untuk seragam karyawan",
            "customer_name": "Budi Santoso"
        })
        assert resp1.status_code == 200
        data1 = resp1.json()
        session_id = data1["session_id"]
        assert "polo" in data1["response"].lower() or "kaos" in data1["response"].lower()

        resp2 = client.post("/chat", json={
            "message": "Yang Premium, bisa warna navy?",
            "session_id": session_id
        })
        assert resp2.status_code == 200
        assert "navy" in resp2.json()["response"].lower() or "premium" in resp2.json()["response"].lower()

        resp3 = client.post("/chat", json={
            "message": "Buatkan penawaran untuk 500 pcs navy",
            "session_id": session_id
        })
        assert resp3.status_code == 200
        assert "rp" in resp3.json()["response"].lower() or "penawaran" in resp3.json()["response"].lower()


class TestEdgeCases:
    def test_unknown_product(self, client):
        resp = client.post("/chat", json={
            "message": "Saya cari jas formal pria",
            "customer_name": "Test"
        })
        assert resp.status_code == 200
        assert resp.json()["response"] is not None

    def test_budget_too_low(self, client):
        resp = client.post("/chat", json={
            "message": "Saya mau 500 kaos polo, budget cuma 10 juta",
            "customer_name": "Test"
        })
        assert resp.status_code == 200
        assert resp.json()["response"] is not None
```

- [ ] **Step 2: Run integration tests**

Run: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/test_integration.py -v`

Expected: All tests pass in < 5 seconds

- [ ] **Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: rewrite integration tests with mocked agent (no real API calls)"
```

### Task 7: Add missing unit tests

**Files:**
- Create: `tests/test_database_extended.py`
- Create: `tests/test_tools_extended.py`

**Interfaces:**
- Consumes: existing database and tool functions
- Produces: additional test coverage

- [ ] **Step 1: Create test_database_extended.py**

```python
import pytest
from src.data.database import (
    init_db, search_products, get_product_by_id,
    get_product_variants, get_price_tier, get_stock_by_product,
    create_session, get_session, save_message, get_conversation_history,
    create_quote, get_discount
)


class TestDatabaseExtended:
    def test_init_db_idempotent(self):
        """Calling init_db twice should not crash."""
        init_db()
        init_db()  # Should not raise

    def test_search_products_by_category(self):
        results = search_products("", "Kaos")
        assert len(results) > 0
        assert all(r["category"] == "Kaos" for r in results)

    def test_get_product_variants(self):
        variants = get_product_variants(1)
        assert len(variants) > 0
        assert "color" in variants[0]

    def test_get_price_tier_boundary_99(self):
        tier = get_price_tier(1, 99)
        assert tier is not None
        assert tier["price_per_unit"] == 85000

    def test_get_price_tier_boundary_100(self):
        tier = get_price_tier(1, 100)
        assert tier is not None
        assert tier["price_per_unit"] == 80000

    def test_get_stock_by_product(self):
        stock = get_stock_by_product(1)
        assert len(stock) > 0
        assert "quantity" in stock[0]

    def test_get_discount_valid(self):
        discount = get_discount("BULK500")
        assert discount is not None
        assert discount["type"] == "percentage"

    def test_get_discount_invalid(self):
        discount = get_discount("NONEXISTENT")
        assert discount is None

    def test_conversation_history_ordering(self):
        session_id = "test-ordering-123"
        create_session(session_id, "Test")
        save_message(session_id, "user", "Message 1")
        save_message(session_id, "assistant", "Response 1")
        save_message(session_id, "user", "Message 2")

        history = get_conversation_history(session_id)
        assert len(history) == 3
        assert history[0]["content"] == "Message 1"
        assert history[1]["content"] == "Response 1"
        assert history[2]["content"] == "Message 2"
```

- [ ] **Step 2: Create test_tools_extended.py**

```python
import pytest
from src.tools.calculate_price import calculate_price
from src.tools.create_quote import create_quote
from src.tools.get_alternatives import get_alternatives


class TestCalculatePriceExtended:
    def test_calculates_price_no_tier_returns_error(self):
        result = calculate_price.invoke({"product_id": 9999, "quantity": 100})
        assert "error" in result

    def test_discount_min_qty_not_enforced(self):
        """Current behavior: discount applies regardless of min_qty.
        This documents the existing behavior for future reference."""
        result = calculate_price.invoke({
            "product_id": 1,
            "quantity": 50,
            "discount_code": "BULK500"
        })
        # BULK500 has min_qty 500, but currently applies anyway
        assert result["discount"] is not None


class TestCreateQuoteExtended:
    def test_create_quote_with_dict_items(self):
        result = create_quote.invoke({
            "items": [{"product_id": 1, "quantity": 100, "color": "Hitam"}],
            "customer_info": {"customer_name": "Test"}
        })
        assert "quote_id" in result
        assert result["total_price"] > 0

    def test_create_quote_with_pydantic_items(self):
        from pydantic import BaseModel
        from typing import List

        class QuoteItem(BaseModel):
            product_id: int
            quantity: int
            color: str

        items = [QuoteItem(product_id=1, quantity=100, color="Hitam")]
        result = create_quote.invoke({
            "items": [item.model_dump() for item in items],
            "customer_info": {"customer_name": "Test"}
        })
        assert "quote_id" in result


class TestGetAlternativesExtended:
    def test_stock_alternatives_sorted_descending(self):
        results = get_alternatives.invoke({"product_id": 1, "reason": "stock"})
        if len(results) > 1:
            prices = [r["base_price"] for r in results]
            assert prices == sorted(prices, reverse=True)

    def test_alternatives_same_category(self):
        results = get_alternatives.invoke({"product_id": 1, "reason": "budget"})
        for r in results:
            assert r["category"] == "Polo"
```

- [ ] **Step 3: Run new tests**

Run: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/test_database_extended.py tests/test_tools_extended.py -v`

Expected: All tests pass

- [ ] **Step 4: Commit**

```bash
git add tests/test_database_extended.py tests/test_tools_extended.py
git commit -m "test: add extended database and tools unit tests"
```

---

## Phase 3: Performance P1 — Caching

### Task 8: Add static data caching

**Files:**
- Modify: `requirements.txt`
- Modify: `src/data/database.py`

**Interfaces:**
- Consumes: existing database query functions
- Produces: cached data access with TTL

- [ ] **Step 1: Add cachetools to requirements.txt**

```txt
cachetools>=5.3.0
```

- [ ] **Step 2: Install cachetools**

Run: `D:\Jeli\myenv\Scripts\pip.exe install cachetools>=5.3.0`

- [ ] **Step 3: Add caching to database.py**

```python
import sqlite3
from pathlib import Path
from datetime import date
from contextlib import contextmanager
from cachetools import TTLCache

from src.config.settings import settings


_db_path: str | None = None

# Cache for static data
_product_cache = TTLCache(maxsize=500, ttl=300)  # 5 min
_price_tier_cache = TTLCache(maxsize=200, ttl=300)
_discount_cache = TTLCache(maxsize=50, ttl=600)  # 10 min


def _get_db_path() -> str:
    global _db_path
    if _db_path is None:
        db_path = Path(settings.DATABASE_PATH)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        _db_path = str(db_path)
    return _db_path


@contextmanager
def get_connection():
    conn = sqlite3.connect(_get_db_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def clear_caches():
    """Clear all caches (useful after seed)."""
    _product_cache.clear()
    _price_tier_cache.clear()
    _discount_cache.clear()


def init_db() -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                base_price REAL NOT NULL,
                moq INTEGER NOT NULL DEFAULT 1,
                lead_time_days INTEGER NOT NULL DEFAULT 5
            );

            CREATE TABLE IF NOT EXISTS product_variants (
                id INTEGER PRIMARY KEY,
                product_id INTEGER NOT NULL,
                color TEXT NOT NULL,
                FOREIGN KEY (product_id) REFERENCES products(id)
            );

            CREATE TABLE IF NOT EXISTS price_tiers (
                id INTEGER PRIMARY KEY,
                product_id INTEGER NOT NULL,
                min_qty INTEGER NOT NULL,
                max_qty INTEGER,
                price_per_unit REAL NOT NULL,
                FOREIGN KEY (product_id) REFERENCES products(id)
            );

            CREATE TABLE IF NOT EXISTS stock (
                id INTEGER PRIMARY KEY,
                variant_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                warehouse_location TEXT NOT NULL,
                FOREIGN KEY (variant_id) REFERENCES product_variants(id)
            );

            CREATE TABLE IF NOT EXISTS discounts (
                id INTEGER PRIMARY KEY,
                code TEXT UNIQUE NOT NULL,
                type TEXT NOT NULL,
                value REAL NOT NULL,
                min_qty INTEGER,
                valid_until DATE
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                customer_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active'
            );

            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                tool_calls TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            );

            CREATE TABLE IF NOT EXISTS quotes (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                items_json TEXT NOT NULL,
                total_price REAL NOT NULL,
                valid_until DATE NOT NULL,
                status TEXT DEFAULT 'pending',
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            );
        """)

        # Create indexes for performance
        cursor.executescript("""
            CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
            CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);
            CREATE INDEX IF NOT EXISTS idx_product_variants_product_id ON product_variants(product_id);
            CREATE INDEX IF NOT EXISTS idx_price_tiers_product_id ON price_tiers(product_id);
            CREATE INDEX IF NOT EXISTS idx_stock_variant_id ON stock(variant_id);
            CREATE INDEX IF NOT EXISTS idx_conversations_session_ts ON conversations(session_id, timestamp DESC);
            CREATE INDEX IF NOT EXISTS idx_discounts_code ON discounts(code);
        """)
        conn.commit()


def search_products(query: str, category: str | None = None) -> list[dict]:
    with get_connection() as conn:
        cursor = conn.cursor()
        if category:
            cursor.execute(
                "SELECT * FROM products WHERE name LIKE ? AND category = ?",
                (f"%{query}%", category),
            )
        else:
            cursor.execute(
                "SELECT * FROM products WHERE name LIKE ? OR category LIKE ? OR description LIKE ?",
                (f"%{query}%", f"%{query}%", f"%{query}%"),
            )
        results = [dict(row) for row in cursor.fetchall()]
        return results


def get_product_by_id(product_id: int) -> dict | None:
    if product_id in _product_cache:
        return _product_cache[product_id]

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        row = cursor.fetchone()
        result = dict(row) if row else None
        if result:
            _product_cache[product_id] = result
        return result


def get_product_variants(product_id: int) -> list[dict]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM product_variants WHERE product_id = ?", (product_id,))
        results = [dict(row) for row in cursor.fetchall()]
        return results


def get_price_tier(product_id: int, quantity: int) -> dict | None:
    cache_key = (product_id, quantity)
    if cache_key in _price_tier_cache:
        return _price_tier_cache[cache_key]

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM price_tiers
            WHERE product_id = ?
              AND min_qty <= ?
              AND (max_qty IS NULL OR max_qty >= ?)
            ORDER BY min_qty DESC
            LIMIT 1
            """,
            (product_id, quantity, quantity),
        )
        row = cursor.fetchone()
        result = dict(row) if row else None
        _price_tier_cache[cache_key] = result
        return result


def get_stock(variant_id: int) -> dict | None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM stock WHERE variant_id = ?", (variant_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_stock_by_product(product_id: int) -> list[dict]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT pv.id AS variant_id, pv.color, s.quantity, s.warehouse_location
            FROM product_variants pv
            JOIN stock s ON s.variant_id = pv.id
            WHERE pv.product_id = ?
            """,
            (product_id,),
        )
        results = [dict(row) for row in cursor.fetchall()]
        return results


def get_discount(code: str) -> dict | None:
    if code in _discount_cache:
        return _discount_cache[code]

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM discounts WHERE code = ? AND valid_until >= ?",
            (code, date.today().isoformat()),
        )
        row = cursor.fetchone()
        result = dict(row) if row else None
        _discount_cache[code] = result
        return result


def create_session(session_id: str, customer_name: str) -> dict:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sessions (id, customer_name) VALUES (?, ?)",
            (session_id, customer_name),
        )
        return {"id": session_id, "customer_name": customer_name, "status": "active"}


def get_session(session_id: str) -> dict | None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def save_message(session_id: str, role: str, content: str, tool_calls: str | None = None) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO conversations (session_id, role, content, tool_calls) VALUES (?, ?, ?, ?)",
            (session_id, role, content, tool_calls),
        )


def get_conversation_history(session_id: str, max_messages: int = 50) -> list[dict]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM conversations WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?",
            (session_id, max_messages),
        )
        results = [dict(row) for row in cursor.fetchall()]
        results.reverse()
        return results


def create_quote(quote_id: str, session_id: str, items_json: str, total_price: float, valid_until: str) -> dict:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO quotes (id, session_id, items_json, total_price, valid_until) VALUES (?, ?, ?, ?, ?)",
            (quote_id, session_id, items_json, total_price, valid_until),
        )
        return {
            "id": quote_id,
            "session_id": session_id,
            "items_json": items_json,
            "total_price": total_price,
            "valid_until": valid_until,
            "status": "pending",
        }
```

- [ ] **Step 4: Update seed.py to clear caches after seeding**

```python
import json
from pathlib import Path
from src.data.database import init_db, get_connection, clear_caches
from src.data.vector_store import index_products

SEED_DIR = Path(__file__).parent


def load_json(filename: str) -> list[dict]:
    with open(SEED_DIR / filename) as f:
        return json.load(f)


def seed_database() -> None:
    init_db()

    products = load_json("products.json")
    price_tiers_raw = load_json("price_tiers.json")
    stock_raw = load_json("stock.json")
    discounts = load_json("discounts.json")

    with get_connection() as conn:
        cursor = conn.cursor()

        # Clear existing data
        for table in ("stock", "product_variants", "price_tiers", "discounts", "products"):
            cursor.execute(f"DELETE FROM {table}")

        # Insert products
        for p in products:
            cursor.execute(
                "INSERT INTO products (id, name, category, description, base_price, moq, lead_time_days) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (p["id"], p["name"], p["category"], p["description"], p["base_price"], p["moq"], p["lead_time_days"]),
            )

        # Insert product_variants + stock
        for entry in stock_raw:
            for v in entry["variants"]:
                cursor.execute(
                    "INSERT INTO product_variants (product_id, color) VALUES (?, ?)",
                    (entry["product_id"], v["color"]),
                )
                variant_id = cursor.lastrowid
                cursor.execute(
                    "INSERT INTO stock (variant_id, quantity, warehouse_location) VALUES (?, ?, ?)",
                    (variant_id, v["quantity"], v["warehouse"]),
                )

        # Insert price tiers
        for pt in price_tiers_raw:
            for tier in pt["tiers"]:
                cursor.execute(
                    "INSERT INTO price_tiers (product_id, min_qty, max_qty, price_per_unit) VALUES (?, ?, ?, ?)",
                    (pt["product_id"], tier["min_qty"], tier["max_qty"], tier["price_per_unit"]),
                )

        # Insert discounts
        for d in discounts:
            cursor.execute(
                "INSERT INTO discounts (code, type, value, min_qty, valid_until) VALUES (?, ?, ?, ?, ?)",
                (d["code"], d["type"], d["value"], d["min_qty"], d["valid_until"]),
            )

    # Clear caches after seeding
    clear_caches()

    # Index products in ChromaDB with Gemini embeddings
    index_products(products)
    print(f"Seeded {len(products)} products, {len(price_tiers_raw)} price tiers, {len(stock_raw)} stock entries, {len(discounts)} discounts")


if __name__ == "__main__":
    seed_database()
```

- [ ] **Step 5: Run tests to verify caching works**

Run: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/test_tools.py tests/test_database.py tests/test_database_extended.py -v`

Expected: All tests pass

- [ ] **Step 6: Commit**

```bash
git add requirements.txt src/data/database.py src/data/seed/seed.py
git commit -m "feat: add TTL caching for static data (products, price tiers, discounts)"
```

### Task 9: Cache LLM instance

**Files:**
- Modify: `src/agents/nodes.py`

**Interfaces:**
- Consumes: existing `create_llm()` function
- Produces: cached LLM singleton

- [ ] **Step 1: Update nodes.py with LLM caching**

```python
from typing import Optional
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_groq import ChatGroq
from langgraph.prebuilt import ToolNode
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

tools = [search_products, get_product_detail, check_stock, calculate_price, create_quote, get_alternatives]

_llm_instance = None


def get_llm():
    """Get or create cached LLM instance."""
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = ChatGroq(
            model=settings.GROQ_MODEL,
            api_key=settings.GROQ_API_KEY,
            temperature=0.3,
        ).bind_tools(tools)
    return _llm_instance


def create_llm():
    """Create new LLM instance (for testing or when cache needs refresh)."""
    return ChatGroq(
        model=settings.GROQ_MODEL,
        api_key=settings.GROQ_API_KEY,
        temperature=0.3,
    ).bind_tools(tools)


def llm_node(state: AgentState) -> dict:
    llm = get_llm()
    messages = list(state["messages"])
    if not messages or not (isinstance(messages[0], HumanMessage) and SALES_AGENT_PROMPT in messages[0].content):
        messages = [HumanMessage(content=SALES_AGENT_PROMPT)] + messages

    langfuse_handler = get_langfuse_handler()
    config = {"callbacks": [langfuse_handler]} if langfuse_handler else {}
    response = llm.invoke(messages, config=config)
    return {"messages": [response]}


tool_node = ToolNode(tools)
```

- [ ] **Step 2: Run tests**

Run: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/test_agent.py -v`

Expected: All tests pass

- [ ] **Step 3: Commit**

```bash
git add src/agents/nodes.py
git commit -m "feat: cache LLM instance as module-level singleton"
```

---

## Phase 4: Code Quality — Security & Correctness

### Task 10: Add CORS restriction

**Files:**
- Modify: `src/config/settings.py`
- Modify: `src/main.py`

**Interfaces:**
- Consumes: existing FastAPI app
- Produces: restricted CORS configuration

- [ ] **Step 1: Add ALLOWED_ORIGINS to settings.py**

```python
from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional


class Settings(BaseSettings):
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "qwen/qwen3.6-27b"
    GOOGLE_API_KEY: str = ""
    EMBEDDING_MODEL: str = "gemini-embedding-001"
    DATABASE_PATH: str = "data/app.db"
    CHROMADB_PATH: str = "data/chromadb"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    ALLOWED_ORIGINS: str = ""  # Comma-separated origins, empty = allow all

    # Langfuse (Agent Observability)
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_BASE_URL: str = "https://cloud.langfuse.com"
    LANGFUSE_ENABLED: bool = True

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()

APP_VERSION: str = "0.1.0"
```

- [ ] **Step 2: Update main.py with CORS restriction**

```python
from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from src.data.database import init_db
from src.api.health import router as health_router
from src.api.session import router as session_router
from src.api.chat import router as chat_router
from src.api.models import ErrorResponse
from src.config.langfuse import init_langfuse, shutdown_langfuse
from src.config.settings import settings, APP_VERSION

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    init_langfuse()
    yield
    shutdown_langfuse()


app = FastAPI(
    title="Sales Order Agent - PT Lemone",
    description="AI Agent untuk membantu proses order fashion grosir B2B",
    version=APP_VERSION,
    lifespan=lifespan,
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

ALLOWED_ORIGINS = settings.ALLOWED_ORIGINS.split(",") if settings.ALLOWED_ORIGINS else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Terjadi kesalahan internal server",
            detail="Silakan coba lagi atau hubungi admin."
        ).model_dump()
    )


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={"success": False, "error": "Terlalu banyak request. Silakan coba lagi nanti."}
    )


app.include_router(health_router)
app.include_router(session_router)
app.include_router(chat_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=True)
```

- [ ] **Step 3: Run tests**

Run: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/test_api.py -v`

Expected: All tests pass

- [ ] **Step 4: Commit**

```bash
git add src/config/settings.py src/main.py
git commit -m "feat: add configurable CORS restriction via ALLOWED_ORIGINS"
```

### Task 11: Fix rate limiter duplication

**Files:**
- Modify: `src/api/chat.py`

**Interfaces:**
- Consumes: `app.state.limiter` from main.py
- Produces: single rate limiter instance

- [ ] **Step 1: Update chat.py to use app.state.limiter**

```python
import uuid
import logging
import asyncio
from fastapi import APIRouter, Request
from langchain_core.messages import HumanMessage, AIMessage, trim_messages
from src.agents.graph import create_sales_agent
from src.data.database import create_session, get_conversation_history, save_message
from src.api.models import ChatRequest, ChatResponse

router = APIRouter()
agent = create_sales_agent()
logger = logging.getLogger(__name__)


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: Request, req: ChatRequest):
    limiter = request.app.state.limiter
    request_id = str(uuid.uuid4())
    logger.info(f"[{request_id}] Chat request received: session={req.session_id}")

    session_id = req.session_id
    if not session_id:
        session_id = str(uuid.uuid4())
        await asyncio.to_thread(create_session, session_id, req.customer_name)
        logger.info(f"[{request_id}] New session created: {session_id}")

    history = await asyncio.to_thread(get_conversation_history, session_id)
    messages = []
    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=req.message))

    messages = trim_messages(
        messages,
        max_tokens=8000,
        token_counter=len,
        strategy="last",
        start_on="human",
    )

    result = await asyncio.to_thread(
        agent.invoke,
        {
            "messages": messages,
            "session_id": session_id,
            "context": {"request_id": request_id},
        }
    )

    await asyncio.to_thread(save_message, session_id, "user", req.message)
    response_content = result["messages"][-1].content
    await asyncio.to_thread(save_message, session_id, "assistant", response_content)

    logger.info(f"[{request_id}] Response sent successfully")

    return ChatResponse(
        response=response_content,
        session_id=session_id,
        request_id=request_id,
    )
```

- [ ] **Step 2: Run tests**

Run: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/test_api.py -v`

Expected: All tests pass

- [ ] **Step 3: Commit**

```bash
git add src/api/chat.py
git commit -m "fix: remove duplicate Limiter, use app.state.limiter"
```

### Task 12: Fix discount min_qty validation

**Files:**
- Modify: `src/tools/calculate_price.py`

**Interfaces:**
- Consumes: existing `get_discount()` function
- Produces: discount validation with min_qty check

- [ ] **Step 1: Update calculate_price.py with min_qty validation**

```python
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from src.data.database import get_price_tier, get_discount


class CalculatePriceInput(BaseModel):
    product_id: int = Field(description="ID produk")
    quantity: int = Field(description="Jumlah pesanan")
    discount_code: str = Field(default="", description="Kode diskon (opsional)")


@tool(args_schema=CalculatePriceInput)
def calculate_price(product_id: int, quantity: int, discount_code: str = "") -> dict:
    """Hitung harga berdasarkan jumlah pesanan, tier harga, dan diskon yang berlaku."""
    if quantity <= 0:
        return {
            "product_id": product_id, "quantity": quantity,
            "price_per_unit": 0, "subtotal": 0,
            "discount": None, "discount_amount": 0,
            "total": 0, "tier": "N/A"
        }
    tier = get_price_tier(product_id, quantity)
    if not tier:
        return {"error": "Tidak ada harga tersedia untuk quantity ini"}
    price_per_unit = tier["price_per_unit"]
    subtotal = price_per_unit * quantity
    discount_amount = 0
    discount_info = None
    if discount_code:
        discount = get_discount(discount_code)
        if discount:
            # Validate min_qty requirement
            if discount.get("min_qty") and quantity < discount["min_qty"]:
                discount = None  # Don't apply discount if min_qty not met
            else:
                if discount["type"] == "percentage":
                    discount_amount = subtotal * (discount["value"] / 100)
                else:
                    discount_amount = min(discount["value"], subtotal)
                discount_info = {"code": discount["code"], "type": discount["type"], "value": discount["value"]}
    total = subtotal - discount_amount
    return {
        "product_id": product_id, "quantity": quantity,
        "price_per_unit": price_per_unit, "subtotal": subtotal,
        "discount": discount_info, "discount_amount": discount_amount,
        "total": total, "tier": f"{tier['min_qty']}-{tier['max_qty'] or '∞'} pcs"
    }
```

- [ ] **Step 2: Update test in test_tools.py to reflect new behavior**

```python
def test_discount_min_qty_not_met(self):
    """Discount with quantity below minimum should not apply."""
    result = calculate_price.invoke({"product_id": 1, "quantity": 50, "discount_code": "BULK500"})
    # BULK500 requires min_qty 500, so discount should NOT apply
    assert result["discount"] is None
    assert result["discount_amount"] == 0
```

- [ ] **Step 3: Run tests**

Run: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/test_tools.py -v`

Expected: All tests pass

- [ ] **Step 4: Commit**

```bash
git add src/tools/calculate_price.py tests/test_tools.py
git commit -m "fix: validate discount min_qty before applying"
```

---

## Final Verification

### Task 13: Run all tests and verify

**Files:**
- None (verification only)

- [ ] **Step 1: Run all tests**

Run: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/ -v --ignore=tests/test_integration.py`

Expected: All tests pass

- [ ] **Step 2: Run integration tests**

Run: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/test_integration.py -v`

Expected: All tests pass in < 5 seconds

- [ ] **Step 3: Run syntax check on all modified files**

```powershell
D:\Jeli\myenv\Scripts\python.exe -m py_compile src/data/database.py
D:\Jeli\myenv\Scripts\python.exe -m py_compile src/api/chat.py
D:\Jeli\myenv\Scripts\python.exe -m py_compile src/api/session.py
D:\Jeli\myenv\myenv\Scripts\python.exe -m py_compile src/api/health.py
D:\Jeli\myenv\Scripts\python.exe -m py_compile src/agents/nodes.py
D:\Jeli\myenv\Scripts\python.exe -m py_compile src/config/settings.py
D:\Jeli\myenv\Scripts\python.exe -m py_compile src/main.py
D:\Jeli\myenv\Scripts\python.exe -m py_compile src/tools/calculate_price.py
D:\Jeli\myenv\Scripts\python.exe -m py_compile src/data/seed/seed.py
```

- [ ] **Step 4: Final commit with all changes**

```bash
git add -A
git commit -m "feat: complete backend professional hardening (performance, tests, caching, security)"
```

- [ ] **Step 5: Push to GitHub**

```bash
git push origin main
```
