import uuid
from datetime import datetime

from src.data.schema import get_connection


class CustomerRepo:

    def create(self, name: str, phone: str | None = None, email: str | None = None, tier: str = "regular") -> dict:
        customer_id = f"CUST-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now().isoformat()
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO customers (id, name, phone, email, tier, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (customer_id, name, phone, email, tier, now),
            )
            return {"id": customer_id, "name": name, "phone": phone, "email": email, "tier": tier, "created_at": now}

    def get_by_id(self, customer_id: str) -> dict | None:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_by_phone(self, phone: str) -> dict | None:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM customers WHERE phone = ?", (phone,))
            row = cursor.fetchone()
            return dict(row) if row else None
