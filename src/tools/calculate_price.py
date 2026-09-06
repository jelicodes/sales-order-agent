from pydantic import BaseModel, Field
from langchain_core.tools import tool
from src.data.repos.product_repo import ProductRepo

_product_repo = ProductRepo()


class CalculatePriceInput(BaseModel):
    product_id: int = Field(description="ID produk")
    quantity: int = Field(description="Jumlah pesanan")
    discount_code: str = Field(default="", description="Kode diskon (opsional)")


@tool(args_schema=CalculatePriceInput)
def calculate_price(product_id: int, quantity: int, discount_code: str = "") -> dict:
    """Hitung harga berdasarkan jumlah pesanan. Menghasilkan price table."""
    if quantity <= 0:
        return {"error": "Quantity harus lebih dari 0"}

    product = _product_repo.get_by_id(product_id)
    if not product:
        return {"error": f"Produk dengan ID {product_id} tidak ditemukan"}

    tiers = _product_repo.get_price_tiers(product_id)
    if not tiers:
        return {"error": "Tidak ada harga tersedia"}

    selected_tier = None
    for tier in tiers:
        max_qty = tier.get("max_qty") or float("inf")
        if tier["min_qty"] <= quantity <= max_qty:
            selected_tier = tier
            break

    if not selected_tier:
        selected_tier = tiers[-1]

    price_per_unit = selected_tier["price_per_unit"]
    subtotal = price_per_unit * quantity

    discount_amount = 0
    discount_info = None
    if discount_code:
        discount = _product_repo.get_discount(discount_code)
        if discount:
            if discount.get("min_qty") and quantity < discount["min_qty"]:
                discount = None
            else:
                if discount["type"] == "percentage":
                    discount_amount = subtotal * (discount["value"] / 100)
                else:
                    discount_amount = min(discount["value"], subtotal)
                discount_info = {"code": discount["code"], "type": discount["type"], "value": discount["value"]}

    total = subtotal - discount_amount

    return {
        "type": "price_breakdown",
        "data": {
            "product_id": product_id,
            "product_name": product["name"],
            "quantity": quantity,
            "price_per_unit": price_per_unit,
            "subtotal": subtotal,
            "discount": discount_info,
            "discount_amount": discount_amount,
            "total": total,
            "tiers": [
                {"min_qty": t["min_qty"], "max_qty": t.get("max_qty"), "price_per_unit": t["price_per_unit"]}
                for t in tiers
            ],
        },
    }
