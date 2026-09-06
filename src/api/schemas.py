from pydantic import BaseModel, Field


class ProductCardData(BaseModel):
    type: str = Field(default="product_card")
    product_id: int
    name: str
    category: str
    price: int
    moq: int
    stock: int
    image_url: str = ""
    description: str = ""


class ProductCardsData(BaseModel):
    type: str = Field(default="product_cards")
    cards: list[ProductCardData]


class PriceTier(BaseModel):
    min_qty: int
    max_qty: int | None
    price_per_unit: int


class PriceTableData(BaseModel):
    type: str = Field(default="price_table")
    product_id: int
    product_name: str
    tiers: list[PriceTier]
    selected_qty: int | None = None


class OrderItem(BaseModel):
    product_id: int
    product_name: str
    qty: int
    price_per_unit: int
    subtotal: int


class OrderSummaryData(BaseModel):
    type: str = Field(default="order_summary")
    order_id: str
    items: list[OrderItem]
    subtotal: int
    total_price: int
    status: str = "pending"
    customer_name: str = ""


class ReorderItem(BaseModel):
    product_id: int
    product_name: str
    last_qty: int
    last_price: int
    last_order_date: str
    image_url: str = ""


class ReorderSuggestionsData(BaseModel):
    type: str = Field(default="reorder_suggestions")
    customer_name: str
    items: list[ReorderItem]


UIToolOutput = ProductCardsData | PriceTableData | OrderSummaryData | ReorderSuggestionsData
