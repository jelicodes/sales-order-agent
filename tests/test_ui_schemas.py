from src.api.schemas import (
    ProductCardData, ProductCardsData, PriceTableData,
    PriceTier, OrderSummaryData, OrderItem,
    ReorderSuggestionsData, ReorderItem,
)


def test_product_card_serializes():
    card = ProductCardData(
        product_id=1, name="Kemeja Flanel", category="Kemeja",
        price=85000, moq=12, stock=500, image_url="/img/kemeja.jpg"
    )
    d = card.model_dump()
    assert d["type"] == "product_card"
    assert d["price"] == 85000


def test_price_table_serializes():
    table = PriceTableData(
        product_id=1, product_name="Kemeja Flanel",
        tiers=[PriceTier(min_qty=1, max_qty=11, price_per_unit=85000)],
        selected_qty=50,
    )
    d = table.model_dump()
    assert d["type"] == "price_table"
    assert len(d["tiers"]) == 1


def test_order_summary_serializes():
    summary = OrderSummaryData(
        order_id="ORD-20260905-ABCD",
        items=[OrderItem(product_id=1, product_name="Kemeja", qty=100, price_per_unit=75000, subtotal=7500000)],
        subtotal=7500000, total_price=7500000, status="pending", customer_name="Budi"
    )
    d = summary.model_dump()
    assert d["type"] == "order_summary"
    assert d["total_price"] == 7500000


def test_reorder_suggestions_serializes():
    reorder = ReorderSuggestionsData(
        customer_name="Budi",
        items=[ReorderItem(product_id=1, product_name="Kemeja", last_qty=100, last_price=75000, last_order_date="2026-08-01", image_url="")]
    )
    d = reorder.model_dump()
    assert d["type"] == "reorder_suggestions"
    assert len(d["items"]) == 1
