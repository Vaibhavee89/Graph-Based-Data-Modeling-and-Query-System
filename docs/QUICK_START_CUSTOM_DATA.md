# Quick Start: Using Your Own Data

This guide helps you get started with your own data sources in under 10 minutes.

## 🎯 Choose Your Scenario

### Scenario 1: I have a MySQL/PostgreSQL database
**Time: 5 minutes**

```bash
# 1. Update connection string
nano backend/.env
# Change: DATABASE_URL=mysql+pymysql://user:pass@host:3306/mydb

# 2. Install driver (if needed)
docker-compose exec backend pip install pymysql

# 3. Restart
docker-compose restart backend
```

✅ **Done!** Your existing database is now connected.

---

### Scenario 2: I have CSV/Excel files
**Time: 3 minutes**

```bash
# 1. Place CSV files in data/raw/
cp /path/to/your/*.csv data/raw/

# 2. Load data
docker-compose exec backend python scripts/load_from_api.py csv data/raw/

# 3. Build graph
docker-compose exec backend python scripts/build_graph.py

# 4. Restart
docker-compose restart backend
```

**CSV Format Example:**
```csv
customer_id,name,email,segment
C001,Acme Corp,contact@acme.com,Enterprise
```

✅ **Done!** Your CSV data is now visualized as a graph.

---

### Scenario 3: I have a REST API (Salesforce, custom, etc.)
**Time: 5 minutes**

```bash
# 1. Edit the API script
nano backend/scripts/load_from_api.py
# Update API URL and credentials (lines 27-40)

# 2. Run loader
docker-compose exec backend python scripts/load_from_api.py salesforce

# 3. Build graph
docker-compose exec backend python scripts/build_graph.py
```

✅ **Done!** API data is loaded.

---

### Scenario 4: I need real-time updates
**Time: 10 minutes**

```bash
# 1. Configure sync intervals
nano backend/scripts/sync_realtime_data.py
# Edit lines 154-156 for your schedule

# 2. Run continuous sync
docker-compose exec backend python scripts/sync_realtime_data.py continuous

# Or schedule with cron:
crontab -e
# Add: 0 * * * * cd /path/to/project && python scripts/sync_realtime_data.py once
```

✅ **Done!** System auto-updates every N minutes.

---

## 🔧 Custom Entities (Different from Orders/Customers)

**Example: Healthcare System**

### Step 1: Define Models
Create `backend/app/models/healthcare.py`:
```python
from sqlalchemy import Column, String, DateTime, ForeignKey
from app.core.database import Base

class Patient(Base):
    __tablename__ = "patients"
    patient_id = Column(String(50), primary_key=True)
    name = Column(String(255))
    date_of_birth = Column(DateTime)
```

### Step 2: Update Graph Builder
Edit `backend/app/utils/graph_builder.py` (around line 50):
```python
# Add Patient nodes
patients = self.db.query(Patient).all()
for patient in patients:
    self.add_node(
        node_id=patient.patient_id,
        node_type="Patient",
        label=patient.name,
        color="#3B82F6",  # Blue
        properties={"name": patient.name, ...}
    )
```

### Step 3: Rebuild
```bash
docker-compose exec backend python scripts/init_db.py
docker-compose exec backend python scripts/build_graph.py
docker-compose restart backend
```

✅ **Done!** Custom entities now in graph.

See [CUSTOM_SCHEMA_GUIDE.md](./CUSTOM_SCHEMA_GUIDE.md) for complete examples (E-commerce, Healthcare, Supply Chain).

---

## 📊 Supported Databases

| Database | Connection String Example |
|----------|--------------------------|
| **PostgreSQL** | `postgresql://user:pass@host:5432/db` |
| **MySQL** | `mysql+pymysql://user:pass@host:3306/db` |
| **SQLite** | `sqlite:///./local.db` |
| **SQL Server** | `mssql+pyodbc://user:pass@host/db?driver=...` |
| **Oracle** | `oracle+cx_oracle://user:pass@host:1521/db` |

---

## 🚀 Complete Guides

1. **[DATA_INTEGRATION_GUIDE.md](./DATA_INTEGRATION_GUIDE.md)** - Full integration guide with examples
2. **[CUSTOM_SCHEMA_GUIDE.md](./CUSTOM_SCHEMA_GUIDE.md)** - How to add custom entities
3. **[DEPLOYMENT.md](./DEPLOYMENT.md)** - Production deployment

---

## ❓ Troubleshooting

### Graph not showing data?
```bash
# Check if data loaded
docker-compose exec backend python -c "from app.core.database import SessionLocal; from app.models import Customer; db = SessionLocal(); print(f'{db.query(Customer).count()} customers')"

# Rebuild graph
docker-compose exec backend python scripts/build_graph.py
docker-compose restart backend
```

### Connection errors?
```bash
# Test database connection
docker-compose exec backend python -c "from sqlalchemy import create_engine; engine = create_engine('YOUR_DATABASE_URL'); engine.connect()"
```

### Can't see logs?
```bash
docker-compose logs backend -f
docker-compose logs frontend -f
```

---

## 💡 Next Steps

1. **Try with sample data first** (already loaded: 140 nodes, 212 edges)
2. **Connect your database** (Scenario 1 or 2 above)
3. **Customize for your domain** (if needed - see CUSTOM_SCHEMA_GUIDE.md)
4. **Set up real-time sync** (optional - Scenario 4)

Need help? Check the complete guides linked above!
