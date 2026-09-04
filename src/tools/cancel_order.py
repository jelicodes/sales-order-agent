from langchain_core.tools import tool
from src.data.database import update_order_status


@tool
def cancel_order(order_id: str) -> str:
    """Batalkan order berdasarkan order_id. Hanya bisa dibatalkan jika status pending atau confirmed."""
    success = update_order_status(order_id, "cancelled")
    if success:
        return f"Order {order_id} berhasil dibatalkan"
    return f"Error: Order {order_id} tidak bisa dibatalkan (mungkin sudah diproses atau tidak ditemukan)"
