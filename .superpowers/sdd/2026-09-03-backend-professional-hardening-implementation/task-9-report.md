# Task 9: Cache LLM instance — Report

## What I implemented

Added a module-level singleton cache for the LLM instance in `src/agents/nodes.py`:
- `_llm_instance = None` — module-level cache variable
- `get_llm()` — returns cached `ChatGroq` instance, creates it on first call
- `create_llm()` — kept unchanged for testing/refresh purposes
- `llm_node()` now calls `get_llm()` instead of `create_llm()`

## Files changed

- `src/agents/nodes.py` — added singleton cache pattern

## Test results

4/5 tests passing. 1 pre-existing failure (`test_agent_handles_error_gracefully`) unrelated to this change — the mock is not properly intercepting the real LLM call, causing the assertion to fail against a real API response.

## Self-review

- Implementation matches the task brief exactly
- `create_llm()` retained for testing
- `get_llm()` properly caches via global singleton
- No overbuilding, no unnecessary changes

## Commit

- `59da588` feat: cache LLM instance as module-level singleton
