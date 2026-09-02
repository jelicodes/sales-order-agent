import json
from pathlib import Path
from src.data.database import init_db, get_connection
from src.data.vector_store import index_products

SEED_DIR = Path(__file__).parent


def load_json(filename: str) -> list[dict]:
    with open(SEED_DIR / filename) as f:
        return json.load(f)


def seed_database() -> None:
    init_db()

    products = load_json("products.json")
    price_tiers_raw = load_json("price_tiers.json")
    stock_raw = load_json("stock.json")
    discounts = load_json("discounts.json")

    conn = get_connection()
    cursor = conn.cursor()

    # Clear existing data
    for table in ("stock", "product_variants", "price_tiers", "discounts", "products"):
        cursor.execute(f"DELETE FROM {table}")

    # Insert products
    for p in products:
        cursor.execute(
            "INSERT INTO products (id, name, category, description, base_price, moq, lead_time_days) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (p["id"], p["name"], p["category"], p["description"], p["base_price"], p["moq"], p["lead_time_days"]),
        )

    # Insert product_variants + stock
    for entry in stock_raw:
        for v in entry["variants"]:
            cursor.execute(
                "INSERT INTO product_variants (product_id, color) VALUES (?, ?)",
                (entry["product_id"], v["color"]),
            )
            variant_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO stock (variant_id, quantity, warehouse_location) VALUES (?, ?, ?)",
                (variant_id, v["quantity"], v["warehouse"]),
            )

    # Insert price tiers
    for pt in price_tiers_raw:
        for tier in pt["tiers"]:
            cursor.execute(
                "INSERT INTO price_tiers (product_id, min_qty, max_qty, price_per_unit) VALUES (?, ?, ?, ?)",
                (pt["product_id"], tier["min_qty"], tier["max_qty"], tier["price_per_unit"]),
            )

    # Insert discounts
    for d in discounts:
        cursor.execute(
            "INSERT INTO discounts (code, type, value, min_qty, valid_until) VALUES (?, ?, ?, ?, ?)",
            (d["code"], d["type"], d["value"], d["min_qty"], d["valid_until"]),
        )

    conn.commit()
    conn.close()

    # Index products in ChromaDB with Gemini embeddings
    index_products(products)
    print(f"Seeded {len(products)} products, {len(price_tiers_raw)} price tiers, {len(stock_raw)} stock entries, {len(discounts)} discounts")


if __name__ == "__main__":
    seed_database()
