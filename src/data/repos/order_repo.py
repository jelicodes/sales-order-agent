import uuid
import json
from datetime import datetime

from src.data.schema import get_connection


class OrderRepo:

    VALID_TRANSITIONS = {
        "pending": ["confirmed", "cancelled"],
        "confirmed": ["processing", "cancelled"],
        "processing": ["shipped"],
        "shipped": ["delivered"],
    }

    def create_order(
        self,
        customer_id: str,
        items: list[dict],
        subtotal: int,
        discount_amount: int,
        total_price: int,
        shipping_address: str | None = None,
        notes: str | None = None,
    ) -> dict:
        order_id = f"ORD-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
        now = datetime.now().isoformat()
        items_json = json.dumps(items)
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO orders (id, customer_id, items, subtotal, discount_amount,
                   total_price, status, shipping_address, notes, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?)""",
                (order_id, customer_id, items_json, subtotal, discount_amount,
                 total_price, shipping_address, notes, now, now),
            )
            for item in items:
                cursor.execute(
                    """INSERT INTO order_items (order_id, product_id, product_name,
                       qty, price_per_unit, subtotal)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (order_id, item["product_id"], item["product_name"],
                     item["qty"], item["price_per_unit"], item["subtotal"]),
                )
            cursor.execute(
                "UPDATE customers SET last_order_at = ? WHERE id = ?",
                (now, customer_id),
            )
            return {"id": order_id, "customer_id": customer_id, "total_price": total_price, "status": "pending", "created_at": now}

    def get_by_id(self, order_id: str) -> dict | None:
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

    def get_by_customer(self, customer_id: str, limit: int = 10) -> list[dict]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM orders WHERE customer_id = ? ORDER BY created_at DESC LIMIT ?",
                (customer_id, limit),
            )
            return [dict(row) for row in cursor.fetchall()]

    def update_status(self, order_id: str, status: str) -> bool:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT status FROM orders WHERE id = ?", (order_id,))
            row = cursor.fetchone()
            if not row:
                return False
            current_status = row["status"]
            if status not in self.VALID_TRANSITIONS.get(current_status, []):
                return False
            now = datetime.now().isoformat()
            cursor.execute(
                "UPDATE orders SET status = ?, updated_at = ? WHERE id = ?",
                (status, now, order_id),
            )
            return True
