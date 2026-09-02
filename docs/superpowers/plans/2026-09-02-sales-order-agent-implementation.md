# Sales Order Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a LangGraph-based Sales Order Agent for PT Lemone with FastAPI backend, Groq LLM, ChromaDB for RAG, and SQLite for structured data.

**Architecture:** ReAct agent pattern using LangGraph. Single agent with 6 tools handling multi-turn sales conversations. FastAPI serves the API, ChromaDB handles product semantic search, SQLite stores structured data (products, stock, quotes, sessions).

**Tech Stack:** Python 3.11+, LangChain, LangGraph, Groq (langchain-groq), FastAPI, ChromaDB, SQLite, Pydantic

## Global Constraints

- Python 3.11+
- LLM provider: Groq (model: llama-3.3-70b-versatile or similar GPT OSS)
- No external database services — SQLite + ChromaDB (in-process)
- No frontend in this plan (Phase 2)
- All monetary values in IDR (Indonesian Rupiah)
- System prompts and user-facing text in Bahasa Indonesia

---

## File Structure

```
src/
├── __init__.py
├── main.py                        # FastAPI app + startup/shutdown
├── config/
│   ├── __init__.py
│   └── settings.py                # Pydantic Settings (env vars)
├── data/
│   ├── __init__.py
│   ├── database.py                # SQLite CRUD operations
│   ├── vector_store.py            # ChromaDB setup + product indexing
│   └── seed/
│       ├── products.json          # 50 synthetic products
│       ├── price_tiers.json       # Tiered pricing per product
│       ├── stock.json             # Stock per variant
│       ├── discounts.json         # Active discounts
│       └── seed.py                # Populate SQLite + ChromaDB
├── tools/
│   ├── __init__.py
│   ├── search_products.py         # Semantic product search
│   ├── get_product_detail.py      # Product specs lookup
│   ├── check_stock.py             # Stock availability check
│   ├── calculate_price.py         # Price calculation with tiers
│   ├── create_quote.py            # Generate quote
│   └── get_alternatives.py        # Alternative product suggestions
├── agents/
│   ├── __init__.py
│   ├── state.py                   # AgentState schema
│   ├── prompts.py                 # System prompts
│   ├── graph.py                   # LangGraph state graph
│   └── nodes.py                   # Node functions (llm, tools, response)
└── api/
    ├── __init__.py
    ├── chat.py                    # POST /chat
    ├── session.py                 # POST /session, GET /session/{id}
    └── health.py                  # GET /health
tests/
├── __init__.py
├── conftest.py                    # Shared fixtures
├── test_tools.py
├── test_agent.py
└── test_api.py
requirements.txt
.env.example
```

---

### Task 1: Project Setup & Configuration

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `src/__init__.py`
- Create: `src/config/__init__.py`
- Create: `src/config/settings.py`
- Create: `.gitignore`

**Interfaces:**
- Produces: `settings` object (Pydantic Settings) with attributes: `GROQ_API_KEY`, `GROQ_MODEL`, `DATABASE_PATH`, `CHROMADB_PATH`, `APP_HOST`, `APP_PORT`

- [ ] **Step 1: Create requirements.txt**

```txt
langchain>=0.3.0
langchain-core>=0.3.0
langchain-groq>=0.2.0
langgraph>=0.2.0
fastapi>=0.115.0
uvicorn>=0.30.0
chromadb>=0.5.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
python-dotenv>=1.0.0
```

- [ ] **Step 2: Create .env.example**

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
DATABASE_PATH=data/app.db
CHROMADB_PATH=data/chromadb
APP_HOST=0.0.0.0
APP_PORT=8000
```

- [ ] **Step 3: Create src/config/settings.py**

```python
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    DATABASE_PATH: str = "data/app.db"
    CHROMADB_PATH: str = "data/chromadb"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
```

- [ ] **Step 4: Create .gitignore**

```gitignore
__pycache__/
*.pyc
.env
data/
.venv/
venv/
*.egg-info/
dist/
build/
.pytest_cache/
```

- [ ] **Step 5: Create empty __init__.py files**

Create empty files:
- `src/__init__.py`
- `src/config/__init__.py`
- `src/data/__init__.py`
- `src/tools/__init__.py`
- `src/agents/__init__.py`
- `src/api/__init__.py`
- `tests/__init__.py`

- [ ] **Step 6: Install dependencies and verify**

Run: `pip install -r requirements.txt`
Expected: All packages install successfully

- [ ] **Step 7: Commit**

```bash
git init
git add requirements.txt .env.example .gitignore src/ tests/
git commit -m "feat: project setup with dependencies and config"
```

---

### Task 2: Seed Data (Products, Pricing, Stock, Discounts)

**Files:**
- Create: `src/data/seed/products.json`
- Create: `src/data/seed/price_tiers.json`
- Create: `src/data/seed/stock.json`
- Create: `src/data/seed/discounts.json`

**Interfaces:**
- Produces: JSON files that will be consumed by seed.py in Task 3

- [ ] **Step 1: Create products.json**

```json
[
  {
    "id": 1,
    "name": "Polo Premium Cotton",
    "category": "Polo",
    "description": "Polo shirt premium dengan bahan cotton combed 30s, nyaman dan awet. Cocok untuk seragam kantor.",
    "base_price": 85000,
    "moq": 100,
    "lead_time_days": 5
  },
  {
    "id": 2,
    "name": "Polo Basic",
    "category": "Polo",
    "description": "Polo shirt standar dengan bahan cotton combet 20s. Harga terjangkau untuk order volume besar.",
    "base_price": 65000,
    "moq": 100,
    "lead_time_days": 5
  },
  {
    "id": 3,
    "name": "Kaos Polos Premium",
    "category": "Kaos",
    "description": "Kaos polos premium cotton combed 30s. Tersedia dalam berbagai warna. Cocok untuk event dan promosi.",
    "base_price": 55000,
    "moq": 50,
    "lead_time_days": 3
  },
  {
    "id": 4,
    "name": "Kaos Polos Standar",
    "category": "Kaos",
    "description": "Kaos polos standar cotton 20s. Harga ekonomis untuk order grosir.",
    "base_price": 35000,
    "moq": 50,
    "lead_time_days": 3
  },
  {
    "id": 5,
    "name": "Jaket Bomber Kulit",
    "category": "Jaket",
    "description": "Jaket bomber bahan kulit sintetis premium. Desain modern, cocok untuk fashion casual.",
    "base_price": 250000,
    "moq": 25,
    "lead_time_days": 7
  },
  {
    "id": 6,
    "name": "Jaket Hoodie Premium",
    "category": "Jaket",
    "description": "Hoodie premium dengan bahan fleece tebal. Nyaman dan hangat, cocok untuk cuaca dingin.",
    "base_price": 180000,
    "moq": 50,
    "lead_time_days": 7
  },
  {
    "id": 7,
    "name": "Seragam Kantor Putih",
    "category": "Seragam",
    "description": "Kemeja seragam kantor warna putih, bahan Oxford. Formal dan profesional.",
    "base_price": 120000,
    "moq": 30,
    "lead_time_days": 5
  },
  {
    "id": 8,
    "name": "Seragam Kerja Navy",
    "category": "Seragam",
    "description": "Kemeja seragam kerja warna navy, bahan TC. Cocok untuk lingkungan kerja kasual.",
    "base_price": 95000,
    "moq": 30,
    "lead_time_days": 5
  },
  {
    "id": 9,
    "name": "Celana Chino Premium",
    "category": "Celana",
    "description": "Celana chino bahan twill premium. Nyaman dan stylish, cocok untuk seragam kasual.",
    "base_price": 145000,
    "moq": 30,
    "lead_time_days": 7
  },
  {
    "id": 10,
    "name": "Celana Jogger Kantor",
    "category": "Celana",
    "description": "Celana jogger dengan desain formal. Bahan cotton stretch, nyaman untuk aktivitas kantor.",
    "base_price": 130000,
    "moq": 30,
    "lead_time_days": 7
  },
  {
    "id": 11,
    "name": "Tas Selempang Premium",
    "category": "Aksesoris",
    "description": "Tas selempang bahan canvas premium. Cocok untuk aksesoris seragam atau merchandise.",
    "base_price": 85000,
    "moq": 50,
    "lead_time_days": 5
  },
  {
    "id": 12,
    "name": "Topi Baseball Custom",
    "category": "Aksesoris",
    "description": "Topi baseball custom dengan bordir logo. Cocok untuk merchandise perusahaan.",
    "base_price": 45000,
    "moq": 100,
    "lead_time_days": 5
  }
]
```

- [ ] **Step 2: Create price_tiers.json**

```json
[
  {"product_id": 1, "min_qty": 1, "max_qty": 99, "price_per_unit": 85000},
  {"product_id": 1, "min_qty": 100, "max_qty": 299, "price_per_unit": 80000},
  {"product_id": 1, "min_qty": 300, "max_qty": 499, "price_per_unit": 75000},
  {"product_id": 1, "min_qty": 500, "max_qty": null, "price_per_unit": 70000},
  {"product_id": 2, "min_qty": 1, "max_qty": 99, "price_per_unit": 65000},
  {"product_id": 2, "min_qty": 100, "max_qty": 299, "price_per_unit": 60000},
  {"product_id": 2, "min_qty": 300, "max_qty": 499, "price_per_unit": 55000},
  {"product_id": 2, "min_qty": 500, "max_qty": null, "price_per_unit": 50000},
  {"product_id": 3, "min_qty": 1, "max_qty": 99, "price_per_unit": 55000},
  {"product_id": 3, "min_qty": 100, "max_qty": 299, "price_per_unit": 50000},
  {"product_id": 3, "min_qty": 300, "max_qty": 499, "price_per_unit": 45000},
  {"product_id": 3, "min_qty": 500, "max_qty": null, "price_per_unit": 40000},
  {"product_id": 4, "min_qty": 1, "max_qty": 99, "price_per_unit": 35000},
  {"product_id": 4, "min_qty": 100, "max_qty": 299, "price_per_unit": 32000},
  {"product_id": 4, "min_qty": 300, "max_qty": 499, "price_per_unit": 29000},
  {"product_id": 4, "min_qty": 500, "max_qty": null, "price_per_unit": 26000},
  {"product_id": 5, "min_qty": 1, "max_qty": 24, "price_per_unit": 250000},
  {"product_id": 5, "min_qty": 25, "max_qty": 99, "price_per_unit": 230000},
  {"product_id": 5, "min_qty": 100, "max_qty": null, "price_per_unit": 210000},
  {"product_id": 6, "min_qty": 1, "max_qty": 49, "price_per_unit": 180000},
  {"product_id": 6, "min_qty": 50, "max_qty": 199, "price_per_unit": 165000},
  {"product_id": 6, "min_qty": 200, "max_qty": null, "price_per_unit": 150000},
  {"product_id": 7, "min_qty": 1, "max_qty": 29, "price_per_unit": 120000},
  {"product_id": 7, "min_qty": 30, "max_qty": 99, "price_per_unit": 110000},
  {"product_id": 7, "min_qty": 100, "max_qty": null, "price_per_unit": 100000},
  {"product_id": 8, "min_qty": 1, "max_qty": 29, "price_per_unit": 95000},
  {"product_id": 8, "min_qty": 30, "max_qty": 99, "price_per_unit": 88000},
  {"product_id": 8, "min_qty": 100, "max_qty": null, "price_per_unit": 80000},
  {"product_id": 9, "min_qty": 1, "max_qty": 29, "price_per_unit": 145000},
  {"product_id": 9, "min_qty": 30, "max_qty": 99, "price_per_unit": 135000},
  {"product_id": 9, "min_qty": 100, "max_qty": null, "price_per_unit": 125000},
  {"product_id": 10, "min_qty": 1, "max_qty": 29, "price_per_unit": 130000},
  {"product_id": 10, "min_qty": 30, "max_qty": 99, "price_per_unit": 120000},
  {"product_id": 10, "min_qty": 100, "max_qty": null, "price_per_unit": 110000},
  {"product_id": 11, "min_qty": 1, "max_qty": 49, "price_per_unit": 85000},
  {"product_id": 11, "min_qty": 50, "max_qty": null, "price_per_unit": 75000},
  {"product_id": 12, "min_qty": 1, "max_qty": 99, "price_per_unit": 45000},
  {"product_id": 12, "min_qty": 100, "max_qty": null, "price_per_unit": 38000}
]
```

- [ ] **Step 3: Create stock.json**

```json
[
  {"variant_id": 1, "product_id": 1, "color": "Hitam", "quantity": 1200, "warehouse": "Tanah Abang"},
  {"variant_id": 2, "product_id": 1, "color": "Navy", "quantity": 950, "warehouse": "Tanah Abang"},
  {"variant_id": 3, "product_id": 1, "color": "Putih", "quantity": 800, "warehouse": "Tanah Abang"},
  {"variant_id": 4, "product_id": 1, "color": "Abu-abu", "quantity": 600, "warehouse": "Tanah Abang"},
  {"variant_id": 5, "product_id": 2, "color": "Hitam", "quantity": 800, "warehouse": "Tanah Abang"},
  {"variant_id": 6, "product_id": 2, "color": "Navy", "quantity": 1500, "warehouse": "Tanah Abang"},
  {"variant_id": 7, "product_id": 2, "color": "Putih", "quantity": 1200, "warehouse": "Tanah Abang"},
  {"variant_id": 8, "product_id": 3, "color": "Hitam", "quantity": 2000, "warehouse": "Tanah Abang"},
  {"variant_id": 9, "product_id": 3, "color": "Navy", "quantity": 1800, "warehouse": "Tanah Abang"},
  {"variant_id": 10, "product_id": 3, "color": "Putih", "quantity": 1500, "warehouse": "Tanah Abang"},
  {"variant_id": 11, "product_id": 3, "color": "Merah", "quantity": 1200, "warehouse": "Tanah Abang"},
  {"variant_id": 12, "product_id": 4, "color": "Hitam", "quantity": 3000, "warehouse": "Tanah Abang"},
  {"variant_id": 13, "product_id": 4, "color": "Putih", "quantity": 2500, "warehouse": "Tanah Abang"},
  {"variant_id": 14, "product_id": 5, "color": "Hitam", "quantity": 300, "warehouse": "Tanah Abang"},
  {"variant_id": 15, "product_id": 5, "color": "Coklat", "quantity": 200, "warehouse": "Tanah Abang"},
  {"variant_id": 16, "product_id": 6, "color": "Hitam", "quantity": 500, "warehouse": "Tanah Abang"},
  {"variant_id": 17, "product_id": 6, "color": "Abu-abu", "quantity": 400, "warehouse": "Tanah Abang"},
  {"variant_id": 18, "product_id": 6, "color": "Navy", "quantity": 350, "warehouse": "Tanah Abang"},
  {"variant_id": 19, "product_id": 7, "color": "Putih", "quantity": 600, "warehouse": "Tanah Abang"},
  {"variant_id": 20, "product_id": 8, "color": "Navy", "quantity": 450, "warehouse": "Tanah Abang"},
  {"variant_id": 21, "product_id": 9, "color": "Khaki", "quantity": 400, "warehouse": "Tanah Abang"},
  {"variant_id": 22, "product_id": 9, "color": "Hitam", "quantity": 350, "warehouse": "Tanah Abang"},
  {"variant_id": 23, "product_id": 10, "color": "Hitam", "quantity": 500, "warehouse": "Tanah Abang"},
  {"variant_id": 24, "product_id": 10, "color": "Navy", "quantity": 300, "warehouse": "Tanah Abang"},
  {"variant_id": 25, "product_id": 11, "color": "Hitam", "quantity": 700, "warehouse": "Tanah Abang"},
  {"variant_id": 26, "product_id": 12, "color": "Hitam", "quantity": 1000, "warehouse": "Tanah Abang"},
  {"variant_id": 27, "product_id": 12, "color": "Navy", "quantity": 800, "warehouse": "Tanah Abang"}
]
```

- [ ] **Step 4: Create discounts.json**

```json
[
  {"code": "NEWCUSTOMER10", "type": "percentage", "value": 10, "min_qty": 100, "valid_until": "2026-12-31"},
  {"code": "BULK500", "type": "percentage", "value": 5, "min_qty": 500, "valid_until": "2026-12-31"},
  {"code": "HEMAT20K", "type": "fixed", "value": 20000, "min_qty": 200, "valid_until": "2026-10-31"},
  {"code": "MERDEKA15", "type": "percentage", "value": 15, "min_qty": 100, "valid_until": "2026-08-31"},
  {"code": "FIRSTORDER", "type": "percentage", "value": 8, "min_qty": 50, "valid_until": "2026-12-31"}
]
```

- [ ] **Step 5: Commit**

```bash
git add src/data/seed/
git commit -m "feat: add synthetic seed data for PT Lemone products"
```

---

### Task 3: Database Layer (SQLite + ChromaDB)

**Files:**
- Create: `src/data/database.py`
- Create: `src/data/vector_store.py`
- Create: `src/data/seed/seed.py`

**Interfaces:**
- Consumes: JSON seed files from Task 2
- Produces: `db` object with CRUD methods, `vector_store` with search methods

- [ ] **Step 1: Create database.py with SQLite schema and CRUD**

```python
import sqlite3
from pathlib import Path
from typing import Optional
from src.config.settings import settings


def get_connection() -> sqlite3.Connection:
    Path(settings.DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    conn.executescript("""
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
    conn.close()


def search_products(query: str, category: Optional[str] = None) -> list[dict]:
    conn = get_connection()
    if category:
        rows = conn.execute(
            "SELECT * FROM products WHERE category = ?", (category,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM products").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_product_by_id(product_id: int) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_product_variants(product_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM product_variants WHERE product_id = ?", (product_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_price_tier(product_id: int, quantity: int) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute(
        """SELECT * FROM price_tiers
           WHERE product_id = ? AND min_qty <= ? AND (max_qty IS NULL OR max_qty >= ?)
           ORDER BY min_qty DESC LIMIT 1""",
        (product_id, quantity, quantity),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_stock(variant_id: int) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM stock WHERE variant_id = ?", (variant_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_stock_by_product(product_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT s.*, pv.color FROM stock s
           JOIN product_variants pv ON s.variant_id = pv.id
           WHERE pv.product_id = ?""",
        (product_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_discount(code: str) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM discounts WHERE code = ? AND valid_until >= date('now')",
        (code,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def create_session(session_id: str, customer_name: str = "") -> dict:
    conn = get_connection()
    conn.execute(
        "INSERT INTO sessions (id, customer_name) VALUES (?, ?)",
        (session_id, customer_name),
    )
    conn.commit()
    conn.close()
    return {"id": session_id, "customer_name": customer_name, "status": "active"}


def get_session(session_id: str) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def save_message(session_id: str, role: str, content: str, tool_calls: str = "") -> None:
    conn = get_connection()
    conn.execute(
        "INSERT INTO conversations (session_id, role, content, tool_calls) VALUES (?, ?, ?, ?)",
        (session_id, role, content, tool_calls),
    )
    conn.commit()
    conn.close()


def get_conversation_history(session_id: str) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM conversations WHERE session_id = ? ORDER BY timestamp",
        (session_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_quote(quote_id: str, session_id: str, items_json: str, total_price: float, valid_until: str) -> dict:
    conn = get_connection()
    conn.execute(
        "INSERT INTO quotes (id, session_id, items_json, total_price, valid_until) VALUES (?, ?, ?, ?, ?)",
        (quote_id, session_id, items_json, total_price, valid_until),
    )
    conn.commit()
    conn.close()
    return {"quote_id": quote_id, "total_price": total_price, "valid_until": valid_until}
```

- [ ] **Step 2: Create vector_store.py for ChromaDB product search**

```python
import chromadb
from src.config.settings import settings


_client = None
_collection = None


def get_vector_store():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=settings.CHROMADB_PATH)
        _collection = _client.get_or_create_collection(
            name="products",
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def index_products(products: list[dict]):
    collection = get_vector_store()
    collection.upsert(
        ids=[f"product_{p['id']}" for p in products],
        documents=[f"{p['name']} {p['description']} {p['category']}" for p in products],
        metadatas=[{"product_id": p["id"], "category": p["category"], "base_price": p["base_price"]} for p in products],
    )


def search_products_semantic(query: str, n_results: int = 5) -> list[dict]:
    collection = get_vector_store()
    results = collection.query(query_texts=[query], n_results=n_results)
    if not results["metadatas"][0]:
        return []
    return [
        {"product_id": m["product_id"], "category": m["category"], "base_price": m["base_price"], "score": 1 - d}
        for m, d in zip(results["metadatas"][0], results["distances"][0])
    ]
```

- [ ] **Step 3: Create seed.py to populate both databases**

```python
import json
from pathlib import Path
from src.data.database import init_db, get_connection
from src.data.vector_store import index_products
from src.config.settings import settings


SEED_DIR = Path(__file__).parent


def load_json(filename: str) -> list[dict]:
    with open(SEED_DIR / filename) as f:
        return json.load(f)


def seed_database():
    init_db()

    products = load_json("products.json")
    price_tiers = load_json("price_tiers.json")
    stock = load_json("stock.json")
    discounts = load_json("discounts.json")

    conn = get_connection()

    for p in products:
        conn.execute(
            "INSERT OR REPLACE INTO products (id, name, category, description, base_price, moq, lead_time_days) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (p["id"], p["name"], p["category"], p["description"], p["base_price"], p["moq"], p["lead_time_days"]),
        )

    for pt in price_tiers:
        conn.execute(
            "INSERT OR REPLACE INTO price_tiers (product_id, min_qty, max_qty, price_per_unit) VALUES (?, ?, ?, ?)",
            (pt["product_id"], pt["min_qty"], pt["max_qty"], pt["price_per_unit"]),
        )

    for s in stock:
        conn.execute(
            "INSERT OR REPLACE INTO product_variants (id, product_id, color) VALUES (?, ?, ?)",
            (s["variant_id"], s["product_id"], s["color"]),
        )
        conn.execute(
            "INSERT OR REPLACE INTO stock (variant_id, quantity, warehouse_location) VALUES (?, ?, ?)",
            (s["variant_id"], s["quantity"], s["warehouse"]),
        )

    for d in discounts:
        conn.execute(
            "INSERT OR REPLACE INTO discounts (code, type, value, min_qty, valid_until) VALUES (?, ?, ?, ?, ?)",
            (d["code"], d["type"], d["value"], d["min_qty"], d["valid_until"]),
        )

    conn.commit()
    conn.close()

    # Index products in ChromaDB
    index_products(products)

    print(f"Seeded {len(products)} products, {len(price_tiers)} price tiers, {len(stock)} stock entries, {len(discounts)} discounts")


if __name__ == "__main__":
    seed_database()
```

- [ ] **Step 4: Run seed script to verify**

Run: `python -m src.data.seed.seed`
Expected: "Seeded 12 products, 39 price tiers, 27 stock entries, 5 discounts"

- [ ] **Step 5: Commit**

```bash
git add src/data/database.py src/data/vector_store.py src/data/seed/seed.py
git commit -m "feat: SQLite database layer, ChromaDB vector store, and seed script"
```

---

### Task 4: Agent Tools (6 Tools)

**Files:**
- Create: `src/tools/__init__.py`
- Create: `src/tools/search_products.py`
- Create: `src/tools/get_product_detail.py`
- Create: `src/tools/check_stock.py`
- Create: `src/tools/calculate_price.py`
- Create: `src/tools/create_quote.py`
- Create: `src/tools/get_alternatives.py`
- Create: `tests/test_tools.py`

**Interfaces:**
- Consumes: database functions from Task 3, vector_store from Task 3
- Produces: 6 LangChain `@tool` decorated functions

- [ ] **Step 1: Write test_tools.py**

```python
import pytest
from src.tools.search_products import search_products_tool
from src.tools.get_product_detail import get_product_detail_tool
from src.tools.check_stock import check_stock_tool
from src.tools.calculate_price import calculate_price_tool
from src.tools.create_quote import create_quote_tool
from src.tools.get_alternatives import get_alternatives_tool


class TestSearchProducts:
    def test_returns_results_for_valid_query(self):
        results = search_products_tool("polo")
        assert isinstance(results, list)
        assert len(results) > 0
        assert "name" in results[0]

    def test_returns_empty_for_no_match(self):
        results = search_products_tool("jas formal pria")
        assert isinstance(results, list)


class TestGetProductDetail:
    def test_returns_detail_for_valid_id(self):
        result = get_product_detail_tool(1)
        assert result is not None
        assert result["name"] == "Polo Premium Cotton"
        assert "moq" in result

    def test_returns_none_for_invalid_id(self):
        result = get_product_detail_tool(9999)
        assert result is None


class TestCheckStock:
    def test_returns_stock_info(self):
        result = check_stock_tool(1, 100)
        assert "available" in result
        assert "stock" in result

    def test_detects_insufficient_stock(self):
        result = check_stock_tool(1, 99999)
        assert result["available"] is False


class TestCalculatePrice:
    def test_calculates_correct_tier(self):
        result = calculate_price_tool(1, 500)
        assert result["price_per_unit"] == 70000
        assert result["subtotal"] == 35000000

    def test_applies_discount(self):
        result = calculate_price_tool(1, 500, "BULK500")
        assert result["discount_amount"] > 0
        assert result["total"] < result["subtotal"]


class TestCreateQuote:
    def test_creates_quote(self):
        result = create_quote_tool(
            [{"product_id": 1, "quantity": 100, "color": "Hitam"}],
            {"customer_name": "Test Corp"}
        )
        assert "quote_id" in result
        assert result["total_price"] > 0


class TestGetAlternatives:
    def test_returns_alternatives_for_budget(self):
        results = get_alternatives_tool(5, "budget")
        assert isinstance(results, list)
        assert len(results) > 0

    def test_returns_alternatives_for_stock(self):
        results = get_alternatives_tool(1, "stock")
        assert isinstance(results, list)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_tools.py -v`
Expected: FAIL (tools not implemented yet)

- [ ] **Step 3: Implement all 6 tools**

Create `src/tools/search_products.py`:
```python
from langchain_core.tools import tool
from src.data.vector_store import search_products_semantic
from src.data.database import search_products as db_search


@tool
def search_products(query: str, category: str = "") -> list[dict]:
    """Cari produk fashion grosir berdasarkan query. Gunakan untuk mencari produk berdasarkan nama, kategori, atau deskripsi."""
    # Try semantic search first
    results = search_products_semantic(query, n_results=5)
    if results:
        return results
    # Fallback to DB search
    return db_search(query, category if category else None)
```

Create `src/tools/get_product_detail.py`:
```python
from langchain_core.tools import tool
from src.data.database import get_product_by_id, get_product_variants


@tool
def get_product_detail(product_id: int) -> dict | None:
    """Ambil spesifikasi lengkap produk berdasarkan product_id. Termasuk nama, kategori, deskripsi, bahan, MOQ, dan lead time."""
    product = get_product_by_id(product_id)
    if not product:
        return None
    variants = get_product_variants(product_id)
    product["variants"] = [{"id": v["id"], "color": v["color"]} for v in variants]
    return product
```

Create `src/tools/check_stock.py`:
```python
from langchain_core.tools import tool
from src.data.database import get_stock_by_product


@tool
def check_stock(product_id: int, quantity: int) -> dict:
    """Cek ketersediaan stok produk. Masukkan product_id dan jumlah yang dibutuhkan."""
    variants = get_stock_by_product(product_id)
    if not variants:
        return {"available": False, "stock": 0, "message": "Produk tidak ditemukan"}

    total_stock = sum(v["quantity"] for v in variants)
    available = total_stock >= quantity

    return {
        "available": available,
        "total_stock": total_stock,
        "variants": [{"color": v["color"], "quantity": v["quantity"], "warehouse": v["warehouse_location"]} for v in variants],
        "message": f"Stok mencukupi ({total_stock} tersedia)" if available else f"Stok tidak cukup. Tersedia: {total_stock}, dibutuhkan: {quantity}"
    }
```

Create `src/tools/calculate_price.py`:
```python
from langchain_core.tools import tool
from src.data.database import get_price_tier, get_discount


@tool
def calculate_price(product_id: int, quantity: int, discount_code: str = "") -> dict:
    """Hitung harga berdasarkan jumlah pesanan, tier harga, dan diskon yang berlaku."""
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
            if discount["type"] == "percentage":
                discount_amount = subtotal * (discount["value"] / 100)
            else:
                discount_amount = min(discount["value"], subtotal)
            discount_info = {"code": discount["code"], "type": discount["type"], "value": discount["value"]}

    total = subtotal - discount_amount

    return {
        "product_id": product_id,
        "quantity": quantity,
        "price_per_unit": price_per_unit,
        "subtotal": subtotal,
        "discount": discount_info,
        "discount_amount": discount_amount,
        "total": total,
        "tier": f"{tier['min_qty']}-{tier['max_qty'] or '∞'} pcs"
    }
```

Create `src/tools/create_quote.py`:
```python
import json
from datetime import datetime, timedelta
from langchain_core.tools import tool
from src.data.database import create_quote as db_create_quote, get_price_tier


@tool
def create_quote(items: list[dict], customer_info: dict) -> dict:
    """Buat penawaran harga final. Masukkan list item [{product_id, quantity, color}] dan customer_info {customer_name, phone, email}."""
    quote_items = []
    total_price = 0

    for item in items:
        tier = get_price_tier(item["product_id"], item["quantity"])
        if tier:
            item_total = tier["price_per_unit"] * item["quantity"]
            quote_items.append({
                **item,
                "price_per_unit": tier["price_per_unit"],
                "subtotal": item_total,
            })
            total_price += item_total

    quote_id = f"Q-{datetime.now().strftime('%Y-%m-%d')}-{datetime.now().strftime('%H%M%S')}"
    valid_until = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

    result = db_create_quote(
        quote_id=quote_id,
        session_id="",
        items_json=json.dumps(quote_items),
        total_price=total_price,
        valid_until=valid_until,
    )

    return {
        "quote_id": quote_id,
        "items": quote_items,
        "total_price": total_price,
        "formatted_total": f"Rp {total_price:,.0f}".replace(",", "."),
        "valid_until": valid_until,
        "customer_info": customer_info,
    }
```

Create `src/tools/get_alternatives.py`:
```python
from langchain_core.tools import tool
from src.data.database import get_product_by_id, search_products


@tool
def get_alternatives(product_id: int, reason: str) -> list[dict]:
    """Cari produk alternatif. reason: 'stock' (stok tidak cukup) atau 'budget' (budget tidak sesuai)."""
    original = get_product_by_id(product_id)
    if not original:
        return []

    category = original["category"]
    base_price = original["base_price"]

    # Search products in same category
    candidates = search_products("", category)
    alternatives = []

    for c in candidates:
        if c["id"] == product_id:
            continue

        price_diff = c["base_price"] - base_price
        price_pct = (price_diff / base_price) * 100 if base_price else 0

        alternatives.append({
            "product_id": c["id"],
            "name": c["name"],
            "category": c["category"],
            "base_price": c["base_price"],
            "price_diff": price_diff,
            "price_diff_pct": f"{price_pct:+.0f}%",
            "reason": reason,
        })

    # Sort by relevance to reason
    if reason == "budget":
        alternatives.sort(key=lambda x: x["base_price"])
    else:
        alternatives.sort(key=lambda x: x["base_price"], reverse=True)

    return alternatives[:3]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_tools.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/tools/ tests/test_tools.py
git commit -m "feat: implement 6 agent tools with unit tests"
```

---

### Task 5: LangGraph Agent (State, Prompts, Graph, Nodes)

**Files:**
- Create: `src/agents/state.py`
- Create: `src/agents/prompts.py`
- Create: `src/agents/nodes.py`
- Create: `src/agents/graph.py`
- Create: `tests/test_agent.py`

**Interfaces:**
- Consumes: 6 tools from Task 4, settings from Task 1
- Produces: `sales_agent` compiled graph ready for invocation

- [ ] **Step 1: Write test_agent.py**

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
        # Agent should have used search_products tool
        last_message = result["messages"][-1]
        assert last_message.content is not None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_agent.py -v`
Expected: FAIL (agent not implemented)

- [ ] **Step 3: Create state.py**

```python
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    session_id: str
    context: dict
```

- [ ] **Step 4: Create prompts.py**

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

- [ ] **Step 5: Create nodes.py**

```python
from langchain_core.messages import HumanMessage, AIMessage
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
    messages = state["messages"]
    if not any(isinstance(m, HumanMessage) for m in messages):
        messages = [HumanMessage(content=SALES_AGENT_PROMPT)] + list(messages)
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

- [ ] **Step 6: Create graph.py**

```python
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
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

- [ ] **Step 7: Run tests to verify they pass**

Run: `pytest tests/test_agent.py -v`
Expected: All PASS

- [ ] **Step 8: Commit**

```bash
git add src/agents/ tests/test_agent.py
git commit -m "feat: LangGraph sales agent with ReAct pattern"
```

---

### Task 6: FastAPI Endpoints

**Files:**
- Create: `src/api/health.py`
- Create: `src/api/session.py`
- Create: `src/api/chat.py`
- Create: `src/main.py`
- Create: `tests/test_api.py`

**Interfaces:**
- Consumes: agent from Task 5, database from Task 3
- Produces: FastAPI app with 3 endpoint groups

- [ ] **Step 1: Write test_api.py**

```python
import pytest
from fastapi.testclient import TestClient
from src.main import app


client = TestClient(app)


class TestHealth:
    def test_health_endpoint(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


class TestSession:
    def test_create_session(self):
        response = client.post("/session", json={"customer_name": "Test User"})
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data

    def test_get_session(self):
        create_resp = client.post("/session", json={"customer_name": "Test"})
        session_id = create_resp.json()["session_id"]
        response = client.get(f"/session/{session_id}")
        assert response.status_code == 200


class TestChat:
    def test_chat_without_session(self):
        response = client.post("/chat", json={"message": "Halo"})
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "session_id" in data

    def test_chat_with_session(self):
        create_resp = client.post("/session", json={"customer_name": "Test"})
        session_id = create_resp.json()["session_id"]
        response = client.post("/chat", json={"message": "Cari kaos polo", "session_id": session_id})
        assert response.status_code == 200
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_api.py -v`
Expected: FAIL (endpoints not implemented)

- [ ] **Step 3: Create health.py**

```python
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "sales-order-agent"}
```

- [ ] **Step 4: Create session.py**

```python
import uuid
from fastapi import APIRouter
from pydantic import BaseModel
from src.data.database import create_session, get_session

router = APIRouter()


class CreateSessionRequest(BaseModel):
    customer_name: str = ""


@router.post("/session")
async def create_session_endpoint(req: CreateSessionRequest):
    session_id = str(uuid.uuid4())
    session = create_session(session_id, req.customer_name)
    return {"session_id": session_id, "status": session["status"]}


@router.get("/session/{session_id}")
async def get_session_endpoint(session_id: str):
    session = get_session(session_id)
    if not session:
        return {"error": "Session not found"}, 404
    return session
```

- [ ] **Step 5: Create chat.py**

```python
import uuid
from fastapi import APIRouter
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage
from src.agents.graph import create_sales_agent
from src.data.database import create_session, get_conversation_history, save_message

router = APIRouter()
agent = create_sales_agent()


class ChatRequest(BaseModel):
    message: str
    session_id: str = ""
    customer_name: str = ""


@router.post("/chat")
async def chat_endpoint(req: ChatRequest):
    session_id = req.session_id
    if not session_id:
        session_id = str(uuid.uuid4())
        create_session(session_id, req.customer_name)

    # Build message history
    history = get_conversation_history(session_id)
    messages = []
    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=req.message))

    # Run agent
    result = agent.invoke({
        "messages": messages,
        "session_id": session_id,
        "context": {},
    })

    # Save conversation
    save_message(session_id, "user", req.message)
    response_content = result["messages"][-1].content
    save_message(session_id, "assistant", response_content)

    return {
        "response": response_content,
        "session_id": session_id,
    }
```

- [ ] **Step 6: Create main.py**

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.data.database import init_db
from src.api.health import router as health_router
from src.api.session import router as session_router
from src.api.chat import router as chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Sales Order Agent - PT Lemone",
    description="AI Agent untuk membantu proses order fashion grosir B2B",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(session_router)
app.include_router(chat_router)


if __name__ == "__main__":
    import uvicorn
    from src.config.settings import settings
    uvicorn.run("src.main:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=True)
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `pytest tests/test_api.py -v`
Expected: All PASS

- [ ] **Step 8: Commit**

```bash
git add src/api/ src/main.py tests/test_api.py
git commit -m "feat: FastAPI endpoints for chat, session, and health"
```

---

### Task 7: Integration Test & README

**Files:**
- Create: `tests/test_integration.py`
- Create: `README.md`

**Interfaces:**
- Consumes: all previous tasks
- Produces: end-to-end test, documentation

- [ ] **Step 1: Create test_integration.py**

```python
import pytest
from fastapi.testclient import TestClient
from src.main import app


client = TestClient(app)


class TestFullFlow:
    def test_inquiry_to_quote_flow(self):
        # Turn 1: Inquiry
        resp1 = client.post("/chat", json={
            "message": "Saya butuh 500 kaos polo hitam untuk seragam karyawan",
            "customer_name": "Budi Santoso"
        })
        assert resp1.status_code == 200
        data1 = resp1.json()
        session_id = data1["session_id"]
        assert "polo" in data1["response"].lower() or "kaos" in data1["response"].lower()

        # Turn 2: Specify product
        resp2 = client.post("/chat", json={
            "message": "Yang Premium, bisa warna navy?",
            "session_id": session_id
        })
        assert resp2.status_code == 200
        assert "navy" in resp2["response"].lower() or "premium" in resp2["response"].lower()

        # Turn 3: Ask for quote
        resp3 = client.post("/chat", json={
            "message": "Buatkan penawaran untuk 500 pcs navy",
            "session_id": session_id
        })
        assert resp3.status_code == 200
        assert "rp" in resp3["response"].lower() or "penawaran" in resp3["response"].lower()


class TestEdgeCases:
    def test_unknown_product(self):
        resp = client.post("/chat", json={
            "message": "Saya cari jas formal pria",
            "customer_name": "Test"
        })
        assert resp.status_code == 200
        # Should gracefully handle no results
        assert resp.json()["response"] is not None

    def test_budget_too_low(self):
        resp = client.post("/chat", json={
            "message": "Saya mau 500 kaos polo, budget cuma 10 juta",
            "customer_name": "Test"
        })
        assert resp.status_code == 200
        assert resp.json()["response"] is not None
```

- [ ] **Step 2: Run integration test**

Run: `pytest tests/test_integration.py -v`
Expected: All PASS

- [ ] **Step 3: Create README.md**

```markdown
# Sales Order Agent — PT Lemone Surya Indonesia

AI Agent untuk membantu proses order fashion grosir B2B. Multi-turn conversation dengan 6 tools untuk product search, stock checking, price calculation, dan quote generation.

## Tech Stack

- **Agent:** LangChain + LangGraph (ReAct pattern)
- **LLM:** Groq (llama-3.3-70b-versatile)
- **Backend:** FastAPI
- **Vector DB:** ChromaDB
- **Database:** SQLite

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your GROQ_API_KEY

# Seed database
python -m src.data.seed.seed

# Run server
python -m src.main
```

Server berjalan di `http://localhost:8000`

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/session` | Buat session baru |
| GET | `/session/{id}` | Get session info |
| POST | `/chat` | Kirim pesan ke agent |

## Contoh Percakapan

```
User: Saya butuh 500 kaos polo hitam untuk seragam karyawan
Agent: Saya temukan 2 opsi:
       1. Polo Premium Cotton - stok: 1200 ✓
       2. Polo Basic - stok: 800 ✓
       Mau saya buatkan penawaran untuk yang mana?

User: Yang Premium. Tapi bisa warna navy?
Agent: Polo Premium tersedia dalam warna:
       - Hitam (stok: 1200) ✓
       - Navy (stok: 950) ✓
       Untuk 500 pcs navy, stok aman. Mau lanjut?

User: Oke, buatkan penawaran 500 pcs navy
Agent: Penawaran Q-2026-09-02:
       - 500 x Polo Premium Navy @ Rp 70.000
       - Subtotal: Rp 35.000.000
       - Berlaku 7 hari
```

## Testing

```bash
pytest tests/ -v
```

## Project Structure

See [design spec](docs/superpowers/specs/2026-09-02-sales-order-agent-design.md) for full architecture details.
```

- [ ] **Step 4: Final commit**

```bash
git add tests/test_integration.py README.md
git commit -m "feat: integration tests and README documentation"
```

- [ ] **Step 5: Run full test suite**

Run: `pytest tests/ -v`
Expected: All PASS

- [ ] **Step 6: Final verification**

Run: `python -m src.main`
Open: `http://localhost:8000/docs` (FastAPI auto-docs)
Test: Send chat message via Swagger UI
Expected: Agent responds with product recommendations
