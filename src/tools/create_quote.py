import json
import uuid
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from src.data.database import create_quote as db_create_quote, get_price_tier


class QuoteItem(BaseModel):
    product_id: int = Field(description="ID produk")
    quantity: int = Field(description="Jumlah pesanan")
    color: str = Field(description="Warna yang dipilih")


class CreateQuoteInput(BaseModel):
    items: list[QuoteItem] = Field(description="Daftar item pesanan")
    customer_info: dict = Field(description="Informasi customer (nama, alamat, kontak)")


@tool(args_schema=CreateQuoteInput)
def create_quote(items: list[dict], customer_info: dict) -> dict:
    """Buat penawaran harga final. Masukkan list item [{product_id, quantity, color}] dan customer_info."""
    quote_items = []
    total_price = 0
    for item in items:
        tier = get_price_tier(item.product_id, item.quantity)
        if tier:
            item_total = tier["price_per_unit"] * item.quantity
            quote_items.append({"product_id": item.product_id, "quantity": item.quantity, "color": item.color, "price_per_unit": tier["price_per_unit"], "subtotal": item_total})
            total_price += item_total
    short_id = uuid.uuid4().hex[:8].upper()
    quote_id = f"Q-{datetime.now().strftime('%Y-%m-%d')}-{short_id}"
    valid_until = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    result = db_create_quote(quote_id=quote_id, session_id="", items_json=json.dumps(quote_items), total_price=total_price, valid_until=valid_until)
    return {
        "quote_id": quote_id, "items": quote_items, "total_price": total_price,
        "formatted_total": f"Rp {total_price:,.0f}".replace(",", "."),
        "valid_until": valid_until, "customer_info": customer_info,
    }
