# Task 11: Add database unit tests

**Status:** DONE

## What was done

Created `tests/test_database.py` with 6 database unit tests using temporary SQLite files (via `tempfile.NamedTemporaryFile`):

1. **test_create_and_get_session** — verifies session creation and retrieval
2. **test_get_nonexistent_session** — returns None for missing session
3. **test_save_and_get_messages** — saves messages and retrieves history in order
4. **test_get_conversation_history_max_messages** — respects `max_messages` limit, returns most recent
5. **test_search_products_empty_database** — returns empty list when no products exist
6. **test_create_quote** — creates quote with correct fields and pending status

## Deviations from spec

- **Import path fixed:** `from src.config.settings import settings` (spec used `from src.config import settings` which failed due to empty `__init__.py`)
- **Timestamp ordering:** Used direct SQL inserts with explicit timestamps instead of `save_message()` to avoid non-deterministic ordering from SQLite `CURRENT_TIMESTAMP` having second-level precision
- **Added `_insert_message` helper:** Inserts into conversations table with explicit timestamp for deterministic test assertions

## Test results

```
67 passed, 1 warning in 9.10s
```

All existing tests (test_tools.py: 51, test_api.py: 10) plus new database tests (6) pass.

## Commit

```
00cdd90 test: add database unit tests with in-memory SQLite
```

## Concerns

None. Tests are isolated via temp files that are cleaned up after each test.
