from langchain_core.tools import tool
from src.data.database import get_product_by_id, get_product_variants


@tool
def get_product_detail(product_id: int) -> dict | None:
    """Ambil spesifikasi lengkap produk berdasarkan product_id."""
    product = get_product_by_id(product_id)
    if not product:
        return None
    variants = get_product_variants(product_id)
    product["variants"] = [{"id": v["id"], "color": v["color"]} for v in variants]
    return product
