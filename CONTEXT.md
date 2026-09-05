# CONTEXT.md — Sales Order Agent

## Overview

AI-powered B2B fashion wholesale ordering system for **PT Lemone Surya Indonesia**, a fashion wholesale company based in Pusat Grosir Metro Tanah Abang, Jakarta Pusat. The agent handles multi-turn conversations for product search, stock checking, price calculation, quote generation, and order management.

## Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Agent | LangGraph (ReAct pattern) | Stateful multi-turn with tool calling |
| LLM | Groq (Qwen 3.6 27B) | Ultra-fast inference (~100ms) |
| Embedding | Google Gemini (gemini-embedding-001) | Semantic product search |
| Backend | FastAPI + Uvicorn | Async Python 3.11+ |
| Database | SQLite + ChromaDB | Structured data + vector embeddings |
| Observability | Langfuse | Agent tracing & monitoring |
| Rate Limiting | Slowapi | 10 req/min per IP |
| Caching | cachetools (TTLCache) | Static data cached 5-10 min |

## Domain Glossary

| Term | Definition |
|------|-----------|
| **Order** | Customer purchase request — contains product, qty, price, status |
| **Quote** | Price quotation sent to customer — valid 7 days, multi-item |
| **Stock** | Per-variant (product + color + size) inventory count |
| **Tier pricing** | Volume-based pricing — larger qty = lower unit price |
| **MOQ** | Minimum Order Quantity — smallest order a supplier accepts |
| **Lead time** | Days between order confirmation and ready-to-ship |
| **Session** | Conversation thread — identified by `session_id`, persisted via checkpointer |
| **Agent** | LangGraph ReAct agent — thinks, calls tools, observes results |
| **Tool** | Single-purpose function the agent can call (search, stock, price, quote, etc.) |
| **Checkpointer** | SqliteSaver — persists agent state across turns in a session |

## Architecture Decisions

See `docs/adr/` for recorded architectural decisions. Key ones:

- ADR-0001: LangGraph over raw LangChain for stateful agent
- ADR-0002: Groq for LLM inference (speed priority)
- ADR-0003: ChromaDB for semantic product search
- ADR-0004: SQLite for structured data (lightweight, no server)

## Conventions

- **Language**: Bahasa Indonesia for user-facing content (agent responses, prompts)
- **Error format**: `{"error": "message"}` dict from tools, never raise exceptions
- **Tool output**: Structured dicts, not raw strings
- **Async wrapping**: `await asyncio.to_thread(sync_db_call)` for non-blocking
- **State flow**: All state through `messages` key in `AgentState`
- **System prompt**: Isolated in `prompts.py` — never concatenate user input
