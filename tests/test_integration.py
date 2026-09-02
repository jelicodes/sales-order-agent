import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


class TestFullFlow:
    def test_inquiry_to_quote_flow(self):
        resp1 = client.post("/chat", json={
            "message": "Saya butuh 500 kaos polo hitam untuk seragam karyawan",
            "customer_name": "Budi Santoso"
        })
        assert resp1.status_code == 200
        data1 = resp1.json()
        session_id = data1["session_id"]
        assert "polo" in data1["response"].lower() or "kaos" in data1["response"].lower()

        resp2 = client.post("/chat", json={
            "message": "Yang Premium, bisa warna navy?",
            "session_id": session_id
        })
        assert resp2.status_code == 200
        assert "navy" in resp2.json()["response"].lower() or "premium" in resp2.json()["response"].lower()

        resp3 = client.post("/chat", json={
            "message": "Buatkan penawaran untuk 500 pcs navy",
            "session_id": session_id
        })
        assert resp3.status_code == 200
        assert "rp" in resp3.json()["response"].lower() or "penawaran" in resp3.json()["response"].lower()


class TestEdgeCases:
    def test_unknown_product(self):
        resp = client.post("/chat", json={
            "message": "Saya cari jas formal pria",
            "customer_name": "Test"
        })
        assert resp.status_code == 200
        assert resp.json()["response"] is not None

    def test_budget_too_low(self):
        resp = client.post("/chat", json={
            "message": "Saya mau 500 kaos polo, budget cuma 10 juta",
            "customer_name": "Test"
        })
        assert resp.status_code == 200
        assert resp.json()["response"] is not None
