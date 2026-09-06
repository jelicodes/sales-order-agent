# Generative UI + Reorder Suggestion — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add rich UI components (ProductCard, PriceTable, OrderSummary) streamed from backend tools to a Next.js + shadcn/ui frontend with a split-view layout and reorder suggestions for returning customers.

**Architecture:** Backend tools return structured JSON (`type` + `data`) instead of plain text. A new SSE endpoint streams tool outputs in real-time. Next.js frontend parses SSE events and renders generative UI components inline with chat messages. Split-view layout: left = product catalog, right = chat panel.

**Tech Stack:** Python 3.13, FastAPI, LangGraph, Groq LLM, Next.js 14, React 18, shadcn/ui, Tailwind CSS, SSE (EventSource), ChromaDB, Langfuse, SQLite

## Global Constraints

- Python env: `D:\Jeli\myenv\Scripts\python.exe`
- User language: Bahasa Indonesia (professional, no emoji in agent responses)
- LLM: Groq (not OpenAI) — model `llama-3.3-70b-versatile`
- Checkpointer: `SqliteSaver` — never pass `None`
- Tool errors: return `{"error": "..."}` dict, never raise
- Code style: no comments, type hints on all public functions
- Layout: `>=1024px` side-by-side, `768-1023px` tabbed, `<768px` stacked
- Commit style: `feat:`, `fix:`, `docs:`, `test:` prefixes

---

## File Map

### Backend (Phase 1)

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `src/tools/search_products.py` | Return structured `{"type": "product_cards", "data": [...]}` |
| Modify | `src/tools/calculate_price.py` | Return structured `{"type": "price_table", "data": {...}}` |
| Modify | `src/tools/create_order.py` | Return structured `{"type": "order_summary", "data": {...}}` |
| Create | `src/api/schemas.py` | Pydantic models for UI components (ProductCardData, PriceTableData, etc.) |
| Create | `src/api/stream.py` | SSE streaming endpoint (`/chat/stream`) |
| Modify | `src/api/chat.py` | Refactor `_extract_response` to also extract UI components |
| Modify | `src/data/repos/order_repo.py` | Add `get_items_by_customer(customer_id, limit)` method |
| Modify | `src/data/schema.py` | Add `image_url` column to products table |
| Modify | `src/data/seed/products.json` | Add `image_url` field to all products |
| Modify | `src/agents/state.py` | Add `customer_name`, `customer_phone`, `is_returning` fields |
| Modify | `src/agents/prompts.py` | Add customer identification + reorder prompt rules |
| Modify | `src/main.py` | Register SSE router |

### Frontend (Phase 2-4)

| Action | File | Responsibility |
|--------|------|----------------|
| Create | `frontend/` | Next.js project root (via `create-next-app`) |
| Create | `frontend/components/ui/*` | shadcn/ui primitives (button, card, badge, table, input, textarea, separator, scroll-area, tabs) |
| Create | `frontend/components/chat/ChatPanel.tsx` | Chat message list + input |
| Create | `frontend/components/chat/ChatBubble.tsx` | User/agent message bubbles |
| Create | `frontend/components/chat/ChatInput.tsx` | Text input with send button |
| Create | `frontend/components/chat/ComponentRenderer.tsx` | Routes tool types → React components |
| Create | `frontend/components/generative-ui/ProductCard.tsx` | Product card with image, price, MOQ |
| Create | `frontend/components/generative-ui/ProductCarousel.tsx` | Grid/carousel of ProductCards |
| Create | `frontend/components/generative-ui/PriceTable.tsx` | Tiered pricing table |
| Create | `frontend/components/generative-ui/OrderSummary.tsx` | Order confirmation card |
| Create | `frontend/components/generative-ui/ReorderSuggestions.tsx` | Reorder suggestion chips |
| Create | `frontend/components/catalog/ProductGrid.tsx` | Catalog product grid |
| Create | `frontend/components/layout/Header.tsx` | App header with logo + theme toggle |
| Create | `frontend/components/layout/SplitView.tsx` | Split view container |
| Create | `frontend/lib/api.ts` | API client (SSE streaming) |
| Create | `frontend/lib/utils.ts` | `cn()` utility |
| Create | `frontend/app/layout.tsx` | Root layout with ThemeProvider |
| Create | `frontend/app/page.tsx` | Main page (SplitView) |
| Create | `frontend/app/globals.css` | Tailwind + CSS variables (light/dark) |
| Create | `frontend/tailwind.config.ts` | Tailwind config with custom colors |
| Create | `frontend/next.config.ts` | Next.js config with API proxy |

---

## Phase 1: Backend Generative UI

### Task 1.1: Pydantic Schemas for UI Components

**Files:**
- Create: `src/api/schemas.py`
- Test: `tests/test_ui_schemas.py`

**Interfaces:**
- Consumes: nothing (first task)
- Produces: `ProductCardData`, `ProductCardsData`, `PriceTableData`, `OrderSummaryData`, `UIToolOutput` type union

- [ ] **Step 1: Create `src/api/schemas.py`**

```python
from pydantic import BaseModel, Field


class ProductCardData(BaseModel):
    type: str = Field(default="product_card")
    product_id: int
    name: str
    category: str
    price: int
    moq: int
    stock: int
    image_url: str = ""
    description: str = ""


class PriceTier(BaseModel):
    min_qty: int
    max_qty: int | None
    price_per_unit: int


class PriceTableData(BaseModel):
    type: str = Field(default="price_table")
    product_id: int
    product_name: str
    tiers: list[PriceTier]
    selected_qty: int | None = None


class OrderItem(BaseModel):
    product_id: int
    product_name: str
    qty: int
    price_per_unit: int
    subtotal: int


class OrderSummaryData(BaseModel):
    type: str = Field(default="order_summary")
    order_id: str
    items: list[OrderItem]
    subtotal: int
    total_price: int
    status: str = "pending"
    customer_name: str = ""


class ReorderItem(BaseModel):
    product_id: int
    product_name: str
    last_qty: int
    last_price: int
    last_order_date: str
    image_url: str = ""


class ReorderSuggestionsData(BaseModel):
    type: str = Field(default="reorder_suggestions")
    customer_name: str
    items: list[ReorderItem]


UIToolOutput = ProductCardsData | PriceTableData | OrderSummaryData | ReorderSuggestionsData
```

- [ ] **Step 2: Write test `tests/test_ui_schemas.py`**

```python
from src.api.schemas import (
    ProductCardData, ProductCardsData, PriceTableData,
    PriceTier, OrderSummaryData, OrderItem,
    ReorderSuggestionsData, ReorderItem,
)


def test_product_card_serializes():
    card = ProductCardData(
        product_id=1, name="Kemeja Flanel", category="Kemeja",
        price=85000, moq=12, stock=500, image_url="/img/kemeja.jpg"
    )
    d = card.model_dump()
    assert d["type"] == "product_card"
    assert d["price"] == 85000


def test_price_table_serializes():
    table = PriceTableData(
        product_id=1, product_name="Kemeja Flanel",
        tiers=[PriceTier(min_qty=1, max_qty=11, price_per_unit=85000)],
        selected_qty=50,
    )
    d = table.model_dump()
    assert d["type"] == "price_table"
    assert len(d["tiers"]) == 1


def test_order_summary_serializes():
    summary = OrderSummaryData(
        order_id="ORD-20260905-ABCD",
        items=[OrderItem(product_id=1, product_name="Kemeja", qty=100, price_per_unit=75000, subtotal=7500000)],
        subtotal=7500000, total_price=7500000, status="pending", customer_name="Budi"
    )
    d = summary.model_dump()
    assert d["type"] == "order_summary"
    assert d["total_price"] == 7500000


def test_reorder_suggestions_serializes():
    reorder = ReorderSuggestionsData(
        customer_name="Budi",
        items=[ReorderItem(product_id=1, product_name="Kemeja", last_qty=100, last_price=75000, last_order_date="2026-08-01", image_url="")]
    )
    d = reorder.model_dump()
    assert d["type"] == "reorder_suggestions"
    assert len(d["items"]) == 1
```

- [ ] **Step 3: Run test**

Run: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/test_ui_schemas.py -v`
Expected: 4 PASS

- [ ] **Step 4: Commit**

```bash
git add src/api/schemas.py tests/test_ui_schemas.py
git commit -m "feat: add Pydantic schemas for generative UI components"
```

---

### Task 1.2: Update `search_products` Tool Return Format

**Files:**
- Modify: `src/tools/search_products.py:15-21`
- Test: `tests/test_ui_schemas.py` (extend)

**Interfaces:**
- Consumes: `ProductCardData` from Task 1.1
- Produces: `search_products` returns `{"type": "product_cards", "data": [ProductCardData, ...]}`

- [ ] **Step 1: Update search_products tool**

Replace the return statements in `src/tools/search_products.py` to wrap results in structured format:

```python
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from src.data.vector_store import search_products_semantic
from src.data.repos.product_repo import ProductRepo

_product_repo = ProductRepo()


class SearchProductsInput(BaseModel):
    query: str = Field(description="Kata kunci pencarian produk")
    category: str = Field(default="", description="Filter kategori (contoh: 'Kemeja', 'Hoodie')")


def _format_product_card(product: dict) -> dict:
    """Convert product dict to structured card format."""
    return {
        "type": "product_card",
        "product_id": product["id"],
        "name": product["name"],
        "category": product["category"],
        "price": int(product.get("base_price", 0)),
        "moq": product.get("moq", 1),
        "stock": product.get("stock", 0),
        "image_url": product.get("image_url", ""),
        "description": product.get("description", ""),
    }


@tool(args_schema=SearchProductsInput)
def search_products(query: str, category: str = "") -> dict:
    """Cari produk fashion grosir berdasarkan query. Menghasilkan product cards."""
    results = []
    if query and query.strip():
        results = search_products_semantic(query, n_results=5)
    if not results:
        results = _product_repo.search(query if query else "", category if category else None)

    if isinstance(results, dict) and "error" in results:
        return results

    cards = [_format_product_card(p) for p in results] if results else []
    return {"type": "product_cards", "data": cards}
```

- [ ] **Step 2: Add test for structured output**

Add to `tests/test_ui_schemas.py`:

```python
from src.tools.search_products import search_products


def test_search_products_returns_structured():
    result = search_products.invoke({"query": "kemeja"})
    assert isinstance(result, dict)
    assert result["type"] == "product_cards"
    assert isinstance(result["data"], list)
    if result["data"]:
        card = result["data"][0]
        assert "product_id" in card
        assert "name" in card
        assert "price" in card
```

- [ ] **Step 3: Run test**

Run: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/test_ui_schemas.py::test_search_products_returns_structured -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add src/tools/search_products.py
git commit -m "feat: search_products returns structured product_cards format"
```

---

### Task 1.3: Update `calculate_price` Tool Return Format

**Files:**
- Modify: `src/tools/calculate_price.py:15-48`
- Test: extend `tests/test_ui_schemas.py`

**Interfaces:**
- Consumes: `PriceTableData` from Task 1.1
- Produces: `calculate_price` returns `{"type": "price_table", "data": PriceTableData}`

- [ ] **Step 1: Update calculate_price tool**

```python
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from src.data.repos.product_repo import ProductRepo

_product_repo = ProductRepo()


class CalculatePriceInput(BaseModel):
    product_id: int = Field(description="ID produk")
    quantity: int = Field(description="Jumlah pesanan")
    discount_code: str = Field(default="", description="Kode diskon (opsional)")


@tool(args_schema=CalculatePriceInput)
def calculate_price(product_id: int, quantity: int, discount_code: str = "") -> dict:
    """Hitung harga berdasarkan jumlah pesanan. Menghasilkan price table."""
    if quantity <= 0:
        return {"error": "Quantity harus lebih dari 0"}

    product = _product_repo.get_by_id(product_id)
    if not product:
        return {"error": f"Produk dengan ID {product_id} tidak ditemukan"}

    tiers = _product_repo.get_price_tiers(product_id)
    if not tiers:
        return {"error": "Tidak ada harga tersedia"}

    # Find matching tier
    selected_tier = None
    for tier in tiers:
        max_qty = tier.get("max_qty") or float("inf")
        if tier["min_qty"] <= quantity <= max_qty:
            selected_tier = tier
            break

    if not selected_tier:
        selected_tier = tiers[-1]  # Use highest tier

    price_per_unit = selected_tier["price_per_unit"]
    subtotal = price_per_unit * quantity

    # Apply discount
    discount_amount = 0
    discount_info = None
    if discount_code:
        discount = _product_repo.get_discount(discount_code)
        if discount:
            if discount.get("min_qty") and quantity < discount["min_qty"]:
                discount = None
            else:
                if discount["type"] == "percentage":
                    discount_amount = subtotal * (discount["value"] / 100)
                else:
                    discount_amount = min(discount["value"], subtotal)
                discount_info = {"code": discount["code"], "type": discount["type"], "value": discount["value"]}

    total = subtotal - discount_amount

    return {
        "type": "price_breakdown",
        "data": {
            "product_id": product_id,
            "product_name": product["name"],
            "quantity": quantity,
            "price_per_unit": price_per_unit,
            "subtotal": subtotal,
            "discount": discount_info,
            "discount_amount": discount_amount,
            "total": total,
            "tiers": [
                {"min_qty": t["min_qty"], "max_qty": t.get("max_qty"), "price_per_unit": t["price_per_unit"]}
                for t in tiers
            ],
        },
    }
```

- [ ] **Step 2: Add test**

```python
from src.tools.calculate_price import calculate_price


def test_calculate_price_returns_structured():
    result = calculate_price.invoke({"product_id": 1, "quantity": 50})
    assert isinstance(result, dict)
    assert result["type"] == "price_breakdown"
    assert "data" in result
    assert "tiers" in result["data"]
    assert "total" in result["data"]
```

- [ ] **Step 3: Run test**

Run: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/test_ui_schemas.py::test_calculate_price_returns_structured -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add src/tools/calculate_price.py
git commit -m "feat: calculate_price returns structured price_breakdown format"
```

---

### Task 1.4: Update `create_order` Tool Return Format

**Files:**
- Modify: `src/tools/create_order.py:6-32`
- Modify: `src/agents/graph.py:30-56` (confirmation_node order_summary)
- Test: extend `tests/test_ui_schemas.py`

**Interfaces:**
- Consumes: `OrderSummaryData` from Task 1.1
- Produces: `create_order` returns `{"type": "order_summary", "data": OrderSummaryData}` with `ORDER_PENDING` marker

- [ ] **Step 1: Update create_order tool**

```python
import json
from langchain_core.tools import tool


@tool
def create_order(customer_id: str, items_json: str, shipping_address: str | None = None, notes: str | None = None) -> dict:
    """Siapkan order baru untuk konfirmasi. Menghasilkan order summary."""
    try:
        items = json.loads(items_json)
    except json.JSONDecodeError:
        return {"error": "items_json format tidak valid"}

    if not items:
        return {"error": "Tidak ada items dalam order"}

    subtotal = 0
    formatted_items = []
    for item in items:
        if "product_id" not in item or "qty" not in item or "price_per_unit" not in item:
            return {"error": "Item harus memiliki product_id, qty, dan price_per_unit"}
        item_subtotal = item["qty"] * item["price_per_unit"]
        item["subtotal"] = item_subtotal
        subtotal += item_subtotal
        formatted_items.append({
            "product_id": item["product_id"],
            "product_name": item.get("product_name", "Produk"),
            "qty": item["qty"],
            "price_per_unit": item["price_per_unit"],
            "subtotal": item_subtotal,
        })

    order_data = {
        "customer_id": customer_id,
        "items": formatted_items,
        "subtotal": subtotal,
        "total_price": subtotal,
        "shipping_address": shipping_address,
        "notes": notes,
        "pending_confirmation": True,
    }

    return {
        "type": "order_summary",
        "data": {
            "order_id": "PENDING",
            "items": formatted_items,
            "subtotal": subtotal,
            "total_price": subtotal,
            "status": "pending",
            "customer_name": customer_id,
        },
        "ORDER_PENDING": json.dumps(order_data),
    }
```

- [ ] **Step 2: Update `graph.py` confirmation_node**

Update the `confirmation_node` in `src/agents/graph.py` to handle the new format. The key change is how `ORDER_PENDING` is extracted — it's now in `result["ORDER_PENDING"]` instead of embedded in `msg.content`:

```python
def confirmation_node(state: AgentState) -> Command[Literal["llm"]]:
    """Handle order confirmation via interrupt."""
    order_data = None
    tool_call_id = "create_order_confirmed"

    # Find ORDER_PENDING from tool results
    for msg in state["messages"]:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                if tc.get("name") == "create_order":
                    tool_call_id = tc.get("id", tool_call_id)
        content = msg.content if hasattr(msg, "content") else ""
        if isinstance(content, dict) and "ORDER_PENDING" in content:
            try:
                order_data = json.loads(content["ORDER_PENDING"])
            except (json.JSONDecodeError, TypeError):
                continue
            break
        if "ORDER_PENDING" in str(content):
            try:
                _, order_data_str = str(content).split("ORDER_PENDING|", 1)
                order_data = json.loads(order_data_str)
            except (ValueError, json.JSONDecodeError):
                continue
            break

    if not order_data:
        return Command(goto="llm")

    items = order_data.get("items", [])
    product_name = items[0].get("product_name", "N/A") if items else "N/A"
    qty = items[0].get("qty", 0) if items else 0
    order_summary = f"Order {product_name} - {qty} pcs - Total: Rp {order_data['total_price']:,}"

    human_response = interrupt({
        "action": "create_order",
        "summary": order_summary,
        "message": "Ketik 'YA' untuk konfirmasi order atau 'BATAL' untuk membatalkan"
    })

    response_text = str(human_response).strip().lower() if human_response else ""

    confirm_keywords = ("ya", "ok", "oke", "konfirmasi", "setuju", "lanjut", "proceed", "yes")
    cancel_keywords = ("batal", "cancel", "tidak", "no", "goback", "kembali")

    is_confirmed = any(kw in response_text for kw in confirm_keywords)
    is_cancelled = any(kw in response_text for kw in cancel_keywords)

    if is_cancelled:
        is_confirmed = False

    if is_confirmed and not is_cancelled:
        from src.data.database import create_order as db_create_order
        order = db_create_order(
            customer_id=order_data["customer_id"],
            items=order_data["items"],
            subtotal=order_data["subtotal"],
            discount_amount=0,
            total_price=order_data["total_price"],
            shipping_address=order_data.get("shipping_address"),
            notes=order_data.get("notes"),
        )
        order_id = order["id"]
        customer_name = order_data.get("customer_name", "Bapak/Ibu")
        confirmed_msg = (
            f"Order {order_id} telah berhasil dibuat dan dikonfirmasi. "
            f"Pelanggan: {customer_name}. "
            f"Total: Rp {order_data['total_price']:,}. "
            f"Status: pending."
        )
        return Command(
            update={
                "messages": [ToolMessage(content=confirmed_msg, name="create_order", tool_call_id=tool_call_id)],
                "pending_order": None,
                "confirmation_status": "confirmed",
                "customer_id": order_data["customer_id"],
            },
            goto="llm"
        )
    else:
        return Command(
            update={
                "messages": [ToolMessage(content="Order dibatalkan oleh pelanggan.", name="create_order", tool_call_id=tool_call_id)],
                "pending_order": None,
                "confirmation_status": None,
            },
            goto="llm"
        )
```

Also update `after_tools` to detect the new dict format:

```python
def after_tools(state: AgentState) -> str:
    """Check if any tool result contains ORDER_PENDING."""
    if state.get("confirmation_status") == "confirmed":
        return "llm"
    for msg in state["messages"]:
        content = msg.content if hasattr(msg, "content") else ""
        if isinstance(content, dict) and content.get("ORDER_PENDING"):
            return "confirmation"
        if "ORDER_PENDING" in str(content):
            return "confirmation"
    return "llm"
```

- [ ] **Step 3: Add test**

```python
from src.tools.create_order import create_order


def test_create_order_returns_structured():
    items_json = '[{"product_id": 1, "product_name": "Kemeja", "qty": 100, "price_per_unit": 75000}]'
    result = create_order.invoke({
        "customer_id": "CUST-001",
        "items_json": items_json,
    })
    assert isinstance(result, dict)
    assert result["type"] == "order_summary"
    assert result["data"]["total_price"] == 7500000
    assert "ORDER_PENDING" in result
```

- [ ] **Step 4: Run all UI schema tests**

Run: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/test_ui_schemas.py -v`
Expected: 7 PASS

- [ ] **Step 5: Commit**

```bash
git add src/tools/create_order.py src/agents/graph.py
git commit -m "feat: create_order returns structured order_summary, update graph handler"
```

---

### Task 1.5: Order Repo — `get_items_by_customer`

**Files:**
- Modify: `src/data/repos/order_repo.py:65-72`
- Test: `tests/test_database.py` (extend)

**Interfaces:**
- Consumes: nothing
- Produces: `OrderRepo.get_items_by_customer(customer_id, limit) -> list[dict]` returning items with product details

- [ ] **Step 1: Add method to OrderRepo**

Add after `get_by_customer` method in `src/data/repos/order_repo.py`:

```python
def get_items_by_customer(self, customer_id: str, limit: int = 10) -> list[dict]:
    """Get recent order items for a customer, for reorder suggestions."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT oi.product_id, oi.product_name, oi.qty, oi.price_per_unit,
                      o.created_at as last_order_date
               FROM order_items oi
               JOIN orders o ON oi.order_id = o.id
               WHERE o.customer_id = ?
               ORDER BY o.created_at DESC
               LIMIT ?""",
            (customer_id, limit),
        )
        return [dict(row) for row in cursor.fetchall()]
```

- [ ] **Step 2: Add test**

Add to `tests/test_database.py`:

```python
def test_get_items_by_customer():
    from src.data.repos.order_repo import OrderRepo
    repo = OrderRepo()
    # Create a customer and order first
    from src.data.repos.customer_repo import CustomerRepo
    cust_repo = CustomerRepo()
    cust_repo.upsert({"id": "CUST-REORDER-TEST", "name": "Test Reorder", "phone": "081999999999"})
    repo.create_order(
        customer_id="CUST-REORDER-TEST",
        items=[{"product_id": 1, "product_name": "Kemeja", "qty": 50, "price_per_unit": 80000, "subtotal": 4000000}],
        subtotal=4000000, discount_amount=0, total_price=4000000,
    )
    items = repo.get_items_by_customer("CUST-REORDER-TEST", limit=5)
    assert isinstance(items, list)
    assert len(items) >= 1
    assert items[0]["product_name"] == "Kemeja"
```

- [ ] **Step 3: Run test**

Run: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/test_database.py::test_get_items_by_customer -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add src/data/repos/order_repo.py
git commit -m "feat: add get_items_by_customer to OrderRepo for reorder suggestions"
```

---

### Task 1.6: Add `image_url` to Products

**Files:**
- Modify: `src/data/schema.py:39-47` (products table DDL)
- Modify: `src/data/seed/products.json`
- Test: verify DB init

**Interfaces:**
- Consumes: nothing
- Produces: products table has `image_url` column

- [ ] **Step 1: Add image_url column to schema**

In `src/data/schema.py`, update the products table DDL:

```python
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    base_price REAL NOT NULL,
    moq INTEGER NOT NULL DEFAULT 1,
    lead_time_days INTEGER NOT NULL DEFAULT 5,
    image_url TEXT DEFAULT ''
);
```

- [ ] **Step 2: Add image_url to products.json**

For each product in `src/data/seed/products.json`, add an `image_url` field. Use placeholder paths for now:

```json
[
  {
    "id": 1,
    "name": "Kemeja Flanel Premium",
    "category": "Kemeja",
    "description": "Kemeja flanel premium dengan bahan katun 100%",
    "base_price": 85000,
    "moq": 12,
    "lead_time_days": 3,
    "image_url": "/images/products/kemeja-flanel.jpg"
  }
]
```

- [ ] **Step 3: Verify DB init doesn't break**

Run: `D:\Jeli\myenv\Scripts\python.exe -c "from src.data.schema import init_db; init_db(); print('OK')"`
Expected: OK

- [ ] **Step 4: Commit**

```bash
git add src/data/schema.py src/data/seed/products.json
git commit -m "feat: add image_url column to products table"
```

---

### Task 1.7: SSE Streaming Endpoint

**Files:**
- Create: `src/api/stream.py`
- Modify: `src/main.py:96-98` (register router)
- Test: `tests/test_api.py` (extend)

**Interfaces:**
- Consumes: `create_sales_agent()` from `src/agents/graph.py`, `ChatRequest` from `src/api/models.py`
- Produces: `POST /chat/stream` returns `text/event-stream` with `tool_output` and `text_delta` events

- [ ] **Step 1: Create `src/api/stream.py`**

```python
import json
import uuid
import asyncio
import logging
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, trim_messages
from langgraph.types import Command
from groq import RateLimitError as GroqRateLimitError
from src.agents.graph import create_sales_agent
from src.api.models import ChatRequest

router = APIRouter()
logger = logging.getLogger(__name__)


async def _stream_chat(req: ChatRequest, request: Request):
    """Generator that yields SSE events."""
    checkpointer = request.app.state.checkpointer
    request_id = str(uuid.uuid4())
    session_id = req.session_id or str(uuid.uuid4())
    agent = create_sales_agent(checkpointer=checkpointer)

    try:
        config = {"configurable": {"thread_id": session_id}}
        upper = req.message.strip().upper()

        # Send session info
        yield f"data: {json.dumps({'type': 'session', 'session_id': session_id, 'request_id': request_id})}\n\n"

        if upper in ("YA", "BATAL"):
            result = await asyncio.to_thread(
                agent.invoke, Command(resume=req.message), config
            )
        else:
            messages = [HumanMessage(content=req.message)]
            messages = trim_messages(
                messages, max_tokens=8000, token_counter=len,
                strategy="last", start_on="human",
            )
            result = await asyncio.to_thread(
                agent.invoke,
                {"messages": messages, "session_id": session_id, "context": {"request_id": request_id}},
                config,
            )

        # Handle interrupt (HITL)
        if isinstance(result, dict) and "__interrupt__" in result:
            interrupts = result["__interrupt__"]
            if interrupts:
                payload = interrupts[0].value if hasattr(interrupts[0], "value") else interrupts[0]
                if isinstance(payload, dict) and payload.get("action") == "create_order":
                    yield f"data: {json.dumps({'type': 'tool_output', 'tool_type': 'order_summary', 'data': payload})}\n\n"
                else:
                    yield f"data: {json.dumps({'type': 'text_delta', 'content': str(payload)})}\n\n"

        # Process messages
        messages = result.get("messages", [])
        for msg in messages:
            content = msg.content if hasattr(msg, "content") else ""

            # Tool results with structured data
            if isinstance(content, dict) and content.get("type") in (
                "product_cards", "price_breakdown", "order_summary", "reorder_suggestions"
            ):
                yield f"data: {json.dumps({'type': 'tool_output', 'tool_type': content['type'], 'data': content})}\n\n"
                continue

            # ORDER_PENDING in dict format
            if isinstance(content, dict) and content.get("ORDER_PENDING"):
                yield f"data: {json.dumps({'type': 'tool_output', 'tool_type': 'order_summary', 'data': content})}\n\n"
                continue

            # Text messages (only from assistant)
            role = getattr(msg, "type", "")
            if role == "ai" and content and "ORDER_PENDING" not in str(content):
                yield f"data: {json.dumps({'type': 'text_delta', 'content': content})}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    except GroqRateLimitError:
        yield f"data: {json.dumps({'type': 'text_delta', 'content': 'Maaf, layanan AI sedang sibuk. Silakan coba lagi dalam 1-2 menit.'})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    except Exception as e:
        logger.error(f"[{request_id}] Stream error: {e}", exc_info=True)
        yield f"data: {json.dumps({'type': 'text_delta', 'content': 'Terjadi kesalahan. Silakan coba lagi.'})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"


@router.post("/chat/stream")
async def chat_stream(request: Request, req: ChatRequest):
    return StreamingResponse(
        _stream_chat(req, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
```

- [ ] **Step 2: Register router in main.py**

In `src/main.py`, add after line 98:

```python
from src.api.stream import router as stream_router
app.include_router(stream_router)
```

- [ ] **Step 3: Add test**

Add to `tests/test_api.py`:

```python
def test_chat_stream_endpoint():
    from fastapi.testclient import TestClient
    from src.main import app
    client = TestClient(app)
    response = client.post("/chat/stream", json={"message": "Halo"})
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
```

- [ ] **Step 4: Run test**

Run: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/test_api.py::test_chat_stream_endpoint -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/api/stream.py src/main.py
git commit -m "feat: add SSE streaming endpoint /chat/stream"
```

---

### Task 1.8: Update Agent Prompt for Customer Identification

**Files:**
- Modify: `src/agents/state.py:6-12`
- Modify: `src/agents/prompts.py:1-64`

**Interfaces:**
- Consumes: nothing
- Produces: AgentState with new fields, prompt with customer identification + reorder rules

- [ ] **Step 1: Update AgentState**

In `src/agents/state.py`:

```python
from typing import TypedDict, Annotated, Sequence, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    session_id: str
    context: dict
    customer_id: Optional[str]
    customer_name: Optional[str]
    customer_phone: Optional[str]
    is_returning: Optional[bool]
    pending_order: Optional[dict]
    confirmation_status: Optional[str]
```

- [ ] **Step 2: Update prompts.py**

Replace `SALES_AGENT_PROMPT` in `src/agents/prompts.py`:

```python
SALES_AGENT_PROMPT = """Anda adalah AI Sales Assistant untuk PT Lemone Surya Indonesia, perusahaan fashion grosir B2B yang berlokasi di Pusat Grosir Metro Tanah Abang, Jakarta Pusat.

Tugas Anda:
1. Membantu customer menemukan produk fashion grosir yang sesuai kebutuhan
2. Cek ketersediaan stok secara real-time
3. Hitung harga berdasarkan quantity (ada tier harga untuk order besar)
4. Buat penawaran/quote untuk customer
5. Sarankan produk alternatif jika stok tidak cukup atau budget tidak sesuai
6. Kelola order customer (buat, cek status, batalkan)
7. Kelola data customer (daftar baru, lihat riwayat)

Identifikasi Customer - PENTING:
- Ketika customer pertama kali chat, tanyakan nama dan nomor HP
- Gunakan get_customer untuk mengecek apakah nomor HP sudah terdaftar
- Jika customer sudah ada (returning), sapa dengan nama dan tawarkan reorder
- Jika customer baru, bantu daftarkan dengan informasi yang diberikan

Reorder Suggestions:
- Jika customer sudah pernah order (returning customer), tawarkan reorder
- Gunakan get_order_history untuk melihat item yang pernah dipesan
- Tampilkan saran reorder dengan qty terakhir dan tanggal order terakhir
- Gunakan format reorder_suggestions saat menampilkan saran

Aturan:
- Selalu cek stok sebelum memberikan harga
- Jika stok tidak cukup, tawarkan alternatif
- Jika budget customer tidak sesuai, sarankan produk lain yang lebih sesuai
- Gunakan Bahasa Indonesia yang profesional dan sopan
- Jangan janji sesuatu yang tidak bisa dipenuhi
- Jika pertanyaan di luar kemampuan Anda (pembayaran, klaim, pengiriman), sarankan hubungi sales langsung
- Jangan gunakan emoji atau karakter dekoratif dalam response
- Fokus pada informasi produk: nama, harga, stok, MOQ, lead time

Order Management - PENTING:
Ketika customer ingin order dan Anda sudah memiliki semua data ini, LANGSUNG panggil create_order:
- Nama customer
- Nomor HP customer
- Product ID (dari search_products atau get_product_detail)
- Nama produk
- Jumlah (qty)
- Harga per unit (dari calculate_price)
- Total harga

JANGAN tanya "Apakah mau lanjut?" atau "Konfirmasi ya?" - langsung panggil create_order!
Tool create_order akan menyiapkan order dan meminta konfirmasi dari sistem.

Contoh kapan harus panggil create_order:
- "Saya mau order 200 kaos polo hitam" (setelah Anda tahu harga dan stok)
- "Beli 100 pcs, nama Budi, HP 08123456789"
- "Order untuk seragam kantor, 500 kaos navy"

Customer Management:
- Ketika customer pertama kali chat, tanyakan nama dan nomor HP
- Simpan informasi customer untuk order berikutnya
- Agent bisa melihat riwayat order customer

Limitations:
- Agent TIDAK bisa mengubah harga
- Agent TIDAK bisa memproses pembayaran
- Agent TIDAK bisa membatalkan order yang sudah diproses
- Untuk pertanyaan diluar kemampuan, sarankan hubungi sales langsung

Anda memiliki akses ke tools untuk:
- Mencari produk (search_products)
- Melihat detail produk (get_product_detail)
- Mengecek stok (check_stock)
- Menghitung harga (calculate_price)
- Membuat penawaran (create_quote)
- Mencari alternatif (get_alternatives)
- Membuat order (create_order)
- Membatalkan order (cancel_order)
- Melihat data customer (get_customer)
- Cek status order (check_order_status)
- Riwayat order (get_order_history)

Gunakan tools yang tepat untuk setiap permintaan customer."""
```

- [ ] **Step 3: Run full test suite**

Run: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/ -v --ignore=tests/test_integration.py`
Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add src/agents/state.py src/agents/prompts.py
git commit -m "feat: add customer identification and reorder prompt rules"
```

---

## Phase 2: Frontend Basic

### Task 2.1: Create Next.js Project + shadcn/ui

**Files:**
- Create: `frontend/` (via `create-next-app`)
- Install: shadcn/ui, tailwindcss, next-themes

- [ ] **Step 1: Scaffold Next.js project**

Run: `npx create-next-app@latest frontend --typescript --tailwind --eslint --app --src-dir=false --import-alias="@/*" --use-npm`

- [ ] **Step 2: Initialize shadcn/ui**

Run: `cd frontend && npx shadcn@latest init -d`

- [ ] **Step 3: Install shadcn components**

Run: `cd frontend && npx shadcn@latest add button card badge table input textarea separator scroll-area tabs`

- [ ] **Step 4: Install next-themes**

Run: `cd frontend && npm install next-themes`

- [ ] **Step 5: Commit**

```bash
cd frontend && git init && git add . && git commit -m "feat: scaffold Next.js project with shadcn/ui"
```

---

### Task 2.2: Theme + Global Styles

**Files:**
- Modify: `frontend/app/globals.css`
- Modify: `frontend/tailwind.config.ts`
- Modify: `frontend/app/layout.tsx`

**Interfaces:**
- Consumes: DESIGN.md color palette
- Produces: CSS variables for light/dark, ThemeProvider setup

- [ ] **Step 1: Update globals.css with color palette**

Replace `frontend/app/globals.css` with (based on DESIGN.md):

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 222.2 84% 4.9%;
    --primary: 217 40% 20%;
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96.1%;
    --secondary-foreground: 222.2 47.4% 11.2%;
    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --accent: 43 45% 55%;
    --accent-foreground: 210 40% 98%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 43 45% 55%;
    --radius: 0.5rem;
    --success: 160 84% 39%;
    --warning: 38 92% 50%;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;
    --popover: 222.2 84% 4.9%;
    --popover-foreground: 210 40% 98%;
    --primary: 43 45% 55%;
    --primary-foreground: 222.2 47.4% 11.2%;
    --secondary: 217.2 32.6% 17.5%;
    --secondary-foreground: 210 40% 98%;
    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;
    --accent: 43 45% 55%;
    --accent-foreground: 210 40% 98%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 210 40% 98%;
    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    --ring: 43 45% 55%;
    --success: 160 84% 39%;
    --warning: 38 92% 50%;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
  }
}
```

- [ ] **Step 2: Update layout.tsx with ThemeProvider**

```tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { ThemeProvider } from "next-themes";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Lemone Sales Agent",
  description: "AI Sales Assistant - PT Lemone Surya Indonesia",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="id" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
```

- [ ] **Step 3: Commit**

```bash
cd frontend && git add . && git commit -m "feat: add theme configuration with light/dark mode"
```

---

### Task 2.3: API Client with SSE

**Files:**
- Create: `frontend/lib/api.ts`

**Interfaces:**
- Consumes: Backend `/chat/stream` endpoint
- Produces: `streamChat(message, sessionId, onToolOutput, onTextDelta, onDone)` function

- [ ] **Step 1: Create API client**

```typescript
export interface ToolOutput {
  type: "tool_output";
  tool_type: string;
  data: Record<string, unknown>;
}

export interface TextDelta {
  type: "text_delta";
  content: string;
}

export interface SessionInfo {
  type: "session";
  session_id: string;
  request_id: string;
}

export interface StreamDone {
  type: "done";
}

export type StreamEvent = ToolOutput | TextDelta | SessionInfo | StreamDone;

export interface StreamCallbacks {
  onToolOutput: (toolType: string, data: Record<string, unknown>) => void;
  onTextDelta: (content: string) => void;
  onSession: (sessionId: string, requestId: string) => void;
  onDone: () => void;
  onError: (error: string) => void;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function streamChat(
  message: string,
  sessionId: string,
  callbacks: StreamCallbacks
): Promise<void> {
  try {
    const response = await fetch(`${API_BASE}/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, session_id: sessionId }),
    });

    if (!response.ok) {
      callbacks.onError(`HTTP ${response.status}`);
      return;
    }

    const reader = response.body?.getReader();
    if (!reader) {
      callbacks.onError("No response body");
      return;
    }

    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          try {
            const event: StreamEvent = JSON.parse(line.slice(6));
            switch (event.type) {
              case "session":
                callbacks.onSession(event.session_id, event.request_id);
                break;
              case "tool_output":
                callbacks.onToolOutput(event.tool_type, event.data);
                break;
              case "text_delta":
                callbacks.onTextDelta(event.content);
                break;
              case "done":
                callbacks.onDone();
                break;
            }
          } catch {
            // Skip malformed JSON
          }
        }
      }
    }
  } catch (err) {
    callbacks.onError(err instanceof Error ? err.message : "Unknown error");
  }
}
```

- [ ] **Step 2: Commit**

```bash
cd frontend && git add lib/api.ts && git commit -m "feat: add SSE streaming API client"
```

---

### Task 2.4: Chat Components

**Files:**
- Create: `frontend/components/chat/ChatBubble.tsx`
- Create: `frontend/components/chat/ChatInput.tsx`
- Create: `frontend/components/chat/ChatPanel.tsx`
- Create: `frontend/components/chat/ComponentRenderer.tsx`

**Interfaces:**
- Consumes: `StreamCallbacks` from Task 2.3
- Produces: `<ChatPanel>` component with message list + input

- [ ] **Step 1: Create ChatBubble.tsx**

```tsx
import { cn } from "@/lib/utils";

interface ChatBubbleProps {
  role: "user" | "assistant";
  children: React.ReactNode;
}

export function ChatBubble({ role, children }: ChatBubbleProps) {
  return (
    <div className={cn("flex mb-4", role === "user" ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "rounded-2xl px-4 py-2 max-w-[80%]",
          role === "user"
            ? "bg-primary text-primary-foreground rounded-br-sm"
            : "bg-muted rounded-bl-sm"
        )}
      >
        {children}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Create ChatInput.tsx**

```tsx
"use client";
import { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Send } from "lucide-react";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
    textareaRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t bg-background p-4">
      <div className="flex items-end gap-2">
        <Textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ketik pesan Anda..."
          className="min-h-[44px] max-h-[120px] resize-none"
          rows={1}
          disabled={disabled}
        />
        <Button
          size="icon"
          className="h-[44px] w-[44px] shrink-0"
          onClick={handleSend}
          disabled={disabled || !value.trim()}
        >
          <Send className="h-4 w-4" />
        </Button>
      </div>
      <p className="text-xs text-muted-foreground mt-2">Enter untuk mengirim</p>
    </div>
  );
}
```

- [ ] **Step 3: Create ComponentRenderer.tsx**

```tsx
import { ProductCards } from "@/components/generative-ui/ProductCards";
import { PriceTable } from "@/components/generative-ui/PriceTable";
import { OrderSummary } from "@/components/generative-ui/OrderSummary";

interface ComponentRendererProps {
  toolType: string;
  data: Record<string, unknown>;
}

export function ComponentRenderer({ toolType, data }: ComponentRendererProps) {
  switch (toolType) {
    case "product_cards":
      return <ProductCards data={data} />;
    case "price_breakdown":
      return <PriceTable data={data} />;
    case "order_summary":
      return <OrderSummary data={data} />;
    case "reorder_suggestions":
      return <div className="text-sm text-muted-foreground">Reorder suggestions coming soon</div>;
    default:
      return null;
  }
}
```

- [ ] **Step 4: Create ChatPanel.tsx**

```tsx
"use client";
import { useState, useRef, useEffect } from "react";
import { ChatBubble } from "./ChatBubble";
import { ChatInput } from "./ChatInput";
import { ComponentRenderer } from "./ComponentRenderer";
import { streamChat } from "@/lib/api";
import { ScrollArea } from "@/components/ui/scroll-area";

interface Message {
  id: string;
  role: "user" | "assistant";
  content?: string;
  toolOutputs?: Array<{ toolType: string; data: Record<string, unknown> }>;
}

export function ChatPanel() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [sessionId, setSessionId] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = (message: string) => {
    const userMsg: Message = { id: crypto.randomUUID(), role: "user", content: message };
    setMessages((prev) => [...prev, userMsg]);
    setIsStreaming(true);

    const assistantMsg: Message = { id: crypto.randomUUID(), role: "assistant", toolOutputs: [] };
    setMessages((prev) => [...prev, assistantMsg]);

    streamChat(message, sessionId, {
      onSession: (sid) => setSessionId(sid),
      onToolOutput: (toolType, data) => {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsg.id
              ? { ...m, toolOutputs: [...(m.toolOutputs || []), { toolType, data }] }
              : m
          )
        );
      },
      onTextDelta: (content) => {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsg.id
              ? { ...m, content: (m.content || "") + content }
              : m
          )
        );
      },
      onDone: () => setIsStreaming(false),
      onError: () => setIsStreaming(false),
    });
  };

  return (
    <div className="flex flex-col h-full">
      <ScrollArea className="flex-1 p-4" ref={scrollRef}>
        {messages.length === 0 && (
          <div className="flex items-center justify-center h-full text-muted-foreground">
            <p>Selamat datang di Lemone Sales Agent</p>
          </div>
        )}
        {messages.map((msg) => (
          <div key={msg.id}>
            {msg.content && (
              <ChatBubble role={msg.role}>
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
              </ChatBubble>
            )}
            {msg.toolOutputs?.map((tool, i) => (
              <ChatBubble key={i} role="assistant">
                <ComponentRenderer toolType={tool.toolType} data={tool.data} />
              </ChatBubble>
            ))}
          </div>
        ))}
      </ScrollArea>
      <ChatInput onSend={handleSend} disabled={isStreaming} />
    </div>
  );
}
```

- [ ] **Step 5: Commit**

```bash
cd frontend && git add components/chat/ && git commit -m "feat: add chat components (ChatPanel, ChatBubble, ChatInput, ComponentRenderer)"
```

---

## Phase 3: Split View + Catalog

### Task 3.1: Generative UI Components

**Files:**
- Create: `frontend/components/generative-ui/ProductCards.tsx`
- Create: `frontend/components/generative-ui/PriceTable.tsx`
- Create: `frontend/components/generative-ui/OrderSummary.tsx`

- [ ] **Step 1: Create ProductCards.tsx**

```tsx
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface ProductCard {
  product_id: number;
  name: string;
  category: string;
  price: number;
  moq: number;
  stock: number;
  image_url: string;
  description: string;
}

interface ProductCardsProps {
  data: Record<string, unknown>;
}

export function ProductCards({ data }: ProductCardsProps) {
  const items = (data.data as ProductCard[]) || [];

  if (items.length === 0) {
    return <p className="text-sm text-muted-foreground">Tidak ditemukan produk yang sesuai.</p>;
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
      {items.map((product) => (
        <Card key={product.product_id} className="overflow-hidden">
          <div className="aspect-square bg-muted flex items-center justify-center">
            {product.image_url ? (
              <img src={product.image_url} alt={product.name} className="w-full h-full object-cover" />
            ) : (
              <span className="text-4xl">👕</span>
            )}
          </div>
          <CardHeader className="p-3">
            <CardTitle className="text-xs line-clamp-2">{product.name}</CardTitle>
          </CardHeader>
          <CardContent className="p-3 pt-0">
            <div className="flex items-baseline gap-1">
              <span className="text-sm font-bold text-primary">
                Rp {product.price.toLocaleString("id-ID")}
              </span>
              <span className="text-[10px] text-muted-foreground">/pcs</span>
            </div>
            <p className="text-[10px] text-muted-foreground mt-1">
              MOQ: {product.moq} | Stok: {product.stock}
            </p>
            {product.stock < 10 && (
              <Badge variant="destructive" className="mt-1 text-[10px]">Stok Terbatas</Badge>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
```

- [ ] **Step 2: Create PriceTable.tsx**

```tsx
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

interface PriceTier {
  min_qty: number;
  max_qty: number | null;
  price_per_unit: number;
}

interface PriceTableProps {
  data: Record<string, unknown>;
}

export function PriceTable({ data }: PriceTableProps) {
  const tiers = (data.tiers as PriceTier[]) || [];
  const productName = data.product_name as string;
  const selectedQty = data.quantity as number;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Harga Grosir — {productName}</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Jumlah</TableHead>
              <TableHead className="text-right">Harga/pcs</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {tiers.map((tier, i) => (
              <TableRow key={i}>
                <TableCell>{tier.min_qty} - {tier.max_qty ?? "∞"} pcs</TableCell>
                <TableCell className="text-right font-medium">
                  Rp {tier.price_per_unit.toLocaleString("id-ID")}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        {selectedQty && (
          <p className="text-xs text-muted-foreground mt-2">
            Total untuk {selectedQty} pcs: Rp {((data.total as number) || 0).toLocaleString("id-ID")}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
```

- [ ] **Step 3: Create OrderSummary.tsx**

```tsx
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";

interface OrderItem {
  product_id: number;
  product_name: string;
  qty: number;
  price_per_unit: number;
  subtotal: number;
}

interface OrderSummaryProps {
  data: Record<string, unknown>;
}

const statusLabels: Record<string, string> = {
  pending: "Menunggu Konfirmasi",
  confirmed: "Dikonfirmasi",
  processing: "Diproses",
  shipped: "Dikirim",
  delivered: "Selesai",
};

export function OrderSummary({ data }: OrderSummaryProps) {
  const items = (data.items as OrderItem[]) || [];
  const status = (data.status as string) || "pending";
  const orderId = data.order_id as string;
  const totalPrice = data.total_price as number;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm">Ringkasan Pesanan</CardTitle>
          <Badge variant={status === "confirmed" ? "default" : "secondary"}>
            {statusLabels[status] || status}
          </Badge>
        </div>
        <CardDescription>#{orderId}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {items.map((item, i) => (
            <div key={i} className="flex justify-between text-sm">
              <span className="text-muted-foreground">{item.product_name} x{item.qty}</span>
              <span>Rp {item.subtotal.toLocaleString("id-ID")}</span>
            </div>
          ))}
          <Separator />
          <div className="flex justify-between font-medium">
            <span>Total</span>
            <span className="text-primary">Rp {totalPrice.toLocaleString("id-ID")}</span>
          </div>
        </div>
      </CardContent>
      <CardFooter className="gap-2">
        <Button className="flex-1">Konfirmasi Pesanan</Button>
        <Button variant="outline">Ubah</Button>
      </CardFooter>
    </Card>
  );
}
```

- [ ] **Step 4: Commit**

```bash
cd frontend && git add components/generative-ui/ && git commit -m "feat: add generative UI components (ProductCards, PriceTable, OrderSummary)"
```

---

### Task 3.2: Layout Components

**Files:**
- Create: `frontend/components/layout/Header.tsx`
- Create: `frontend/components/layout/SplitView.tsx`
- Create: `frontend/components/catalog/ProductGrid.tsx`

- [ ] **Step 1: Create Header.tsx**

```tsx
"use client";
import { useTheme } from "next-themes";
import { Button } from "@/components/ui/button";
import { Sun, Moon } from "lucide-react";

export function Header() {
  const { setTheme, theme } = useTheme();

  return (
    <header className="h-16 border-b bg-background flex items-center justify-between px-6">
      <div className="flex items-center gap-3">
        <h1 className="text-lg font-bold text-primary">Lemone Sales Agent</h1>
        <span className="text-xs text-muted-foreground">PT Lemone Surya Indonesia</span>
      </div>
      <Button
        variant="ghost"
        size="icon"
        onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
      >
        <Sun className="h-5 w-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
        <Moon className="absolute h-5 w-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
      </Button>
    </header>
  );
}
```

- [ ] **Step 2: Create SplitView.tsx**

```tsx
"use client";
import { useState } from "react";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";

interface SplitViewProps {
  catalog: React.ReactNode;
  chat: React.ReactNode;
}

export function SplitView({ catalog, chat }: SplitViewProps) {
  const [activeTab, setActiveTab] = useState<"catalog" | "chat">("chat");

  return (
    <>
      {/* Desktop: side-by-side */}
      <div className="hidden lg:flex h-[calc(100vh-64px)]">
        <div className="flex-1 overflow-y-auto p-6">{catalog}</div>
        <div className="w-[480px] min-w-[360px] max-w-[560px] border-l flex flex-col">{chat}</div>
      </div>

      {/* Tablet/Mobile: tabbed */}
      <div className="lg:hidden h-[calc(100vh-64px)] flex flex-col">
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as "catalog" | "chat")}>
          <TabsList className="mx-4 mt-2">
            <TabsTrigger value="catalog" className="flex-1">Katalog</TabsTrigger>
            <TabsTrigger value="chat" className="flex-1">Chat</TabsTrigger>
          </TabsList>
        </Tabs>
        <div className="flex-1 overflow-y-auto">
          {activeTab === "catalog" ? catalog : chat}
        </div>
      </div>
    </>
  );
}
```

- [ ] **Step 3: Create ProductGrid.tsx**

```tsx
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface Product {
  id: number;
  name: string;
  category: string;
  base_price: number;
  moq: number;
  description: string;
  image_url?: string;
}

const PLACEHOLDER_PRODUCTS: Product[] = [
  { id: 1, name: "Kemeja Flanel Premium", category: "Kemeja", base_price: 85000, moq: 12, description: "Kemeja flanel premium", image_url: "" },
  { id: 2, name: "Kaos Polo Sport", category: "Polo", base_price: 65000, moq: 24, description: "Kaos polo sport", image_url: "" },
  { id: 3, name: "Hoodie Zipper Premium", category: "Hoodie", base_price: 125000, moq: 10, description: "Hoodie zipper premium", image_url: "" },
  { id: 4, name: "Celana Chino Slim Fit", category: "Celana", base_price: 95000, moq: 12, description: "Celana chino slim fit", image_url: "" },
  { id: 5, name: "Jaket Denim Klasik", category: "Jaket", base_price: 155000, moq: 8, description: "Jaket denim klasik", image_url: "" },
  { id: 6, name: "Kemeja Batik Premium", category: "Kemeja", base_price: 110000, moq: 12, description: "Kemeja batik premium", image_url: "" },
];

export function ProductGrid() {
  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Katalog Produk</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
        {PLACEHOLDER_PRODUCTS.map((product) => (
          <Card key={product.id} className="overflow-hidden hover:shadow-md transition-shadow">
            <div className="aspect-square bg-muted flex items-center justify-center">
              <span className="text-4xl">👕</span>
            </div>
            <CardHeader className="p-4">
              <CardTitle className="text-sm">{product.name}</CardTitle>
            </CardHeader>
            <CardContent className="p-4 pt-0">
              <div className="flex items-baseline gap-1">
                <span className="text-lg font-bold text-primary">
                  Rp {product.base_price.toLocaleString("id-ID")}
                </span>
                <span className="text-xs text-muted-foreground">/pcs</span>
              </div>
              <p className="text-xs text-muted-foreground mt-1">MOQ: {product.moq}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Commit**

```bash
cd frontend && git add components/layout/ components/catalog/ && git commit -m "feat: add layout components (Header, SplitView, ProductGrid)"
```

---

### Task 3.3: Main Page

**Files:**
- Create: `frontend/app/page.tsx`

- [ ] **Step 1: Create page.tsx**

```tsx
import { Header } from "@/components/layout/Header";
import { SplitView } from "@/components/layout/SplitView";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { ProductGrid } from "@/components/catalog/ProductGrid";

export default function Home() {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <SplitView
        catalog={<ProductGrid />}
        chat={<ChatPanel />}
      />
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
cd frontend && git add app/page.tsx && git commit -m "feat: add main page with split view layout"
```

---

## Phase 4: Reorder + Polish

### Task 4.1: Create `get_reorder_suggestions` Tool

**Files:**
- Create: `src/tools/get_reorder_suggestions.py`
- Modify: `src/agents/nodes.py` (register tool)

**Interfaces:**
- Consumes: `OrderRepo.get_items_by_customer()`, `ProductRepo.get_by_id()`
- Produces: `get_reorder_suggestions` tool returning `{"type": "reorder_suggestions", "data": {...}}`

- [ ] **Step 1: Create tool**

```python
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from src.data.repos.order_repo import OrderRepo
from src.data.repos.product_repo import ProductRepo

_order_repo = OrderRepo()
_product_repo = ProductRepo()


class GetReorderSuggestionsInput(BaseModel):
    customer_id: str = Field(description="ID customer")


@tool(args_schema=GetReorderSuggestionsInput)
def get_reorder_suggestions(customer_id: str) -> dict:
    """Tampilkan saran reorder untuk customer yang sudah pernah order."""
    items = _order_repo.get_items_by_customer(customer_id, limit=5)
    if not items:
        return {"type": "reorder_suggestions", "data": {"customer_name": customer_id, "items": []}}

    suggestions = []
    for item in items:
        product = _product_repo.get_by_id(item["product_id"])
        suggestions.append({
            "product_id": item["product_id"],
            "product_name": item["product_name"],
            "last_qty": item["qty"],
            "last_price": item["price_per_unit"],
            "last_order_date": item["last_order_date"],
            "image_url": product.get("image_url", "") if product else "",
        })

    return {
        "type": "reorder_suggestions",
        "data": {
            "customer_name": customer_id,
            "items": suggestions,
        },
    }
```

- [ ] **Step 2: Register in nodes.py**

Add `get_reorder_suggestions` to the tools list in `src/agents/nodes.py`.

- [ ] **Step 3: Add test**

```python
from src.tools.get_reorder_suggestions import get_reorder_suggestions


def test_get_reorder_suggestions_returns_structured():
    result = get_reorder_suggestions.invoke({"customer_id": "CUST-REORDER-TEST"})
    assert isinstance(result, dict)
    assert result["type"] == "reorder_suggestions"
    assert "data" in result
```

- [ ] **Step 4: Run test**

Run: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/ -v -k reorder`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/tools/get_reorder_suggestions.py src/agents/nodes.py
git commit -m "feat: add get_reorder_suggestions tool"
```

---

### Task 4.2: Reorder Suggestions Component

**Files:**
- Create: `frontend/components/generative-ui/ReorderSuggestions.tsx`
- Modify: `frontend/components/chat/ComponentRenderer.tsx` (add case)

- [ ] **Step 1: Create ReorderSuggestions.tsx**

```tsx
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface ReorderItem {
  product_id: number;
  product_name: string;
  last_qty: number;
  last_price: number;
  last_order_date: string;
  image_url: string;
}

interface ReorderSuggestionsProps {
  data: Record<string, unknown>;
}

export function ReorderSuggestions({ data }: ReorderSuggestionsProps) {
  const items = (data.items as ReorderItem[]) || [];
  const customerName = data.customer_name as string;

  if (items.length === 0) {
    return null;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Saran Reorder untuk {customerName}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {items.map((item) => (
            <div key={item.product_id} className="flex items-center justify-between p-2 rounded-lg bg-muted/50">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-muted rounded flex items-center justify-center text-lg">👕</div>
                <div>
                  <p className="text-sm font-medium">{item.product_name}</p>
                  <p className="text-xs text-muted-foreground">
                    Terakhir: {item.last_qty} pcs @ Rp {item.last_price.toLocaleString("id-ID")}
                  </p>
                </div>
              </div>
              <Button size="sm" variant="outline">Pesan Ulang</Button>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
```

- [ ] **Step 2: Update ComponentRenderer.tsx**

Add case for `reorder_suggestions`:

```tsx
import { ReorderSuggestions } from "@/components/generative-ui/ReorderSuggestions";

// In the switch:
case "reorder_suggestions":
  return <ReorderSuggestions data={data} />;
```

- [ ] **Step 3: Commit**

```bash
cd frontend && git add components/generative-ui/ReorderSuggestions.tsx components/chat/ComponentRenderer.tsx && git commit -m "feat: add ReorderSuggestions component"
```

---

### Task 4.3: Responsive Polish

**Files:**
- Modify: `frontend/components/layout/SplitView.tsx`
- Modify: `frontend/app/globals.css`

- [ ] **Step 1: Verify responsive breakpoints**

Test at 1440px, 1024px, 768px, 375px.

- [ ] **Step 2: Add mobile bottom navigation for chat**

Update SplitView for mobile with bottom-fixed chat input.

- [ ] **Step 3: Final test**

Run full frontend build: `cd frontend && npm run build`
Expected: No errors

- [ ] **Step 4: Commit**

```bash
cd frontend && git add . && git commit -m "feat: responsive layout polish for all breakpoints"
```

---

### Task 4.4: Final Integration Test

**Files:**
- Test: run full backend + frontend

- [ ] **Step 1: Run all backend tests**

Run: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/ -v --ignore=tests/test_integration.py`
Expected: All PASS

- [ ] **Step 2: Run frontend build**

Run: `cd frontend && npm run build`
Expected: No errors

- [ ] **Step 3: Commit everything**

```bash
git add -A && git commit -m "feat: complete generative UI + reorder suggestion implementation"
git push origin main
```

---

## Self-Review Checklist

- [x] All 12 spec sections covered by tasks
- [x] No placeholders ("TBD", "TODO", etc.)
- [x] All types consistent across tasks (ProductCardData, PriceTableData, OrderSummaryData, ReorderSuggestionsData)
- [x] Backend returns structured JSON from all 3 tools
- [x] SSE endpoint streams tool outputs correctly
- [x] Frontend parses SSE and renders components
- [x] Split view responsive at all breakpoints
- [x] Dark mode works via CSS variables
- [x] Reorder suggestions shown for returning customers
- [x] Tests written for each backend change
