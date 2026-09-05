from datetime import date
from cachetools import TTLCache

from src.data.schema import get_connection

_product_cache = TTLCache(maxsize=500, ttl=300)
_price_tier_cache = TTLCache(maxsize=200, ttl=300)
_discount_cache = TTLCache(maxsize=50, ttl=600)


class ProductRepo:

    def clear_caches(self):
        _product_cache.clear()
        _price_tier_cache.clear()
        _discount_cache.clear()

    def search(self, query: str, category: str | None = None) -> list[dict]:
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
            return [dict(row) for row in cursor.fetchall()]

    def get_by_id(self, product_id: int) -> dict | None:
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

    def get_variants(self, product_id: int) -> list[dict]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM product_variants WHERE product_id = ?", (product_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_price_tier(self, product_id: int, quantity: int) -> dict | None:
        cache_key = (product_id, quantity)
        if cache_key in _price_tier_cache:
            return _price_tier_cache[cache_key]
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM price_tiers
                WHERE product_id = ? AND min_qty <= ?
                AND (max_qty IS NULL OR max_qty >= ?)
                ORDER BY min_qty DESC LIMIT 1""",
                (product_id, quantity, quantity),
            )
            row = cursor.fetchone()
            result = dict(row) if row else None
            _price_tier_cache[cache_key] = result
            return result

    def get_stock_by_product(self, product_id: int) -> list[dict]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT pv.id AS variant_id, pv.color, s.quantity, s.warehouse_location
                FROM product_variants pv
                JOIN stock s ON s.variant_id = pv.id
                WHERE pv.product_id = ?""",
                (product_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_discount(self, code: str) -> dict | None:
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
