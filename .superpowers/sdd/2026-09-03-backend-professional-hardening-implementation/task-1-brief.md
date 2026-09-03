### Task 1: Add database indexes

**Files:**
- Modify: `src/data/database.py`

**Interfaces:**
- Consumes: existing `init_db()` function
- Produces: indexed database schema

- [ ] **Step 1: Add index creation to init_db()**

After the `CREATE TABLE` statements in `init_db()`, add index creation:

```python
def init_db() -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                base_price REAL NOT NULL,
                moq INTEGER NOT NULL DEFAULT 1,
                lead_time_days INTEGER NOT NULL DEFAULT 5
            );

            CREATE TABLE IF NOT EXISTS product_variants (
                id INTEGER PRIMARY KEY,
                product_id INTEGER NOT NULL,
                color TEXT NOT NULL,
                FOREIGN KEY (product_id) REFERENCES products(id)
            );

            CREATE TABLE IF NOT EXISTS price_tiers (
                id INTEGER PRIMARY KEY,
                product_id INTEGER NOT NULL,
                min_qty INTEGER NOT NULL,
                max_qty INTEGER,
                price_per_unit REAL NOT NULL,
                FOREIGN KEY (product_id) REFERENCES products(id)
            );

            CREATE TABLE IF NOT EXISTS stock (
                id INTEGER PRIMARY KEY,
                variant_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                warehouse_location TEXT NOT NULL,
                FOREIGN KEY (variant_id) REFERENCES product_variants(id)
            );

            CREATE TABLE IF NOT EXISTS discounts (
                id INTEGER PRIMARY KEY,
                code TEXT UNIQUE NOT NULL,
                type TEXT NOT NULL,
                value REAL NOT NULL,
                min_qty INTEGER,
                valid_until DATE
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                customer_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active'
            );

            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                tool_calls TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            );

            CREATE TABLE IF NOT EXISTS quotes (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                items_json TEXT NOT NULL,
                total_price REAL NOT NULL,
                valid_until DATE NOT NULL,
                status TEXT DEFAULT 'pending',
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            );
        """)

        # Create indexes for performance
        cursor.executescript("""
            CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
            CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);
            CREATE INDEX IF NOT EXISTS idx_product_variants_product_id ON product_variants(product_id);
            CREATE INDEX IF NOT EXISTS idx_price_tiers_product_id ON price_tiers(product_id);
            CREATE INDEX IF NOT EXISTS idx_stock_variant_id ON stock(variant_id);
            CREATE INDEX IF NOT EXISTS idx_conversations_session_ts ON conversations(session_id, timestamp DESC);
            CREATE INDEX IF NOT EXISTS idx_discounts_code ON discounts(code);
        """)
        conn.commit()
```

- [ ] **Step 2: Verify indexes exist**

Run: `D:\Jeli\myenv\Scripts\python.exe -c "from src.data.database import init_db; init_db(); import sqlite3; conn = sqlite3.connect('data/app.db'); cursor = conn.cursor(); cursor.execute(\"SELECT name FROM sqlite_master WHERE type='index'\"); print([r[0] for r in cursor.fetchall()])"`

Expected: List of 7 index names

- [ ] **Step 3: Run existing tests to verify no regression**

Run: `D:\Jeli\myenv\Scripts\python.exe -m pytest tests/test_tools.py tests/test_database.py -v`

Expected: All tests pass

- [ ] **Step 4: Commit**

```bash
git add src/data/database.py
git commit -m "feat: add database indexes for query performance"
```
