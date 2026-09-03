from pydantic import BaseModel, Field
from langchain_core.tools import tool
from src.data.database import get_price_tier, get_discount


class CalculatePriceInput(BaseModel):
    product_id: int = Field(description="ID produk")
    quantity: int = Field(description="Jumlah pesanan")
    discount_code: str = Field(default="", description="Kode diskon (opsional)")


@tool(args_schema=CalculatePriceInput)
def calculate_price(product_id: int, quantity: int, discount_code: str = "") -> dict:
    """Hitung harga berdasarkan jumlah pesanan, tier harga, dan diskon yang berlaku."""
    if quantity <= 0:
        return {
            "product_id": product_id, "quantity": quantity,
            "price_per_unit": 0, "subtotal": 0,
            "discount": None, "discount_amount": 0,
            "total": 0, "tier": "N/A"
        }
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
            # Validate min_qty requirement
            if discount.get("min_qty") and quantity < discount["min_qty"]:
                discount = None  # Don't apply discount if min_qty not met
            else:
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
