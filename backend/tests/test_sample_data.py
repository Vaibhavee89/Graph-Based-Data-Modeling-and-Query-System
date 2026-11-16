"""Built-in sample data: loaded from CSV, shown by default, replaced when a user connects."""
from unittest.mock import patch

import networkx as nx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.config import settings
from app.connectors import demo as demo_mod
from app.connectors import sessions as sessions_mod
from app.core.rate_limit import RateLimiter
from app.main import app
from app.routers import connect as connect_router


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "allow_sqlite_connections", True)
    monkeypatch.setattr(connect_router, "_connect_limiter", RateLimiter(limit=100))
    demo_mod.reset_for_tests()
    sessions_mod.sessions._sessions.clear()
    # no legacy (Postgres-model) graph in these tests
    with patch("app.routers.graph.get_graph", return_value=nx.DiGraph()), \
         patch("app.routers.query.get_graph", return_value=nx.DiGraph()):
        yield TestClient(app)


def test_sample_csvs_become_a_connected_graph(client):
    ov = client.get("/api/graph/overview").json()
    assert ov["node_types"] == {
        "customers": 10, "products": 20, "addresses": 15, "orders": 40,
        "order_items": 141, "invoices": 32, "payments": 27, "deliveries": 31,
    }
    # every foreign key resolves: orders->customers, items->orders/products, invoices->orders, ...
    assert ov["edge_types"]["orders->customers"] == 40
    assert ov["edge_types"]["payments->invoices"] == 27
    assert client.get("/api/connect/config").json()["sample_data_available"] is True


def test_sample_data_is_read_only(client):
    demo = demo_mod.get_demo()
    with demo.engine.connect() as c, pytest.raises(Exception):
        c.execute(text("DELETE FROM customers"))
    with demo.engine.connect() as c:
        assert c.execute(text("SELECT COUNT(*) FROM customers")).scalar() == 10


def test_connecting_replaces_sample_and_disconnect_restores_it(client, tmp_path):
    path = tmp_path / "mine.db"
    e = create_engine(f"sqlite:///{path}")
    with e.begin() as c:
        c.execute(text("CREATE TABLE pets (id INTEGER PRIMARY KEY, name TEXT)"))
        c.execute(text("INSERT INTO pets VALUES (1,'Rex')"))

    sample = client.get("/api/graph/overview").json()
    r = client.post("/api/connect", json={"url": f"sqlite:///{path}"})
    assert r.status_code == 200
    h = {"X-Session-Id": r.json()["session_id"]}

    mine = client.get("/api/graph/overview", headers=h).json()
    assert mine["node_types"] == {"pets": 1}                       # their data only, none of the sample
    assert "customers" not in client.get("/api/graph/export", headers=h).text
    assert client.get("/api/graph/overview").json() == sample      # others still see the sample

    client.delete("/api/connect", headers=h)
    assert client.get("/api/graph/overview").json() == sample      # disconnect returns to sample


def test_questions_about_sample_data_run_through_generic_service(client):
    llm = {"sql": "SELECT status, COUNT(*) AS n FROM orders GROUP BY status ORDER BY n DESC", "explanation": "orders by status"}
    with patch("app.connectors.query.GuardrailService.validate_query") as g, \
         patch("app.connectors.query.LLMService.generate_structured", return_value=llm):
        g.return_value.is_valid, g.return_value.reason, g.return_value.service_error = True, "ok", False
        r = client.post("/api/query/chat", json={"query": "orders by status"})
    body = r.json()
    assert body["success"] is True and sum(row["n"] for row in body["data"]) == 40


def test_missing_sample_files_disable_demo_gracefully(client, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "sample_data_dir", str(tmp_path))
    demo_mod.reset_for_tests()
    assert client.get("/api/connect/config").json()["sample_data_available"] is False


def test_starter_view_is_connected_and_mixed(client):
    d = client.get("/api/graph/starter?limit=40").json()
    types = {n["type"] for n in d["nodes"]}
    assert len(d["nodes"]) == 40 and len(types) >= 4          # several entity types, not one table
    ids = {n["id"] for n in d["nodes"]}
    assert d["edges"] and all(e["source"] in ids and e["target"] in ids for e in d["edges"])
    assert client.get("/api/graph/starter?limit=0").status_code == 422
    assert client.get("/api/graph/starter?limit=9999").status_code == 422


def test_focus_resolves_plain_ids_and_returns_neighbours(client):
    # chat text says "ORD-008", the graph node is "orders:ORD-008"
    r = client.get("/api/graph/focus/ORD-008")
    assert r.status_code == 200
    d = r.json()
    assert d["node_id"] == "orders:ORD-008"
    ids = {n["id"] for n in d["nodes"]}
    assert "orders:ORD-008" in ids and len(ids) > 1
    assert all(e["source"] in ids and e["target"] in ids for e in d["edges"])
    # exact ids and different casing work too; unknown ids are a clean 404
    assert client.get("/api/graph/focus/orders:ORD-008").json()["node_id"] == "orders:ORD-008"
    assert client.get("/api/graph/focus/ord-008").json()["node_id"] == "orders:ORD-008"
    assert client.get("/api/graph/focus/ORD-999").status_code == 404
