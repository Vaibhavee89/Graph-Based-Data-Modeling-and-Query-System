"""Generate and load sample data for testing."""
import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.models import (
    Customer, Product, Order, OrderItem,
    Invoice, Payment, Delivery, Address
)


def generate_sample_data():
    """Generate sample graph data."""
    db = SessionLocal()

    try:
        print("🚀 Generating sample data...")

        # Clear existing data
        print("  Clearing existing data...")
        db.query(OrderItem).delete()
        db.query(Payment).delete()
        db.query(Invoice).delete()
        db.query(Delivery).delete()
        db.query(Order).delete()
        db.query(Address).delete()
        db.query(Product).delete()
        db.query(Customer).delete()
        db.commit()

        # Generate Customers (10)
        print("  Creating customers...")
        customers = []
        customer_names = [
            "Acme Corporation", "TechStart Inc", "Global Dynamics",
            "Innovative Solutions", "NextGen Systems", "Digital Ventures",
            "Smart Industries", "Future Technologies", "Prime Solutions",
            "Elite Enterprises"
        ]
        segments = ["Enterprise", "SMB", "Startup", "Partner"]

        for i, name in enumerate(customer_names, 1):
            customer = Customer(
                customer_id=f"CUST-{i:03d}",
                name=name,
                email=f"contact@{name.lower().replace(' ', '')}.com",
                segment=random.choice(segments)
            )
            db.add(customer)
            customers.append(customer)

        db.commit()
        print(f"    ✓ Created {len(customers)} customers")

        # Generate Addresses (15)
        print("  Creating addresses...")
        addresses = []
        cities = ["New York", "San Francisco", "Chicago", "Boston", "Seattle",
                 "Austin", "Denver", "Miami", "Portland", "Atlanta"]
        states = ["NY", "CA", "IL", "MA", "WA", "TX", "CO", "FL", "OR", "GA"]

        for i in range(15):
            idx = i % len(cities)
            address = Address(
                address_id=f"ADDR-{i+1:03d}",
                street=f"{random.randint(100, 9999)} Main Street",
                city=cities[idx],
                state=states[idx],
                postal_code=f"{random.randint(10000, 99999)}",
                country="USA",
                address_type=random.choice(["billing", "shipping"])
            )
            db.add(address)
            addresses.append(address)

        db.commit()
        print(f"    ✓ Created {len(addresses)} addresses")

        # Generate Products (20)
        print("  Creating products...")
        products = []
        product_data = [
            ("Enterprise Software License", "Software", 5000),
            ("Cloud Storage - 1TB", "Cloud", 99),
            ("API Access Premium", "Service", 299),
            ("Consulting Hours - Senior", "Service", 200),
            ("Hardware Server - Rack", "Hardware", 8000),
            ("Database License", "Software", 3000),
            ("Network Switch 48-port", "Hardware", 2500),
            ("Security Audit", "Service", 5000),
            ("Training Package", "Service", 1500),
            ("Support Contract - Gold", "Service", 10000),
            ("Mobile App License", "Software", 1200),
            ("Analytics Platform", "Software", 4000),
            ("Load Balancer", "Hardware", 3500),
            ("SSL Certificate", "Service", 199),
            ("Backup Solution", "Software", 1800),
            ("Monitoring Tools", "Software", 800),
            ("Development Tools", "Software", 2200),
            ("Integration Service", "Service", 3000),
            ("Custom Development", "Service", 15000),
            ("Maintenance Contract", "Service", 5000)
        ]

        for i, (name, category, price) in enumerate(product_data, 1):
            product = Product(
                product_id=f"PROD-{i:03d}",
                name=name,
                category=category,
                price=float(price),
                description=f"High-quality {name.lower()}"
            )
            db.add(product)
            products.append(product)

        db.commit()
        print(f"    ✓ Created {len(products)} products")

        # Generate Orders and related data (30 orders)
        print("  Creating orders with items, invoices, payments, and deliveries...")
        base_date = datetime.now() - timedelta(days=90)

        for i in range(1, 31):
            # Create Order
            order_date = base_date + timedelta(days=random.randint(0, 90))
            customer = random.choice(customers)

            order = Order(
                order_id=f"ORD-{i:03d}",
                customer_id=customer.customer_id,
                order_date=order_date,
                status=random.choice(["completed", "completed", "completed", "processing", "shipped"]),
                total_amount=0  # Will calculate
            )
            db.add(order)
            db.flush()

            # Create Order Items (2-5 items per order)
            num_items = random.randint(2, 5)
            order_total = 0

            for j in range(num_items):
                product = random.choice(products)
                quantity = random.randint(1, 10)
                item_total = product.price * quantity
                order_total += item_total

                order_item = OrderItem(
                    order_id=order.order_id,
                    product_id=product.product_id,
                    quantity=quantity,
                    unit_price=product.price,
                    subtotal=item_total
                )
                db.add(order_item)

            order.total_amount = order_total

            # Create Invoice (80% of orders have invoices)
            if random.random() < 0.8:
                invoice_date = order_date + timedelta(days=1)
                invoice = Invoice(
                    invoice_id=f"INV-{i:03d}",
                    order_id=order.order_id,
                    invoice_date=invoice_date,
                    due_date=invoice_date + timedelta(days=30),
                    amount=order_total,
                    status=random.choice(["paid", "paid", "paid", "pending", "overdue"])
                )
                db.add(invoice)
                db.flush()

                # Create Payment (90% of invoices have payments)
                if random.random() < 0.9:
                    payment_date = invoice_date + timedelta(days=random.randint(1, 20))
                    payment = Payment(
                        payment_id=f"PAY-{i:03d}",
                        invoice_id=invoice.invoice_id,
                        payment_date=payment_date,
                        amount=order_total,
                        method=random.choice(["credit_card", "bank_transfer", "check", "wire"]),
                        transaction_id=f"TXN{random.randint(100000, 999999)}",
                        status="completed"
                    )
                    db.add(payment)

            # Create Delivery (75% of orders have deliveries)
            if random.random() < 0.75:
                delivery_date = order_date + timedelta(days=random.randint(3, 10))
                delivery_address = random.choice(addresses)
                delivery = Delivery(
                    delivery_id=f"DEL-{i:03d}",
                    order_id=order.order_id,
                    delivery_date=delivery_date,
                    status=random.choice(["delivered", "delivered", "in_transit", "pending"]),
                    tracking_number=f"TRACK{random.randint(100000, 999999)}",
                    address_id=delivery_address.address_id
                )
                db.add(delivery)

        db.commit()
        print(f"    ✓ Created 30 orders with items, invoices, payments, and deliveries")

        # Summary
        print("\n✅ Sample data generated successfully!")
        print("\n📊 Summary:")
        print(f"  • Customers: {db.query(Customer).count()}")
        print(f"  • Products: {db.query(Product).count()}")
        print(f"  • Orders: {db.query(Order).count()}")
        print(f"  • Order Items: {db.query(OrderItem).count()}")
        print(f"  • Addresses: {db.query(Address).count()}")
        print(f"  • Invoices: {db.query(Invoice).count()}")
        print(f"  • Payments: {db.query(Payment).count()}")
        print(f"  • Deliveries: {db.query(Delivery).count()}")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    generate_sample_data()
