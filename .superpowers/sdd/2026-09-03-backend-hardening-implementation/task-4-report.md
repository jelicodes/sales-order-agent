# Task 4: Add version constant

**Status:** DONE

## Changes Made

| File | Change |
|------|--------|
| `src/config/settings.py` | Added module-level `APP_VERSION: str = "0.1.0"` constant |
| `src/main.py` | Imported `APP_VERSION`, used in FastAPI `version=` param |
| `src/api/health.py` | Imported `APP_VERSION`, used in health response `version=` field |

## Commit

```
feat: centralize APP_VERSION constant in settings
```

Commit hash: `129aef3`

## Test Results

```
55 passed, 1 warning in 9.18s
```

All tests pass: `test_tools.py` (52 tests) and `test_api.py` (3 tests).

## Notes

- `APP_VERSION` is a module-level constant (not a `Settings` class field) so it can be imported directly without accessing the `settings` instance.
- Centralized in one place — any future version bump only needs to change `settings.py`.
