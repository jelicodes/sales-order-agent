import sqlite3
from pathlib import Path
from datetime import date
from contextlib import contextmanager

from cachetools import TTLCache
from src.config.settings import settings

# Cache for static data
_product_cache = TTLCache(maxsize=500, ttl=300)  # 5 min
_price_tier_cache = TTLCache(maxsize=200, ttl=300)
_discount_cache = TTLCache(maxsize=50, ttl=600)  # 10 min


def clear_caches():
    """Clear all caches (useful after seed)."""
    _product_cache.clear()
    _price_tier_cache.clear()
    _discount_cache.clear()


_db_path: str | None = None


def _get_db_path() -> str:
    global _db_path
    if _db_path is None:
        db_path = Path(settings.DATABASE_PATH)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        _db_path = str(db_path)
    return _db_path


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

            CREATE TABLE IF NOT EXISTS customers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                tier TEXT DEFAULT 'regular',
                created_at TEXT NOT NULL,
                last_order_at TEXT
            );

            CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY,
                customer_id TEXT NOT NULL,
                items TEXT NOT NULL,
                subtotal INTEGER NOT NULL,
                discount_amount INTEGER DEFAULT 0,
                total_price INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                shipping_address TEXT,
                payment_status TEXT DEFAULT 'unpaid',
                payment_terms INTEGER DEFAULT 0,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            );

            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT NOT NULL,
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                qty INTEGER NOT NULL,
                price_per_unit INTEGER NOT NULL,
                subtotal INTEGER NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            );

            CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
            CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);
            CREATE INDEX IF NOT EXISTS idx_product_variants_product_id ON product_variants(product_id);
            CREATE INDEX IF NOT EXISTS idx_price_tiers_product_id ON price_tiers(product_id);
            CREATE INDEX IF NOT EXISTS idx_stock_variant_id ON stock(variant_id);
            CREATE INDEX IF NOT EXISTS idx_conversations_session_ts ON conversations(session_id, timestamp DESC);
            CREATE INDEX IF NOT EXISTS idx_discounts_code ON discounts(code);
            CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);
            CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
            CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
        """)


def search_products(query: str, category: str | None = None) -> list[dict]:
    with get_connection() as conn:
        cursor = conn.cursor()
        if category:
            cursor.execute(
                "SELECT * FROM products WHERE name LIKE ? AND category = ?",
                (f"%{query}%", category),
            )
        else:
            cursor.execute(
                "SELECT * FROM products WHERE name LIKE ? OR category LIKE ? OR description LIKE ?",
                (f"%{query}%", f"%{query}%", f"%{query}%"),
            )
        results = [dict(row) for row in cursor.fetchall()]
        return results


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


def get_product_variants(product_id: int) -> list[dict]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM product_variants WHERE product_id = ?", (product_id,))
        results = [dict(row) for row in cursor.fetchall()]
        return results


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


def get_stock(variant_id: int) -> dict | None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM stock WHERE variant_id = ?", (variant_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_stock_by_product(product_id: int) -> list[dict]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT pv.id AS variant_id, pv.color, s.quantity, s.warehouse_location
            FROM product_variants pv
            JOIN stock s ON s.variant_id = pv.id
            WHERE pv.product_id = ?
            """,
            (product_id,),
        )
        results = [dict(row) for row in cursor.fetchall()]
        return results


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


def create_session(session_id: str, customer_name: str) -> dict:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sessions (id, customer_name) VALUES (?, ?)",
            (session_id, customer_name),
        )
        return {"id": session_id, "customer_name": customer_name, "status": "active"}


def get_session(session_id: str) -> dict | None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def save_message(session_id: str, role: str, content: str, tool_calls: str | None = None) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO conversations (session_id, role, content, tool_calls) VALUES (?, ?, ?, ?)",
            (session_id, role, content, tool_calls),
        )


def get_conversation_history(session_id: str, max_messages: int = 50) -> list[dict]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM conversations WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?",
            (session_id, max_messages),
        )
        results = [dict(row) for row in cursor.fetchall()]
        results.reverse()
        return results


def create_quote(quote_id: str, session_id: str, items_json: str, total_price: float, valid_until: str) -> dict:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO quotes (id, session_id, items_json, total_price, valid_until) VALUES (?, ?, ?, ?, ?)",
            (quote_id, session_id, items_json, total_price, valid_until),
        )
        return {
            "id": quote_id,
            "session_id": session_id,
            "items_json": items_json,
            "total_price": total_price,
            "valid_until": valid_until,
            "status": "pending",
        }


import uuid
import json
from datetime import datetime


def create_customer(name: str, phone: str | None = None, email: str | None = None, tier: str = "regular") -> dict:
    customer_id = f"CUST-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.now().isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO customers (id, name, phone, email, tier, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (customer_id, name, phone, email, tier, now),
        )
        return {"id": customer_id, "name": name, "phone": phone, "email": email, "tier": tier, "created_at": now}


def get_customer_by_id(customer_id: str) -> dict | None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_customer_by_phone(phone: str) -> dict | None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customers WHERE phone = ?", (phone,))
        row = cursor.fetchone()
        return dict(row) if row else None


def create_order(customer_id: str, items: list[dict], subtotal: int, discount_amount: int, total_price: int, shipping_address: str | None = None, notes: str | None = None) -> dict:
    order_id = f"ORD-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
    now = datetime.now().isoformat()
    items_json = json.dumps(items)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO orders (id, customer_id, items, subtotal, discount_amount, total_price, status, shipping_address, notes, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?)""",
            (order_id, customer_id, items_json, subtotal, discount_amount, total_price, shipping_address, notes, now, now),
        )
        for item in items:
            cursor.execute(
                """INSERT INTO order_items (order_id, product_id, product_name, qty, price_per_unit, subtotal)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (order_id, item["product_id"], item["product_name"], item["qty"], item["price_per_unit"], item["subtotal"]),
            )
        cursor.execute("UPDATE customers SET last_order_at = ? WHERE id = ?", (now, customer_id))
        return {"id": order_id, "customer_id": customer_id, "total_price": total_price, "status": "pending", "created_at": now}


def get_order_by_id(order_id: str) -> dict | None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        row = cursor.fetchone()
        if row:
            order = dict(row)
            cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,))
            order["items"] = [dict(item) for item in cursor.fetchall()]
            return order
        return None


def get_orders_by_customer(customer_id: str, limit: int = 10) -> list[dict]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM orders WHERE customer_id = ? ORDER BY created_at DESC LIMIT ?",
            (customer_id, limit),
        )
        return [dict(row) for row in cursor.fetchall()]


def update_order_status(order_id: str, status: str) -> bool:
    valid_transitions = {
        "pending": ["confirmed", "cancelled"],
        "confirmed": ["processing", "cancelled"],
        "processing": ["shipped"],
        "shipped": ["delivered"],
    }
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM orders WHERE id = ?", (order_id,))
        row = cursor.fetchone()
        if not row:
            return False
        current_status = row["status"]
        if status not in valid_transitions.get(current_status, []):
            return False
        now = datetime.now().isoformat()
        cursor.execute(
            "UPDATE orders SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, order_id),
        )
        return True
