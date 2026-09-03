# Task 6: Add Message History Truncation — Report

**Status:** DONE

## Changes Made

### `src/data/database.py`
- Added `max_messages` parameter (default 50) to `get_conversation_history`
- Query now uses `ORDER BY timestamp DESC LIMIT ?` then `.reverse()` to fetch the N most recent messages efficiently at the DB level

### `src/api/chat.py`
- Added `trim_messages` import from `langchain_core.messages`
- After building the messages list, applied `trim_messages` with `max_tokens=8000`, `token_counter=len`, `strategy="last"`, `start_on="human"` to cap token usage before sending to Groq

## Test Results

All 55 tests passed (0 failures, 1 deprecation warning unrelated to changes).

## Commit

```
c7b64b1 feat: add message history truncation with max_messages and trim_messages
```

## Concerns

- `token_counter=len` is a character-count proxy. Acceptable for a portfolio project; production would use a real tokenizer.
