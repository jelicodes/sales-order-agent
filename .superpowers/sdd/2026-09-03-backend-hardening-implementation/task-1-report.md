# Task 1: Add slowapi rate limiting

**Status:** DONE

## Changes Made

1. **requirements.txt** — Added `slowapi>=0.1.9`
2. **src/main.py** — Added Limiter imports, middleware setup, and RateLimitExceeded exception handler
3. **src/api/chat.py** — Added `@limiter.limit("10/minute")` decorator and `request: Request` parameter to chat endpoint

## Test Results

```
55 passed, 1 warning in 11.20s
```

All existing tests pass with no regressions.

## Commit

```
50ea5fd feat: add rate limiting with slowapi (10 req/min per IP)
```

## Notes

- Added `request: Request` parameter to `chat_endpoint` as required by slowapi's limiter decorator
- Rate limit: 10 requests per minute per IP address
- Returns HTTP 429 with Indonesian error message when limit exceeded
