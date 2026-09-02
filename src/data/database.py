import sqlite3
from pathlib import Path
from datetime import date

from src.config.settings import settings


def get_connection() -> sqlite3.Connection:
    db_path = Path(settings.DATABASE_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
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
    conn.commit()
    conn.close()


def search_products(query: str, category: str | None = None) -> list[dict]:
    conn = get_connection()
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
    conn.close()
    return results


def get_product_by_id(product_id: int) -> dict | None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_product_variants(product_id: int) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM product_variants WHERE product_id = ?", (product_id,))
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def get_price_tier(product_id: int, quantity: int) -> dict | None:
    conn = get_connection()
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
    conn.close()
    return dict(row) if row else None


def get_stock(variant_id: int) -> dict | None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM stock WHERE variant_id = ?", (variant_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_stock_by_product(product_id: int) -> list[dict]:
    conn = get_connection()
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
    conn.close()
    return results


def get_discount(code: str) -> dict | None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM discounts WHERE code = ? AND valid_until >= ?",
        (code, date.today().isoformat()),
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def create_session(session_id: str, customer_name: str) -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sessions (id, customer_name) VALUES (?, ?)",
        (session_id, customer_name),
    )
    conn.commit()
    conn.close()
    return {"id": session_id, "customer_name": customer_name, "status": "active"}


def get_session(session_id: str) -> dict | None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def save_message(session_id: str, role: str, content: str, tool_calls: str | None = None) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO conversations (session_id, role, content, tool_calls) VALUES (?, ?, ?, ?)",
        (session_id, role, content, tool_calls),
    )
    conn.commit()
    conn.close()


def get_conversation_history(session_id: str) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM conversations WHERE session_id = ? ORDER BY timestamp",
        (session_id,),
    )
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def create_quote(quote_id: str, session_id: str, items_json: str, total_price: float, valid_until: str) -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO quotes (id, session_id, items_json, total_price, valid_until) VALUES (?, ?, ?, ?, ?)",
        (quote_id, session_id, items_json, total_price, valid_until),
    )
    conn.commit()
    conn.close()
    return {
        "id": quote_id,
        "session_id": session_id,
        "items_json": items_json,
        "total_price": total_price,
        "valid_until": valid_until,
        "status": "pending",
    }
