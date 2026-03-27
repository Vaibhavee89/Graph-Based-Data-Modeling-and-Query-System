"""ETL Pipeline for SAP O2C JSONL dataset."""
import sys
import json
from pathlib import Path
import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.core.database import SessionLocal, init_db
from app.models import (
    Customer, Product, Order, OrderItem,
    Invoice, Payment, Delivery, Address
)


class SapO2CETLPipeline:
    """ETL Pipeline for SAP Order-to-Cash JSONL data."""

    def __init__(self, source_dir: str):
        """
        Initialize ETL pipeline.

        Args:
            source_dir: Path to SAP O2C data directory
        """
        self.source_dir = Path(source_dir)
        self.db = SessionLocal()
        self.data_dir = Path(__file__).parent.parent.parent / "data"
        self.processed_dir = self.data_dir / "processed"
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def log(self, message: str):
        """Print timestamped log message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def read_jsonl(self, directory: str) -> list:
        """
        Read all JSONL files from a directory.

        Args:
            directory: Subdirectory name

        Returns:
            List of dictionaries
        """
        dir_path = self.source_dir / directory
        if not dir_path.exists():
            self.log(f"Warning: Directory {directory} not found")
            return []

        records = []
        for file_path in dir_path.glob("*.jsonl"):
            with open(file_path, 'r') as f:
                for line in f:
                    if line.strip():
                        records.append(json.loads(line))

        return records

    def extract_customers(self) -> pd.DataFrame:
        """Extract and transform business partners to customers."""
        self.log("Extracting business partners...")
        records = self.read_jsonl("business_partners")

        if not records:
            self.log("  Warning: No business partner records found")
            return pd.DataFrame()

        customers = []
        for rec in records:
            customers.append({
                'customer_id': rec.get('businessPartner'),
                'name': rec.get('businessPartnerFullName', rec.get('businessPartnerName', '')),
                'email': f"{rec.get('businessPartner')}@example.com",  # SAP doesn't have email in this dataset
                'segment': rec.get('businessPartnerGrouping', 'Unknown'),
            })

        df = pd.DataFrame(customers)
        self.log(f"  ✓ Extracted {len(df)} customers")
        return df

    def extract_products(self) -> pd.DataFrame:
        """Extract and transform products."""
        self.log("Extracting products...")
        records = self.read_jsonl("products")

        if not records:
            self.log("  Warning: No product records found")
            return pd.DataFrame()

        # Also get product descriptions
        descriptions = self.read_jsonl("product_descriptions")
        desc_map = {d.get('product'): d.get('productDescription', '') for d in descriptions}

        products = []
        for rec in records:
            product_id = rec.get('product')
            products.append({
                'product_id': product_id,
                'name': desc_map.get(product_id, f"Product {product_id}"),
                'category': rec.get('productGroup', 'Uncategorized'),
                'price': float(rec.get('grossWeight', 100)) * 1000,  # Dummy price based on weight
                'description': desc_map.get(product_id, ''),
            })

        df = pd.DataFrame(products)
        self.log(f"  ✓ Extracted {len(df)} products")
        return df

    def extract_addresses(self, customer_df: pd.DataFrame) -> pd.DataFrame:
        """Extract and transform addresses."""
        self.log("Extracting addresses...")
        records = self.read_jsonl("business_partner_addresses")

        if not records:
            self.log("  Warning: No address records found, creating dummy addresses")
            # Create dummy addresses for customers
            addresses = []
            for idx, customer_id in enumerate(customer_df['customer_id'].unique()[:50]):
                addresses.append({
                    'address_id': f"ADDR-{idx+1:04d}",
                    'customer_id': customer_id,
                    'street': "Street Address",
                    'city': "City",
                    'state': "State",
                    'postal_code': "000000",
                    'country': "India",
                    'address_type': "billing",
                })
            return pd.DataFrame(addresses)

        addresses = []
        for idx, rec in enumerate(records):
            addresses.append({
                'address_id': f"ADDR-{idx+1:04d}",
                'customer_id': rec.get('businessPartner'),
                'street': rec.get('streetName', '') + ' ' + rec.get('houseNumber', ''),
                'city': rec.get('cityName', 'Unknown'),
                'state': rec.get('region', ''),
                'postal_code': rec.get('postalCode', ''),
                'country': rec.get('country', 'IN'),
                'address_type': 'billing',
            })

        df = pd.DataFrame(addresses)
        self.log(f"  ✓ Extracted {len(df)} addresses")
        return df

    def extract_orders(self, customer_df: pd.DataFrame) -> pd.DataFrame:
        """Extract and transform sales orders."""
        self.log("Extracting sales orders...")
        records = self.read_jsonl("sales_order_headers")

        if not records:
            self.log("  Warning: No sales order records found")
            return pd.DataFrame()

        customer_ids = set(customer_df['customer_id'])

        orders = []
        for rec in records:
            # Only include orders for customers we have
            sold_to = rec.get('soldToParty')
            if sold_to not in customer_ids:
                continue

            orders.append({
                'order_id': rec.get('salesOrder'),
                'customer_id': sold_to,
                'order_date': rec.get('creationDate', '').split('T')[0] if rec.get('creationDate') else None,
                'status': self._map_order_status(rec.get('overallDeliveryStatus', '')),
                'total_amount': float(rec.get('totalNetAmount', 0)),
            })

        df = pd.DataFrame(orders)
        df['order_date'] = pd.to_datetime(df['order_date'], errors='coerce')
        self.log(f"  ✓ Extracted {len(df)} orders")
        return df

    def extract_order_items(self, order_df: pd.DataFrame, product_df: pd.DataFrame) -> pd.DataFrame:
        """Extract and transform sales order items."""
        self.log("Extracting sales order items...")
        records = self.read_jsonl("sales_order_items")

        if not records:
            self.log("  Warning: No sales order item records found")
            return pd.DataFrame()

        order_ids = set(order_df['order_id'])
        product_ids = set(product_df['product_id'])

        items = []
        for idx, rec in enumerate(records, 1):
            order_id = rec.get('salesOrder')
            product_id = rec.get('material')

            # Only include items for orders and products we have
            if order_id not in order_ids or product_id not in product_ids:
                continue

            quantity = float(rec.get('orderQuantity', 1))
            unit_price = float(rec.get('netAmount', 0)) / quantity if quantity > 0 else 0

            items.append({
                'id': idx,
                'order_id': order_id,
                'product_id': product_id,
                'quantity': int(quantity),
                'unit_price': unit_price,
                'subtotal': float(rec.get('netAmount', 0)),
            })

        df = pd.DataFrame(items)
        self.log(f"  ✓ Extracted {len(df)} order items")
        return df

    def extract_invoices(self, order_df: pd.DataFrame) -> pd.DataFrame:
        """Extract and transform billing documents (invoices)."""
        self.log("Extracting billing documents (invoices)...")
        records = self.read_jsonl("billing_document_headers")

        if not records:
            self.log("  Warning: No billing document records found")
            return pd.DataFrame()

        # Read billing items to link to orders
        items = self.read_jsonl("billing_document_items")
        invoice_to_order = {}
        for item in items:
            invoice_id = item.get('billingDocument')
            order_id = item.get('salesDocument')
            if invoice_id and order_id:
                invoice_to_order[invoice_id] = order_id

        order_ids = set(order_df['order_id'])

        invoices = []
        for rec in records:
            invoice_id = rec.get('billingDocument')
            order_id = invoice_to_order.get(invoice_id)

            # Skip if we don't have the linked order
            if not order_id or order_id not in order_ids:
                continue

            invoices.append({
                'invoice_id': invoice_id,
                'order_id': order_id,
                'invoice_date': rec.get('billingDocumentDate', '').split('T')[0] if rec.get('billingDocumentDate') else None,
                'due_date': None,  # Not in SAP data
                'amount': float(rec.get('totalNetAmount', 0)),
                'status': 'paid' if rec.get('accountingDocument') else 'sent',
            })

        df = pd.DataFrame(invoices)
        df['invoice_date'] = pd.to_datetime(df['invoice_date'], errors='coerce')
        df['due_date'] = df['invoice_date'] + pd.Timedelta(days=30)  # Default 30 days
        self.log(f"  ✓ Extracted {len(df)} invoices")
        return df

    def extract_payments(self, invoice_df: pd.DataFrame) -> pd.DataFrame:
        """Extract and transform payments from AR data."""
        self.log("Extracting payments...")
        records = self.read_jsonl("payments_accounts_receivable")

        if not records:
            self.log("  Warning: No payment records found")
            return pd.DataFrame()

        # Build mapping from accounting document to invoice
        billing_records = self.read_jsonl("billing_document_headers")
        acct_doc_to_invoice = {rec.get('accountingDocument'): rec.get('billingDocument')
                               for rec in billing_records if rec.get('accountingDocument')}

        invoice_ids = set(invoice_df['invoice_id'])

        payments = []
        seen_invoices = set()

        for rec in records:
            # Only process cleared payments
            if not rec.get('clearingDate'):
                continue

            acct_doc = rec.get('accountingDocument')
            invoice_id = acct_doc_to_invoice.get(acct_doc)

            # Skip if no invoice match or already processed
            if not invoice_id or invoice_id not in invoice_ids or invoice_id in seen_invoices:
                continue

            seen_invoices.add(invoice_id)

            payments.append({
                'payment_id': f"PAY-{len(payments)+1:04d}",
                'invoice_id': invoice_id,
                'payment_date': rec.get('clearingDate', '').split('T')[0] if rec.get('clearingDate') else None,
                'amount': float(rec.get('amountInTransactionCurrency', 0)),
                'method': 'bank_transfer',
                'transaction_id': rec.get('clearingAccountingDocument', ''),
                'status': 'completed',
            })

        df = pd.DataFrame(payments)
        df['payment_date'] = pd.to_datetime(df['payment_date'], errors='coerce')
        self.log(f"  ✓ Extracted {len(df)} payments")
        return df

    def extract_deliveries(self, order_df: pd.DataFrame, address_df: pd.DataFrame) -> pd.DataFrame:
        """Extract and transform outbound deliveries."""
        self.log("Extracting outbound deliveries...")
        records = self.read_jsonl("outbound_delivery_headers")

        if not records:
            self.log("  Warning: No delivery records found")
            return pd.DataFrame()

        # Read delivery items to link to orders
        items = self.read_jsonl("outbound_delivery_items")
        delivery_to_order = {}
        for item in items:
            delivery_id = item.get('deliveryDocument')
            order_id = item.get('referenceSDDocument')
            if delivery_id and order_id:
                delivery_to_order[delivery_id] = order_id

        order_ids = set(order_df['order_id'])
        address_ids = list(address_df['address_id'])

        deliveries = []
        for idx, rec in enumerate(records):
            delivery_id = rec.get('deliveryDocument')
            order_id = delivery_to_order.get(delivery_id)

            # Skip if we don't have the linked order
            if not order_id or order_id not in order_ids:
                continue

            # Assign a random address from available ones
            address_id = address_ids[idx % len(address_ids)] if address_ids else None

            deliveries.append({
                'delivery_id': delivery_id,
                'order_id': order_id,
                'address_id': address_id,
                'delivery_date': rec.get('actualGoodsMovementDate', '').split('T')[0] if rec.get('actualGoodsMovementDate') else None,
                'status': self._map_delivery_status(rec.get('overallGoodsMovementStatus', '')),
                'tracking_number': f"TRK-{delivery_id}",
                'carrier': 'Carrier',
            })

        df = pd.DataFrame(deliveries)
        df['delivery_date'] = pd.to_datetime(df['delivery_date'], errors='coerce')
        self.log(f"  ✓ Extracted {len(df)} deliveries")
        return df

    def _map_order_status(self, sap_status: str) -> str:
        """Map SAP order status to our status."""
        status_map = {
            'C': 'completed',
            'A': 'pending',
            'B': 'pending',
            '': 'pending',
        }
        return status_map.get(sap_status, 'pending')

    def _map_delivery_status(self, sap_status: str) -> str:
        """Map SAP delivery status to our status."""
        status_map = {
            'C': 'delivered',
            'A': 'in_transit',
            'B': 'pending',
            '': 'pending',
        }
        return status_map.get(sap_status, 'pending')

    def load_to_db(self, customers_df, products_df, addresses_df, orders_df,
                   order_items_df, invoices_df, payments_df, deliveries_df):
        """Load data into PostgreSQL."""
        self.log("\n" + "=" * 60)
        self.log("Loading data into PostgreSQL...")
        self.log("=" * 60)

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
        self.log("SAP O2C ETL Pipeline Starting")
        self.log("=" * 60)
        self.log(f"Source directory: {self.source_dir}")

        try:
            # Initialize database
            init_db()
            self.log("✓ Database initialized")

            # Extract
            self.log("\n" + "=" * 60)
            self.log("Extract & Transform Phase")
            self.log("=" * 60)

            customers_df = self.extract_customers()
            products_df = self.extract_products()
            addresses_df = self.extract_addresses(customers_df)
            orders_df = self.extract_orders(customers_df)
            order_items_df = self.extract_order_items(orders_df, products_df)
            invoices_df = self.extract_invoices(orders_df)
            payments_df = self.extract_payments(invoices_df)
            deliveries_df = self.extract_deliveries(orders_df, addresses_df)

            # Save processed data
            self.log("\n" + "=" * 60)
            self.log("Saving Processed Data")
            self.log("=" * 60)

            customers_df.to_csv(self.processed_dir / 'customers.csv', index=False)
            products_df.to_csv(self.processed_dir / 'products.csv', index=False)
            addresses_df.to_csv(self.processed_dir / 'addresses.csv', index=False)
            orders_df.to_csv(self.processed_dir / 'orders.csv', index=False)
            order_items_df.to_csv(self.processed_dir / 'order_items.csv', index=False)
            invoices_df.to_csv(self.processed_dir / 'invoices.csv', index=False)
            payments_df.to_csv(self.processed_dir / 'payments.csv', index=False)
            deliveries_df.to_csv(self.processed_dir / 'deliveries.csv', index=False)
            self.log("✓ Processed data saved to CSV files")

            # Load to database
            self.load_to_db(
                customers_df, products_df, addresses_df, orders_df,
                order_items_df, invoices_df, payments_df, deliveries_df
            )

            # Summary
            self.log("\n" + "=" * 60)
            self.log("ETL Pipeline Complete!")
            self.log("=" * 60)
            self.log(f"Customers:    {len(customers_df)}")
            self.log(f"Products:     {len(products_df)}")
            self.log(f"Addresses:    {len(addresses_df)}")
            self.log(f"Orders:       {len(orders_df)}")
            self.log(f"Order Items:  {len(order_items_df)}")
            self.log(f"Invoices:     {len(invoices_df)}")
            self.log(f"Payments:     {len(payments_df)}")
            self.log(f"Deliveries:   {len(deliveries_df)}")
            self.log("\nNext step: Build graph with 'python backend/scripts/build_graph.py'")

        except Exception as e:
            self.log(f"\n✗ ETL Pipeline failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.db.close()


def main():
    """Main function."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python etl_sap_o2c.py <path_to_sap_o2c_data>")
        print("Example: python backend/scripts/etl_sap_o2c.py /Users/vaibhavee/Downloads/sap-o2c-data")
        sys.exit(1)

    source_dir = sys.argv[1]
    pipeline = SapO2CETLPipeline(source_dir)
    pipeline.run()


if __name__ == "__main__":
    main()
