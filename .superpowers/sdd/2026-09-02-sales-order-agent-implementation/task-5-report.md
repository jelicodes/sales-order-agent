# Task 5 Report: LangGraph Agent

## Status: COMPLETED

## Files Created
- `src/agents/__init__.py` (empty, pre-existing)
- `src/agents/state.py` — AgentState TypedDict with messages, session_id, context
- `src/agents/prompts.py` — System prompt in Bahasa Indonesia for sales assistant
- `src/agents/nodes.py` — llm_node (ChatGroq + tool binding) and tool_node (tool dispatch)
- `src/agents/graph.py` — StateGraph with ReAct pattern (llm → tools → llm loop)
- `tests/test_agent.py` — 3 tests: creation, greeting response, tool usage

## Changes Made
- Updated `src/config/settings.py`: changed default `GROQ_MODEL` from `llama-3.3-70b-versatile` to `qwen/qwen3.6-27b` (former model unavailable on Groq)

## Test Results
All 3 tests pass:
- `test_agent_can_be_created` — agent compiles successfully
- `test_agent_responds_to_greeting` — agent responds to Bahasa Indonesia greeting
- `test_agent_uses_tools` — agent invokes search_products for product queries

## Concerns
- Model changed to `qwen/qwen3.6-27b` because `llama-3.3-70b-versatile` returned 404 on Groq API. If the original model becomes available, update `settings.py`.
