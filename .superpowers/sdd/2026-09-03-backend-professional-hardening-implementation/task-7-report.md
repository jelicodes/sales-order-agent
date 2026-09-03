## Task 7: Add missing unit tests

### What I implemented

Created two new test files:

- `tests/test_database_extended.py` — 9 tests covering database functions with seeded data: init_db idempotency, search by category, product variants, price tier boundaries (99/100), stock by product, valid/invalid discount lookup, and conversation history ordering with explicit timestamps.

- `tests/test_tools_extended.py` — 6 tests covering tool functions: calculate_price error for nonexistent product, discount min_qty not enforced (documents current behavior for Task 12), create_quote with dict items and Pydantic items, alternatives sorted descending for stock reason, and alternatives same category for budget reason.

### What I tested

- Ran new tests: 15/15 passing
- Ran full suite (excluding integration): 87/87 passing, output pristine (only pre-existing StarletteDeprecationWarning)

### Files changed

- `tests/test_database_extended.py` (created)
- `tests/test_tools_extended.py` (created)

### Self-review findings

- Modified the `test_conversation_history_ordering` test from the brief: used explicit timestamps via an `_insert_message` helper instead of `save_message`, because messages inserted in rapid succession share the same `CURRENT_TIMESTAMP` and SQLite doesn't guarantee stable ordering for equal timestamps.
- Both test files use an `autouse` `seeded_db` fixture that creates a temporary database, loads seed data from JSON files, and cleans up after. This avoids depending on ChromaDB/vector store during tests.

### Concerns

None.
