### Task 8: Add static data caching

**Files:**
- Modify: `requirements.txt`
- Modify: `src/data/database.py`
- Modify: `src/data/seed/seed.py`

**Interfaces:**
- Consumes: existing database query functions
- Produces: cached data access with TTL

- [ ] **Step 1: Add cachetools to requirements.txt**

```txt
cachetools>=5.3.0
```

- [ ] **Step 2: Install cachetools**

Run: `D:\Jeli\myenv\Scripts\pip.exe install cachetools>=5.3.0`

- [ ] **Step 3: Add caching to database.py**

Add these imports and cache instances at the top of `database.py`:

```python
from cachetools import TTLCache

# Cache for static data
_product_cache = TTLCache(maxsize=500, ttl=300)  # 5 min
_price_tier_cache = TTLCache(maxsize=200, ttl=300)
_discount_cache = TTLCache(maxsize=50, ttl=600)  # 10 min
```

Add a `clear_caches()` function:

```python
def clear_caches():
    """Clear all caches (useful after seed)."""
    _product_cache.clear()
    _price_tier_cache.clear()
    _discount_cache.clear()
```

Update `get_product_by_id()` to use cache:

```python
def get_product_by_id(product_id: int) -> dict | None:
    if product_id in _product_cache:
        return _product_cache[product_id]

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        row = cursor.fetchone()
        result = dict(row) if row else None
        if result:
            _product_cache[product_id] = result
        return result
```

Update `get_price_tier()` to use cache:

```python
def get_price_tier(product_id: int, quantity: int) -> dict | None:
    cache_key = (product_id, quantity)
    if cache_key in _price_tier_cache:
        return _price_tier_cache[cache_key]

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM price_tiers
            WHERE product_id = ?
              AND min_qty <= ?
              AND (max_qty IS NULL OR max_qty >= ?)
            ORDER BY min_qty DESC
            LIMIT 1
            """,
            (product_id, quantity, quantity),
        )
        row = cursor.fetchone()
        result = dict(row) if row else None
        _price_tier_cache[cache_key] = result
        return result
```

Update `get_discount()` to use cache:

```python
def get_discount(code: str) -> dict | None:
    if code in _discount_cache:
        return _discount_cache[code]

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM discounts WHERE code = ? AND valid_until >= ?",
            (code, date.today().isoformat()),
        )
        row = cursor.fetchone()
        result = dict(row) if row else None
        _discount_cache[code] = result
        return result
```

- [ ] **Step 4: Update seed.py to clear caches after seeding**

Update the import:
```python
from src.data.database import init_db, get_connection, clear_caches
```

Add `clear_caches()` call after seeding (before `index_products`):
```python
    # Clear caches after seeding
    clear_caches()
```

Also fix the context manager usage — change:
```python
conn = get_connection()
cursor = conn.cursor()
# ... inserts ...
conn.commit()
conn.close()
```

To:
```python
with get_connection() as conn:
    cursor = conn.cursor()
    # ... inserts ...
    # conn.commit() handled by context manager
```

- [ ] **Step 5: Run tests to verify caching works**

Run: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/test_tools.py tests/test_database.py tests/test_database_extended.py -v`

Expected: All tests pass

- [ ] **Step 6: Commit**

```bash
git add requirements.txt src/data/database.py src/data/seed/seed.py
git commit -m "feat: add TTL caching for static data (products, price tiers, discounts)"
```
