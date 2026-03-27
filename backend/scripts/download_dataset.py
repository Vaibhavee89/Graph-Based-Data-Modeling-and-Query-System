"""Download dataset from Google Drive or other sources."""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def download_from_google_drive(file_id: str, output_path: str):
    """
    Download file from Google Drive using gdown.

    Args:
        file_id: Google Drive file ID (from shareable link)
        output_path: Local path to save file
    """
    try:
        import gdown
    except ImportError:
        print("gdown not installed. Install with: pip install gdown")
        return False

    url = f"https://drive.google.com/uc?id={file_id}"
    print(f"Downloading from Google Drive...")
    print(f"URL: {url}")
    print(f"Output: {output_path}")

    try:
        gdown.download(url, output_path, quiet=False)
        print(f"✓ Downloaded successfully to {output_path}")
        return True
    except Exception as e:
        print(f"✗ Download failed: {e}")
        return False


def setup_data_directories():
    """Create data directories if they don't exist."""
    data_dir = Path(__file__).parent.parent.parent / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"

    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    print(f"✓ Data directories ready:")
    print(f"  - Raw: {raw_dir}")
    print(f"  - Processed: {processed_dir}")

    return raw_dir, processed_dir


def create_sample_data():
    """
    Create sample CSV files for testing purposes.
    Use this when you don't have access to the actual dataset.
    """
    import pandas as pd
    from datetime import datetime, timedelta
    import random

    raw_dir, _ = setup_data_directories()

    print("\nCreating sample data for testing...")

    # Sample Customers
    customers = []
    for i in range(1, 101):
        customers.append({
            'customer_id': f'CUST-{i:04d}',
            'name': f'Customer {i}',
            'email': f'customer{i}@example.com',
            'segment': random.choice(['Enterprise', 'SMB', 'Individual'])
        })
    pd.DataFrame(customers).to_csv(raw_dir / 'customers.csv', index=False)
    print(f"  ✓ Created customers.csv ({len(customers)} records)")

    # Sample Products
    products = []
    categories = ['Electronics', 'Software', 'Hardware', 'Services']
    for i in range(1, 51):
        products.append({
            'product_id': f'PROD-{i:04d}',
            'name': f'Product {i}',
            'category': random.choice(categories),
            'price': round(random.uniform(10, 1000), 2),
            'description': f'Description for product {i}'
        })
    pd.DataFrame(products).to_csv(raw_dir / 'products.csv', index=False)
    print(f"  ✓ Created products.csv ({len(products)} records)")

    # Sample Addresses
    addresses = []
    cities = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix']
    states = ['NY', 'CA', 'IL', 'TX', 'AZ']
    for i in range(1, 201):
        city_idx = random.randint(0, len(cities) - 1)
        addresses.append({
            'address_id': f'ADDR-{i:04d}',
            'customer_id': f'CUST-{random.randint(1, 100):04d}' if i <= 100 else None,
            'street': f'{random.randint(1, 999)} Main St',
            'city': cities[city_idx],
            'state': states[city_idx],
            'postal_code': f'{random.randint(10000, 99999)}',
            'country': 'USA',
            'address_type': random.choice(['billing', 'shipping'])
        })
    pd.DataFrame(addresses).to_csv(raw_dir / 'addresses.csv', index=False)
    print(f"  ✓ Created addresses.csv ({len(addresses)} records)")

    # Sample Orders
    orders = []
    base_date = datetime.now() - timedelta(days=365)
    for i in range(1, 301):
        order_date = base_date + timedelta(days=random.randint(0, 365))
        orders.append({
            'order_id': f'ORD-{i:04d}',
            'customer_id': f'CUST-{random.randint(1, 100):04d}',
            'order_date': order_date.strftime('%Y-%m-%d'),
            'status': random.choice(['pending', 'completed', 'cancelled']),
            'total_amount': round(random.uniform(50, 5000), 2)
        })
    pd.DataFrame(orders).to_csv(raw_dir / 'orders.csv', index=False)
    print(f"  ✓ Created orders.csv ({len(orders)} records)")

    # Sample Order Items
    order_items = []
    item_id = 1
    for order in orders:
        num_items = random.randint(1, 5)
        for _ in range(num_items):
            product = random.choice(products)
            quantity = random.randint(1, 10)
            unit_price = product['price']
            order_items.append({
                'id': item_id,
                'order_id': order['order_id'],
                'product_id': product['product_id'],
                'quantity': quantity,
                'unit_price': unit_price,
                'subtotal': round(quantity * unit_price, 2)
            })
            item_id += 1
    pd.DataFrame(order_items).to_csv(raw_dir / 'order_items.csv', index=False)
    print(f"  ✓ Created order_items.csv ({len(order_items)} records)")

    # Sample Invoices (80% of orders)
    invoices = []
    for i, order in enumerate(orders[:int(len(orders) * 0.8)], 1):
        order_date = datetime.strptime(order['order_date'], '%Y-%m-%d')
        invoice_date = order_date + timedelta(days=random.randint(0, 5))
        invoices.append({
            'invoice_id': f'INV-{i:04d}',
            'order_id': order['order_id'],
            'invoice_date': invoice_date.strftime('%Y-%m-%d'),
            'due_date': (invoice_date + timedelta(days=30)).strftime('%Y-%m-%d'),
            'amount': order['total_amount'],
            'status': random.choice(['draft', 'sent', 'paid', 'overdue'])
        })
    pd.DataFrame(invoices).to_csv(raw_dir / 'invoices.csv', index=False)
    print(f"  ✓ Created invoices.csv ({len(invoices)} records)")

    # Sample Payments (70% of invoices)
    payments = []
    for i, invoice in enumerate(invoices[:int(len(invoices) * 0.7)], 1):
        invoice_date = datetime.strptime(invoice['invoice_date'], '%Y-%m-%d')
        payment_date = invoice_date + timedelta(days=random.randint(1, 30))
        payments.append({
            'payment_id': f'PAY-{i:04d}',
            'invoice_id': invoice['invoice_id'],
            'payment_date': payment_date.strftime('%Y-%m-%d'),
            'amount': invoice['amount'],
            'method': random.choice(['credit_card', 'bank_transfer', 'check']),
            'transaction_id': f'TXN-{random.randint(100000, 999999)}',
            'status': random.choice(['completed', 'pending', 'failed'])
        })
    pd.DataFrame(payments).to_csv(raw_dir / 'payments.csv', index=False)
    print(f"  ✓ Created payments.csv ({len(payments)} records)")

    # Sample Deliveries (75% of orders)
    deliveries = []
    for i, order in enumerate(orders[:int(len(orders) * 0.75)], 1):
        order_date = datetime.strptime(order['order_date'], '%Y-%m-%d')
        delivery_date = order_date + timedelta(days=random.randint(3, 14))
        # Get a random shipping address
        shipping_addr = random.choice([a for a in addresses if a.get('address_type') == 'shipping'])
        deliveries.append({
            'delivery_id': f'DEL-{i:04d}',
            'order_id': order['order_id'],
            'address_id': shipping_addr['address_id'] if shipping_addr else None,
            'delivery_date': delivery_date.strftime('%Y-%m-%d') if random.random() > 0.2 else None,
            'status': random.choice(['pending', 'in_transit', 'delivered', 'failed']),
            'tracking_number': f'TRK-{random.randint(100000000, 999999999)}',
            'carrier': random.choice(['FedEx', 'UPS', 'USPS', 'DHL'])
        })
    pd.DataFrame(deliveries).to_csv(raw_dir / 'deliveries.csv', index=False)
    print(f"  ✓ Created deliveries.csv ({len(deliveries)} records)")

    print(f"\n✓ Sample data created in {raw_dir}/")
    print("\nNext steps:")
    print("  1. Run ETL pipeline: python backend/scripts/etl.py")
    print("  2. Initialize database: python backend/scripts/init_db.py")
    print("  3. Build graph: python backend/scripts/build_graph.py")


def main():
    """Main function."""
    print("=" * 60)
    print("Dataset Download Script")
    print("=" * 60)

    # Set up directories
    raw_dir, processed_dir = setup_data_directories()

    print("\nOptions:")
    print("  1. Create sample data (for testing)")
    print("  2. Download from Google Drive (requires file ID)")
    print("  3. Manual download (instructions)")

    choice = input("\nSelect option (1-3): ").strip()

    if choice == "1":
        create_sample_data()
    elif choice == "2":
        file_id = input("Enter Google Drive file ID: ").strip()
        output_path = input(f"Enter output filename (in {raw_dir}/): ").strip()
        download_from_google_drive(file_id, str(raw_dir / output_path))
    elif choice == "3":
        print("\nManual Download Instructions:")
        print("1. Download your dataset files from Google Drive or other source")
        print(f"2. Place CSV files in: {raw_dir}/")
        print("3. Expected files:")
        print("   - customers.csv")
        print("   - products.csv")
        print("   - orders.csv")
        print("   - order_items.csv")
        print("   - invoices.csv")
        print("   - payments.csv")
        print("   - deliveries.csv")
        print("   - addresses.csv")
        print("\n4. Run ETL pipeline: python backend/scripts/etl.py")
    else:
        print("Invalid choice. Exiting.")


if __name__ == "__main__":
    main()
