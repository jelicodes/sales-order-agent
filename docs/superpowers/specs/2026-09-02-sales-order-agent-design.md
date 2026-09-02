# Sales Order Agent — PT Lemone Surya Indonesia

**Date:** 2026-09-02
**Status:** Approved
**Author:** AI-assisted design

## Overview

AI Agent berbasis LangGraph (ReAct pattern) yang membantu customer proses order fashion grosir B2B. Multi-turn conversation (3-5 turns) dengan 6 tools, synthetic data PT Lemone, backend FastAPI.

**Goal:** Portfolio project untuk melamar posisi AI Engineer di PT Lemone Surya Indonesia. Menunjukkan pemahaman agentic AI, RAG, tool use, dan business acumen di industri fashion grosir B2B.

## Tech Stack

| Component | Technology | Reasoning |
|-----------|-----------|-----------|
| Agent Framework | LangChain + LangGraph | Requirement lowongan, ReAct pattern support |
| LLM Provider | Groq (GPT OSS) | Fast inference, free tier, LangChain integration |
| Backend | FastAPI | Async, type-safe, auto docs, production-ready |
| Vector DB | ChromaDB | Ringan, in-process, cocok untuk demo |
| Database | SQLite | Simple, no setup, cukup untuk synthetic data |
| Frontend | React/Next.js | Phase 2, backend first |

## Architecture

```
┌─────────────────────────────────────────────────┐
│                   FastAPI Server                 │
│  POST /chat   POST /session   GET /health       │
└─────────────┬───────────────────────────────────┘
              │
┌─────────────▼───────────────────────────────────┐
│              LangGraph Agent (ReAct)             │
│                                                  │
│  State: messages, context, tool_results          │
│  Nodes: llm_node → tool_node → conditional      │
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │ LLM Node │→ │Tool Node │→ │ Response Node│  │
│  │ (Groq)   │  │(execute) │  │ (format)     │  │
│  └──────────┘  └──────────┘  └──────────────┘  │
└─────────────┬───────────────────────────────────┘
              │
┌─────────────▼───────────────────────────────────┐
│                   Tools Layer                    │
│  search_products  │  check_stock  │  calc_price  │
│  get_product_spec │  create_quote │  get_altern. │
└─────────────┬───────────────────────────────────┘
              │
┌─────────────▼───────────────────────────────────┐
│              Data Layer                          │
│  ChromaDB (vectors)  │  SQLite (structured)      │
│  - product_embeddings│  - products               │
│                      │  - price_tiers            │
│                      │  - stock                  │
│                      │  - sessions               │
│                      │  - conversations          │
│                      │  - quotes                 │
└─────────────────────────────────────────────────┘
```

**Request flow:**
1. User kirim message → FastAPI terima
2. LangGraph agent mulai ReAct loop
3. LLM (Groq) reason → decide tool → execute tool
4. Tool result dikembalikan ke LLM → reason lagi
5. Sampai LLM decide untuk final response
6. Response dikirim kembali ke user

**Session management:** Setiap percakapan punya session ID. Context disimpan di SQLite (conversation history + extracted constraints).

## Tools

### Tool 1: search_products

| Attribute | Value |
|-----------|-------|
| Fungsi | Translate natural language query → produk dari katalog |
| Input | `query: str`, `filters: dict` (optional: kategori, warna, bahan) |
| Output | `list[dict]` — ranked products dengan relevance score |
| Contoh | `search_products("kaos polo hitam")` → `[{id: 1, name: "Polo Premium", score: 0.95}, ...]` |

### Tool 2: get_product_detail

| Attribute | Value |
|-----------|-------|
| Fungsi | Ambil spesifikasi lengkap 1 produk |
| Input | `product_id: int` |
| Output | `dict` — name, category, description, bahan, ukuran, warna, MOQ, lead_time |
| Contoh | `get_product_detail(1)` → `{name: "Polo Premium", bahan: "Cotton Combed 30s", moq: 100, lead_time_days: 5}` |

### Tool 3: check_stock

| Attribute | Value |
|-----------|-------|
| Fungsi | Cek ketersediaan stok real-time |
| Input | `product_id: int`, `quantity: int` |
| Output | `dict` — available (bool), current_stock, warehouse, restock_date (if unavailable) |
| Contoh | `check_stock(1, 500)` → `{available: true, stock: 1200, warehouse: "Tanah Abang"}` |

### Tool 4: calculate_price

| Attribute | Value |
|-----------|-------|
| Fungsi | Hitung harga berdasarkan qty + tier + diskon |
| Input | `product_id: int`, `quantity: int`, `discount_code: str` (optional) |
| Output | `dict` — price_per_unit, subtotal, discount_amount, total, applicable_tier |
| Contoh | `calculate_price(1, 500)` → `{unit: 75000, subtotal: 37500000, discount: 5, total: 35625000}` |

### Tool 5: create_quote

| Attribute | Value |
|-----------|-------|
| Fungsi | Generate penawaran final |
| Input | `items: list[dict]`, `customer_info: dict` |
| Output | `dict` — quote_id, itemized_breakdown, grand_total, valid_until, notes |
| Contoh | `create_quote([{product_id: 1, qty: 500}], {...})` → `{quote_id: "Q-2026-001", total: "Rp 35.625.000"}` |

### Tool 6: get_alternatives

| Attribute | Value |
|-----------|-------|
| Fungsi | Cari produk pengganti (stok kurang / budget tidak sesuai) |
| Input | `original_product_id: int`, `reason: str` ("stock" / "budget") |
| Output | `list[dict]` — alternatif dengan perbandingan harga & spesifikasi |
| Contoh | `get_alternatives(1, "budget")` → `[{id: 2, name: "Polo Basic", price_diff: "-20%"}]` |

## Conversation Flow

### Normal Flow (5 Turns)

**Turn 1: Inquiry**
```
Customer: "Saya butuh 500 kaos polo hitam untuk seragam karyawan"
Agent: search_products("kaos polo hitam") → find 3 products
       get_product_detail(top 2 products)
       check_stock(product_1, 500)
       check_stock(product_2, 500)
Response: "Saya temukan 2 opsi:
          1. Polo Premium - Rp 85.000/pc, stok 1200 ✓
          2. Polo Basic - Rp 65.000/pc, stok 800 ✓
          Mau saya buatkan penawaran untuk yang mana?"
```

**Turn 2: Specification**
```
Customer: "Yang Premium. Tapi bisa warna navy juga gak?"
Agent: get_product_detail(polo_premium) → check available colors
       check_stock(polo_premium_navy, 500)
Response: "Polo Premium tersedia dalam warna:
          - Hitam (stok: 1200) ✓
          - Navy (stok: 950) ✓
          Untuk 500 pcs navy, stok aman. Mau lanjut?"
```

**Turn 3: Quote**
```
Customer: "Oke, buatkan penawaran 500 pcs navy"
Agent: calculate_price(polo_premium_navy, 500)
       → unit: 80.000 (tier 300-500), subtotal: 40.000.000
       create_quote([{polo_premium_navy, 500}], customer_info)
Response: "Penawaran Q-2026-001:
          - 500 x Polo Premium Navy @ Rp 80.000
          - Subtotal: Rp 40.000.000
          - Berlaku 7 hari
          Ada yang mau diubah?"
```

**Turn 4: Negotiation**
```
Customer: "Bisa diskon kalau 700 pcs?"
Agent: calculate_price(polo_premium_navy, 700)
       → unit: 75.000 (tier 500+), subtotal: 52.500.000
       check_stock(polo_premium_navy, 700) → stock: 950 ✓
Response: "Untuk 700 pcs:
          - Harga satuan: Rp 75.000 (turun dari Rp 80.000)
          - Subtotal: Rp 52.500.000
          - Hemat Rp 2.500.000 dari harga 500 pcs
          Stok masih cukup (950 pcs tersedia).
          Mau saya update penawarannya?"
```

**Turn 5: Confirmation**
```
Customer: "Oke, 700 pcs navy. Kirim penawaran finalnya"
Agent: create_quote([{polo_premium_navy, 700}], customer_info)
Response: "Penawaran final Q-2026-001:
          - 700 x Polo Premium Navy @ Rp 75.000
          - Total: Rp 52.500.000
          - Estimasi produksi: 5-7 hari kerja
          - Berlaku hingga: 9 September 2026
          Terima kasih! Silakan hubungi sales kami untuk konfirmasi."
```

### Edge Cases

**Edge Case 1: Stok Tidak Cukup**
- check_stock → available: false
- Agent suggest: (1) split order, (2) ganti produk, (3) mix
- Jangan janji stok yang tidak ada

**Edge Case 2: Budget Tidak Sesuai**
- calculate_price → total > budget
- Agent suggest: (1) produk lebih murah, (2) kurangi qty, (3) mix produk

**Edge Case 3: MOQ Tidak Terpenuhi**
- get_product_detail → moq > requested qty
- Agent suggest: (1) naikkan ke MOQ, (2) ganti produk dengan MOQ lebih rendah

**Edge Case 4: Produk Tidak Ditemukan**
- search_products → 0 results
- Agent inform kategori produk yang tersedia, offer bantuan

**Edge Case 5: Deadline Tidak Realistis**
- get_product_detail → lead_time > deadline
- Agent suggest: (1) stok ready, (2) adjust timeline, (3) warna ready stock

**Edge Case 6: Follow-up Di Luar Scope**
- Pertanyaan pembayaran, klaim, komplain
- Agent eskalasi ke manusia, provide info yang tersedia

## Data Model

### SQLite Schema

```sql
-- Produk
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    base_price REAL NOT NULL,
    moq INTEGER NOT NULL DEFAULT 1,
    lead_time_days INTEGER NOT NULL DEFAULT 5
);

-- Varian produk (ukuran, warna)
CREATE TABLE product_variants (
    id INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL,
    size TEXT,
    color TEXT NOT NULL,
    sku TEXT UNIQUE NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Harga berdasarkan quantity tier
CREATE TABLE price_tiers (
    id INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL,
    min_qty INTEGER NOT NULL,
    max_qty INTEGER,
    price_per_unit REAL NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Stok
CREATE TABLE stock (
    id INTEGER PRIMARY KEY,
    variant_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    warehouse_location TEXT NOT NULL,
    FOREIGN KEY (variant_id) REFERENCES product_variants(id)
);

-- Diskon
CREATE TABLE discounts (
    id INTEGER PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,
    type TEXT NOT NULL,  -- 'percentage' or 'fixed'
    value REAL NOT NULL,
    min_qty INTEGER,
    valid_until DATE
);

-- Sessions
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    customer_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'active'
);

-- Conversations
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    tool_calls TEXT,  -- JSON array of tool calls
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- Quotes
CREATE TABLE quotes (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    items_json TEXT NOT NULL,  -- JSON array of items
    total_price REAL NOT NULL,
    valid_until DATE NOT NULL,
    status TEXT DEFAULT 'pending',
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);
```

### ChromaDB Collections

- **products** — product descriptions, specs, embedding untuk semantic search
- **Metadata:** product_id, category, price_range

### Synthetic Data

~50 produk fashion grosir:
- Kategori: Kaos, Polo, Jaket, Seragam, Celana, Aksesoris
- 3-4 varian warna per produk
- 3-4 ukuran per produk (S, M, L, XL)
- 3-4 price tier per produk (1-99, 100-299, 300-499, 500+)
- Stok realistis: 200-2000 pcs per varian
- 5-8 diskon aktif

## Project Structure

```
portfolio-PT-Lemone-Surya-Indonesia/
├── AGENTS.md
├── docs/
│   ├── agents/
│   │   ├── issue-tracker.md
│   │   ├── triage-labels.md
│   │   └── domain.md
│   └── superpowers/specs/
│       └── 2026-09-02-sales-order-agent-design.md  (this file)
│
├── src/
│   ├── __init__.py
│   ├── main.py                    # FastAPI entry point
│   │
│   ├── agents/                    # LangGraph Agent
│   │   ├── __init__.py
│   │   ├── graph.py               # State graph definition
│   │   ├── state.py               # Agent state schema
│   │   ├── nodes.py               # LLM node, tool node, response node
│   │   └── prompts.py             # System prompts
│   │
│   ├── tools/                     # Agent tools (6 files)
│   │   ├── __init__.py
│   │   ├── search_products.py
│   │   ├── get_product_detail.py
│   │   ├── check_stock.py
│   │   ├── calculate_price.py
│   │   ├── create_quote.py
│   │   └── get_alternatives.py
│   │
│   ├── data/                      # Data layer
│   │   ├── __init__.py
│   │   ├── database.py            # SQLite connection & queries
│   │   ├── vector_store.py        # ChromaDB setup & queries
│   │   └── seed/
│   │       ├── products.json
│   │       ├── price_tiers.json
│   │       ├── stock.json
│   │       └── seed.py            # Script untuk populate DB
│   │
│   ├── api/                       # API routes
│   │   ├── __init__.py
│   │   ├── chat.py                # POST /chat
│   │   ├── session.py             # POST /session, GET /session/{id}
│   │   └── health.py              # GET /health
│   │
│   └── config/
│       ├── __init__.py
│       ├── settings.py            # Environment variables
│       └── constants.py           # App constants
│
├── tests/
│   ├── __init__.py
│   ├── test_tools.py              # Unit tests untuk tools
│   ├── test_agent.py              # Agent integration test
│   └── test_api.py                # API endpoint tests
│
├── requirements.txt
├── .env.example
├── README.md
└── .gitignore
```

## Metrics

| Metrik | Target | Cara Ukur |
|--------|--------|-----------|
| Quote Accuracy | Harga final = harga yang benar (toleransi < 2%) | Unit test: hitung manual vs agent output |
| Product Match | Agent rekomendasikan produk yang relevan | Unit test: assertion product relevance |
| Context Retention | Agent ingat semua constraint sebelumnya | Integration test: multi-turn conversation test |
| Tool Usage | Agent pakai tool yang tepat di step tepat | Logging: track tool calls per turn |
| Edge Case Handling | Semua 6 edge case ditangani dengan benar | Unit test: test case per edge case |
| Conversation Completion | Flow sampai final quote tanpa error | Integration test: end-to-end flow |

## Testing Strategy

1. **Unit tests** — test setiap tool secara individual (output yang benar untuk input tertentu)
2. **Agent tests** — test agent response untuk scenario tertentu (assertions pada tool calls dan response)
3. **Integration tests** — test full flow dari inquiry sampai quote (end-to-end)

## Constraints

- Backend only untuk Phase 1 (frontend Phase 2)
- Groq sebagai LLM provider (GPT OSS model)
- Tidak ada payment/checkout system (eskalasi ke manusia)
- Synthetic data only (tidak scrape dari website asli)
- Single-context layout (CONTEXT.md + docs/adr/ di repo root)
