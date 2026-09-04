# Order Management System — Design Spec

**Date:** 2026-09-04
**Status:** Draft
**Author:** opencode

## Problem Statement

Reseller/Toko Fashion di seluruh Indonesia membeli grosir dari PT Lemone untuk dijual kembali. Saat ini, proses order masih manual via WhatsApp/admin, yang membutuhkan 30 menit - 1 jam per order. AI Agent harus bisa langsung memproses order dari chat.

## Target Customer

**Reseller/Toko Fashion** — pemilik toko kecil-menengah di seluruh Indonesia yang:
- Membeli grosir dari Lemone untuk dijual kembali dengan merek toko sendiri
- Butuh harga transparan, stok ready, pengiriman cepat
- Saat ini harus WhatsApp admin untuk order

## Business Risks

| Risk | Impact | Severity |
|------|--------|----------|
| Wrong pricing | Perusahaan rugi | High |
| Wrong discount | Perusahaan rugi | High |
| False stock info | Reseller kecewa | Medium |
| Double order | Stok terpotong 2x | Medium |
| Unauthorized order | Reseller marah | Medium |

## Solution: Order Management with HITL

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    API Layer                             │
│  POST /chat → chat_endpoint → agent.invoke()           │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                   Agent Layer                           │
│                                                         │
│  Read-only Tools (L0 - No HITL):                       │
│  ├─ search_products                                    │
│  ├─ get_product_detail                                 │
│  ├─ check_stock                                        │
│  ├─ calculate_price                                    │
│  ├─ get_alternatives                                   │
│  ├─ get_customer                                       │
│  ├─ get_order_history                                  │
│  └─ check_order_status                                 │
│                                                         │
│  Write Tools (L2 - HITL via interrupt):                │
│  ├─ create_order                                       │
│  └─ cancel_order                                       │
│                                                         │
│  Forbidden (L3 - Agent tidak boleh):                   │
│  ├─ Ubah harga                                         │
│  └─ Proses bayar                                       │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│              LangGraph HITL Layer                       │
│                                                         │
│  interrupt() → pause execution                         │
│  Command(resume=...) → resume with human input         │
│                                                         │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                  Checkpoint Layer                        │
│  thread_id → load/save state → memory                  │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                    DB Layer                             │
│  products │ customers │ orders │ order_items            │
└─────────────────────────────────────────────────────────┘
```

### Data Model

#### Tabel `customers`

```sql
CREATE TABLE customers (
    id TEXT PRIMARY KEY,           -- Format: CUST-{RANDOM8}
    name TEXT NOT NULL,            -- Nama toko/reseller
    phone TEXT,                    -- Nomor WhatsApp
    email TEXT,                    -- Opsional
    tier TEXT DEFAULT 'regular',   -- regular, vip, premium
    created_at TEXT NOT NULL,
    last_order_at TEXT
);
```

#### Tabel `orders`

```sql
CREATE TABLE orders (
    id TEXT PRIMARY KEY,           -- Format: ORD-{YYYYMMDD}-{RANDOM4}
    customer_id TEXT NOT NULL,     -- FK → customers.id
    items TEXT NOT NULL,           -- JSON: [{product_id, product_name, qty, price_per_unit, subtotal}]
    subtotal INTEGER NOT NULL,     -- Total sebelum diskon
    discount_amount INTEGER DEFAULT 0,
    total_price INTEGER NOT NULL,  -- Final price
    status TEXT NOT NULL DEFAULT 'pending',  -- pending → confirmed → processing → shipped → delivered → cancelled
    shipping_address TEXT,
    payment_status TEXT DEFAULT 'unpaid',    -- unpaid, paid, credit
    payment_terms INTEGER DEFAULT 0,         -- Hari kredit (0 = bayar langsung)
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);
```

#### Tabel `order_items`

```sql
CREATE TABLE order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT NOT NULL,        -- FK → orders.id
    product_id INTEGER NOT NULL,   -- FK → products.id
    product_name TEXT NOT NULL,    -- Snapshot nama produk
    qty INTEGER NOT NULL,
    price_per_unit INTEGER NOT NULL,
    subtotal INTEGER NOT NULL,     -- qty × price_per_unit
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);
```

### State Machine

```
         ┌──────────────┐
         │   pending    │  ← Order baru dibuat
         └──────┬───────┘
                │
                ▼
         ┌──────────────┐
    ┌────│  confirmed   │  ← Reseller konfirmasi
    │    └──────┬───────┘
    │           │
    ▼           ▼
┌────────┐  ┌──────────────┐
│cancelled│  │  processing  │  ← Mulai diproses
└────────┘  └──────┬───────┘
                   │
                   ▼
            ┌──────────────┐
            │   shipped    │  ← Dikirim
            └──────┬───────┘
                   │
                   ▼
            ┌──────────────┐
            │  delivered   │  ← Sampai
            └──────────────┘
```

**Valid Transitions:**
- `pending` → `confirmed`, `cancelled`
- `confirmed` → `processing`, `cancelled`
- `processing` → `shipped`
- `shipped` → `delivered`

### LangGraph HITL Pattern

Menggunakan `interrupt()` dari LangGraph untuk confirmation flow:

```python
from langgraph.types import interrupt, Command

def create_order_node(state: AgentState) -> Command[Literal["llm", "tools"]]:
    """Node yang meminta konfirmasi sebelum create order."""
    
    # Build order summary
    order_summary = build_order_summary(state["pending_order"])
    
    # Interrupt untuk konfirmasi
    human_response = interrupt({
        "action": "create_order",
        "summary": order_summary,
        "message": "Ketik 'YA' untuk konfirmasi atau 'BATAL' untuk membatalkan"
    })
    
    # Process response
    if human_response and human_response.strip().upper() == "YA":
        # Execute order
        order_id = execute_create_order(state["pending_order"])
        return Command(
            update={
                "pending_order": None,
                "last_order_id": order_id
            },
            goto="llm"
        )
    else:
        # Cancel
        return Command(
            update={"pending_order": None},
            goto="llm"
        )
```

### Error Handling

| Error Type | Strategy | Implementation |
|------------|----------|----------------|
| Stok tidak cukup | Retry with alternatif | check_stock → if insufficient → get_alternatives |
| Harga berubah | Re-confirm dengan harga baru | calculate_price → if different → interrupt again |
| Database error | Retry + log | RetryPolicy(max_attempts=3) |
| LLM timeout | Retry 1x, lalu fail | RetryPolicy(max_attempts=2) |
| Input tidak valid | Agent minta klarifikasi | Validate in tool, return error message |

### Testing Strategy

**Unit Tests (40 tests):**
- create_order: success, stok kurang, produk tidak ada, qty invalid
- cancel_order: pending (ok), confirmed (ok), processing (fail)
- calculate_price: normal, diskon, tier vip, tier premium

**Integration Tests (15 tests):**
- Full order flow: search → check_stock → calculate → confirm → create
- Order with confirmation: user bilang YA
- Order cancelled: user bilang BATAL
- Stok berubah saat konfirmasi
- Harga berubah saat konfirmasi

**E2E Tests (5 scenarios):**
- Reseller order 200 pcs
- Reseller cek status order
- Reseller batal order (pending)
- Reseller order stok kurang
- Reseller tanya "order kemana?"

### Implementation Plan

| Task | Description | Est. Time |
|------|-------------|-----------|
| 1 | Add DB tables (customers, orders, order_items) | 30 min |
| 2 | Create tool functions (create_order, cancel_order, get_customer, check_order_status, get_order_history) | 2 hours |
| 3 | Add interrupt-based HITL to graph | 1 hour |
| 4 | Update system prompt for order flow | 30 min |
| 5 | Add unit tests | 1 hour |
| 6 | Add integration tests | 1 hour |
| 7 | Manual E2E testing | 30 min |
| **Total** | | **6.5 hours** |
