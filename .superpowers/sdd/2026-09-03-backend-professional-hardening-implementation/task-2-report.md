# Task 2: Refactor connection management with proper error handling

## What was implemented

Refactored `get_connection()` in `src/data/database.py` to provide proper error handling:

1. **Added `check_same_thread=False`** to `sqlite3.connect()` call
2. **Added auto-commit on success** via `conn.commit()` in the try block
3. **Added rollback on exception** via `conn.rollback()` in the except block
4. **Removed redundant `conn.commit()` calls** from:
   - `init_db()` (line 113, after indexes)
   - `create_session()` (line 209)
   - `save_message()` (line 228)
   - `create_quote()` (line 250)

## Changes

### `src/data/database.py`
- Updated `get_connection()` context manager with commit/rollback/close
- Removed 4 redundant `conn.commit()` calls from individual functions

## Tests

Ran: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/test_tools.py tests/test_database.py -v`

Result: **58/58 passing**, output pristine (only deprecation warning from FastAPI test client)

## Self-Review

- **Completeness:** All 4 steps from the task brief completed
- **Quality:** Clean, focused changes; follows existing patterns
- **Discipline:** No overbuilding; only implemented what was requested
- **Testing:** All existing tests pass; rollback behavior tested implicitly by database tests

## Commits

- `b8c93fa` - feat: refactor connection management with rollback on error

## Concerns

None.
