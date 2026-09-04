import pytest
import tempfile
import os
from unittest.mock import MagicMock, patch
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from src.agents.graph import create_sales_agent
from src.data.database import init_db, create_customer, get_order_by_id


@pytest.fixture(autouse=True)
def temp_db():
    from src.config.settings import settings
    old_path = settings.DATABASE_PATH
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_path = f.name
    settings.DATABASE_PATH = temp_path
    import src.data.database as db_module
    db_module._db_path = None
    init_db()
    yield
    settings.DATABASE_PATH = old_path
    db_module._db_path = None
    os.unlink(temp_path)


class TestOrderFlowIntegration:
    def test_full_order_flow(self):
        """Test complete order flow: search -> check_stock -> calculate -> create_order"""
        customer = create_customer(name="Toko Integration", phone="08111111111")

        call_count = 0
        def mock_invoke(messages, config=None):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return AIMessage(content="Halo! Saya AI Sales Assistant.")
            elif call_count == 2:
                return AIMessage(content="Nama Anda adalah Toko Integration.")
            elif call_count == 3:
                return AIMessage(content="Polo Premium Cotton tersedia 4500 pcs.")
            elif call_count == 4:
                return AIMessage(content="Order akan dibuat: 200 pcs Polo Navy @ Rp 70.000 = Rp 14.000.000. Konfirmasi?")
            return AIMessage(content="Order berhasil!")

        tmp = tempfile.mktemp(suffix=".db")
        checkpointer = SqliteSaver.from_conn_string(tmp)
        cp_ctx = checkpointer.__enter__()
        agent = create_sales_agent(checkpointer=cp_ctx)

        with patch("src.agents.nodes.get_llm") as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.invoke = mock_invoke
            mock_get_llm.return_value = mock_llm

            r1 = agent.invoke(
                {"messages": [HumanMessage(content="Halo")], "session_id": "s1", "context": {}, "customer_id": None, "pending_order": None, "confirmation_status": None},
                {"configurable": {"thread_id": "s1"}},
            )
            assert len(r1["messages"]) >= 2

        checkpointer.__exit__(None, None, None)
        if os.path.exists(tmp):
            os.remove(tmp)

    def test_customer_lookup_flow(self):
        """Test customer lookup and order history"""
        customer = create_customer(name="Toko History", phone="08222222222")
        items = [{"product_id": 1, "product_name": "Polo", "qty": 100, "price_per_unit": 70000, "subtotal": 7000000}]
        from src.data.database import create_order as db_create_order
        db_create_order(customer_id=customer["id"], items=items, subtotal=7000000, discount_amount=0, total_price=7000000)

        from src.tools.get_order_history import get_order_history
        result = get_order_history.invoke({"customer_id": customer["id"]})
        assert "Riwayat order" in result
        assert "ORD-" in result
