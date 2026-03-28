"""
Real-time data synchronization script.

Use this for continuously syncing data from your live systems.
"""
import sys
from pathlib import Path
import time
from datetime import datetime, timedelta
import schedule

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.models import Order, Customer, Product
import requests


class DataSyncService:
    """Service to sync data from external sources."""

    def __init__(self):
        self.db = SessionLocal()
        self.last_sync = {}

    def sync_new_orders(self):
        """
        Sync new orders from external system.

        This runs periodically to fetch new orders.
        """
        try:
            print(f"[{datetime.now()}] 🔄 Syncing new orders...")

            # Get timestamp of last sync
            last_sync_time = self.last_sync.get('orders', datetime.now() - timedelta(hours=1))

            # Fetch new orders from your API/database
            # Example: REST API
            response = requests.get(
                "https://api.yourcompany.com/orders",
                params={"since": last_sync_time.isoformat()}
            )

            new_orders = response.json()

            # Add new orders to database
            count = 0
            for order_data in new_orders:
                # Check if order already exists
                existing = self.db.query(Order).filter_by(
                    order_id=order_data['id']
                ).first()

                if not existing:
                    order = Order(
                        order_id=order_data['id'],
                        customer_id=order_data['customer_id'],
                        order_date=datetime.fromisoformat(order_data['date']),
                        status=order_data['status'],
                        total_amount=float(order_data['total'])
                    )
                    self.db.add(order)
                    count += 1

            self.db.commit()
            self.last_sync['orders'] = datetime.now()

            print(f"  ✓ Synced {count} new orders")

        except Exception as e:
            print(f"  ❌ Error syncing orders: {e}")
            self.db.rollback()

    def sync_customer_updates(self):
        """
        Sync customer information updates.

        This captures changes to customer data.
        """
        try:
            print(f"[{datetime.now()}] 🔄 Syncing customer updates...")

            # Fetch updated customers
            response = requests.get(
                "https://api.yourcompany.com/customers/updated",
                params={"since": self.last_sync.get('customers', datetime.now() - timedelta(hours=1)).isoformat()}
            )

            updated_customers = response.json()

            count = 0
            for customer_data in updated_customers:
                customer = self.db.query(Customer).filter_by(
                    customer_id=customer_data['id']
                ).first()

                if customer:
                    # Update existing customer
                    customer.name = customer_data['name']
                    customer.email = customer_data['email']
                    customer.segment = customer_data.get('segment', customer.segment)
                    count += 1
                else:
                    # Create new customer
                    customer = Customer(
                        customer_id=customer_data['id'],
                        name=customer_data['name'],
                        email=customer_data['email'],
                        segment=customer_data.get('segment', 'Unknown')
                    )
                    self.db.add(customer)
                    count += 1

            self.db.commit()
            self.last_sync['customers'] = datetime.now()

            print(f"  ✓ Synced {count} customer updates")

        except Exception as e:
            print(f"  ❌ Error syncing customers: {e}")
            self.db.rollback()

    def rebuild_graph(self):
        """
        Rebuild graph after data sync.

        This should run less frequently (e.g., every hour).
        """
        try:
            print(f"[{datetime.now()}] 🔧 Rebuilding graph...")
            import subprocess
            subprocess.run(['python', 'scripts/build_graph.py'], check=True)
            print("  ✓ Graph rebuilt")
        except Exception as e:
            print(f"  ❌ Error rebuilding graph: {e}")

    def run_continuous_sync(self):
        """
        Run continuous synchronization.

        Schedules:
        - Orders: every 5 minutes
        - Customers: every 15 minutes
        - Graph rebuild: every 1 hour
        """
        print("🚀 Starting continuous data sync...")
        print("  Orders: every 5 minutes")
        print("  Customers: every 15 minutes")
        print("  Graph rebuild: every 1 hour")
        print()

        # Schedule jobs
        schedule.every(5).minutes.do(self.sync_new_orders)
        schedule.every(15).minutes.do(self.sync_customer_updates)
        schedule.every(1).hours.do(self.rebuild_graph)

        # Run immediately once
        self.sync_new_orders()
        self.sync_customer_updates()
        self.rebuild_graph()

        # Run scheduled jobs
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute


def sync_from_database_changes():
    """
    Alternative: Sync by monitoring database changes.

    Use database triggers or change data capture (CDC).
    """
    # Example: PostgreSQL using LISTEN/NOTIFY
    import psycopg2

    conn = psycopg2.connect("postgresql://user:pass@localhost/source_db")
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

    cursor = conn.cursor()
    cursor.execute("LISTEN new_order_event;")

    print("🎧 Listening for database events...")

    while True:
        conn.poll()
        while conn.notifies:
            notify = conn.notifies.pop(0)
            print(f"Received notification: {notify.payload}")
            # Process the change...


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python sync_realtime_data.py continuous  # Run continuous sync")
        print("  python sync_realtime_data.py once        # Run once")
        sys.exit(1)

    mode = sys.argv[1]

    sync_service = DataSyncService()

    if mode == "continuous":
        sync_service.run_continuous_sync()
    elif mode == "once":
        sync_service.sync_new_orders()
        sync_service.sync_customer_updates()
        sync_service.rebuild_graph()
    else:
        print(f"Unknown mode: {mode}")
        sys.exit(1)
