"""Tests for bring-your-own-database connections (exercised against SQLite)."""
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.config import settings
from app.connectors import sessions as sessions_mod
from app.connectors.url_safety import UnsafeURL, parse_and_check
from app.main import app
from app.routers import connect as connect_router
from app.core.rate_limit import RateLimiter


@pytest.fixture
def db_url(tmp_path):
    path = tmp_path / "shop.db"
    e = create_engine(f"sqlite:///{path}")
    with e.begin() as c:
        c.execute(text("CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT)"))
        c.execute(text("CREATE TABLE orders (id INTEGER PRIMARY KEY, customer_id INTEGER REFERENCES customers(id), total REAL, placed TEXT)"))
        c.execute(text("INSERT INTO customers VALUES (1,'Ada'),(2,'Grace')"))
        c.execute(text("INSERT INTO orders VALUES (10,1,5.5,'2024-01-01 12:30'),(11,1,7,'2024-01-02 09:00'),(12,2,3,'2024-01-03 10:00')"))
    return f"sqlite:///{path}"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(settings, "allow_sqlite_connections", True)
    monkeypatch.setattr(settings, "access_code", None)
    monkeypatch.setattr(connect_router, "_connect_limiter", RateLimiter(limit=100))
    sessions_mod.sessions._sessions.clear()
    return TestClient(app)


def test_connect_builds_graph_from_foreign_keys(client, db_url):
    r = client.post("/api/connect", json={"url": db_url})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["tables"] == 2 and body["nodes"] == 5 and body["edges"] == 3
    h = {"X-Session-Id": body["session_id"]}

    ov = client.get("/api/graph/overview", headers=h).json()
    assert ov["node_types"] == {"customers": 2, "orders": 3}
    assert ov["edge_types"] == {"orders->customers": 3}

    nodes = client.get("/api/graph/nodes?node_type=customers", headers=h).json()
    assert {n["label"] for n in nodes} == {"Ada", "Grace"}

    exp = client.post("/api/graph/nodes/customers:1/expand", json={"depth": 1}, headers=h).json()
    assert len(exp["nodes"]) == 3  # Ada + her two orders


def test_session_is_isolated_and_expires(client, db_url):
    sid = client.post("/api/connect", json={"url": db_url}).json()["session_id"]
    client.delete("/api/connect", headers={"X-Session-Id": sid})
    r = client.get("/api/graph/overview", headers={"X-Session-Id": sid})
    assert r.status_code == 401


def test_query_runs_generated_sql_read_only(client, db_url):
    sid = client.post("/api/connect", json={"url": db_url}).json()["session_id"]
    h = {"X-Session-Id": sid}
    llm = {"sql": "SELECT c.name, SUM(o.total) AS spent FROM customers c JOIN orders o ON o.customer_id=c.id WHERE o.placed > '2024-01-01 00:00' GROUP BY c.name ORDER BY spent DESC",
           "explanation": "Spend per customer"}
    with patch("app.connectors.query.GuardrailService.validate_query") as g, \
         patch("app.connectors.query.LLMService.generate_structured", return_value=llm):
        g.return_value.is_valid, g.return_value.reason, g.return_value.service_error = True, "ok", False
        r = client.post("/api/query/chat", json={"query": "spend per customer"}, headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True, body
    assert body["data"][0]["name"] == "Ada"  # the ':' in '12:30' literal must not break binding

    # destructive SQL from the model is refused and nothing changes
    llm = {"sql": "DELETE FROM customers", "explanation": "x"}
    with patch("app.connectors.query.GuardrailService.validate_query") as g, \
         patch("app.connectors.query.LLMService.generate_structured", return_value=llm):
        g.return_value.is_valid, g.return_value.reason, g.return_value.service_error = True, "ok", False
        r = client.post("/api/query/chat", json={"query": "wipe"}, headers=h)
    assert r.json()["success"] is False
    n = client.get("/api/graph/overview", headers=h).json()["node_types"]["customers"]
    assert n == 2


def test_sqlite_connection_pragma_blocks_writes(client, db_url):
    from app.connectors.sessions import sessions
    s = sessions.get(client.post("/api/connect", json={"url": db_url}).json()["session_id"])
    with s.engine.connect() as c, pytest.raises(Exception):
        c.execute(text("DELETE FROM customers"))


def test_access_code_required_when_configured(client, db_url, monkeypatch):
    monkeypatch.setattr(settings, "access_code", "letmein")
    assert client.post("/api/connect", json={"url": db_url}).status_code == 401
    assert client.post("/api/connect", json={"url": db_url}, headers={"X-Access-Code": "nope"}).status_code == 401
    assert client.post("/api/connect", json={"url": db_url}, headers={"X-Access-Code": "letmein"}).status_code == 200


def test_connection_errors_do_not_leak_details(client):
    r = client.post("/api/connect", json={"url": "sqlite:////nonexistent_dir/x.db"})
    assert r.status_code == 400
    assert "nonexistent" not in r.text


@pytest.mark.parametrize("url", [
    "postgresql://u:p@127.0.0.1:5432/db",
    "mysql://u:p@localhost/db",
    "postgresql://u:p@169.254.169.254/db",
    "postgresql://u:p@10.0.0.5/db",
    "mssql://u:p@192.168.1.10/db",
    "postgresql://u:p@example.com/db?host=/var/run",
    "mongodb://u:p@example.com/db",
    "not a url",
])
def test_unsafe_urls_rejected(url, monkeypatch):
    monkeypatch.setattr(settings, "allow_private_hosts", False)
    with pytest.raises(UnsafeURL):
        parse_and_check(url)


def test_sqlite_disabled_by_default(monkeypatch):
    monkeypatch.setattr(settings, "allow_sqlite_connections", False)
    with pytest.raises(UnsafeURL):
        parse_and_check("sqlite:////etc/passwd")


def test_scheme_to_driver_mapping(monkeypatch):
    monkeypatch.setattr(settings, "allow_private_hosts", True)
    for raw, driver, dialect in [
        ("postgres://u:p@h/db", "postgresql+psycopg2", "postgres"),
        ("mysql://u:p@h/db", "mysql+pymysql", "mysql"),
        ("mariadb://u:p@h/db", "mysql+pymysql", "mysql"),
        ("mssql://u:p@h/db", "mssql+pymssql", "tsql"),
        ("oracle://u:p@h:1521/?service_name=x", "oracle+oracledb", "oracle"),
    ]:
        try:
            url, d, _ = parse_and_check(raw)
        except UnsafeURL as e:
            pytest.fail(f"{raw}: {e}")
        assert url.drivername == driver and d == dialect


def test_postgres_read_only_settings_are_committed():
    """Regression: psycopg2 runs the SETs in a transaction; without a commit the pool's rollback reverts them."""
    from unittest.mock import MagicMock
    from sqlalchemy import create_engine
    from app.connectors.sessions import _install_read_only

    engine = create_engine("sqlite://")
    handlers = []
    from sqlalchemy import event
    real = event.listens_for
    try:
        event.listens_for = lambda target, name: (lambda fn: handlers.append(fn) or fn)
        _install_read_only(engine, "postgresql")
    finally:
        event.listens_for = real
    conn = MagicMock()
    handlers[0](conn, None)
    statements = [c.args[0] for c in conn.cursor.return_value.execute.call_args_list]
    assert "SET default_transaction_read_only = on" in statements
    assert any(s.startswith("SET statement_timeout") for s in statements)
    conn.commit.assert_called_once()


@pytest.mark.parametrize("url", [
    # exactly what Neon's dashboard gives you
    "postgresql://user:pw@ep-cool-123.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require",
    # Supabase pooler
    "postgresql://postgres.abcdefgh:pw@aws-0-us-east-1.pooler.supabase.com:6543/postgres",
    "postgresql://user:pw@host.example.com:5432/db?sslmode=require",
])
def test_hosted_postgres_connection_strings_are_accepted(url, monkeypatch):
    monkeypatch.setattr(settings, "allow_private_hosts", True)   # skip DNS for made-up hosts
    parsed, dialect, backend = parse_and_check(url)
    assert dialect == "postgres" and backend == "postgresql"
