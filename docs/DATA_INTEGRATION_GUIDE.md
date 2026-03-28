# Data Integration Guide

Complete guide for integrating your own data sources with the Graph System.

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Database Options](#database-options)
3. [Data Source Options](#data-source-options)
4. [Custom Schema](#custom-schema)
5. [Real-Time Sync](#real-time-sync)
6. [Examples](#examples)

---

## Quick Start

### Scenario: You have an existing PostgreSQL database

```bash
# 1. Update connection string
cd backend
nano .env

# Change this line:
DATABASE_URL=postgresql://user:password@your-server:5432/your-database

# 2. Load your data (see options below)
python scripts/load_from_existing_db.py

# 3. Build graph
python scripts/build_graph.py

# 4. Restart backend
docker-compose restart backend

# 5. Done! Open http://localhost:3000
```

---

## Database Options

### ✅ Supported Databases

The system uses SQLAlchemy and supports:

| Database | Connection String | Driver Required |
|----------|-------------------|-----------------|
| **PostgreSQL** | `postgresql://user:pass@host:5432/db` | `psycopg2-binary` ✓ |
| **MySQL** | `mysql+pymysql://user:pass@host:3306/db` | `pymysql` |
| **SQLite** | `sqlite:///path/to/db.db` | Built-in ✓ |
| **SQL Server** | `mssql+pyodbc://user:pass@host/db?driver=...` | `pyodbc` |
| **Oracle** | `oracle+cx_oracle://user:pass@host:1521/db` | `cx_oracle` |
| **MariaDB** | `mysql+pymysql://user:pass@host:3306/db` | `pymysql` |

### Switch to MySQL

```bash
# 1. Install MySQL driver
pip install pymysql

# 2. Update .env
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/businessdb

# 3. Initialize tables
python scripts/init_db.py
```

### Switch to SQLite (Local Testing)

```bash
# 1. Update .env
DATABASE_URL=sqlite:///./graphdb.db

# 2. Initialize
python scripts/init_db.py
```

---

## Data Source Options

### Option 1: Existing Database (Direct Connection)

**Best for:** You have data in another database

```bash
# Edit scripts/load_from_existing_db.py
# Update the connection string and field mappings

python scripts/load_from_existing_db.py
```

**Field Mapping Example:**
```python
# Your database has: customer_number, full_name, email_addr
# Our system needs: customer_id, name, email

FIELD_MAPPINGS = {
    'customers': {
        'source_table': 'tbl_customers',
        'fields': {
            'customer_number': 'customer_id',   # Your field → Our field
            'full_name': 'name',
            'email_addr': 'email',
            'type': 'segment'
        }
    }
}
```

### Option 2: CSV/Excel Files

**Best for:** Exporting data from existing systems

```bash
# 1. Export your data to CSV
# Files needed: customers.csv, orders.csv, products.csv, etc.

# 2. Place in data/raw/ directory
cp /path/to/your/data/*.csv data/raw/

# 3. Load from CSV
python scripts/load_from_api.py csv data/raw/
```

**CSV Format Example (customers.csv):**
```csv
customer_id,name,email,segment
C001,Acme Corp,contact@acme.com,Enterprise
C002,TechStart,info@techstart.com,SMB
```

### Option 3: REST APIs

**Best for:** Salesforce, SAP, custom APIs

```bash
# Edit scripts/load_from_api.py
# Add your API credentials and endpoints

python scripts/load_from_api.py salesforce
```

**Example API Integration:**
```python
# Salesforce
headers = {"Authorization": "Bearer YOUR_TOKEN"}
response = requests.get(
    "https://yourinstance.salesforce.com/services/data/v52.0/query/",
    headers=headers,
    params={"q": "SELECT Id, Name, Email FROM Account"}
)

# SAP
response = requests.get(
    "https://your-sap-system:8000/sap/opu/odata/sap/API_BUSINESS_PARTNER",
    auth=("username", "password")
)

# Custom API
response = requests.get(
    "https://api.yourcompany.com/customers",
    headers={"X-API-Key": "your-key"}
)
```

### Option 4: Real-Time Sync

**Best for:** Live data that changes frequently

```bash
# Run continuous sync (updates every 5-15 minutes)
python scripts/sync_realtime_data.py continuous
```

**Schedule as a background service:**
```bash
# Using systemd (Linux)
sudo systemctl start graph-sync.service

# Using cron (run every hour)
0 * * * * cd /path/to/project && python scripts/sync_realtime_data.py once

# Using Docker
docker-compose up -d sync-service
```

---

## Custom Schema

### Your Data Model is Different?

**No problem!** The system is flexible.

#### Example: E-commerce Platform

You have: `Stores`, `Products`, `Reviews`, `Carts`

**1. Define your models** (`backend/app/models/custom.py`):

```python
class Store(Base):
    __tablename__ = "stores"
    store_id = Column(String(50), primary_key=True)
    name = Column(String(255))
    location = Column(String(255))
    rating = Column(Float)

class Review(Base):
    __tablename__ = "reviews"
    review_id = Column(String(50), primary_key=True)
    product_id = Column(String(50), ForeignKey("products.product_id"))
    customer_id = Column(String(50), ForeignKey("customers.customer_id"))
    rating = Column(Integer)
    comment = Column(String(1000))
```

**2. Update graph builder** (add to `backend/app/utils/graph_builder.py`):

```python
# Add Store nodes (Purple)
stores = self.db.query(Store).all()
for store in stores:
    self.add_node(store.store_id, "Store", store.name, "#8B5CF6", {...})

# Add Review nodes (Pink)
reviews = self.db.query(Review).all()
for review in reviews:
    self.add_node(review.review_id, "Review", f"{review.rating}★", "#EC4899", {...})

# Add edges
for review in reviews:
    self.add_edge(review.customer_id, review.review_id, "WROTE", "wrote")
    self.add_edge(review.review_id, review.product_id, "REVIEWS", "reviews")
```

**3. Rebuild and see your custom graph!**

```bash
python scripts/init_db.py
python scripts/build_graph.py
docker-compose restart backend
```

See [CUSTOM_SCHEMA_GUIDE.md](./CUSTOM_SCHEMA_GUIDE.md) for complete examples.

---

## Real-Time Sync

### Method 1: Polling (Simple)

Check for changes every N minutes:

```python
# scripts/sync_realtime_data.py
schedule.every(5).minutes.do(sync_new_orders)
schedule.every(15).minutes.do(sync_customer_updates)
schedule.every(1).hours.do(rebuild_graph)
```

### Method 2: Webhooks (Event-driven)

Listen for changes from external systems:

```python
@app.post("/webhook/new-order")
async def handle_new_order(order_data: dict):
    # Add new order to database
    order = Order(**order_data)
    db.add(order)
    db.commit()

    # Trigger graph rebuild
    asyncio.create_task(rebuild_graph())
```

### Method 3: Database Triggers (Advanced)

Use PostgreSQL LISTEN/NOTIFY:

```sql
-- In your source database
CREATE TRIGGER notify_new_order
AFTER INSERT ON orders
FOR EACH ROW
EXECUTE FUNCTION pg_notify('new_order', row_to_json(NEW)::text);
```

```python
# In Python
cursor.execute("LISTEN new_order;")
while True:
    conn.poll()
    for notify in conn.notifies:
        process_new_order(notify.payload)
```

---

## Examples

### Example 1: Connect to Existing SAP Database

```bash
# 1. Update .env
DATABASE_URL=postgresql://sapuser:sappass@sap-db-server:5432/sapdb

# 2. Map SAP tables to our schema
# Edit scripts/load_from_existing_db.py:

FIELD_MAPPINGS = {
    'customers': {
        'source_table': 'KNA1',  # SAP customer table
        'fields': {
            'KUNNR': 'customer_id',   # Customer number
            'NAME1': 'name',           # Name
            'SMTP_ADDR': 'email',      # Email
        }
    },
    'orders': {
        'source_table': 'VBAK',  # SAP sales order header
        'fields': {
            'VBELN': 'order_id',
            'KUNNR': 'customer_id',
            'ERDAT': 'order_date',
            'NETWR': 'total_amount'
        }
    }
}

# 3. Load and build
python scripts/load_from_existing_db.py
python scripts/build_graph.py
```

### Example 2: Load from Salesforce

```bash
# 1. Get Salesforce access token
# 2. Edit scripts/load_from_api.py
# 3. Run:

python scripts/load_from_api.py salesforce
python scripts/build_graph.py
docker-compose restart backend
```

### Example 3: Daily Batch Updates from CSV

```bash
# 1. Create cron job
crontab -e

# 2. Add this line (runs at 2 AM daily):
0 2 * * * cd /path/to/project && python scripts/load_from_api.py csv /data/exports/ && python scripts/build_graph.py

# 3. Your system auto-updates daily with fresh data!
```

### Example 4: Healthcare System

```python
# Custom models for healthcare
class Patient(Base):
    patient_id = Column(String(50), primary_key=True)
    name = Column(String(255))
    date_of_birth = Column(Date)

class Doctor(Base):
    doctor_id = Column(String(50), primary_key=True)
    name = Column(String(255))
    specialization = Column(String(100))

class Appointment(Base):
    appointment_id = Column(String(50), primary_key=True)
    patient_id = Column(String(50), ForeignKey("patients.patient_id"))
    doctor_id = Column(String(50), ForeignKey("doctors.doctor_id"))
    appointment_date = Column(DateTime)

# Graph will show: Patient → Appointment → Doctor → Prescription
```

---

## Troubleshooting

### Connection Issues

```bash
# Test database connection
python -c "from sqlalchemy import create_engine; engine = create_engine('YOUR_DATABASE_URL'); engine.connect()"
```

### Data Not Appearing

```bash
# Check if data loaded
docker-compose exec backend python -c "from app.core.database import SessionLocal; from app.models import Customer; db = SessionLocal(); print(db.query(Customer).count())"

# Rebuild graph
docker-compose exec backend python scripts/build_graph.py
docker-compose restart backend
```

### Graph Not Updating

```bash
# Clear cache and rebuild
rm backend/graph.pickle
docker-compose exec backend python scripts/build_graph.py
docker-compose restart backend
```

---

## Need Help?

1. **Check logs:**
   ```bash
   docker-compose logs backend
   ```

2. **Test individual components:**
   ```bash
   # Test database connection
   python scripts/test_connection.py

   # Test data loading
   python scripts/load_sample_data.py

   # Test graph building
   python scripts/build_graph.py
   ```

3. **Examples:**
   - See `scripts/load_from_existing_db.py` for database integration
   - See `scripts/load_from_api.py` for API integration
   - See `docs/CUSTOM_SCHEMA_GUIDE.md` for schema customization

---

## Summary

**Your Data → Graph System:**

1. ✅ **Choose source:** Existing DB, CSV, API, Real-time
2. ✅ **Configure connection:** Update `.env` with DATABASE_URL
3. ✅ **Load data:** Run appropriate script
4. ✅ **Build graph:** `python scripts/build_graph.py`
5. ✅ **Restart:** `docker-compose restart backend`
6. ✅ **Visualize:** Open http://localhost:3000

The system is **database-agnostic** and **schema-flexible**. Adapt it to your needs! 🚀
