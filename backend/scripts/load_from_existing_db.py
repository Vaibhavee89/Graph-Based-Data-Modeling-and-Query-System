"""
Load data from an existing database into the graph system.

This script shows how to connect to your existing database
and map it to the graph system's schema.
"""
import sys
from pathlib import Path
from sqlalchemy import create_engine, MetaData, Table, select
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.models import (
    Customer, Product, Order, OrderItem,
    Invoice, Payment, Delivery, Address
)


def load_from_existing_database():
    """
    Load data from your existing database.

    Customize this function to match your database schema.
    """

    # Step 1: Connect to YOUR existing database
    # Replace with your actual database connection string
    existing_db_url = "postgresql://user:password@your-server:5432/your-existing-db"
    source_engine = create_engine(existing_db_url)
    source_metadata = MetaData()

    # Step 2: Connect to graph system database
    target_db = SessionLocal()

    try:
        print("🔄 Loading data from existing database...")

        # Step 3: Load your existing tables
        # Example: Your existing customers table
        customers_table = Table('your_customers_table', source_metadata, autoload_with=source_engine)

        with source_engine.connect() as conn:
            # Fetch data from your existing table
            result = conn.execute(select(customers_table))

            print("  Loading customers...")
            for row in result:
                # Map YOUR fields to OUR model
                customer = Customer(
                    customer_id=str(row.id),  # Your field → Our field
                    name=row.customer_name,   # Your field → Our field
                    email=row.email_address,  # Your field → Our field
                    segment=row.customer_type # Your field → Our field
                )
                target_db.add(customer)

            # Commit customers
            target_db.commit()
            print(f"  ✓ Loaded {target_db.query(Customer).count()} customers")

        # Step 4: Load other entities (orders, products, etc.)
        # Repeat the pattern above for each entity type

        print("\n✅ Data loaded successfully!")

    except Exception as e:
        print(f"❌ Error: {e}")
        target_db.rollback()
        raise
    finally:
        target_db.close()


# Example mapping configurations
FIELD_MAPPINGS = {
    'customers': {
        'source_table': 'your_customers_table',
        'fields': {
            'id': 'customer_id',
            'customer_name': 'name',
            'email_address': 'email',
            'customer_type': 'segment',
        }
    },
    'orders': {
        'source_table': 'your_orders_table',
        'fields': {
            'order_number': 'order_id',
            'customer_ref': 'customer_id',
            'order_timestamp': 'order_date',
            'order_status': 'status',
            'total': 'total_amount',
        }
    },
    # Add more mappings for products, invoices, etc.
}


if __name__ == "__main__":
    load_from_existing_database()
