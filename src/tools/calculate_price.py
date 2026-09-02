from langchain_core.tools import tool
from src.data.database import get_price_tier, get_discount


@tool
def calculate_price(product_id: int, quantity: int, discount_code: str = "") -> dict:
    """Hitung harga berdasarkan jumlah pesanan, tier harga, dan diskon yang berlaku."""
    tier = get_price_tier(product_id, quantity)
    if not tier:
        return {"error": "Tidak ada harga tersedia untuk quantity ini"}
    price_per_unit = tier["price_per_unit"]
    subtotal = price_per_unit * quantity
    discount_amount = 0
    discount_info = None
    if discount_code:
        discount = get_discount(discount_code)
        if discount:
            if discount["type"] == "percentage":
                discount_amount = subtotal * (discount["value"] / 100)
            else:
                discount_amount = min(discount["value"], subtotal)
            discount_info = {"code": discount["code"], "type": discount["type"], "value": discount["value"]}
    total = subtotal - discount_amount
    return {
        "product_id": product_id, "quantity": quantity,
        "price_per_unit": price_per_unit, "subtotal": subtotal,
        "discount": discount_info, "discount_amount": discount_amount,
        "total": total, "tier": f"{tier['min_qty']}-{tier['max_qty'] or '∞'} pcs"
    }
