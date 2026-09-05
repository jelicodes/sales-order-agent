# ADR-0003: ChromaDB for Semantic Product Search

## Status

Accepted

## Context

Customers search for fashion products using natural language ("kaos polo hitam untuk seragam"). Keyword matching is insufficient — we need semantic understanding to match intent.

Options considered:
1. **SQLite FTS** — fast but keyword-only, no semantic understanding
2. **ChromaDB** — embedded vector DB, lightweight, good for our scale
3. **Pinecone / Weaviate** — cloud-hosted, overkill for single-tenant use case

## Decision

Use **ChromaDB** as embedded vector database. Product embeddings generated via Google Gemini (gemini-embedding-001). Semantic search returns ranked results by cosine similarity.

## Consequences

- Natural language queries match product intent, not just keywords
- Embedded — no separate server process to manage
- Data lives alongside SQLite in `data/` directory
- Embedding model configurable via `EMBEDDING_MODEL` env var
