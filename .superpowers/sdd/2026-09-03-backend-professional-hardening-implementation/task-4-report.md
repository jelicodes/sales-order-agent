## Task 4: Add mock_llm fixture to conftest.py

**Status:** DONE

### What I implemented

Added the `mock_llm` fixture to `tests/conftest.py` that patches `src.agents.nodes.create_llm` to return a mock LLM instance with scripted responses. The fixture follows a factory pattern: call `mock_llm(responses)` with a list of `AIMessage` objects to get a compiled agent that uses the mocked LLM.

### What I tested

- Verified `pytest tests/conftest.py -v` runs without import errors — only a pre-existing Starlette deprecation warning (unrelated).
- Fixture loads correctly with all imports resolving.

### Files changed

- `tests/conftest.py` — Added `mock_llm` fixture with `unittest.mock.patch`

### Commit

- `8fe0802` — `test: add mock_llm fixture for agent tests`

### Self-review findings

- No issues. The implementation matches the task brief exactly, preserves existing fixtures, and follows the project's established patterns.
