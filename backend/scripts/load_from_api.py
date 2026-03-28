"""
Load data from REST APIs into the graph system.

Examples: Salesforce, SAP, custom APIs, etc.
"""
import sys
from pathlib import Path
import requests
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.models import Customer, Product, Order


def load_from_salesforce_api():
    """
    Example: Load customers from Salesforce API.

    Adapt this for your API (Salesforce, SAP, custom, etc.)
    """
    db = SessionLocal()

    try:
        # Step 1: Authenticate with your API
        api_url = "https://your-instance.salesforce.com/services/data/v52.0"
        headers = {
            "Authorization": "Bearer YOUR_ACCESS_TOKEN",
            "Content-Type": "application/json"
        }

        print("🔄 Fetching data from API...")

        # Step 2: Fetch customers
        response = requests.get(
            f"{api_url}/query/?q=SELECT Id, Name, Email, Type FROM Account",
            headers=headers
        )
        response.raise_for_status()
        salesforce_data = response.json()

        # Step 3: Transform and load
        print(f"  Loading {len(salesforce_data['records'])} customers...")

        for record in salesforce_data['records']:
            customer = Customer(
                customer_id=record['Id'],
                name=record['Name'],
                email=record.get('Email', ''),
                segment=record.get('Type', 'Unknown')
            )
            db.add(customer)

        db.commit()
        print(f"  ✓ Loaded {db.query(Customer).count()} customers")

        print("\n✅ API data loaded successfully!")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def load_from_csv_files(csv_directory: str):
    """
    Load data from CSV files.

    Args:
        csv_directory: Path to directory containing CSV files
    """
    import pandas as pd

    db = SessionLocal()

    try:
        print("🔄 Loading data from CSV files...")

        # Load customers
        customers_df = pd.read_csv(f"{csv_directory}/customers.csv")
        print(f"  Loading {len(customers_df)} customers...")

        for _, row in customers_df.iterrows():
            customer = Customer(
                customer_id=str(row['customer_id']),
                name=row['name'],
                email=row['email'],
                segment=row.get('segment', 'Unknown')
            )
            db.add(customer)

        db.commit()
        print(f"  ✓ Loaded customers")

        # Load products
        products_df = pd.read_csv(f"{csv_directory}/products.csv")
        print(f"  Loading {len(products_df)} products...")

        for _, row in products_df.iterrows():
            product = Product(
                product_id=str(row['product_id']),
                name=row['name'],
                category=row.get('category', 'General'),
                price=float(row['price']),
                description=row.get('description', '')
            )
            db.add(product)

        db.commit()
        print(f"  ✓ Loaded products")

        # Add similar logic for orders, invoices, etc.

        print("\n✅ CSV data loaded successfully!")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def load_from_json_api():
    """
    Example: Load from JSON REST API.
    """
    db = SessionLocal()

    try:
        print("🔄 Fetching data from JSON API...")

        # Example: Your custom API
        response = requests.get("https://api.yourcompany.com/customers")
        response.raise_for_status()
        customers = response.json()

        for customer_data in customers:
            customer = Customer(
                customer_id=customer_data['id'],
                name=customer_data['name'],
                email=customer_data['email'],
                segment=customer_data.get('segment', 'Unknown')
            )
            db.add(customer)

        db.commit()
        print(f"  ✓ Loaded {len(customers)} customers")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python load_from_api.py salesforce")
        print("  python load_from_api.py csv /path/to/csv/directory")
        print("  python load_from_api.py json")
        sys.exit(1)

    source = sys.argv[1]

    if source == "salesforce":
        load_from_salesforce_api()
    elif source == "csv" and len(sys.argv) >= 3:
        load_from_csv_files(sys.argv[2])
    elif source == "json":
        load_from_json_api()
    else:
        print(f"Unknown source: {source}")
        sys.exit(1)
