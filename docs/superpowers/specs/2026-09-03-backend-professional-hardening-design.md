# Backend Professional Hardening — Design Spec

> **Goal:** Meningkatkan backend Sales Order Agent dari "functional" menjadi "production-ready" — reliable, tested, performant, dan secure.

**Current State:** 70 unit tests passing, 4 phases backend hardening selesai. Tapi evaluasi mendalam menemukan 8 HIGH issues, 16 MEDIUM, dan performance bottlenecks kritis.

---

## Phase 1: Performance P0 — Critical Fixes

### 1.1 Database Indexes

**Problem:** 0 indexes di 7 tabel. Setiap query = full table scan.

**Solution:** Tambahkan indexes di `init_db()`:

```sql
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);
CREATE INDEX IF NOT EXISTS idx_product_variants_product_id ON product_variants(product_id);
CREATE INDEX IF NOT EXISTS idx_price_tiers_product_id ON price_tiers(product_id);
CREATE INDEX IF NOT EXISTS idx_stock_variant_id ON stock(variant_id);
CREATE INDEX IF NOT EXISTS idx_conversations_session_ts ON conversations(session_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_discounts_code ON discounts(code);
```

**File:** `src/data/database.py` — tambah di `init_db()` setelah `CREATE TABLE`

### 1.2 Connection Management

**Problem:** Setiap DB call buka connection baru (8-15 per request). Tidak ada rollback on error.

**Solution:** Refactor `get_connection()` dengan proper error handling:

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

**File:** `src/data/database.py` — update `get_connection()`

### 1.3 Async DB Calls

**Problem:** `create_session()`, `get_conversation_history()`, `save_message()` blocking event loop.

**Solution:** Wrap semua sync DB calls di `chat.py` dengan `asyncio.to_thread`:

```python
# Before (blocking)
session = create_session(session_id, req.customer_name)

# After (non-blocking)
session = await asyncio.to_thread(create_session, session_id, req.customer_name)
```

**Files:** `src/api/chat.py`, `src/api/session.py`, `src/api/health.py`

---

## Phase 2: Test Coverage — Mock LLM & Fix Timeout

### 2.1 LLM Mocking Strategy

**Problem:** `test_agent.py` dan `test_integration.py` panggil real Groq API. Timeout, flaky, non-deterministic.

**Solution:** Create `mock_llm` fixture di `conftest.py`:

```python
@pytest.fixture
def mock_llm():
    """Patch create_llm to return mock LLM with scripted responses."""
    def _make_agent(responses):
        with patch("src.agents.nodes.create_llm") as mock_create:
            mock_instance = MagicMock()
            mock_instance.invoke.side_effect = responses
            mock_create.return_value = mock_instance
            yield create_sales_agent()
    return _make_agent
```

**Files:** `tests/conftest.py`, `tests/test_agent.py`, `tests/test_integration.py`

### 2.2 Agent Test Improvements

**Current:** 3 tests, shallow assertions.

**Add:**
- Test agent calls correct tool for product search
- Test agent returns proper error when tool fails
- Test agent handles multi-turn context
- Assert response content, not just `len > 0`

### 2.3 Integration Test Fix

**Current:** Real API calls → timeout.

**Solution:** Mock entire agent at module level:

```python
@pytest.fixture(autouse=True)
def mock_agent(monkeypatch):
    mock = MagicMock()
    mock.return_value = {"messages": [AIMessage(content="Mocked response")]}
    monkeypatch.setattr("src.api.chat.agent", mock)
```

### 2.4 Missing Unit Tests

Add tests for:
- `trim_messages` logic (message truncation)
- Rate limiting behavior
- `calculate_price` error path (no tier found)
- `create_quote` with dict vs Pydantic input
- `search_products_semantic` with mocked ChromaDB
- `init_langfuse` / `shutdown_langfuse`

---

## Phase 3: Performance P1 — Caching

### 3.1 Static Data Caching

**Problem:** Product, price tier, discount data query berulang tanpa caching.

**Solution:** TTLCache untuk data statis:

```python
from cachetools import TTLCache

_product_cache = TTLCache(maxsize=500, ttl=300)  # 5 min
_price_tier_cache = TTLCache(maxsize=200, ttl=300)
_discount_cache = TTLCache(maxsize=50, ttl=600)  # 10 min

def get_product_by_id(product_id: int) -> dict | None:
    if product_id in _product_cache:
        return _product_cache[product_id]
    # ... existing query ...
    _product_cache[product_id] = result
    return result
```

**Files:** `src/data/database.py` — add caches + cache invalidation
**Dependency:** Tambah `cachetools>=5.3.0` ke `requirements.txt`

### 3.2 LLM Instance Caching

**Problem:** `create_llm()` dipanggil setiap `llm_node` invocation.

**Solution:** Cache LLM instance sebagai module-level singleton:

```python
_llm_instance = None

def get_llm():
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = ChatGroq(
            model=settings.GROQ_MODEL,
            api_key=settings.GROQ_API_KEY,
            temperature=0.3,
        ).bind_tools(tools)
    return _llm_instance
```

**File:** `src/agents/nodes.py`

---

## Phase 4: Code Quality — Security & Correctness

### 4.1 CORS Restriction

**Problem:** `allow_origins=["*"]` + `allow_credentials=True` = invalid config.

**Solution:**
```python
ALLOWED_ORIGINS = settings.ALLOWED_ORIGINS.split(",") if settings.ALLOWED_ORIGINS else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Files:** `src/main.py`, `src/config/settings.py`

### 4.2 Error Detail Leakage

**Problem:** `str(exc)` di global handler leak internal details.

**Solution:**
```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Terjadi kesalahan internal server",
            detail="Silakan coba lagi atau hubungi admin."  # Generic message
        ).model_dump()
    )
```

**File:** `src/main.py`

### 4.3 Rate Limiter Unification

**Problem:** Duplikat `Limiter` di `main.py` dan `chat.py`. Import dari `main.py` ke `chat.py` bisa circular import.

**Solution:** Gunakan `app.state.limiter` yang sudah di-set di `main.py`:

```python
# chat.py
from fastapi import Request

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: Request, req: ChatRequest):
    limiter = request.app.state.limiter
    # ... logic ...
```

Atau: buat `src/config/limiter.py` sebagai single source of truth.

**Files:** `src/api/chat.py`, `src/main.py`, `src/config/limiter.py` (new)

### 4.4 Discount min_qty Validation

**Problem:** `BULK500` (min_qty 500) apply untuk qty 50.

**Solution:**
```python
# calculate_price.py
if discount:
    if discount.get("min_qty") and quantity < discount["min_qty"]:
        discount = None  # Don't apply
        discount_amount = 0
```

**File:** `src/tools/calculate_price.py`

### 4.5 Seed Script Fix

**Problem:** `get_connection()` adalah `@contextmanager`, tapi seed script tidak pakai `with` statement. Connection leak jika error terjadi.

**Solution:**
```python
# seed.py — SEBELUM (bug)
conn = get_connection()  # yields sqlite3.Connection, but context not managed
cursor = conn.cursor()
# ... inserts ...
conn.commit()
conn.close()  # context manager's finally never runs

# seed.py — SESUDAH (benar)
with get_connection() as conn:
    cursor = conn.cursor()
    # ... inserts ...
    # conn.commit() handled by context manager's __exit__
```

**File:** `src/data/seed/seed.py`

---

## Implementation Order

| Phase | Tasks | Estimated Effort |
|-------|-------|-----------------|
| Phase 1: Performance P0 | 3 tasks (indexes, connection, async) | 2-3 hours |
| Phase 2: Test Coverage | 4 tasks (mock LLM, agent tests, integration, missing tests) | 3-4 hours |
| Phase 3: Performance P1 | 2 tasks (static cache, LLM cache) | 1-2 hours |
| Phase 4: Code Quality | 5 tasks (CORS, error, rate limiter, discount, seed) | 1-2 hours |

**Total:** ~14 tasks, 7-11 hours

---

## Success Criteria

- [ ] All 70+ existing tests still pass
- [ ] New tests add 15+ test cases
- [ ] Integration tests run in < 5 seconds (no real API calls)
- [ ] Database queries use indexes (verify with EXPLAIN QUERY PLAN)
- [ ] No sync blocking calls in async handlers
- [ ] Static data cached with TTL
- [ ] CORS restricted to configured origins
- [ ] Error responses don't leak internal details
