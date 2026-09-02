# Task 3 Report: Database Layer (SQLite + ChromaDB + Gemini Embedding)

**Status:** ✅ Complete

**Date:** 2026-09-02

## Files Created/Modified

| File | Status |
|------|--------|
| `src/config/settings.py` | Modified — added `GOOGLE_API_KEY`, `EMBEDDING_MODEL`, `extra: "ignore"` |
| `.env.example` | Modified — added `GOOGLE_API_KEY`, `EMBEDDING_MODEL` |
| `src/data/database.py` | Created — full SQLite CRUD (16 functions) |
| `src/data/vector_store.py` | Created — ChromaDB + Gemini embeddings |
| `src/data/seed/seed.py` | Created — seeds both SQLite and ChromaDB from JSON |

## SQLite Tables

- `products`, `product_variants`, `price_tiers`, `stock`, `discounts` — product catalog
- `sessions`, `conversations`, `quotes` — chat/ordering state

## Database Functions (database.py)

`get_connection`, `init_db`, `search_products`, `get_product_by_id`, `get_product_variants`, `get_price_tier`, `get_stock`, `get_stock_by_product`, `get_discount`, `create_session`, `get_session`, `save_message`, `get_conversation_history`, `create_quote`

## Vector Store (vector_store.py)

- Uses `GoogleGenerativeAIEmbeddings` with `gemini-embedding-001`
- `chromadb.PersistentClient` for persistent storage
- `index_products()` — batch embeds via `embed_documents()`
- `search_products_semantic()` — query via `embed_query()`, cosine similarity

## Seed Script (seed.py)

- Runnable via `python -m src.data.seed.seed`
- Loads all 4 JSON files (products, price_tiers, stock, discounts)
- Clears and re-inserts on each run (idempotent)
- Creates `product_variants` from stock.json variant data
- Calls `index_products()` to populate ChromaDB

## Test Summary

- All imports verified: `database OK`, `vector_store OK`, `seed OK`
- SQLite `init_db()` runs and creates tables successfully
- `search_products('polo')` returns 4 matching products from DB
- ChromaDB indexing requires valid `GOOGLE_API_KEY` — will fail at runtime without it (expected)

## Concerns

1. **`extra: "ignore"`** was needed on the Settings model because `.env` contains keys (LANGSMITH, LLAMA_CLOUD, etc.) not defined in Settings. This is a good practice but means unknown env vars are silently ignored.
2. **Seed is destructive** — it clears all product/variant/stock/discount data on each run. Consider adding a `--drop` flag if re-seeding while preserving conversations/quotes.
3. **No migrations** — tables are created via raw SQL. For schema changes in production, a migration tool (e.g., `alembic`) would be needed.
