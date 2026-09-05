## Agent skills

### Issue tracker

Issues live in GitHub Issues, managed via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Five canonical role labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout — one `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.

## Coding standards

### Python

- **Version**: Python 3.13.1
- **Virtual environment**: `D:\Jeli\myenv` — always use this for pip install and running scripts
- **Python executable**: `D:\Jeli\myenv\Scripts\python.exe`
- **Formatter**: Follow existing code style (no black/ruff enforced, but stay consistent)
- **Type hints**: Use on all public functions and Pydantic models
- **Imports**: stdlib → third-party → local, separated by blank lines
- **Async**: Use `asyncio.to_thread()` for blocking DB calls in async contexts

### Naming conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Files | `snake_case.py` | `search_products.py` |
| Classes | `PascalCase` | `AgentState`, `Settings` |
| Functions | `snake_case` | `search_products()`, `calculate_price()` |
| Constants | `UPPER_SNAKE_CASE` | `SALES_AGENT_PROMPT`, `APP_VERSION` |
| Pydantic models | `PascalCase` | `ChatRequest`, `SessionResponse` |

### Project structure

```
src/
├── main.py              # FastAPI entry point + lifespan
├── agents/              # LangGraph agent (graph, state, nodes, prompts)
├── tools/               # Agent tools (one file per tool)
├── api/                 # FastAPI routes + Pydantic models
├── data/                # Database, vector store, seed data
│   ├── repos/           # Domain repositories (ProductRepo, OrderRepo, etc.)
│   └── schema.py        # Centralized DDL + connection management
└── config/              # Settings, integrations (Langfuse)
```

- **One tool per file** in `src/tools/`
- **Routes grouped by domain** in `src/api/` (chat, session, health)
- **Config centralized** in `src/config/settings.py` via Pydantic Settings

## Testing

### Commands

```bash
# Run all unit tests
pytest tests/ -v --ignore=tests/test_integration.py

# Run specific test suites
pytest tests/test_tools.py -v          # 52 tool tests
pytest tests/test_database.py -v       # 10 DB tests
pytest tests/test_database_extended.py -v  # 8 extended DB tests
pytest tests/test_api.py -v            # 3 non-chat API tests
pytest tests/test_agent.py -v          # 9 agent tests
pytest tests/test_integration.py -v    # integration tests (mocked LLM)
```

### Conventions

- Tests live in `tests/` mirroring `src/` structure
- Use `pytest` with fixtures defined in `conftest.py`
- Mock LLM calls in unit tests — never hit real APIs in CI
- Integration tests use mocked LLM responses (3 tests)
- Tool tests cover both success and error paths

## Agent conventions

### LangGraph patterns

- **State**: `AgentState` (TypedDict) with `messages` key — all state flows through messages
- **Graph**: `StateGraph` → `add_conditional_edges` for tool routing
- **Checkpointer**: `SqliteSaver` for conversation persistence — never pass `None` in production
- **Retry policy**: 3x retry on transient LLM failures via `retry_policy`

### System prompt

- Isolated in `src/agents/prompts.py` — never concatenate user input into system prompt
- Language: Bahasa Indonesia (professional, no emoji)
- Rules: always check stock before pricing, suggest alternatives on stock mismatch

### Tool design

- Each tool is a standalone `@tool` decorated function
- Tools return structured dicts, not raw strings
- Async wrapping: `await asyncio.to_thread(sync_db_call)` for non-blocking
- Error handling: return `{"error": "..."}` dict, never raise in tools

### Observability

- Langfuse tracing enabled by default (`LANGFUSE_ENABLED=true`)
- Trace name matches operation: `search_products`, `create_quote`, etc.
- Never log API keys or secrets to traces
