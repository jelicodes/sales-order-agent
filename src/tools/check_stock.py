from langchain_core.tools import tool
from src.data.database import get_stock_by_product


@tool
def check_stock(product_id: int, quantity: int) -> dict:
    """Cek ketersediaan stok produk. Masukkan product_id dan jumlah yang dibutuhkan."""
    variants = get_stock_by_product(product_id)
    if not variants:
        return {"available": False, "stock": 0, "message": "Produk tidak ditemukan"}
    total_stock = sum(v["quantity"] for v in variants)
    available = total_stock >= quantity
    return {
        "available": available,
        "total_stock": total_stock,
        "variants": [{"color": v["color"], "quantity": v["quantity"], "warehouse": v["warehouse_location"]} for v in variants],
        "message": f"Stok mencukupi ({total_stock} tersedia)" if available else f"Stok tidak cukup. Tersedia: {total_stock}, dibutuhkan: {quantity}"
    }
