"""Built-in sample dataset, served from an in-memory SQLite database built from CSV files.

It is only shown while a user has no connection of their own. It is never written to by
users, and connecting a real database replaces it in the UI for that user.
"""

import csv
import logging
import threading
import time
from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.connectors.graph_from_db import build_graph
from app.connectors.introspect import introspect
from app.connectors.sessions import DbSession

logger = logging.getLogger(__name__)

DDL = [
    "CREATE TABLE customers (customer_id TEXT PRIMARY KEY, name TEXT, email TEXT, segment TEXT)",
    "CREATE TABLE products (product_id TEXT PRIMARY KEY, name TEXT, category TEXT, price REAL, description TEXT)",
    "CREATE TABLE addresses (address_id TEXT PRIMARY KEY, street TEXT, city TEXT, state TEXT, postal_code TEXT, country TEXT, address_type TEXT)",
    "CREATE TABLE orders (order_id TEXT PRIMARY KEY, customer_id TEXT REFERENCES customers(customer_id), order_date TEXT, status TEXT, total_amount REAL)",
    "CREATE TABLE order_items (id INTEGER PRIMARY KEY, order_id TEXT REFERENCES orders(order_id), product_id TEXT REFERENCES products(product_id), quantity INTEGER, unit_price REAL, subtotal REAL)",
    "CREATE TABLE invoices (invoice_id TEXT PRIMARY KEY, order_id TEXT REFERENCES orders(order_id), invoice_date TEXT, due_date TEXT, amount REAL, status TEXT)",
    "CREATE TABLE payments (payment_id TEXT PRIMARY KEY, invoice_id TEXT REFERENCES invoices(invoice_id), payment_date TEXT, amount REAL, method TEXT, transaction_id TEXT, status TEXT)",
    "CREATE TABLE deliveries (delivery_id TEXT PRIMARY KEY, order_id TEXT REFERENCES orders(order_id), delivery_date TEXT, status TEXT, tracking_number TEXT, address_id TEXT REFERENCES addresses(address_id))",
]
LOAD_ORDER = [
    "customers",
    "products",
    "addresses",
    "orders",
    "order_items",
    "invoices",
    "payments",
    "deliveries",
]

_lock = threading.Lock()
_demo: Optional[DbSession] = None
_tried = False


def _build(data_dir: Path) -> Optional[DbSession]:
    if not all((data_dir / f"{t}.csv").exists() for t in LOAD_ORDER):
        return None

    engine = create_engine(
        "sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    with engine.begin() as conn:
        for stmt in DDL:
            conn.execute(text(stmt))
        for table in LOAD_ORDER:
            with open(data_dir / f"{table}.csv", newline="", encoding="utf-8") as f:
                rows = [
                    {k: (v if v != "" else None) for k, v in r.items()}
                    for r in csv.DictReader(f)
                ]
            if rows:
                cols = list(rows[0])
                conn.execute(
                    text(
                        f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join(':' + c for c in cols)})"
                    ),
                    rows,
                )
    # Loaded: from now on the shared connection refuses writes
    with engine.connect() as conn:
        conn.exec_driver_sql("PRAGMA query_only = ON")

    schema = introspect(engine, settings.max_tables)
    graph = build_graph(
        engine, schema, settings.max_rows_per_table, settings.max_graph_nodes
    )
    return DbSession(
        token="__demo__",
        engine=engine,
        dialect="sqlite",
        backend="sqlite",
        database="sample data",
        schema=schema,
        graph=graph,
        expires_at=float("inf"),
    )


def get_demo() -> Optional[DbSession]:
    """The sample dataset session, built lazily; None if the CSV files are missing."""
    global _demo, _tried
    with _lock:
        if not _tried:
            _tried = True
            try:
                _demo = _build(Path(settings.sample_data_dir))
                if _demo:
                    logger.info(
                        "Sample data loaded: %d nodes", _demo.graph.number_of_nodes()
                    )
            except Exception:
                logger.exception("Could not build sample data")
        return _demo


def reset_for_tests() -> None:
    global _demo, _tried
    with _lock:
        _demo, _tried = None, False
