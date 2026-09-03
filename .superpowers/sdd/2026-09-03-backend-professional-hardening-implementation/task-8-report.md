# Task 8: Add static data caching — Report

## What was implemented
- Added `cachetools>=5.3.0` to `requirements.txt`
- Installed `cachetools` (v7.1.8)
- Added `TTLCache` instances in `database.py`: `_product_cache` (500, 5min), `_price_tier_cache` (200, 5min), `_discount_cache` (50, 10min)
- Added `clear_caches()` function to reset all caches
- Updated `get_product_by_id()`, `get_price_tier()`, and `get_discount()` to check/populate caches before querying DB
- Updated `seed.py`: fixed context manager usage (`with get_connection() as conn:`), added `clear_caches()` call after seeding

## What was tested
- Ran `test_tools.py`, `test_database.py`, `test_database_extended.py`
- **67/67 passing**, output pristine (only pre-existing StarletteDeprecationWarning)

## Files changed
- `requirements.txt`
- `src/data/database.py`
- `src/data/seed/seed.py`

## Self-review findings
None — all requirements met, code follows existing patterns, no overbuilding.

## Commit
`1b7d209` — feat: add TTL caching for static data (products, price tiers, discounts)
