"""Tests for LLM-generated SQL validation."""
import pytest

from app.utils.sql_safety import validate_sql


@pytest.mark.parametrize("sql", [
    "SELECT * FROM customers",
    "SELECT created_at, updated_at FROM orders LIMIT 5",  # old keyword check rejected these
    "SELECT p.name, COUNT(*) c FROM products p JOIN order_items oi ON oi.product_id = p.product_id GROUP BY p.name ORDER BY c DESC LIMIT 10",
    "WITH t AS (SELECT order_id FROM orders) SELECT * FROM t",
    "SELECT * FROM orders UNION SELECT * FROM orders",
    "SELECT 1;",
])
def test_allows_safe_queries(sql):
    safe, err = validate_sql(sql)
    assert err is None, err
    assert safe


@pytest.mark.parametrize("sql", [
    "",
    "DROP TABLE orders",
    "DELETE FROM orders",
    "UPDATE orders SET status='x'",
    "SELECT 1; DROP TABLE orders",
    "SELECT * INTO newtable FROM orders",
    "SELECT * FROM orders FOR UPDATE",
    "WITH d AS (DELETE FROM orders RETURNING *) SELECT * FROM d",
    "SELECT pg_sleep(100)",
    "SELECT pg_read_file('/etc/passwd')",
    "SELECT * FROM pg_catalog.pg_user",
    "SELECT * FROM pg_shadow",
    "SELECT * FROM information_schema.tables",
    "COPY orders TO '/tmp/x'",
    "SELECT FROM WHERE",
])
def test_rejects_unsafe_queries(sql):
    safe, err = validate_sql(sql)
    assert safe is None
    assert err


def test_limit_is_added_and_capped():
    safe, _ = validate_sql("SELECT * FROM customers", max_limit=50)
    assert "LIMIT 50" in safe

    safe, _ = validate_sql("SELECT * FROM customers LIMIT 100000", max_limit=50)
    assert "LIMIT 50" in safe

    safe, _ = validate_sql("SELECT * FROM customers LIMIT 5", max_limit=50)
    assert "LIMIT 5" in safe and "LIMIT 50" not in safe


def test_union_is_wrapped_with_limit():
    safe, _ = validate_sql("SELECT order_id FROM orders UNION SELECT invoice_id FROM invoices", max_limit=20)
    assert "LIMIT 20" in safe
