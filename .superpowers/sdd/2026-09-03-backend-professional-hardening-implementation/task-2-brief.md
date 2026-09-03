### Task 2: Refactor connection management with proper error handling

**Files:**
- Modify: `src/data/database.py`

**Interfaces:**
- Consumes: existing `get_connection()` usage across codebase
- Produces: `get_connection()` with commit/rollback/close

- [ ] **Step 1: Update get_connection() with error handling**

```python
@contextmanager
def get_connection():
    conn = sqlite3.connect(_get_db_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
```

- [ ] **Step 2: Remove redundant commit calls**

In `database.py`, remove `conn.commit()` from all functions since `get_connection()` now handles it:
- `init_db()` line 105 (the one after the indexes)
- `create_session()` line 201
- `save_message()` line 220
- `create_quote()` line 242

Note: The `conn.commit()` at the end of `init_db()` should be removed since `get_connection()` now handles commit automatically. The same applies to `create_session()`, `save_message()`, and `create_quote()`.

- [ ] **Step 3: Run existing tests**

Run: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/test_tools.py tests/test_database.py -v`

Expected: All tests pass

- [ ] **Step 4: Commit**

```bash
git add src/data/database.py
git commit -m "feat: refactor connection management with rollback on error"
```
