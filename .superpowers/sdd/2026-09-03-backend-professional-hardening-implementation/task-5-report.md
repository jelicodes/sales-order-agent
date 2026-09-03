## Task 5: Rewrite agent tests with mocked LLM

**Status:** DONE_WITH_CONCERNS

### What I implemented

Rewrote `tests/test_agent.py` with 5 deterministic tests using the `mock_llm` fixture:

1. **TestAgentCreation.test_agent_can_be_created** - Verifies agent can be created with mocked LLM
2. **TestAgentFlow.test_agent_responds_to_greeting** - Verifies greeting response with scripted AIMessage
3. **TestAgentFlow.test_agent_calls_search_tool** - Verifies tool call flow (AIMessage with tool_calls → tool execution → final response)
4. **TestAgentFlow.test_agent_handles_error_gracefully** - Verifies error message handling
5. **TestAgentFlow.test_agent_maintains_context** - Verifies multi-turn context passing

### What I tested

```
tests/test_agent.py::TestAgentCreation::test_agent_can_be_created PASSED
tests/test_agent.py::TestAgentFlow::test_agent_responds_to_greeting PASSED
tests/test_agent.py::TestAgentFlow::test_agent_calls_search_tool PASSED
tests/test_agent.py::TestAgentFlow::test_agent_handles_error_gracefully PASSED
tests/test_agent.py::TestAgentFlow::test_agent_maintains_context PASSED

5 passed in 2.19s
```

### Files changed

- `tests/test_agent.py` - Rewritten with mocked LLM tests
- `tests/conftest.py` - Fixed `mock_llm` fixture (see concerns)

### Self-review findings

**Concern:** The `mock_llm` fixture from Task 4 had a bug. It used `yield` inside the factory function `_make_agent`, which made it a generator function. When called, it returned a generator object instead of the agent, causing `AttributeError: 'generator' object has no attribute 'invoke'`.

**Fix applied:** Rewrote the fixture to use manual `patcher.start()` / `patcher.stop()` instead of `with patch(...)` + `yield`. The fixture now:
- Starts the patch when `_make_agent` is called
- Returns the agent directly
- Cleans up all patches when the test finishes

This fix was necessary for the tests to work. The original fixture design was incorrect for a factory pattern.
