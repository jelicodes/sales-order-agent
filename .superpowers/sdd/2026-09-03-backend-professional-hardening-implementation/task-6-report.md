## Task 6: Rewrite integration tests with mocked agent

**Status:** DONE

### What I implemented

Rewrote `tests/test_integration.py` to mock the entire agent at the module level, eliminating real Groq API calls.

**Key change from the task brief:** The brief suggested patching `src.api.chat.create_sales_agent`, but that function is called at module import time (`src/api/chat.py:11`), so the `agent` variable is already bound. I patched `src.api.chat.agent` directly instead.

**Mock behavior:** The mock agent's `invoke.side_effect` routes based on keywords in the last user message:
- `polo`, `kaos`, `premium`, `navy` → product info response
- `penawaran`, `quote` → formal quote response
- Everything else → "not found" fallback

**Additional fix:** Added `premium` and `navy` to the product keyword list so the follow-up message "Yang Premium, bisa warna navy?" matches correctly (it doesn't contain "polo" or "kaos").

### Files changed

- `tests/test_integration.py` — full rewrite with fixture-based mocking

### Test results

All 3 integration tests pass in ~1.7 seconds (well under 5s requirement):
- `TestFullFlow::test_inquiry_to_quote_flow` — PASSED
- `TestEdgeCases::test_unknown_product` — PASSED
- `TestEdgeCases::test_budget_too_low` — PASSED

Full test suite (75 tests) also passing, no regressions.

### Commit

- `8147f03` — test: rewrite integration tests with mocked agent (no real API calls)

### Self-review

- ✅ All acceptance criteria met (mocked agent, < 5s, fixture-based)
- ✅ No real API calls
- ✅ Follows existing test patterns
- ✅ Clean, maintainable code
- No concerns
