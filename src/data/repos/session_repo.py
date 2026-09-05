from src.data.schema import get_connection


class SessionRepo:

    def create(self, session_id: str, customer_name: str) -> dict:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sessions (id, customer_name) VALUES (?, ?)",
                (session_id, customer_name),
            )
            return {"id": session_id, "customer_name": customer_name, "status": "active"}

    def get_by_id(self, session_id: str) -> dict | None:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def create_quote(self, quote_id: str, session_id: str, items_json: str, total_price: float, valid_until: str) -> dict:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO quotes (id, session_id, items_json, total_price, valid_until) VALUES (?, ?, ?, ?, ?)",
                (quote_id, session_id, items_json, total_price, valid_until),
            )
            return {
                "id": quote_id, "session_id": session_id,
                "items_json": items_json, "total_price": total_price,
                "valid_until": valid_until, "status": "pending",
            }
