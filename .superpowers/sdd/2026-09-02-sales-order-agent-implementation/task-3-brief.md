# Task 3: Database Layer (SQLite + ChromaDB + Gemini Embedding)

## Files to Create
- `src/data/database.py`
- `src/data/vector_store.py`
- `src/data/seed/seed.py`
- Update: `src/config/settings.py` (add GOOGLE_API_KEY)

## Prerequisites
- Task 2 completed: seed JSON files exist at `src/data/seed/*.json`
- `src/config/settings.py` exists with `settings` object
- Packages installed: `langchain-google-genai`, `google-generativeai`, `chromadb`

## What to Do

### 0. Update `src/config/settings.py`

Add `GOOGLE_API_KEY` to settings:
```python
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GOOGLE_API_KEY: str = ""
    EMBEDDING_MODEL: str = "gemini-embedding-001"
    DATABASE_PATH: str = "data/app.db"
    CHROMADB_PATH: str = "data/chromadb"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
```

Also update `.env.example` to include:
```
GOOGLE_API_KEY=your_google_api_key_here
EMBEDDING_MODEL=gemini-embedding-001
```

### 1. Create `src/data/database.py`

SQLite database with full CRUD operations. Use `sqlite3` stdlib.

**Tables:**
```sql
CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT NOT NULL, category TEXT NOT NULL, description TEXT, base_price REAL NOT NULL, moq INTEGER NOT NULL DEFAULT 1, lead_time_days INTEGER NOT NULL DEFAULT 5);
CREATE TABLE product_variants (id INTEGER PRIMARY KEY, product_id INTEGER NOT NULL, color TEXT NOT NULL, FOREIGN KEY (product_id) REFERENCES products(id));
CREATE TABLE price_tiers (id INTEGER PRIMARY KEY, product_id INTEGER NOT NULL, min_qty INTEGER NOT NULL, max_qty INTEGER, price_per_unit REAL NOT NULL, FOREIGN KEY (product_id) REFERENCES products(id));
CREATE TABLE stock (id INTEGER PRIMARY KEY, variant_id INTEGER NOT NULL, quantity INTEGER NOT NULL, warehouse_location TEXT NOT NULL, FOREIGN KEY (variant_id) REFERENCES product_variants(id));
CREATE TABLE discounts (id INTEGER PRIMARY KEY, code TEXT UNIQUE NOT NULL, type TEXT NOT NULL, value REAL NOT NULL, min_qty INTEGER, valid_until DATE);
CREATE TABLE sessions (id TEXT PRIMARY KEY, customer_name TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, status TEXT DEFAULT 'active');
CREATE TABLE conversations (id INTEGER PRIMARY KEY, session_id TEXT NOT NULL, role TEXT NOT NULL, content TEXT NOT NULL, tool_calls TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (session_id) REFERENCES sessions(id));
CREATE TABLE quotes (id TEXT PRIMARY KEY, session_id TEXT NOT NULL, items_json TEXT NOT NULL, total_price REAL NOT NULL, valid_until DATE NOT NULL, status TEXT DEFAULT 'pending', FOREIGN KEY (session_id) REFERENCES sessions(id));
```

**Functions to implement:**
- `get_connection()` → sqlite3.Connection
- `init_db()` → creates all tables
- `search_products(query, category=None)` → list[dict]
- `get_product_by_id(product_id)` → Optional[dict]
- `get_product_variants(product_id)` → list[dict]
- `get_price_tier(product_id, quantity)` → Optional[dict]
- `get_stock(variant_id)` → Optional[dict]
- `get_stock_by_product(product_id)` → list[dict] (JOIN with product_variants)
- `get_discount(code)` → Optional[dict] (check valid_until >= today)
- `create_session(session_id, customer_name)` → dict
- `get_session(session_id)` → Optional[dict]
- `save_message(session_id, role, content, tool_calls)` → None
- `get_conversation_history(session_id)` → list[dict]
- `create_quote(quote_id, session_id, items_json, total_price, valid_until)` → dict

### 2. Create `src/data/vector_store.py`

**IMPORTANT: Use Google Gemini Embedding (gemini-embedding-001)**

```python
import chromadb
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from src.config.settings import settings

_client = None
_collection = None
_embedding_fn = None


def get_embeddings():
    """Get Gemini embedding function."""
    global _embedding_fn
    if _embedding_fn is None:
        _embedding_fn = GoogleGenerativeAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
        )
    return _embedding_fn


def get_vector_store():
    """Get ChromaDB collection with Gemini embeddings."""
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=settings.CHROMADB_PATH)
        _collection = _client.get_or_create_collection(
            name="products",
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def index_products(products: list[dict]):
    """Index products using Gemini embeddings."""
    collection = get_vector_store()
    embeddings = get_embeddings()
    
    # Create documents for embedding
    documents = [f"{p['name']} {p['description']} {p['category']}" for p in products]
    
    # Get embeddings from Gemini
    embedding_vectors = embeddings.embed_documents(documents)
    
    collection.upsert(
        ids=[f"product_{p['id']}" for p in products],
        embeddings=embedding_vectors,
        documents=documents,
        metadatas=[{"product_id": p["id"], "category": p["category"], "base_price": p["base_price"]} for p in products],
    )


def search_products_semantic(query: str, n_results: int = 5) -> list[dict]:
    """Search products using Gemini embeddings."""
    collection = get_vector_store()
    embeddings = get_embeddings()
    
    # Embed the query
    query_embedding = embeddings.embed_query(query)
    
    results = collection.query(query_embeddings=[query_embedding], n_results=n_results)
    if not results["metadatas"][0]:
        return []
    return [
        {"product_id": m["product_id"], "category": m["category"], "base_price": m["base_price"], "score": 1 - d}
        for m, d in zip(results["metadatas"][0], results["distances"][0])
    ]
```

### 3. Create `src/data/seed/seed.py`

Script to populate both SQLite and ChromaDB from JSON files.

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
    # Insert products, price_tiers, product_variants, stock, discounts
    # ... (full implementation)
    conn.commit()
    conn.close()

    # Index products in ChromaDB with Gemini embeddings
    index_products(products)
    print(f"Seeded {len(products)} products, {len(price_tiers)} price tiers, {len(stock)} stock entries, {len(discounts)} discounts")

if __name__ == "__main__":
    seed_database()
```

## Verification
1. Create `.env` with `GOOGLE_API_KEY` set (user must provide their own key)
2. Run: `D:\Jeli\myenv\Scripts\python.exe -m src.data.seed.seed`
3. Expected output: "Seeded X products, Y price tiers, Z stock entries, W discounts"

## Report
Write your report to: `.superpowers/sdd/2026-09-02-sales-order-agent-implementation/task-3-report.md`
