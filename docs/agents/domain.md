# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

## Before exploring, read these

- **`CONTEXT.md`** at the repo root, or
- **`CONTEXT-MAP.md`** at the repo root if it exists — it points at one `CONTEXT.md` per context. Read each one relevant to the topic.
- **`docs/adr/`** — read ADRs that touch the area you're about to work in. In multi-context repos, also check `src/<context>/docs/adr/` for context-scoped decisions.

If any of these files don't exist, **proceed silently**. Don't flag their absence; don't suggest creating them upfront. The `/domain-modeling` skill (reached via `/grill-with-docs` and `/improve-codebase-architecture`) creates them lazily when terms or decisions actually get resolved.

## File structure

Single-context repo (most repos):

```
/
├── CONTEXT.md
├── docs/adr/
│   ├── 0001-langgraph-for-agent-framework.md
│   ├── 0002-groq-for-llm-inference.md
│   ├── 0003-chromadb-for-semantic-search.md
│   └── 0004-sqlite-for-structured-data.md
└── src/
```

This repo is **single-context** — one `CONTEXT.md` at the root covers the entire codebase. No `CONTEXT-MAP.md` exists (no monorepo signals).

## Use the glossary's vocabulary

When your output names a domain concept (in an issue title, a refactor proposal, a hypothesis, a test name), use the term as defined in `CONTEXT.md`. Don't drift to synonyms the glossary explicitly avoids.

If the concept you need isn't in the glossary yet, that's a signal — either you're inventing language the project doesn't use (reconsider) or there's a real gap (note it for `/domain-modeling`).

**Current glossary terms** (from `CONTEXT.md`):

| Term | Use this | Don't use |
|------|----------|-----------|
| Order | Order | Purchase, transaction, deal |
| Quote | Quotation, quote | Proposal, estimate |
| Stock | Stock | Inventory (in agent context) |
| Tier pricing | Tier pricing | Volume discount, bulk pricing |
| MOQ | MOQ | Minimum order, minimum quantity |
| Lead time | Lead time | Delivery time, turnaround |
| Session | Session | Thread, conversation, chat |
| Agent | Agent | Bot, assistant, chatbot |
| Tool | Tool | Function, method, capability |
| Checkpointer | Checkpointer | State manager, persistence layer |

## Flag ADR conflicts

If your output contradicts an existing ADR, surface it explicitly rather than silently overriding:

> _Contradicts ADR-0002 (Groq for LLM inference) — but worth reopening because…_

**Current ADRs:**

- **ADR-0001**: LangGraph over raw LangChain for stateful agent
- **ADR-0002**: Groq for LLM inference (speed priority)
- **ADR-0003**: ChromaDB for semantic product search
- **ADR-0004**: SQLite for structured data (lightweight, no server)

## Key architectural patterns

When exploring or proposing changes, respect these patterns:

### State flow

All state flows through `messages` key in `AgentState` (TypedDict). Never add separate state keys unless absolutely necessary.

### Tool design

- One tool per file in `src/tools/`
- Tools return structured dicts, not raw strings
- Async wrapping: `await asyncio.to_thread(sync_db_call)` for non-blocking
- Error handling: return `{"error": "..."}` dict, never raise in tools

### Observability

- Langfuse tracing enabled by default
- Trace name matches operation: `search_products`, `create_quote`, etc.
- Never log API keys or secrets to traces

### Testing

- Mock LLM calls in unit tests — never hit real APIs in CI
- Integration tests use mocked LLM responses
- Tool tests cover both success and error paths

## File locations for exploration

| What you're looking for | Where to find it |
|------------------------|------------------|
| Agent logic | `src/agents/` (graph.py, nodes.py, state.py, prompts.py) |
| Tools | `src/tools/` (one file per tool) |
| API routes | `src/api/` (chat.py, products.py, session.py) |
| Database | `src/data/` (schema.py, repos/) |
| Config | `src/config/` (settings.py) |
| Tests | `tests/` (mirrors src/ structure) |
| Frontend | `frontend/` (Next.js, components/) |
| Seed data | `src/data/seed_data.py` |
| Design system | `DESIGN.md` at repo root |
