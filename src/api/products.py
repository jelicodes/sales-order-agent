from fastapi import APIRouter
from src.data.schema import get_db_connection

router = APIRouter()


@router.get("/api/products")
def get_products():
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            "SELECT id, name, category, base_price, moq, description, image_url FROM products ORDER BY id"
        )
        rows = cursor.fetchall()
        return [
            {
                "id": row["id"],
                "name": row["name"],
                "category": row["category"],
                "base_price": row["base_price"],
                "moq": row["moq"],
                "description": row["description"],
                "image_url": row["image_url"] or "",
            }
            for row in rows
        ]
    finally:
        conn.close()
