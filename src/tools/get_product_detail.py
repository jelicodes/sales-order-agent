from pydantic import BaseModel, Field
from langchain_core.tools import tool
from src.data.repos.product_repo import ProductRepo

_product_repo = ProductRepo()


class GetProductDetailInput(BaseModel):
    product_id: int = Field(description="ID produk yang ingin dilihat detailnya")


@tool(args_schema=GetProductDetailInput)
def get_product_detail(product_id: int) -> dict | None:
    """Ambil spesifikasi lengkap produk berdasarkan product_id."""
    product = _product_repo.get_by_id(product_id)
    if not product:
        return None
    variants = _product_repo.get_variants(product_id)
    product["variants"] = [{"id": v["id"], "color": v["color"]} for v in variants]
    return product
