"""ETL Pipeline - Extract, Transform, Load data into PostgreSQL."""
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.core.database import engine, SessionLocal, init_db
from app.models import (
    Customer, Product, Order, OrderItem,
    Invoice, Payment, Delivery, Address
)


class ETLPipeline:
    """ETL Pipeline for processing and loading data."""

    def __init__(self):
        self.data_dir = Path(__file__).parent.parent.parent / "data"
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        self.db = SessionLocal()

    def log(self, message: str):
        """Print timestamped log message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def extract(self, filename: str) -> pd.DataFrame:
        """Extract data from CSV file."""
        filepath = self.raw_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        self.log(f"Extracting {filename}...")
        df = pd.DataFrame(pd.read_csv(filepath))
        self.log(f"  ✓ Loaded {len(df)} records from {filename}")
        return df

    def clean_customers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate customer data."""
        self.log("Cleaning customers...")

        # Remove duplicates
        before = len(df)
        df = df.drop_duplicates(subset=['customer_id'])
        if len(df) < before:
            self.log(f"  - Removed {before - len(df)} duplicate customer_ids")

        # Handle missing values
        df['email'] = df['email'].fillna('')
        df['segment'] = df['segment'].fillna('Unknown')

        # Standardize email
        df['email'] = df['email'].str.lower().str.strip()

        return df

    def clean_products(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate product data."""
        self.log("Cleaning products...")

        # Remove duplicates
        before = len(df)
        df = df.drop_duplicates(subset=['product_id'])
        if len(df) < before:
            self.log(f"  - Removed {before - len(df)} duplicate product_ids")

        # Handle missing values
        df['description'] = df['description'].fillna('')
        df['category'] = df['category'].fillna('Uncategorized')

        # Validate price
        df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)
        df = df[df['price'] >= 0]

        return df

    def clean_orders(self, df: pd.DataFrame, customer_ids: set) -> pd.DataFrame:
        """Clean and validate order data."""
        self.log("Cleaning orders...")

        # Remove duplicates
        before = len(df)
        df = df.drop_duplicates(subset=['order_id'])
        if len(df) < before:
            self.log(f"  - Removed {before - len(df)} duplicate order_ids")

        # Parse dates
        df['order_date'] = pd.to_datetime(df['order_date'], errors='coerce')
        df = df.dropna(subset=['order_date'])

        # Validate foreign keys
        before = len(df)
        df = df[df['customer_id'].isin(customer_ids)]
        if len(df) < before:
            self.log(f"  - Removed {before - len(df)} orders with invalid customer_id")

        # Validate amount
        df['total_amount'] = pd.to_numeric(df['total_amount'], errors='coerce').fillna(0)
        df = df[df['total_amount'] >= 0]

        # Standardize status
        df['status'] = df['status'].str.lower().str.strip()

        return df

    def clean_order_items(self, df: pd.DataFrame, order_ids: set, product_ids: set) -> pd.DataFrame:
        """Clean and validate order items data."""
        self.log("Cleaning order items...")

        # Validate foreign keys
        before = len(df)
        df = df[df['order_id'].isin(order_ids) & df['product_id'].isin(product_ids)]
        if len(df) < before:
            self.log(f"  - Removed {before - len(df)} items with invalid order_id/product_id")

        # Validate numeric fields
        df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').fillna(1).astype(int)
        df['unit_price'] = pd.to_numeric(df['unit_price'], errors='coerce').fillna(0)
        df['subtotal'] = pd.to_numeric(df['subtotal'], errors='coerce').fillna(0)

        # Recalculate subtotal
        df['subtotal'] = df['quantity'] * df['unit_price']

        return df

    def clean_addresses(self, df: pd.DataFrame, customer_ids: set) -> pd.DataFrame:
        """Clean and validate address data."""
        self.log("Cleaning addresses...")

        # Remove duplicates
        before = len(df)
        df = df.drop_duplicates(subset=['address_id'])
        if len(df) < before:
            self.log(f"  - Removed {before - len(df)} duplicate address_ids")

        # Validate foreign keys (allow null customer_id for deliveries)
        df['customer_id'] = df['customer_id'].where(
            df['customer_id'].isin(customer_ids) | df['customer_id'].isna(),
            None
        )

        # Handle missing values
        df['street'] = df['street'].fillna('Unknown')
        df['city'] = df['city'].fillna('Unknown')
        df['state'] = df['state'].fillna('')
        df['postal_code'] = df['postal_code'].fillna('')
        df['country'] = df['country'].fillna('Unknown')

        return df

    def clean_invoices(self, df: pd.DataFrame, order_ids: set) -> pd.DataFrame:
        """Clean and validate invoice data."""
        self.log("Cleaning invoices...")

        # Remove duplicates
        before = len(df)
        df = df.drop_duplicates(subset=['invoice_id'])
        if len(df) < before:
            self.log(f"  - Removed {before - len(df)} duplicate invoice_ids")

        # Validate foreign keys
        before = len(df)
        df = df[df['order_id'].isin(order_ids)]
        if len(df) < before:
            self.log(f"  - Removed {before - len(df)} invoices with invalid order_id")

        # Parse dates
        df['invoice_date'] = pd.to_datetime(df['invoice_date'], errors='coerce')
        df['due_date'] = pd.to_datetime(df['due_date'], errors='coerce')
        df = df.dropna(subset=['invoice_date'])

        # Validate amount
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)

        # Standardize status
        df['status'] = df['status'].str.lower().str.strip()

        return df

    def clean_payments(self, df: pd.DataFrame, invoice_ids: set) -> pd.DataFrame:
        """Clean and validate payment data."""
        self.log("Cleaning payments...")

        # Remove duplicates
        before = len(df)
        df = df.drop_duplicates(subset=['payment_id'])
        if len(df) < before:
            self.log(f"  - Removed {before - len(df)} duplicate payment_ids")

        # Validate foreign keys
        before = len(df)
        df = df[df['invoice_id'].isin(invoice_ids)]
        if len(df) < before:
            self.log(f"  - Removed {before - len(df)} payments with invalid invoice_id")

        # Parse dates
        df['payment_date'] = pd.to_datetime(df['payment_date'], errors='coerce')
        df = df.dropna(subset=['payment_date'])

        # Validate amount
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)

        # Standardize status and method
        df['status'] = df['status'].str.lower().str.strip()
        df['method'] = df['method'].str.lower().str.strip()

        return df

    def clean_deliveries(self, df: pd.DataFrame, order_ids: set, address_ids: set) -> pd.DataFrame:
        """Clean and validate delivery data."""
        self.log("Cleaning deliveries...")

        # Remove duplicates
        before = len(df)
        df = df.drop_duplicates(subset=['delivery_id'])
        if len(df) < before:
            self.log(f"  - Removed {before - len(df)} duplicate delivery_ids")

        # Validate foreign keys
        before = len(df)
        df = df[df['order_id'].isin(order_ids)]
        if len(df) < before:
            self.log(f"  - Removed {before - len(df)} deliveries with invalid order_id")

        # Validate address_id (can be null)
        df['address_id'] = df['address_id'].where(
            df['address_id'].isin(address_ids) | df['address_id'].isna(),
            None
        )

        # Parse dates (can be null for pending deliveries)
        df['delivery_date'] = pd.to_datetime(df['delivery_date'], errors='coerce')

        # Standardize status
        df['status'] = df['status'].str.lower().str.strip()

        return df

    def save_processed(self, df: pd.DataFrame, filename: str):
        """Save processed data to CSV."""
        filepath = self.processed_dir / filename
        df.to_csv(filepath, index=False)
        self.log(f"  ✓ Saved {len(df)} records to {filename}")

    def load_to_db(self):
        """Load processed data into PostgreSQL."""
        self.log("Loading data into PostgreSQL...")

        # Load processed CSVs
        customers_df = pd.read_csv(self.processed_dir / 'customers.csv')
        products_df = pd.read_csv(self.processed_dir / 'products.csv')
        addresses_df = pd.read_csv(self.processed_dir / 'addresses.csv')
        orders_df = pd.read_csv(self.processed_dir / 'orders.csv')
        order_items_df = pd.read_csv(self.processed_dir / 'order_items.csv')
        invoices_df = pd.read_csv(self.processed_dir / 'invoices.csv')
        payments_df = pd.read_csv(self.processed_dir / 'payments.csv')
        deliveries_df = pd.read_csv(self.processed_dir / 'deliveries.csv')

        # Clear existing data
        self.log("Clearing existing data...")
        self.db.query(Payment).delete()
        self.db.query(Invoice).delete()
        self.db.query(Delivery).delete()
        self.db.query(OrderItem).delete()
        self.db.query(Order).delete()
        self.db.query(Address).delete()
        self.db.query(Product).delete()
        self.db.query(Customer).delete()
        self.db.commit()

        # Load customers
        self.log("Loading customers...")
        for _, row in customers_df.iterrows():
            customer = Customer(**row.to_dict())
            self.db.add(customer)
        self.db.commit()
        self.log(f"  ✓ Loaded {len(customers_df)} customers")

        # Load products
        self.log("Loading products...")
        for _, row in products_df.iterrows():
            product = Product(**row.to_dict())
            self.db.add(product)
        self.db.commit()
        self.log(f"  ✓ Loaded {len(products_df)} products")

        # Load addresses
        self.log("Loading addresses...")
        for _, row in addresses_df.iterrows():
            address = Address(**row.to_dict())
            self.db.add(address)
        self.db.commit()
        self.log(f"  ✓ Loaded {len(addresses_df)} addresses")

        # Load orders
        self.log("Loading orders...")
        for _, row in orders_df.iterrows():
            order = Order(**row.to_dict())
            self.db.add(order)
        self.db.commit()
        self.log(f"  ✓ Loaded {len(orders_df)} orders")

        # Load order items
        self.log("Loading order items...")
        for _, row in order_items_df.iterrows():
            item = OrderItem(**row.to_dict())
            self.db.add(item)
        self.db.commit()
        self.log(f"  ✓ Loaded {len(order_items_df)} order items")

        # Load invoices
        self.log("Loading invoices...")
        for _, row in invoices_df.iterrows():
            invoice = Invoice(**row.to_dict())
            self.db.add(invoice)
        self.db.commit()
        self.log(f"  ✓ Loaded {len(invoices_df)} invoices")

        # Load payments
        self.log("Loading payments...")
        for _, row in payments_df.iterrows():
            payment = Payment(**row.to_dict())
            self.db.add(payment)
        self.db.commit()
        self.log(f"  ✓ Loaded {len(payments_df)} payments")

        # Load deliveries
        self.log("Loading deliveries...")
        for _, row in deliveries_df.iterrows():
            delivery = Delivery(**row.to_dict())
            self.db.add(delivery)
        self.db.commit()
        self.log(f"  ✓ Loaded {len(deliveries_df)} deliveries")

    def run(self):
        """Run the complete ETL pipeline."""
        self.log("=" * 60)
        self.log("ETL Pipeline Starting")
        self.log("=" * 60)

        try:
            # Extract
            customers_df = self.extract('customers.csv')
            products_df = self.extract('products.csv')
            addresses_df = self.extract('addresses.csv')
            orders_df = self.extract('orders.csv')
            order_items_df = self.extract('order_items.csv')
            invoices_df = self.extract('invoices.csv')
            payments_df = self.extract('payments.csv')
            deliveries_df = self.extract('deliveries.csv')

            # Transform
            self.log("\n" + "=" * 60)
            self.log("Transform Phase")
            self.log("=" * 60)

            customers_clean = self.clean_customers(customers_df)
            products_clean = self.clean_products(products_df)

            customer_ids = set(customers_clean['customer_id'])
            product_ids = set(products_clean['product_id'])

            addresses_clean = self.clean_addresses(addresses_df, customer_ids)
            address_ids = set(addresses_clean['address_id'])

            orders_clean = self.clean_orders(orders_df, customer_ids)
            order_ids = set(orders_clean['order_id'])

            order_items_clean = self.clean_order_items(order_items_df, order_ids, product_ids)

            invoices_clean = self.clean_invoices(invoices_df, order_ids)
            invoice_ids = set(invoices_clean['invoice_id'])

            payments_clean = self.clean_payments(payments_df, invoice_ids)
            deliveries_clean = self.clean_deliveries(deliveries_df, order_ids, address_ids)

            # Save processed data
            self.log("\n" + "=" * 60)
            self.log("Saving Processed Data")
            self.log("=" * 60)

            self.save_processed(customers_clean, 'customers.csv')
            self.save_processed(products_clean, 'products.csv')
            self.save_processed(addresses_clean, 'addresses.csv')
            self.save_processed(orders_clean, 'orders.csv')
            self.save_processed(order_items_clean, 'order_items.csv')
            self.save_processed(invoices_clean, 'invoices.csv')
            self.save_processed(payments_clean, 'payments.csv')
            self.save_processed(deliveries_clean, 'deliveries.csv')

            # Initialize database tables
            self.log("\n" + "=" * 60)
            self.log("Database Initialization")
            self.log("=" * 60)
            init_db()
            self.log("  ✓ Database tables created")

            # Load to database
            self.log("\n" + "=" * 60)
            self.log("Load Phase")
            self.log("=" * 60)
            self.load_to_db()

            # Summary
            self.log("\n" + "=" * 60)
            self.log("ETL Pipeline Complete!")
            self.log("=" * 60)
            self.log(f"Customers:    {len(customers_clean)}")
            self.log(f"Products:     {len(products_clean)}")
            self.log(f"Addresses:    {len(addresses_clean)}")
            self.log(f"Orders:       {len(orders_clean)}")
            self.log(f"Order Items:  {len(order_items_clean)}")
            self.log(f"Invoices:     {len(invoices_clean)}")
            self.log(f"Payments:     {len(payments_clean)}")
            self.log(f"Deliveries:   {len(deliveries_clean)}")
            self.log("\nNext step: Build graph with 'python backend/scripts/build_graph.py'")

        except Exception as e:
            self.log(f"\n✗ ETL Pipeline failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.db.close()


def main():
    """Main function."""
    pipeline = ETLPipeline()
    pipeline.run()


if __name__ == "__main__":
    main()
