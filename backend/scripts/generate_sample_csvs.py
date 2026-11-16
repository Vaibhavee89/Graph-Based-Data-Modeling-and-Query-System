"""Generate the deterministic sample dataset as CSV files in backend/sample_data/.

Same shape as the original demo (customers, products, addresses, orders, order items,
invoices, payments, deliveries) with a few deliberately incomplete order flows so
anomaly-style questions have something to find.
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "sample_data"
random.seed(42)
BASE = date(2025, 1, 1)


def write(name, header, rows):
    with open(OUT / f"{name}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"  {name}.csv: {len(rows)} rows")


def main():
    OUT.mkdir(exist_ok=True)

    names = ["Acme Corporation", "TechStart Inc", "Global Dynamics", "Innovative Solutions",
             "NextGen Systems", "Digital Ventures", "Smart Industries", "Future Technologies",
             "Prime Solutions", "Elite Enterprises"]
    segments = ["Enterprise", "SMB", "Startup", "Partner"]
    customers = [(f"CUST-{i:03d}", n, f"contact@{n.lower().replace(' ', '')}.com", random.choice(segments))
                 for i, n in enumerate(names, 1)]
    write("customers", ["customer_id", "name", "email", "segment"], customers)

    cities = ["New York", "San Francisco", "Chicago", "Boston", "Seattle",
              "Austin", "Denver", "Miami", "Portland", "Atlanta"]
    states = ["NY", "CA", "IL", "MA", "WA", "TX", "CO", "FL", "OR", "GA"]
    addresses = []
    for i in range(15):
        k = i % len(cities)
        addresses.append((f"ADDR-{i+1:03d}", f"{random.randint(100, 9999)} Main Street", cities[k], states[k],
                          f"{random.randint(10000, 99999)}", "USA", random.choice(["billing", "shipping"])))
    write("addresses", ["address_id", "street", "city", "state", "postal_code", "country", "address_type"], addresses)

    product_data = [
        ("Enterprise Software License", "Software", 5000), ("Cloud Storage - 1TB", "Cloud", 99),
        ("API Access Premium", "Service", 299), ("Consulting Hours - Senior", "Service", 200),
        ("Hardware Server - Rack", "Hardware", 8000), ("Database License", "Software", 3000),
        ("Network Switch 48-port", "Hardware", 2500), ("Security Audit", "Service", 5000),
        ("Training Package", "Service", 1500), ("Support Contract - Gold", "Service", 10000),
        ("Mobile App License", "Software", 1200), ("Analytics Platform", "Software", 4000),
        ("Load Balancer", "Hardware", 3500), ("SSL Certificate", "Service", 199),
        ("Backup Solution", "Software", 1800), ("Monitoring Tools", "Software", 800),
        ("Development Tools", "Software", 2200), ("Integration Service", "Service", 3000),
        ("Custom Development", "Service", 15000), ("Maintenance Contract", "Service", 5000),
    ]
    products = [(f"PROD-{i:03d}", n, c, float(p), f"High-quality {n.lower()}")
                for i, (n, c, p) in enumerate(product_data, 1)]
    write("products", ["product_id", "name", "category", "price", "description"], products)

    orders, items, invoices, payments, deliveries = [], [], [], [], []
    item_id = 0
    for i in range(1, 41):
        order_date = BASE + timedelta(days=random.randint(0, 120))
        cust = random.choice(customers)[0]
        total = 0.0
        for _ in range(random.randint(2, 5)):
            prod = random.choice(products)
            qty = random.randint(1, 10)
            item_id += 1
            items.append((item_id, f"ORD-{i:03d}", prod[0], qty, prod[3], prod[3] * qty))
            total += prod[3] * qty
        orders.append((f"ORD-{i:03d}", cust, order_date.isoformat(),
                       random.choice(["completed", "completed", "completed", "processing", "shipped"]), total))
        if random.random() < 0.8:
            inv_date = order_date + timedelta(days=1)
            invoices.append((f"INV-{i:03d}", f"ORD-{i:03d}", inv_date.isoformat(),
                             (inv_date + timedelta(days=30)).isoformat(), total,
                             random.choice(["paid", "paid", "paid", "pending", "overdue"])))
            if random.random() < 0.9:
                pay_date = inv_date + timedelta(days=random.randint(1, 20))
                payments.append((f"PAY-{i:03d}", f"INV-{i:03d}", pay_date.isoformat(), total,
                                 random.choice(["credit_card", "bank_transfer", "check", "wire"]),
                                 f"TXN{random.randint(100000, 999999)}", "completed"))
        if random.random() < 0.75:
            deliveries.append((f"DEL-{i:03d}", f"ORD-{i:03d}",
                               (order_date + timedelta(days=random.randint(3, 10))).isoformat(),
                               random.choice(["delivered", "delivered", "in_transit", "pending"]),
                               f"TRACK{random.randint(100000, 999999)}", random.choice(addresses)[0]))

    write("orders", ["order_id", "customer_id", "order_date", "status", "total_amount"], orders)
    write("order_items", ["id", "order_id", "product_id", "quantity", "unit_price", "subtotal"], items)
    write("invoices", ["invoice_id", "order_id", "invoice_date", "due_date", "amount", "status"], invoices)
    write("payments", ["payment_id", "invoice_id", "payment_date", "amount", "method", "transaction_id", "status"], payments)
    write("deliveries", ["delivery_id", "order_id", "delivery_date", "status", "tracking_number", "address_id"], deliveries)


if __name__ == "__main__":
    main()
