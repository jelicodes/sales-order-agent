from pydantic import BaseModel, Field
from langchain_core.tools import tool
from src.data.database import get_product_by_id, get_product_variants


class GetProductDetailInput(BaseModel):
    product_id: int = Field(description="ID produk yang ingin dilihat detailnya")


@tool(args_schema=GetProductDetailInput)
def get_product_detail(product_id: int) -> dict | None:
    """Ambil spesifikasi lengkap produk berdasarkan product_id."""
    product = get_product_by_id(product_id)
    if not product:
        return None
    variants = get_product_variants(product_id)
    product["variants"] = [{"id": v["id"], "color": v["color"]} for v in variants]
    return product
