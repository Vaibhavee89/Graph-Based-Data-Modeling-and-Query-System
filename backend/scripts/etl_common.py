"""Shared helpers for the ETL scripts."""
from typing import Callable, Dict, List

import pandas as pd
from sqlalchemy.orm import Session

from app.models import (
    Customer, Product, Order, OrderItem,
    Invoice, Payment, Delivery, Address
)

# Load order respects foreign keys; delete order is the reverse.
LOAD_ORDER = [
    ("customers", Customer),
    ("products", Product),
    ("addresses", Address),
    ("orders", Order),
    ("order_items", OrderItem),
    ("invoices", Invoice),
    ("payments", Payment),
    ("deliveries", Delivery),
]


def df_to_records(df: pd.DataFrame) -> List[dict]:
    """Convert a DataFrame to dicts, turning NaN/NaT into None."""
    if df is None or df.empty:
        return []
    clean = df.astype(object).where(pd.notna(df), None)
    return clean.to_dict(orient="records")


def load_all(db: Session, frames: Dict[str, pd.DataFrame], log: Callable[[str], None]) -> None:
    """
    Replace all table contents with the given frames in ONE transaction.

    Any failure rolls everything back, so the database is never left half-empty.
    """
    try:
        log("Clearing existing data...")
        for _, model in reversed(LOAD_ORDER):
            db.query(model).delete()

        for name, model in LOAD_ORDER:
            records = df_to_records(frames.get(name))
            log(f"Loading {name}...")
            if records:
                db.bulk_insert_mappings(model, records)
            log(f"  ✓ Loaded {len(records)} {name}")

        db.commit()
    except Exception:
        db.rollback()
        raise
