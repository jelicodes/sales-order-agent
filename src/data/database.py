"""Backward-compatible re-exports. New code should import from src.data.repos directly."""
import src.data.schema as _schema
from src.data.schema import get_connection, init_db, set_db_path  # noqa: F401
from src.data.repos.product_repo import ProductRepo  # noqa: F401
from src.data.repos.order_repo import OrderRepo  # noqa: F401
from src.data.repos.customer_repo import CustomerRepo  # noqa: F401
from src.data.repos.session_repo import SessionRepo  # noqa: F401

_product_repo = ProductRepo()
_order_repo = OrderRepo()
_customer_repo = CustomerRepo()
_session_repo = SessionRepo()


def clear_caches():
    _product_repo.clear_caches()


def search_products(query, category=None):
    return _product_repo.search(query, category)


def get_product_by_id(product_id):
    return _product_repo.get_by_id(product_id)


def get_product_variants(product_id):
    return _product_repo.get_variants(product_id)


def get_price_tier(product_id, quantity):
    return _product_repo.get_price_tier(product_id, quantity)


def get_stock_by_product(product_id):
    return _product_repo.get_stock_by_product(product_id)


def get_discount(code):
    return _product_repo.get_discount(code)


def create_session(session_id, customer_name):
    return _session_repo.create(session_id, customer_name)


def get_session(session_id):
    return _session_repo.get_by_id(session_id)


def create_quote(quote_id, session_id, items_json, total_price, valid_until):
    return _session_repo.create_quote(quote_id, session_id, items_json, total_price, valid_until)


def create_customer(name, phone=None, email=None, tier="regular"):
    return _customer_repo.create(name, phone, email, tier)


def get_customer_by_id(customer_id):
    return _customer_repo.get_by_id(customer_id)


def get_customer_by_phone(phone):
    return _customer_repo.get_by_phone(phone)


def create_order(customer_id, items, subtotal, discount_amount, total_price, shipping_address=None, notes=None):
    return _order_repo.create_order(customer_id, items, subtotal, discount_amount, total_price, shipping_address, notes)


def get_order_by_id(order_id):
    return _order_repo.get_by_id(order_id)


def get_orders_by_customer(customer_id, limit=10):
    return _order_repo.get_by_customer(customer_id, limit)


def update_order_status(order_id, status):
    return _order_repo.update_status(order_id, status)
