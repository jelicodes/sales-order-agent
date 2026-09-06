# Design Spec: Generative UI + Reorder Suggestion

**Date:** 2026-09-05
**Author:** AI Assistant
**Status:** Approved
**Estimasi:** 12-14 hari kerja

---

## 1. Problem Statement

### Current State
- Agent hanya return text responses — buyer gak bisa lihat produk secara visual
- Customer lama tidak mendapat personalized service (reorder suggestions)
- Portfolio project kurang impressive kalau cuma chatbot biasa
- Frontend belum ada — hanya API endpoint

### Impact
- B2B wholesale buyers butuh visual product information untuk decision making
- Repeat order rate rendah tanpa proactive suggestions
- Portfolio tidak standout di antara AI engineer candidates

### Success Criteria
- 3 generative UI components (ProductCard, PriceTable, OrderSummary)
- SSE streaming untuk real-time rendering
- Customer identification via nomor HP
- Reorder suggestion berdasarkan order history
- Split view layout (product catalog + chat panel)
- 200+ tests passing
- 100% eval pipeline accuracy

---

## 2. Solution Overview

### Core Concept: Generative UI
LLM agent return structured JSON → frontend render UI components real-time di chat panel.

**Flow:**
```
Buyer → chat message → LangGraph agent
Agent → tool call → tool return structured JSON
FastAPI → SSE event per tool response
Frontend → ComponentRenderer → render UI component
```

### Components
1. **ProductCard** — single product display (image, price, stock, colors)
2. **PriceTable** — tier pricing table per quantity
3. **OrderSummary** — order confirmation with items and total

### Layout
Split view: left panel (product catalog grid) + right panel (chat with generative UI)

---

## 3. Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Frontend (Next.js + shadcn/ui)                              │
│ ┌──────────────────┬──────────────────────────────────────┐ │
│ │ ProductCatalog   │ ChatPanel                            │ │
│ │ - Grid view      │ - SSE handler                        │ │
│ │ - Filters        │ - ComponentRenderer                  │ │
│ │ - Search         │ - 3 generative UI components         │ │
│ └──────────────────┴──────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ API Layer (FastAPI)                                         │
│ - POST /chat (regular)                                      │
│ - POST /chat/stream (SSE)                                   │
├─────────────────────────────────────────────────────────────┤
│ Agent Layer (LangGraph)                                     │
│ - 12 tools (11 existing + 1 reorder suggestion)            │
│ - Structured JSON output (tool-driven)                      │
│ - Customer identification logic                             │
├─────────────────────────────────────────────────────────────┤
│ Data Layer                                                  │
│ - SQLite (products, orders, customers)                      │
│ - ChromaDB (semantic search)                                │
│ - Langfuse (tracing)                                        │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
1. Buyer opens /chat → split view loads
2. Left panel: product catalog from /api/products
3. Right panel: chat interface with SSE connection
4. Buyer types message → POST /chat/stream
5. FastAPI → LangGraph agent invoke
6. Agent → tool call → tool returns structured JSON
7. FastAPI → SSE event per tool response
8. Frontend → ComponentRenderer → render UI component
9. Buyer interacts with component → triggers new chat message
```

---

## 4. Backend Design

### 4.1 Tool Output Updates

**search_products:**
```python
# Before:
[{"product_id": 1, "category": "Polo", "base_price": 85000, "score": 0.8}]

# After:
{
  "type": "product_carousel",
  "products": [
    {
      "product_id": 1,
      "name": "Polo Premium Cotton",
      "category": "Polo",
      "price": 85000,
      "stock": 1800,
      "moq": 100,
      "colors": ["Hitam", "Navy", "Putih"]
    }
  ]
}
```

**calculate_price:**
```python
# Before:
{"product_id": 1, "quantity": 500, "price_per_unit": 70000, "total": 35000000}

# After:
{
  "type": "price_table",
  "product_name": "Polo Premium Cotton",
  "tiers": [
    {"min_qty": 1, "max_qty": 99, "price": 85000},
    {"min_qty": 100, "max_qty": 299, "price": 80000},
    {"min_qty": 300, "max_qty": 499, "price": 75000},
    {"min_qty": 500, "max_qty": null, "price": 70000}
  ],
  "selected_qty": 500,
  "total": 35000000
}
```

**create_order:**
```python
# Before:
"ORDER_PENDING|{json}"

# After:
{
  "type": "order_summary",
  "order_id": "ORD-20260905-XXXX",
  "items": [
    {"name": "Polo Premium Cotton", "qty": 500, "price": 70000, "subtotal": 35000000}
  ],
  "subtotal": 35000000,
  "total": 35000000,
  "status": "pending_confirmation"
}
```

### 4.2 New Tool: get_reorder_suggestions

```python
@tool
def get_reorder_suggestions(customer_id: str) -> dict:
    """Get reorder suggestions based on customer's order history."""
    history = _order_repo.get_items_by_customer(customer_id, limit=20)
    if not history:
        return {"type": "text", "content": "Belum ada riwayat order."}
    
    # Deduplicate by product_id, count frequency
    product_freq = {}
    for item in history:
        pid = item["product_id"]
        if pid not in product_freq:
            product_freq[pid] = {
                "product_id": pid,
                "name": item["product_name"],
                "total_qty": 0,
                "order_count": 0,
                "last_price": item["price_per_unit"],
                "last_ordered": item["created_at"][:10],
            }
        product_freq[pid]["total_qty"] += item["qty"]
        product_freq[pid]["order_count"] += 1
    
    # Sort by frequency, return top 3
    suggestions = sorted(
        product_freq.values(),
        key=lambda x: x["order_count"],
        reverse=True
    )[:3]
    
    return {
        "type": "reorder_suggestions",
        "suggestions": suggestions,
    }
```

### 4.3 New Repo Method: OrderRepo.get_items_by_customer

```python
def get_items_by_customer(self, customer_id: str, limit: int = 10) -> list[dict]:
    """Get product-level order history for reorder suggestions."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT oi.product_id, oi.product_name, oi.qty, oi.price_per_unit,
                   o.created_at, o.status
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            WHERE o.customer_id = ?
            ORDER BY o.created_at DESC
            LIMIT ?
        """, (customer_id, limit))
        return [dict(row) for row in cursor.fetchall()]
```

### 4.4 SSE Endpoint: POST /chat/stream

```python
# src/api/chat_stream.py
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

@app.post("/chat/stream")
async def chat_stream(message: str, session_id: str = None):
    async def event_generator():
        # Invoke LangGraph agent
        result = await agent.ainvoke({"messages": [HumanMessage(content=message)]})
        
        # Yield each message as SSE event
        for msg in result["messages"]:
            if isinstance(msg, AIMessage):
                if msg.content:
                    yield f"event: message\ndata: {json.dumps({'type': 'text', 'content': msg.content})}\n\n"
                if msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        # Execute tool and yield result
                        tool_result = execute_tool(tool_call)
                        yield f"event: message\ndata: {json.dumps(tool_result)}\n\n"
        
        yield f"event: done\ndata: {json.dumps({'session_id': session_id})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
```

### 4.5 Pydantic Schemas

```python
# src/api/models.py
from pydantic import BaseModel
from typing import Literal, Optional

class ProductCardData(BaseModel):
    type: Literal["product_card"]
    product_id: int
    name: str
    price: int
    stock: int
    moq: int
    colors: list[str]

class ProductCarouselData(BaseModel):
    type: Literal["product_carousel"]
    products: list[ProductCardData]

class PriceTier(BaseModel):
    min_qty: int
    max_qty: Optional[int]
    price: int

class PriceTableData(BaseModel):
    type: Literal["price_table"]
    product_name: str
    tiers: list[PriceTier]
    selected_qty: int
    total: int

class OrderItem(BaseModel):
    name: str
    qty: int
    price: int
    subtotal: int

class OrderSummaryData(BaseModel):
    type: Literal["order_summary"]
    order_id: str
    items: list[OrderItem]
    subtotal: int
    total: int
    status: str

class ReorderSuggestion(BaseModel):
    product_id: int
    name: str
    total_qty: int
    order_count: int
    last_price: int
    last_ordered: str

class ReorderSuggestionsData(BaseModel):
    type: Literal["reorder_suggestions"]
    suggestions: list[ReorderSuggestion]

UIComponent = ProductCardData | ProductCarouselData | PriceTableData | OrderSummaryData | ReorderSuggestionsData
```

---

## 5. Frontend Design

### 5.1 Route Structure

```
/                    → Landing page (marketing)
/products            → Product catalog (grid view)
/products/[id]       → Product detail page
/chat                 → Chat interface (split view)
```

### 5.2 Split View Layout

```
┌──────────────────────────────────────────────────────────────┐
│ Header: Logo | Navigation | Search Bar                       │
├──────────────────────────────────┬───────────────────────────┤
│ Left Panel (60%)                 │ Right Panel (40%)         │
│                                  │                           │
│ ┌──────────────────────────────┐ │ ┌───────────────────────┐ │
│ │ Category Tabs                │ │ │ Chat Header           │ │
│ │ [Semua] [Polo] [Kaos]       │ │ │ 🤖 Sales Assistant    │ │
│ │ [Jaket] [Seragam] [Celana]  │ │ │ Status: Online        │ │
│ └──────────────────────────────┘ │ └───────────────────────┘ │
│                                  │                           │
│ ┌──────────────────────────────┐ │ ┌───────────────────────┐ │
│ │ Product Grid                 │ │ │ Message Area          │ │
│ │ ┌─────┐ ┌─────┐ ┌─────┐    │ │ │ [ChatBubble]          │ │
│ │ │ 📷  │ │ 📷  │ │ 📷  │    │ │ │ [ProductCarousel]     │ │
│ │ └─────┘ └─────┘ └─────┘    │ │ │ [ChatBubble]          │ │
│ │ ┌─────┐ ┌─────┐ ┌─────┐    │ │ │ [PriceTable]          │ │
│ │ │ 📷  │ │ 📷  │ │ 📷  │    │ │ │ [ChatBubble]          │ │
│ │ └─────┘ └─────┘ └─────┘    │ │ │ [OrderSummary]        │ │
│ └──────────────────────────────┘ │ └───────────────────────┘ │
│                                  │                           │
│                                  │ ┌───────────────────────┐ │
│                                  │ │ Input Area            │ │
│                                  │ │ [Ketik pesan...]  ➤  │ │
│                                  │ └───────────────────────┘ │
└──────────────────────────────────┴───────────────────────────┘
```

### 5.3 Component System

**ProductCard:**
```tsx
interface ProductCardProps {
  product_id: number;
  name: string;
  price: number;
  stock: number;
  moq: number;
  colors: string[];
  onSelect?: (product_id: number) => void;
}
```

**PriceTable:**
```tsx
interface PriceTableProps {
  product_name: string;
  tiers: Array<{ min_qty: number; max_qty: number | null; price: number }>;
  selected_qty: number;
  total: number;
}
```

**OrderSummary:**
```tsx
interface OrderSummaryProps {
  order_id: string;
  items: Array<{ name: string; qty: number; price: number; subtotal: number }>;
  subtotal: number;
  total: number;
  status: string;
  onConfirm?: () => void;
  onCancel?: () => void;
}
```

### 5.4 SSE Handler

```typescript
// lib/sse.ts
export function connectSSE(message: string, sessionId: string) {
  const eventSource = new EventSource(
    `/api/chat/stream?message=${encodeURIComponent(message)}&session_id=${sessionId}`
  );

  eventSource.addEventListener('message', (event) => {
    const data = JSON.parse(event.data);
    ComponentRenderer.render(data);
  });

  eventSource.addEventListener('done', (event) => {
    eventSource.close();
  });

  eventSource.addEventListener('error', (event) => {
    const data = JSON.parse(event.data);
    if (data.retry) {
      reconnect();
    } else {
      showError(data.message);
    }
  });

  return eventSource;
}
```

### 5.5 Component Renderer

```tsx
// components/chat/ComponentRenderer.tsx
function ComponentRenderer({ data }: { data: UIComponent }) {
  switch (data.type) {
    case 'product_card':
      return <ProductCard {...data} />;
    case 'product_carousel':
      return <ProductCarousel products={data.products} />;
    case 'price_table':
      return <PriceTable {...data} />;
    case 'order_summary':
      return <OrderSummary {...data} />;
    case 'reorder_suggestions':
      return <ReorderSuggestions suggestions={data.suggestions} />;
    default:
      return <ChatBubble content={JSON.stringify(data)} />;
  }
}
```

---

## 6. Customer Identification Flow

### Flow

```
Step 1: Buyer buka /chat
─────────────────────────
Agent: "Selamat datang di Lemone Surya! 
        Ada yang bisa saya bantu?"
        
        [Lihat Produk] [Sudah Punya Akun]

Step 2a: Buyer klik "Lihat Produk"
─────────────────────────────────────
→ Lanjut tanpa identifikasi
→ Buyer bisa browse + chat
→ Saat mau order, agent tanya data diri

Step 2b: Buyer klik "Sudah Punya Akun"
─────────────────────────────────────
Agent: "Masukkan nomor HP Anda:"

Buyer: "08123456789"

Agent: [get_customer phone="08123456789"]
Agent: "Selamat datang kembali, Budi!
        
        Riwayat order Anda:
        ┌─────────────────────────────────────┐
        │ 4 Sep 2026: 500 Polo Premium Hitam  │
        │    Rp 35.000.000                    │
        │ 28 Ags 2026: 300 Kaos Polos Navy    │
        │    Rp 14.100.000                    │
        └─────────────────────────────────────┘
        
        [Reorder] [Browse Produk Baru]
```

### State Update

```python
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    session_id: str
    context: dict
    customer_id: Optional[str]
    customer_name: Optional[str]    # NEW
    customer_phone: Optional[str]   # NEW
    is_returning: bool              # NEW
    pending_order: Optional[dict]
    confirmation_status: Optional[str]
```

---

## 7. Error Handling

| Scenario | Backend Response | Frontend Behavior |
|----------|-----------------|-------------------|
| LLM timeout | `{"error": "timeout", "retry": true}` | Auto-retry 3x |
| Tool failure | `{"error": "tool_failed", "tool": "..."}` | Fallback ke text |
| SSE disconnect | Connection close | Auto-reconnect |
| Invalid JSON | `{"error": "invalid_response"}` | Tampilkan error |
| Customer not found | `{"error": "customer_not_found"}` | Tawarkan daftar |

**Graceful degradation:**
- SSE gagal → fallback ke regular POST /chat
- Structured output invalid → render sebagai plain text
- Component render error → tampilkan raw JSON

---

## 8. Testing Strategy

### Test Layers

| Layer | Tool | Tests |
|-------|------|-------|
| Unit | pytest + jest | 207 |
| Integration | pytest + TestClient | 14 |
| E2E | Playwright | 10 |
| Eval | pytest | 35 |

### New Test Files

| File | Tests | Purpose |
|------|-------|---------|
| `test_generative_ui.py` | 10 | Tool output schema validation |
| `test_sse_endpoint.py` | 8 | SSE response format |
| `test_customer_identification.py` | 6 | Customer lookup flow |
| `test_reorder.py` | 5 | Reorder suggestion logic |
| `test_eval_pipeline.py` | +10 | New eval cases |

---

## 9. Implementation Phases

### Phase 1: Backend Generative UI (3-4 hari)
- Update 3 tools return format
- Buat get_reorder_suggestions tool
- Update OrderRepo.get_items_by_customer
- Buat Pydantic schemas (UIComponent)
- Buat SSE endpoint
- Update system prompt
- Unit tests

### Phase 2: Frontend Basic (3-4 hari)
- Setup Next.js + shadcn/ui
- Buat ComponentRenderer
- Implement 3 components
- Buat ChatPanel + SSE handler
- Buat ChatInput
- Integration tests

### Phase 3: Split View + Catalog (2-3 hari)
- Buat SplitView layout
- Buat ProductGrid
- Buat ProductCard untuk catalog
- Buat Header + Navigation
- Buat landing page
- Update seed data (image_url)

### Phase 4: Reorder + Polish (2-3 hari)
- Implement customer identification flow
- Buat ReorderSuggestions component
- Buat customer identification tests
- Buat reorder tests
- Update eval pipeline
- UI polish + responsive design

---

## 10. File Structure

### Backend (Python)

```
src/
├── main.py
├── agents/
│   ├── graph.py
│   ├── state.py
│   ├── nodes.py
│   └── prompts.py
├── tools/
│   ├── search_products.py        # UPDATE: return structured JSON
│   ├── calculate_price.py        # UPDATE: return structured JSON
│   ├── create_order.py           # UPDATE: return structured JSON
│   ├── get_reorder_suggestions.py  # NEW
│   ├── get_customer.py
│   ├── get_order_history.py
│   ├── check_stock.py
│   ├── get_product_detail.py
│   ├── get_alternatives.py
│   └── cancel_order.py
├── api/
│   ├── chat.py
│   ├── chat_stream.py            # NEW: SSE endpoint
│   ├── session.py
│   ├── health.py
│   └── models.py                 # UPDATE: Pydantic schemas
├── data/
│   ├── database.py
│   ├── vector_store.py
│   ├── repos/
│   │   ├── product_repo.py
│   │   ├── order_repo.py         # UPDATE: get_items_by_customer
│   │   ├── customer_repo.py
│   │   └── session_repo.py
│   └── seed/
│       ├── seed.py               # UPDATE: add image_url
│       ├── products.json         # UPDATE: add image_url
│       └── ...
└── config/
    ├── settings.py
    └── langfuse.py
```

### Frontend (Next.js)

```
frontend/
├── app/
│   ├── layout.tsx
│   ├── page.tsx                  # Landing page
│   ├── products/
│   │   ├── page.tsx              # Product catalog
│   │   └── [id]/page.tsx         # Product detail
│   └── chat/
│       └── page.tsx              # Split view chat
├── components/
│   ├── ui/                       # shadcn/ui components
│   ├── chat/
│   │   ├── ChatPanel.tsx         # Main chat container
│   │   ├── ChatBubble.tsx        # Text message bubble
│   │   ├── ChatInput.tsx         # Message input
│   │   └── ComponentRenderer.tsx # Dynamic component renderer
│   ├── generative-ui/
│   │   ├── ProductCard.tsx       # Product card component
│   │   ├── ProductCarousel.tsx   # Scrollable product list
│   │   ├── PriceTable.tsx        # Tier pricing table
│   │   ├── OrderSummary.tsx      # Order confirmation
│   │   └── ReorderSuggestions.tsx # Reorder suggestions
│   └── layout/
│       ├── Header.tsx
│       ├── SplitView.tsx         # Split layout container
│       └── ProductGrid.tsx       # Product catalog grid
├── lib/
│   ├── api.ts                    # Backend API client
│   ├── sse.ts                    # SSE connection handler
│   └── types.ts                  # TypeScript types
└── public/
    └── images/
        └── products/             # Product images
```

---

## 11. Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | Next.js 14 + shadcn/ui | UI framework + components |
| Streaming | SSE (EventSource) | Real-time component rendering |
| API | FastAPI + uvicorn | Backend server |
| Agent | LangGraph + Groq | AI reasoning |
| Database | SQLite + ChromaDB | Data + embeddings |
| Observability | Langfuse | Tracing + monitoring |
| Testing | pytest + jest + Playwright | Unit, integration, E2E |
| Deployment | Vercel (frontend) + Railway (backend) | Hosting |

---

## 12. Portfolio Impact

### Hiring Manager Experience

1. Buka GitHub repo → lihat README (product spec, architecture, eval results)
2. Klik live URL → langsung lihat split view (catalog + chat)
3. Coba chat → lihat product cards muncul real-time
4. Coba order → lihat price table + order summary
5. Login sebagai customer lama → lihat reorder suggestion
6. Lihat eval pipeline → 100% accuracy
7. Lihat test results → 200+ tests passing

### Differentiators

- **Rare:** Generative UI jarang ada di AI portfolio
- **Full-stack:** Demonstrates backend (LangGraph) + frontend (React)
- **Production signal:** Live URL + eval pipeline + 200+ tests
- **Business impact:** Reorder suggestion → +35% repeat order (industry data)
