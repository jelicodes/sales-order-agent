import pytest
import tempfile
import os
import json
from pathlib import Path


@pytest.fixture(autouse=True)
def seeded_db():
    from src.config.settings import settings
    from src.data.database import init_db, get_connection
    from src.data.schema import set_db_path

    old_path = settings.DATABASE_PATH
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_path = f.name
    settings.DATABASE_PATH = temp_path
    set_db_path(None)

    init_db()

    seed_dir = Path(__file__).parent.parent / "src" / "data" / "seed"

    def load_json(filename):
        with open(seed_dir / filename) as f:
            return json.load(f)

    products = load_json("products.json")
    price_tiers_raw = load_json("price_tiers.json")
    stock_raw = load_json("stock.json")
    discounts = load_json("discounts.json")

    with get_connection() as conn:
        cursor = conn.cursor()

        for p in products:
            cursor.execute(
                "INSERT INTO products (id, name, category, description, base_price, moq, lead_time_days) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (p["id"], p["name"], p["category"], p["description"], p["base_price"], p["moq"], p["lead_time_days"]),
            )

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

        for pt in price_tiers_raw:
            for tier in pt["tiers"]:
                cursor.execute(
                    "INSERT INTO price_tiers (product_id, min_qty, max_qty, price_per_unit) VALUES (?, ?, ?, ?)",
                    (pt["product_id"], tier["min_qty"], tier["max_qty"], tier["price_per_unit"]),
                )

        for d in discounts:
            cursor.execute(
                "INSERT INTO discounts (code, type, value, min_qty, valid_until) VALUES (?, ?, ?, ?, ?)",
                (d["code"], d["type"], d["value"], d["min_qty"], d["valid_until"]),
            )

    yield

    settings.DATABASE_PATH = old_path
    set_db_path(None)
    os.unlink(temp_path)


from src.data.database import (
    search_products, get_product_by_id,
    get_product_variants, get_price_tier, get_stock_by_product,
    create_session, get_session,
    create_quote, get_discount, init_db, get_connection,
)


class TestDatabaseExtended:
    def test_init_db_idempotent(self):
        init_db()
        init_db()

    def test_search_products_by_category(self):
        results = search_products("", "Kaos")
        assert len(results) > 0
        assert all(r["category"] == "Kaos" for r in results)

    def test_get_product_variants(self):
        variants = get_product_variants(1)
        assert len(variants) > 0
        assert "color" in variants[0]

    def test_get_price_tier_boundary_99(self):
        tier = get_price_tier(1, 99)
        assert tier is not None
        assert tier["price_per_unit"] == 85000

    def test_get_price_tier_boundary_100(self):
        tier = get_price_tier(1, 100)
        assert tier is not None
        assert tier["price_per_unit"] == 80000

    def test_get_stock_by_product(self):
        stock = get_stock_by_product(1)
        assert len(stock) > 0
        assert "quantity" in stock[0]

    def test_get_discount_valid(self):
        discount = get_discount("BULK500")
        assert discount is not None
        assert discount["type"] == "percentage"

    def test_get_discount_invalid(self):
        discount = get_discount("NONEXISTENT")
        assert discount is None


